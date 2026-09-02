# =============================================================================
# File Name : Register-LauncherPad.ps1
# Artifact  : LearningClock - Current-User Start Menu Registration
# Author    : javaboy-vk
# Date      : 2026-09-01
# Version   : v1.0.0
# Purpose:
#   Creates or updates the current user's LearningClock LauncherPad shortcut and
#   requests a Start pin when the Windows shell exposes that supported action.
# =============================================================================

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TargetPath,

    [Parameter(Mandatory = $true)]
    [string]$ShortcutArguments,

    [Parameter(Mandatory = $true)]
    [string]$WorkingDirectory,

    [Parameter(Mandatory = $true)]
    [string]$IconPath,

    [switch]$PinToStart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedTarget = (Resolve-Path -LiteralPath $TargetPath).Path
$resolvedWorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory).Path
$resolvedIcon = (Resolve-Path -LiteralPath $IconPath).Path
$programsPath = [Environment]::GetFolderPath("Programs")
if ([string]::IsNullOrWhiteSpace($programsPath)) {
    throw "Windows did not return the current user's Start Menu Programs folder."
}

$shortcutName = "LearningClock LauncherPad.lnk"
$shortcutPath = Join-Path $programsPath $shortcutName
$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $resolvedTarget
$shortcut.Arguments = $ShortcutArguments
$shortcut.WorkingDirectory = $resolvedWorkingDirectory
$shortcut.IconLocation = "$resolvedIcon,0"
$shortcut.Description = "Open LearningClock LauncherPad"
$shortcut.WindowStyle = 1
$shortcut.Save()

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class LauncherPadShellRefresh
{
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(uint eventId, uint flags, IntPtr item1, IntPtr item2);
}
"@
[LauncherPadShellRefresh]::SHChangeNotify(0x08000000, 0x1000, [IntPtr]::Zero, [IntPtr]::Zero)
Write-Output "LauncherPad Start Menu shortcut registered: $shortcutPath"

if ($PinToStart) {
    try {
        $shellApplication = New-Object -ComObject Shell.Application
        $programsFolder = $shellApplication.Namespace($programsPath)
        $shortcutItem = $programsFolder.ParseName($shortcutName)
        if ($null -eq $shortcutItem) {
            Write-Warning "The Start entry is registered, but Windows has not indexed it for pinning yet. Pin LearningClock LauncherPad manually from Start."
        }
        else {
            $pinVerb = @($shortcutItem.Verbs()) | Where-Object {
                ($_.Name -replace "&", "").Trim() -eq "Pin to Start"
            } | Select-Object -First 1

            if ($null -ne $pinVerb) {
                $pinVerb.DoIt()
                Write-Output "Windows accepted the LauncherPad Pin to Start request."
            }
            else {
                Write-Warning "Windows does not expose automatic Start pinning. Open Start, find LearningClock LauncherPad, right-click it, and select Pin to Start."
            }
        }
    }
    catch {
        Write-Warning "The Start entry is registered, but the automatic pin request failed: $($_.Exception.Message). Pin LearningClock LauncherPad manually from Start."
    }
}
