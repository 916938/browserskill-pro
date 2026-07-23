[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("start", "stop")]
    [string] $SubCommand,

    [string] $Browser,
    [string] $Url,
    [string] $Purpose,
    [string] $Output = "trace.json"
)

# Thin wrapper around `bsk record start` / `bsk record stop`.
# Blocks until the user clicks Finish in the recording panel, then prints
# the trace file path. Keep in sync with record.sh.

switch ($SubCommand) {
    "start" {
        $bskArgs = @("bsk", "record", "start", "--output", $Output)
        if ($Browser) { $bskArgs += @("--browser", $Browser) }
        if ($Url)     { $bskArgs += @("--url", $Url) }
        if ($Purpose) { $bskArgs += @("--purpose", $Purpose) }
        & $bskArgs[0] $bskArgs[1..($bskArgs.Count - 1)]
        $Output
    }
    "stop" {
        bsk record stop --output $Output
        $Output
    }
}
