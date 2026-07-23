[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Session,

    [string] $TabId,
    [string] $Since,
    [int] $Limit,
    [int] $MaxTextChars,
    [switch] $Json
)

# Thin wrapper around `bsk network` — read buffered network responses/failures
# for a tab. Cursor-paginated: pass the previous call's next_since to -Since to
# read only new entries. Keep in sync with network.sh.

$bskArgs = @("bsk", "network", "--session", $Session)
if ($TabId)       { $bskArgs += @("--tab-id", $TabId) }
if ($Since)       { $bskArgs += @("--since", $Since) }
if ($PSBoundParameters.ContainsKey("Limit"))        { $bskArgs += @("--limit", $Limit.ToString()) }
if ($PSBoundParameters.ContainsKey("MaxTextChars")) { $bskArgs += @("--max-text-chars", $MaxTextChars.ToString()) }
if ($Json)        { $bskArgs += "--json" }

& $bskArgs[0] $bskArgs[1..($bskArgs.Count - 1)]
