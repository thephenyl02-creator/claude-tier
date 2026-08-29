# tier - model & effort tiering for Claude Code

A tiny, opinionated Claude Code skill: run **`/tier`** in any project and it
installs a standing *model/effort-tiering* working preference for that
project. From then on, that project runs **quality-first and
cost-efficient** - automatically. By default the rule lands in a
machine-local `CLAUDE.local.md`, so **your repo stays clean** - teammates and
diffs never see your personal preference; `/tier repo` commits it instead
when you want web + mobile coverage too.

Simple on purpose. It doesn't hook, poll, or call anything - it writes one
clear rule into the file Claude Code always reads, and gets out of the way.

## What the rule does

- **Plan on the highest model available**; every plan assigns a model tier
  **and** an effort level (low to max) per work item.
- **Routes work to the right tier:** deterministic batteries (tests, builds,
  linters) run with no model at all; mechanical gathering to Sonnet;
  substantive builds, verifiers, correctness/security reviews, and final
  judgment to Opus - since Opus 5, Opus is the default top tier.
- **Fable is an escalation, not a default:** roughly 2x Opus cost and heavier
  token use for an overall lead that is now marginal (Opus 5 wins several
  areas outright). The rule reserves Fable for the longest, hardest
  frontier-reasoning work, high-stakes deep research, large or high-stakes
  work in the domains where Fable actually benchmarks ahead (long-horizon
  software engineering, legal/compliance-critical analysis, deep security
  analysis), tie-break adjudication after strong models disagree, or an
  explicit request.
- **Subscription-aware:** on plans without Fable (e.g. Claude Pro), Opus is
  simply the top tier - would-be escalations run on Opus at max effort, and
  the rule never stalls on an unavailable model. No configuration needed; it
  adapts to whatever models the session actually has.
- **Routing is free:** the rule is a lookup table, not a deliberation. The
  routing decision must never cost more tokens than it can save - small tasks
  skip routing entirely and just run on the current model.
- **Written for the model:** the installed block is compact, imperative
  markdown optimized for Claude to follow (and cheap to load every session),
  not prose for humans to study.
- **Per-task fit:** *downgrade* to a cheaper model directly when the work is
  clearly mechanical; *upgrade* only after asking you first.
- **Hard rule that overrides everything: never compromise quality.** Any doubt
  whether a downgrade would hurt = don't downgrade.

## Install

Three paths - pick the one that matches you.

### 1. New to Claude Code? One command sets up everything

Nothing needs to be installed first - not even Claude Code itself.

**macOS / Linux / Ubuntu / WSL** (any bash shell):

```
curl -fsSL https://raw.githubusercontent.com/thephenyl02-creator/claude-tier/main/install.sh | bash
```

**Windows** (PowerShell):

```
irm https://raw.githubusercontent.com/thephenyl02-creator/claude-tier/main/install.ps1 | iex
```

The installer absorbs everything that usually goes wrong on a fresh machine:
it installs the Claude Code CLI if it's missing, works even when `claude`
isn't on your PATH yet, never depends on your git/SSH setup, and if the
plugin route is still blocked it falls back to copying the skill directly
into `~/.claude/skills/` - no git needed at all. It changes nothing outside
its job: your git config and shell session are left exactly as found. Safe to
re-run any time; it updates an existing install.

### 2. Already have Claude Code? Two commands

From any terminal:

```
claude plugin marketplace add thephenyl02-creator/claude-tier
claude plugin install tier@claude-tier
```

Or the same thing inside a Claude Code session:

```
/plugin marketplace add thephenyl02-creator/claude-tier
/plugin install tier@claude-tier
```

(Typed `/plugin` commands exist only in the terminal CLI. On the **desktop
app**, click **+** next to the prompt box -> **Plugins** -> **Add plugin** ->
add marketplace `thephenyl02-creator/claude-tier` -> install **tier**.)

### 3. Plugin authors & the git-averse: fully native, fully git-free

The marketplace can be added straight from its manifest URL, and the plugin
itself ships as a sha256-pinned zip archive - so the whole chain installs
over plain HTTPS, even on machines with no git or SSH configured:

```
claude plugin marketplace add https://raw.githubusercontent.com/thephenyl02-creator/claude-tier/main/.claude-plugin/marketplace.json
claude plugin install tier@claude-tier
```

