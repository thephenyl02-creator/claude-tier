# Codex Tier v1 — authoritative consolidated benchmark report

Status: **final for Codex Tier v1**
Authoritative through: **September 2, 2026**
Fixed benchmark commit: `75c2c6926bb317803e66946f72194788cac16ebe`
Fixed benchmark tree: `dd890aa87fa6d8aab33f868f2ec54acf3f3fb382`
Official CLI: `codex-cli 0.149.1`

This is the authoritative benchmark summary for Codex Tier v1. The raw suites,
answers, blinded verdicts, usage JSONL, checkpoints, hashes, and historical
reports remain alongside this file. Earlier reports are evidence records, not
the current product claim, wherever this report marks them superseded.

## Final result

Codex Tier's rule is quality first: use the cheapest route that reliably meets
the required quality, and spend more only when quality requires it. Corrected
evidence now validates the parent path for all five stabilized workload
classes. In the controlled benchmark, that parent was fixed to
`gpt-5.6-sol/low`.

Two comparisons answer different questions:

- **Versus Sol/low:** the corrected five-workload benchmark was essentially
  neutral on the primary workload-median exposed-token metric: `-0.073%`
  reduction, meaning a `0.073%` increase. The workload mean was a `3.556%`
  increase, driven by the now-superseded Terra/xhigh debugging route. Quality
  was preserved in `5/5` classes and both conditions passed at `100%`.
- **Versus always Sol/max:** Codex Tier measured a **9.83% median** and
  **12.57% mean exposed-token reduction** across the five tested workloads,
  with `100%` quality-gate pass rates in both conditions. All five workload
  reductions were positive.

These are **exposed-token results** (`input_tokens + output_tokens`). They are
not Codex-credit, billing, dollar, or 5-hour-quota savings. Codex exposed no
mapping from token counters to those account-consumption measures.

The route corrections made after the benchmark may improve the router further
by removing two unnecessary workers. No new percentage is claimed without a
new controlled measurement.

## Original goal and architecture

Codex Tier v1 was built as an explicit, local, quality-constrained compute
router. It separates the model from reasoning effort and dynamically constructs
the candidate space from the current Codex client's visible models and the
efforts actually supported by each model. It does not use a global model
hierarchy.

For a classified work unit, the router returns one of three modes:

- `TOOL` for deterministic work that commands or exact checks can prove;
- `DIRECT` for work that should remain on the parent, including cases where no
  cheaper worker is reliably quality-preserving;
- `WORKER` for an explicitly pinned model × effort pair, followed by targeted
  verification and selective escalation.

The active implementation and data are:

- `plugins/codex-tier/skills/codex-tier/scripts/codex_tier.py`
- `plugins/codex-tier/skills/codex-tier/references/model-registry.json`
- `plugins/codex-tier/skills/codex-tier/references/candidate-matrix.json`
- `plugins/codex-tier/skills/codex-tier/references/frontiers.json`
- `plugins/codex-tier/skills/codex-tier/references/measured-frontiers.json`

The router overlays real measured decisions on distributable priors. A
measured `routing_decision: "parent"` empties the worker list, removes stale
availability fallbacks, and marks the profile parent-only. This prevents a
superseded worker from reappearing because of availability or escalation.

## Evidence hierarchy

Evidence is authoritative in this order:

1. `corrected-final-results.json` for Sol/low baseline versus the then-frozen
   Tier routes and the five-workload quality gate;
2. `sol-max-comparison-final-results.json` for the comparison with always
   Sol/max;
3. fixture-correction results for repaired bulk/debug evidence and the valid
   routine/security/architecture records selected from the original final
   batch;
4. targeted tuning and confirmation runs as historical candidate evidence;
5. synthetic 29-pair calibration as availability, enforcement, and narrow
   fixture evidence only;
6. deterministic harness results as executor validation only.

No lower-ranked artifact overrides a later result with the same task, complete
evidence, and stricter provenance.

## Model discovery and 29-pair calibration

The current account exposed six coding-capable models and 29 candidate pairs:

| Model | Exposed candidate efforts | Pairs |
| --- | --- | ---: |
| `gpt-5.4-mini` | low, medium, high, xhigh | 4 |
| `gpt-5.4` | low, medium, high, xhigh | 4 |
| `gpt-5.5` | low, medium, high, xhigh | 4 |
| `gpt-5.6-luna` | low, medium, high, xhigh, max | 5 |
| `gpt-5.6-terra` | low, medium, high, xhigh, max, ultra | 6 |
| `gpt-5.6-sol` | low, medium, high, xhigh, max, ultra | 6 |

