# Claude Tier

> Part of the [Claude Tier + Codex Tier](../../README.md) repository. Release history: [CHANGELOG](CHANGELOG.md).

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

- **Plan and judge on the session's model; execute through pinned
  sub-agents.** The main session's model and effort are frozen at start
  (the prompt cache is keyed by both - switching either mid-session measured
  20x the cost of the same turn), so sub-agents are the only tier lever.
- **Routes work by shape:** tests, builds and linters run with no model;
  gathering, search fan-out and doc refresh go to Sonnet at low effort; the
  same simple operation over many items goes to Haiku; substantive builds,
  synthesis, verification and final judgment go to **Opus at low effort** -
  measured to hold full quality where Sonnet did not at any effort.
- **Model is the strong lever, effort the weak one.** Effort spread within a
  model measured 1.3-1.6x in cost; model spread 2-5x. Low is the default;
  `max` is never a default (2-5x the cost of low for no correctness gain).
- **Fable 5.1 is an escalation, not a default:** the hardest frontier
  reasoning, high-stakes research, a tie-break after an Opus attempt fails,
  or an explicit request. Measured total cost ran 1-2x Opus/low by task with
  no quality edge on any shape measured. Without Fable on the plan, Opus at
  max is the ceiling - the rule never stalls on an unavailable model.
- **Newest model within a tier, always** - same or lower price, better model.
- **Every sub-agent is pinned** (model, effort, tools) and pays a boot cost
  before any work (~10K tokens on Haiku, ~44K on Opus, 3x that with
  `tools: *`), so small one-shot work stays inline. Independent same-tier
  agents go out in one batch; a pinned-low agent that meets more than its
  brief replies `ESCALATE:` and is re-run one tier up.
- **Routing is free:** the rule is a lookup table, not a deliberation. Small
  tasks skip routing entirely and run on the current model.
- **Per-task fit:** *downgrade* clearly mechanical work directly; *upgrade*
  only after asking you first.
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
