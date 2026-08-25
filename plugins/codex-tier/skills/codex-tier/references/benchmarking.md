# Benchmarking and calibration

Benchmark only after routing, enforcement, verification, logging, and
install/discovery tests pass.

Use:

```text
python <skill-dir>/scripts/benchmark.py
```

The default is plan-only. It validates the five representative workload
classes and lists only adjacent or competing candidates. It does not spend
model usage.

For an authorized live run with a callable Codex CLI:

```text
python <skill-dir>/scripts/benchmark.py \
  --run \
  --repo <fixture-repository> \
  --results-file <results.json>
```

Before a live run, replace placeholder paths in implementation, debugging, and
security packets with a controlled fixture repository and deterministic
verification commands. Do not benchmark against live production state.

Measure:

- correctness or quality result;
- verification pass rate;
- actual Codex credits when exposed;
- input, cached input, output, and reasoning tokens;
- worker count, retries, escalations, latency, and failure mode.

Compare only candidates relevant to that class. Do not brute-force all
model × effort combinations. A candidate that fails the quality gate is not a
savings win regardless of its usage.

The harness reports raw usage and does not invent a savings percentage. Publish
a percentage only after comparable, verified trials establish the numerator,
baseline, and Codex consumption metric.
