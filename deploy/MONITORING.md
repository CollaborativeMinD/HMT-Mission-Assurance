# Local monitoring bundle

The MCP metrics listener is private at `mcp:9000/metrics`, with a dedicated bearer
secret mounted into Prometheus at `/run/secrets/metrics_token`. It must not be
published as a host port. Metrics labels contain only bounded tool names and
status, never prompts, evidence, tokens, user identities, or paths.

Prometheus scrapes every 15 seconds and evaluates availability, tool failure,
and p95 execution latency alerts. Alertmanager routes every alert to an empty
`local-only` receiver. Alerts can be inspected locally; no email, webhook, or
external notification delivery is configured or claimed.

The Grafana data source uses the private Prometheus service. Dashboards are
provisioned read-only from `grafana/dashboards`. The custom source contract is
`grafana/dashboard.spec.json`; `grafana/dashboard.schema.json` defines its
versioned schema. Regenerate and verify with:

```sh
uv run python deploy/grafana/build_dashboard.py
uv run python deploy/grafana/build_dashboard.py --check
uv run pytest tests/test_dashboard_schema.py
```

The custom schema is a small repository-owned dashboard specification, not a
claim of validating every Grafana option. The generator renders Grafana's
classic JSON dashboard representation. Empty rate panels before the first tool
call are expected. Scrape health is not an end-to-end MCP authentication probe.

Run Prometheus native checks inside the pinned container (or equivalent local
`promtool`), with this directory mounted at `/etc/prometheus`:

```sh
promtool check config /etc/prometheus/prometheus.yml
promtool check rules /etc/prometheus/rules.yml
cd /etc/prometheus && promtool test rules rules.test.yml
amtool check-config /etc/alertmanager/alertmanager.yml
```

`prometheus/prometheus.yml`, `prometheus/rules.yml`, and the test file must be
mounted together. Alertmanager uses its separate configuration directory.
The config check also needs the metrics token mount. Do not replace it with a
real credential in version control.

## Version evidence

Version candidates verified against official release pages on 2026-11-03:

- Prometheus `3.13.5` (LTS): https://prometheus.io/download/
- Alertmanager `0.34.2`: https://prometheus.io/download/
- Grafana `13.2.4`: https://github.com/grafana/grafana/releases/tag/v13.2.4

Container references: `prom/prometheus:v3.13.5`,
`prom/alertmanager:v0.34.2`, `grafana/grafana:13.2.4`.
Release existence is not an image pull, image-digest verification, vulnerability
scan, or successful live deployment. Tags should be resolved to reviewed digests
for production. Review https://prometheus.io/docs/alerting/latest/configuration/
before adding any authorized external receiver.
