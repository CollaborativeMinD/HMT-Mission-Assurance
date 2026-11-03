# Native monitoring qualification

Scope: offline parsing and rule evaluation only. No containers, listeners,
live infrastructure, credentials, or outbound notification receivers were used.

Official release assets downloaded to `/tmp/hmt-monitoring-tools`:

- https://github.com/prometheus/prometheus/releases/download/v3.13.5/prometheus-3.13.5.linux-amd64.tar.gz
- https://github.com/prometheus/alertmanager/releases/download/v0.34.2/alertmanager-0.34.2.linux-amd64.tar.gz

SHA-256 verified against https://prometheus.io/download/ before execution:

- Prometheus: `0388822ace519c5a3a8ef556a541ce1b536e21d872f82deded465bd27a5a0699`
- Alertmanager: `17ee14acd0f6ba6e25a436ff223d9c17ddd5cf484f543ad12f0932eaa89ba186`

Commands and results:

1. `promtool --version`: 3.13.5, recorded in `promtool-version.log`.
2. `promtool check config --syntax-only deploy/prometheus/prometheus.yml`: PASS.
3. `promtool check rules deploy/prometheus/rules.yml`: PASS, three rules.
4. From `deploy/prometheus`, `promtool test rules rules.test.yml`: PASS,
   six scenarios covering outage hold duration, healthy availability/errors,
   repeated errors, slow latency hold duration, healthy latency, and exception-only failures.
5. `amtool --version`: 0.34.2, recorded in `amtool-version.log`.
6. `amtool check-config deploy/alertmanager/alertmanager.yml`: PASS, one receiver.
7. Full `promtool check config` on a temporary host-path-adapted copy: PASS.
   Only `/etc/prometheus/rules.yml` was replaced with its checkout path and
   `/run/secrets/metrics_token` with a synthetic noncredential text fixture.
   The committed configuration was not changed for this check.

The exact committed Prometheus config received syntax validation, while file
reference checking required host-path adaptation because no Docker daemon is
available. This does not prove container mount permissions or network reachability.
The initial native validation passed, but review found missing exception-status coverage.
See monitoring-rrca.md for the bounded repair and added regression witness.
All six native scenarios pass after repair.

Static Compose mount review:

- `./deploy/prometheus:/etc/prometheus:ro` includes config, rules and rule tests.
- Prometheus secret `metrics_token` maps to its configured credentials_file.
- `./deploy/alertmanager:/etc/alertmanager:ro` matches Alertmanager command.
- Grafana provisioning bind includes `datasources/prometheus.yml` and
  `dashboards/hmt.yml`; the latter points to `/var/lib/grafana/dashboards`,
  matching the separate dashboard bind mount.
- Service names match scrape, alert routing, and Grafana datasource URLs.
- Host secret file readability for numeric service UIDs remains a deployment
  precondition; this offline check does not prove it.

Logs are adjacent. `monitoring-inputs.sha256` identifies the validated config,
rule fixture, dashboard artifacts, and inspected Compose file.
