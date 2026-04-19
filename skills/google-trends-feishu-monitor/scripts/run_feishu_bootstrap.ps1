param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"

function Get-CodexHome {
    if ($env:CODEX_HOME) {
        return $env:CODEX_HOME
    }
    if ($env:USERPROFILE) {
        return (Join-Path $env:USERPROFILE ".codex")
    }
    throw "Unable to resolve CODEX_HOME. Set CODEX_HOME or USERPROFILE first."
}

$codexHome = Get-CodexHome
$bootstrap = Join-Path $codexHome "skills\feishu-sheets-toolkit\scripts\bootstrap.mjs"

if (-not (Test-Path $bootstrap)) {
    throw "feishu-sheets-toolkit is not installed at $bootstrap. Install that skill first, then rerun."
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is required but was not found in PATH."
}

& node $bootstrap @Arguments
