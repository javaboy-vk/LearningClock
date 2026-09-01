[CmdletBinding()]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$SeqUrl = $(
        if ([string]::IsNullOrWhiteSpace($env:SEQ_URL)) {
            "http://localhost:5341"
        }
        else {
            $env:SEQ_URL
        }
    ),

    [Parameter()]
    [string]$ApiKey = $(
        if (-not [string]::IsNullOrWhiteSpace($env:SEQ_ADMIN_API_KEY)) {
            $env:SEQ_ADMIN_API_KEY
        }
        else {
            $env:SEQ_API_KEY
        }
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$dashboardFile = Join-Path $PSScriptRoot "dashboard-LearningClock.template"
$signalFile = Join-Path $PSScriptRoot "signal-LearningClock - All Events.template"
$queryFile = Join-Path $PSScriptRoot "sqlquery-LearningClock Events - Log Format.template"
$workspaceFile = Join-Path $PSScriptRoot "workspace-LearningClock.template"
$stateFile = Join-Path $PSScriptRoot "import.state"

foreach ($templateFile in @($dashboardFile, $signalFile, $queryFile, $workspaceFile)) {
    if (-not (Test-Path -LiteralPath $templateFile -PathType Leaf)) {
        throw "The LearningClock Seq template was not found: $templateFile"
    }
}

$seqCli = Get-Command "seqcli" -ErrorAction SilentlyContinue
if ($null -eq $seqCli) {
    throw "seqcli was not found on PATH. Install Seq/seqcli, reopen PowerShell, and run this command again."
}

$seqArguments = @(
    "template"
    "import"
    "--input", $PSScriptRoot
    "--state", $stateFile
    "--server", $SeqUrl.TrimEnd("/")
    "--merge"
)

if (-not [string]::IsNullOrWhiteSpace($ApiKey)) {
    $seqArguments += @("--apikey", $ApiKey)
}

Write-Output "Installing the LearningClock Seq workspace into $($SeqUrl.TrimEnd('/'))..."
& $seqCli.Source @seqArguments

if ($LASTEXITCODE -ne 0) {
    throw "LearningClock Seq workspace installation failed with exit code $LASTEXITCODE."
}

Write-Output "LearningClock Seq workspace installed successfully."
Write-Output "Select the LearningClock workspace in Seq and enable Tail in Events."
Write-Output "Open dashboards: $($SeqUrl.TrimEnd('/'))/#/dashboards"

