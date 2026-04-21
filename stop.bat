@echo off
setlocal

echo Stopping proposals vectorize-and-store module...
taskkill /FI "WINDOWTITLE eq PROPOSALS_VECTORIZED_STORE_BLOCKCHAIN_MPC" /T /F >nul 2>nul
if %errorlevel%==0 (
    echo Module stopped.
) else (
    echo Module process not found (or already stopped).
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
