@echo off
REM Starts Loki natively on Windows (replaces the WSL Docker container that
REM ran grafana/loki:2.9.6 prior to 2026-05-27).
REM
REM Double-click this file, or run: infra\start-loki.bat
REM Stop with Ctrl+C in this window.
REM
REM Data dir: D:\loki\data (outside the repo, like Prometheus).

setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "REPO=%%~fI"
if defined QA_HARNESS_ROOT set "REPO=%QA_HARNESS_ROOT%"
set "LOKI_CONFIG=%REPO%\02-platform\03-infra\02-loki\loki-config.yaml"

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 3100 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
  echo Loki already listening on :3100; skipping.
  exit /b 0
)

D:\loki\loki-windows-amd64.exe ^
  -config.file="%LOKI_CONFIG%"

endlocal
