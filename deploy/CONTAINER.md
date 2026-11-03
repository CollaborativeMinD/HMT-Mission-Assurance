# Mission Assurance container derivative

## Scope

Derived from main b4f8324d84766d40a4b8104b47cf7716dd57c1b5 (0.1.1).
Reference: HMT_Agentic_Control_Loop_v1.3.6.zip SHA256 f21251045780e17e343979e73f1059cc94fcc913c4f31020419b3a06ef5f5ed0, embedded FastAPI backend 1.0.0.
Reused composition principles: strict settings, injected evaluator, lifespan-owned service, bounded transport, no authority in HTTP. Reference files are not shipped or imported.

Core four tools and evaluation schema are unchanged. Default container uses optional authenticated stateless Streamable HTTP at /mcp. No fake REST tool route. Original stdio remains usable with an entrypoint override. All tool outputs remain advisory and read-only; no models, databases, execution or promotion powers added.

## Interfaces

- 127.0.0.1:8000/mcp: MCP protocol, bearer required.
- 127.0.0.1:8000/skills/hmt-mission-assurance: original skill text, bearer required.
- /health/live: process liveness, bearer required, not mission/target readiness.
- mcp:9000/metrics: monitoring-only listener on private Docker network, distinct bearer.
- 127.0.0.1:3000: Grafana login. No Prometheus/Alertmanager host ports.

No remote TLS/auth gateway is included. Never publish these HTTP ports on public/peer interfaces; remote admission needs a separately reviewed TLS identity boundary. This bearer configuration is for trusted operator-managed local clients, not generic OAuth discovery or multitenancy. One worker/process. Do not enable proxy-header trust or anonymous Grafana.

## Clone, test, build

Requires Git, uv, Python 3.12+ and Docker Desktop using Linux containers
(or Docker Engine with Compose v2 on Linux). Start Docker and confirm
`docker info` succeeds before building. The application tests do not require Docker.

```sh
git clone --branch container/mission-assurance-monitoring https://github.com/CollaborativeMinD/HMT-Mission-Assurance.git
cd HMT-Mission-Assurance
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
uv run pytest --cov --cov-report=term-missing
uv run python scripts/check_structure.py
uv build
uv run python scripts/verify_install.py
docker info
docker build --pull -t hmt-mission-assurance:0.1.1-container.1 .
```

The branch is explicit until its review is merged. These commands work in
PowerShell and a POSIX shell. Browser screenshot tests additionally require
`uv run playwright install chromium`, followed by
`uv run python scripts/check_reports.py`; no browser test pass is implied here.
Building an image does not start services or require runtime credentials.

## Owner setup (not performed by builder)

Provide three different high-entropy secrets named mcp_token, metrics_token, grafana_password in an owner-only directory outside the repository. No actual credentials are generated, embedded, or saved by this bundle. MCP/metrics strings must be 32–512 ASCII non-whitespace characters. Container numeric UIDs require read permission to their mounted files. For local Compose, use an owner-only 0700 directory and read-only 0444 files inside it, then bind through secrets; ensure no untrusted host user can traverse the parent. Secret mounts alone are not encrypted storage. Validate host ownership and secret admission before startup.

Set HMT_SECRET_DIR to that absolute directory. In PowerShell use
`$env:HMT_SECRET_DIR = 'C:\path\to\private-secrets'`; in a POSIX shell use
`export HMT_SECRET_DIR=/path/to/private-secrets`. On Windows, restrict the
folder with Windows ACLs; POSIX chmod is not a Windows ACL check. Confirm the
Linux containers can read the supplied secret mounts without broadening host access.
Do not put secrets in the repository or print them in logs.

Then start the isolated Compose project (ports 8000 and 3000 must be free):

```sh
docker compose config --quiet
docker compose build --pull
docker compose up -d
docker compose ps
docker compose logs --tail 100 mcp prometheus alertmanager grafana
```

Grafana initial username is admin; password comes from its secret file. Existing Grafana volumes retain prior credentials. Do not treat changing the file as password rotation. Scrape token and MCP token are separate capabilities; the metrics token cannot call tools.

A stdio-only invocation can override entrypoint and disable networking:

```sh
docker run --rm -i --read-only --network none --cap-drop ALL --security-opt no-new-privileges --pids-limit 64 --memory 512m --cpus 1 --entrypoint hmt-mission-assurance-mcp hmt-mission-assurance:0.1.1-container.1
```

## Bounds and limits

1 MiB MCP envelope cap before SDK parsing, strict existing contract bounds, 4 active HTTP requests per listener by default, 30-second cooperative deadline and 5-second keepalive. Synchronous evaluator CPU cannot be preempted by asyncio timeout; Docker CPU/memory limits are backstops, not proven latency guarantees. MCP listener and metrics listener share process CPU. Runtime isolation and overload behavior must be qualified on target Docker.

No cAdvisor/host-root/Docker-socket mounts. Process/container resource monitoring is not claimed. No extra Prometheus MCP bridge: monitoring does not require granting another agent data-source access. Alertmanager empty receiver is deliberately local-only; external delivery needs explicit recipient/routing configuration.

## Runtime qualification (HOLD until executed)

Verify image build, health, skills, all four MCP tools via real client, wrong/no-token denial, metric tool/error counts, scrape up==1, Grafana dashboard data and alert transitions. Confirm unauthorized peer cannot reach host ports; containers cannot reach public network; metrics port unpublished; mounts/read-only/caps/resources match compose; restart persistence works. Run native promtool/amtool checks described in MONITORING.md. Check platform digests and vulnerability scan before promotion. No production-ready assertion until these have receipts.

## Stop and troubleshoot

`docker compose down` stops this project and keeps its named data volumes.
Do not add `--volumes` unless you explicitly intend to delete its stored data.
If Docker cannot boot or `docker info` fails, resolve that host issue before
running this workflow; do not reset Docker or remove unrelated containers.
A failed build, unhealthy MCP service, missing dashboard data, or permission
error is a failed runtime gate, not a qualified deployment. Read this project's
logs and verify secret filenames, readability, distinct token values and free
ports. The Grafana dashboard is provisioned automatically after login.
