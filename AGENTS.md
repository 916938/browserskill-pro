# AGENTS.md

## What is this

BrowserSkill Pro is an agent skill that wraps the `bsk` CLI with Python/PowerShell helpers, examples, and layered documentation. It does not contain the CLI or extension source — those live in the [BrowserSkill repo](https://github.com/Tencent/BrowserSkill).

## Structure

| Path | What it is |
|------|------------|
| `skill/SKILL.md` | Primary agent instructions — read this first. |
| `skill/references/protocol.md` | Command parameters, exit codes, privacy constraints. |
| `skill/references/operations.md` | Installation, status checks, failure recovery. |
| `skill/references/how-it-works.md` | Architecture and design rationale (human-only, high context cost). |
| `skill/examples/` | End-to-end workflow examples (form fill, scroll, popup, network, record + replay). |
| `skill/scripts/` | Python and shell helpers (`doctor.py`, `snapshot.py`, `screenshot.py`, `wait_for.py`, `invoke.ps1`, `invoke.sh`, `record.ps1`, `record.sh`, `network.ps1`, `network.sh`, `replay.py`). |
| `skill/agents/openai.yaml` | Optional OpenAI/Codex UI metadata. |
| `tests/` | Unit tests for the Python helpers. |

## Commands

### Run tests

```bash
python -m unittest discover -s tests -v
```

### Lint scripts

```powershell
# PowerShell syntax check
Get-ChildItem .\skill\scripts -Filter *.ps1 | ForEach-Object {
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $_.FullName, [ref]$null, [ref]$errors
    ) | Out-Null
    if ($errors.Count) { throw $errors }
}
```

```bash
# Bash syntax check
bash -n skill/scripts/invoke.sh
```

### Smoke test (requires bsk daemon)

```bash
bsk session start
SESSION_ID=$(bsk session start)
bsk tab list --session $SESSION_ID
bsk session stop $SESSION_ID
```

## Important quirks

- **Python helpers use `bsk_client.py`** — all bsk CLI calls go through this wrapper. Do not call `bsk` directly from other scripts.
- **Windows uses `py -3`** — do not assume `python3` exists on Windows.
- **UTF-8 output** — Python helpers configure UTF-8 stdout themselves. If mojibake appears, use `--mode file` and read the file instead.
- **`invoke.ps1` safety** — `close_session` requires `-Force` flag to prevent accidental tab closure.
- **`doctor.py` is read-only** — it never sends browser actions or starts the daemon.
- **Layered docs** — `SKILL.md` for agent execution, `protocol.md` for parameters, `operations.md` for recovery, `how-it-works.md` for humans only.

## Style conventions

- Python: follow existing patterns in `skill/scripts/`. Minimal comments, clear variable names.
- PowerShell: use `[CmdletBinding()]`, named parameters, `-ErrorAction Stop`.
- Bash: `set -euo pipefail`. Quote all variables.
- Markdown: 2-space indent, LF line endings.
