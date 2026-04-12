/**
 * @brief Generates an HTML report from the test execution results.
 *
 * @Note !!This module was not part of the project assignment!!
 * I wanted to try out of how difficult it would be for an AI agent
 * to create a module like this.
 *
 * @author Marek Gašpierik (xgaspim00)
 *
 * @usage Use -h / --help while running the tester for usage instructions.
 *
 * @details It takes a TestReportJSON object, which contains the results of test execution,
 * and produces a styled HTML report that summarizes the results and provides
 * detailed information for each test case.
 *
 * The report includes a summary section with overall statistics,
 * as well as sections for executed categories and unexecuted tests.
 *
 * The HTML is designed to be clean and easy to navigate,
 * with badges indicating test results and expandable details for each test case.
 *
 * @ai_usage_notice The author used AI to create this module
 * @ai_usage_details Details about AI usage can be found in the root of this project in the file ai-github_copilot.pdf
 */

import { readFileSync, writeFileSync } from "node:fs";

// Using the same types as defined in models.ts
export interface TestCaseDefinition {
  name: string;
  test_source_path: string;
  stdin_file?: string | null;
  expected_stdout_file?: string | null;
  test_type: number;
  description?: string | null;
  category: string;
  points: number;
  expected_parser_exit_codes?: number[] | null;
  expected_interpreter_exit_codes?: number[] | null;
}

export interface UnexecutedReason {
  code: number;
  message: string | null;
}

export interface TestCaseReport {
  result: "passed" | "parse_fail" | "int_fail" | "diff_fail";
  parser_exit_code: number | null;
  interpreter_exit_code: number | null;
  parser_stdout: string | null;
  parser_stderr: string | null;
  interpreter_stdout: string | null;
  interpreter_stderr: string | null;
  diff_output: string | null;
}

export interface CategoryReport {
  total_points: number;
  passed_points: number;
  test_results: Record<string, TestCaseReport>;
}

export interface TestReportJSON {
  discovered_test_cases: TestCaseDefinition[];
  unexecuted: Record<string, UnexecutedReason>;
  results?: Record<string, CategoryReport>;
}