**Cloud (claude.ai/code):** cloud sessions have no plugin browser - declare
the plugin in the repo's `.claude/settings.json` instead, and it installs at
session start:

```json
{
  "extraKnownMarketplaces": {
    "claude-tier": {
      "source": { "source": "github", "repo": "thephenyl02-creator/claude-tier" }
    }
  },
  "enabledPlugins": { "tier@claude-tier": true }
}
```

(In a cloud session `/tier` will offer to install in repo mode - untracked
local files don't survive there, so durable coverage needs the committed
`CLAUDE.md`.)

Then, in any project:

```
/tier
```

By default the rule lands in the project's `CLAUDE.local.md` - a
machine-local file Claude Code loads right alongside `CLAUDE.md` - and it's
kept out of version control via `.git/info/exclude`, so even your
`.gitignore` stays untouched. **Nothing about your repo changes.** Your
personal routing preference stays yours instead of being pushed onto every
collaborator.

Want the rule on web (claude.ai/code) + mobile too? Those surfaces only read
committed files, so that coverage requires committing it:

```
/tier repo
```

writes the block into the committed `CLAUDE.md` instead (and offers the
commit).

If the project already carries an **older version** of the rule, `/tier`
upgrades the block in place automatically; if it's already current, it skips.
If an old install lives in your committed `CLAUDE.md`, `/tier` offers to
migrate it out to `CLAUDE.local.md`.

Not inside a git repo? `/tier` still works: the rule lands in the current
directory's `CLAUDE.md` as a machine-local install (sessions launched there
load it; web + mobile only read committed repo config).

## Troubleshooting

Every entry below is a real blocker someone hit installing this. The
one-command installer handles all of them automatically - these are the
manual fixes if you're doing it by hand.

- **`command not found: claude`** - the Claude Code CLI isn't installed, or
  it's installed but `~/.local/bin` isn't on your PATH. Install:
  `curl -fsSL https://claude.ai/install.sh | bash`, then follow its PATH note
  (usually `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc` and open
  a new terminal).
- **`permission denied: ~/.zshrc`** while adding the PATH line - your shell
  profile is owned by root (usually from an old `sudo` mishap). Reclaim it:
  `sudo chown $(whoami) ~/.zshrc`, then retry.
- **`/plugin isn't available in this environment`** - typed `/plugin`
  commands exist only in the terminal CLI. On the desktop app use **+ ->
  Plugins -> Add plugin**; on claude.ai/code use the `settings.json` route
  above.
- **`Host key verification failed` / `No ED25519 host key is known for
  github.com`** during install - git is trying SSH without SSH set up (a
  missing `~/.ssh` also means no key, so fixing `known_hosts` alone won't
  help). Make git use HTTPS for GitHub:
  `git config --global url."https://github.com/".insteadOf "git@github.com:"`
  and retry. The repo is public - HTTPS needs no credentials. (Since 1.6.0
  the plugin itself ships as a zip over HTTPS, so git only comes into play
  when the marketplace was added in `owner/repo` form.)
- **`This plugin uses a source type your Claude Code version does not
  support`** - zip-archive plugins need Claude Code v2.1.224+. Update Claude
  Code (`claude update`) and retry.

## Why "simple is best"

Other routers auto-switch your model via hooks, or ship complex config
profiles. This one is deliberately minimal: one command, one durable rule, no
moving parts to break. You stay in control of the actual model; the rule just
keeps every session honest about tiering - and never trades quality for cost.

## Release notes

- **1.7.8** - Puts the rule back to being a rule. Versions 1.7.1 through 1.7.7
  each folded a fresh measurement into the rule text, and by 1.7.7 the
  delegation bullet had grown to **17 lines** carrying five separate ideas plus
  a bracketed provenance note. The rule's own opening line demands that routing
  be "a lookup, never a deliberation" - it had stopped being one. No instruction
  is lost here: the boot figures, the tier-drop inversion and the single-source
  caveats all live in these release notes, which is where evidence belongs. The
  rule keeps the two numbers that actually change behaviour (~10K vs ~44K boot,
  and the ~$0.28 an unpinned Opus agent costs before doing anything) and states
  the condition in one sentence instead of a paragraph.