`none` was not exposed and was excluded. All 29 advertised pairs launched
successfully. The calibration then executed 87 comparable calls: 29 pairs on
each of three narrow synthetic fixtures (bulk scan, difficult debugging, and
security review). All 87 calls completed and passed structured verification,
with zero retries and zero error events.

The first synthetic frontier placed `gpt-5.4-mini/low` at the lowest measured
usage on all three fixtures. That finding remains valid for those synthetic
snapshots, as do the model/effort launch results. It is superseded for
production routing because later realistic repository workloads showed that
the same cheap route failed relative quality gates. GPT-5.5 did not occupy the
narrow synthetic frontier but remains an available registry model.

Primary calibration artifacts:

- `plugins/codex-tier/skills/codex-tier/references/candidate-matrix.json`
  (`SHA-256 4d133706933443810c54c52ecf8102c6c83d45be2c3a070b308421a0155b4d31`)
- `plugins/codex-tier/skills/codex-tier/references/real-calibration-results.json`
  (`SHA-256 df03273f2da7ac204644dabb5ab51e7afe030ddd5944386624665722096fe367`)

## First controlled benchmark and why it was invalid for economics

The first realistic benchmark scheduled five workload classes, baseline versus
Tier, five repetitions per condition: 50 primary runs at the fixed commit. It
used randomized order, blinded Sol/max verification, checkpoints, and exposed
token logging.

It successfully exposed two engineering problems, but its quality/economic
numbers are not publishable:

1. managed-shell and repository-inspection failures prevented some workers
   from reliably reading the repository;
2. routine refactor and architecture suffered severe Tier over-consumption
   from poor initial routing and quality remediation.

Both conditions had a `0%` final pass rate. Tier's raw workload-median result
was `33.34%` lower usage, but the workload mean was a `56.51%` increase and no
workload preserved quality. Those figures diagnose the harness and executor;
they do not measure a valid quality-preserving frontier.

The complete historical record remains in `benchmark-results.json` (SHA-256
`6424ad80db4253e3c0f8fcddcef9ea8723e82649d9904c1a2cc344ac632e663c`).

## Harness stabilization and targeted tuning

The existing benchmark architecture was retained. It gained workload-specific
frozen evidence, immediate attempt checkpoints, clean usage-limit stopping and
resume, infrastructure/quality separation, and small targeted candidate sets.
Candidate tasks did not receive hidden expected answers or verifier criteria.

The first targeted tuning batch tested routine refactor and architecture with
two repetitions:

| Workload | Route | Median tokens | Median quality | Pass rate | Historical decision |
| --- | --- | ---: | ---: | ---: | --- |
| routine refactor | Sol/low baseline | 70,412 | 88.0 | 100% | reference |
| routine refactor | Terra/low | 59,964 | 87.0 | 100% | initially preferred |
| architecture | Sol/low baseline | 94,208 | 92.5 | 100% | parent |
| architecture | Sol/medium | 142,142 | 91.5 | 100% | dominated by parent |
| architecture | GPT-5.5/medium | 69,845 | 82.5 | 50% | failed quality |

This justified an interim Terra/low routine route and retained architecture on
the parent. The corrected final benchmark later superseded the routine route:
under the corrected identical packet, Sol/low used 22,004 tokens versus 22,020
for Terra/low and both passed.

A confirmation pass then rejected `gpt-5.4-mini/low` for bulk scan, difficult
debugging, and security review. It consumed fewer tokens but failed the
relative quality gate in all three, so no savings was published.

The quality-recovery tuning batch tested two stronger candidates per remaining
workload. It rejected bulk candidates that failed absolute or relative quality.
It initially preferred Terra/xhigh for difficult debugging because that fixture
showed `100%` pass and quality 89 versus a `50%`-pass Sol/low baseline. That
decision was later superseded because the frozen debugging evidence omitted a
function the task and verifier required.

## Security grounding-gate repair

All six initial security tuning records—including the Sol/low baseline—were
deterministically assigned quality zero before strong-model judgment. The task
asked for six security surfaces, but the gate required exact helper/file names
such as `command_prefix`, `write_event`, and `log_file`. A correct answer could
cover the requested trust boundaries without using those spellings.

