/**
 * @file runner.ts
 * @author Marek Gašpierik (xgaspim00)
 *
 * @brief Implements the main runner function that orchestrates the discovery, filtering, execution, and reporting of test cases.
 * @details This file was created to split object-oriented code into separate files for better organization and maintainability.
 */

import { mkdtempSync, rmSync, writeFileSync } from "fs";
import { tmpdir } from "os";
import { join } from "path";

import { TestDiscoverer } from "./discover_tests.js";
import { TestExecutor } from "./executor.js";
import { TestFilter } from "./filter.js";
import {
  CategoryReport,
  TestCaseDefinition,
  TestCaseDefinitionFile,
  TestCaseReport,
  TestCaseType,
  TestReport,
  TestResult,
  UnexecutedReason,
  UnexecutedReasonCode,
} from "./models.js";
import { CliArguments } from "./tester.js";

/**
 * @brief The main Tester class that orchestrates the discovery, filtering, execution, and reporting of test cases.
 */
export class Tester {
  private discoverer: TestDiscoverer;
  private filter: TestFilter;
  private executor: TestExecutor;
  private discovered: TestCaseDefinitionFile[];
  private parsed: TestCaseDefinition[];
  private unexecuted: Record<string, UnexecutedReason>;
  private to_run: TestCaseDefinition[];

  constructor(args: CliArguments) {
    this.discoverer = new TestDiscoverer(args.tests_dir, args.recursive);
    this.filter = new TestFilter(
      args.include,
      args.include_category,
      args.include_test,
      args.exclude,
      args.exclude_category,
      args.exclude_test
    );
    this.executor = new TestExecutor(
      process.env["SOL2XML"] ?? "sol2xml",
      process.env["INTERPRETER"] ?? "python3"
    );
    this.discovered = [];
    this.parsed = [];
    this.unexecuted = {};
    this.to_run = [];
  }

  /**
   * @brief Calls the discoverer to find test files and parses them into TestCaseDefinition objects,
   * while handling any unexecuted reasons.
   * @details More information about the discovery logic can be found in discover_tests.ts.
   */
  discover(): void {
    this.discovered = this.discoverer.discover();
    for (const file of this.discovered) {
      const result = this.discoverer.parse(file);
      if (result instanceof UnexecutedReason) {
        this.unexecuted[file.name] = result;
      } else {
        this.parsed.push(result);
      }
    }
  }

  /**
   * @brief Calls the filter to determine which tests should be run.
   * @details More information about the filtering logic can be found in filter.ts.
   */
  filter_tests(): void {
    const { tests_to_run, filtered_out } = this.filter.filter(this.parsed);
    this.to_run = tests_to_run;
    for (const test of filtered_out) {
      this.unexecuted[test.name] = new UnexecutedReason(UnexecutedReasonCode.FILTERED_OUT);
    }
  }

  /**
   * @brief Runs a single PARSE_ONLY test: compile SOL26 source, check exit code.
   *
   * @param test The test case to run.
   * @param source_code The source code of the test case.
   * @param tmp_dir The temporary directory for the test.
   *
   * @returns The report of the test execution.
   */
  private run_parse_only(
    test: TestCaseDefinition,
    source_code: string,
    tmp_dir: string
  ): TestCaseReport {
    const source_file = join(tmp_dir, "source.sol");
    writeFileSync(source_file, source_code);

    const compiler_result = this.executor.run_compiler(source_file);
    let passed = false;
    if (test.expected_parser_exit_codes !== null) {
      passed = test.expected_parser_exit_codes.includes(compiler_result.exit_code);
    } else {
      passed = compiler_result.exit_code === 0;
    }

    let final_result_status: TestResult;
    if (passed) {
      final_result_status = TestResult.PASSED;
    } else {
      final_result_status = TestResult.UNEXPECTED_PARSER_EXIT_CODE;
    }

    return new TestCaseReport(
      final_result_status,
      compiler_result.exit_code,
      null,
      compiler_result.stdout,
      compiler_result.stderr
    );
  }

  /**
   * @brief Runs a single EXECUTE_ONLY test: run interpreter on provided XML, check exit code and optionally diff output.
   *
   * @param test The test case to run.
   * @param source_code The source code of the test case.
   * @param tmp_dir The temporary directory for the test.
   *
   * @returns The report of the test execution.
   */
  private run_execute_only(
    test: TestCaseDefinition,
    source_code: string,
    tmp_dir: string
  ): TestCaseReport {
    const xml_file = join(tmp_dir, "source.xml");
    writeFileSync(xml_file, source_code);

    const interp_result = this.executor.run_interpreter(xml_file, test.stdin_file);
    let exit_ok = false;
    if (test.expected_interpreter_exit_codes !== null) {
      exit_ok = test.expected_interpreter_exit_codes.includes(interp_result.exit_code);
    } else {
      exit_ok = interp_result.exit_code === 0;
    }

    if (!exit_ok) {
      return new TestCaseReport(
        TestResult.UNEXPECTED_INTERPRETER_EXIT_CODE,
        null,
        interp_result.exit_code,
        null,
        null,
        interp_result.stdout,
        interp_result.stderr
      );
    }

    if (test.expected_stdout_file !== null) {
      const diff = this.executor.run_diff(interp_result.stdout, test.expected_stdout_file);
      if (diff.differs) {
        return new TestCaseReport(
          TestResult.INTERPRETER_RESULT_DIFFERS,
          null,
          interp_result.exit_code,
          null,
          null,
          interp_result.stdout,
          interp_result.stderr,
          diff.diff_output
        );
      }
    }

    return new TestCaseReport(
      TestResult.PASSED,
      null,
      interp_result.exit_code,
      null,
      null,
      interp_result.stdout,
      interp_result.stderr
    );
  }

