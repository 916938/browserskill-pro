# Changelog

## [Unreleased]

### Synced from BrowserSkill upstream (2026-07-17)

- **SKILL.md**: Added comprehensive **"Dual-mode execution"** documentation section (8 subsections):
  - **Mode comparison table**: Side-by-side comparison of passthrough vs legacy across 11 dimensions (version requirements, JSON handling, Unicode support, host-side dependencies, action resolution, error messages, performance)
  - **Auto-detection workflow**: ASCII flowchart showing runtime detection logic (`bsk invoke --help` check → mode selection → command construction)
  - **When each mode is used**:
    - Passthrough: complex nested args, Unicode text, large payloads (>1KB), production environments
    - Legacy: simple flat args, older bsk versions, basic workflows
  - **Legacy mode limitations**: Documented 4 known limitations with workarounds (nested objects, arrays, Chinese text, unmapped actions)
  - **Code examples for both modes**:
    - Passthrough: Complex nested JSON with options object, PowerShell hashtable with nested structure
    - Legacy: Simple URL navigation, flat fill command, snapshot call
  - **Advanced forcing methods**: Direct `bsk invoke` calls and `BSK_SKIP_INVOKE` env var (with deprecation note)
  - **Mode verification commands**: Bash/PowerShell one-liners to check active mode and test helper output
  - **Upgrade guide**: 4-step migration path from legacy to passthrough (check version → upgrade bsk CLI → verify → no config changes needed)
  - **Agent developer notes**: Migration guidance, testing recommendations, future-proofing tips, new feature targeting strategy
- **SKILL.md**: Added version compatibility section:
  - Documented bsk CLI 0.1.0+ requirement and recommended versions (CLI 0.1.7, Extension 0.1.3)
  - Explained `bsk invoke` passthrough command (available in bsk 0.2.0+) benefits
  - Updated Quick action map with auto-detection behavior explanation
  - Enhanced Use helpers section with runtime detection details
- **invoke.sh / invoke.ps1**: Implemented **backward-compatible `bsk invoke` auto-detection**:
  - **Passthrough mode** (preferred, bsk 0.2.0+): Forwards raw JSON via `bsk invoke --action <name> --args-json <json>`; no host-side JSON parsing required
  - **Legacy mode** (fallback, bsk < 0.2.0): Maps action names to specific typed bsk commands (`fill` → `bsk fill`, `tab_list` → `bsk tab list`, etc.)
  - Auto-detection via `bsk invoke --help` at script invocation time (zero-config)
  - Legacy mode supports 20+ actions: navigate, tab_create, tab_list, snapshot, click, fill, evaluate, screenshot, tab_close, session_stop, press, select, navigate-back, navigate-forward, reload, request-help, get-html, wait-for-navigation, wait-ms, tab_select
  - Complex/nested JSON works reliably in passthrough mode; legacy mode has limitations but covers common use cases
  - Both scripts maintain identical feature parity: --force guards, session validation, timeout handling, dry-run support
- **operations.md**: Added comprehensive **"Development environment setup"** section with:
  - **Runtime dependencies table**: Python 3.8+ (recommended 3.10+/3.12+), PowerShell 5.1+/7+, Bash, bsk CLI 0.1.7, Extension 0.1.3, Git 2.20+
  - **Python environment verification**: Windows (`py -3`) vs POSIX (`python3`) commands; confirms zero external dependencies (standard library only)
  - **PowerShell environment check**: Version detection, language parser availability
  - **bsk CLI verification**: `bsk --version`, `bsk status`, `bsk doctor` connectivity tests
  - **Browser/extension validation**: `bsk browsers`, extension connection status
  - **Development tools for contributors** (optional): IDE recommendations, ShellCheck for Bash linting
  - **Platform-specific notes**:
    - Windows: `py -3` launcher, PowerShell paths, Git Bash behavior, temp directory location
    - macOS: Xcode command-line tools, Homebrew option, python3 vs python distinction
    - Linux: Debian/Ubuntu package requirements, bash availability
  - Positioned between Status routing and Building sections for logical flow
