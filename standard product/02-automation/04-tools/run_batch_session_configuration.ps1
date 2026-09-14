param(
    [string]$PythonExe = "D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$ProjectRoot = Resolve-Path (Join-Path $Root "..")
$HarnessSrc = "D:\Workspace\qa-harness\02-platform\01-automation\02-src"
$ProjectSrc = Join-Path $Root "03-src"
$FeatureRoot = Join-Path $Root "01-features"
$ArtifactDir = Join-Path $Root "07-artifacts\batch_session_configuration"
$RequirementPackage = "D:\Workspace\standard product\01-requirements\02-subprojects\01-domestic projects\02-modules\04-Configuration Related\2026-07-15"
$ExportTool = "D:\Workspace\qa-harness\01-system\03-tools\export_execution_results.py"

New-Item -ItemType Directory -Force -Path $ArtifactDir | Out-Null

$env:ENV = if ($env:ENV) { $env:ENV } else { "sit" }
$env:TA_ENV = if ($env:TA_ENV) { $env:TA_ENV } else { "sit" }
$env:TA_ANTANK_URL = if ($env:TA_ANTANK_URL) { $env:TA_ANTANK_URL } else { "https://anticket.lengliwh.com" }
$env:TA_BASE_URL = if ($env:TA_BASE_URL) { $env:TA_BASE_URL } else { "https://anticket.lengliwh.com" }
$env:QA_PROJECT_AUTOMATION_ROOT = $Root
$env:QA_PROJECT_KEY = "standard product"
$env:QA_REQUIREMENT_PACKAGE = $RequirementPackage
$env:QA_DASHBOARD_API_BASE = "http://127.0.0.1:8002"
$env:PYTHONPATH = "$HarnessSrc;$ProjectSrc"

if (-not $env:TA_USER1_USERNAME) {
    $env:TA_USER1_USERNAME = "Mplus01"
}

if (-not $env:TA_USER1_PASSWORD) {
    $AccessRoot = "D:\Workspace\standard product\01-requirements\02-subprojects\01-domestic projects\01-source-documents"
    $AccessFile = Get-ChildItem -LiteralPath $AccessRoot -File -ErrorAction SilentlyContinue |
        Where-Object {
            $Content = Get-Content -Raw -LiteralPath $_.FullName -ErrorAction SilentlyContinue
            $Content -match 'Mplus01\s*/'
        } |
        Select-Object -First 1
    if ($AccessFile) {
        $Access = Get-Content -Raw -LiteralPath $AccessFile.FullName
        $Match = [regex]::Match($Access, 'Mplus01\s*/\s*([^\s]+)')
        if ($Match.Success) {
            $env:TA_USER1_PASSWORD = $Match.Groups[1].Value
        }
    }
}

Write-Host "[batch-session-configuration] Behave-first execution is required."
Write-Host "[batch-session-configuration] API steps must use real Python requests calls."
Write-Host "[batch-session-configuration] UI steps must use Playwright against the real application."
Write-Host "[batch-session-configuration] Mixed steps must use API setup/action plus final UI verification."

if (-not $env:TA_USER1_USERNAME -or -not $env:TA_USER1_PASSWORD) {
    Write-Error "Real Standard Product credentials are not configured. Set TA_USER1_USERNAME and TA_USER1_PASSWORD, or provide the local access file."
}

if ($env:TA_ALLOW_BATCH_MUTATION -ne "1") {
    Write-Error "This suite performs approved reversible batch writes. Set TA_ALLOW_BATCH_MUTATION=1 before execution."
}

if (-not (Get-ChildItem -Path $FeatureRoot -Filter "*.feature" -Recurse -ErrorAction SilentlyContinue)) {
    Write-Error "No runnable Behave .feature file exists yet. Real API endpoint mapping and real UI flow details are required before execution."
}

& $PythonExe -m behave $FeatureRoot --tags="@batch_session_configuration" --format json --outfile (Join-Path $ArtifactDir "latest-full-behave.json") --format pretty --no-capture
$BehaveExitCode = $LASTEXITCODE

$ExecutionRecord = Join-Path $ArtifactDir "latest-execution-record.json"
if (Test-Path -LiteralPath $ExecutionRecord) {
    $Record = Get-Content -Raw -LiteralPath $ExecutionRecord | ConvertFrom-Json
    if ($Record.dashboard_run_id) {
        $RunId = [int]$Record.dashboard_run_id
        & $PythonExe $ExportTool `
            --run-id $RunId `
            --package $RequirementPackage `
            --scope batch-session-configuration `
            --project "standard product" `
            --project-root $ProjectRoot `
            --artifact-scope batch_session_configuration `
            --manual-scope "None for current 13-case scope after SIT-TC-STD-CONFIG-002 and SIT-TC-STD-CONFIG-015 removal"
        if ($LASTEXITCODE -ne 0 -and $BehaveExitCode -eq 0) {
            exit $LASTEXITCODE
        }
    }
}

exit $BehaveExitCode
