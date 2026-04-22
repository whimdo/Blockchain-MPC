@echo off
setlocal

echo Stopping proposals vectorize-and-store module...
taskkill /FI "WINDOWTITLE eq PROPOSALS_VECTORIZED_STORE_BLOCKCHAIN_MPC" /T /F >nul 2>nul
if %errorlevel%==0 (
    echo Vectorize-and-store module stopped.
) else (
    echo Vectorize-and-store module not found (or already stopped).
)

echo Stopping proposals get-and-push module...
taskkill /FI "WINDOWTITLE eq PROPOSALS_GET_AND_PUSH_BLOCKCHAIN_MPC" /T /F >nul 2>nul
if %errorlevel%==0 (
    echo Get-and-push module stopped.
) else (
    echo Get-and-push module not found (or already stopped).
)

echo Stopping Kafka server...
taskkill /FI "WINDOWTITLE eq KAFKA_SERVER_BLOCKCHAIN_MPC" /T /F >nul 2>nul
if %errorlevel%==0 (
    echo Kafka stopped.
) else (
    echo Kafka process not found (or already stopped).
)

echo Done.
endlocal
