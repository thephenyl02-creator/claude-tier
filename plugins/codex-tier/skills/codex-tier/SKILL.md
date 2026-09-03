---
name: codex-tier
description: Explicitly invoked quality-constrained compute routing for a complete Codex task. Use only when the user invokes $codex-tier; route meaningful work units through deterministic tools, direct parent execution, or enforced model × reasoning-effort workers, then verify and selectively escalate.
---

# Codex Tier

Complete the user's whole task. Codex Tier is an execution workflow, not a
planning report or a model recommendation.

The invariant is:

> Quality first. Among model × reasoning-effort combinations expected to meet
> the required quality, choose the cheapest one with a confidence margin.
> Verify once, and escalate only the affected work unit when needed.

## Route cheaply

Decompose only when doing so can save meaningful usage or protect quality.
Classify each meaningful unit with four short labels:

- reasoning: deterministic, mechanical, routine, substantial, or frontier
- volume: tiny, small, moderate, large, or repetitive/high-volume
- risk: low, ordinary, correctness-sensitive, security-sensitive,
  production-critical, or irreversible
- context: minimal, local, multi-file, repository-wide, or large-context

Do not narrate a long routing analysis. For a non-obvious unit, run:

```text
python <skill-dir>/scripts/codex_tier.py route \
  --work-class <class> \
  --complexity <label> \
  --volume <label> \
  --risk <label> \
  --context <label>
```

An optional `--quality-margin` can only raise the default confidence margin for
the unit's risk level; it can never lower it, and values outside 0 to 20 are
rejected.

Read [routing.md](references/routing.md) before choosing a worker for an
unfamiliar work class or when the classification materially changes the quality
bar.

## Execute the returned mode

### TOOL

Use deterministic commands when they can prove the result: searches, builds,
tests, lint, type checking, schema checks, rendering, static analysis, exact
transformations, or file metadata. Do not buy model reasoning to imitate them.

### DIRECT

Use the current parent for a tiny unit already in context when worker startup
and packet construction would cost more than the work. DIRECT is also the
quality-safe fallback when no available pinned worker clears the configured
quality bar. DIRECT never changes or pins the current parent model or effort.

### WORKER

Before the first worker in a task, read
[executor.md](references/executor.md). Use one bounded worker unless independent
parallelism has a concrete latency or quality benefit.

Prefer native Codex subagents when the active tool exposes explicit
`model` and `reasoning_effort` inputs:

1. Pass both selected values explicitly. Never let the worker inherit them.
2. Send only the bounded work packet described in executor.md.
3. Record the actual pinned pair. Never report a cheaper pair unless the tool
   call enforced it.

A benchmark-validated baseline pair is a WORKER route, not DIRECT. If the
router returns a validated worker, enforce its exact model and effort even when
the invoking parent is a stronger or more expensive pair. Do not treat the word
"baseline" in benchmark evidence as permission to inherit the current parent.

If native workers on the current surface cannot enforce both pins, use the
bounded `codex exec` wrapper in `scripts/codex_tier.py execute`. If neither
mechanism is enforceable, keep the unit DIRECT and disclose that enforcement
was unavailable.

Read [model-registry.md](references/model-registry.md) only when a model or
effort is unavailable, compatibility is uncertain, or the registry needs
maintenance.

The active worker matrix comes from the current Codex client's model cache,
then from matching real launch-probe results. Never add `none`: this Codex
surface does not expose it. Do not assume a global model hierarchy or a common
effort set across models.

## Verify and escalate selectively

Run the cheapest reliable verification immediately after each unit. Prefer
tests, build, lint, type checking, schema validation, smoke tests, rendering,
and exact assertions. Use strong-model review only for judgment that
deterministic checks cannot establish.

If verification passes, accept the unit. Do not rerun it on a stronger model
for reassurance.

If verification fails, evidence conflicts, risk rises, or the worker reports
material uncertainty, route only that unit again with
`--escalate-from MODEL/EFFORT`. Use the returned next candidate and include
the failure evidence in the new bounded packet. If no stronger calibrated
worker remains, handle the unit on the parent.

## Log without content

Record TOOL, DIRECT, native-worker, and fallback-worker events with the bundled
logger when practical. The default JSONL file is
`$CODEX_HOME/codex-tier/usage.jsonl` or
`~/.codex/codex-tier/usage.jsonl`.

Log routing metadata and exposed usage only. Never log prompts, file contents,
credentials, private form answers, secrets, or raw worker transcripts.

## Finish the user's task

Integrate verified outputs and give the user the normal task result. Mention
routing only when it is useful for trust or when enforcement, verification, or
availability limited the result. Report measured usage honestly and never
invent a savings percentage.

Read [benchmarking.md](references/benchmarking.md) only when the user asks to
benchmark, calibrate, or tune Codex Tier.