- **1.7.7** - The thrashing penalty was understated, and the headline claim is
  now verified rather than assumed. **(1)** Every version said cache writes bill
  `1.25x` and reads `0.1x`. That is the FIVE-MINUTE TTL figure; a Claude
  subscription's main conversation runs on the one-hour TTL, which bills writes
  higher. Solved from the controlled run: 57,631 tokens written cost $0.3459
  while 57,583 tokens read cost $0.0174 - **a write costs ~20x a read for the
  same tokens**, implying ~2x base rather than 1.25x. So a thrashing session
  pays roughly DOUBLE list price, not a quarter over. **(2)** "An unpinned
  sub-agent inherits the session model" has been the skill's central claim since
  1.0.0 and had never been tested. It holds: an unpinned agent spawned from an
  Opus 5 session ran on Opus 5 - and burned **44,363 tokens to reply "OK"**,
  about $0.28. That figure now stands in the rule as the concrete cost of
  forgetting to pin. **(3)** The boot floor is stated per-tier instead of as a
  flat "~10+ turns", since 10K on Haiku and 44K on Opus clear at very different
  amounts of work.
- **1.7.6** - Delegation overhead is not a constant either; it depends on
  whether the tier actually drops. Every version since 1.7.0 carried a `~1.6x
  token overhead of delegating`, taken from one published measurement and used
  to derive the `>1.7x` break-even. Tested directly - identical bounded task,
  one session counting files itself, one spawning a Haiku sub-agent to do it,
  both answers correct and the sub-agent's tokens included in the parent's
  total via `modelUsage`:

  ```
  inline    (sonnet, 6 turns)              206,465 tokens   $0.1702
  delegated (sonnet 2 turns + haiku)       102,829 tokens   $0.1399   0.82x
  ```

  Delegating was **cheaper**, not 1.6x dearer. The likely reconciliation: the
  published figure delegated to the SAME model, so it measured pure overhead
  with no tier drop, while a real drop lets the cheap tier work in its own
  small context instead of growing the expensive one. The rule now says the
  ~1.6x is a same-model figure and records the measured inversion, marked n=1.
- **1.7.5** - The fan-out claim, now measured; and the last trusted number,
  now labelled. "Batch by configuration" entered the rule in 1.7.0 on the
  strength of documentation plus one blog measurement. Verified directly:
  three independent agents dispatched in one parallel batch produced
  `read=0 / write=9,802` for the first and `read=5,755 / write=4,055` for each
  of the other two - **17,912 boot tokens against ~29,406 run separately,
  about 39% less** - and the shared portion bills as reads (0.1x) rather than
  writes (1.25x), so the cost gap is wider than the token gap. The rule now
  carries those figures. Separately, the `~1.6x` delegation overhead and the
  `>1.7x` break-even derived from it are marked inline as resting on a single
  published measurement of three tasks, unverified here - the direction is
  sound, the exact threshold is not established.
- **1.7.4** - Corrects the Haiku effort claim. Earlier versions said Haiku "has
  no effort dial", and the reference Haiku agent carried no `effort:` line on
  that basis. **Both were wrong.** Measured directly, same prompt, same model:
  Haiku at `low` produced 1,149 output / 445 thinking tokens; at `max`, 1,979 /
  925. The dial works - it simply has a narrow range. For contrast the same
  prompt on Sonnet went 1,544 -> 14,673 output (155 -> 12,002 thinking), a 9.5x
  swing against Haiku's 1.7x. Passing `--effort` to Haiku also does not error,
  as had been assumed. The routing table now states the narrow range instead of
  denying the dial, and the reference Haiku agent declares `effort: low`.
