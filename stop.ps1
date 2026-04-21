$ErrorActionPreference = "Continue"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidDir = Join-Path (Join-Path $ProjectDir "log") "pids"

function Stop-FromPidFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PidFile,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not (Test-Path $PidFile)) {
        Write-Host "$Name PID file not found, skip."
        return
    }

    $pidText = (Get-Content -Path $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    if (-not $pidText) {
        Write-Host "$Name PID file empty, skip."
        Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
        return
    }

    $pid = 0
    if (-not [int]::TryParse($pidText, [ref]$pid)) {
        Write-Host "$Name PID invalid ($pidText), skip."
        Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
        return
    }

    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($proc) {
        & taskkill /PID $pid /T /F | Out-Null
        Write-Host "$Name stopped. PID=$pid (process tree)"
    } else {
        Write-Host "$Name process already stopped. PID=$pid"
    }

    Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
}

Stop-FromPidFile -PidFile (Join-Path $PidDir "proposals_vectorized_and_store.pid") -Name "Module"
Stop-FromPidFile -PidFile (Join-Path $PidDir "kafka.pid") -Name "Kafka"

Write-Host "Done."