The repair left the task and quality rubric intact and changed only the brittle
grounding screen: exact terms became semantic surface groups for the Windows
installer, Unix installer, plugin-source trust, bounded `codex exec`,
model-cache/probe ingestion, and content-free usage logging. Five of six groups
were required. The repaired batch had zero deterministic failures; it did not
identify a cheaper reliable security route. The corrected final security
records later passed at `100%` for both conditions on the parent.

## Bulk and debugging fixture repairs

The first 30-run final batch left routine refactor, security review, and
architecture valid, but contained two genuine fixture defects:

- **Bulk repository scan:** the task required repository inspection with
  tools while the candidate packet prohibited repository tools and supplied
  excerpts. The repaired task treats frozen evidence as the inspection
  surface. Its packet contains the complete tracked-file manifest and the
  complete text of all 50 tracked files (455,341 characters).
- **Difficult debugging:** the task required tracing
  `merge_measured_frontiers`, but the evidence omitted the function body while
  the rubric expected its logic. The repaired packet contains seven complete
  relevant files (124,785 characters), including the full implementation,
  tests, registry, candidate matrix, prior/measured frontiers, and calibration
  documentation.

Mechanical validation ran before the correction batch: required task phrases,
evidence terms, complete paths, all-tracked-file coverage, contradictory
constraints, and rubric leakage were checked. Baseline and Tier shared one
task, evidence, and canonical-packet hash per workload.

Only bulk and debugging were rerun: three repetitions per condition, 12 new
primaries. All 12 passed and completed without primary retries, escalation, or
infrastructure failure. Their records were combined with the unchanged 18
valid records from the first final batch. Source-batch randomized positions and
hashes are preserved in `corrected-final-results.json`.

## Corrected Sol/low benchmark

The parent/baseline was fixed to `gpt-5.6-sol/low`. The following table reports
the routes used during measurement; routine and debugging are subsequently
corrected to parent-only.

| Workload | Measured Tier route | Baseline median tokens | Tier median tokens | Tier token change | Quality baseline/Tier | Pass baseline/Tier |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| bulk repository scan | Sol/low parent | 155,373 | 155,369 | -0.003% | 96 / 94 | 100% / 100% |
| routine refactor | Terra/low | 22,004 | 22,020 | +0.073% | 88 / 89 | 100% / 100% |
| difficult debugging | Terra/xhigh | 53,112 | 62,424 | +17.533% | 94 / 93 | 100% / 100% |
| security review | Sol/low parent | 28,773 | 28,861 | +0.306% | 84 / 85 | 100% / 100% |
| architecture | Sol/low parent | 45,814 | 45,756 | -0.127% | 94 / 93 | 100% / 100% |

Quality was preserved in `5/5` workload classes. Baseline/Tier median quality
was 91/92, and both pass rates were `100%`.

The workload-median exposed-token usage reduction was `-0.073%`, or a `0.073%`
increase: essentially neutral versus Sol/low. The workload mean was `-3.556%`,
or a `3.556%` increase, primarily because the interim Terra/xhigh debugging
route spent 17.533% more while scoring one point lower. This is the direct
evidence for returning debugging to Sol/low.

Authoritative Sol/low artifact:
`corrected-final-results.json` (SHA-256
`36c8ab014eec04460d478429c78ca6545f05098ee34fb4f8f8d56108f1f09b06`).

## Comparison with always Sol/max

Tier was not rerun. Existing corrected Tier medians were compared with direct
Sol/max calls using identical tasks, frozen evidence, commit, verifier protocol,
and usage measurement. The four initially ambiguous workloads received two
additional Max observations; architecture remained at its already-clear single
Max observation.

| Workload | Max runs | Median Max tokens | Median Tier tokens | Tier reduction vs Max | Median quality Max/Tier | Pass Max/Tier | Median latency Max/Tier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bulk repository scan | 3 | 163,721 | 155,369 | 5.10% | 96 / 94 | 100% / 100% | 130.2s / 36.1s |
| routine refactor | 3 | 25,532 | 22,020 | 13.76% | 89 / 89 | 100% / 100% | 81.7s / 32.0s |
| difficult debugging | 3 | 63,883 | 62,424 | 2.28% | 94 / 93 | 100% / 100% | 165.1s / 138.4s |
| security review | 3 | 42,378 | 28,861 | 31.90% | 91 / 85 | 100% / 100% | 207.3s / 36.6s |
| architecture | 1 | 50,746 | 45,756 | 9.83% | 96 / 93 | 100% / 100% | 141.9s / 33.0s |