- **1.7.3** - Retracts 1.7.2's central claim. 1.7.2 stated that declaring a
  narrow `tools:` list cuts an agent's boot cost ~4x. **That was wrong.** It
  rested on a group comparison - 23 "restricted" runs averaging 9.6K boot
  against 17 "full-tool" runs averaging 37.7K - in which the two groups also
  differed by MODEL. A controlled A/B run afterwards, same model (Opus 5), same
  trivial task, one agent tool-restricted and one not, came back **44,148 vs
  44,394 tokens - a 0.6% difference**. The `tools:` frontmatter governs what an
  agent may call, not what is loaded into its prompt. Boot scales with the
  model instead: ~10K on Haiku, ~44K on Opus, measured. The rule now says that.
  The reference agents keep their tool lists, but on the honest justification:
  the verifier and adjudicator have no write access because a checker that can
  edit what it was asked to assess is a failure mode - that argument never
  depended on cost. Lesson worth recording: 1.7.2 shipped a cause inferred from
  correlated groups without an A/B, in a release whose own subject line was
  "measured, not assumed".
- **1.7.2** - Boot cost is not a constant; it depends on the agent's tool set.
  1.7.1 put a single "~35-50K tokens to boot" figure in the rule. Measured
  across 40 real sub-agent runs, boot splits cleanly: **~9.6K average for
  tool-restricted agents vs ~37.7K for full-tool ones - a 3.9x gap**. The
  expensive definitions are consistently `Skill`, `Agent`, `ToolSearch` and MCP
  tool sets, not the count of tools as such. So **declaring a narrow `tools:`
  list in agent frontmatter is a cost lever, not just a safety one** - it cuts
  boot roughly fourfold and therefore lowers the amount of work an agent needs
  to be worth spawning. The rule now states both figures and names the lever.
  The reference agent set was updated to declare tool lists throughout; the
  verifier and adjudicator additionally lose write access, which is a
  correctness improvement as much as a cost one - a checker that can edit what
  it was asked to assess is a failure mode, not a feature.
- **1.7.1** - Adds the floor 1.7.0 was missing. 1.7.0 told you *which* tier to
  delegate to but never *whether* the task was worth delegating at all. Measured
  on 222 real sub-agent runs: an agent pays **~35-50K tokens just to boot**
  (system prompt, memory, tool definitions) before doing any work, and that cost
  is flat regardless of task size. The one agent in the sample that ran three
  turns or fewer spent **463x more on boot than the work it produced**. So a
  small one-shot task is cheaper done INLINE however cheap the agent's model -
  and 1.7.0's `>1.7x cheaper` test, taken alone, actively recommended the wrong
  thing. The rule now requires BOTH: enough work to amortise the boot (roughly
  10+ turns) AND either a meaningfully cheaper tier or context-hygiene grounds.
  Consequences for the reference agent set: a Haiku agent scoped to "one small
  bounded lookup" was exactly backwards and is recast for high-volume simple
  work across many items; an executor agent is scoped to substantial changes,
  with small edits explicitly left inline. Provenance note: the ~1.6x
  token overhead of delegating comes from a single published measurement of
  three tasks, whereas the boot-cost figures above are measured from 222 runs.
- **1.7.0** - Measured, not assumed. A live experiment changed the rule.
  **(1) Model AND effort are both frozen at session start.** The prompt cache
  is keyed by both, so changing either mid-session drops `cache_read` to zero
  and rebuilds the entire prefix - measured at **20x the cost of the identical
  turn** ($0.017 -> $0.346), with a control turn confirming the cache returned
  as soon as the setting was held steady. 1.6.0 was silent on this, and an
  earlier draft of 1.7 wrongly claimed effort changes were cache-free.
  **(2) Delegation is now the only mid-session tier lever**, with a threshold:
  delegating costs ~1.6x the tokens of working inline, so it pays when either
  the tier drops >1.7x or the material would otherwise sit in the main context
  being re-read on every later turn. Same-tier delegation buys only the second.
  **(3) Effort is pinned in agent frontmatter**, not on the `Agent` call - that
  tool has no effort parameter, so a plain delegation silently inherits session
  effort. Also new: batch independent same-tier agents into ONE parallel
  fan-out (they share the prefix the first one cached); thrashing the cache
  costs *more* than not caching at all (writes bill 1.25x, reads 0.1x); re-run
  a weak sub-agent one tier UP rather than accepting a cheap wrong answer;
  never Opus 4.6 or Sonnet 4.6 (same or higher price than their successors and
  no `xhigh`); Opus 5 starts at `high`, not `xhigh`. Block tag is now
  `tier-rule v1.7` - `/tier` auto-upgrades older installs in place.
