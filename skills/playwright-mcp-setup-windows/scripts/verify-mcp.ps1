param(
    [string]$McpName = 'playwright',
    [switch]$IncludeTrendsCheck
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw 'codex command not found.'
}

function Get-McpDetail {
    param([string]$Name)
    return (codex mcp get $Name 2>&1 | Out-String)
}

function Get-ProfileDirFromMcpDetail {
    param([string]$Detail)

    $pattern = '--user-data-dir\s+(.+?)(?:\s+--|$)'
    $match = [regex]::Match($Detail, $pattern)
    if ($match.Success) {
        return $match.Groups[1].Value.Trim()
    }
    return $null
}

function Stop-ChromeUsingProfile {
    param([string]$ProfileDir)

    if (-not $ProfileDir) {
        return
    }

    $procs = Get-CimInstance Win32_Process -Filter "name = 'chrome.exe'" |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*$ProfileDir*" }

    if ($procs) {
        $ids = $procs.ProcessId
        Stop-Process -Id $ids -Force
        Start-Sleep -Seconds 2
        Write-Output ("Stopped profile-scoped Chrome PIDs: " + ($ids -join ', '))
    }
}

$mcpDetail = Get-McpDetail -Name $McpName
$profileDir = Get-ProfileDirFromMcpDetail -Detail $mcpDetail
Stop-ChromeUsingProfile -ProfileDir $profileDir

$tmp = Join-Path $env:TEMP 'codex-playwright-mcp-verify.txt'
if (Test-Path $tmp) {
    Remove-Item $tmp -Force
}

$prompt = @'
Use the configured Playwright MCP browser tools, not web search.

Perform exactly these checks:
1. Navigate to https://example.com/ and report the page title and the visible primary link text.
2. Navigate to this data URL and interact with it:
data:text/html,<html><body><input id="name" /><button id="go" onclick="document.getElementById(&quot;out&quot;).textContent=&quot;Hello, &quot;+document.getElementById(&quot;name&quot;).value">Run</button><div id="out"></div></body></html>
Fill the input with hello, click the Run button, and report the final text shown in #out.

Return a short plain text result with PASS/FAIL for each check.
'@

$prompt | codex exec --dangerously-bypass-approvals-and-sandbox -o $tmp -
$baseResult = Get-Content $tmp -Raw

Write-Output '--- VERIFY BASE START ---'
Write-Output $baseResult.Trim()
Write-Output '--- VERIFY BASE END ---'

if ($IncludeTrendsCheck) {
    $tmp2 = Join-Path $env:TEMP 'codex-playwright-mcp-trends-verify.txt'
    if (Test-Path $tmp2) {
        Remove-Item $tmp2 -Force
    }

    $prompt2 = @'
Use the configured Playwright MCP browser tools, not web search.
Navigate to https://trends.google.com/ .
Wait for the page to settle, then report:
1. final page URL
2. page title
3. whether the page appears usable or is blocked/challenged
Keep the answer very short.
'@

    $prompt2 | codex exec --dangerously-bypass-approvals-and-sandbox -o $tmp2 -
    $trendsResult = Get-Content $tmp2 -Raw

    Write-Output '--- VERIFY TRENDS START ---'
    Write-Output $trendsResult.Trim()
    Write-Output '--- VERIFY TRENDS END ---'
}
