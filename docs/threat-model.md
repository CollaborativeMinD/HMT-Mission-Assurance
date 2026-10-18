# Trust and authority boundary

The server is a local stdio process under the MCP host's OS identity. The host chooses what evidence to disclose. The application has no target path argument, filesystem reader, URL fetcher, subprocess adapter, attack runner, model provider, plugin loader, or repository writer. Fixed report templates are bundled application assets. Local CLI report writing and skill installation are separate explicit actions.

| Threat | Implemented boundary | Residual limit |
| --- | --- | --- |
| Instructions hidden in evidence | No LLM/interpreter; evidence is parsed as bounded data; skill tells the host not to follow embedded instructions | The host agent must uphold its own instruction hierarchy |
| Shell/URL/path payload | Source references are inert strings; no target I/O adapters | The host may separately possess dangerous tools |
| Witness laundering | Narrative cannot pass; hashes, context, time, and scenario links checked | A dishonest producer can forge a matching executed record |
| Disposition injection | No caller-supplied result field; all calls recompute | Caller controls declared claims and exclusions |
| Optimistic overwrite | Conflicts and integrity blockers outrank passing observations | Evidence omitted by the caller cannot be detected |
| HTML/script injection | JSON script-breakout escaping, textContent rendering, restrictive CSP, no network | The browser and local environment remain trusted |
| Resource exhaustion | Record, string, count, and 1 MiB application-input bounds; no transitive path enumeration | SDK parses a stdio message before the application limit; no OS memory/CPU sandbox is provided |
| Cross-call leakage | No application evaluation state or per-user storage | MCP protocol connection state and the host's logs are outside that claim |
| Registry/supply-chain compromise | uv lock and CI against pinned resolutions; install by reviewed commit supported | Dependency integrity is not dependency security certification |

Tool annotations declare read-only/idempotent intent; they are not access-control enforcement. OS isolation remains the operator's responsibility. No HTTP service, remote authentication, multi-tenant hosting, authorization server, or production deployment claim is made. These boundaries are deliberately narrower than an end-to-end zero-trust security architecture.

Report data is sensitive to the extent the caller's records are sensitive. Redact before submission. Errors do not echo field values. The server does not log evidence bodies itself; an MCP host may log inputs and outputs. Duplicate JSON keys are rejected in the CLI and witness bodies; the MCP SDK has already parsed outer request JSON, so duplicate-key detection at that transport boundary is not claimed.
