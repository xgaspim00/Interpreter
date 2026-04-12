/**
 * @file discover_tests.ts
 * @author Marek Gašpierik (xgaspim00)
 *
 * @brief Implements the TestDiscoverer class responsible for discovering test files and parsing them into TestCaseDefinition objects.
 */

import { readdirSync, readFileSync, existsSync } from "fs";
import { join, basename } from "path";
import {
  TestCaseDefinition,
  TestCaseDefinitionFile,
  UnexecutedReason,
  TestCaseType,
  UnexecutedReasonCode,
} from "./models.js";

/**
 * @brief Discovers test files, parses them, and produces TestCaseDefinition objects for execution.
 * @details Discovering both non-recursively and recursively is supported.
 */
export class TestDiscoverer {
  constructor(
    private dir: string,
    private recursive: boolean
  ) {}

  /**
   * @brief Recursively discovers test files in the specified directory.
   *
   * @returns A list of TestCaseDefinitionFile objects representing discovered test files.
   */
  discover(): TestCaseDefinitionFile[] {
    const test_files: TestCaseDefinitionFile[] = [];
    const entries = readdirSync(this.dir, { withFileTypes: true });

    for (const entry of entries) {
      const full_path = join(this.dir, entry.name);
      if (entry.isDirectory() && this.recursive) {
        const sub = new TestDiscoverer(full_path, this.recursive);
        test_files.push(...sub.discover());
      } else if (entry.isFile() && entry.name.endsWith(".test")) {
        const base_path = join(this.dir, basename(entry.name, ".test"));

        // Check for optional .in and .out files corresponding to the test file
        let stdin_file: string | null = null;
        let expected_stdout_file: string | null = null;
        if (existsSync(base_path + ".in")) {
          stdin_file = base_path + ".in";
        }
        if (existsSync(base_path + ".out")) {
          expected_stdout_file = base_path + ".out";
        }

        test_files.push(
          new TestCaseDefinitionFile({
            name: basename(entry.name, ".test"),
            test_source_path: full_path,
            stdin_file: stdin_file,
            expected_stdout_file: expected_stdout_file,
          })
        );
      }
    }
    return test_files;
  }

  /**
   * @brief Parses a test file to extract metadata and determine the test type.
   *
   * @returns The source code of the test case as a string.
   */
  public get_source_code(file: TestCaseDefinitionFile): string {
    const lines = readFileSync(file.test_source_path, "utf-8").split("\n");
    const { source_code } = this.parse_headers(lines);
    return source_code;
  }

  /**
   * @brief Parses the headers of a test file to extract metadata
   *
   * @param lines The lines of the test file to parse
   *
   * @returns An object containing the parsed metadata and the source code of the test case
   */
  private parse_headers(lines: string[]): {
    description: string | null;
    category: string | null;
    points: number | null;
    parser_exit_codes: number[];
    interpreter_exit_codes: number[];
    source_code: string;
  } {
    // Header lines appear before the first blank line. Supported prefixes:
    //   *** Short description of the test
    //   +++ category-name       (required)
    //   !C! 0        (expected parser exit code, repeatable)
    //   !I! 0        (expected interpreter exit code, repeatable)
    //   >>> 1.5      (point value, required)
    // Everything after the blank line is the SOL source code.
    let description: string | null = null;
    let category: string | null = null;
    let points: number | null = null;
    const parser_exit_codes: number[] = [];
    const interpreter_exit_codes: number[] = [];

    let i = 0;
    for (; i < lines.length; i++) {
      const line = lines[i];
      if (line === undefined || line.trim() === "") {
        break;
      }
      if (line.startsWith("*** ")) {
        description = line.slice(4).trim();
      }
      if (line.startsWith("+++ ")) {
        category = line.slice(4).trim();
      }
      if (line.startsWith("!C! ")) {
        parser_exit_codes.push(parseInt(line.slice(4).trim()));
      }
      if (line.startsWith("!I! ")) {
        interpreter_exit_codes.push(parseInt(line.slice(4).trim()));
      }
      if (line.startsWith(">>> ")) {
        points = parseFloat(line.slice(4).trim());
      }
    }

    return {
      description,
      category,
      points,
      parser_exit_codes,
      interpreter_exit_codes,
      source_code: lines.slice(i + 1).join("\n"),
    };
  }

  /**
   * @brief Determines the test type
   *
   * @param has_parser Whether the test case has parser exit codes defined
   * @param has_interpreter Whether the test case has interpreter exit codes defined
   * @param is_xml Whether the test case source code appears to be XML
   *
   * @returns The determined test type or an unexecuted reason
   */
  private determine_test_type(
    has_parser: boolean,
    has_interpreter: boolean,
    is_xml: boolean
  ): TestCaseType | UnexecutedReason {
    if (has_parser && !has_interpreter) {
      return TestCaseType.PARSE_ONLY;
    }
    if (is_xml && !has_parser && has_interpreter) {
      return TestCaseType.EXECUTE_ONLY;
    }
    if (has_interpreter) {
      return TestCaseType.COMBINED;
    }
    if (is_xml) {
      return new UnexecutedReason(
        UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE,
        "XML source requires at least one interpreter exit code (!I!)"
      );
    }
    return new UnexecutedReason(
      UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE,
      "SOL26 source requires at least one parser exit code (!C!)"
    );
  }

  /**
   * @brief Parses a test file
   *
   * @param file The test file to parse
   *
   * @returns A TestCaseDefinition if parsing was successful
   * @returns An UnexecutedReason if a problem was encountered during parsing
   */
  parse(file: TestCaseDefinitionFile): TestCaseDefinition | UnexecutedReason {
    if (!existsSync(file.test_source_path)) {
      return new UnexecutedReason(
        UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE,
        "Cannot read file"
      );
    }

    const lines = readFileSync(file.test_source_path, "utf-8").split("\n");
    const {
      description,
      category,
      points,
      parser_exit_codes,
      interpreter_exit_codes,
      source_code,
    } = this.parse_headers(lines);

    if (category === null) {
      return new UnexecutedReason(
        UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE,
        "Missing category (+++)"
      );
    }

    if (points === null) {
      return new UnexecutedReason(
        UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE,
        "Missing point weight (>>>)"
      );
    }

    if (source_code.trim() === "") {
      return new UnexecutedReason(
        UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE,
        "Missing source code"
      );
    }

    const has_parser = parser_exit_codes.length > 0;
    const has_interpreter = interpreter_exit_codes.length > 0;
    const is_xml =
      source_code.trimStart().startsWith("<?xml") ||
      source_code.trimStart().startsWith("<program");

    const test_type = this.determine_test_type(has_parser, has_interpreter, is_xml);
    if (test_type instanceof UnexecutedReason) {
      return test_type;
    }

    let expected_parser_exit_codes: number[] | null = null;
    let expected_interpreter_exit_codes: number[] | null = null;

    if (has_parser) {
      expected_parser_exit_codes = parser_exit_codes;
    }
    if (has_interpreter) {
      expected_interpreter_exit_codes = interpreter_exit_codes;
    }

    return new TestCaseDefinition({
      name: file.name,
      test_source_path: file.test_source_path,
      stdin_file: file.stdin_file,
      expected_stdout_file: file.expected_stdout_file,
      test_type,
      description,
      category,
      points,
      expected_parser_exit_codes: expected_parser_exit_codes,
      expected_interpreter_exit_codes: expected_interpreter_exit_codes,
    });
  }
}
