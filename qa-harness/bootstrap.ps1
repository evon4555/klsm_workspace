<#
.SYNOPSIS
    Idempotent installer for qa-harness on a fresh Windows machine.

.DESCRIPTION
    Verifies prereqs (Python, Node), downloads + extracts the three
    observability binaries (Prometheus, Loki, Grafana) to fixed locations
    under D:\, creates the automation Python venv, installs all deps,
    installs the Playwright browser, and installs the dashboard frontend's
    npm packages.

    Re-runnable: every step skips work that's already done.

.PREREQUISITES
    - Windows 10/11 or Windows Server 2019+
    - PowerShell 5+ (default on Windows)
    - Repo root is detected from this script's location, or from
      QA_HARNESS_ROOT when set.
    - Python 3.10+ on PATH
    - Node.js 18+ on PATH
    - About 1.5 GB of free space on D:\

.EXAMPLE
    PS C:\path\to\qa-harness> .\bootstrap.ps1
#>

[CmdletBinding()]
param(
    [switch]$Force,             # Re-download binaries even if present
    [switch]$SkipBrowsers       # Skip playwright install chromium (~150 MB)
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # Speeds up Invoke-WebRequest a lot

# Wrap native-command calls so their stderr-bound warnings (pip's network
# retry chatter, etc.) don't trip PowerShell's "Stop" error preference.
# Returns the exit code; throws if non-zero.
function Invoke-Native($description, $exe, [string[]]$argv) {
    $cmdline = "& `"$exe`" " + ($argv -join " ")
    Write-Host "    $description" -ForegroundColor DarkGray
    & cmd.exe /c "`"$exe`" $($argv -join ' ') 2>&1" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "$description failed (exit $LASTEXITCODE). Command was: $exe $($argv -join ' ')"
    }
}

# --------------------------------------------------------------------------
# Resolve repo root. Default: directory containing this script. Override with
# QA_HARNESS_ROOT when running through a workspace view or wrapper.
# --------------------------------------------------------------------------
$scriptRoot = Split-Path -Parent $PSCommandPath
if ([string]::IsNullOrWhiteSpace($scriptRoot)) {
    $scriptRoot = (Get-Location).Path
}
$REPO = if ($env:QA_HARNESS_ROOT) {
    (Resolve-Path $env:QA_HARNESS_ROOT).Path
} else {
    (Resolve-Path $scriptRoot).Path
}
if ((Get-Location).Path -ne $REPO) {
    Write-Host "Switching cwd to $REPO" -ForegroundColor Yellow
    Set-Location $REPO
}
$AUTOMATION = Join-Path $REPO "02-platform\01-automation"
$DASHBOARD = Join-Path $REPO "02-platform\02-dashboard"
$FRONTEND = Join-Path $DASHBOARD "02-frontend"
if (-not (Test-Path "$AUTOMATION\pyproject.toml")) {
    throw "Not a qa-harness checkout: $AUTOMATION\pyproject.toml missing"
}

# Component install dirs (outside the repo by design)
$PROM_DIR    = "D:\prometheus"
$PROM_BINDIR = "$PROM_DIR\prometheus-2.51.0.windows-amd64"
$PROM_DATA   = "$PROM_DIR\data"

$LOKI_DIR  = "D:\loki"
$LOKI_EXE  = "$LOKI_DIR\loki-windows-amd64.exe"
$LOKI_DATA = "$LOKI_DIR\data"

$GRAF_DIR    = "D:\grafana"
$GRAF_BINDIR = "$GRAF_DIR\grafana-v10.4.1"

# Download URLs (pin to exact versions for reproducibility)
$PROM_URL = "https://github.com/prometheus/prometheus/releases/download/v2.51.0/prometheus-2.51.0.windows-amd64.zip"
$LOKI_URL = "https://github.com/grafana/loki/releases/download/v2.9.6/loki-windows-amd64.exe.zip"
$GRAF_URL = "https://dl.grafana.com/oss/release/grafana-10.4.1.windows-amd64.zip"

function Step($label) {
    Write-Host ""
    Write-Host "=== $label ===" -ForegroundColor Cyan
}

function Done($msg) {
    Write-Host "    $msg" -ForegroundColor Green
}

function Skip($msg) {
    Write-Host "    $msg" -ForegroundColor DarkGray
}

# --------------------------------------------------------------------------
Step "1. Verify prereqs"
# --------------------------------------------------------------------------
try {
    $pyVer = & python --version 2>&1
    if ($pyVer -notmatch "Python\s+3\.(1[0-9]|[2-9][0-9])") {
        throw "Python 3.10+ required; got: $pyVer"
    }
    Done "Python OK: $pyVer"
} catch {
    throw "Python not on PATH or too old. Install Python 3.10+ from https://www.python.org/downloads/windows/"
}

try {
    $nodeVer = & node --version 2>&1
    if ($nodeVer -notmatch "v(1[89]|[2-9][0-9])\.") {
        throw "Node 18+ required; got: $nodeVer"
    }
    Done "Node OK: $nodeVer"
} catch {
    throw "Node not on PATH or too old. Install Node 18+ from https://nodejs.org/"
}