- **operations.md**: Enhanced "Building the extension from source" section with:
  - Structured subsections: Prerequisites, Build steps, Load in Chrome, Development with hot reload, Version matching, Troubleshooting builds
  - **Updated dependency version information**:
    - Added version requirements table: Node.js 18+, pnpm 10.17.0 (pinned), Rust 1.85+ (edition 2024)
    - Added prerequisite verification commands (`node --version`, `pnpm --version`, `rustc --version`, `bsk --version`)
    - Documented pnpm pinning policy and lockfile integrity requirements
    - Noted Rust edition 2024 specifics and component requirements (rustfmt, clippy)
  - **Enhanced version matching section**:
    - Added current versions: CLI 0.1.7, Extension 0.1.3 (as of 2026-07-16)
    - Documented protocol schema location and commit policy
    - Explained version skew consequences and CI verification
  - **Expanded troubleshooting table** (6 → 11 entries):
    - Added Node.js/Rust/pnpm version-specific issues
    - Added Cargo lockfile, Biome, WXT, schema regeneration failures
    - Included exit code 5 protocol mismatch diagnosis
    - Linked to specific fix commands for each issue
  - **Added build command reference section**:
    - Full CI-equivalent build sequence (format → lint → test → compile → build)
    - Quick iteration commands for development
    - Documented `wxt prepare` requirement before TypeScript checks
  - Removed duplicate "Building the extension from source" section that existed later in the file
- **operations.md**: Restructured "Installation" section with:
  - Three-step installation flow: CLI → Extension → Pro skill package
  - Added `bsk --version` verification step
  - Added Chrome Web Store extension installation link
  - Documented `bsk install-skill` command for automatic harness installation (with `--list`, `-H`, `--all`, `-y` options)
  - Added Option A (automatic) vs Option B (manual) installation paths
  - Integrated Post-install verification into Installation section (removed duplicate standalone section)
  - Clarified installation paths (~/.local/bin) and platform-specific notes
- **README.md**: Added link from extension build instructions to the detailed operations.md section
- Verified all 21 unit tests pass after sync.
- Confirmed SKILL.md already contains equivalent or more detailed versions of upstream additions (quick decision tree, feature comparison table, multi-browser support).

### Fixed

- `invoke.sh` no longer silently drops all action arguments when `jq` is absent. The helpers no longer parse or flatten JSON at all — see the passthrough rework below — so the `jq` dependency (and the silent-drop failure mode) is gone entirely.
- Action names in examples and reference tables now use bsk protocol vocabulary (`tab_list`, `tab_close`, `session_stop`) instead of friendly names (`find_tab`, `list_tabs`, `close_session`) that resolved to non-existent `bsk` commands (e.g. `find_tab` → `bsk find tab`) and never actually ran.
- The `find_tab`-with-URL recipe was corrected: no server-side URL filter exists (`tool.tab_list` accepts only `scope` + `session_id`), so the docs now show `tab_list --scope user` followed by client-side URL/title matching instead of implying a server-side filter.

### Added

- `bsk invoke` passthrough subcommand (in the bsk CLI at `H:\skills\BrowserSkill`): forwards a raw JSON params object to any `tool.*`/`session.*` RPC, resolving bare (`fill`) or qualified (`tool.fill`) action names to protocol methods. This lets the shell helpers stop flattening JSON into typed flags.
- `invoke.sh` / `invoke.ps1` are now thin passthroughs to `bsk invoke` — they validate a few flags, translate `--timeout` seconds to `--timeout-ms`, and forward the JSON blob (`--args-json`, `--args-file`, or stdin) verbatim. No host-side `jq`/`python3` JSON handling remains.
- `--force` / `-Force` guards on both helpers cover every spelling that resolves to a session-stopping method (`session_stop`, `session_stop_all`, `session.stop`, `session.stop_all`, plus the legacy `close_session`), so the gate cannot be bypassed via an alternate form.
- `invoke.sh --args-stdin` and `--args-file -` to read UTF-8 JSON from stdin, avoiding temporary files for non-ASCII or complex arguments.
- Interactive terminal guard: `invoke.sh --args-stdin` refuses to wait on an interactive terminal.
- Rich-text editor guidance in SKILL.md and protocol.md: `fill` on `contenteditable` is plain-text replacement, does not preserve formatting.
- Shell boundary clarity: explicitly match `invoke.ps1` to PowerShell and `invoke.sh` to Bash.
- BrowserSkill-specific commands: `bsk press`, `bsk select`, `bsk navigate-back`, `bsk navigate-forward`, `bsk reload`, `bsk request-help`, `bsk get-html`, `bsk wait-for-navigation`, `bsk wait-ms`.
- Session management via `bsk session start` / `bsk session stop`.
- Tab borrowing/returning via `bsk tab borrow` / `bsk tab return`.
- Multi-browser support: `bsk browsers` lists connected instances, `--browser <id-or-label>` targets a specific browser.
- `bsk tab select` for focusing agent tabs (documented in recovery flow and action tables).
- `bsk status` for connection health diagnostics.
- `bsk session list` for listing active sessions.
- `bsk session stop --all` for emergency cleanup.
- `bsk reload --hard` flag to bypass browser cache.
- Session idle timeout warning (5 minutes) in SKILL.md and operations.md.
- Exit code table (0–5) in protocol.md with meaning and recommended action.
- Global flags table (`--json`, `--quiet`, `-v`/`-vv`) in protocol.md.
- `request-help` parameter details (`--prompt`, `--target`, `--title`, `--timeout`) and outcome types in SKILL.md.
- "When NOT to use" section in SKILL.md with usage boundary constraints.
- Extension build-from-source instructions for `apps/extension/dist/chrome-mv3` unpacked load.
- `system.ping` keepalive heartbeat documented in protocol and how-it-works.
- `screenshot --ref @eN` element crop example in protocol.md.
- Multi-browser architecture explanation in how-it-works.md.

