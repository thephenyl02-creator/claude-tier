# Worker enforcement and usage capture

Read this reference before the first routed worker in a task.

## Native pinned worker

Current Codex subagent contracts support explicit model and reasoning-effort
pins. Explicit spawn values take precedence over configured defaults; an
unpinned worker inherits the parent.

Use a native worker only when the active spawn tool exposes both inputs.
Set the exact pair returned by the router. Keep the worker count at one unless
independent parallel work has a concrete benefit.

This includes measured validated-worker routes. A validated Sol/low baseline
must be spawned as Sol/low even when the invoking parent is Sol/max, Sol/xhigh,
or another pair; an unpinned spawn would inherit the parent and is invalid.

The work packet contains only:

```text
OBJECTIVE
SCOPE
RELEVANT FILES / PATHS
KNOWN FACTS
CONSTRAINTS
QUALITY BAR / RISK
EXPECTED OUTPUT
DEFINITION OF DONE
VERIFICATION
```

Do not forward the full conversation. For broad discovery, request distilled
findings rather than raw files, logs, or page contents.

After the native worker completes, record an event with:

```text
python <skill-dir>/scripts/codex_tier.py record \
  --execution-mode WORKER \
  --work-class <class> \
  --selected-model <model> \
  --selected-effort <effort> \
  --worker-count 1 \
  --verification-result <pass|fail|uncertain>
```

Add token or credit fields only when the current surface actually exposes them.

## Bounded codex exec fallback

When native tools cannot enforce both pins, use:

```text
python <skill-dir>/scripts/codex_tier.py execute \
  --repo <repository-root> \
  --model <selected-model> \
  --effort <selected-effort> \
  --sandbox <read-only|workspace-write> \
  --work-class <class> \
  --packet-file <packet-file>
```

The wrapper invokes the current documented form:

```text
codex exec \
  --cd <repository-root> \
  --model <selected-model> \
  --config 'model_reasoning_effort="<selected-effort>"' \
  --sandbox <policy> \
  --json \
  --ephemeral \
  --output-last-message <temporary-file> \
  -
```

The packet is sent on stdin. JSONL events provide
`input_tokens`, `cached_input_tokens`, `output_tokens`, and
`reasoning_output_tokens` when exposed. The wrapper writes one content-free
usage event and returns a compact JSON summary containing the final worker
message.

Use read-only for discovery and review. Use workspace-write only when the
bounded unit is authorized to edit the repository. Never use
danger-full-access merely to avoid an approval.

## Failure handling

Treat launch failure, timeout, model rejection, effort rejection, nonzero exit,
or missing required output as a failed unit. Preserve a short sanitized error,
mark the selected pair unavailable when appropriate, and route only that unit
again.

Never claim the pair ran merely because it was selected. A pair counts as
enforced only when it was present in the native spawn call or the actual
`codex exec` command and the worker started successfully.
