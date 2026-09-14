@echo off
REM Starts Grafana natively on Windows.
REM Double-click this file, or run: infra\start-grafana.bat
REM Stop with Ctrl+C in this window.

setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "REPO=%%~fI"
if defined QA_HARNESS_ROOT set "REPO=%QA_HARNESS_ROOT%"
set "INFRA_DIR=%REPO%\02-platform\03-infra"
set "GRAFANA_DIR=%INFRA_DIR%\03-grafana"
set "GF_PATHS_PROVISIONING=%GRAFANA_DIR%\provisioning"
set "QA_GRAFANA_DASHBOARDS=%GRAFANA_DIR%\dashboards"

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
  echo Grafana already listening on :3000; skipping.
  exit /b 0
)

if not exist "%GF_PATHS_PROVISIONING%\alerting" mkdir "%GF_PATHS_PROVISIONING%\alerting"
if not exist "%GF_PATHS_PROVISIONING%\notifiers" mkdir "%GF_PATHS_PROVISIONING%\notifiers"
if not exist "%GF_PATHS_PROVISIONING%\plugins" mkdir "%GF_PATHS_PROVISIONING%\plugins"
if not exist "D:\grafana\grafana-v10.4.1\data\plugins" mkdir "D:\grafana\grafana-v10.4.1\data\plugins"

cd /d D:\grafana\grafana-v10.4.1
bin\grafana-server.exe ^
  --config="%GRAFANA_DIR%\grafana.windows.ini" ^
  --homepath=D:\grafana\grafana-v10.4.1

endlocal
