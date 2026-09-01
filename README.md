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

Other routers auto-switch your model mid-session via hooks, or ship complex
config profiles. This one deliberately does neither, and there is now a
measurement behind that rather than a preference.

The prompt cache is keyed by model AND effort. Switching either mid-session
drops `cache_read` to zero and forces a full rebuild - measured at **20x the
cost of the identical turn** ($0.017 -> $0.346), with a control turn confirming
the cache returned as soon as the setting was held steady. An auto-switching
router pays that toll every time it fires. Worse, a cache write costs about
20x a cache read for the same tokens, so a session that keeps invalidating
pays roughly double list price - not merely losing a discount.

So: one command, one durable rule, no moving parts to break. You stay in
control of the actual model; the rule keeps every session honest about
tiering, and never trades quality for cost.

### One dependency worth knowing

The rule tells you to pin a sub-agent's effort in `.claude/agents/*.md`
frontmatter, because the `Agent` tool exposes no effort parameter. **`/tier`
does not create agent files** - that part is yours. The minimal shape is:

```markdown
---
name: scout
description: <one line on exactly when to reach for it>
model: sonnet
effort: low
tools: Read, Grep, Glob, Bash
---
<the agent's instructions>
```

Boot cost is worth knowing before you write these: a sub-agent pays roughly
10K tokens to start on Haiku and 44K on Opus, flat regardless of task size,
so small one-shot work is cheaper done inline however cheap the model. List
the tools you need rather than `*`: the wildcard loads every MCP schema and
measured 3x the boot on the same model.

## Release notes

- **1.10.0** - The measured rule, audited. Four sweep rounds (125 graded
  agent runs across build, bug-fix, refactor, integration, long build,
  verification, synthesis and a deliberately hard build, every grader
  validated against a baseline and a reference before any model ran) settled
  the model-versus-effort question: **model is the strong lever, effort the
  weak one.** Opus at LOW effort held full quality on the one edge case Sonnet
  failed at low, medium and high; a 19-test hard build came back perfect from
  every cell, so a low pin does not degrade on difficulty - only on ambiguity,
  which is what the new `ESCALATE:` hatch is for (a pinned-low agent that
  meets more than its brief hands the task back; the caller re-runs it one
  tier up). `max` is now "never by default": 2-5x the cost of `low` for no
  correctness gain in 48 runs. Then an independent adversarial read of the
  rule found that its headline verification claim ("Fable 5.1 catches what
  Opus misses") rested on a grader flaw - the scored bug sat in a function
  with no docstring while the spec said "does not do what the docstring
  says". Re-measured with a fair criterion: Opus/low 4/4, Fable/low 4/4,
  Sonnet/low 3/4. So the verification lane is retracted, Fable 5.1 is
  escalation-only again with an honest cost line (list output 2x Opus,
  measured total 1-2x by task, no quality edge on any shape measured), and
  the reference agent set pins verification and integration to Opus/low -
  the integrator had been paying 2.7x for a tighter summary a prompt line
  buys. Boot cost gained a clause: it tracks the model AND whether the agent
  takes `tools: *` (every MCP schema, measured 3x the boot), not which
  built-ins it lists. A zero-token hook that rewrites unpinned `Agent` calls
  was built, proven, and rejected as unnecessary at a 3% miss rate - the rule
  stays one block with no moving parts. Block tag `tier-rule v1.10.0`.
- **1.9.0** - Newest-in-tier, and Fable 5.1. The per-version deny list ("never
  Opus 4.6 or Sonnet 4.6") was a special case of a general rule the routing
  table now states once: **within a tier, always the newest model** - same or
  lower price, better model. Verified against the live pricing page: Opus 5,
  4.8, 4.7 and 4.6 are all $5/$25; Sonnet 5's $2/$10 (introductory pricing now
  made permanent) undercuts Sonnet 4.6's $3/$15; Fable 5.1 matches Fable 5's
  $10/$50 with **cache reads at a quarter of the price** and materially higher
  benchmarks. Fable 5.1 is therefore the Fable the rule means. Two practical
  facts ride along: the short alias `fable` still resolves to Fable 5, so pin
  by full model ID where an alias lags (agent frontmatter honors full IDs -
  verified at runtime); and because Fable 5.1's cache reads are half of Opus
  5's, long cache-bound sessions narrow the "2x Opus" gap the escalation rule
  assumes. Block tag `tier-rule v1.9.0`; `/tier` upgrades older installs in place.
- **1.8.1** - `/tier` is now aware of a user-level global rule. The skill only
  ever read PROJECT files, so a user carrying the rule in `~/.claude/CLAUDE.md`
  (which loads automatically in every session) who ran `/tier` in a project got
  a second ~900-token copy loading alongside the global on every turn - the
  skill's own author accumulated six stale project copies this way before
  noticing. New step 0 checks the user-level file first: already covered by a
  same-or-newer global in local mode -> stop and say so; global older than the
  skill -> offer to upgrade the GLOBAL in place (one copy, every project);
  `/tier repo` proceeds regardless, since committed-file coverage for web and
  mobile sessions is its whole point, noting that local sessions in that
  project will then load both copies. Rule content is unchanged - the block tag
  stays `tier-rule v1.8.0` and existing installs are untouched.
- **1.8.0** - The first release since 1.6.0, and the first whose every number
  was measured rather than reasoned about. 1.6.0 was not broken; it was simply
  built on assumptions nobody had tested. Everything in between was unreleased
  development - including several corrections that never reached anyone, which
  is why it collapses into this one entry rather than a run of them. The commit
  log carries that detail.

  **Measured, reproducible on any machine:**
  - Switching model OR effort mid-session drops `cache_read` to zero and costs
    **20x the identical turn** ($0.017 -> $0.346), with a control turn proving
    the cache returns once the setting holds. Both are start-of-session choices.
  - A cache WRITE costs ~20x a cache READ for the same tokens, so a thrashing
    session pays roughly **double list price** - not merely losing a discount.
  - A sub-agent pays a flat BOOT cost before doing any work: **~10K on Haiku,
    ~44K on Opus** (~$0.28). It scales with the MODEL, not the agent's `tools:`
    list - a controlled A/B differed by 0.6%. Small one-shot work is therefore
    cheaper INLINE however cheap the model.
  - An unpinned sub-agent really does inherit the session model - verified, and
    it burned 44,363 tokens to reply "OK".
  - A parallel fan-out shares the prefix the first agent cached: three agents
    dispatched together wrote **17.9K boot tokens against ~29.4K separately**.
  - Delegation overhead is not a constant. WITH a real tier drop it inverts -
    a bounded task cost **0.82x** delegated versus inline.
  - Haiku's effort dial works, with a narrow range: 1.7x low-to-max against
    Sonnet's 9.5x.

  **Also fixed:** the routing table no longer contradicts the boot floor; the
  rule states each condition in one sentence instead of a paragraph of
  evidence; and the README documents that pinning sub-agent effort needs
  `.claude/agents/*.md` files, which `/tier` does not create.

  **If you installed between 14 Aug and now, you had 1.6.0 regardless of what
  this repo said.** The plugin manifests pin a release asset by URL and
  sha256, and they had been left at 1.6.0, so the marketplace served that
  build no matter what landed on `main`. Fixed here, and the verification
  suite now fails if the published release and the pinned version ever
  diverge again.
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
