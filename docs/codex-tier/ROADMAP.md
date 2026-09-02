# Codex Tier roadmap

> Part of the [Claude Tier + Codex Tier](../../README.md) repository. Current
> behaviour: [guide](README.md). Evidence:
> [benchmark report](../../benchmarks/codex-tier-e2e/CONSOLIDATED-BENCHMARK-REPORT.md).

This is the working list of what Codex Tier adopts next, what it deliberately
does not, and why. It comes from a September 2026 read of more than twenty
routing projects for Claude Code and Codex, seven of them in full, followed by
two adversarial reviews of Codex Tier against them. Ideas are credited to the project they were seen in.
No code is copied from any of them.

Every item must respect the design constraints Codex Tier already holds:
quality first, so cost never buys a downgrade; explicit invocation only; an
enforced model x reasoning-effort pin on every worker; no daemon, proxy, port,
or hook; and no savings claim the evidence does not support.

## Now

1. **The quality margin can only be raised, never lowered.** Today a caller may
   pass `--quality-margin 0` on an irreversible unit and replace the risk
   default of 9. A supplied margin should become the maximum of itself and the
   risk default, and the decision should say when it was raised. This is the
   one real hole the reviews found. Seen as an override clamp in NadirClaw's
   cascade rules.
2. **TOOL is the first question, not the third.** The skill lists TOOL first,
   but the guidance reads as a tier choice. Reword the routing guidance so "can
   a deterministic command prove this result?" is asked before any
   classification, and say plainly that the cheapest route is the call not
   made. No code changes: the TOOL branch already returns before any candidate
   logic. No benchmark run has exercised TOOL yet, so its saving is unmeasured.
   Seen in Claude-Pipeline's deterministic QA paths.
3. **Say what Codex Tier adds over native Codex agents.** Native custom agents
   can pin a model and effort per role, and one earlier Codex router now tells
   new users to prefer them over installing it. The guide needs a short paragraph on what
   per-unit routing, calibrated frontiers, the enforced fail-safe to DIRECT,
   and post-unit verification add, or readers will assume the same answer
   applies here.
4. **State the classification failure polarity.** One sentence in the skill: if
   a unit cannot be confidently classified, keep it DIRECT and say so; never
   pick the cheap route by default. The router already fails safe in code; the
   prose that drives classification does not say it. Seen as a fail-closed
   classifier in codex-smart-router.

## Next release

5. **Read the ledger back.** Codex Tier writes a content-free JSONL usage log
   with twenty-two fields and has no command that reads it. Add a `stats`
   subcommand: events by execution mode, by work class and selected pair,
   success and verification rates, escalation counts, and token sums split
   into input, cached input, cache write, output, and reasoning. Plain JSON or
   a table, no server, no port, and never a dollar or credit figure, because
   Codex exposes no credits. Seen in codex-smart-router and in the
   claude-code-model-router dispatch ledger.
6. **Publish quality-preserved figures beside the token figure.** They are
   computable from the existing benchmark data. Against the Sol/low parent
   baseline the per-workload median ratio is about 98.9 percent and matches the
   report's "quality preserved in 5/5". Against always-Sol/max it is about 97.9
   percent, but security review regressed from 91 to 85 and the results file
   already records that a quality-equivalence claim is not defensible, so that
   figure ships only with the comparator named and the regression stated.
   Seen as a "quality preserved" column in NadirClaw's benchmark table.
7. **Run the test suite in CI.** Nothing runs the Codex Tier tests
   automatically. A small workflow on push and pull request, on Linux and
   Windows, running the unit tests and `codex_tier.py validate`, with the one
   test that needs a frozen benchmark checkout skipped for a stated reason.
   Seen in claude-code-model-router, which runs its routing corpus on every
   push.
8. **Escalate on observable output pathologies.** A worker that returns an
   empty or very short final message, or that hit a token cap, has probably
   not done the job. Those signals are already captured and never inspected.
   One escalation step on such a signal costs no model call. The exact Codex
   signals are unmeasured and need a small study first. Seen as truncation and
   refusal triggers in claude-router and as a heuristic screener in NadirClaw.
9. **Unrunnable verification leaves the unit unverified.** The skill assumes
   verification can always run. State the contract for when it cannot: the
   unit is recorded as unverified and the caller is told, never silently
   accepted. This is the opposite polarity to a request proxy, where failing
   open is reasonable; here the failure mode is unverified code.

## Later

10. **Host-observed receipt.** After a worker runs, read the rollout record
    Codex itself wrote and confirm the model, effort, and sandbox that actually
    applied, halting on any mismatch. Today the log echoes the arguments we
    passed. The rollout format is undocumented and changes between Codex
    versions, so this needs a version gate and a feature flag. Seen in
    codex-tier-routing.
11. **Role-bound sandbox.** Let `route` emit a maximum sandbox per work class,
    so a review unit can never run with write access, instead of sandbox being
    an unrelated per-call flag. Seen in codex-tier-routing's agent profiles.
12. **Shadow mode for routing changes.** Record the route a proposed change
    would have taken beside the route actually taken, then compare before
    enforcing. This produces evidence for a change without new infrastructure.
    Seen in Claude-Pipeline's rollout of its deterministic paths.
13. **Pre-register the next benchmark.** Fix interpretation bands before the
    run, and re-score a sample with a clarified judge prompt to publish how
    unstable the judge is. Seen in claude-router's research notes.
14. **A held-out sixth workload.** The frontier pins were calibrated on the
    same five work classes the savings claim is measured over. The next
    benchmark needs at least one class that took no part in calibration.
15. **Warn on deprecated configuration keys.** When a routing knob is removed,
    keep the key in the schema and warn once that it no longer does anything,
    rather than parsing it silently. Seen in claude-router.
16. **A Gaps section in every verification report.** State what was not
    observed, not only what passed. Seen in moai-adk's report format.

## Deliberately not

- A proxy or gateway that rewrites the model per request. The prompt cache is
  keyed by model and effort, and switching either mid-session was measured on
  the Claude Tier side at twenty times the cost of the same turn (see the
  [Claude Tier guide](../claude-tier/README.md)). That measurement has not been
  repeated on Codex.
- A model call to decide routing. The router should not cost tokens to run.
- A dashboard server. It binds a port; the `stats` reader gives the same
  evidence without one.
- A downward per-unit override. Forcing a stronger pair already exists as
  `--escalate-from`; forcing a cheaper one is the downgrade the hard rule
  forbids.
- Dollar or credit savings figures. Codex does not expose credits, and the
  registry's API prices are supplementary metadata by design.
- Copying code from any of these projects. Every item here is reimplemented
  from the described idea.

## Sources

Read in full, September 2026: NadirClaw, moai-adk, claude-router
(serhiileniv), codex-tier-routing (0xTitanas), codex-smart-router,
claude-code-model-router (nobodyohm-web), and Claude-Pipeline (TheAstrelo).
The remaining projects were read at README and configuration depth.
