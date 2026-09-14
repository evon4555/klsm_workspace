@echo off
REM Starts Prometheus natively on Windows (replaces the WSL Docker container
REM that ran prom/prometheus:v2.51.0 prior to 2026-05-27).
REM
REM Double-click this file, or run: infra\start-prometheus.bat
REM Stop with Ctrl+C in this window.
REM
REM Data dir: D:\prometheus\data (outside the repo, like Grafana).

setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "REPO=%%~fI"
if defined QA_HARNESS_ROOT set "REPO=%QA_HARNESS_ROOT%"
set "PROM_CONFIG=%REPO%\02-platform\03-infra\01-prometheus\prometheus.yml"

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 9090 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
  echo Prometheus already listening on :9090; skipping.
  exit /b 0
)

D:\prometheus\prometheus-2.51.0.windows-amd64\prometheus.exe ^
  --config.file="%PROM_CONFIG%" ^
  --storage.tsdb.path=D:\prometheus\data ^
  --storage.tsdb.retention.time=7d ^
  --web.enable-lifecycle ^
  --web.listen-address=0.0.0.0:9090

endlocal
