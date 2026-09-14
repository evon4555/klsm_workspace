<#
.SYNOPSIS
    Set qa-harness workspace environment variables for the current PowerShell session.

.DESCRIPTION
    This script does not persist machine/user environment variables. It only
    prepares the current shell so tools resolve the clean workspace view.
#>

$env:QA_WORKSPACE_ROOT = "D:\Workspace"
$env:QA_HARNESS_ROOT = "D:\Workspace\qa-harness"
$env:QA_STANDARD_PRODUCT_ROOT = "D:\Workspace\standard product"
$env:QA_WESTK_ROOT = "D:\Workspace\west-kowloon"
$env:QA_JOCKEY_CLUB_ROOT = "D:\Workspace\jockey club"

Write-Host "QA_WORKSPACE_ROOT=$env:QA_WORKSPACE_ROOT"
Write-Host "QA_HARNESS_ROOT=$env:QA_HARNESS_ROOT"
Write-Host "QA_STANDARD_PRODUCT_ROOT=$env:QA_STANDARD_PRODUCT_ROOT"
Write-Host "QA_WESTK_ROOT=$env:QA_WESTK_ROOT"
Write-Host "QA_JOCKEY_CLUB_ROOT=$env:QA_JOCKEY_CLUB_ROOT"