  /**
   * @brief Runs a single COMBINED test: compile SOL26 source, check compiler exit code,
   * run interpreter on XML output, check interpreter exit code and optionally diff output.
   *
   * @param test The test case to run.
   * @param source_code The source code of the test case.
   * @param tmp_dir The temporary directory for the test.
   *
   * @returns The report of the test execution.
   */
  private run_combined(
    test: TestCaseDefinition,
    source_code: string,
    tmp_dir: string
  ): TestCaseReport {
    const source_file = join(tmp_dir, "source.sol");
    writeFileSync(source_file, source_code);

    const compiler_result = this.executor.run_compiler(source_file);
    const compiler_exit_ok = compiler_result.exit_code === 0;

    if (!compiler_exit_ok) {
      return new TestCaseReport(
        TestResult.UNEXPECTED_PARSER_EXIT_CODE,
        compiler_result.exit_code,
        null,
        compiler_result.stdout,
        compiler_result.stderr
      );
    }

    const xml_file = join(tmp_dir, "output.xml");
    writeFileSync(xml_file, compiler_result.stdout);

    const interp_result = this.executor.run_interpreter(xml_file, test.stdin_file);
    let exit_ok = false;
    if (test.expected_interpreter_exit_codes !== null) {
      exit_ok = test.expected_interpreter_exit_codes.includes(interp_result.exit_code);
    } else {
      exit_ok = interp_result.exit_code === 0;
    }

    if (!exit_ok) {
      return new TestCaseReport(
        TestResult.UNEXPECTED_INTERPRETER_EXIT_CODE,
        compiler_result.exit_code,
        interp_result.exit_code,
        compiler_result.stdout,
        compiler_result.stderr,
        interp_result.stdout,
        interp_result.stderr
      );
    }

    if (test.expected_stdout_file !== null) {
      const diff = this.executor.run_diff(interp_result.stdout, test.expected_stdout_file);
      if (diff.differs) {
        return new TestCaseReport(
          TestResult.INTERPRETER_RESULT_DIFFERS,
          compiler_result.exit_code,
          interp_result.exit_code,
          compiler_result.stdout,
          compiler_result.stderr,
          interp_result.stdout,
          interp_result.stderr,
          diff.diff_output
        );
      }
    }

    return new TestCaseReport(
      TestResult.PASSED,
      compiler_result.exit_code,
      interp_result.exit_code,
      compiler_result.stdout,
      compiler_result.stderr,
      interp_result.stdout,
      interp_result.stderr
    );
  }

  /**
   * @brief Runs a single test case based on its type and returns the corresponding report.
   *
   * @param test The test case to run.
   *
   * @returns The report of the test execution or an unexecuted reason if the test could not be executed.
   */
  private run_test(test: TestCaseDefinition): TestCaseReport | UnexecutedReason {
    const source_code = this.discoverer.get_source_code(test);
    // Each test gets its own temp dir to isolate generated files (source.sol, output.xml)
    const tmp_dir = mkdtempSync(join(tmpdir(), "sol26-"));
    try {
      if (test.test_type === TestCaseType.PARSE_ONLY) {
        return this.run_parse_only(test, source_code, tmp_dir);
      } else if (test.test_type === TestCaseType.EXECUTE_ONLY) {
        return this.run_execute_only(test, source_code, tmp_dir);
      } else {
        return this.run_combined(test, source_code, tmp_dir);
      }
    } catch (err) {
      return new UnexecutedReason(
        UnexecutedReasonCode.CANNOT_EXECUTE,
        err instanceof Error ? err.message : String(err)
      );
    } finally {
      rmSync(tmp_dir, { recursive: true });
    }
  }

  /**
   * @brief Runs all the tests that passed the filtering stage and compiles a report of the results.
   *
   * @param dry_run Flag indicating whether to run in dry-run mode (only discover and filter tests, don't execute).
   *
   * @returns The final test report.
   */
  run(dry_run: boolean): TestReport {
    if (dry_run) {
      return new TestReport({
        discovered_test_cases: this.parsed,
        unexecuted: this.unexecuted,
        results: null,
      });
    }

    const results: Record<string, CategoryReport> = {};

    for (const test of this.to_run) {
      const report = this.run_test(test);

      if (report instanceof UnexecutedReason) {
        this.unexecuted[test.name] = report;
        continue;
      }

      if (results[test.category] === undefined) {
        results[test.category] = new CategoryReport(0, 0, {});
      }

      const category = results[test.category] as CategoryReport;
      const total = category.total_points + test.points;

      let passed = category.passed_points;
      if (report.result === TestResult.PASSED) {
        passed += test.points;
      }
      const test_results = Object.assign({}, category.test_results);
      test_results[test.name] = report;

      results[test.category] = new CategoryReport(total, passed, test_results);
    }

    return new TestReport({
      discovered_test_cases: this.parsed,
      unexecuted: this.unexecuted,
      results,
    });
  }
}
