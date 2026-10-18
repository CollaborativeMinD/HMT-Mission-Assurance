# Operator SOP

1. Install with the Git URL in README; run `hmt-mission-assurance --version`.
2. Install the skill into your agent's skill directory. Restart/reload the agent if it caches skill discovery. The skill text is self-contained; MCP is optional.
3. Configure the local stdio MCP command if desired. Confirm exactly four tools are discovered. Never expose this process as an unauthenticated remote service.
4. Name the baseline, scope, environment, UTC assessment time, claim, authority boundary, and limitations. Read authorized existing code/test/evidence artifacts. Do not execute target code through the evaluator.
5. Build an input from `schema` and `example`; bind observations to exact scenario expectations. Redact secrets. Record unverified authenticity as a limitation.
6. Call inspect → coverage → requirements → report, or use `evaluate contract.json --out NEW_DIRECTORY`.
7. Read the primary disposition and all findings. Confirm graph paths, omitted witnesses, regression obligations, and source hashes. Preserve the baseline if no measurable change is supported.
8. For a proposed correction, commission an external, authorized campaign. Supply new records under the new baseline. Never interpret this evaluator as deployment authorization.

| Symptom | Check and recovery |
| --- | --- |
| Exit 2 | Valid evaluation has findings; inspect JSON/Markdown. This is not a CLI crash |
| Exit 3 | Validate against `schema`; use UTC timestamps, globally unique IDs, and a new output directory |
| MCP INVALID_CONTRACT | Check exact `{"contract": ...}` envelope, schema, strict types, and 1 MiB cap; errors omit input values |
| MCP INPUT_TOO_LARGE | Reduce selected evidence; evaluate separate bounded scopes; do not truncate silently |
| Evidence hash mismatch | Re-read source bytes and hash the exact UTF-8 content; preserve the conflicting record until reconciled |
| Context/time mismatch | Obtain current evidence for the exact baseline/environment; do not rewrite timestamps to admit stale evidence |
| Conflicting witnesses | Reconcile case/environment and repeated-run variability; do not discard the failing record to obtain stability |
| Missing execution witness | Collect an authorized external run; never relabel prose as executed |
| Existing report/skill directory | Choose another destination; review before manually replacing anything |
| HTML blank | Enable local JavaScript or read Markdown/JSON; report has no CDN dependency |

Maintainers: run the verification commands in README after each code/contract change. Rebuild examples, schema, and validation evidence. Check the Cumulative Gate Ledger and Reverse RCA Ledger. Do not suppress failing checks or reduce thresholds to admit a release. CI executes the same bounded checks; inspect the actual run before claiming a hosted pass.
