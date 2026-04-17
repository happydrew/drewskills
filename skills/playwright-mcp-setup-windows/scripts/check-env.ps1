$ErrorActionPreference = 'Stop'

function Get-CommandPath {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Find-ChromePath {
    $candidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    return $candidates | Select-Object -First 1
}

$chromePath = Find-ChromePath
$codexPath = Get-CommandPath 'codex'
$nodePath = Get-CommandPath 'node'
$npxPath = Get-CommandPath 'npx'
$playwrightMcpCmd = Get-CommandPath 'playwright-mcp'

$mcpList = ''
try {
    if ($codexPath) {
        $mcpList = codex mcp list 2>&1 | Out-String
    }
} catch {
    $mcpList = $_ | Out-String
}

$mcpGet = ''
$playwrightConfigured = $false
$usesOfficialPackage = $false
$usesChrome = $false
$usesPersistentProfile = $false

try {
    if ($codexPath -and $mcpList -match '(?m)^\s*playwright\s') {
        $playwrightConfigured = $true
        $mcpGet = codex mcp get playwright 2>&1 | Out-String
        $usesOfficialPackage = $mcpGet -match '@playwright/mcp'
        $usesChrome = $mcpGet -match '--browser chrome'
        $usesPersistentProfile = $mcpGet -match '--user-data-dir'
    }
} catch {
    $mcpGet = $_ | Out-String
}

[PSCustomObject]@{
    codex_found = [bool]$codexPath
    codex_path = $codexPath
    node_found = [bool]$nodePath
    node_path = $nodePath
    npx_found = [bool]$npxPath
    npx_path = $npxPath
    chrome_found = [bool]$chromePath
    chrome_path = $chromePath
    playwright_mcp_cmd_found = [bool]$playwrightMcpCmd
    playwright_mcp_cmd_path = $playwrightMcpCmd
    playwright_mcp_configured = $playwrightConfigured
    uses_official_package = $usesOfficialPackage
    uses_chrome = $usesChrome
    uses_persistent_profile = $usesPersistentProfile
} | ConvertTo-Json -Depth 3

if ($mcpGet) {
    Write-Output '--- MCP DETAIL START ---'
    Write-Output $mcpGet.Trim()
    Write-Output '--- MCP DETAIL END ---'
}
