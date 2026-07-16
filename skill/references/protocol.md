# Command Protocol

Use `bsk` CLI with JSON output:

```bash
# Start a session
bsk session start

# Navigate
bsk navigate "https://example.com" --session <session-id>

# Create new tab
bsk tab create --url "https://example.com" --session <session-id>
```

Keep `--session` and reuse one session ID for the task.

## Global flags

| Flag | Purpose |
|---|---|
| `--json` | Machine-readable JSON on stdout (errors too) |
| `--quiet` | Suppress informational stderr |
| `-v` / `-vv` | More verbose logging |

Command-specific flags: run `bsk <cmd> --help`.

## Exit codes

| Code | Meaning | Action |
|---|---|---|
| `0` | Success (including `evaluate` where JS threw but RPC succeeded) | Continue |
| `1` | User error — bad args, unknown session, tab not in Agent Window, stale ref | Fix args; `bsk session list`; re-snapshot |
| `2` | Protocol / transport — service unreachable, IPC failure | `bsk doctor`; check extension connected; retry |
| `3` | Browser / CDP execution failed | Retry; simplify selector; check tab still open |
| `4` | Timeout | Increase `--timeout`; try `--wait-until domcontentloaded` |
| `5` | Version skew (CLI vs extension) | Upgrade/reinstall matching versions |

Human errors print `error:` + `hint:` on stderr; `--json` includes `code`, `message`, `hint`, `exit_code`.

## Helper scripts

PowerShell accepts a hashtable directly:

```powershell
bsk fill "@e10" --value "显卡日报" --session demo
```

For PowerShell, use a UTF-8 JSON file when arguments contain non-ASCII text, nested objects, or complex quoting:

```powershell
@'
{
  "selector": "@e10",
  "value": "显卡日报：RTX 5090 价格"
}
'@ | Set-Content -LiteralPath .\bsk-args.json -Encoding UTF8
bsk fill "@e10" --value "显卡日报：RTX 5090 价格" --session demo
Remove-Item -LiteralPath .\bsk-args.json
```

For Bash, use a UTF-8 JSON file when arguments contain non-ASCII text or complex quoting:

```bash
printf '%s' '{"selector":"@e10","value":"显卡日报"}' > /tmp/bsk-args.json
bsk fill "@e10" --value "显卡日报" --session demo
rm -f /tmp/bsk-args.json
```

Both invoke helpers support a no-request payload check:

```powershell
& scripts\invoke.ps1 -Session demo -Action fill -ActionArgs @{
  selector = "@e10"
  value = "显卡日报"
} -DryRun
```

```bash
scripts/invoke.sh --session demo --action fill \
  --args-file /tmp/bsk-args.json --dry-run
```

Use `snapshot.py` to prevent large snapshot responses from flooding context:

```powershell
# Windows: use the Python launcher
py -3 scripts\snapshot.py --session demo --auto
py -3 scripts\snapshot.py --session demo --mode compact
py -3 scripts\snapshot.py --session demo --mode file
```

```bash
# POSIX
# Auto: compact for small pages, file path for large pages
python3 scripts/snapshot.py --session demo --auto

# URL, title, headings, and actionable refs only
python3 scripts/snapshot.py --session demo --mode compact

# Full UTF-8 response saved under the system temp directory
python3 scripts/snapshot.py --session demo --mode file
```

`auto` is the recommended first choice for unfamiliar pages: it returns compact output for small snapshots and writes large or overfull snapshots to a UTF-8 JSON file. `compact` is for locating controls. Use `file` when the task requires article text or other static page content, then read only the relevant portions of that file.
On Windows, prefer `py -3` or `py`; do not assume a `python3` command exists.
The Python helpers configure UTF-8 stdout themselves. If an older shell still renders mojibake, use `--mode file` and read the UTF-8 file instead.

Use the cross-platform screenshot helper:

```powershell
py -3 scripts\screenshot.py --session demo
```

```bash
python3 scripts/screenshot.py --session demo
```

Crop to a specific element using a snapshot ref:

```bash
bsk screenshot --ref @e3 --out /tmp/element.png --session demo
```

