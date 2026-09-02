# Claude Tier + Codex Tier

This repository ships two independent quality-first routing systems. They
coexist, install separately, and do not share model-routing logic.

| Product | Designed for | Routing model | Invocation |
| --- | --- | --- | --- |
| **Claude Tier** | Claude Code | Claude intelligence/model routing with deterministic tools and tiered delegation | `/tier` |
| **Codex Tier** | Codex | Quality-constrained compute routing across tools, direct execution, and pinned model × reasoning effort workers | `$codex-tier` |

## Codex Tier

Codex Tier treats model and reasoning effort as separate dimensions. For each
meaningful work unit it chooses TOOL, DIRECT, or the cheapest calibrated
model × effort candidate expected to meet the quality bar with a confidence
margin. It verifies the result and selectively escalates only the affected
unit.

For the five stabilized v1 workloads, corrected evidence selects an explicitly
pinned `gpt-5.6-sol/low` worker. This remains Sol/low even when the invoking
Codex session is running Sol/max or Sol/xhigh; ordinary DIRECT routes continue
to mean the unchanged current parent.

**macOS / Linux / WSL:**

```bash
curl -fsSL https://raw.githubusercontent.com/thephenyl02-creator/claude-tier/main/install-codex.sh | bash
```

**Windows PowerShell:**

```powershell
irm https://raw.githubusercontent.com/thephenyl02-creator/claude-tier/main/install-codex.ps1 | iex
```

Then start a new Codex task and invoke:

```text
$codex-tier

<normal task>
```

Users do not choose a model, reasoning effort, worker count, or escalation
path. The active matrix is discovered per Codex client/account. See
[CODEX-TIER.md](CODEX-TIER.md) for architecture,
enforcement, configuration, logging, tests, and current limitations.

The [authoritative consolidated benchmark report](benchmarks/codex-tier-e2e/CONSOLIDATED-BENCHMARK-REPORT.md)
documents the complete calibration and benchmark history, corrected evidence,
superseded results, final routing decisions, and the exact limits of the v1
exposed-token claims. It separates the directly measured pre-correction Tier
comparison (9.83% median / 12.57% mean reduction versus always Sol/max) from
the compatible-observation final-route derivation (13.82% median / 15.52%
mean). Neither is a credit, billing, dollar, or quota-savings claim.

---

# Claude Tier

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
