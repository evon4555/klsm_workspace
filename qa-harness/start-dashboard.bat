@echo off
REM Build the Vite frontend and serve it from the FastAPI process.
REM Use start-all.bat when Vite HMR and the full observability stack are needed.

setlocal
set "REPO=%~dp0"
set "REPO=%REPO:~0,-1%"
if defined QA_HARNESS_ROOT set "REPO=%QA_HARNESS_ROOT%"
for %%I in ("%REPO%") do set "REPO=%%~fI"
for %%I in ("%REPO%\..") do set "DEFAULT_WORKSPACE=%%~fI"

if not defined QA_WORKSPACE_ROOT set "QA_WORKSPACE_ROOT=%DEFAULT_WORKSPACE%"
if not defined QA_HARNESS_ROOT set "QA_HARNESS_ROOT=%REPO%"

set "AUTOMATION_DIR=%REPO%\02-platform\01-automation"
set "BACKEND_DIR=%REPO%\02-platform\02-dashboard\01-backend"
set "FRONTEND_DIR=%REPO%\02-platform\02-dashboard\02-frontend"
set "PYTHON_EXE=%AUTOMATION_DIR%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python venv missing at %AUTOMATION_DIR%\.venv.
    exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo ERROR: Frontend dependencies missing. Run npm install in %FRONTEND_DIR%.
    exit /b 1
)

if not exist "%FRONTEND_DIR%\dist\index.html" goto build_frontend
if /I "%QA_DASHBOARD_REBUILD%"=="1" goto build_frontend
goto start_backend

:build_frontend
pushd "%FRONTEND_DIR%"
call npm run build
if errorlevel 1 (
    popd
    exit /b 1
)
popd

:start_backend
echo QA Dashboard: http://127.0.0.1:8002
pushd "%BACKEND_DIR%"
"%PYTHON_EXE%" -m uvicorn main:app --host 127.0.0.1 --port 8002
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
