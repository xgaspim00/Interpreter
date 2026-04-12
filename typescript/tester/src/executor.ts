/**
 * @file executor.ts
 * @author Marek Gašpierik (xgaspim00)
 *
 * @brief Executes compiler, interpreter and checks for differences in the output.
 */

import { spawnSync, SpawnSyncReturns } from "child_process";

/**
 * @brief Main executor class.
 */
export class TestExecutor {
  constructor(
    private compiler: string,
    private interpreter: string
  ) {}

  /**
   * @brief Splits a command string into the command and its arguments.
   *
   * @param cmd The command string to split, e.g., "tsc --noEmit".
   *
   * @returns A tuple containing the command and its arguments.
   */
  private split_command(cmd: string): [string, string[]] {
    const parts = cmd.split(" ");
    return [parts[0] as string, parts.slice(1)];
  }

  /**
   * @brief Extracts the exit code, stdout, and stderr
   *
   * @param result The result object containing the execution results of a command.
   *
   * @returns An object containing the extracted exit code, stdout, and stderr.
   */
  private extract_result(result: SpawnSyncReturns<string>): {
    exit_code: number;
    stdout: string;
    stderr: string;
  } {
    let exit_code = -1;
    if (result.status !== null) {
      exit_code = result.status;
    }
    const stdout = result.stdout;
    const stderr = result.stderr;
    return { exit_code, stdout, stderr };
  }

  /**
   * @brief Executes the compiler with the provided source path and captures the exit code, stdout, and stderr.
   *
   * @param source_path The path to the source file to compile.
   *
   * @returns An object containing the exit code, stdout, and stderr.
   */
  run_compiler(source_path: string): {
    exit_code: number;
    stdout: string;
    stderr: string;
  } {
    const [cmd, base_args] = this.split_command(this.compiler);
    const result = spawnSync(cmd, [...base_args, source_path], { encoding: "utf8" });
    const { exit_code, stdout, stderr } = this.extract_result(result);
    return {
      exit_code: exit_code,
      stdout: stdout,
      stderr: stderr,
    };
  }

  /**
   * @brief Executes the interpreter.
   *
   * @param xml_path The path to the XML file to execute.
   * @param stdin_file An optional path to a file containing input to be passed to the interpreter's stdin.
   *
   * @returns An object containing the exit code, stdout, and stderr from the interpreter execution.
   */
  run_interpreter(
    xml_path: string,
    stdin_file: string | null
  ): {
    exit_code: number;
    stdout: string;
    stderr: string;
  } {
    const [cmd, base_args] = this.split_command(this.interpreter);
    // -s: source file; -i: optional stdin file passed directly to the interpreter
    const extra_args = stdin_file !== null ? ["-i", stdin_file] : [];
    const result = spawnSync(cmd, [...base_args, "-s", xml_path, ...extra_args], {
      encoding: "utf8",
    });
    const { exit_code, stdout, stderr } = this.extract_result(result);
    return {
      exit_code: exit_code,
      stdout: stdout,
      stderr: stderr,
    };
  }

  /**
   * @brief Runs the diff command to compare the actual output with the expected output from a file.
   *
   * @param actual_output The actual output to compare.
   * @param expected_file The path to the file containing the expected output.
   *
   * @returns An object indicating whether the outputs differ and the diff output.
   */
  run_diff(
    actual_output: string,
    expected_file: string
  ): { differs: boolean; diff_output: string } {
    const result = spawnSync("diff", ["-", expected_file], {
      input: actual_output,
      encoding: "utf-8",
    });

    // diff exits with 1 when files differ, 2+ on error — only treat 1 as a diff
    const is_different = result.status === 1;
    return {
      differs: is_different,
      diff_output: result.stdout,
    };
  }
}
