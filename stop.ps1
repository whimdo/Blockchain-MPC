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

    $pidText = (Get-Content -Path $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($null -eq $pidText) {
        Write-Host "$Name PID file empty, skip."
        Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
        return
    }
    $pidText = $pidText.ToString().Trim()
    if (-not $pidText) {
        Write-Host "$Name PID file empty, skip."
        Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
        return
    }

    $targetPid = 0
    if (-not [int]::TryParse($pidText, [ref]$targetPid)) {
        Write-Host "$Name PID invalid ($pidText), skip."
        Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
        return
    }

    $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
    if ($proc) {
        & taskkill /PID $targetPid /T /F | Out-Null
        Write-Host "$Name stopped. PID=$targetPid (process tree)"
    } else {
        Write-Host "$Name process already stopped. PID=$targetPid"
    }

    Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
}

Stop-FromPidFile -PidFile (Join-Path $PidDir "proposals_vectorized_and_store.pid") -Name "Module"
# Stop-FromPidFile -PidFile (Join-Path $PidDir "proposals_get_and_push.pid") -Name "Module"
Stop-FromPidFile -PidFile (Join-Path $PidDir "backend_api.pid") -Name "Backend"
Stop-FromPidFile -PidFile (Join-Path $PidDir "frontend_vite.pid") -Name "Frontend"

Write-Host "Done."
