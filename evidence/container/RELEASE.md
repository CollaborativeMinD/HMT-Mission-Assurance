# Container derivative qualification

Version: 0.1.1+container.1. Baseline commit b4f8324d84766d40a4b8104b47cf7716dd57c1b5.
Final checks rerun November 3, 2026; see final/ for fresh receipts.

PASS: 77 tests, 97.50% branch-inclusive coverage; Ruff, format, pyrefly,
structure, generated examples and dashboard parity. Native Prometheus and
Alertmanager prior receipts validate the exact monitoring inputs recorded in
monitoring-inputs.sha256; all ten hashes rechecked after environment restoration.
The temporary native binaries were lost during restoration, so no later native
rerun is claimed. Earlier schema.log failure is retained; final/examples.log
records recovery after regeneration for the derivative version.

HOLD: Docker image build/startup, OS isolation, mounted secret UID access,
restart/persistence, actual scrape network, Grafana rendering, external alert
receiver delivery and image vulnerability qualification. No live infrastructure
was accessed or changed. Alertmanager has a deliberate empty local receiver.
Browser capture was blocked by missing Playwright browser; no new screenshot
is claimed. HTTP deadline is cooperative, not CPU preemption.

Root evidence files predate this derivative and remain historical baseline
records, not a seal for changed code. SHA256SUMS.container enumerates this
packaged derivative independently. No private upstream archive is included.
