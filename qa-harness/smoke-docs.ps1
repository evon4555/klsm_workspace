$env:QA_WORKSPACE_ROOT = "D:\Workspace"
# Workspace is now the primary qa-harness root.
$env:QA_HARNESS_ROOT = "D:\Workspace\qa-harness"
$env:QA_WESTK_ROOT = "D:\Workspace\west-kowloon"

$python = Join-Path $PSScriptRoot "02-platform\01-automation\.venv\Scripts\python.exe"
$smoke = Join-Path $PSScriptRoot "02-platform\01-automation\03-tools\smoke_docs.py"

& $python $smoke @args
exit $LASTEXITCODE
