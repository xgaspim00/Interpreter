/**
 * @file filter.ts
 * @author Marek Gašpierik (xgaspim00)
 *
 * @brief Implements the TestFilter class responsible for filtering test cases based on various criteria.
 */

import { TestCaseDefinition } from "./models.js";

/**
 * @brief Filters test cases based on inclusion and exclusion criteria specified by the user.
 * @details Matching uses exact string comparison against test name and/or category.
 */
export class TestFilter {
  constructor(
    private include: string[] | null,
    private include_category: string[] | null,
    private include_test: string[] | null,
    private exclude: string[] | null,
    private exclude_category: string[] | null,
    private exclude_test: string[] | null
    // TODO: Implement regex filters as extension
    // private regex_filters: boolean,
  ) {}

  /**
   * @brief Checks if a test case matches a given value based on the specified mode.
   *
   * @param test The test case to check.
   * @param value The value to match against.
   * @param mode The matching mode ("both" matches against either name or category, "category" matches only category, "name" matches only name).
   *
   * @returns True if the test case matches the value, false otherwise.
   */
  private matches(
    test: TestCaseDefinition,
    value: string,
    mode: "both" | "category" | "name"
  ): boolean {
    if (mode === "category") {
      return test.category === value;
    }
    if (mode === "name") {
      return test.name === value;
    }
    return test.name === value || test.category === value;
  }

  /**
   * @brief Checks if a test case is included based on the inclusion criteria.
   *
   * @param test The test case to check.
   *
   * @returns True if the test case is included, false otherwise.
   */
  private is_included(test: TestCaseDefinition): boolean {
    if (this.include === null && this.include_category === null && this.include_test === null) {
      return true;
    }

    if (this.include !== null) {
      for (const pattern of this.include) {
        if (this.matches(test, pattern, "both")) {
          return true;
        }
      }
    }

    if (this.include_category !== null) {
      for (const pattern of this.include_category) {
        if (this.matches(test, pattern, "category")) {
          return true;
        }
      }
    }

    if (this.include_test !== null) {
      for (const pattern of this.include_test) {
        if (this.matches(test, pattern, "name")) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * @brief Checks if a test case is excluded based on the exclusion criteria.
   *
   * @param test The test case to check.
   *
   * @returns True if the test case is excluded, false otherwise.
   */
  private is_excluded(test: TestCaseDefinition): boolean {
    if (this.exclude !== null) {
      for (const v of this.exclude) {
        if (this.matches(test, v, "both")) {
          return true;
        }
      }
    }
    if (this.exclude_category !== null) {
      for (const v of this.exclude_category) {
        if (this.matches(test, v, "category")) {
          return true;
        }
      }
    }
    if (this.exclude_test !== null) {
      for (const v of this.exclude_test) {
        if (this.matches(test, v, "name")) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * @brief Filters the provided test cases based on the inclusion and exclusion criteria.
   *
   * @param tests The array of test cases to filter.
   *
   * @returns Test cases that should be run and test cases that were filtered out.
   */
  filter(tests: TestCaseDefinition[]): {
    tests_to_run: TestCaseDefinition[];
    filtered_out: TestCaseDefinition[];
  } {
    const tests_to_run: TestCaseDefinition[] = [];
    const filtered_out: TestCaseDefinition[] = [];

    for (const test of tests) {
      if (this.is_included(test) && !this.is_excluded(test)) {
        tests_to_run.push(test);
      } else {
        filtered_out.push(test);
      }
    }
    return { tests_to_run, filtered_out };
  }
}
