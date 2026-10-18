# hmt-mission-assurance

**Stop asking your AI agent whether your system is good. Give it a contract for determining what the evidence actually supports.**

One repository. One `SKILL.md`. Four read-only MCP tools. One typed evaluation contract.

HMT Mission Assurance separates observed failures from untested claims, derives falsifiable requirements, and returns a delta report with evidence references and a traceability graph. It produces **evaluation findings, not a security certification**. A passing scoped assessment never authorizes deployment or promotion.

## Install

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv tool install 'git+https://github.com/CollaborativeMinD/HMT-Mission-Assurance.git'
hmt-mission-assurance --version
hmt-mission-assurance install-skill
```

If your shell cannot find the installed command, run `uv tool update-shell`, then open a new shell. MCP hosts can use the executable's absolute path.

The skill installer creates `hmt-mission-assurance/SKILL.md` beneath `$CODEX_HOME/skills` (or `~/.codex/skills`). It refuses to replace an existing skill. For another skill-compatible agent, select its skill directory explicitly:

```bash
hmt-mission-assurance install-skill --dest /path/to/your/agent/skills
```

Repository access is required while this GitHub repository is private. A package-index release is **not** required for the Git install above; `uv tool install hmt-mission-assurance` is not claimed to work until a registry release exists. For a fixed release, pin a reviewed commit with `git+https://github.com/CollaborativeMinD/HMT-Mission-Assurance.git@COMMIT_SHA`.

## Point an agent at a project

Invoke `$hmt-mission-assurance` and provide a project path plus a specific claim and baseline. The agent reads authorized project artifacts using its host tools, selects existing execution witnesses, and constructs the contract. The evaluator does not autonomously crawl or execute a project. Missing witnesses are a useful finding.

> Use $hmt-mission-assurance on /work/gateway at commit abc123. Assess whether expired tokens are rejected without weakening valid-token behavior. Derive requirements for anything the evidence cannot establish. Save the delta report.

For an immediate CLI demonstration:

```bash
hmt-mission-assurance example > contract.json
hmt-mission-assurance evaluate contract.json --out first-report
# Exit 2 is expected: the starter intentionally lacks failure-mode witnesses.
```

Open `first-report/delta-report.html`, or read its Markdown and JSON companions. The HTML is self-contained and makes no external requests. It provides Graph, Findings, Paths, Couplings, Requirements, Evidence, and Record tabs. Search nodes, adjust zoom, and select a node to inspect its connections. Paths are declared witness chains, not exhaustive execution paths.

## Connect MCP

Add this server to any MCP host supporting local stdio:

```json
{
  "mcpServers": {
    "hmt-mission-assurance": {
      "command": "hmt-mission-assurance-mcp",
      "args": []
    }
  }
}
```

Use the executable's absolute path if the host does not inherit your tool directory in `PATH`. No HTTP endpoint or hosted service is included. Each tool accepts `{"contract": {...}}` and recomputes from the complete contract. There are no evaluation sessions, caches, cross-call state, credentials, or model calls.

| Tool | Result |
| --- | --- |
| `inspect_baseline` | Applicable evidence and matching submitted scenario observations |
| `evaluate_coverage` | Gaps, contradictions, coverage counts, and one primary disposition |
| `derive_requirements` | Stable requirements, acceptance thresholds, and regression obligations |
| `emit_delta_report` | Structured evaluation, Markdown tables, Mermaid flow, and offline HTML graph |

The MCP tools write nothing. The optional CLI writes only explicitly requested new report directories or skill installations.

## Five dispositions

| Disposition | Meaning |
| --- | --- |
| `STABLE_AS_IS` | Current supplied witnesses match every declared scenario and coverage-mode obligation |
| `UPDATE_REQUIRED` | A usable execution record contradicts a nonblocking expected observation |
| `SEMANTIC_DRIFT_DETECTED` | A usable record contradicts a declared semantic expectation |
| `HOLD` | A hash mismatch, conflicting witnesses, or witnessed blocking-invariant failure prevents progression |
| `INSUFFICIENT_EVIDENCE` | Evidence or a positive, negative, or regression obligation is missing or unusable |

Exactly one primary disposition is selected. The explicit precedence is HOLD → SEMANTIC_DRIFT_DETECTED → UPDATE_REQUIRED → INSUFFICIENT_EVIDENCE → STABLE_AS_IS. Supporting findings remain visible. An update disposition permits a proposal, not promotion.

## A small before-and-after

| Stage | Claim/evidence | Assessment |
| --- | --- | --- |
| Weak evaluation | “The gateway is secure; valid-token test passes.” | The broader claim is unsupported |
| Structured before | Valid-token witness present; invalid-token and regression witnesses absent | `INSUFFICIENT_EVIDENCE`; collect the two missing witnesses |
| Reproduced gap | Invalid token produces `allowed`; contract expects `denied` | `UPDATE_REQUIRED`; propose a bounded correction and retain regression obligations |
| Corrected assessment | Current records match valid, invalid, and regression scenarios | `STABLE_AS_IS` for those scenarios; broader security remains unestablished |

Run `uv run python scripts/build_examples.py` to regenerate these illustrative contracts and reports. They are synthetic demonstrations, not a tested gateway product. See [examples](examples/) and [contract semantics](docs/contract.md).

## What the evidence supports

Pydantic v2 rejects unknown fields, coercions, unresolved references, duplicate IDs, invalid UTC timestamps, and bounded-size violations. The evaluator checks evidence content hashes, baseline/environment binding, freshness, case identity fields, and observed-versus-expected equality. Narrative-only records cannot satisfy execution obligations. Every derived requirement retains its baseline contract digest and available evidence references.

**A caller can fabricate a matching record and hash.** This implementation checks submitted-record consistency; it does not authenticate producers, independently rerun tests, prove that a cited function executed, discover undeclared failure modes, establish causal improvement, or establish cross-domain generalization. Scenario counts are not whole-project test coverage or probabilistic confidence. Those limits also apply to the project's [self-assessment](evidence/).

The public package contains the method, reference code, synthetic examples, and its own validation evidence. It excludes the author's internal kernels, policy corpus, formula compendia, private integrations, and uploaded reference notebook. [Harness² review](docs/adjacent-work.md) records adjacent lessons without claiming novelty or equivalence.

## Develop and verify

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
uv run pytest --cov --cov-report=term-missing --cov-report=json:evidence/coverage.json
uv run python scripts/check_structure.py
uv run python scripts/check_reports.py
uv build
uv run python scripts/verify_install.py
```

To regenerate the complete gate receipts and SQLite ledgers, run `uv run python scripts/record_validation.py` after installing Playwright Chromium. This reruns all gates and emits the scoped self-assessment. Run `uv run python scripts/release_manifest.py` last to classify and hash the finalized source artifacts.

See [Runbook.md](Runbook.md) for operator procedures and [Agents.md](Agents.md) for authority and interception rules. Apache-2.0 covers only this published repository; excluded internal materials are not licensed by implication.
