@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title Campus Scene

set "PROJECT_DIR=%~dp0"
set "WEB_DIR=%PROJECT_DIR%web"
set "OUTPUT_DIR=%PROJECT_DIR%output"
set "LOG_FILE=%OUTPUT_DIR%\local-server.log"

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

where npm >nul 2>&1 || goto no_npm
if not exist "%WEB_DIR%\package.json" goto no_package
if not exist "%WEB_DIR%\node_modules" goto no_modules
if not exist "%WEB_DIR%\public\campus.glb" goto no_model

cd /d "%WEB_DIR%"

for /L %%P in (5173,1,5183) do (
  set "PORT=%%P"
  set "URL=http://localhost:%%P/"
  curl.exe -fsS -o nul --max-time 3 "!URL!" >nul 2>&1
  if not errorlevel 1 (
    echo Campus page is already running: !URL!
    start "" "!URL!"
    exit /b 0
  )
  netstat -ano -p TCP | findstr /R /C:":%%P .*LISTENING" >nul
  if errorlevel 1 goto port_found
)

goto ports_busy

:port_found
echo Starting campus page. First startup may take up to 90 seconds.
echo Log: "%LOG_FILE%"
start "Campus local server" /min cmd /c "npm run dev -- --host localhost --port %PORT% 1^>^"%LOG_FILE%^" 2^>^&1"

for /L %%I in (1,1,90) do (
  curl.exe -fsS -o nul --max-time 2 "%URL%" >nul 2>&1
  if not errorlevel 1 (
    echo Campus page started: %URL%
    start "" "%URL%"
    exit /b 0
  )
  timeout /t 1 /nobreak >nul
)

call :fail "Startup timed out. Check the log file."
exit /b 1

:no_npm
call :fail "Node.js or npm was not found. Install Node.js, then retry."
exit /b 1

:no_package
call :fail "web\package.json was not found. Keep this file in the project root."
exit /b 1

:no_modules
call :fail "Dependencies are missing. Run npm install in the web folder first."
exit /b 1

:no_model
call :fail "web\public\campus.glb was not found."
exit /b 1

:ports_busy
call :fail "Ports 5173 through 5183 are all in use."
exit /b 1

:fail
echo.
echo Startup failed: %~1
echo Log: "%LOG_FILE%"
echo.
pause
exit /b 1