### Changed

- Migrated from Kimi WebBridge to Tencent BrowserSkill.
- Replaced `webbridge_client.py` with `bsk_client.py` — a subprocess-based CLI wrapper for the `bsk` command.
- Updated `doctor.py` to use `bsk doctor --json` instead of HTTP-based daemon status checks.
- Updated `snapshot.py`, `screenshot.py`, and `wait_for.py` to use `bsk` CLI instead of HTTP POST.
- Updated `invoke.ps1` and `invoke.sh` to use `bsk` CLI instead of HTTP POST to daemon.
- Updated `SKILL.md`, `protocol.md`, `operations.md`, and `how-it-works.md` for BrowserSkill.
- Updated `openai.yaml` with new skill name and prompt.
- Updated README.md with BrowserSkill installation and usage instructions.
- Updated unit tests to work with new `bsk_client.py` module.
- README installation section now recommends `install.sh` / `install.ps1` installer scripts as primary method, with `cargo install` as alternative.
- Version skew (exit code 5) failure entry added to operations.md diagnose table.

### Fixed

- Removed `webbridge_client.py` and `test_mock_daemon.py` (HTTP-based mock daemon tests no longer applicable).
- Fixed duplicate `## 隐私与安全` header in README.md.
- Fixed step numbering in README: extension install is step 2, skill install is step 3.

### Validation

- All unit tests pass: `python -m unittest discover -s tests -v`

## v1.0.0 — 2026-06-20

First formal release of BrowserSkill Pro as an agent-neutral browser-control skill.

### Added

- PowerShell `invoke.ps1 -ArgsFile` support for UTF-8 JSON argument files, including Chinese text and nested action arguments.
- `snapshot.py --auto` and `--mode auto`, which return compact snapshots for small pages and write large or overfull snapshots to a UTF-8 JSON file.
- Top-level `reason` in `doctor.py` readiness output, plus a `--json` compatibility flag for agents that explicitly request JSON output.
- A quick decision tree in `SKILL.md` for choosing tab ownership, snapshot strategy, argument passing, and post-click recovery flow.
- End-to-end examples under `skill/examples/` for form filling, long-page extraction, popup/background-tab recovery, and network debugging.

### Changed

- Updated protocol and operations guidance to prefer `wait_for.py` plus a fresh snapshot after navigation or state-changing clicks.
- Clarified when to use `snapshot.py --auto`, `--mode compact`, and `--mode file`.
- Documented UTF-8 args-file workflows for both PowerShell and Bash.
- Updated README feature and project-structure sections to reflect the helper and examples layout.

### Validation

- Unit tests: `py -3 -m unittest discover -s tests -v`
- Python script compilation for `skill/scripts/*.py`
- PowerShell parser checks for `skill/scripts/*.ps1`
- Git Bash syntax check for `skill/scripts/invoke.sh`
- `git diff --check`
- `skill-creator` quick validation for `skill/`
- Manual PowerShell dry-run for `invoke.ps1 -ArgsFile` with Chinese and nested JSON

### Deferred

- Daemon-side automatic tab switching after clicks remains outside this skill repository.
- Stitched full-page screenshots are deferred until there is a stable screenshot/scroll contract and an explicit image dependency decision.