# --------------------------------------------------------------------------
Step "2. Install Prometheus 2.51.0"
# --------------------------------------------------------------------------
if ((Test-Path "$PROM_BINDIR\prometheus.exe") -and (-not $Force)) {
    Skip "Already installed at $PROM_BINDIR"
} else {
    New-Item -ItemType Directory -Path $PROM_DIR -Force | Out-Null
    $zip = Join-Path $env:TEMP "prometheus-2.51.0.zip"
    Write-Host "    Downloading $PROM_URL ..."
    Invoke-WebRequest -Uri $PROM_URL -OutFile $zip -UseBasicParsing
    Write-Host "    Extracting to $PROM_DIR ..."
    Expand-Archive -Path $zip -DestinationPath $PROM_DIR -Force
    Remove-Item $zip
    Done "Installed: $PROM_BINDIR\prometheus.exe"
}
New-Item -ItemType Directory -Path $PROM_DATA -Force | Out-Null

# --------------------------------------------------------------------------
Step "3. Install Loki 2.9.6"
# --------------------------------------------------------------------------
if ((Test-Path $LOKI_EXE) -and (-not $Force)) {
    Skip "Already installed at $LOKI_EXE"
} else {
    New-Item -ItemType Directory -Path $LOKI_DIR -Force | Out-Null
    $zip = Join-Path $env:TEMP "loki-2.9.6.zip"
    Write-Host "    Downloading $LOKI_URL ..."
    Invoke-WebRequest -Uri $LOKI_URL -OutFile $zip -UseBasicParsing
    Write-Host "    Extracting to $LOKI_DIR ..."
    Expand-Archive -Path $zip -DestinationPath $LOKI_DIR -Force
    Remove-Item $zip
    Done "Installed: $LOKI_EXE"
}
New-Item -ItemType Directory -Path $LOKI_DATA -Force | Out-Null

# --------------------------------------------------------------------------
Step "4. Install Grafana 10.4.1"
# --------------------------------------------------------------------------
if ((Test-Path "$GRAF_BINDIR\bin\grafana-server.exe") -and (-not $Force)) {
    Skip "Already installed at $GRAF_BINDIR"
} else {
    New-Item -ItemType Directory -Path $GRAF_DIR -Force | Out-Null
    $zip = Join-Path $env:TEMP "grafana-10.4.1.zip"
    Write-Host "    Downloading $GRAF_URL ..."
    Invoke-WebRequest -Uri $GRAF_URL -OutFile $zip -UseBasicParsing
    Write-Host "    Extracting to $GRAF_DIR ..."
    Expand-Archive -Path $zip -DestinationPath $GRAF_DIR -Force
    Remove-Item $zip
    Done "Installed: $GRAF_BINDIR\bin\grafana-server.exe"
}

# --------------------------------------------------------------------------
Step "5. Create + populate Python venv"
# --------------------------------------------------------------------------
$VENV = "$AUTOMATION\.venv"
if ((Test-Path "$VENV\Scripts\python.exe") -and (-not $Force)) {
    Skip "venv already at $VENV"
} else {
    Write-Host "    Creating venv at $VENV ..."
    & python -m venv $VENV
    Done "venv created"
}

# Skip "pip install --upgrade pip" intentionally: it tends to hit PyPI hard
# and on flaky proxies trips the script. The base pip that ships with the
# venv is fine for installing our deps.
Invoke-Native "pip install -e .[web,dashboard] (1-3 min)" `
    "$VENV\Scripts\python.exe" `
    @("-m", "pip", "install", "-e", "$AUTOMATION[web,dashboard]", "--quiet", "--disable-pip-version-check")
Done "Python deps installed"

# --------------------------------------------------------------------------
Step "6. Install Playwright Chromium"
# --------------------------------------------------------------------------
if ($SkipBrowsers) {
    Skip "Skipped (--SkipBrowsers passed)"
} else {
    # Playwright stores its browser cache under %USERPROFILE%\AppData\Local\ms-playwright;
    # the install command is idempotent so always running it is fine.
    Invoke-Native "Installing chromium (~150 MB if missing)" `
        "$VENV\Scripts\python.exe" `
        @("-m", "playwright", "install", "chromium")
    Done "Chromium installed"
}

# --------------------------------------------------------------------------
Step "7. Install dashboard frontend npm packages"
# --------------------------------------------------------------------------
$NM = "$FRONTEND\node_modules"
if ((Test-Path $NM) -and (-not $Force)) {
    Skip "node_modules already at $NM"
} else {
    Push-Location $FRONTEND
    try {
        Write-Host "    Running npm install ..." -ForegroundColor DarkGray
        & cmd.exe /c "npm install --silent 2>&1" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "npm install failed (exit $LASTEXITCODE)" }
        Done "Frontend deps installed"
    } finally {
        Pop-Location
    }
}

# --------------------------------------------------------------------------
Step "Verify"
# --------------------------------------------------------------------------
& "$VENV\Scripts\python.exe" -c @"
import test_automation
print('    test_automation @', test_automation.__file__)
"@

# --------------------------------------------------------------------------
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host " Bootstrap complete." -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host " NEXT:" -ForegroundColor Green
Write-Host "   1. notepad ..\west-kowloon\02-automation\06-envs\.env.sit" -ForegroundColor Green
Write-Host "      Fill TA_WEBSITE_USERNAME and TA_WEBSITE_PASSWORD." -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "   2. .\start-all.bat" -ForegroundColor Green
Write-Host "      Five windows open (Prometheus/Loki/Grafana/Backend/Frontend)." -ForegroundColor Green
Write-Host "      Then open http://127.0.0.1:5174 in a browser." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
