# Operations

Read this file when BrowserSkill is missing, stopped, disconnected, timing out, or behaving inconsistently.

## Status routing

Prefer the no-action doctor when it is available:

```powershell
py -3 scripts\doctor.py --wait-connected 20
```

```bash
python3 scripts/doctor.py --wait-connected 20
```

`doctor.py` checks the bsk daemon status, extension connection. It always prints JSON and accepts `--json` as an explicit compatibility flag for agents that require one. It does not send browser actions.

Run:

```bash
bsk doctor --json
```

| Observed state | Action |
|---|---|
| bsk command not found | Install bsk CLI via Cargo or download precompiled binaries. |
| Daemon not running | Start the daemon with `bsk daemon start`. |
| Extension not connected | Ask the user to open the browser and verify that the BrowserSkill extension is installed and enabled. |
| Multiple browsers connected | Run `bsk browsers` to list instances, then use `--browser <id>` to target a specific one. |
| All checks passed | Return to `SKILL.md` and send browser commands. |

Interpret the doctor report as follows:

- `ready: true`: the daemon is running and the extension is connected.
- `reason`: a short machine-readable readiness summary such as `ready`, `daemon not running`, or `extension not connected`.
- `ready: false` with daemon not running: start the daemon with `bsk daemon start`.
- `ready: false` with daemon running and extension disconnected: open the browser, install or enable the extension, and rerun `doctor.py`.

Prerequisite links:

- BrowserSkill official repository: `https://github.com/tencent/browserskill`

## Development environment setup

This section covers the complete development environment for working with BrowserSkill Pro — both for using the helpers and for contributing to the skill package.

### Runtime dependencies

These are required to run BrowserSkill Pro in agent workflows:

| Component | Minimum Version | Recommended | Notes |
|-----------|-----------------|-------------|-------|
| **Python** | 3.8+ | 3.10+ or 3.12+ | For `doctor.py`, `snapshot.py`, `screenshot.py`, `wait_for.py` |
| **PowerShell** | 5.1+ (Windows) | 7+ (PowerShell Core cross-platform) | For `invoke.ps1` and Windows workflows |
| **Bash** | Any (Git Bash, WSL, macOS) | Latest | For `invoke.sh` and POSIX workflows |
| **bsk CLI** | 0.1.0+ | **0.1.7** (current) | Must match extension protocol version |
| **Browser extension** | MV3-compatible | **0.1.3** (current) | Chrome Web Store or built from source |
| **Git** | 2.20+ | Latest | For version control and skill installation |

### Python environment

**Windows** (use the Python launcher):

```powershell
# Check Python installation
py -3 --version          # should show Python 3.8+

# Verify required modules are available (no external dependencies needed)
py -3 -c "import json, sys, subprocess, tempfile, os; print('OK')"
```

**macOS / Linux**:

```bash
# Check Python installation
python3 --version        # should show Python 3.8+

# Verify modules
python3 -c "import json, sys, subprocess, tempfile, os; print('OK')"
```

> **Note**: The Python helpers have zero external dependencies — they use only standard library modules (`json`, `sys`, `subprocess`, `temporalfile`, `os`, `re`, `argparse`). No `pip install` is required.

### PowerShell environment

```powershell
# Check PowerShell version
$PSVersionTable.PSVersion   # should be 5.1+ (Windows) or 7+ (cross-platform)

# Verify language parser availability (for lint checks)
[System.Management.Automation.Language.Parser] | Out-Null
```

### bsk CLI verification

```bash
# Check bsk CLI version
bsk --version              # should be 0.1.7 or compatible

# Quick connectivity test (no browser actions)
bsk status                 # should show daemon and extension status
bsk doctor                 # detailed diagnostics
```

### Browser and extension check

```bash
# List connected browsers
bsk browsers               # should show at least one Chromium instance

# Verify extension connection
bsk status                 # extension status should be "connected"
```

### Development tools (for contributors only)

If you plan to modify BrowserSkill Pro helper scripts or documentation:

| Tool | Version | Purpose |
|------|---------|---------|
| **Text editor / IDE** | Any | VS Code recommended (with Python + PowerShell extensions) |
| **Unit test runner** | Built-in (`unittest`) | Python's standard library — no extra install needed |
| **ShellCheck** (optional) | Latest | Bash script linting: `shellcheck skill/scripts/invoke.sh` |

### Platform-specific notes

**Windows**:
- Use `py -3` or `py` to invoke Python (never assume `python3` exists)
- PowerShell scripts use `.ps1` extension; run with `powershell -File` or `&`
- Git Bash provides POSIX-like environment; paths use forward slashes `/`
- Temporary files default to `%TEMP%` or system temp directory

**macOS**:
- Pre-installed Python 3 via Xcode command-line tools (`xcode-select --install`)
- Use `python3` explicitly (macOS ships Python 2.7 as `python`)
- Homebrew packages available but not required: `brew install python@3.12`