Across workload classes, the median exposed-token reduction versus always
Sol/max was **9.83%** and the mean was **12.57%**. The best measured reduction
was security review at 31.90%; the smallest was difficult debugging at 2.28%.
All five reductions were positive and both conditions passed the quality gate
at `100%`.

This supports a scoped exposed-token reduction claim, not a quality-equivalence
claim. Security's Max median quality was six points higher, and architecture
has one Max observation. The completed artifact is
`sol-max-comparison-final-results.json` (SHA-256
`a9a9ebffe69cd506f0001318a9e197a167c5374bd62c51f8f543bc2c8054e115`).

## Final validated routing

All five measured profiles now resolve directly to the parent. The controlled
parent pair was `gpt-5.6-sol/low`.

| Workload class | Final v1 route | Authoritative reason |
| --- | --- | --- |
| `bulk_repository_scan` | DIRECT parent (validated Sol/low) | No cheaper tested worker preserved quality; the corrected complete-repository conditions both passed on the parent. |
| `routine_refactor` | DIRECT parent (validated Sol/low) | Sol/low used 22,004 median tokens versus 22,020 for Terra/low; both passed. |
| `difficult_debugging` | DIRECT parent (validated Sol/low) | Sol/low used 53,112 median tokens and quality 94 versus Terra/xhigh at 62,424 and quality 93. |
| `security_review` | DIRECT parent (validated Sol/low) | No cheaper candidate preserved required quality; corrected parent conditions passed. |
| `architecture` | DIRECT parent (validated Sol/low) | No cheaper quality-preserving route was found. |

The router does not retain a stronger route because it once looked promising
under superseded evidence. Parent-only overlays also remove prior availability
fallback candidates.

## Superseded results

| Artifact or conclusion | Current status |
| --- | --- |
| Deterministic executor harness | Valid for executor, pinning, logging, and packet validation; never an economic benchmark. |
| First synthetic 29-pair frontier | Valid for pair launchability and its narrow fixtures; superseded for production route economics. |
| `benchmark-results.json` | Preserved diagnostic evidence; its economic and quality conclusions are invalid because repository access failed. |
| Interim GPT-5.4-mini routes | Superseded after realistic confirmation failed relative quality in bulk, debugging, and security. |
| Terra/low routine preference from `tuning-results.json` | Superseded by the corrected final identical-packet result; parent used slightly fewer tokens and passed. |
| Terra/xhigh debugging preference from `quality-recovery-tuning-v2-results.json` | Superseded because the fixture omitted required merge logic; corrected Sol/low was cheaper and equal/better quality. |
| Security quality-zero records in quality-recovery tuning | Invalidated by the overly brittle deterministic grounding gate. |
| `final-results.json` bulk/debug records | Superseded by the 12-run fixture correction. Routine, security, and architecture records remain valid and are preserved in the corrected composite. |
| `fixture-correction-results.json` | Authoritative source batch for corrected bulk/debug records. |
| `corrected-final-results.json` | Authoritative five-workload Sol/low comparison. |
| Initial five-run Sol/max comparison | Preserved as repetition 1; the combined extension artifact is authoritative. |
| `sol-max-comparison-final-results.json` | Authoritative always-Sol/max comparison. |

Superseded does not mean deleted. Every raw result, suite, usage log, verifier
log, report, and checkpoint remains in `benchmarks/codex-tier-e2e/`.

## Final claims and limitations

Defensible claims:

- The account exposed 29 executable coding model × effort pairs across six
  models; all 29 launched with the tested CLI.
- The corrected Sol/low comparison preserved the quality gate in all five
  workloads and was essentially neutral on the workload-median exposed-token
  metric.
- Against always Sol/max, the tested workloads measured 9.83% median and
  12.57% mean exposed-token reductions, with 100% pass rates.
- The final five stabilized routing profiles are parent-only under the
  corrected evidence.

Limitations:

- Exposed tokens are a proxy. Codex credits, billing, dollars, and 5-hour quota
  consumption were not exposed and no savings claim is made for them.
- The repository, commit, workload set, prompts, and model catalog are fixed;
  results do not imply a universal model ranking.
- Architecture has one direct Sol/max observation; the other Max workloads
  have three.
- Security passed both quality gates but Sol/max had a six-point higher median
  score, so this is not a quality-equivalence result.
- Correcting routine and debugging to parent occurred after measurement. It may
  improve the final router, but no post-correction percentage is claimed.
- Future Codex model catalogs or usage semantics require new discovery and
  calibration rather than extrapolation from these numbers.

Codex Tier v1 is frozen at this evidence boundary.
