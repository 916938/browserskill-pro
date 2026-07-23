# Record a Flow, Replay with Different Values

Use this when the user does a task once and asks the agent to repeat it — with new inputs — later. Recording captures *what the user did*; the agent decides at replay time which values are variable.

The one-shot alternative (agent watches, then re-does live) is fine for a single repetition. Prefer record → replay when the flow will run multiple times, or when the agent needs a durable artifact (e.g. cron, CI).

## 1. Record

Ask the user to run the flow themselves. Recording is user-driven and blocks until they click **Finish** in the Agent Window's recording panel.

```bash
scripts/record.sh start \
  --purpose "publish a wiki doc" \
  --url "https://wiki.example.com/new" \
  --output ./flows/publish.json
```

```powershell
& scripts\record.ps1 start `
  -Purpose "publish a wiki doc" `
  -Url "https://wiki.example.com/new" `
  -Output .\flows\publish.json
```

Do **not** record on banking, SSO, or password-manager pages. Passwords are auto-redacted, but the trace may still contain sensitive text.

## 2. Inspect the trace

Open `publish.json` and skim the `steps` array. Each step is one of `navigate`, `click`, `fill`, `select`, `press` — with a semantic `target` (role + name), not a CSS selector. Figure out which `fill` values are variable (title, body) and which are constants (category, tag).

`redacted: true` fill steps mean the user typed a password; the recorded `value` is a placeholder, not the real password.

## 3. Dry-run first

Always plan before executing. `--dry-run` runs `bsk snapshot` for target resolution but does not click / fill / navigate:

```bash
SID=$(bsk session start)
python3 scripts/replay.py ./flows/publish.json --session "$SID" --dry-run
```

Read the output. Every step should print a resolved `@eN` ref. If any step reports **no ref matches** or **ambiguous**, either the page differs from recording or the target's name has drifted — pick a different starting page or re-record.

## 4. Replay for real, substituting variable values

`replay.py` today runs the trace verbatim; to change values, either edit the trace JSON in place (preserve `id` / `page` fields) or open the trace, walk the steps, and call the equivalent `bsk` commands with new values:

```bash
# In-place edit (jq or Python) — swap the title, keep everything else
python3 -c '
import json, sys, pathlib
t = json.loads(pathlib.Path("flows/publish.json").read_text(encoding="utf-8"))
for step in t["steps"]:
    if step["op"] == "fill" and step["target"].get("name") == "标题":
        step["value"] = sys.argv[1]
pathlib.Path("flows/publish.instance.json").write_text(json.dumps(t, ensure_ascii=False), encoding="utf-8")
' "GPU 日报 2026-07-23"

python3 scripts/replay.py ./flows/publish.instance.json --session "$SID"
```

## 5. Handle failures

- **Ambiguous / missing target**: replay halts with the step id. Re-run the earlier steps that reached that page, snapshot the page, and check whether the recorded `role`/`name` still identifies a unique element. Fix the trace target or re-record.
- **Redacted fill**: `replay.py` refuses. Call `bsk request-help` to ask the user, or edit the trace to drop `redacted:true` and supply the real value (only when the user asked for it, not silently).
- **Mid-flow crash**: resume with `--from-step N`, where `N` is the step id reported in the error.

## 6. Clean up

```bash
bsk session stop "$SID"
```

Always run `session stop` — even on error paths. Idle timeout is 5 min and is not a substitute.
