# First real Codex calibration

Measured August 25, 2026 with official `codex-cli 0.149.1` and the current
account's Codex model catalog.

## Candidate discovery and execution

The client advertised 29 pairs across six coding-capable models. `none` was not
exposed and was excluded. Real launch probes succeeded for all 29; none were
marked unavailable. The runner then made 87 comparable workload calls: every
pair received the same inline synthetic repository snapshot for each of bulk
repository scan, difficult debugging, and security review.

All 87 workers succeeded and passed verification. There were zero retries and
zero error events. Quality scores ranged from 95 to 100. The longest call was
`gpt-5.4-mini/xhigh` on difficult debugging at 143.429 seconds.

## Usage and first frontier

Codex JSONL exposed input tokens, cached input tokens, output tokens, and
reasoning output tokens. It did not expose Codex account credits or a mapping
from those token counters to subscription consumption. The provisional primary
metric is therefore `input_tokens + output_tokens`; cached and uncached counts
remain separate secondary evidence.

For each of the three fixtures, `gpt-5.4-mini/low` scored 100 and had the lowest
primary measured total:

| Workload | Total exposed tokens | Uncached input | Output |
| --- | ---: | ---: | ---: |
| bulk repository scan | 12,382 | 501 | 233 |
| difficult debugging | 12,742 | 652 | 442 |
| security review | 12,492 | 491 | 353 |

Every other pair was dominated on these fixtures. GPT-5.5 therefore does not
occupy the first measured frontier. This is one trial per pair on three narrow
synthetic fixtures, not a general claim that one model wins all coding work.
No savings percentage is published.

Full evidence is in `candidate-matrix.json`,
`real-calibration-results.json`, and `measured-frontiers.json`.

## Exact local Windows command

If a managed shell cannot invoke the installed CLI, run this in a normal
PowerShell session from the repository root:

```powershell
npm install --global @openai/codex@0.149.1
$codex = (Get-Command codex.cmd).Source
python .\plugins\codex-tier\skills\codex-tier\scripts\calibrate.py --run --codex-bin $codex --timeout 300
```

The fixtures are inline because the managed Codex policy rejected nested shell
inspection even in isolated read-only fixture directories. They contain no
user repository data or production state.
