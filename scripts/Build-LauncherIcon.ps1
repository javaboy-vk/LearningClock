# =============================================================================
# File Name : Build-LauncherIcon.ps1
# Artifact  : LearningClock - Multi-Resolution Windows Icon Builder
# Author    : javaboy-vk
# Date      : 2026-09-01
# Version   : v1.0.1
# Purpose:
#   Resizes the high-contrast LauncherPad source artwork into PNG-compressed ICO
#   frames so Windows can choose a sharp native size instead of shrinking one image.
# =============================================================================

[CmdletBinding()]
param(
    [string]$SourcePath = "launcher\Learning-Clock-source.png",
    [string]$OutputPath = "launcher\Learning-Clock.ico",
    [string]$PackageOutputPath = "src\learningclock\assets\Learning-Clock.ico"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$resolvedSource = (Resolve-Path -LiteralPath $SourcePath).Path
$resolvedOutput = [IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputPath))
$outputDirectory = Split-Path -Parent $resolvedOutput
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    [IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
}

$source = [System.Drawing.Bitmap]::new($resolvedSource)
if ($source.Width -ne $source.Height) {
    $source.Dispose()
    throw "Launcher icon source must be square: $resolvedSource"
}

$sizes = @(16, 20, 24, 32, 40, 48, 64, 96, 128, 256)
$frames = @()
try {
    foreach ($size in $sizes) {
        $bitmap = [System.Drawing.Bitmap]::new(
            $size,
            $size,
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $stream = [IO.MemoryStream]::new()
        try {
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
            $graphics.Clear([System.Drawing.Color]::Transparent)
            $graphics.DrawImage($source, 0, 0, $size, $size)
            $bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
            $frames += [pscustomobject]@{
                Size = $size
                Bytes = $stream.ToArray()
            }
        }
        finally {
            $stream.Dispose()
            $graphics.Dispose()
            $bitmap.Dispose()
        }
    }
}
finally {
    $source.Dispose()
}

$file = [IO.File]::Open($resolvedOutput, [IO.FileMode]::Create, [IO.FileAccess]::Write)
$writer = [IO.BinaryWriter]::new($file)
try {
    $writer.Write([uint16]0)
    $writer.Write([uint16]1)
    $writer.Write([uint16]$frames.Count)

    $offset = 6 + (16 * $frames.Count)
    foreach ($frame in $frames) {
        $dimension = if ($frame.Size -eq 256) { 0 } else { $frame.Size }
        $writer.Write([byte]$dimension)
        $writer.Write([byte]$dimension)
        $writer.Write([byte]0)
        $writer.Write([byte]0)
        $writer.Write([uint16]1)
        $writer.Write([uint16]32)
        $writer.Write([uint32]$frame.Bytes.Length)
        $writer.Write([uint32]$offset)
        $offset += $frame.Bytes.Length
    }

    foreach ($frame in $frames) {
        $writer.Write([byte[]]$frame.Bytes)
    }
}
finally {
    $writer.Dispose()
    $file.Dispose()
}

Write-Output "Built LauncherPad icon: $resolvedOutput"
Write-Output "Included sizes: $($sizes -join ', ')"

$resolvedPackageOutput = [IO.Path]::GetFullPath((Join-Path (Get-Location) $PackageOutputPath))
$packageOutputDirectory = Split-Path -Parent $resolvedPackageOutput
if (-not (Test-Path -LiteralPath $packageOutputDirectory)) {
    [IO.Directory]::CreateDirectory($packageOutputDirectory) | Out-Null
}
[IO.File]::Copy($resolvedOutput, $resolvedPackageOutput, $true)
Write-Output "Synchronized packaged window icon: $resolvedPackageOutput"
