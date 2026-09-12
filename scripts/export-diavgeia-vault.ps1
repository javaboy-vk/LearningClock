# =============================================================================
# File Name : export-diavgeia-vault.ps1
# Artifact  : LearningClock - Diavgeia Vault Export
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.2.0
# Purpose:
#   Copies LearningClock documentation under Engineering while placing the
#   single dashboard note at the Diavgeia vault root.
# =============================================================================

param(
    [string]$Destination = "D:\DiavgeiaVault\Engineering\LearningClock",
    [string]$DashboardDestination = "D:\DiavgeiaVault"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$source = Join-Path $repoRoot "diavgeia\LearningClock"

if (-not (Test-Path -LiteralPath $source)) {
    throw "Diavgeia source folder not found: $source"
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
New-Item -ItemType Directory -Force -Path $DashboardDestination | Out-Null

$dashboardName = "Learning-Clock-Dashboard.md"
Get-ChildItem -LiteralPath $source | Where-Object { $_.Name -ne $dashboardName } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Destination -Recurse -Force
}

$dashboardSource = Join-Path $source $dashboardName
$dashboardTarget = Join-Path $DashboardDestination $dashboardName
Copy-Item -LiteralPath $dashboardSource -Destination $dashboardTarget -Force

$oldDashboardTarget = Join-Path $Destination $dashboardName
if (
    (Test-Path -LiteralPath $oldDashboardTarget) -and
    ([IO.Path]::GetFullPath($oldDashboardTarget) -ne [IO.Path]::GetFullPath($dashboardTarget))
) {
    Remove-Item -LiteralPath $oldDashboardTarget -Force
}

$manifest = Join-Path $Destination "_LearningClock Export Manifest.md"
@(
    "# LearningClock Export Manifest",
    "",
    "- Source: $source",
    "- Destination: $Destination",
    "- Dashboard: $dashboardTarget",
    "- Exported: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))"
) | Set-Content -Path $manifest -Encoding UTF8

Write-Host "Exported LearningClock Diavgeia content to $Destination"
Write-Host "Exported LearningClock dashboard to $dashboardTarget"
