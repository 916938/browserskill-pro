<div align="center">

**English | [简体中文](README_ZH.md)**

# BrowserSkill Pro

**Real browser control skill for local AI agents with privacy minimization and tab safety**

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-black.svg)](skill/SKILL.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](#quick-start)
[![Version](https://img.shields.io/badge/Version-v1.0.0-green.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation Guide](#installation-guide)
  - [Windows Installation](#windows-installation-codebuddy--workbuddy--claude-code--codex)
  - [Linux/macOS Installation](#linuxmacos-installation-codebuddy--workbuddy--claude-code--codex)
  - [Docker Deployment](#docker-containerized-deployment)
- [Multi-Environment Support](#multi-environment-support)
- [Usage Examples](#usage-examples)
- [Privacy & Security](#privacy--security)
- [Project Structure](#project-structure)
- [Verification & Testing](#verification--testing)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## Introduction

BrowserSkill Pro is a standalone Agent Skill that controls users' **real, authenticated browsers** through the local **BrowserSkill daemon**.

As long as an Agent can read Agent Skill instructions and execute local shell commands, it can use the core workflow. This repository additionally provides OpenAI/Codex metadata, but core protocol and operation instructions do not depend on any specific Agent product.

### Use Cases

- Reading websites where users are already logged in
- Searching, clicking, and filling forms in existing tabs
- Saving page screenshots or PDFs
- Troubleshooting when pages don't change after clicks, background tabs, or popup blocking

### Architecture Overview

```
Local AI Agent (CodeBuddy / Claude Code / WorkBuddy / Codex)
       │
       ▼
   bsk CLI ──► 127.0.0.1:52800 daemon (WebSocket)
                    │
                    ▼
          Browser Extension + Real Chromium Tabs
```

> **Note:** This project is NOT a search engine and does not contain browser drivers. It depends on **BrowserSkill daemon** and browser extensions, supplementing cross-Agent workflow constraints on top of the original skill.

---

## Features

| Feature | Description |
|---------|-------------|
| **Tab Borrow/Return** | `bsk tab borrow` / `bsk tab return` safely borrows user tabs and returns them after task completion |
| **Human Intervention Request** | `bsk request-help` proactively requests user assistance for CAPTCHA, login, etc. |
| **WebSocket Communication** | Daemon communicates with extension via WebSocket for efficiency and low latency |
| **Rich CLI Commands** | Built-in `press`, `select`, `navigate`, `reload`, `get-html`, etc. |
| **Cross-Platform Support** | Native helpers for Windows (PowerShell), Linux/macOS (Bash) |
| **Smart Snapshot Control** | Auto-strategy, compact UI summary, or full snapshot to file |
| **Doctor Self-Check** | Checks daemon, port, and extension connection; outputs JSON reason |
| **Smart Waiting** | Polls by URL, title, or accessible text without repeating original click |
| **Popup Diagnostics** | Checks SPA, background tabs, and popup blocking when page doesn't change |
| **Privacy Minimization** | Limits reading of cookies, auth headers, browser storage, and private content |
| **Multi-Browser Support** | `bsk browsers` lists all instances; each browser has independent sessions |
| **Layered Documentation** | Agent operations, protocol reference, recovery docs, and architecture docs are separated |

---

## Quick Start

### 1. Install BrowserSkill

> You need to install the local daemon and browser extension before using this skill.

**macOS / Linux (Recommended):**
```bash
curl -fsSL https://raw.githubusercontent.com/Tencent/BrowserSkill/main/install.sh | sh
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/Tencent/BrowserSkill/main/install.ps1 | iex
```

**Or via Cargo:**
```bash
cargo install bsk-cli
```

### 2. Install Browser Extension

Install from [Chrome Web Store](https://chromewebstore.google.com/detail/hhcmgoofomhgciiibhipgmgkgnoenaoi), or build from source:

```bash
cd <browser-skill-repo>
pnpm install && pnpm ext:build  # Output: apps/extension/dist/chrome-mv3
```

Then load unpacked extension in Chrome (`chrome://extensions` → Developer mode → Load unpacked).

> For detailed build steps, see [operations.md - Building the extension from source](skill/references/operations.md#building-the-extension-from-source)

### 3. Install This Skill

Copy the `skill/` directory from this repository to your Agent's skills directory:

```text
<agent-skills-directory>/
└── browserskill-pro/
    ├── SKILL.md          # Core Agent instructions
    ├── scripts/          # Python/Bash/PowerShell helpers
    ├── examples/         # Workflow examples
    └── references/       # Protocol and operation docs
```

### 4. Self-Check Verification

**Windows:**
```powershell
py -3 <your-path>\browserskill-pro\scripts\doctor.py --wait-connected 20
```

**Linux / macOS:**
```bash
python3 <your-path>/browserskill-pro/scripts/doctor.py --wait-connected 20
```

Expected output:
```json
{
  "ready": true,
  "reason": "All checks passed",
  "checks": [
    {"name": "daemon_running", "status": "passed"},
    {"name": "port_52800_listening", "status": "passed"},
    {"name": "extension_connected", "status": "passed"}
  ]
}
```

### 5. Start Using

In your Agent dialog, type:

```text
Use $browserskill-pro to check my currently opened web page.
```

```text
Use $browserskill-pro to search for OpenAI on my Zhihu page.
```

```text
Use $browserskill-pro to take a screenshot of the current page and delete temporary files after completion.
```

---

## Installation Guide

### Windows Installation (CodeBuddy / WorkBuddy / Claude Code / Codex)

#### Method 1: Git Clone + Manual Copy (Recommended)

```powershell
# 1. Clone repository
git clone https://github.com/916938/browserskill-pro.git %TEMP%\bsk-install

# 2. Copy to target path (choose based on your Agent environment)
$target = "$env:USERPROFILE\.codebuddy\skills\browserskill-pro"     # CodeBuddy
# $target = "$env:USERPROFILE\.workbuddy\skills\browserskill-pro"   # WorkBuddy
# $target = "$env:USERPROFILE\.claude\skills\browserskill-pro"      # Claude Code (Skills)
# $target = "$env:USERPROFILE\.claude\commands\browserskill-pro"    # Claude Code (Commands)
# $target = "$env:USERPROFILE\.codex\skills\browserskill-pro"        # Codex

New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item "%TEMP%\bsk-install\skill\*" -Destination $target -Recurse -Force

# 3. Clean up and verify
Remove-Item -Recurse -Force %TEMP%\bsk-install
Test-Path "$target\SKILL.md"
```

#### Method 2: PowerShell One-Click Script (Automated)

```powershell
# Download and run directly
irm https://raw.githubusercontent.com/916938/browserskill-pro/main/install.ps1 | iex

# Or save then run (recommended for code review)
irm https://raw.githubusercontent.com/916938/browserskill-pro/main/install.ps1 -OutFile install.ps1
.\install.ps1 -Branch main

# Force overwrite existing installation
.\install.ps1 -Branch main -Force
```

**Script Features:**
- ✅ Auto-detect Agent environment (CodeBuddy / WorkBuddy / Claude Code / Codex)
- ✅ Force overwrite with backup support
- ✅ Post-installation verification
- ✅ Color-coded output and error messages

#### Method 3: Manual ZIP Download

1. Visit https://github.com/916938/browserskill-pro
2. Click **Code** → **Download ZIP**
3. Extract and copy `skill/` directory contents to target path

---

### Linux/macOS Installation (CodeBuddy / WorkBuddy / Claude Code / Codex)

#### Prerequisites

```bash
# Check required tools
git --version && python3 --version && curl --version

# If dependencies are missing, install by system:
# Ubuntu/Debian: sudo apt update && sudo apt install -y git python3 curl
# macOS: brew install git python3 curl
# Fedora: sudo dnf install -y git python3 curl
# Arch: sudo pacman -S git python3 curl
```

#### Method 1: Git Clone + Manual Copy (Recommended)

```bash
# 1. Clone repository
TMPDIR=$(mktemp -d)
git clone https://github.com/916938/browserskill-pro.git "$TMPDIR/bsk"

# 2. Choose target path (based on your Agent environment)
TARGET="$HOME/.codebuddy/skills/browserskill-pro"           # CodeBuddy
# TARGET="$HOME/.workbuddy/skills/browserskill-pro"         # WorkBuddy
# TARGET="$HOME/.claude/skills/browserskill-pro"            # Claude Code (Skills)
# TARGET="$HOME/.claude/commands/browserskill-pro"          # Claude Code (Commands)
# TARGET="$HOME/.codex/skills/browserskill-pro"             # Codex

# 3. Copy files
mkdir -p "$(dirname "$TARGET")"
cp -r "$TMPDIR/bsk/skill/." "$TARGET"

# 4. Clean up and verify
rm -rf "$TMPDIR"
test -f "$TARGET/SKILL.md" && echo "✅ Installation successful!"
```

#### Method 2: Bash One-Click Script (Automated)

```bash
# Option A: Execute directly
curl -fsSL https://raw.githubusercontent.com/916938/browserskill-pro/main/install.sh | bash

# Option B: Download then execute (recommended)
curl -fsSL https://raw.githubusercontent.com/916938/browserskill-pro/main/install.sh -o install.sh
chmod +x install.sh
./install.sh --branch main

# Advanced options
./install.sh --force                          # Force overwrite
./install.sh --dry-run                        # Dry run (no actual changes)
./install.sh --target-path "/custom/path"     # Custom path
./install.sh -v                               # Verbose output
```

#### Method 3: Manual ZIP Download

```bash
# 1. Download and extract
cd ~/Downloads
unzip browserskill-pro-main.zip -d /tmp/bsk-install

# 2. Copy files
ZIP_EXTRACT="/tmp/bsk-install/browserskill-pro-main"
TARGET="$HOME/.codebuddy/skills/browserskill-pro"
mkdir -p "$(dirname "$TARGET")"
cp -r "$ZIP_EXTRACT/skill/." "$TARGET"

# 3. Verify
test -f "$TARGET/SKILL.md" && echo "✅ Installation successful!"
```

---

### Docker Containerized Deployment

Suitable for CI/CD, isolated environments, and unified deployment scenarios.

#### Prerequisites

```bash
docker --version        # Docker Engine 20.10+
docker compose version  # Docker Compose V2+
```

#### Method 1: Single Container Quick Start (Recommended for Beginners)

```bash
# 1. Build image
git clone https://github.com/916938/browserskill-pro.git
cd browserskill-pro
docker build -t browserskill-pro:latest .

# 2. Run self-check (requires connection to host's bsk daemon)
docker run --rm \
  --network host \
  -v ~/.bsk:/app/.bsk:ro \
  browserskill-pro:latest python3 skill/scripts/doctor.py --wait-connected 20

# 3. Execute snapshot example
docker run --rm --network host \
  browserskill-pro:latest python3 skill/scripts/snapshot.py --session demo --auto
```

**Common Parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--network host` | Use host network to access local daemon | Required |
| `-v` | Mount volumes (data persistence) | `-v ./data:/app/data` |
| `-e` | Set environment variables | `-e LOG_LEVEL=DEBUG` |
| `--rm` | Auto-remove container after exit | Recommended for testing |
| `-d` | Run in background (detached mode) | Recommended for production |

#### Method 2: Docker Compose Orchestration (Production Environment)

Complete deployment including **daemon + Chrome + Redis + monitoring**:

```bash
# Start all services
docker compose up -d

# Start core services only (without monitoring)
docker compose up -d bsk-daemon browserskill-pro redis chrome-browser

# Start development environment (source code hot-mounting)
docker compose -f docker-compose.dev.yml up --build -d

# Start complete environment with monitoring
docker compose --profile monitoring up -d

# Access Grafana dashboard
# http://localhost:3000 (default: admin/admin)
```

**Architecture Diagram:**

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Network (172.28.0.0/16)            │
│                                                             │
│  ┌──────────────┐    ┌─────────────────┐    ┌──────────┐   │
│  │ bsk-daemon   │◄──►│browserskill-pro │◄──►│  chrome  │   │
│  │ (WebSocket)  │    │ (Skill + Helpers)│    │(Browser) │   │
│  │ :52800       │    │                 │    │ :9222    │   │
│  └──────┬───────┘    └────────┬────────┘    └──────────┘   │
│         │                     │                              │
│         ▼                     ▼                              │
│  ┌──────────┐          ┌─────────────┐                      │
│  │   redis  │          │ monitoring  │ (Grafana, Optional)  │
│  │ :6379    │          │ :3000       │                      │
│  └──────────┘          └─────────────┘                      │
│                                                             │
│  Volumes: data, screenshots, snapshots, chrome-profile, grafana│
└─────────────────────────────────────────────────────────────┘
```

**Custom Configuration (`.env` file):**

```bash
BSK_AUTH_TOKEN=your-secure-token-here
BSK_MAX_SESSIONS=20
CHROME_MODE=headed              # or headless
LOG_LEVEL=INFO                  # DEBUG, INFO, WARN, ERROR
DOCKER_CPUS_LIMIT=2.0
DOCKER_MEMORY_LIMIT=4G
```

#### Method 3: CI/CD Integration

**GitHub Actions Example (`.github/workflows/docker-test.yml`):**

```yaml
name: Docker Integration Tests
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      bsk-daemon:
        image: browserskill/bsk-daemon:latest
        ports:
          - 52800:52800
        options: >-
          --health-cmd "curl -f http://localhost:52801/health || exit 1"
          --health-interval 10s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - name: Build & Test
        run: |
          docker build -t browserskill-pro:test .
          docker run --rm --network host browserskill-pro:test \
            python3 -m unittest discover -s tests -v
```

#### Performance Optimization & Security Hardening

**Reduced Image Size:** Multi-stage build implemented in Dockerfile

**Cache Layer Optimization:** Optimized `.dockerignore`

**Production Security Hardening (additional config):**

```yaml
services:
  browserskill-pro:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:size=100M
      - /app/data/screenshots,size=1G
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

**Troubleshooting:**

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Cannot connect to daemon | Incorrect network mode | Use `--network host` |
| Permission denied | Volume mount permission issue | Adjust UID (`user: "1000:1000"`) |
| Chrome won't start | Insufficient shared memory | Increase `shm_size: '2gb'` |
| Container restart loop | Health check failure | View logs `docker compose logs <service>` |

**Image Management:**

```bash
# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t browserskill-pro:latest .

# Push to registry
docker tag browserskill-pro:latest ghcr.io/916938/browserskill-pro:v1.0.0
docker push ghcr.io/916938/browserskill-pro:v1.0.0

# Export/import (offline environments)
docker save -o browserskill-pro.tar browserskill-pro:latest
docker load -i browserskill-pro.tar
```

---

## Multi-Environment Support

This Skill supports **four major AI Agent platforms**: CodeBuddy, WorkBuddy, Claude Code, and Codex.

| Agent Platform | Skills Path | Commands Path | Notes |
|----------------|------------|---------------|-------|
| **CodeBuddy** | `~/.codebuddy/skills/browserskill-pro` | - | Primary supported platform |
| **Claude Code** | `~/.claude/skills/browserskill-pro` | `~/.claude/commands/browserskill-pro` | Dual-mode support (Skills recommended) |
| **WorkBuddy** | `~/.workbuddy/skills/browserskill-pro` | - | Enterprise-grade Agent |
| **Codex** | `~/.codex/skills/browserskill-pro` | - | OpenAI coding assistant |

### Auto-Detection Priority

When using one-click installation scripts, auto-detection order is:
**CodeBuddy > Claude Code > WorkBuddy > Codex**

Override default paths via environment variables or command-line arguments:

```bash
# Linux/macOS
CODEBUDDY_SKILLS_DIR=/custom/path ./install.sh
./install.sh --target-path "$HOME/.my-agent/skills/browserskill-pro"

# Windows
$env:CODEBUDDY_SKILLS_DIR="C:\Custom\Path"
.\install.ps1
```

### Uninstallation

```bash
# Linux/macOS
rm -rf ~/.codebuddy/skills/browserskill-pro

# PowerShell
Remove-Item -Recurse -Force "$env:USERPROFILE\.codebuddy\skills\browserskill-pro"
```

---

## Usage Examples

### Page Snapshots

**Windows:**
```powershell
# Compact mode (suitable for locating elements)
py -3 .\skill\scripts\snapshot.py --session demo --auto
py -3 .\skill\scripts\snapshot.py --session demo --mode compact

# Full mode (write to temp file)
py -3 .\skill\scripts\snapshot.py --session demo --mode file
```

**Linux / macOS:**
```bash
python3 ./skill/scripts/snapshot.py --session demo --auto
python3 ./skill/scripts/snapshot.py --session demo --mode file
```

### Screenshots

**Windows:**
```powershell
py -3 .\skill\scripts\screenshot.py --session demo
```

**Linux / macOS:**
```bash
python3 ./skill/scripts/screenshot.py --session demo
```

### Smart Wait

**Windows:**
```powershell
py -3 .\skill\scripts\wait_for.py --session demo `
  --url-contains "example.com" --timeout 10
py -3 .\skill\scripts\wait_for.py --session demo `
  --visible-text "saved" --timeout 10
```

**Linux / macOS:**
```bash
python3 ./skill/scripts/wait_for.py --session demo \
  --url-contains "example.com" --timeout 10
python3 ./skill/scripts/wait_for.py --session demo \
  --visible-text "completed" --timeout 10
```

### Daemon Smoke Test (No Side Effects)

**PowerShell:**
```powershell
bsk session start
$sessionId = bsk session start
bsk tab list --session $sessionId
bsk session stop $sessionId
```

**Bash:**
```bash
SESSION_ID=$(bsk session start)
bsk tab list --session $SESSION_ID
bsk session stop $SESSION_ID
```

---

## Privacy & Security

### Data Flow & Permission Boundary

```
Local AI agent
    │
    ▼
bsk CLI ──► 127.0.0.1:52800 daemon (WebSocket)
                │
                ▼
      Browser Extension + Real Tabs
```

**Helper Script Behavior Constraints:**

- ✅ Only send commands via `bsk` CLI
- ✅ Do not save cookies, passwords, auth tokens, or browser storage
- ✅ Do not contain telemetry or third-party analytics code
- ⚠️ Once snapshots/screenshots/PDFs are returned to the Agent, they enter the AI session processing scope

### Default Privacy Rules

1. **Minimal Read Principle** — Read only the minimum page content required to complete tasks
2. **Sensitive Data Protection** — Do not return cookies, Authorization headers, tokens, password fields, or browser storage
3. **Temporary File Cleanup** — Delete screenshots and PDFs after task completion (unless explicitly requested by user)
4. **Dangerous Operation Confirmation** — Must confirm before uploading, sending, publishing, purchasing, deleting, or changing permissions
5. **Do Not Bypass Security Mechanisms** — Do not bypass CAPTCHAs, paywalls, age restrictions, or browser warnings
6. **Human Intervention Mechanism** — Use `bsk request-help` for scenarios requiring human confirmation

### Multi-Browser Security Isolation

```bash
# List all connected browser instances
bsk browsers

# Start session on specific browser (independent isolation)
bsk session start --browser <instance-id-or-label>
```

> If multiple browsers are connected but `--browser` is not specified, `bsk session start` will output available instance list.
>
> **Warning:** This Skill can access real authentication states and should be treated as a high-privilege tool.

### External Dependencies Note

BrowserSkill daemon and browser extensions are external dependencies whose data processing behavior is not controlled by this repository.
Please review the privacy policy and implementation of the corresponding products before installation and use.

---

## Project Structure

```text
browserskill-pro/
├── README.md                           # This document (Chinese version)
├── README_EN.md                        # English documentation
├── CHANGELOG.md                        # Version changelog
├── LICENSE                             # Open source license
├── AGENTS.md                           # Agent collaboration guidelines
├── docs/
│   └── v1.1.0-roadmap.md              # Version planning document
├── install.ps1                         # Windows one-click installer
├── install.sh                          # Linux/macOS one-click installer
├── Dockerfile                          # Docker multi-stage build
├── docker-compose.yml                 # Production environment orchestration
├── docker-compose.dev.yml             # Development environment orchestration
├── .dockerignore                       # Docker build ignore rules
│
├── skill/                              # 🔑 Core Skill Package
│   ├── SKILL.md                        # Agent execution instructions (must-read)
│   ├── agents/
│   │   └── openai.yaml                 # OpenAI/Codex metadata
│   ├── examples/                       # Workflow examples
│   │   ├── login_and_fill_form.md
│   │   ├── scroll_and_extract.md
│   │   ├── handle_popup.md
│   │   └── network_debug.md
│   ├── references/                     # Reference documents
│   │   ├── protocol.md                 # Command parameters and response formats
│   │   ├── operations.md               # Installation, status checks, fault recovery
│   │   └── how-it-works.md             # Architecture principles (for human maintainers)
│   └── scripts/
│       ├── invoke.ps1                  # PowerShell invocation wrapper
│       ├── invoke.sh                   # Bash invocation wrapper
│       ├── doctor.py                   # Environment self-check
│       ├── snapshot.py                 # Page snapshot tool
│       ├── screenshot.py               # Screenshot utility
│       ├── wait_for.py                 # Smart wait utility
│       ├── bsk_client.py               # bsk CLI abstraction layer
│       └── screenshot.ps1              # Windows screenshot helper
│
└── tests/                              # Unit tests
    ├── test_doctor.py
    ├── test_snapshot.py
    └── test_wait_for.py
```

**Documentation Layering Guide:**

| Document | Target Audience | Load Timing |
|----------|---------------|-------------|
| `SKILL.md` | AI Agent | Loaded during every execution |
| `protocol.md` | Agent Developers | Loaded when querying parameters |
| `operations.md` | DevOps/Maintainers | Loaded during troubleshooting |
| `how-it-works.md` | Human Maintainers | Not loaded for routine operations |

---

## Verification & Testing

### Unit Tests

```bash
python3 -m unittest discover -s tests -v
```

### PowerShell Syntax Check

```powershell
Get-ChildItem .\skill\scripts -Filter *.ps1 | ForEach-Object {
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $_.FullName, [ref]$null, [ref]$errors
    ) | Out-Null
    if ($errors.Count) { throw $errors }
}
```

### Bash Syntax Check

```bash
bash -n skill/scripts/invoke.sh
```

### Codex Validator (Optional)

If you have Codex's `skill-creator` installed:

```powershell
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\skill
```

### Doctor Self-Check (No Side Effects)

**Windows:**
```powershell
py -3 .\skill\scripts\doctor.py --wait-connected 20
```

**Linux / macOS:**
```bash
python3 ./skill/scripts/doctor.py --wait-connected 20
```

---

## Known Limitations

| Category | Description |
|----------|-------------|
| **Platform Compatibility** | PowerShell helpers primarily target Windows; other platforms can use bsk CLI directly |
| **Python Version** | Python helpers require Python 3.8+; Bash helpers require Bash 4.0+ |
| **Event Trust** | Synthetic clicks and inputs cannot satisfy websites requiring `event.isTrusted` |
| **Cross-Origin iframes** | Top-level page operations cannot directly access cross-origin iframe content |
| **Popup Blocking** | Browsers may block popups or new tabs that websites attempt to open |
| **Protocol Stability** | Response protocols may change after daemon and extension upgrades, requiring re-testing |
| **Windows Python** | On Windows, use `py -3` or `py` to start Python; do not assume `python3` command exists |

---

## Roadmap

### Current Version: v1.0.0

See [CHANGELOG.md](CHANGELOG.md) for details.

### Next Version: v1.1.0 (Planning)

View the complete roadmap with 23 planned features and priorities: [docs/v1.1.0-roadmap.md](docs/v1.1.0-roadmap.md)

**Key Focus Areas:**

| Priority | Feature Area | Examples |
|----------|-------------|----------|
| **P0** | Error Recovery | Retry mechanisms, checkpoint resume, graceful degradation |
| **P1** | Performance Optimization | Concurrent session management, caching strategies, resource pooling |
| **P2** | Enhanced Actions | Drag-and-drop upload, file download, keyboard shortcut recording |
| **P3** | Observability | Structured logging, Prometheus metrics, distributed tracing |

---

## Contributing

We welcome community contributions! Please follow these guidelines when submitting modifications:

### Code Style Guidelines

1. **Python**: Follow existing patterns in `skill/scripts/`. Minimal comments, clear variable names
2. **PowerShell**: Use `[CmdletBinding()]`, named parameters, `-ErrorAction Stop`
3. **Bash**: `set -euo pipefail`. Quote all variables
4. **Markdown**: 2-space indentation, LF line endings

### Documentation Layering Principles

1. **Script comments** — Keep only minimal comments that help understand intent
2. **SKILL.md** — Only include steps Agents must execute and common issues
3. **Protocol details** — Go into `protocol.md`
4. **Lifecycle and recovery flows** — Go into `operations.md`

### Submission Workflow

1. Fork this repository
2. Create feature branch (`git checkout -b feat/amazing-feature`)
3. Commit changes (`but commit main -c -m "feat: add amazing feature"`)
4. Push to branch (`git push origin feat/amazing-feature`)
5. Create Pull Request

### Code of Conduct

- Respect privacy and security principles
- Test cross-platform compatibility of all Helper scripts
- Update relevant documentation (README, CHANGELOG, reference docs)
- Ensure CI/CD tests pass

---

## License

This project is open-sourced under the [MIT License](LICENSE).

## Acknowledgments

- [BrowserSkill](https://github.com/Tencent/BrowserSkill) — Underlying daemon and browser extensions
- [CodeBuddy](https://cnb.cool/codebuddy/codebuddy-code) — Primarily supported AI Agent platform
- [Claude Code](https://claude.ai/) — Multi-mode Agent platform support
- All contributors and users

---

<div align="center">

**Made with ❤️ by the BrowserSkill Pro Team**

[Report Issues](https://github.com/916938/browserskill-pro/issues) · [Feature Requests](https://github.com/916938/browserskill-pro/discussions) · [Changelog](CHANGELOG.md)

</div>
