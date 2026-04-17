param(
    [Parameter(Mandatory = $true)]
    [string]$ChromePath,
    [Parameter(Mandatory = $true)]
    [string]$ProfileDir,
    [int]$NavigationTimeoutMs = 90000,
    [string]$ViewportSize = '1600x900'
)

$ErrorActionPreference = 'Stop'

$arguments = @(
    '-y', '@playwright/mcp@latest',
    '--browser', 'chrome',
    '--executable-path', $ChromePath,
    '--user-data-dir', $ProfileDir,
    '--timeout-navigation', $NavigationTimeoutMs,
    '--viewport-size', $ViewportSize
)

& npx @arguments
