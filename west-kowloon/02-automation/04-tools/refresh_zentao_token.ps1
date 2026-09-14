param(
    [string]$ZenTaoBase = "https://lengliwh.chandao.net",
    [string]$BackendRoot = "D:\Workspace\qa-harness\02-platform\02-dashboard\01-backend",
    [string]$PythonExe = "D:\Workspace\qa-harness\02-platform\01-automation\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "ZenTao API token refresh" -ForegroundColor Cyan
Write-Host "Your password/token will not be printed. Do not paste it into chat." -ForegroundColor Yellow
Write-Host ""

$account = Read-Host "ZenTao account"
$securePassword = Read-Host "ZenTao password" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $password = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

$tokenUri = "$ZenTaoBase/api.php/v1/tokens"
$body = @{
    account = $account
    password = $password
} | ConvertTo-Json

Write-Host ""
Write-Host "Requesting token from $tokenUri ..."

try {
    $resp = Invoke-RestMethod -Method Post -Uri $tokenUri -ContentType "application/json" -Body $body
} catch {
    Write-Host "Token request failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "If your account uses SSO/QR login only, ask the ZenTao admin for an API-capable account or token."
    Read-Host "Press Enter to close"
    exit 1
}

if (-not $resp.token) {
    Write-Host "ZenTao response did not include token." -ForegroundColor Red
    $resp | ConvertTo-Json -Depth 5
    Read-Host "Press Enter to close"
    exit 1
}

[Environment]::SetEnvironmentVariable("ZENTAO_API_V2_TOKEN", $resp.token, "User")
$env:ZENTAO_API_V2_TOKEN = $resp.token
Write-Host "Saved ZENTAO_API_V2_TOKEN to Windows User environment." -ForegroundColor Green

Write-Host ""
Write-Host "Validating product API ..."
$productsUri = "$ZenTaoBase/api.php/v1/products?limit=1"
try {
    $products = Invoke-RestMethod -Method Get -Uri $productsUri -Headers @{ Token = $resp.token }
    $count = if ($products.products) { $products.products.Count } elseif ($products.data) { $products.data.Count } else { 0 }
    Write-Host "ZenTao product API OK. Sample count: $count" -ForegroundColor Green
} catch {
    Write-Host "Token was saved, but product API validation failed:" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "Restarting dashboard backend on 8002 ..."
$listeners = @(Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess)
$toStop = @()
foreach ($processId in $listeners) {
    $toStop += $processId
    try {
        $parent = (Get-CimInstance Win32_Process -Filter "ProcessId=$processId").ParentProcessId
        if ($parent) { $toStop += $parent }
    } catch {}
}
$toStop | Sort-Object -Unique | ForEach-Object {
    try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {}
}

Start-Sleep -Seconds 2
Start-Process -FilePath $PythonExe `
    -ArgumentList @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8002") `
    -WorkingDirectory $BackendRoot `
    -RedirectStandardOutput (Join-Path $BackendRoot "dashboard-backend.out.log") `
    -RedirectStandardError (Join-Path $BackendRoot "dashboard-backend.err.log") `
    -WindowStyle Hidden

Start-Sleep -Seconds 4
try {
    $dashboardProducts = Invoke-RestMethod "http://127.0.0.1:8002/api/zentao/products"
    Write-Host "Dashboard products: $($dashboardProducts.products.Count)" -ForegroundColor Green
    if ($dashboardProducts.error) {
        Write-Host "Dashboard warning: $($dashboardProducts.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Dashboard validation failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "Done. Refresh the ZenTao Integration page." -ForegroundColor Green
Read-Host "Press Enter to close"
