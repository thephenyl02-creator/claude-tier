# Codex Tier end-to-end benchmark directory

This directory holds the complete evidence record for the Codex Tier v1
benchmark: run suites (inputs), result checkpoints, rendered per-run reports,
content-free usage logs, the harness scripts, and the verifier schema.
`CONSOLIDATED-BENCHMARK-REPORT.md` is the only authoritative summary; every
other report here is an evidence record, superseded where that report says so.
Nothing in this directory may be moved or renamed: the scripts hard-code
sibling paths, and the evidence is frozen against repository commit
`75c2c6926bb317803e66946f72194788cac16ebe`.

## Read this first

- `CONSOLIDATED-BENCHMARK-REPORT.md`, section "Final result": what Codex
  Tier v1 actually claims.
- Same file, section "Superseded results": which artifact here still stands
  and which is diagnostic only.
- Same file, section "Final claims and limitations": the exact scope of the
  numbers, including that they are exposed tokens only.

## Runs, in order

| Family prefix | Phase (as the report names it) | Status | Files |
| --- | --- | --- | --- |
| (none) `suite`, `benchmark-` | First controlled benchmark and why it was invalid for economics | superseded | `suite.json`, `benchmark-results.json`, `benchmark-report.md`, `benchmark-task-usage.jsonl`, `benchmark-verifier-usage.jsonl` |
| `tuning-` | Harness stabilization and targeted tuning | superseded (Terra/low routine preference) | `tuning-suite.json`, `tuning-results.json`, `tuning-report.md`, `tuning-task-usage.jsonl`, `tuning-verifier-usage.jsonl` |
| `confirmation-` | Confirmation pass rejecting GPT-5.4-mini | superseded (interim GPT-5.4-mini routes) | `confirmation-suite.json`, `confirmation-results.json`, `confirmation-report.md`, `confirmation-task-usage.jsonl`, `confirmation-verifier-usage.jsonl` |
| `quality-recovery-tuning-` | Quality-recovery tuning batch | supporting | `quality-recovery-tuning-suite.json`, `quality-recovery-tuning-results.json`, `quality-recovery-tuning-task-usage.jsonl` |
| `quality-recovery-tuning-v2-` | Quality-recovery tuning batch (second pass) | superseded (Terra/xhigh debugging preference) | `quality-recovery-tuning-v2-results.json`, `quality-recovery-tuning-v2-report.md`, `quality-recovery-tuning-v2-task-usage.jsonl`, `quality-recovery-tuning-v2-verifier-usage.jsonl` |
| `security-gate-repair-` | Security grounding-gate repair | supporting | `security-gate-repair-suite.json`, `security-gate-repair-results.json`, `security-gate-repair-report.md`, `security-gate-repair-task-usage.jsonl`, `security-gate-repair-verifier-usage.jsonl` |
| `final-` | First 30-run final batch | partly superseded: bulk/debug records superseded, routine/security/architecture records remain valid | `final-suite.json`, `final-results.json`, `final-report.md`, `final-task-usage.jsonl`, `final-verifier-usage.jsonl` |
| `fixture-correction-` | Bulk and debugging fixture repairs | authoritative source batch for corrected bulk/debug records | `fixture-correction-suite.json`, `fixture-correction-results.json`, `fixture-correction-report.md`, `fixture-correction-task-usage.jsonl`, `fixture-correction-verifier-usage.jsonl` |
| `corrected-final-` | Corrected Sol/low benchmark | authoritative (five-workload Sol/low comparison) | `corrected-final-suite.json`, `corrected-final-results.json`, `corrected-final-report.md` |
| `sol-max-comparison-` | Comparison with always Sol/max, first five-run batch | superseded (preserved as repetition 1) | `sol-max-comparison-suite.json`, `sol-max-comparison-results.json`, `sol-max-comparison-report.md`, `sol-max-comparison-task-usage.jsonl`, `sol-max-comparison-verifier-usage.jsonl` |
| `sol-max-comparison-extension-` | Comparison with always Sol/max, added Max observations | supporting | `sol-max-comparison-extension-suite.json`, `sol-max-comparison-extension-task-usage.jsonl`, `sol-max-comparison-extension-verifier-usage.jsonl` |
| `sol-max-comparison-final-` | Comparison with always Sol/max, combined result | authoritative (always-Sol/max comparison) | `sol-max-comparison-final-results.json`, `sol-max-comparison-final-report.md` |

The "Final-route derived comparison" section of the report has no files of its
own: it is derived from `corrected-final-results.json` and
`sol-max-comparison-final-results.json`, with no new model calls.

## Scripts

- `e2e_benchmark.py` is the main harness: "Controlled normal-Codex versus Codex
  Tier real-repository benchmark." It accepts `--run`, `--resume`, `--tuning`,
  `--status`, `--suite`, `--repo`, `--codex-bin`, `--timeout`, `--results-file`,
  `--report-file`, and `--verifier-schema`.
- `validate_results.py` independently validates the checked-in end-to-end
  benchmark artifact (`--results`, `--suite`).
- `merge_fixture_correction.py` merges the two corrected fixtures with the three
  valid final workloads. It executes no Codex calls; it verifies source
  provenance and hashes, keeps each source batch's randomized position, and
  recomputes the five-workload analysis, writing the `corrected-final-` files.
- `sol_max_comparison.py` runs the five-run always-Sol/max comparison using the
  frozen corrected-final evidence (`--run`, `--resume`, `--status`, `--repo`,
  `--codex-bin`, `--config`, `--results-file`, `--report-file`,
  `--verifier-schema`, `--timeout`).
- `sol_max_comparison_extension.py` adds two Sol/max observations to each
  ambiguous lightweight comparison and writes the `sol-max-comparison-final-`
  artifacts (same flag set as above).
- `verifier-schema.json` is the JSON Schema the blinded verifier output must
  satisfy: integer `score` 0-100, boolean `passed`, the four `dimensions`
  (correctness, evidence, completeness, actionability), `critical_errors`, and
  `summary`.

## Re-running

The harness calls `assert_repository_state` (e2e_benchmark.py line 114) on
every phase, so the benchmark repository must be checked out at the frozen
commit `75c2c6926bb317803e66946f72194788cac16ebe`. That checkout is expected
under `.benchmark-state/repo`, which is gitignored and therefore absent on a
fresh clone. One unit test needs it and errors without it:
`tests/codex-tier/test_e2e_benchmark.py::test_repaired_fixtures_are_complete_and_mechanically_consistent`
(the path is built at test_e2e_benchmark.py line 371).

From the repository root:

```
python -m unittest discover -s tests/codex-tier
```
