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

if (-not $env:KAFKA_HOME) {
    throw "KAFKA_HOME is not set."
}

$kafkaScript = Join-Path $env:KAFKA_HOME "bin\windows\kafka-server-start.bat"
$kafkaConfig = Join-Path $env:KAFKA_HOME "config\server.properties"
if (-not (Test-Path $kafkaScript)) {
    throw "kafka-server-start.bat not found under KAFKA_HOME."
}

$pythonCmd = Get-Command py -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $pythonInvoke = 'py -3'
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python runtime not found."
    }
    $pythonInvoke = "python"
}

Write-Host "Starting Kafka server in background..."
$kafkaLog = Join-Path $LogDir "kafka.log"
$kafkaCmd = "`"$kafkaScript`" `"$kafkaConfig`" > `"$kafkaLog`" 2>&1"
$kafkaProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $kafkaCmd" -PassThru -WindowStyle Hidden
Set-Content -Path (Join-Path $PidDir "kafka.pid") -Value $kafkaProc.Id -Encoding ascii
Write-Host "Kafka started. PID=$($kafkaProc.Id)"

Write-Host "Starting proposals vectorize-and-store module in background..."
$moduleLog = Join-Path $LogDir "proposals_vectorized_and_store.log"
$moduleCmd = "cd /d `"$ProjectDir`" && $pythonInvoke -m app.modules.propasals_vectorized_and_store > `"$moduleLog`" 2>&1"
$moduleProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $moduleCmd" -PassThru -WindowStyle Hidden
Set-Content -Path (Join-Path $PidDir "proposals_vectorized_and_store.pid") -Value $moduleProc.Id -Encoding ascii
Write-Host "Module started. PID=$($moduleProc.Id)"

Write-Host "Done. Logs: $LogDir"
