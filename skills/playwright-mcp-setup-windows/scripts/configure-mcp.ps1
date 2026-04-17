param(
    [string]$McpName = 'playwright',
    [string]$ChromePath,
    [string]$ProfileDir,
    [int]$NavigationTimeoutMs = 90000,
    [string]$ViewportSize = '1600x900',
    [switch]$ForceRecreate
)

$ErrorActionPreference = 'Stop'

function Find-ChromePath {
    $candidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
    ) | Where-Object { $_ -and (Test-Path $_) }

    return $candidates | Select-Object -First 1
}

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw 'codex command not found.'
}

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    throw 'npx command not found.'
}

if (-not $ChromePath) {
    $ChromePath = Find-ChromePath
}

if (-not $ChromePath) {
    throw 'Chrome executable not found automatically. Pass -ChromePath explicitly.'
}

if (-not $ProfileDir) {
    $ProfileDir = Join-Path $env:LocalAppData "ms-playwright\mcp-chrome-profile"
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcherPath = Join-Path $scriptDir 'launch-playwright-mcp.ps1'

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$existing = $null
try {
    $existing = codex mcp get $McpName 2>&1 | Out-String
} catch {
    $existing = $null
}

$needsReplace = $ForceRecreate.IsPresent
if ($existing) {
    if ($existing -notmatch [regex]::Escape($launcherPath)) { $needsReplace = $true }
    if ($existing -notmatch [regex]::Escape($ChromePath)) { $needsReplace = $true }
    if ($existing -notmatch [regex]::Escape($ProfileDir)) { $needsReplace = $true }
    if ($ViewportSize) {
        if ($existing -notmatch ('-ViewportSize\s+' + [regex]::Escape($ViewportSize))) { $needsReplace = $true }
    } elseif ($existing -match '-ViewportSize\s+\S+') {
        $needsReplace = $true
    }
}

if ($existing -and $needsReplace) {
    codex mcp remove $McpName | Out-Null
}

if (-not $existing -or $needsReplace) {
    $addArgs = @(
        'mcp', 'add', $McpName, '--',
        'powershell', '-ExecutionPolicy', 'Bypass', '-File', $launcherPath,
        '-ChromePath', $ChromePath,
        '-ProfileDir', $ProfileDir,
        '-NavigationTimeoutMs', $NavigationTimeoutMs
    )

    if ($ViewportSize) {
        $addArgs += @('-ViewportSize', $ViewportSize)
    }

    & codex @addArgs | Out-Null
}

codex mcp get $McpName
