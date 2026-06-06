# =============================================================================
# File Name : export-diavgeia-vault.ps1
# Artifact  : LearningClock - Diavgeia Vault Export
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Copies repo-local Diavgeia content into the local Diavgeia vault.
# =============================================================================

param(
    [string]$Destination = "D:\DiavgeiaVault\Engineering\LearningClock"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$source = Join-Path $repoRoot "diavgeia\LearningClock"

if (-not (Test-Path -LiteralPath $source)) {
    throw "Diavgeia source folder not found: $source"
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null
Copy-Item -Path (Join-Path $source "*") -Destination $Destination -Recurse -Force

$manifest = Join-Path $Destination "_LearningClock Export Manifest.md"
@(
    "# LearningClock Export Manifest",
    "",
    "- Source: $source",
    "- Destination: $Destination",
    "- Exported: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))"
) | Set-Content -Path $manifest -Encoding UTF8

Write-Host "Exported LearningClock Diavgeia content to $Destination"
