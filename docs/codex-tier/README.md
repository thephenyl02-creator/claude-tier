# Codex Tier v1

> Part of the [Claude Tier + Codex Tier](../../README.md) repository. Release history: [CHANGELOG](CHANGELOG.md). Plans: [ROADMAP](ROADMAP.md).

Codex Tier is a local, explicit, quality-constrained compute router for Codex.
It is designed to reduce Codex usage without lowering the required quality.

The permanent rule is:

> Quality first. Among all model × reasoning-effort combinations expected to
> meet the required quality, choose the cheapest one with a confidence margin.
> Verify, and escalate only when needed.

Claude Tier remains a separate product. Codex Tier does not modify Claude's
plugin metadata, skill, installers, or routing rules.

## Install

macOS, Linux, or WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/thephenyl02-creator/claude-codex-tier/main/install-codex.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/thephenyl02-creator/claude-codex-tier/main/install-codex.ps1 | iex
```

The installers:

- detect a callable Codex CLI or the Windows Codex app;
- validate the pinned `codex exec` flags when a CLI is callable;
- prefer the repo's Codex plugin marketplace;
- fall back to an idempotent standalone copy under
  `~/.agents/skills/codex-tier`;
- preserve unrelated configuration and hand-authored skill copies;
- validate the deterministic routing configuration;
- never modify global Git settings or Claude Tier.

If Codex is missing, install the official CLI first:

```bash
npm install --global @openai/codex
```

For local plugin development:

```text
codex plugin marketplace add <repository-root>
codex plugin add codex-tier@codex-tier
```

Start a new task after installing or updating so Codex reloads the skill.

## Use

```text
$codex-tier

<normal task>
```

The skill is explicit-only in v1. Its `agents/openai.yaml` sets
`allow_implicit_invocation: false`.

## Routing

```text
quality requirement
  → workload class
  → reasoning × volume × risk × context
  → workload-specific calibrated frontier
  → cheapest reliable model × effort with margin
  → execute
  → verify
  → selective escalation when needed
```

Codex Tier has three execution modes:

- **TOOL** — deterministic commands such as search, build, tests, lint,
  type checking, schema validation, rendering, and exact transformations.
- **DIRECT** — the current parent for tiny work when worker startup would
  cost more, or when no available pinned worker safely clears the quality bar.
- **WORKER** — a bounded worker with an actually enforced model and reasoning
  effort.

DIRECT preserves the invoking session's model and effort. A benchmark-validated
baseline pair is therefore represented as WORKER, not DIRECT: the five
stabilized v1 profiles explicitly pin `gpt-5.6-sol/low`, even when the invoking
session is Sol/max or Sol/xhigh. If that exact pair is unavailable, routing
fails safely to DIRECT-current-parent with `requires_parent: true`; it does not
substitute an unvalidated prior candidate.

Routing is deterministic and cheap. It does not benchmark multiple candidates
during a live task and does not use a fixed cross-model escalation ladder.

## Model registry and frontiers

The active matrix is discovered from the current Codex client's visible model
catalog. On August 25, 2026 this account exposed:

- `gpt-5.4-mini`: low, medium, high, xhigh
- `gpt-5.4`: low, medium, high, xhigh
- `gpt-5.5`: low, medium, high, xhigh
- `gpt-5.6-luna`: low, medium, high, xhigh, max
- `gpt-5.6-terra`: low, medium, high, xhigh, max, ultra
- `gpt-5.6-sol`: low, medium, high, xhigh, max, ultra

`none` is not exposed by this Codex surface and is excluded from active
candidates. `ultra` is a client effort available only on Terra and Sol in this
environment.

Model IDs, supported efforts, compatibility, relative capability, and relative
usage priors live in
`plugins/codex-tier/skills/codex-tier/references/model-registry.json`.
Workload-specific candidates live in `frontiers.json`. Future model changes
update configuration and calibration rather than routing architecture.

The checked-in `candidate-matrix.json` records real launch status for all 29
pairs. Matching unavailable probes are automatically excluded; stale probe
artifacts are ignored when the client matrix changes.

Relative usage values are routing priors, not Codex subscription-credit
prices. Runtime usage fields are recorded when Codex exposes them.

## Worker enforcement

Current Codex documentation and the active native tool contract both support
explicit subagent model and reasoning-effort pins. Codex Tier therefore
prefers a native pinned worker when the current surface exposes both values.
Unpinned workers are forbidden because they inherit the parent.

When native pins are unavailable, the bundled executor uses the current
documented non-interactive syntax:

```text
codex exec
  --cd <repository-root>
  --model <selected-model>
  --config 'model_reasoning_effort="<selected-effort>"'
  --sandbox <read-only|workspace-write>
  --json
  --ephemeral
  --output-last-message <file>
  -