function escapeHtml(str: string | null | undefined): string {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatResultBadge(result: string): string {
  const map: Record<string, { label: string; padding: string }> = {
    passed: { label: "Passed", padding: "badge-success" },
    parse_fail: { label: "Parse Failed", padding: "badge-error" },
    int_fail: { label: "Interpreter Failed", padding: "badge-error" },
    diff_fail: { label: "Output Mismatch", padding: "badge-error" },
  };

  const info = map[result] || { label: result, padding: "badge-neutral" };
  return `<span class="badge ${info.padding}">${escapeHtml(info.label)}</span>`;
}

interface ReportStats {
  totalTests: number;
  passedTests: number;
  totalPoints: number;
  passedPoints: number;
  unexecutedCount: number;
}

function calculateStats(report: TestReportJSON): ReportStats {
  let totalTests = 0;
  let passedTests = 0;
  let totalPoints = 0;
  let passedPoints = 0;

  for (const catData of Object.values(report.results ?? {})) {
    totalPoints += catData.total_points;
    passedPoints += catData.passed_points;
    for (const testResult of Object.values(catData.test_results)) {
      totalTests++;
      if (testResult.result === "passed") passedTests++;
    }
  }

  const unexecutedCount = Object.keys(report.unexecuted).length;

  return { totalTests, passedTests, totalPoints, passedPoints, unexecutedCount };
}

function generateCss(): string {
  return `
    :root {
      --bg-color: #f8fafc;
      --text-color: #1e293b;
      --card-bg: #ffffff;
      --border-color: #e2e8f0;
      --success-bg: #dcfce7;
      --success-text: #166534;
      --error-bg: #fee2e2;
      --error-text: #991b1b;
      --neutral-bg: #f1f5f9;
      --neutral-text: #475569;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-color);
      line-height: 1.6;
      margin: 0;
      padding: 0;
    }
    .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
    header { margin-bottom: 2rem; border-bottom: 2px solid var(--border-color); padding-bottom: 1rem; }
    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .stat-card {
      background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px;
      padding: 1.5rem; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stat-card h3 { margin: 0 0 0.5rem 0; font-size: 1rem; color: var(--neutral-text); }
    .stat-card p { margin: 0; font-size: 2rem; font-weight: bold; }
    .category {
      background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px;
      padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .category-header {
      display: flex; justify-content: space-between; align-items: center;
      border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; margin-bottom: 1rem;
    }
    .category-title { margin: 0; font-size: 1.5rem; }
    .badge {
      display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px;
      font-size: 0.875rem; font-weight: 600;
    }
    .badge-success { background: var(--success-bg); color: var(--success-text); }
    .badge-error { background: var(--error-bg); color: var(--error-text); }
    .badge-neutral { background: var(--neutral-bg); color: var(--neutral-text); }
    details.test-item {
      background: var(--neutral-bg); border: 1px solid var(--border-color);
      border-radius: 6px; margin-bottom: 0.5rem; overflow: hidden;
    }
    details.test-item > summary {
      padding: 1rem; cursor: pointer; display: flex; justify-content: space-between;
      align-items: center; font-weight: 600; user-select: none;
    }
    details.test-item > summary:hover { background: #e2e8f0; }
    details.test-item > summary > div:first-child { display: flex; align-items: center; gap: 0.5rem; }
    .test-details { padding: 1rem; background: var(--card-bg); border-top: 1px solid var(--border-color); }
    .output-section { margin-top: 1rem; }
    .output-section h4 {
      margin: 0 0 0.5rem 0; color: var(--neutral-text); font-size: 0.875rem;
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    pre {
      background: #1e1e1e; color: #d4d4d4; padding: 1rem; border-radius: 6px;
      overflow-x: auto; font-size: 0.875rem; margin: 0;
    }
    .empty-output { color: var(--neutral-text); font-style: italic; }
  `;
}

function generateSummaryGrid(stats: ReportStats): string {
  const isPerfect = stats.passedTests === stats.totalTests && stats.totalTests > 0;
  const passedBadge = isPerfect ? "badge-success" : "";

  return `
    <div class="summary-grid">
      <div class="stat-card">
        <h3>Total Tests Executed</h3>
        <p>${String(stats.totalTests)}</p>
      </div>
      <div class="stat-card">
        <h3>Tests Passed</h3>
        <p class="${passedBadge}" style="border-radius:6px; background-color: transparent;">
          ${String(stats.passedTests)} / ${String(stats.totalTests)}
        </p>
      </div>
      <div class="stat-card">
        <h3>Points</h3>
        <p>${String(stats.passedPoints)} / ${String(stats.totalPoints)}</p>
      </div>
      <div class="stat-card">
        <h3>Unexecuted Tests</h3>
        <p>${String(stats.unexecutedCount)}</p>
      </div>
    </div>`;
}

function generateTestOutputHtml(title: string, content: string | null): string {
  if (!content || content.trim() === "") return "";
  return `
    <div class="output-section">
      <h4>${title}</h4>
      <pre><code>${escapeHtml(content)}</code></pre>
    </div>`;
}

function generateTestCaseHtml(testName: string, testResult: TestCaseReport): string {
  const isPassed = testResult.result === "passed";
  const openAttr = isPassed ? "" : "open";

  const pCode = testResult.parser_exit_code ?? "N/A";
  const iCode = testResult.interpreter_exit_code ?? "N/A";
  const pCodeStr = typeof pCode === "number" ? String(pCode) : pCode;
  const iCodeStr = typeof iCode === "number" ? String(iCode) : iCode;

  let detailsHtml = "";
  detailsHtml += generateTestOutputHtml("Diff Output", testResult.diff_output);
  detailsHtml += generateTestOutputHtml("Parser Stdout", testResult.parser_stdout);
  detailsHtml += generateTestOutputHtml("Parser Stderr", testResult.parser_stderr);
  detailsHtml += generateTestOutputHtml("Interpreter Stdout", testResult.interpreter_stdout);
  detailsHtml += generateTestOutputHtml("Interpreter Stderr", testResult.interpreter_stderr);

  if (detailsHtml === "") {
    detailsHtml = `<p class="empty-output">No additional output provided for this test case.</p>`;
  }

  return `
    <details class="test-item" ${openAttr}>
      <summary>
        <div>
          <span>${formatResultBadge(testResult.result)}</span>
          <span>${escapeHtml(testName)}</span>
        </div>
        <span>
          <small>Exit Codes: ${pCodeStr} (Parser) | ${iCodeStr} (Int)</small>
        </span>
      </summary>
      <div class="test-details">
        ${detailsHtml}
      </div>
    </details>`;
}

function generateExecutedCategoriesHtml(results?: Record<string, CategoryReport>): string {
  if (!results) return "";

  let html = "";
  for (const [catName, catData] of Object.entries(results)) {
    html += `
    <div class="category">
      <div class="category-header">
        <h2 class="category-title">${escapeHtml(catName)}</h2>
        <span><strong>${String(catData.passed_points)}</strong> / ${String(catData.total_points)} Points</span>
      </div>
      <div class="test-list">`;

    for (const [testName, testResult] of Object.entries(catData.test_results)) {
      html += generateTestCaseHtml(testName, testResult);
    }

    html += `
      </div>
    </div>`;
  }
  return html;
}

function generateUnexecutedHtml(
  unexecuted: Record<string, UnexecutedReason>,
  count: number
): string {
  if (count <= 0) return "";

  let html = `
    <div class="category">
      <div class="category-header">
        <h2 class="category-title">Unexecuted Tests</h2>
        <span>${String(count)} Total</span>
      </div>
      <div class="test-list">`;

  for (const [testName, reason] of Object.entries(unexecuted)) {
    html += `
      <details class="test-item">
        <summary>
          <div>
            <span class="badge badge-neutral">Skipped</span>
            <span>${escapeHtml(testName)}</span>
          </div>
          <span>Code: ${String(reason.code)}</span>
        </summary>
        <div class="test-details">
          <p><strong>Reason Message:</strong> ${escapeHtml(reason.message ?? "None provided")}</p>
        </div>
      </details>`;
  }

  html += `
      </div>
    </div>`;
  return html;
}

export function generateHtmlReport(report: TestReportJSON): string {
  const stats = calculateStats(report);

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Test Execution Report</title>
  <style>
${generateCss()}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Test Execution Report</h1>
    </header>
    ${generateSummaryGrid(stats)}
    ${generateExecutedCategoriesHtml(report.results)}
    ${generateUnexecutedHtml(report.unexecuted, stats.unexecutedCount)}
  </div>
</body>
</html>`;
}

// Simple CLI execution
if (typeof process !== "undefined" && process.argv.length > 1) {
  const scriptName = process.argv[1] || "";
  if (scriptName.endsWith("htmlGenerator.ts") || scriptName.endsWith("htmlGenerator.js")) {
    const args = process.argv.slice(2);
    if (args.length < 1) {
      console.error("Usage: node htmlGenerator.js <path-to-report.json> [output-file.html]");
      process.exit(1);
    }

    const inputFile = args[0] as string;
    const outputFile = args.length > 1 ? (args[1] as string) : "report.html";

    try {
      const data = readFileSync(inputFile, "utf-8");
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      const jsonData = JSON.parse(data);
      const json = jsonData as TestReportJSON;

      const htmlOutput = generateHtmlReport(json);
      writeFileSync(outputFile, htmlOutput);
      console.log(`Successfully generated HTML report at ${outputFile}`);
    } catch (err) {
      console.error("Error generating HTML report:", err);
      process.exit(1);
    }
  }
}
