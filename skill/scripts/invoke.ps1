[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Action,

    [object] $ActionArgs = @{},

    [string] $ArgsFile,

    [string] $Session,

    [ValidateRange(1, 300)]
    [int] $TimeoutSec = 30,

    [switch] $DryRun,

    [switch] $Force
)

# Thin passthrough to `bsk invoke` (or legacy direct commands).
#
# This helper auto-detects whether `bsk invoke` is available:
# - If available (bsk 0.2.0+): forwards raw JSON via `bsk invoke --action <name> --args-json <json>`
# - If unavailable (legacy): falls back to calling typed `bsk <command>` subcommands directly
#
# The daemon forwards the params object to the extension verbatim, so in passthrough
# mode this helper only assembles a JSON object and hands it to `bsk invoke --args-json`.
# In legacy mode it flattens the JSON into typed flags, which has limitations with
# complex/nested arguments. Keep in sync with invoke.sh.
#
# --action accepts a bare tool name (fill, tab_list) or a qualified method
# (tool.fill). Session-stopping actions are guarded behind -Force.

# Every spelling that resolves to a session-stopping method (bsk invoke maps
# session_stop -> session.stop, session_stop_all -> session.stop_all). Keep this
# list identical to the one in invoke.sh. `close_session` is the deprecated
# friendly name, kept so old callers still hit the -Force gate.
$stopActions = @(
    "session_stop", "session_stop_all",
    "session.stop", "session.stop_all",
    "close_session", "tool.session_stop"
)
if ($stopActions -contains $Action) {
    if (-not $Force) {
        throw "Refusing $Action without -Force; verify every tab is task-owned."
    }
    Write-Warning "Forced $Action can close every tab attached to this session. Run tab_list first and verify they are task-owned."
}

# Resolve the JSON params payload from exactly one source: -ArgsFile or
# -ActionArgs. Both set is an error.
$hasInlineArgs = $false
if ($null -ne $ActionArgs) {
    if ($ActionArgs -is [System.Collections.IDictionary]) {
        $hasInlineArgs = $ActionArgs.Count -gt 0
    }
    else {
        $hasInlineArgs = $true
    }
}

$argsJson = $null
if ($ArgsFile) {
    if ($hasInlineArgs) {
        throw "Use either -ActionArgs or -ArgsFile, not both."
    }
    if (-not (Test-Path -LiteralPath $ArgsFile -PathType Leaf)) {
        throw "Arguments file not found: $ArgsFile"
    }
    $argsJson = Get-Content -LiteralPath $ArgsFile -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($argsJson)) {
        throw "Arguments file is empty: $ArgsFile"
    }
    # Validate it is a JSON object before shipping it to bsk, so the failure
    # names the file instead of surfacing as a generic parse error.
    try {
        $parsed = $argsJson | ConvertFrom-Json
    }
    catch {
        throw "Arguments file must contain valid UTF-8 JSON: $($_.Exception.Message)"
    }
    if ($null -eq $parsed -or $parsed -is [array] -or $parsed -is [string] -or $parsed -is [ValueType]) {
        throw "Arguments file must contain a JSON object."
    }
}
elseif ($hasInlineArgs) {
    if (-not ($ActionArgs -is [System.Collections.IDictionary])) {
        throw "-ActionArgs must be a hashtable / dictionary."
    }
    # ConvertTo-Json emits UTF-8 correctly; -Compress keeps the arg on one line.
    $argsJson = $ActionArgs | ConvertTo-Json -Depth 50 -Compress
}

