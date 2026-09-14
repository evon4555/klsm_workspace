$env:QA_WORKSPACE_ROOT = "D:\Workspace"
# Workspace is now the primary qa-harness root.
$env:QA_HARNESS_ROOT = "D:\Workspace\qa-harness"
$env:QA_WESTK_ROOT = "D:\Workspace\west-kowloon"

$python = Join-Path $PSScriptRoot "02-platform\01-automation\.venv\Scripts\python.exe"
$gate = Join-Path $PSScriptRoot "01-system\03-tools\gate.py"

& $python $gate @args
exit $LASTEXITCODE