Wait for an expected URL, title, or visible accessibility text:

```powershell
py -3 scripts\wait_for.py --session demo `
  --url-contains "zhuanlan.zhihu.com" --timeout 10
py -3 scripts\wait_for.py --session demo `
  --text-contains "已保存" --timeout 10
```

```bash
python3 scripts/wait_for.py --session demo \
  --url-contains "zhuanlan.zhihu.com" --timeout 10
python3 scripts/wait_for.py --session demo \
  --text-contains "Saved" --timeout 10
```

`wait_for.py` accepts these condition flags:

| Flag | Meaning |
|---|---|
| `--url-contains` | Current tab URL contains the value. |
| `--title-contains` | Current tab title contains the value. |
| `--text-contains` | Accessibility tree text contains the value. |
| `--visible-text` | Alias for `--text-contains`; prefer `--text-contains` in docs. |

## Actions

The **Action** column is the name passed to `invoke.sh --action` / `invoke.ps1 -Action` (and to `bsk invoke --action`); it maps to a protocol method. The **BrowserSkill Command** column is the equivalent typed `bsk` subcommand. Both reach the same daemon RPC.

| Action | BrowserSkill Command | Arguments | Purpose |
|---|---|---|---|
| `navigate` | `bsk navigate <url>` | `url`, `wait_until`, `timeout` | Navigate the selected tab. |
| `tab_create` | `bsk tab create` | `url`, `active`, `index` | Create a new tab in the Agent Window. |
| `tab_list` | `bsk tab list` | `scope` | List tabs in scope (`user`/`agent`/`all`). No server-side URL filter; match URLs client-side. |
| `snapshot` | `bsk snapshot` | none | Read URL, title, accessibility tree, and `@e` refs. |
| `click` | `bsk click <ref>` | `ref`/`selector` | Click an `@e` ref or CSS selector. |
| `fill` | `bsk fill <ref>` | `ref`/`selector`, `value` | Replace plain text in inputs, textareas, or contenteditable editors; rich-text markup is not preserved. |
| `evaluate` | `bsk evaluate <code>` | `expression` | Read attributes or perform unsupported page logic. |
| `screenshot` | `bsk screenshot` | `ref`, `format` | Capture the full visible tab, or use `ref` `@eN` to crop to one element. |
| `tab_close` | `bsk tab close <tab-id>` | `tab_id` | Close the selected task-owned tab. |
| `tab_select` | `bsk tab select <tab-id>` | `tab_id` | Focus an agent tab (e.g. after finding a background tab). |
| `session_stop` | `bsk session stop <id>` | `session_id` | Close all tabs associated with the session (`--force` in the helper). |

## Additional BrowserSkill Actions

| Action | Command | Purpose |
|---|---|---|
| `status` | `bsk status` | Connection health, connected browsers, active sessions |
| `browsers` | `bsk browsers` | List all connected browser instances (id, name, version, label, sessions) |
| `session-start-browser` | `bsk session start --browser <id-or-label>` | Target a specific browser when multiple are connected |
| `session-list` | `bsk session list` | List active sessions |
| `session-stop-all` | `bsk session stop --all` | Stop every active session (emergency cleanup) |
| `press` | `bsk press <key>` | Send keyboard events (Enter, Ctrl+A, etc.) |
| `select` | `bsk select <ref> --value <v>` | Select dropdown options |
| `navigate-back` | `bsk navigate-back` | Browser back |
| `navigate-forward` | `bsk navigate-forward` | Browser forward |
| `reload` | `bsk reload` | Refresh current tab; use `--hard` to bypass cache |
| `request-help` | `bsk request-help` | Request human intervention |
| `get-html` | `bsk get-html` | Get page HTML |
| `wait-for-navigation` | `bsk wait-for-navigation` | Wait for navigation to complete |
| `wait-ms` | `bsk wait-ms <duration>` | Wait for specified duration |

## Privacy constraints

