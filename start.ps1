$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $ProjectDir "log"
$PidDir = Join-Path $LogDir "pids"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}
if (-not (Test-Path $PidDir)) {
    New-Item -ItemType Directory -Path $PidDir | Out-Null
}

$pythonInvoke = $null

if ($env:VIRTUAL_ENV) {
    $venvPython = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if (Test-Path $venvPython) {
        $pythonInvoke = "`"$venvPython`""
    }
}

if (-not $pythonInvoke) {
    $localVenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
    if (Test-Path $localVenvPython) {
        $pythonInvoke = "`"$localVenvPython`""
    }
}

if (-not $pythonInvoke) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonInvoke = "py -3"
    } else {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) {
            throw "Python runtime not found."
        }
        $pythonInvoke = "python"
    }
}

Write-Host "Using Python: $pythonInvoke"

Write-Host "Starting proposals vectorize-and-store module in background..."
$moduleLog = Join-Path $LogDir "proposals_vectorized_and_store.log"
$moduleCmd = "cd /d `"$ProjectDir`" && $pythonInvoke -m app.modules.proposals_vectorized_and_store > `"$moduleLog`" 2>&1"
$moduleProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $moduleCmd" -PassThru -WindowStyle Hidden
Set-Content -Path (Join-Path $PidDir "proposals_vectorized_and_store.pid") -Value $moduleProc.Id -Encoding ascii
Write-Host "Module started. PID=$($moduleProc.Id)"

# Write-Host "Starting proposals get-and-push module in background..."
# $module2Log = Join-Path $LogDir "proposals_get_and_push.log"
# $module2Cmd = "cd /d `"$ProjectDir`" && $pythonInvoke -m app.modules.proposals_get_and_push > `"$module2Log`" 2>&1"
# $module2Proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $module2Cmd" -PassThru -WindowStyle Hidden
# Set-Content -Path (Join-Path $PidDir "proposals_get_and_push.pid") -Value $module2Proc.Id -Encoding ascii
# Write-Host "Module started. PID=$($module2Proc.Id)"

Write-Host "Starting FastAPI backend in background..."
$backendLog = Join-Path $LogDir "backend_api.log"
$backendCmd = "cd /d `"$ProjectDir`" && $pythonInvoke -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload > `"$backendLog`" 2>&1"
$backendProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $backendCmd" -PassThru -WindowStyle Hidden
Set-Content -Path (Join-Path $PidDir "backend_api.pid") -Value $backendProc.Id -Encoding ascii
Write-Host "Backend started. PID=$($backendProc.Id) URL=http://127.0.0.1:8000"

$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
}

if ($npm) {
    Write-Host "Starting Vue frontend in background..."
    $frontendDir = Join-Path $ProjectDir "frontend"
    $frontendLog = Join-Path $LogDir "frontend_vite.log"
    $frontendCmd = "cd /d `"$frontendDir`" && npm run dev -- --host 127.0.0.1 --port 5173 > `"$frontendLog`" 2>&1"
    $frontendProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $frontendCmd" -PassThru -WindowStyle Hidden
    Set-Content -Path (Join-Path $PidDir "frontend_vite.pid") -Value $frontendProc.Id -Encoding ascii
    Write-Host "Frontend started. PID=$($frontendProc.Id) URL=http://127.0.0.1:5173"
} else {
    Write-Host "[WARN] npm not found. Frontend was not started."
}

Write-Host "Done. Logs: $LogDir"
