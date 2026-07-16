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

#### Codex 安装示例

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

重新启动 Agent 或打开新会话，使 skill 列表重新加载。

#### CodeBuddy / WorkBuddy 环境安装（Windows）

如果你使用 **CodeBuddy** 或 **WorkBuddy** 作为 AI Agent 环境，可以通过以下步骤从 GitHub 仓库快速安装：

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