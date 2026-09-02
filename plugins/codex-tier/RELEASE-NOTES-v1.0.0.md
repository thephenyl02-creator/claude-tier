# Codex Tier v1.0.0

Codex Tier is a quality-first model × reasoning-effort router for Codex. It
routes work through deterministic tools, ordinary direct execution, or an
explicitly pinned worker, then verifies results and escalates only when the
required quality is not met.

For the five stabilized v1 workload profiles, the released policy pins
`gpt-5.6-sol/low` regardless of the invoking session's model and effort.
Ordinary `DIRECT` semantics remain available for workloads without a validated
pinned route.

## Scoped benchmark result

The **final-route derived comparison** uses hash-compatible authoritative
Sol/low and Sol/max observations; it is not a new post-correction Tier
benchmark run. Across the five tested workloads, it implies a **13.82% median**
and **15.52% mean exposed-token reduction versus always Sol/max**, with **100%
quality-gate pass rates** for both pairs and median workload quality of
`94 / 94`.

The directly measured pre-final-route Tier comparison remains separately
reported at **9.83% median** and **12.57% mean exposed-token reduction versus
always Sol/max**.

These are exposed-token, or token-usage proxy, results. They are not claims
about Codex credits, billing, dollars, or the five-hour usage quota.

## Limitations

- The evidence covers a fixed workload, repository, model, and verifier
  environment.
- Exposed-token usage is a proxy rather than account consumption or billing.
- Security review had a quality-score gap even though both compared conditions
  passed the quality gate.
- Architecture has fewer Sol/max observations than the other workloads.

See the [authoritative consolidated benchmark report](../../benchmarks/codex-tier-e2e/CONSOLIDATED-BENCHMARK-REPORT.md)
for hashes, provenance, superseded results, and the full interpretation.