```

The worker receives a bounded packet with only objective, scope, relevant
paths, known facts, constraints, quality/risk, expected output, definition of
done, and verification.

Codex Tier never claims a selected pair ran unless the native spawn or actual
`codex exec` command enforced it.

## Verification and escalation

Deterministic verification comes first. Strong-model verification is reserved
for security, architecture, subtle concurrency, ambiguous correctness, or
creative judgment that tools cannot prove.

A passed unit is accepted without a stronger rerun. A failed or uncertain unit
is routed through the next stronger candidate in that work class's frontier.
Successful sibling units are not repeated.

## Usage logging

The default content-free JSONL log is:

```text
$CODEX_HOME/codex-tier/usage.jsonl
```

or `~/.codex/codex-tier/usage.jsonl` when `CODEX_HOME` is unset.

Where available, events record run ID, timestamp, work class, execution mode,
selected model and effort, parent model, token fields, Codex credits, worker
count, duration, verification, escalation, and success. Prompts, source files,
credentials, private form responses, and raw transcripts are never logged.

## Validate and test

All commands below run from the repository root.

```text
python plugins/codex-tier/skills/codex-tier/scripts/codex_tier.py validate
python plugins/codex-tier/skills/codex-tier/scripts/codex_tier.py matrix
python -m unittest discover -s tests/codex-tier -p "test_*.py" -v
python plugins/codex-tier/skills/codex-tier/scripts/benchmark.py
python plugins/codex-tier/skills/codex-tier/scripts/calibrate.py
```

The first command validates registry/frontier integrity. The tests cover mode
selection, multiple model/effort regions, unavailable candidates, selective
escalation, bounded worker pin enforcement, usage capture, worker failure, and
representative workload routing. The benchmark command is plan-only by
default.

## Benchmarking

The [authoritative consolidated benchmark report](../../benchmarks/codex-tier-e2e/CONSOLIDATED-BENCHMARK-REPORT.md)
is the canonical v1 summary. It reconciles the 29-pair calibration, invalid
early trials, targeted tuning, fixture repairs, corrected Sol/low benchmark,
always-Sol/max comparison, superseded evidence, and final pinned Sol/low routes.
Raw artifacts remain under `benchmarks/codex-tier-e2e/`.

The deterministic executor-validation manifest covers:

1. high-volume, low-reasoning work;
2. mixed creative and execution work;
3. ordinary implementation;
4. difficult debugging;
5. high-risk review.

It compares adjacent candidates and can run with a CLI double to validate the
executor. It is not the economic benchmark.

Real calibration uses the official Codex CLI, dynamically sweeps the complete
advertised matrix, and runs identical synthetic fixtures:

```text
python plugins/codex-tier/skills/codex-tier/scripts/calibrate.py \
  --run --codex-bin <official-codex-cli> --timeout 300
```

Raw quality, verification, tokens, credits, retries, escalations, and latency
are reported. Codex Tier does not publish a savings percentage until comparable
verified runs support one.

## Final v1 environment findings

As verified on August 25, 2026:

- The current Codex client catalog exposed six models and 29 per-model effort
  combinations listed above. It did not expose `none`; it did expose `ultra`
  for Terra and Sol.
- Official `codex-cli 0.149.1` successfully launched all 29 advertised pairs.
- The separate real calibration completed 87/87 comparable fixture runs with
  87 verification passes, zero retries, and zero error events.
- Codex JSONL exposed input, cached input, output, and reasoning-output token
  counters. It did not expose Codex subscription credits.
- Synthetic calibration initially placed `gpt-5.4-mini/low` on three narrow
  frontiers, but realistic repository confirmation failed the relative quality
  gate. That synthetic frontier is launch/executor evidence, not the final
  production route.
- Corrected evidence validates an explicitly pinned Sol/low worker for bulk
  repository scan, routine refactor, difficult debugging, security review, and
  architecture. This does not inherit the current parent pair.
- Versus Sol/low, corrected Tier usage was essentially neutral on the
  workload-median exposed-token metric. Versus always Sol/max, the tested
  workloads measured 9.83% median and 12.57% mean exposed-token reductions,
  with 100% quality-gate pass rates.
- For the final all-Sol/low route, mechanically compatible existing observations
  imply a derived 13.82% median and 15.52% mean exposed-token reduction versus
  always Sol/max. This is not a new post-correction Tier run and is reported
  separately from the directly measured 9.83% / 12.57% result.
- These percentages are exposed-token results, not credit, billing, dollar,
  or 5-hour-quota savings. The post-benchmark execution correction from
  DIRECT-current-parent to pinned Sol/low has no new directly measured
  percentage.
- Current Codex documentation supports explicit subagent `model` and
  `model_reasoning_effort` pins.
- Current `codex exec` supports `--model`, repeated `--config`,
  `--json`, `--output-last-message`, and explicit sandbox selection.
- The managed shell rejected the app-bundled executable and nested fixture
  shell inspection. A standalone official CLI reused account authentication,
  so calibration used inline synthetic repository snapshots and real model
  calls without user repository data.
- Codex surfaces do not guarantee that every documented model is enabled for
  every workspace or account. Availability is confirmed at execution time.

Official references:

- [Codex developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [Build Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Build Codex plugins](https://learn.chatgpt.com/docs/build-plugins)
- [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)
