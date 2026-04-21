@echo off
setlocal

set PROJECT_DIR=%CD%
set LOG_DIR=%PROJECT_DIR%\log

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

if "%KAFKA_HOME%"=="" (
    echo [ERROR] KAFKA_HOME is not set.
    exit /b 1
)

if not exist "%KAFKA_HOME%\bin\windows\kafka-server-start.bat" (
    echo [ERROR] kafka-server-start.bat not found under KAFKA_HOME.
    exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=py -3
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set PYTHON_CMD=python
    ) else (
        echo [ERROR] Python runtime not found.
        exit /b 1
    )
)

echo Starting Kafka server in background...
start "KAFKA_SERVER_BLOCKCHAIN_MPC" cmd /c ""%KAFKA_HOME%\bin\windows\kafka-server-start.bat" "%KAFKA_HOME%\config\server.properties" ^> "%LOG_DIR%\kafka.log" 2^>^&1"
echo Kafka start command submitted.

echo Starting proposals vectorize-and-store module in background...
start "PROPOSALS_VECTORIZED_STORE_BLOCKCHAIN_MPC" cmd /c "cd /d ""%PROJECT_DIR%"" && %PYTHON_CMD% -m app.modules.propasals_vectorized_and_store ^> ""%LOG_DIR%\proposals_vectorized_and_store.log"" 2^>^&1"
echo Module start command submitted.

echo Done. Logs: "%LOG_DIR%"
endlocal