- Request only the minimum snapshot, screenshot, PDF, evaluation result, or network data needed for the task.
- Never use `evaluate` to read cookies, password values, authentication tokens, browser storage, or unrelated private page state.
- Treat network headers and bodies as sensitive. Do not collect `Cookie`, `Set-Cookie`, `Authorization`, or token-bearing payloads.
- Keep large or sensitive artifacts on disk rather than returning their contents in command output.
- Remove temporary artifacts after inspection unless the user requested a retained file.

### Advanced action privacy

- Use file upload only for local files the user explicitly confirmed. Do not construct hidden upload requests.
- Treat screenshot outputs as sensitive artifacts. Delete temporary screenshots after use unless the user asked to keep them.

## Interaction rules

- Prefer snapshot refs over CSS selectors.
- Snapshot refs such as `@e10` are BrowserSkill references, not DOM attributes. They work with `click` and `fill`, but selectors such as `[data-ref="@e10"]` usually do not exist.
- Refresh the snapshot after navigation or major DOM changes.
- Treat `click` and `fill` as synthetic DOM events. Sites requiring `event.isTrusted` may reject them.
- Treat `fill` as clear-and-replace. Read and concatenate the existing value before filling when appending.
- Wrap repeated `evaluate` code in an IIFE to avoid top-level `const` or `let` redeclaration:

```javascript
(() => {
  const link = document.querySelector("a");
  return link?.href ?? null;
})()
```

- To recover a link when an `@e` click does not navigate, locate the DOM link by stable visible text or another real attribute and return only its URL:

```javascript
(() => {
  const link = Array.from(document.querySelectorAll("a"))
    .find((item) => item.textContent?.includes("显卡日报"));
  return link?.href ?? null;
})()
```

- Click a submit button directly when possible. Use `press` for special key events.
- Top-frame actions cannot access cross-origin iframe contents. Navigate to the iframe URL directly when appropriate.
- For long pages, scroll in bounded steps and take a fresh snapshot afterward:

```javascript
(() => {
  window.scrollBy({ top: 800, behavior: "instant" });
  return { scrollY: window.scrollY, height: document.documentElement.scrollHeight };
})()
```

## Waiting and retrying

- After `navigate` or a click that should change the page, run `wait_for.py` for the expected URL, title, or visible text; then take a fresh snapshot and inspect URL/title.
- Retry the observation up to three times with a short delay when the page is still loading.
- Do not blindly repeat the click while waiting. Repeated clicks can open duplicate tabs or submit an action twice.
- If the page remains unchanged, follow the tab and popup recovery flow below.
- `wait_for.py` polls snapshots and exits nonzero on timeout; it does not repeat the original click.

## Tab and popup behavior

- A click may open a background tab without changing the visible page.
- **If `tab list` shows no destination tab, the browser may have blocked the popup or new window. Ask the user to allow it for the site before retrying.**
- If no tab appears and the clicked element is a link, use `evaluate` to read its real `href`, then call `navigate` directly.

## Rich-text editors

`fill` is a plain-text clear-and-replace action even when the target is `contenteditable`. It does not provide bold, italic, or range-preserving rich-text semantics. Prefer accessible editor toolbar controls. If they are unavailable, report the formatting step as unsupported rather than claiming success.

## Closing sessions safely

```powershell
bsk session stop <session-id>
```

```bash
bsk session stop <session-id>
```

Before stopping the session, call `bsk tab list` and verify that every listed tab was created for the task.

## Local web app smoke-test recipe

For localhost apps where the task owns a fresh tab:

1. Run `doctor.py --wait-connected 20`; proceed only when ready.
2. Start a session with `bsk session start`.
3. Call `bsk navigate <url>` or `bsk tab create --url <url>`.
4. Take `snapshot.py --mode compact` and use `@e` refs for login, edit, or toolbar controls.
5. After every click that should open a modal or update an SPA, call `wait_for.py --text-contains ...` or take a fresh compact snapshot.
6. Use `evaluate` only for bounded state checks such as `location.href`, modal class names, title text, or console error arrays.
7. Call `bsk tab list`; if the selected tab is task-owned, close it via `bsk session stop`. For user-owned tabs, use `bsk tab return <tab-id>` instead.