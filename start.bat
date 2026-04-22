@echo off
setlocal

set PROJECT_DIR=%~dp0
if "%PROJECT_DIR:~-1%"=="\" set PROJECT_DIR=%PROJECT_DIR:~0,-1%
set LOG_DIR=%PROJECT_DIR%\log

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

if defined VIRTUAL_ENV (
    if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
        set PYTHON_CMD="%VIRTUAL_ENV%\Scripts\python.exe"
    )
)

if not defined PYTHON_CMD (
    if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
        set PYTHON_CMD="%PROJECT_DIR%\.venv\Scripts\python.exe"
    )
)

if not defined PYTHON_CMD (
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
)

echo Using Python: %PYTHON_CMD%

echo Starting proposals vectorize-and-store module in background...
start "PROPOSALS_VECTORIZED_STORE_BLOCKCHAIN_MPC" cmd /c "cd /d ""%PROJECT_DIR%"" && %PYTHON_CMD% -m app.modules.proposals_vectorized_and_store ^> ""%LOG_DIR%\proposals_vectorized_and_store.log"" 2^>^&1"
echo Module start command submitted.

echo Starting proposals get-and-push module in background...
start "PROPOSALS_GET_AND_PUSH_BLOCKCHAIN_MPC" cmd /c "cd /d ""%PROJECT_DIR%"" && %PYTHON_CMD% -m app.modules.proposals_get_and_push ^> ""%LOG_DIR%\proposals_get_and_push.log"" 2^>^&1"
echo Module start command submitted.

echo Done. Logs: "%LOG_DIR%"
endlocal
