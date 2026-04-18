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

function Read-McpEntry {
    param([string]$Name)

    try {
        $detail = codex mcp get $Name 2>&1 | Out-String
    } catch {
        return [PSCustomObject]@{
            configured = $false
        }
    }

    $viewportSize = $null
    $viewportMatch = [regex]::Match($detail, '(?:--viewport-size|-ViewportSize)\s+(\S+)')
    if ($viewportMatch.Success) {
        $viewportSize = $viewportMatch.Groups[1].Value
    }

    $browserLocale = $null
    $localeMatch = [regex]::Match($detail, '-BrowserLocale\s+(\S+)')
    if ($localeMatch.Success) {
        $browserLocale = $localeMatch.Groups[1].Value
    }

    $profileMode = $null
    $profileModeMatch = [regex]::Match($detail, '-ProfileMode\s+(\S+)')
    if ($profileModeMatch.Success) {
        $profileMode = $profileModeMatch.Groups[1].Value
    }

    $profileDir = $null
    $profileDirMatch = [regex]::Match($detail, '-ProfileDir\s+(.+?)(?:\s+-|$)')
    if ($profileDirMatch.Success) {
        $profileDir = $profileDirMatch.Groups[1].Value.Trim()
    }

    return [PSCustomObject]@{
        configured = $true
        uses_official_package = ($detail -match '@playwright/mcp') -or ($detail -match 'launch-playwright-mcp\.ps1')
        uses_local_chrome = ($detail -match '-ChromePath')
        profile_mode = $profileMode
        profile_dir = $profileDir
        browser_locale = $browserLocale
        viewport_size = $viewportSize
        detail = $detail.Trim()
    }
}

$chromePath = Find-ChromePath
$codexPath = Get-CommandPath 'codex'
$nodePath = Get-CommandPath 'node'
$npxPath = Get-CommandPath 'npx'

$entries = @('playwright-temp-userdir', 'playwright-fixed-userdir')
$entryStatus = @{}

if ($codexPath) {
    foreach ($entry in $entries) {
        $entryStatus[$entry] = Read-McpEntry -Name $entry
    }
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
    recommended_entries = $entries
    recommended_entry_status = $entryStatus
} | ConvertTo-Json -Depth 5
