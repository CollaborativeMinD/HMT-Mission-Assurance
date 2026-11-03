# Agent connections and validation

HMT Mission Assurance 0.1.1 retains the existing local stdio MCP server and CLI.
The four configurations below launch the same installed executable. No HTTP
service, OAuth, credentials, model provider, persistent evaluation session, or
Agensi connection is required. The MCP protocol has a connection lifecycle;
**evaluation state** is stateless: every tool requires the entire contract and
recomputes its answer. A previous tool response is not authority for another call.

## Install once in the host execution environment

```bash
uv tool install 'git+https://github.com/CollaborativeMinD/HMT-Mission-Assurance.git@REVIEWED_COMMIT_SHA'
hmt-mission-assurance --version
```

Replace `REVIEWED_COMMIT_SHA` with the reviewed release commit. Version should be
`0.1.1`. Use `uv tool install --force` with the new reviewed commit to replace an
older installation. Installation retrieves the package and dependencies; evaluation
itself requires no network. No package-index publication is assumed.

If a GUI cannot resolve `hmt-mission-assurance-mcp`, put the installed executable's
absolute path in `command` (including `.exe` on Windows). `uv tool dir --bin` shows
the tool executable directory. Use JSON escaping for Windows paths, or forward
slashes. Keep paths and arguments separate; do not embed a shell command in
`command`. In WSL, SSH, containers, and remote workspaces, install the tool where
that host actually launches its stdio processes. A local path is not a remote URL.

Merge only the HMT entry into existing configurations. Do not replace unrelated
servers or automatically approve tools. Templates contain no user-specific paths
and are not automatically installed into a user's settings.

## Connection profiles

| Host | Shipped template | Destination |
| --- | --- | --- |
| Claude Code | `integrations/claude-code.mcp.json` | Workspace-root `.mcp.json` |
| Cursor | `integrations/cursor.mcp.json` | `.cursor/mcp.json`, or user `~/.cursor/mcp.json` |
| Codex CLI | `integrations/codex.config.toml` | Merge into `~/.codex/config.toml`, or trusted project `.codex/config.toml` |
| GitHub Copilot Agent mode in VS Code | `integrations/copilot.mcp.json` | `.vscode/mcp.json` (VS Code format) |

Claude Code and Cursor use a top-level `mcpServers` object with `type: "stdio"`,
`command: "hmt-mission-assurance-mcp"`, and `args: []`. Claude Code can also register
it through its CLI:

```bash
claude mcp add --scope project --transport stdio hmt-mission-assurance -- hmt-mission-assurance-mcp
claude mcp get hmt-mission-assurance
```

Review the workspace/server trust request, then use `/mcp` to check discovery.
For Cursor, merge the template and enable the server in its MCP settings. Confirm
four HMT tools appear. These commands/settings are host operations; the package
installer does not change them.

Codex uses TOML and infers stdio from `command` (do not add a JSON `type` field):

```toml
[mcp_servers.hmt-mission-assurance]
command = "hmt-mission-assurance-mcp"
args = []
```

Alternatively:

```bash
codex mcp add hmt-mission-assurance -- hmt-mission-assurance-mcp
codex mcp list
```

For VS Code Copilot, the shipped template uses top-level `servers`, with an explicit
`type: "stdio"`. Select Agent mode, trust the workspace as appropriate, use
**MCP: List Servers** to start HMT, and enable its tools in the agent's tool picker.
A listed configuration alone does not establish a successful tool call.

Current Copilot documentation also describes a portable workspace-root `.mcp.json`
with `mcpServers`. For that destination, use the shape in the Claude Code template,
not the VS Code `servers` wrapper. Pick one configuration route to avoid duplicate
servers. Organization policy or client version can restrict either route.

## Skill instructions are separate from tool discovery

Connecting MCP exposes four tools; it does not itself install `SKILL.md`. The
existing installer supports a chosen agent skill directory:

```bash
hmt-mission-assurance install-skill --dest /path/to/your/agent/skills
```

The default is `$CODEX_HOME/skills`, or `~/.codex/skills`. Select another host's
supported directory explicitly; the installer refuses to replace an existing skill.
For hosts without skill discovery, supply the repository's unchanged `SKILL.md`
as authorized instructions. Do not assume every client accepts Codex's `$skill`
invocation syntax.

## CLI route and operator acceptance

```bash
hmt-mission-assurance schema
hmt-mission-assurance example > contract.json
hmt-mission-assurance evaluate contract.json --out new-report-directory
```

The starter intentionally returns exit **2** (`INSUFFICIENT_EVIDENCE`). Exit **0**
means scoped matching evidence; **3** means invalid input or destination. The three
report files are `evaluation.json`, `delta-report.md`, and `delta-report.html`.
Existing destinations are refused. Without `--out`, evaluation JSON goes to stdout.
`hmt-mission-assurance serve` is an alternate stdio launch command; it is not HTTP.

In each real host, ask the agent to obtain the schema and starter through authorized
host tools, construct the complete contract, and call each of:

1. `inspect_baseline`
2. `evaluate_coverage`
3. `derive_requirements`
4. `emit_delta_report`

Each call uses `{"contract": <complete contract>}`. The starter must remain
`INSUFFICIENT_EVIDENCE`, with missing negative/regression witnesses and no invented
execution. Save returned reports only to the chosen destination using authorized
host tools. MCP writes nothing; the CLI's explicit report/skill writes are separate.

## What is validated

`uv run python scripts/verify_install.py` installs the built wheel into a temporary
uv tool environment. It parses all four shipped profiles, resolves their configured
console command to that installation, and launches real subprocesses outside the
source directory using the MCP Python SDK client. It checks initialization, exactly
four tools, read-only annotations, output-schema validity, all four calls, changed
contract isolation, deterministic replay, invalid/unknown-tool recovery, report
payloads, and an empty MCP working directory. A fresh process through `serve` must
reproduce the result. CLI checks cover schema/example, exit codes 0/2/3, report
files, and refusal to overwrite. Each protocol session has a 30-second bound.

Receipts are `evidence/connections.json` and `evidence/install.json`. The existing
cumulative installation gate runs this campaign in CI as well. To check an already
installed tool from a development checkout:

```bash
uv run python scripts/check_connections.py --bin-dir /absolute/path/to/tool/bin
```

These are installed-package and documented-profile tests, **not executions inside
signed-in Claude Code, Cursor, Codex CLI, or Copilot clients**. Those applications
were unavailable in the validation environment. Their UI, trust-policy handling,
model tool selection, and real-client acceptance remain unverified. The empty-cwd
check is not an exhaustive filesystem/network trace or an OS sandbox. Existing
architecture and source-reference tests provide additional bounded read-only checks.

Synthetic input fixtures test evaluator behavior, not an executed gateway. All
existing evidence limits, Apache-2.0 rights, read-only MCP boundaries, and
no-certification/no-deployment-authorization contracts remain unchanged.

## Host documentation consulted

Reviewed 2026-11-02 (Hawaii). Host configurations can change; record the client
version when completing real-host acceptance.

- Claude Code: https://code.claude.com/docs/en/mcp
- Cursor: https://cursor.com/docs/mcp
- Codex: https://developers.openai.com/codex/mcp
- Copilot/VS Code: https://code.visualstudio.com/docs/agents/reference/mcp-configuration
- Copilot setup: https://code.visualstudio.com/docs/agent-customization/mcp-servers
