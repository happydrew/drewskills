param(
    [Parameter(Mandatory = $true)]
    [string]$ChromePath,
    [string]$ProfileDir,
    [ValidateSet('persistent', 'temporary')]
    [string]$ProfileMode = 'persistent',
    [int]$NavigationTimeoutMs = 90000,
    [string]$ViewportSize = '1600x900',
    [string]$BrowserLocale = 'en-US'
)

$ErrorActionPreference = 'Stop'

function New-TemporaryProfileDir {
    $root = Join-Path $env:LocalAppData 'ms-playwright\mcp-temp-profiles'
    $name = '{0:yyyyMMdd-HHmmss}-{1}' -f (Get-Date), ([guid]::NewGuid().ToString('N').Substring(0, 8))
    $path = Join-Path $root $name
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    return $path
}

function Resolve-ProfileSettings {
    param(
        [string]$ConfiguredProfileDir,
        [string]$ConfiguredProfileMode
    )

    $resolvedMode = if ($env:CODEX_PLAYWRIGHT_PROFILE_MODE) {
        $env:CODEX_PLAYWRIGHT_PROFILE_MODE.Trim().ToLowerInvariant()
    } else {
        $ConfiguredProfileMode.Trim().ToLowerInvariant()
    }

    switch ($resolvedMode) {
        'temp' { $resolvedMode = 'temporary' }
        'temporary' { }
        'persistent' { }
        default {
            throw "Unsupported Playwright profile mode '$resolvedMode'. Use 'persistent' or 'temporary'."
        }
    }

    if ($resolvedMode -eq 'temporary') {
        return [PSCustomObject]@{
            Cleanup = $true
            Mode = $resolvedMode
            ProfileDir = (New-TemporaryProfileDir)
        }
    }

    $resolvedProfileDir = if ($env:CODEX_PLAYWRIGHT_PROFILE_DIR) {
        $env:CODEX_PLAYWRIGHT_PROFILE_DIR
    } elseif ($ConfiguredProfileDir) {
        $ConfiguredProfileDir
    } else {
        Join-Path $env:LocalAppData 'ms-playwright\mcp-chrome-profile'
    }

    New-Item -ItemType Directory -Force -Path $resolvedProfileDir | Out-Null

    return [PSCustomObject]@{
        Cleanup = $false
        Mode = $resolvedMode
        ProfileDir = $resolvedProfileDir
    }
}

function Resolve-BrowserLocale {
    param([string]$ConfiguredBrowserLocale)

    if ($env:CODEX_PLAYWRIGHT_BROWSER_LOCALE) {
        return $env:CODEX_PLAYWRIGHT_BROWSER_LOCALE.Trim()
    }

    return $ConfiguredBrowserLocale
}

function Parse-ViewportSize {
    param([string]$ConfiguredViewportSize)

    $match = [regex]::Match($ConfiguredViewportSize, '^(?<width>\d+)x(?<height>\d+)$')
    if (-not $match.Success) {
        throw "Invalid viewport size '$ConfiguredViewportSize'. Use WIDTHxHEIGHT, for example 1600x900."
    }

    return [PSCustomObject]@{
        Width = [int]$match.Groups['width'].Value
        Height = [int]$match.Groups['height'].Value
    }
}

function New-McpConfigFile {
    param(
        [string]$ResolvedChromePath,
        [string]$ResolvedProfileDir,
        [string]$ResolvedBrowserLocale,
        [pscustomobject]$ResolvedViewport
    )

    $root = Join-Path $env:TEMP 'codex-playwright-mcp'
    New-Item -ItemType Directory -Force -Path $root | Out-Null

    $configPath = Join-Path $root ('config-' + [guid]::NewGuid().ToString('N') + '.json')
    $config = @{
        browser = @{
            browserName = 'chromium'
            userDataDir = $ResolvedProfileDir
            launchOptions = @{
                executablePath = $ResolvedChromePath
                args = @('--lang=' + $ResolvedBrowserLocale)
            }
            contextOptions = @{
                locale = $ResolvedBrowserLocale
                viewport = @{
                    width = $ResolvedViewport.Width
                    height = $ResolvedViewport.Height
                }
            }
        }
    }

    $config | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $configPath -Encoding UTF8
    return $configPath
}

$profileSettings = Resolve-ProfileSettings -ConfiguredProfileDir $ProfileDir -ConfiguredProfileMode $ProfileMode
$browserLocale = Resolve-BrowserLocale -ConfiguredBrowserLocale $BrowserLocale
$viewport = Parse-ViewportSize -ConfiguredViewportSize $ViewportSize
$mcpConfigPath = New-McpConfigFile -ResolvedChromePath $ChromePath -ResolvedProfileDir $profileSettings.ProfileDir -ResolvedBrowserLocale $browserLocale -ResolvedViewport $viewport

$arguments = @(
    '-y', '@playwright/mcp@latest',
    '--config', $mcpConfigPath,
    '--timeout-navigation', $NavigationTimeoutMs,
    '--viewport-size', $ViewportSize
)

try {
    & npx @arguments
} finally {
    if (Test-Path -LiteralPath $mcpConfigPath) {
        Remove-Item -LiteralPath $mcpConfigPath -Force -ErrorAction SilentlyContinue
    }

    if ($profileSettings.Cleanup -and (Test-Path -LiteralPath $profileSettings.ProfileDir)) {
        Remove-Item -LiteralPath $profileSettings.ProfileDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
