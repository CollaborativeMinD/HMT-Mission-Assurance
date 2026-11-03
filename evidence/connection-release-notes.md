# 0.1.1 validation scope and engineering observations

Baseline: 14d519ad33cf30bb27e33b87c7d80cc4c5b6ff59 (0.1.0).
Requirement: REQ-HOST-011 in docs/requirements.md.

- Baseline run: 63 pytest cases passed before changes.
- The first expanded protocol check incorrectly required the report evaluation's
  graph to equal evaluate_coverage's graph. Inspection of reports.py showed the
  documented report route adds the full declared graph. The check now compares
  the common evaluation fields and separately requires a report graph. Evaluator
  behavior was preserved; no production repair was needed.
- The first manifest update exceeded the repository's 60-line function limit.
  The cumulative architecture gate recorded FAIL. Inventory assembly was split
  into a focused function, then the cumulative gates were rerun.
- Playwright's default Chromium and headless-shell downloads returned invalid
  empty archives. For local browser checks, Chromium 153.0.0 was obtained from
  the @sparticuz/chromium npm package; the existing browser gate accepts an
  explicit executable and serverless launch flags. This is a local environment
  choice, not a new runtime/package dependency or an assertion about hosted CI.
- The old validation runner appended a fresh PASS for a historical skill-forward
  receipt without executing that campaign again. That unconditional insertion was
  removed. Historical evidence remains available and is not reattested by 0.1.1.
- Profile and installed-package witnesses are recorded in connections.json and
  install.json. Signed-in agent clients are unavailable; no client UI or model
  tool-selection campaign was run. This remains an explicit unverified item.

The four tool schemas, skill bytes, read-only server behavior, Apache-2.0 license,
and assurance limitations are unchanged. Versioned synthetic reports are
regenerated for evaluator version 0.1.1; they remain synthetic examples.
