param(
    [string]$McpName,
    [string]$ChromePath,
    [string]$ProfileDir,
    [ValidateSet('persistent', 'temporary')]
    [string]$ProfileMode,
    [int]$NavigationTimeoutMs = 90000,
    [string]$ViewportSize = '1600x900',
    [string]$BrowserLocale = 'en-US',
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

function Resolve-DefaultEntries {
    $fixedProfileDir = Join-Path $env:LocalAppData 'ms-playwright\mcp-fixed-userdir-profile'
    return @(
        [PSCustomObject]@{
            Name = 'playwright-temp-userdir'
            ProfileMode = 'temporary'
            ProfileDir = $null
        },
        [PSCustomObject]@{
            Name = 'playwright-fixed-userdir'
            ProfileMode = 'persistent'
            ProfileDir = $fixedProfileDir
        }
    )
}

function Ensure-McpEntry {
    param(
        [string]$EntryName,
        [string]$EntryChromePath,
        [string]$EntryProfileDir,
        [string]$EntryProfileMode,
        [int]$EntryNavigationTimeoutMs,
        [string]$EntryViewportSize,
        [string]$EntryBrowserLocale,
        [switch]$EntryForceRecreate
    )

    $launcherPath = Join-Path $script:SkillScriptDir 'launch-playwright-mcp.ps1'

    if ($EntryProfileMode -eq 'persistent') {
        if (-not $EntryProfileDir) {
            throw "ProfileDir is required for persistent MCP entry '$EntryName'."
        }
        New-Item -ItemType Directory -Force -Path $EntryProfileDir | Out-Null
    }

    $existing = $null
    try {
        $existing = codex mcp get $EntryName 2>&1 | Out-String
    } catch {
        $existing = $null
    }

    $needsReplace = $EntryForceRecreate.IsPresent
    if ($existing) {
        if ($existing -notmatch [regex]::Escape($launcherPath)) { $needsReplace = $true }
        if ($existing -notmatch [regex]::Escape($EntryChromePath)) { $needsReplace = $true }
        if ($existing -notmatch ('-ProfileMode\s+' + [regex]::Escape($EntryProfileMode))) { $needsReplace = $true }
        if ($existing -notmatch ('-BrowserLocale\s+' + [regex]::Escape($EntryBrowserLocale))) { $needsReplace = $true }

        if ($EntryProfileMode -eq 'persistent') {
            if ($existing -notmatch [regex]::Escape($EntryProfileDir)) { $needsReplace = $true }
        } elseif ($existing -match '-ProfileDir\s+\S+') {
            $needsReplace = $true
        }

        if ($EntryViewportSize) {
            if ($existing -notmatch ('-ViewportSize\s+' + [regex]::Escape($EntryViewportSize))) { $needsReplace = $true }
        } elseif ($existing -match '-ViewportSize\s+\S+') {
            $needsReplace = $true
        }
    }

    if ($existing -and $needsReplace) {
        codex mcp remove $EntryName | Out-Null
    }

    if (-not $existing -or $needsReplace) {
        $addArgs = @(
            'mcp', 'add', $EntryName, '--',
            'powershell', '-ExecutionPolicy', 'Bypass', '-File', $launcherPath,
            '-ChromePath', $EntryChromePath,
            '-ProfileMode', $EntryProfileMode,
            '-NavigationTimeoutMs', $EntryNavigationTimeoutMs
        )

        if ($EntryProfileMode -eq 'persistent') {
            $addArgs += @('-ProfileDir', $EntryProfileDir)
        }

        if ($EntryViewportSize) {
            $addArgs += @('-ViewportSize', $EntryViewportSize)
        }

        if ($EntryBrowserLocale) {
            $addArgs += @('-BrowserLocale', $EntryBrowserLocale)
        }

        & codex @addArgs | Out-Null
    }

    return (codex mcp get $EntryName 2>&1 | Out-String).Trim()
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

$script:SkillScriptDir = Split-Path -Parent $PSCommandPath

$results = @()

if ($McpName) {
    if (-not $ProfileMode) {
        if ($McpName -match 'temp') {
            $ProfileMode = 'temporary'
        } else {
            $ProfileMode = 'persistent'
        }
    }

    if ($ProfileMode -eq 'persistent' -and -not $ProfileDir) {
        $ProfileDir = Join-Path $env:LocalAppData 'ms-playwright\mcp-fixed-userdir-profile'
    }

    $results += Ensure-McpEntry `
        -EntryName $McpName `
        -EntryChromePath $ChromePath `
        -EntryProfileDir $ProfileDir `
        -EntryProfileMode $ProfileMode `
        -EntryNavigationTimeoutMs $NavigationTimeoutMs `
        -EntryViewportSize $ViewportSize `
        -EntryBrowserLocale $BrowserLocale `
        -EntryForceRecreate:$ForceRecreate.IsPresent
} else {
    foreach ($entry in Resolve-DefaultEntries) {
        $results += Ensure-McpEntry `
            -EntryName $entry.Name `
            -EntryChromePath $ChromePath `
            -EntryProfileDir $entry.ProfileDir `
            -EntryProfileMode $entry.ProfileMode `
            -EntryNavigationTimeoutMs $NavigationTimeoutMs `
            -EntryViewportSize $ViewportSize `
            -EntryBrowserLocale $BrowserLocale `
            -EntryForceRecreate:$ForceRecreate.IsPresent
    }
}

$results -join "`r`n`r`n"
