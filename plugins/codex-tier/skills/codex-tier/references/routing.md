# Routing and selective escalation

Use this reference when a work unit needs a routed worker or its classification
is not obvious.

## Cheap classification

Choose one value on each axis. Classification is an input to routing, not a
deliverable.

| Axis | Values | What changes |
| --- | --- | --- |
| Reasoning | deterministic, mechanical, routine, substantial, frontier | Minimum inferential capability |
| Volume | tiny, small, moderate, large, repetitive/high-volume | Whether worker startup can save usage |
| Risk | low, ordinary, correctness-sensitive, security-sensitive, production-critical, irreversible | Quality floor and confidence margin |
| Context | minimal, local, multi-file, repository-wide, large-context | Minimum context-handling capability |

Use the closest configured work class:

- bulk_repository_scan
- structured_extraction
- repetitive_execution
- routine_refactor
- standard_feature_build
- routine_debugging
- difficult_debugging
- architecture
- security_review
- creative_planning
- final_quality_review

Do not create a new class during ordinary execution. For a genuinely recurring
unrepresented workload, add a profile only after representative evidence.

## Deterministic selection

`scripts/codex_tier.py route` calculates:

1. the work-class quality prior;
2. dimension-specific quality floors;
3. a risk-proportional confidence margin;
4. the available candidates in that class's frontier;
5. the lowest-relative-usage candidate that clears the resulting threshold.

The frontier files are intentionally different by work class. A candidate that
is efficient for extraction can be absent or dominated for architecture.
There is no global Luna → Terra → Sol ladder.

If the unit is deterministic, the script returns TOOL. If it is tiny, local,
low-risk, and cheap to keep in the current context, it returns DIRECT. If no
available worker clears the threshold, it returns DIRECT with
`requires_parent: true`; this is a quality safeguard, not a failure to save
usage.

## Availability

Pass `--available-model MODEL` once per runtime-available model when that set
is known. Pass `--unavailable-pair MODEL/EFFORT` after an actual
model/effort rejection. Do not run all candidates merely to discover
availability.

The registry's `probe-at-runtime` status means API documentation says the
pair exists but the user's current Codex workspace, plan, or provider can still
deny it.

## Escalation

After a concrete verification or capability failure, rerun the same work class
and dimensions with:

```text
python <skill-dir>/scripts/codex_tier.py route ... \
  --escalate-from gpt-5.6-terra/high
```

The next selection must have strictly higher calibrated quality for that work
class and still clear the quality margin. Carry forward only relevant failure
evidence. Do not rerun successful sibling units.

Escalate for:

- deterministic verification failure;
- explicit worker uncertainty that affects the definition of done;
- conflicting evidence;
- underestimated complexity, risk, or context;
- unavailable selected model/effort;
- capability failure.

Do not escalate because a cheaper worker was used or because the parent wants
reassurance.
