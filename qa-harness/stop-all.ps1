$ports = 9090, 3100, 3000, 8002, 5174

$conns = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in $ports }

if (-not $conns) {
    Write-Host 'Nothing to stop (no listeners on harness ports).' -ForegroundColor DarkGray
    exit 0
}

foreach ($conn in $conns) {
    try {
        $process = Get-Process -Id $conn.OwningProcess -ErrorAction Stop
        Write-Host ("  killing port {0} (PID {1} - {2})" -f $conn.LocalPort, $conn.OwningProcess, $process.Name)
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host ("  port {0}: PID {1} already gone" -f $conn.LocalPort, $conn.OwningProcess) -ForegroundColor DarkGray
    }
}

Start-Sleep -Seconds 1

$still = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in $ports }

if ($still) {
    Write-Host 'Some still listening:' -ForegroundColor Red
    $still | Format-Table LocalPort, OwningProcess
    exit 1
}

Write-Host 'All harness ports freed.' -ForegroundColor Green
exit 0
