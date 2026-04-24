param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Output "[info]: $Message"
}

function Get-CdpPort {
    if ($env:TRENDS_CDP_PORT -and ($env:TRENDS_CDP_PORT -as [int])) {
        return [int]$env:TRENDS_CDP_PORT
    }

    return 9225
}

function Test-CdpReady {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/json/version" -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        return [bool]$listener
    }
}

function Get-BrowserCandidates {
    $paths = @()

    if ($env:TRENDS_CDP_BROWSER) {
        $paths += $env:TRENDS_CDP_BROWSER
    }

    $paths += @(
        (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:LocalAppData 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'),
        (Join-Path $env:LocalAppData 'Google\Chrome\Application\chrome.exe')
    )

    return $paths |
        Where-Object { $_ -and (Test-Path $_) } |
        Select-Object -Unique
}

function Ensure-LocalCdpSession {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    if ($env:TRENDS_SKIP_CDP_BOOTSTRAP -eq "1") {
        Write-Info "Skipping local CDP bootstrap because TRENDS_SKIP_CDP_BOOTSTRAP=1."
        return
    }

    if (Test-CdpReady -Port $Port) {
        return
    }

    $browserCandidates = Get-BrowserCandidates
    if (-not $browserCandidates) {
        throw "No supported Edge/Chrome executable was found. Install Microsoft Edge or Google Chrome, or start a CDP session manually on 127.0.0.1:$Port."
    }

    $baseDir = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { $env:TEMP }
    $profileDir = Join-Path $baseDir 'Codex\google-trends-feishu-monitor\cdp-profile'
    New-Item -ItemType Directory -Force -Path $profileDir | Out-Null

    $browserArgs = @(
        "--remote-debugging-port=$Port",
        "--user-data-dir=$profileDir",
        "--no-first-run",
        "--no-default-browser-check",
        "about:blank"
    )

    foreach ($browserPath in $browserCandidates) {
        Write-Info "CDP port $Port is not listening; trying local browser bootstrap via $browserPath"
        try {
            Start-Process -FilePath $browserPath -ArgumentList $browserArgs -WindowStyle Minimized | Out-Null
        } catch {
            Write-Info ("Browser launch failed for {0}: {1}" -f $browserPath, $_.Exception.Message)
            continue
        }

        $deadline = (Get-Date).AddSeconds(15)
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 500
            if (Test-CdpReady -Port $Port) {
                Write-Info "Local CDP session is ready on 127.0.0.1:$Port."
                return
            }
        }

        Write-Info "Browser launched but CDP endpoint 127.0.0.1:$Port did not become ready in time."
    }

    throw "Unable to start a local CDP browser session on 127.0.0.1:$Port. Fix the local browser environment or launch Edge/Chrome manually with --remote-debugging-port=$Port."
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is required but was not found in PATH."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm is required but was not found in PATH."
}

$skillRoot = Split-Path -Parent $PSScriptRoot
$playwrightModule = Join-Path $skillRoot "node_modules\playwright-core"
$cdpPort = Get-CdpPort

if (-not (Test-Path $playwrightModule)) {
    Push-Location $skillRoot
    try {
        & npm install --no-fund --no-audit
    } finally {
        Pop-Location
    }
}

Ensure-LocalCdpSession -Port $cdpPort

& node (Join-Path $PSScriptRoot "trends_cdp_collect.mjs") @Arguments