- **1.6.0** - Butter-smooth install, clean repos. Two changes.
  **(1) One-command installers** for macOS/Linux (`install.sh`) and Windows
  (`install.ps1`) that absorb every blocker observed in the wild: missing
  Claude Code CLI (auto-installs it), `claude` not on PATH (uses the absolute
  path; persists PATH only when the shell profile is actually writable, with
  the `chown` fix printed when it isn't), and SSH-to-GitHub failures (forces
  HTTPS via env vars for the install only - your git config is never
  touched). If the plugin route still fails, the installer falls back to a
  direct no-git skill copy into `~/.claude/skills/`. The plugin itself now
  ships as a **sha256-pinned zip archive** (release asset), and the
  marketplace can be added straight from its manifest URL - so the native
  plugin flow works end-to-end with no git on the machine at all. README
  gains audience-based install paths (beginner one-liners per platform,
  two-command CLI path, git-free native path, desktop GUI, cloud
  `settings.json`) and a troubleshooting section.
  **(2) `/tier` no longer touches your repo by default.** The rule is a
  personal working preference, so it now lands in a machine-local
  `CLAUDE.local.md` kept untracked via `.git/info/exclude` (not even your
  `.gitignore` changes); previously it was written into the committed
  `CLAUDE.md`, pushing one person's preference onto every collaborator.
  `/tier repo` keeps the old behavior as an explicit opt-in for web + mobile
  coverage, and `/tier` offers to migrate pre-1.6 blocks out of committed
  `CLAUDE.md`. Block tag is now `tier-rule v1.6` (heading made
  location-neutral; rule content unchanged) - `/tier` auto-upgrades older
  installs in place.
- **1.5.0** - Corrects 1.4.0's reasoning and hardens the response. 1.4.0
  implied that keeping web content out of the frontier context would avoid
  mid-task model downgrades. **That was wrong** - a downgrade was later
  observed on a routine README edit with no web content involved. 1.5.0
  therefore states plainly that **downgrades are unpredictable and cannot be
  prevented**, keeps the delegate-bulk-content rule but justifies it purely
  as *routing* (it is Sonnet-tier work regardless), and turns the response
  into a numbered protocol ending in the step 1.4.0 missed: **after the model
  is restored, re-verify any quality-critical output produced during the
  downgrade window.** A silent tier loss is only harmless if nothing
  important was decided inside it.
- **1.4.0** - First attempt at guarding mid-task model downgrades: delegate
  web fetches to cheap sub-agents, announce downgrades, pause judgment work.
  Superseded by 1.5.0, whose rationale is correct.
- **1.3.0** - Anti-drift rules, learned from a long session where the routing
  silently decayed. Three additions: **pin every sub-agent** (an unpinned
  agent inherits the session model, so mechanical fan-out silently runs at
  frontier prices with no visible signal); a **capacity-error repair rule**
  (a rate-limited tier means retry that agent elsewhere, never strip pins
  globally - and restore them immediately if you do); and **state the routing
  before spending it** (any 3+ agent fan-out announces "6 x Sonnet/medium"
  first, so a mis-route is caught before the tokens, not after). Block tag is
  now `tier-rule v1.3`; `/tier` auto-upgrades older installs in place.
- **1.2.1** - `/tier` now handles non-repo directories (home folder, scratch
  space, unversioned code): it installs into the current directory's
  `CLAUDE.md` as a machine-local rule instead of skipping. Installed block
  unchanged (still `tier-rule v1.2`) - existing installs need nothing.
- **1.2.0** - Subscription-aware (plans without Fable treat Opus as the top
  tier automatically); Fable escalation triggers now cover its benchmarked
  strengths (high-stakes deep research, long-horizon software engineering,
  legal/compliance-critical and deep security analysis); canonical block
  rewritten model-first (compact, imperative, cheaper per session); versioned
  upgrade tag (`tier-rule v1.2`) so `/tier` upgrades reliably across future
  releases.
- **1.1.0** - Opus 5 era routing. Opus is now the default top tier (including
  reviews, synthesis, and final judgment); Fable becomes an explicit
  escalation with named triggers. New "routing is free" principle. `/tier`
  now auto-upgrades older installed blocks in place.
- **1.0.0** - Initial release.

## License

MIT (c) Fenil K Ventures LLC
