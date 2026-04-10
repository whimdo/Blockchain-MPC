@echo off

set PROJECT_DIR=%CD%


if not exist "%PROJECT_DIR%\log" mkdir "%PROJECT_DIR%\log"

echo %KAFKA_HOME%
echo Starting Kafka server...
"%KAFKA_HOME%\bin\windows\kafka-server-start.bat" "%KAFKA_HOME%\config\server.properties"
echo started.