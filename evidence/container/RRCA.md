# Container derivative RRCA

Baseline b4f8324d84766d40a4b8104b47cf7716dd57c1b5; historical evidence remains baseline-only.

- RC-C01: first uv sync failed because default home cache was read-only. Set UV_CACHE_DIR=/tmp/uv-cache; hydration succeeded. No dependency pin bypass.
- RC-C02: HTTP tracer first passed actual four-tool MCP wire/metrics assertions, then failed skill endpoint with FileNotFoundError under editable install. Cause: SKILL.md is wheel force-include, absent from editable package data. Reused baseline CLI skill_text fixed-resource fallback. Regression now exercises authenticated skill endpoint; installed-wheel verification required separately.
- RC-C03: Ruff identified unused import and import ordering; deterministic cleanup applied. No suppressions introduced.

HOLD-CONTAINER: Docker daemon/executable unavailable. Images are registry digest-pinned but not built/pulled/run here. No startup, UID/volume permissions, network isolation, restart or resource-enforcement claim is made.

- RC-C04: independent review found relocation of builder virtualenv would retain stale absolute console-script shebangs. Builder now creates /opt/venv and runtime copies to identical path. Static path witness added; actual image startup remains HOLD.
- RC-C05: identical supplied MCP/metrics secrets would collapse distinct capability boundaries. Startup now rejects equality; tests use distinct fixtures and prove swapped credentials denied.
- RC-C06: independent review identified operational exception metric omitted from error-only alert/dashboard expressions. Monitoring repair includes exception status plus native rule regression.
- RC-C07: cooperative asyncio timeout cannot interrupt synchronous evaluator. Explicit blocking witness confirms this limitation; documentation forbids hard latency guarantee. Container resource/backpressure qualification remains HOLD.
