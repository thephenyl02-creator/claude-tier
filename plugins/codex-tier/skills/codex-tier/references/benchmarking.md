# Benchmarking and calibration

Benchmark only after routing, enforcement, verification, logging, and
install/discovery tests pass.

There are two separate harnesses.

## Executor validation

Use:

```text
python <skill-dir>/scripts/benchmark.py
```

The default is plan-only. This deterministic-compatible harness validates the
executor, pinning, logging, and representative routing packets. It is not the
economic benchmark and cannot publish a measured frontier.

For an authorized live run with a callable Codex CLI:

```text
python <skill-dir>/scripts/benchmark.py \
  --run \
  --repo <fixture-repository> \
  --results-file <results.json>
```

## Real Codex calibration

Use the official Codex CLI and the bundled synthetic, identical fixtures:

```text
python <skill-dir>/scripts/calibrate.py --run --codex-bin <official-codex-cli>
```

The runner discovers `available models × per-model exposed efforts`, launch
probes every advertised pair, marks rejected pairs unavailable, executes every
successful pair on each selected fixture, verifies structured results, and
derives workload-specific nondominated frontiers. It rejects deterministic CLI
doubles in `--run` mode.

Read [real-calibration.md](real-calibration.md) for the checked-in first run,
its limitations, and an exact Windows command.

Measure:

- correctness or quality result;
- verification pass rate;
- actual Codex credits when exposed;
- input, cached input, output, and reasoning tokens;
- worker count, retries, escalations, latency, and failure mode.

Full candidate sweeps are reserved for explicit calibration. Ordinary
benchmark maintenance should compare adjacent or newly relevant candidates.
A candidate that fails the quality gate is not a savings win regardless of its
usage.

The harness reports raw usage and does not invent a savings percentage. Publish
a percentage only after comparable, verified trials establish the numerator,
baseline, and Codex consumption metric.

For the frozen v1 evidence hierarchy, corrected fixtures, final parent-only
routes, superseded results, and permitted exposed-token claims, read the
repository-level authoritative report:
`benchmarks/codex-tier-e2e/CONSOLIDATED-BENCHMARK-REPORT.md`.
