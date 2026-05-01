param(
    [string[]]$McpNames,
    [switch]$IncludeTrendsCheck
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw 'codex command not found.'
}

function Resolve-CodexExecCommand {
    $nativeCodex = Get-Command codex -All |
        Where-Object { $_.CommandType -eq 'Application' } |
        Select-Object -First 1

    if ($nativeCodex) {
        return $nativeCodex.Source
    }

    return (Get-Command codex -ErrorAction Stop).Source
}

function Resolve-McpNames {
    param([string[]]$RequestedNames)

    if ($RequestedNames -and $RequestedNames.Count -gt 0) {
        return $RequestedNames
    }

    $mcpList = codex mcp list 2>&1 | Out-String
    $preferredNames = @('playwright-temp-userdir', 'playwright-fixed-userdir')
    $resolved = @()
    foreach ($candidate in $preferredNames) {
        if ($mcpList -match ("(?m)^\\s*" + [regex]::Escape($candidate) + "\\s")) {
            $resolved += $candidate
        }
    }

    if ($resolved.Count -gt 0) {
        return $resolved
    }

    $fallbackMatch = [regex]::Matches($mcpList, '(?m)^(playwright[^\s]*)\s')
    foreach ($match in $fallbackMatch) {
        $resolved += $match.Groups[1].Value
    }

    if ($resolved.Count -eq 0) {
        throw 'No Playwright MCP entries found. Configure them before running verify-mcp.ps1.'
    }

    return $resolved
}

function Get-McpDetail {
    param([string]$Name)
    return (codex mcp get $Name 2>&1 | Out-String)
}

function Get-ProfileDirFromMcpDetail {
    param([string]$Detail)

    $match = [regex]::Match($Detail, '-ProfileDir\s+(.+?)(?:\s+-|$)')
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
        Write-Output ("Stopped profile-scoped Chrome PIDs for " + $ProfileDir + ': ' + ($ids -join ', '))
    }
}

function Invoke-QuietCodexExec {
    param(
        [string]$Prompt,
        [string]$OutputPath
    )

    $promptPath = Join-Path $env:TEMP ('codex-playwright-mcp-prompt-' + [guid]::NewGuid().ToString('N') + '.txt')
    Set-Content -LiteralPath $promptPath -Value $Prompt -Encoding UTF8

    try {
        $cmdLine = ('"{0}" exec --ephemeral --dangerously-bypass-approvals-and-sandbox -o "{1}" - < "{2}" >nul 2>nul' -f $script:CodexExecCommand, $OutputPath, $promptPath)
        & cmd.exe /d /c $cmdLine | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "codex exec failed with exit code $LASTEXITCODE for output path '$OutputPath'."
        }
    } finally {
        if (Test-Path -LiteralPath $promptPath) {
            Remove-Item -LiteralPath $promptPath -Force -ErrorAction SilentlyContinue
        }
    }

    if (-not (Test-Path -LiteralPath $OutputPath)) {
        throw "codex exec did not create the expected output file '$OutputPath'."
    }

    return (Get-Content -LiteralPath $OutputPath -Raw)
}

$script:CodexExecCommand = Resolve-CodexExecCommand
$resolvedNames = Resolve-McpNames -RequestedNames $McpNames

foreach ($name in $resolvedNames) {
    $detail = Get-McpDetail -Name $name
    $profileDir = Get-ProfileDirFromMcpDetail -Detail $detail
    Stop-ChromeUsingProfile -ProfileDir $profileDir

    $tmp = Join-Path $env:TEMP ('codex-playwright-mcp-verify-' + $name + '.txt')
    if (Test-Path $tmp) {
        Remove-Item -LiteralPath $tmp -Force
    }

    $prompt = @"
Use the MCP server named $name. Do not use web search.

Perform exactly these checks:
1. Navigate to this data URL and report:
- navigator.language
- navigator.languages joined by comma
data:text/html,<html><body>lang-check</body></html>
2. Navigate to https://example.com/ and report the page title and the visible primary link text.
3. Navigate to this data URL:
data:text/html,<html><body><input id="name" /><button id="go" onclick="document.getElementById(&quot;out&quot;).textContent=&quot;Hello, &quot;+document.getElementById(&quot;name&quot;).value">Run</button><div id="out"></div></body></html>
Fill the input with hello, click the Run button, and report the final text shown in #out.

Return a short plain text result with PASS or FAIL for:
- locale check: expect navigator.language to be en-US
- example.com check
- interaction check
"@

    $baseResult = Invoke-QuietCodexExec -Prompt $prompt -OutputPath $tmp

    Write-Output ("--- VERIFY " + $name + " START ---")
    Write-Output $baseResult.Trim()
    Write-Output ("--- VERIFY " + $name + " END ---")

    if ($IncludeTrendsCheck) {
        $tmp2 = Join-Path $env:TEMP ('codex-playwright-mcp-trends-verify-' + $name + '.txt')
        if (Test-Path $tmp2) {
            Remove-Item -LiteralPath $tmp2 -Force
        }

        $prompt2 = @"
Use the MCP server named $name. Do not use web search.
Navigate to https://trends.google.com/ .
Wait for the page to settle, then report:
1. final page URL
2. page title
3. whether the page appears usable or is blocked/challenged
Keep the answer very short.
"@

        $trendsResult = Invoke-QuietCodexExec -Prompt $prompt2 -OutputPath $tmp2

        Write-Output ("--- VERIFY TRENDS " + $name + " START ---")
        Write-Output $trendsResult.Trim()
        Write-Output ("--- VERIFY TRENDS " + $name + " END ---")
    }
}
