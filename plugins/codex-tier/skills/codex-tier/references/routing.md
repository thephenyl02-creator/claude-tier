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
3. a risk-proportional confidence margin (`--quality-margin` only raises the
   default margin for the unit's risk level and can never lower it; values
   outside 0 to 20 are rejected);
4. the available candidates in that class's frontier;
5. the lowest-relative-usage candidate that clears the resulting threshold.

The frontier files are intentionally different by work class. A candidate that
is efficient for extraction can be absent or dominated for architecture.
There is no global model or effort ladder.

If the unit is deterministic, the script returns TOOL. If it is tiny, local,
low-risk, and cheap to keep in the current context, it returns DIRECT. If no
available worker clears the threshold, it returns DIRECT with
`requires_parent: true`; this is a quality safeguard, not a failure to save
usage.

A measured `routing_decision: validated_worker` takes precedence over the
generic tiny-unit DIRECT shortcut. It contains exactly one benchmark-validated
pair and returns WORKER with that pair explicitly selected. The invoking parent
may be supplied with `--parent-model` and `--parent-effort` for an auditable
trace, but it never changes the validated selection.

## Availability

The router reads the current client model cache and matching checked-in real
launch probes. Pass `--available-model MODEL` only when the caller has narrower
runtime evidence. Pass `--unavailable-pair MODEL/EFFORT` after a newer actual
rejection. Do not run all candidates merely to discover availability outside
an explicit calibration.

If every measured-frontier point is unavailable, the router may consult the
prior candidate pool. Dominated pairs are not normal economic choices; they are
availability fallbacks after the dominating point is infeasible.

Validated-worker-only profiles are stricter: they never consult the prior
candidate pool. If their exact pair is unavailable in the current model cache,
unsupported at the required effort, or explicitly marked unavailable, routing
returns DIRECT with `requires_parent: true` and names the unavailable pair.
This preserves quality without silently substituting an unvalidated worker.

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