**Linux**:
- Most distributions include Python 3.8+ by default
- Ensure `python3` command is available (may need `python3-is` package on Debian/Ubuntu)
- Bash is always available at `/bin/bash`

## Building the extension from source

If you need to modify the extension, use a custom build, or after updating the BrowserSkill repository:

### Prerequisites

| Dependency | Minimum Version | Notes |
|------------|-----------------|-------|
| **Node.js** | 18+ (LTS recommended) | Required for pnpm and extension build toolchain |
| **pnpm** | 10.17.0 | Pinned in `packageManager` field; do not upgrade without updating lockfile |
| **Rust toolchain** | stable (1.85+) | Edition 2024; requires `rustfmt` and `clippy` components |
| **Cargo** | Latest stable | Workspace with `resolver = "2"` and lockfile integrity checks |
| **Chrome/Edge** | MV3-compatible | Enable Developer mode for unpacked extension loading |
| **bsk CLI** | Installed | See [Installation](#installation) below; must match extension protocol version |

**Verify prerequisites:**

```bash
# Check Node.js
node --version          # should be v18+ or v20+

# Check pnpm version
pnpm --version          # should be 10.17.0

# Check Rust
rustc --version         # should be 1.85+
cargo --version         # latest stable

# Check bsk CLI
bsk --version           # should match extension build
```

> **Note on pnpm**: The repository pins `pnpm@10.17.0` in the root `package.json`. Upgrading pnpm requires regenerating the lockfile (`pnpm install --frozen-lockfile`). See the main repo's AGENTS.md for CI-enforced version constraints.
>
> **Note on Rust**: The workspace uses Cargo edition 2024 and `rust-version = "1.85"`. Some edition 2024 patterns differ from 2021 (e.g., `gen` keyword reserved, `unsafe_op_in_unsafe_fn` warn-by-default).

### Build steps

```bash
# In the BrowserSkill repository
cd <browser-skill-repo>

# Install dependencies and build the extension
pnpm install
pnpm ext:build                    # output: apps/extension/dist/chrome-mv3
```

### Load in Chrome

1. Open `chrome://extensions`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked** and select the `apps/extension/dist/chrome-mv3` directory
4. Verify the BrowserSkill popup turns green once connected to the daemon

### Development with hot reload

For active development with automatic reloading on file changes:

```bash
pnpm ext:dev                      # starts WXT dev server with HMR
```

This runs a local dev server that automatically rebuilds and reloads the extension when you modify source files.

### Version matching

> **Important**: The `bsk` CLI and the browser extension must match in protocol version.
>
> **Current versions (as of 2026-07-16)**:
> - CLI: `0.1.7` (from `Cargo.toml` workspace.package.version)
> - Extension: `0.1.3` (from `apps/extension/package.json`)
>
> **Protocol compatibility**:
> - If you update one side (CLI or extension), you must rebuild/reinstall the other as well
> - Version skew causes exit code 5 errors or silent failures
> - The release workflows verify both versions match the git tag
> - Protocol schemas live in `crates/bsk-protocol/schema/` and are committed
>
> When building from source:
> ```bash
> # After modifying extension source:
> pnpm ext:build                  # rebuilds extension
> cargo build -p bsk              # rebuilds CLI (if protocol changed)
> ```

### Troubleshooting builds

| Issue | Solution |
|-------|----------|
| **Node.js too old** | Upgrade to Node.js 18+ LTS; `nvm install --lts` or download from nodejs.org |
| **pnpm version mismatch** | Install exact pinned version: `npm i -g pnpm@10.17.0`; verify with `pnpm --version` |
| **Rust not installed** | Install via `rustup`; run `rustup component add rustfmt clippy`; verify `rustc --version >= 1.85` |
| **Cargo lockfile stale** | Run `pnpm install --frozen-lockfile` for JS deps; `cargo update` for Rust deps (requires `--locked` in CI) |
| **Build fails (JS)** | Check Biome version (`^2.3.14`); run `pnpm lint` before `pnpm ext:build` |
| **Build fails (Rust)** | Run `cargo fmt --check && cargo clippy --workspace`; check edition 2024 syntax |
| **Extension not loading** | Check `chrome://extensions` errors; verify `dist/chrome-mv3` exists; ensure MV3 manifest valid |
| **Popup stays red** | Restart daemon: `bsk daemon restart`; check port 52800 availability; verify CLI/extension versions match |
| **Protocol mismatch (exit code 5)** | Rebuild both sides: `pnpm ext:build && cargo build -p bsk`; verify `bsk --version` matches extension build |
| **WXT dev server fails** | Run `wxt prepare` first to generate `.wxt/` type stubs (required before `tsc` or `vitest`) |
| **Schema regeneration needed** | Run `pnpm cli:build` to regenerate protocol schemas from Rust source |

### Build command reference

```bash
# Full CI-equivalent build (from BrowserSkill repo root)
cargo fmt --all -- --check                    # Rust formatting
cargo clippy --workspace --all-targets --locked -- -D warnings  # Lint
cargo test --workspace --locked               # Rust tests
pnpm install --frozen-lockfile                # JS dependencies
pnpm --filter @browser-skill/extension exec wxt prepare  # Generate WXT types
pnpm lint                                     # Biome + Stylelint
pnpm --filter @browser-skill/extension compile # TypeScript check
pnpm ext:test                                 # Extension tests (vitest)
pnpm ext:build                                # Production build

# Quick iteration (development)
cargo build -p bsk                           # CLI only
pnpm ext:dev                                 # Extension dev server with HMR
```

## Installation

### 1. Install the `bsk` CLI

**macOS / Linux** (recommended — installs to `~/.local/bin`):

```bash
curl -fsSL https://raw.githubusercontent.com/Tencent/BrowserSkill/main/install.sh | sh
```

**Windows** (PowerShell — installs to `~/.local/bin`):

```powershell
irm https://raw.githubusercontent.com/Tencent/BrowserSkill/main/install.ps1 | iex
```

Verify the binary:

```bash
bsk --version
```

Or via Cargo (from source):

```bash
cargo install bsk-cli
```

### 2. Install the browser extension

Install BrowserSkill from [Chrome Web Store](https://chromewebstore.google.com/detail/hhcmgoofomhgciiibhipgmgkgnoenaoi).

For custom builds or protocol changes, see [Building the extension from source](#building-the-extension-from-source) above.

### 3. Install the BrowserSkill Pro skill package

The base `bsk` CLI ships with a built-in skill (`bsk install-skill`). For enhanced helper scripts and layered documentation, install this Pro package:

**Option A: Automatic installation (if your harness supports `bsk install-skill`)**

```bash
# List supported harnesses on your machine
bsk install-skill --list

# Install into a specific harness (interactive)
bsk install-skill

# Non-interactive mode (for scripts)
bsk install-skill -H <harness-id> -y

# Install into all detected harnesses
bsk install-skill --all -y
```

Use <kbd>Space</kbd> to select the target harness, then <kbd>Enter</kbd> to install.

**Option B: Manual installation**

Copy this repository's `skill/` directory into your agent's skills directory as `browserskill-pro/`. See the main README for agent-specific paths.

### Post-install verification

Run the readiness smoke test:

PowerShell:

```powershell
py -3 scripts\doctor.py --wait-connected 20
bsk session start
$sessionId = bsk session start
bsk tab list --session $sessionId
bsk session stop $sessionId
```

POSIX:

```bash
python3 scripts/doctor.py --wait-connected 20
SESSION_ID=$(bsk session start)
bsk tab list --session $SESSION_ID
bsk session stop $SESSION_ID
```

If the extension remains disconnected, open the browser, verify BrowserSkill is installed and enabled in `chrome://extensions`, then rerun.

## Lifecycle commands

| Operation | Command |
|---|---|
| Status | `bsk status` |
| Doctor (detailed) | `bsk doctor --json` |
| List sessions | `bsk session list` |
| List browsers | `bsk browsers` |
| Start daemon | `bsk daemon start` |
| Stop daemon | `bsk daemon stop` |
| Restart daemon | `bsk daemon restart` |
| Stop all sessions | `bsk session stop --all` |
| Readiness check | `py -3 scripts\doctor.py --wait-connected 20` |

**Session idle timeout is 5 minutes.** Always call `bsk session stop <id>` explicitly — do not rely on idle timeout for cleanup. Use `bsk session stop --all` for emergency cleanup.

## Diagnose failures

| Symptom | Action |
|---|---|
| Address already in use | Stop, then start the daemon. If it persists, identify the process listening on port `52800`. |
| Commands time out | Check daemon status with `bsk doctor`, then retry once after a restart. |
| Extension remains disconnected | Open the browser, install or enable the BrowserSkill extension, and retry status. |
| Extension is connected but actions fail | Check for version mismatches between daemon and extension. |
| Version skew (exit code 5) | Upgrade or reinstall both CLI and extension to matching versions. |
| Session not found | Start a new session with `bsk session start`. |
| Wrong browser targeted | Run `bsk browsers` to list instances, then start a session with `--browser <id>`. |

## Multiple browsers

When more than one Chromium browser with the BrowserSkill extension is running:

```bash
# List all connected instances
bsk browsers

# Start a session on a specific browser
bsk session start --browser <instance-id-or-label>
```

If multiple browsers are connected and no `--browser` is specified, `bsk session start` returns an error with a table of available instances. Each browser gets its own Agent Window and session lifecycle.