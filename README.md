<div align="center">

# BrowserSkill Pro

**面向本地 AI Agent 的真实浏览器控制 skill，强调隐私最小化和标签页安全**

[![Agent Skill](https://img.shields.io/badge/Agent-Skill-black.svg)](skill/SKILL.md)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](#快速开始)
[![Privacy](https://img.shields.io/badge/Privacy-Minimized-green.svg)](#隐私与安全)

</div>

---

## 简介

BrowserSkill Pro 是一个独立的 Agent skill，通过本机 BrowserSkill daemon
控制用户真实、已登录的浏览器。

只要 Agent 能读取 Agent Skill 指令，并能执行本地 shell 命令，就可以使用
核心工作流。仓库额外提供 OpenAI/Codex 元数据，但核心协议和操作说明不依赖某个
特定 Agent 产品。

它适合需要使用现有标签页、Cookie 会话或浏览器扩展状态的任务，例如：

- 阅读用户已经登录的网站
- 在现有标签页中搜索、点击和填写内容
- 保存页面截图或 PDF
- 排查点击后页面没有变化、后台标签页或弹窗拦截

本项目不是搜索引擎，也不包含浏览器驱动。它依赖 BrowserSkill daemon 和浏览器
扩展，并在原有 skill 的基础上补充跨 Agent 工作流约束。

## 主要增强

| 能力 | 说明 |
|---|---|
| **标签页借用/归还** | `bsk tab borrow` / `bsk tab return` 安全借用用户已有标签页，任务完成后归还，不影响用户浏览状态 |
| **人工介入请求** | `bsk request-help` 主动请求用户介入处理 CAPTCHA、登录等需要人工操作的场景 |
| **WebSocket 通信** | daemon 通过 WebSocket 与扩展通信，相比 HTTP 轮询更高效、低延迟 |
| **丰富的 CLI 命令** | 内置 `press`、`select`、`navigate-back/forward`、`reload`、`get-html`、`wait-for-navigation` 等命令 |
| **Windows 原生 helper** | 使用 PowerShell 对象构造参数，通过 bsk CLI 调用，避免命令行转义问题 |
| **Bash 调用 helper** | 通过 `bsk` CLI 直接调用，无需 curl、jq 或 JSON 参数文件 |
| **Snapshot 控制** | 支持自动策略、精简 UI 摘要，或把完整快照写入临时文件 |
| **Doctor 自检** | 检查 daemon、端口和扩展连接，可短轮询等待连接，并输出 JSON reason |
| **跨平台截图** | Python helper 兼容 bsk 返回的路径响应 |
| **智能等待** | 按 URL、标题或可访问性文本轮询，不重复原始点击 |
| **标签页所有权** | 区分用户原有标签页和任务新建标签页，避免误关页面 |
| **弹窗诊断** | 页面无变化时依次检查 SPA、后台标签页和浏览器弹窗拦截 |
| **隐私最小化** | 限制 Cookie、认证头、浏览器存储和无关私人内容的读取 |
| **多浏览器支持** | `bsk browsers` 列出所有实例，`--browser` 指定目标浏览器，每个浏览器独立会话 |
| **分层文档** | Agent 操作说明、协议参考、故障恢复和人类原理文档彼此分离 |

## 快速开始

### 1. 安装 BrowserSkill

使用本 skill 前需要同时安装本地 daemon 和浏览器扩展：

- [BrowserSkill 官方仓库](https://github.com/tencent/browserskill)

**macOS / Linux**（推荐）：

```bash
curl -fsSL https://raw.githubusercontent.com/Tencent/BrowserSkill/main/install.sh | sh
```

**Windows**（PowerShell）：

```powershell
irm https://raw.githubusercontent.com/Tencent/BrowserSkill/main/install.ps1 | iex
```

或者通过 Cargo 安装：

```bash
cargo install bsk-cli
```

安装完成后，确保 `bsk` 命令在 PATH 中可用。

### 2. 安装浏览器扩展

从 [Chrome Web Store](https://chromewebstore.google.com/detail/hhcmgoofomhgciiibhipgmgkgnoenaoi) 安装 BrowserSkill 扩展。

如果需要从源码构建扩展（例如使用了最新的协议变更）：

```bash
cd <browser-skill-repo>
pnpm install
pnpm ext:build                    # 输出: apps/extension/dist/chrome-mv3
```

然后在 Chrome 中：

1. 打开 `chrome://extensions`
2. 开启 **开发者模式**
3. 点击 **加载已解压的扩展程序**，选择 `apps/extension/dist/chrome-mv3` 目录

> 详细构建步骤、开发时热重载（`pnpm ext:dev`）以及 CLI 与扩展版本匹配要求，请参阅 [operations.md - Building the extension from source](skill/references/operations.md#building-the-extension-from-source)。

### 3. 安装 skill

将仓库中的 `skill/` 目录复制到你的 Agent 所使用的 skills 目录，并保持目录名为
`browserskill-pro`。不同 Agent 的 skills 路径和重载方式不同，请以对应 Agent
文档为准。

通用结构：

```text
<agent-skills-directory>/
└── browserskill-pro/
    ├── SKILL.md
    ├── agents/
    ├── references/
    └── scripts/
```

#### Codex / Claude Code 安装示例

**Codex:**

Windows：

```powershell
git clone <repo-url> browserskill-pro
$target = "$env:USERPROFILE\.codex\skills\browserskill-pro"
New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item ".\browserskill-pro\skill\*" -Destination $target -Recurse -Force
```

Linux / macOS：

```bash
git clone <repo-url> browserskill-pro
mkdir -p ~/.codex/skills/browserskill-pro
cp -R browserskill-pro/skill/. ~/.codex/skills/browserskill-pro/
```

**Claude Code (推荐 Skills 方式):**

```bash
# 克隆仓库
git clone https://github.com/916938/browserskill-pro.git

# 安装到 Claude Code skills 目录（方式 1：作为 skill）
mkdir -p ~/.claude/skills/
cp -R browserskill-pro/skill/. ~/.claude/skills/browserskill-pro/

# 或者（方式 2：作为 slash command）
mkdir -p ~/.claude/commands/
cp -R browserskill-pro/skill/. ~/.claude/commands/browserskill-pro/

# 验证安装
ls ~/.claude/skills/browserskill-pro/SKILL.md || ls ~/.claude/commands/browserskill-pro/SKILL.md
```

**Claude Code 使用说明:**

- **Skills 方式**: 在对话中直接使用，Claude 会自动识别 SKILL.md 中的指令
- **Commands 方式**: 可通过 `/browserskill-pro` 命令调用（需要配置）
- 推荐使用 **Skills 方式**，与 CodeBuddy/WorkBuddy 体验一致

重新启动 Agent 或打开新会话，使 skill 列表重新加载。

#### CodeBuddy / WorkBuddy / Claude Code 环境安装（Windows）

如果你使用 **CodeBuddy**、**WorkBuddy** 或 **Claude Code** 作为 AI Agent 环境，可以通过以下步骤从 GitHub 仓库快速安装：

**方法一：Git 克隆 + 手动复制（推荐）**

```powershell
# 1. 克隆仓库到临时目录
git clone https://github.com/916938/browserskill-pro.git %TEMP%\browserskill-pro-install

# 2. 创建目标 skills 目录（如果不存在）
$codebuddySkillsPath = "$env:USERPROFILE\.codebuddy\skills\browserskill-pro"
New-Item -ItemType Directory -Path $codebuddySkillsPath -Force | Out-Null

# 3. 复制 skill 目录内容到 CodeBuddy skills 路径
Copy-Item "%TEMP%\browserskill-pro-install\skill\*" -Destination $codebuddySkillsPath -Recurse -Force

# 4. 清理临时目录
Remove-Item -Recurse -Force %TEMP%\browserskill-pro-install

# 5. 验证安装成功
Write-Host "✅ BrowserSkill Pro 已安装到: $codebuddySkillsPath"
Get-ChildItem $codebuddySkillsPath | Select-Object Name
```

**方法二：PowerShell 一键脚本（自动化）**

```powershell
# 将以下代码保存为 install-browserskill-pro.ps1 并运行
# 或直接在 PowerShell ISE 中执行

param(
    [string]$RepoUrl = "https://github.com/916938/browserskill-pro.git",
    [string]$Branch = "main",
    [switch]$Force
)

Write-Host "🚀 开始安装 BrowserSkill Pro..." -ForegroundColor Cyan

# 检测 Agent 类型并确定安装路径
$possiblePaths = @(
    "$env:USERPROFILE\.codebuddy\skills\browserskill-pro",
    "$env:USERPROFILE\.workbuddy\skills\browserskill-pro",
    "$env:USERPROFILE\.codex\skills\browserskill-pro",
    "$env:APPDATA\CodeBuddy\skills\browserskill-pro"
)

$targetPath = $null
foreach ($path in $possiblePaths) {
    if (Test-Path (Split-Path $path)) {
        $targetPath = $path
        break
    }
}

if (-not $targetPath) {
    # 默认使用 .codebuddy/skills
    $targetPath = "$env:USERPROFILE\.codebuddy\skills\browserskill-pro"
}

Write-Host "📂 安装路径: $targetPath" -ForegroundColor Yellow

# 检查是否已安装
if ((Test-Path $targetPath) -and -not $Force) {
    Write-Host "⚠️  目标目录已存在。如需覆盖请使用 -Force 参数。" -ForegroundColor Red
    exit 1
}

try {
    # 创建临时目录
    $tempDir = Join-Path $env:TEMP "bsk-install-$([guid]::NewGuid().ToString('N'))"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    Write-Host "📥 正在克隆仓库..." -ForegroundColor Green
    git clone --branch $Branch --depth 1 $RepoUrl $tempDir 2>&1 | ForEach-Object { $_ }

    if ($LASTEXITCODE -ne 0) {
        throw "Git clone 失败"
    }

    # 复制文件
    New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
    Copy-Item "$tempDir\skill\*" -Destination $targetPath -Recurse -Force

    # 验证关键文件
    $requiredFiles = @("SKILL.md", "scripts", "references")
    $allPresent = $true
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path (Join-Path $targetPath $file))) {
            Write-Host "❌ 缺少必要文件: $file" -ForegroundColor Red
            $allPresent = $false
        }
    }

    if ($allPresent) {
        Write-Host "`n✅ 安装成功！" -ForegroundColor Green
        Write-Host "`n📋 安装详情:" -ForegroundColor Cyan
        Write-Host "   版本信息:" (Get-Content (Join-Path $targetPath "SKILL.md") -TotalCount 5 | Select-Object -First 5)
        Write-Host ""
        Get-ChildItem $targetPath | Format-Table Name, Mode, LastWriteTime -AutoSize
        Write-Host ""
        Write-Host "🔧 后续步骤:" -ForegroundColor Yellow
        Write-Host "   1. 重启 CodeBuddy / WorkBuddy 以加载新 skill"
        Write-Host "   2. 运行 doctor.py 检查环境:"
        Write-Host "      py -3 `"$targetPath\scripts\doctor.py`" --wait-connected 20"
        Write-Host "   3. 在对话中使用: 使用 \$browserskill-pro 打开我的浏览器"
    } else {
        throw "安装验证失败：缺少必要文件"
    }
}
catch {
    Write-Host "`n❌ 安装失败: $_" -ForegroundColor Red
    exit 1
}
finally {
    # 清理临时目录
    if (Test-Path $tempDir) {
        Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
    }
}
```

**运行一键安装脚本：**

```powershell
# 方式 A：直接下载并执行（需要网络）
irm https://raw.githubusercontent.com/916938/browserskill-pro/main/install.ps1 | iex

# 方式 B：保存后本地执行
# 1. 先将上面的代码保存为 install.ps1
# 2. 执行：
.\install.ps1 -Branch main

# 强制覆盖已有安装：
.\install.ps1 -Branch main -Force
```

**方法三：手动下载 ZIP 文件**

1. 访问 https://github.com/916938/browserskill-pro
2. 点击绿色的 **"Code"** 按钮 → **"Download ZIP"**
3. 解压到临时目录（例如 `C:\Temp\browserskill-pro-main`）
4. 打开 PowerShell 执行：

```powershell
# 设置变量
$zipExtractPath = "C:\Temp\browserskill-pro-main"  # 改为你的解压路径
$targetPath = "$env:USERPROFILE\.codebuddy\skills\browserskill-pro"

# 创建目录并复制
New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
Copy-Item "$zipExtractPath\skill\*" -Destination $targetPath -Recurse -Force

# 验证
Test-Path "$targetPath\SKILL.md"
```

#### 验证安装（CodeBuddy / WorkBuddy）

安装完成后，在 **CodeBuddy / WorkBuddy** 对话框中测试：

```text
使用 $browserskill-pro 帮我查看当前浏览器的状态
```

或者在终端中运行自检：

```powershell
# 替换 <your-path> 为实际安装路径
py -3 "<your-path-to-codebuddy-skills>\browserskill-pro\scripts\doctor.py" --wait-connected 20
```

**预期输出示例：**
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

#### CodeBuddy / WorkBuddy / Claude Code 环境安装（Linux / macOS）

如果你在 **Linux** 或 **macOS** 系统上使用 **CodeBuddy**、**WorkBuddy** 或 **Claude Code**，可以通过以下步骤从 GitHub 仓库快速安装：

**前提条件检查:**

```bash
# 检查 Git 是否已安装
git --version

# 检查 Python3 是否可用
python3 --version

# 检查 curl/wget（用于下载）
curl --version || wget --version
```

如果缺少依赖，请先安装：

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y git python3 curl

# macOS (使用 Homebrew)
brew install git python3 curl

# Fedora / RHEL
sudo dnf install -y git python3 curl

# Arch Linux
sudo pacman -S git python3 curl
```

**方法一：Git 克隆 + 手动复制（推荐）**

```bash
# 1. 克隆仓库到临时目录
TMPDIR=$(mktemp -d)
git clone https://github.com/916938/browserskill-pro.git "$TMPDIR/browserskill-pro"

# 2. 确定目标 skills 目录（根据你的 Agent 环境）
# CodeBuddy:
TARGET_PATH="$HOME/.codebuddy/skills/browserskill-pro"
# 或 WorkBuddy:
# TARGET_PATH="$HOME/.workbuddy/skills/browserskill-pro"
# 或 Codex:
# TARGET_PATH="$HOME/.codex/skills/browserskill-pro"

# 3. 创建目录并复制文件
mkdir -p "$(dirname "$TARGET_PATH")"
cp -r "$TMPDIR/browserskill-pro/skill/." "$TARGET_PATH"

# 4. 清理临时目录
rm -rf "$TMPDIR"

# 5. 验证安装
echo "✅ BrowserSkill Pro 已安装到: $TARGET_PATH"
ls -la "$TARGET_PATH"
```

**方法二：Bash 一键脚本（自动化）**

创建或下载 `install.sh` 脚本：

```bash
# 方式 A：从 GitHub Raw 直接执行
curl -fsSL https://raw.githubusercontent.com/916938/browserskill-pro/main/install.sh | bash

# 方式 B：先下载再执行（推荐，可审查内容）
curl -fsSL https://raw.githubusercontent.com/916938/browserskill-pro/main/install.sh -o install.sh
chmod +x install.sh
./install.sh --branch main

# 指定自定义路径：
./install.sh --target-path "$HOME/.my-agent/skills/browserskill-pro"

# 强制覆盖已有安装：
./install.sh --force
```

**方法三：手动下载 ZIP 文件**

1. 访问 https://github.com/916938/browserskill-pro
2. 点击绿色的 **"Code"** 按钮 → **"Download ZIP"**
3. 解压到临时目录：

```bash
# 解压（假设下载到 ~/Downloads）
cd ~/Downloads
unzip browserskill-pro-main.zip -d /tmp/bsk-install

# 设置变量并复制
ZIP_EXTRACT="/tmp/bsk-install/browserskill-pro-main"
TARGET="$HOME/.codebuddy/skills/browserskill-pro"

mkdir -p "$(dirname "$TARGET")"
cp -r "$ZIP_EXTRACT/skill/." "$TARGET"

# 验证
test -f "$TARGET/SKILL.md" && echo "✅ 安装成功！" || echo "❌ 安装失败"
```

#### 多环境支持（Linux/macOS）

脚本会自动检测常见的 Agent skills 目录：

| Agent | 默认路径 |
|-------|---------|
| CodeBuddy | `~/.codebuddy/skills/browserskill-pro` |
| **Claude Code** (Skills) | `~/.claude/skills/browserskill-pro` |
| **Claude Code** (Commands) | `~/.claude/commands/browserskill-pro` |
| WorkBuddy | `~/.workbuddy/skills/browserskill-pro` |
| Codex | `~/.codex/skills/browserskill-pro` |
| Custom | 使用 `--target-path` 参数指定 |

**自动检测示例:**

```bash
# 如果 ~/.codebuddy/skills 存在，自动安装到该位置
./install.sh

# 如果多个环境都存在，优先级：codebuddy > claude > workbuddy > codex
# 可通过环境变量覆盖：
CODEBUDDY_SKILLS_DIR=/custom/path ./install.sh
```

#### 验证安装（Linux/macOS CodeBuddy / WorkBuddy）

安装完成后，在终端中运行自检：

```bash
# 替换 <your-path> 为实际安装路径
python3 "<your-path-to-skills>/browserskill-pro/scripts/doctor.py" --wait-connected 20
```

或者在 **CodeBuddy / WorkBuddy** 对话框中测试：

```text
使用 $browserskill-pro 帮我查看当前浏览器的状态
```

**预期输出示例:**
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

**常用命令速查（Linux/macOS）：**

```bash
# 环境自检
python3 "~/.codebuddy/skills/browserskill-pro/scripts/doctor.py" --wait-connected 20

# 页面快照（精简模式）
python3 "~/.codebuddy/skills/browserskill-pro/scripts/snapshot.py" --session demo --auto

# 页面快照（完整模式写入文件）
python3 "~/.codebuddy/skills/browserskill-pro/scripts/snapshot.py" --session demo --mode file

# 截图
python3 "~/.codebuddy/skills/browserskill-pro/scripts/screenshot.py" --session demo

# 等待页面加载完成
python3 "~/.codebuddy/skills/browserskill-pro/scripts/wait_for.py" \
  --session demo --url-contains "example.com" --timeout 10

# 运行单元测试
python3 -m unittest discover -s ~/.codebuddy/skills/browserskill-pro/../tests -v
```

**权限问题排查:**

如果在 Linux 上遇到权限错误：

```bash
# 确保 scripts 有执行权限（可选，Python 不需要但保持一致性）
chmod +x ~/.codebuddy/skills/browserskill-pro/scripts/*.sh
chmod +x ~/.codebuddy/skills/browserskill-pro/scripts/*.py

# 如果 doctor.py 无法访问浏览器 socket：
# 检查当前用户是否在正确的组中（通常不需要特殊权限）
id  # 显示当前用户和组

# 如果遇到 Python 模块导入错误：
# 确保使用系统 Python3（不使用虚拟环境中的版本）
which python3
python3 --version  # 推荐 Python 3.8+
```

**卸载说明（Linux/macOS）：**

```bash
# 直接删除安装目录即可
rm -rf ~/.codebuddy/skills/browserskill-pro

# 或者如果是其他路径：
# rm -rf <your-installation-path>
echo "🗑️ BrowserSkill Pro 已卸载"
```

#### Docker 容器化部署（跨平台）

如果你希望在 **Docker 容器**中运行 BrowserSkill Pro（适用于 CI/CD、隔离环境、或统一部署），我们提供了完整的 Docker 支持。

**前置条件:**

- Docker Engine 20.10+ （[安装指南](https://docs.docker.com/get-docker/)）
- Docker Compose V2+ （用于编排多容器环境）

**验证 Docker 环境:**

```bash
docker --version        # 应显示 Docker 版本
docker compose version   # 应显示 Compose 版本
```

---

**方式一：单容器快速启动（推荐入门使用）**

构建并运行 BrowserSkill Pro 容器：

```bash
# 1. 克隆仓库（如果尚未克隆）
git clone https://github.com/916938/browserskill-pro.git
cd browserskill-pro

# 2. 构建 Docker 镜像
docker build -t browserskill-pro:latest .

# 3. 运行容器（交互模式，查看帮助信息）
docker run --rm -it browserskill-pro:latest

# 4. 运行 doctor.py 自检（需要连接到宿主机上的 bsk daemon）
docker run --rm \
  --network host \                    # 使用宿主机网络访问本地 daemon
  -v ~/.bsk:/app/.bsk:ro \           # 挂载配置文件（只读）
  -v $(pwd)/screenshots:/app/data/screenshots \  # 持久化截图目录
  browserskill-pro:latest python3 skill/scripts/doctor.py --wait-connected 20

# 5. 执行 snapshot 操作示例
docker run --rm \
  --network host \
  browserskill-pro:latest python3 skill/scripts/snapshot.py --session demo --auto
```

**常用 Docker 运行参数：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--network host` | 使用宿主机网络（访问本地 daemon） | 必需 |
| `-v` | 挂载卷（数据持久化或配置共享） | `-v ./data:/app/data` |
| `-e` | 设置环境变量 | `-e LOG_LEVEL=DEBUG` |
| `-p` | 端口映射 | `-p 52801:52801` |
| `--rm` | 退出后自动删除容器 | 推荐用于测试 |
| `-d` | 后台运行（detached mode） | 生产环境推荐 |
| `-it` | 交互式终端（调试用） | 开发时推荐 |

---

**方式二：Docker Compose 编排（完整生产环境）**

适用于需要 **daemon + Chrome + Redis + 监控** 的完整部署场景。

**快速开始（基础版）：**

```bash
# 启动所有服务（daemon + skill + redis + chrome）
docker compose up -d

# 查看服务状态
docker compose ps

# 查看 logs
docker compose logs -f browserskill-pro

# 停止所有服务
docker compose down
```

**架构概览:**

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
│  │   redis  │          │ monitoring  │ (可选, Grafana)     │
│  │ :6379    │          │ :3000       │                      │
│  └──────────┘          └─────────────┘                      │
│                                                             │
│  Volumes:                                                    │
│  ├── bsk-data         (daemon 持久化数据)                    │
│  ├── screenshots-data (截图输出)                             │
│  ├── snapshots-data   (快照缓存)                             │
│  ├── chrome-profile    (浏览器用户数据)                       │
│  └── grafana-data      (监控数据)                            │
└─────────────────────────────────────────────────────────────┘
```

**高级用法:**

```bash
# 仅启动核心服务（不含监控）
docker compose up -d bsk-daemon browserskill-pro redis chrome-browser

# 启动开发环境（源代码热挂载）
docker compose -f docker-compose.dev.yml up --build -d

# 进入开发容器进行调试
docker compose -f docker-compose.dev.yml exec browserskill-pro-dev bash

# 在开发容器内运行测试
docker compose -f docker-compose.dev.yml exec browserskill-pro-dev \
  python3 -m unittest discover -s tests -v

# 启动带监控的完整环境
docker compose --profile monitoring up -d

# 访问 Grafana 仪表板
# 打开 http://localhost:3000 (默认账号: admin/admin)
```

**自定义配置:**

创建 `.env` 文件来自定义部署：

```bash
# .env 文件（放在 docker-compose.yml 同级目录）

# Daemon 配置
BSK_AUTH_TOKEN=your-secure-token-here
BSK_MAX_SESSIONS=20
BSK_IDLE_TIMEOUT=600

# Redis 配置（可选，如需外部 Redis）
REDIS_URL=redis://external-redis-host:6379/0

# Chrome 配置
CHROME_MODE=headed              # 或 headless（无头模式）

# 日志级别
LOG_LEVEL=INFO                  # DEBUG, INFO, WARN, ERROR

# 资源限制
DOCKER_CPUS_LIMIT=2.0
DOCKER_MEMORY_LIMIT=4G
```

---

**方式三：CI/CD 集成（自动化测试场景）**

在 GitHub Actions / GitLab CI / Jenkins 中使用 Docker 进行测试:

**GitHub Actions 示例 (.github/workflows/docker-test.yml):**

```yaml
name: Docker Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      # 启动 BSK daemon 测试服务
      bsk-daemon:
        image: browserskill/bsk-daemon:latest
        ports:
          - 52800:52800
        options: >-
          --health-cmd "curl -f http://localhost:52801/health || exit 1"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker build -t browserskill-pro:test .
      
      - name: Run unit tests in container
        run: |
          docker run --rm \
            --network host \
            browserskill-pro:test \
            python3 -m unittest discover -s tests -v
      
      - name: Run doctor.py health check
        run: |
          docker run --rm \
            --network host \
            browserskill-pro:test \
            python3 skill/scripts/doctor.py --json
      
      - name: Test snapshot functionality
        run: |
          docker run --rm \
            --network host \
            -v ${{ github.workspace }}/test-output:/app/data/screenshots \
            browserskill-pro:test \
            python3 skill/scripts/snapshot.py --session test-session --auto || true
```

---

**Docker 镜像管理:**

```bash
# 构建镜像（多平台支持）
docker buildx build --platform linux/amd64,linux/arm64 -t browserskill-pro:latest .

# 标记并推送到镜像仓库（如 Docker Hub、GitHub Container Registry）
docker tag browserskill-pro:latest ghcr.io/916938/browserskill-pro:v1.1.0
docker push ghcr.io/916938/browserskill-pro:v1.1.0

# 查看镜像大小和层级
docker history browserskill-pro:latest

# 清理未使用的镜像
docker image prune -f

# 导出/导入镜像（离线环境）
docker save -o browserskill-pro.tar browserskill-pro:latest
docker load -i browserskill-pro.tar
```

---

**性能优化建议:**

1. **减小镜像体积:**
   ```dockerfile
   # 使用多阶段构建（已实现在 Dockerfile 中）
   # 最终镜像仅包含运行时依赖
   ```

2. **利用 Docker 缓存层:**
   ```
   # 将不常变化的 COPY 指令放在前面（已优化 .dockerignore）
   ```

3. **生产环境安全加固:**
   ```yaml
   # docker-compose.prod.yml 补充配置
   services:
     browserskill-pro:
       # ... 其他配置 ...
       security_opt:
         - no-new-privileges:true
       read_only: true          # 只读根文件系统（需配合 tmpfs）
       tmpfs:
         - /tmp:size=100M
         - /app/data/screenshots,size=1G
       cap_drop:
         - ALL
       cap_add:
         - NET_BIND_SERVICE      # 仅保留绑定端口权限
   ```

4. **资源限制（防止资源耗尽）:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 2G
       reservations:
         cpus: '0.5'
         memory: 512M
   ```

---

**故障排除:**

| 问题 | 可能原因 | 解决方案 |
|------|---------|----------|
| 容器无法连接到 daemon | 网络模式错误 | 使用 `--network host` 或确保在相同 Docker 网络中 |
| 权限被拒绝（Permission denied） | 卷挂载权限问题 | 检查宿主机目录权限，或在 Docker 中调整用户 ID (`user: "1000:1000"`) |
| 镜像构建失败（网络问题） | Dockerfile 中的网络请求失败 | 检查代理设置，或使用预构建的基础镜像 |
| Chrome 无法启动 | 缺少共享内存或权限 | 增加 `shm_size: '2gb'` 并添加 `privileged: true` |
| 容器重启循环 | 健康检查失败 | 检查日志: `docker compose logs <service>` |

**查看详细日志:**
```bash
# 容器实时日志
docker compose logs -f browserskill-pro

# 进入容器调试
docker compose exec browserskill-pro bash

# 检查容器资源使用
docker stats browserskill-pro
```

### 3. 自检

在发送浏览器动作前，先确认 daemon 和扩展都已就绪：

Windows：

```powershell
py -3 .\browserskill-pro\skill\scripts\doctor.py --wait-connected 20
```

Linux / macOS：

```bash
python3 ./browserskill-pro/skill/scripts/doctor.py --wait-connected 20
```

`doctor.py` 默认不启动 daemon，也不发送浏览器动作。

### 4. 调用

```text
使用 $browserskill-pro 查看我当前登录的网页。
```

```text
使用 $browserskill-pro 在我打开的知乎页面搜索 OpenAI。
```

```text
使用 $browserskill-pro 截取当前页面，并在完成后删除临时文件。
```

## 隐私与安全

### 多浏览器使用

当运行多个装有 BrowserSkill 扩展的 Chromium 浏览器时：

```bash
# 列出所有已连接的浏览器实例
bsk browsers

# 在指定浏览器上启动会话
bsk session start --browser <instance-id-or-label>
```

如果连接了多个浏览器但未指定 `--browser`，`bsk session start` 会输出可用实例列表。每个浏览器拥有独立的 Agent Window 和会话生命周期。

这个 skill 能访问真实登录态，因此应按高权限工具对待。

### 数据流

```text
Local AI agent
    |
    | bsk CLI
    v
127.0.0.1:52800 daemon (WebSocket)
    |
    v
浏览器扩展和真实标签页
```

仓库中的 helper：

- 只通过 `bsk` CLI 发送命令
- 不保存 Cookie、密码、认证令牌或浏览器存储
- 不包含遥测或第三方分析代码
- 截图默认使用临时目录或 bsk 返回的本地路径

但是，本地 daemon 不等于数据永远只停留在本机。页面 snapshot、截图内容、PDF 或网络
结果一旦返回给 agent，就会进入当前 AI 会话的处理范围。

### 默认隐私规则

- 只读取完成任务所需的最少页面内容
- 不读取或返回 Cookie、Authorization、session token、密码字段或浏览器存储
- 临时截图和 PDF 在任务完成后删除，除非用户明确要求保留
- 上传、发送、发布、购买、删除和权限变更前需要确认
- 不绕过验证码、付费墙、年龄限制、浏览器警告或网站安全机制
- 使用 `bsk request-help` 处理需要人工介入的场景

BrowserSkill daemon 和浏览器扩展是外部依赖，其自身的数据处理行为不由本仓库控制。
安装和使用前应自行审阅对应产品的隐私政策与实现。

## 项目结构

```text
browserskill-pro/
├── README.md
├── .gitignore
├── .gitattributes
├── skill/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml       # 可选的 OpenAI/Codex UI 元数据
    ├── examples/
    │   ├── login_and_fill_form.md
    │   ├── scroll_and_extract.md
    │   ├── handle_popup.md
    │   └── network_debug.md
    ├── references/
    │   ├── protocol.md
    │   ├── operations.md
    │   └── how-it-works.md
    └── scripts/
        ├── invoke.ps1
        ├── invoke.sh
        ├── doctor.py
        ├── screenshot.py
        ├── snapshot.py
        ├── wait_for.py
        ├── bsk_client.py
        └── screenshot.ps1
└── tests/
    ├── test_doctor.py
    ├── test_snapshot.py
    └── test_wait_for.py
```

- `SKILL.md`：Agent 正常执行时读取的操作手册
- `examples/`：按需读取的端到端工作流样例
- `protocol.md`：动作参数、响应和隐私约束
- `operations.md`：安装、状态检查和 daemon 故障恢复
- `how-it-works.md`：面向人类维护者的原理说明，内容较长，不推荐 Agent 日常加载

## 验证

通用检查包括 frontmatter、相对链接和脚本语法。若本机安装了 Codex 的
`skill-creator`，还可以使用其校验器：

```powershell
py -3 "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\skill
```

PowerShell 语法检查：

```powershell
Get-ChildItem .\skill\scripts -Filter *.ps1 | ForEach-Object {
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $_.FullName,
        [ref]$null,
        [ref]$errors
    ) | Out-Null
    if ($errors.Count) { throw $errors }
}
```

无副作用的 daemon 冒烟测试：

```powershell
bsk session start
$sessionId = bsk session start
bsk tab list --session $sessionId
bsk session stop $sessionId
```

Bash 调用：

```bash
SESSION_ID=$(bsk session start)
bsk tab list --session $SESSION_ID
bsk session stop $SESSION_ID
```

大型页面快照：

Windows：

```powershell
# 精简输出，适合定位输入框、按钮和链接
py -3 .\skill\scripts\snapshot.py --session demo --auto
py -3 .\skill\scripts\snapshot.py --session demo --mode compact

# 完整快照保存到临时文件，仅返回文件路径
py -3 .\skill\scripts\snapshot.py --session demo --mode file
```

Linux / macOS：

```bash
# 精简输出，适合定位输入框、按钮和链接
python3 ./skill/scripts/snapshot.py --session demo --auto
python3 ./skill/scripts/snapshot.py --session demo --mode compact

# 完整快照保存到临时文件，仅返回文件路径
python3 ./skill/scripts/snapshot.py --session demo --mode file
```

Windows 应使用 `py -3` 或 `py` 启动 Python，不要假定存在 `python3` 命令。

Doctor 自检：

```powershell
py -3 .\skill\scripts\doctor.py --wait-connected 20
```

跨平台截图与等待：

```powershell
py -3 .\skill\scripts\screenshot.py --session demo
py -3 .\skill\scripts\wait_for.py --session demo `
  --url-contains "example.com" --timeout 10
py -3 .\skill\scripts\wait_for.py --session demo `
  --visible-text "已保存" --timeout 10
```

回归测试：

```powershell
py -3 -m unittest discover -s tests -v
```

## 已知限制

- PowerShell helper 目前以 Windows 为主；协议本身可在其他平台通过 bsk CLI 调用
- `snapshot.py` 需要 Python 3，Bash helper 需要 Bash
- 合成点击和输入无法满足要求 `event.isTrusted` 的网站
- 顶层页面操作不能直接访问跨域 iframe 内容
- 浏览器可能拦截站点尝试打开的弹窗或新标签页
- daemon 和扩展升级后，响应协议可能发生变化，需要重新实测

## 贡献

提交修改前请保持以下分层：

1. 脚本只保留帮助理解意图的最小注释
2. `SKILL.md` 只写 Agent 必须执行的步骤和常见问题
3. 协议细节进入 `protocol.md`
4. 生命周期与恢复流程进入 `operations.md`
5. 原理和设计原因进入 `how-it-works.md`

涉及 daemon 协议的改动应通过真实请求验证，不能只依据旧文档推断。