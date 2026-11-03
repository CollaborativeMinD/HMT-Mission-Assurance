# Monitoring corrective action

Observed defect: static security review found `HMTMCPToolFailures` and the
Grafana tool error fraction filtered only `status="error"`, excluding the
transport's `status="exception"` internal failures. The initial native tests
covered ordinary errors but had no exception-only regression witness.

Root cause: monitoring assumed a two-state tool outcome model while transport
instrumentation emits success, error, and exception statuses.

Bounded repair: select `status=~"error|exception"` in the alert and dashboard,
add an exception-only native rule fixture, regenerate dashboard JSON, and
rerun native configuration/rules/tests plus dashboard schema parity tests.
The monitoring source schema and transport behavior remain unchanged.

Requirement MON-ERR-001: both ordinary tool errors and unexpected exceptions
must make HMTMCPToolFailures fire after its one-minute hold period, and both
must contribute to the dashboard error fraction. Regression witness:
`exception-only failures fire` in deploy/prometheus/rules.test.yml.

No production or hosted-runtime validation is claimed. Results are recorded
in the refreshed adjacent native validation logs and monitoring-validation.md.
