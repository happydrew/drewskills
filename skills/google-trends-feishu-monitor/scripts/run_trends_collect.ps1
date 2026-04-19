param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is required but was not found in PATH."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm is required but was not found in PATH."
}

$skillRoot = Split-Path -Parent $PSScriptRoot
$playwrightModule = Join-Path $skillRoot "node_modules\playwright-core"

if (-not (Test-Path $playwrightModule)) {
    Push-Location $skillRoot
    try {
        & npm install --no-fund --no-audit
    } finally {
        Pop-Location
    }
}

& node (Join-Path $PSScriptRoot "trends_cdp_collect.mjs") @Arguments
