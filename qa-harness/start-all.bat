@echo off
REM ---------------------------------------------------------------------------
REM start-all.bat - launch the development/HMR dashboard stack in 5 windows.
REM
REM Each service opens its own console so you can see its log and Ctrl+C it
REM individually. To shut everything down cleanly, run stop-all.bat.
REM
REM Repo root is detected from this script location. Override with
REM QA_HARNESS_ROOT when running through a workspace wrapper.
REM ---------------------------------------------------------------------------

setlocal

set "REPO=%~dp0"
set "REPO=%REPO:~0,-1%"
if defined QA_HARNESS_ROOT set "REPO=%QA_HARNESS_ROOT%"
for %%I in ("%REPO%") do set "REPO=%%~fI"
for %%I in ("%REPO%\..") do set "DEFAULT_WORKSPACE=%%~fI"

if not defined QA_WORKSPACE_ROOT set "QA_WORKSPACE_ROOT=%DEFAULT_WORKSPACE%"
if not defined QA_HARNESS_ROOT set "QA_HARNESS_ROOT=%REPO%"
if not defined QA_WESTK_ROOT set "QA_WESTK_ROOT=%QA_WORKSPACE_ROOT%\west-kowloon"

set "AUTOMATION_DIR=%REPO%\02-platform\01-automation"
set "DASHBOARD_DIR=%REPO%\02-platform\02-dashboard"
set "BACKEND_DIR=%DASHBOARD_DIR%\01-backend"
set "FRONTEND_DIR=%DASHBOARD_DIR%\02-frontend"
set "INFRA_DIR=%REPO%\02-platform\03-infra"
set "PYTHON_EXE=%AUTOMATION_DIR%\.venv\Scripts\python.exe"

if not exist "%AUTOMATION_DIR%\pyproject.toml" (
    echo ERROR: %AUTOMATION_DIR%\pyproject.toml missing.
    echo Set QA_HARNESS_ROOT to the qa-harness repo root, or run this script from the repo root.
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python venv missing at %AUTOMATION_DIR%\.venv.
    echo Run .\bootstrap.ps1 first.
    exit /b 1
)

echo Starting Prometheus...
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 9090 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo Prometheus already listening on :9090; skipping.
) else (
    start "qa-harness Prometheus" cmd /k ""%INFRA_DIR%\start-prometheus.bat""
)

echo Starting Loki...
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 3100 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo Loki already listening on :3100; skipping.
) else (
    start "qa-harness Loki" cmd /k ""%INFRA_DIR%\start-loki.bat""
)

echo Starting Grafana...
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo Grafana already listening on :3000; skipping.
) else (
    start "qa-harness Grafana" cmd /k ""%INFRA_DIR%\start-grafana.bat""
)

echo Starting Backend on :8002...
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo Backend already listening on :8002; skipping.
) else (
    start "qa-harness Backend" /D "%BACKEND_DIR%" cmd /k ""%PYTHON_EXE%" -m uvicorn main:app --host 127.0.0.1 --port 8002"
)

echo Starting Frontend on :5174...
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 5174 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 (
    echo Frontend already listening on :5174; skipping.
) else (
    start "qa-harness Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev -- --host 127.0.0.1 --force"
)

echo.
echo Services are available. If any service was newly launched, give it ~10 seconds, then open:
echo.
echo     http://127.0.0.1:5174
echo.
echo To stop everything: run stop-all.bat from this dir.
echo For a built single-process dashboard without Vite HMR: start-dashboard.bat

endlocal