# Auto-detect whether bsk supports the 'invoke' subcommand.
function Test-InvokeSupport {
    try {
        $null = & bsk invoke --help 2>&1 | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Execute using bsk invoke (passthrough mode) - preferred for bsk 0.2.0+
function Execute-WithInvoke {
    $bskArgs = @("bsk", "invoke", "--action", $Action)

    if ($Session) {
        $bskArgs += @("--session", $Session)
    }

    if ($null -ne $argsJson) {
        $bskArgs += @("--args-json", $argsJson)
    }

    $bskArgs += @("--timeout-ms", ($TimeoutSec * 1000).ToString())
    $bskArgs += "--json"

    if ($DryRun) {
        $bskArgs -join " "
        return
    }

    try {
        $response = & $bskArgs[0] $bskArgs[1..($bskArgs.Count - 1)]
    }
    catch {
        throw "BrowserSkill command failed: $($_.Exception.Message)"
    }

    if ($response) {
        # bsk --json already prints a JSON document; pass it through unchanged.
        $response
    }
}

# Legacy mode: map action names to specific bsk commands (for bsk < 0.2.0).
# This flattens JSON args into typed flags, which has limitations with
# complex/nested JSON but works for simple cases.
function Execute-Legacy {
    $cmd = ""
    $cmdArgs = @()

    # Parse args payload once for legacy extraction
    $payloadObj = $null
    if ($argsJson) {
        $payloadObj = $argsJson | ConvertFrom-Json
    }

    # Helper to extract string value from payload
    function Get-PayloadValue {
        param([string]$Key, [string]$Default = "")

        if ($payloadObj -and ($payloadObj.PSObject.Properties[$Key])) {
            return $payloadObj.$Key.ToString()
        }
        return $Default
    }

    # Map action names to bsk commands
    switch ($Action) {
        "navigate" {
            $cmd = "navigate"
            $url = Get-PayloadValue "url"
            $cmdArgs += @($url)
        }
        "tab_create" {
            $cmd = "tab create"
            $url = Get-PayloadValue "url"
            if ($url) { $cmdArgs += @("--url", $url) }
        }
        "tab_list" {
            $cmd = "tab list"
            $scope = Get-PayloadValue "scope"
            if ($scope) { $cmdArgs += @("--scope", $scope) }
        }
        "snapshot" {
            $cmd = "snapshot"
        }
        "click" {
            $cmd = "click"
            $selector = (Get-PayloadValue "selector") -or (Get-PayloadValue "ref")
            $cmdArgs += @($selector)
        }
        "fill" {
            $cmd = "fill"
            $selector = (Get-PayloadValue "selector") -or (Get-PayloadValue "ref")
            $value = Get-PayloadValue "value"
            $cmdArgs += @($selector, "--value", $value)
        }
        "evaluate" {
            $cmd = "evaluate"
            $expression = Get-PayloadValue "expression"
            $cmdArgs += @($expression)
        }
        "screenshot" {
            $cmd = "screenshot"
            $ref = Get-PayloadValue "ref"
            $out = Get-PayloadValue "out"
            if ($ref) { $cmdArgs += @("--ref", $ref) }
            if ($out) { $cmdArgs += @("--out", $out) }
        }
        "tab_close" {
            $cmd = "tab close"
            $tabId = Get-PayloadValue "tab_id"
            $cmdArgs += @($tabId)
        }
        "session_stop" {
            $cmd = "session stop"
            if ($Session) { $cmdArgs += @($Session) }
        }
        "press" {
            $cmd = "press"
            $key = Get-PayloadValue "key"
            $cmdArgs += @($key)
        }
        "select" {
            $cmd = "select"
            $selector = (Get-PayloadValue "selector") -or (Get-PayloadValue "ref")
            $value = Get-PayloadValue "value"
            $cmdArgs += @($selector, "--value", $value)
        }
        "navigate-back" {
            $cmd = "navigate-back"
        }
        "navigate-forward" {
            $cmd = "navigate-forward"
        }
        "reload" {
            $cmd = "reload"
            $hard = Get-PayloadValue "hard"
            if ($hard -eq "True" -or $hard -eq "true") { $cmdArgs += @("--hard") }
        }
        "request-help" {
            $cmd = "request-help"
            $prompt = Get-PayloadValue "prompt"
            $title = Get-PayloadValue "title"
            $timeoutVal = Get-PayloadValue "timeout" -or "5m"

            if ($prompt) { $cmdArgs += @("--prompt", $prompt) }
            if ($title) { $cmdArgs += @("--title", $title) }
            $cmdArgs += @("--timeout", $timeoutVal)

            # Parse targets array
            if ($payloadObj -and ($payloadObj.PSObject.Properties["target"])) {
                $targets = $payloadObj.target
                if ($targets -is [string]) {
                    $targets = @($targets)
                }
                foreach ($t in $targets) {
                    $cmdArgs += @("--target", $t.ToString())
                }
            }
        }
        "get-html" {
            $cmd = "get-html"
        }
        "wait-for-navigation" {
            $cmd = "wait-for-navigation"
        }
        "wait-ms" {
            $cmd = "wait-ms"
            $duration = Get-PayloadValue "duration"
            $cmdArgs += @($duration)
        }
        { $_ -in @("tab_select", "select-tab") } {
            $cmd = "tab select"
            $tabId = Get-PayloadValue "tab_id"
            $cmdArgs += @($tabId)
        }
        default {
            throw "Unknown legacy action: $Action (bsk invoke unavailable). Available actions: navigate, tab_create, tab_list, snapshot, click, fill, evaluate, screenshot, tab_close, session_stop, press, select, navigate-back, navigate-forward, reload, request-help, get-html, wait-for-navigation, wait-ms, tab_select"
        }
    }

    # Add session flag for commands that require it
    $sessionRequiredActions = @(
        "navigate", "tab_create", "snapshot", "click", "fill", "evaluate",
        "screenshot", "press", "select", "reload", "get-html",
        "wait-for-navigation", "tab_list", "tab_close", "tab_select"
    )
    if ($sessionRequiredActions -contains $Action -and $Session) {
        $cmdArgs += @("--session", $Session)
    }

    $bskArgs = @("bsk", $cmd) + $cmdArgs + @("--json")

    if ($DryRun) {
        $bskArgs -join " "
        return
    }

    try {
        $response = & $bskArgs[0] $bskArgs[1..($bskArgs.Count - 1)]
    }
    catch {
        throw "BrowserSkill command failed: $($_.Exception.Message)"
    }

    if ($response) {
        $response
    }
}

# Main execution logic: auto-detect and dispatch
if (Test-InvokeSupport) {
    Write-Verbose "Using bsk invoke passthrough mode"
    Execute-WithInvoke
}
else {
    Write-Verbose "Falling back to legacy direct-command mode"
    Execute-Legacy
}
