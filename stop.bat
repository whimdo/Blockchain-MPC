@echo off
setlocal

echo Stopping proposals vectorize-and-store module...
taskkill /FI "WINDOWTITLE eq PROPOSALS_VECTORIZED_STORE_BLOCKCHAIN_MPC" /T /F >nul 2>nul
if %errorlevel%==0 (
    echo Vectorize-and-store module stopped.
) else (
    echo Vectorize-and-store module not found (or already stopped).
)

@REM echo Stopping proposals get-and-push module...
@REM taskkill /FI "WINDOWTITLE eq PROPOSALS_GET_AND_PUSH_BLOCKCHAIN_MPC" /T /F >nul 2>nul
@REM if %errorlevel%==0 (
@REM     echo Get-and-push module stopped.
@REM ) else (
@REM     echo Get-and-push module not found (or already stopped).
@REM )

echo Stopping FastAPI backend...
taskkill /FI "WINDOWTITLE eq BACKEND_API_BLOCKCHAIN_MPC" /T /F >nul 2>nul
if %errorlevel%==0 (
    echo Backend stopped.
) else (
    echo Backend process not found (or already stopped).
)

echo Stopping Vue frontend...
taskkill /FI "WINDOWTITLE eq FRONTEND_VITE_BLOCKCHAIN_MPC" /T /F >nul 2>nul
if %errorlevel%==0 (
    echo Frontend stopped.
) else (
    echo Frontend process not found (or already stopped).
)

echo Done.
endlocal
