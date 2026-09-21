@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title 校园场景复原

set "PROJECT_DIR=%~dp0"
set "WEB_DIR=%PROJECT_DIR%web"
set "OUTPUT_DIR=%PROJECT_DIR%output"
set "LOG_FILE=%OUTPUT_DIR%\local-server.log"

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

where npm >nul 2>&1 || goto :no_npm
if not exist "%WEB_DIR%\package.json" goto :no_package
if not exist "%WEB_DIR%\node_modules" goto :no_modules
if not exist "%WEB_DIR%\public\campus.glb" goto :no_model

cd /d "%WEB_DIR%"

for /L %%P in (5173,1,5183) do (
    set "PORT=%%P"
    set "URL=http://localhost:%%P/"

    curl.exe -fsS --max-time 3 "!URL!" 2>nul | findstr /C:"校园空间重现" >nul
    if not errorlevel 1 (
        echo 校园网页已经运行，正在打开 !URL!
        start "" "!URL!"
        exit /b 0
    )

    netstat -ano -p TCP | findstr /R /C:":%%P .*LISTENING" >nul
    if errorlevel 1 goto :port_found
)

goto :ports_busy

:port_found
echo 正在启动校园网页，首次加载可能需要约半分钟……
echo 日志文件：%LOG_FILE%
start "校园场景本地服务" /min cmd /c "npm run dev -- --host 127.0.0.1 --port %PORT% 1^>^"%LOG_FILE%^" 2^>^&1"

for /L %%I in (1,1,90) do (
    curl.exe -fsS --max-time 2 "%URL%" 2>nul | findstr /C:"校园空间重现" >nul
    if not errorlevel 1 (
        echo 校园网页已启动：%URL%
        start "" "%URL%"
        timeout /t 2 /nobreak >nul
        exit /b 0
    )
    timeout /t 1 /nobreak >nul
)

call :fail "等待服务超时，请查看日志。"
exit /b 1

:no_npm
call :fail "未找到 Node.js / npm。请先安装 Node.js，并重新打开此文件。"
exit /b 1

:no_package
call :fail "未找到 web\package.json。请把本文件放在项目根目录。"
exit /b 1

:no_modules
call :fail "缺少依赖。请先在 web 目录运行 npm install。"
exit /b 1

:no_model
call :fail "未找到 web\public\campus.glb。"
exit /b 1

:ports_busy
call :fail "5173–5183 端口均被占用。"
exit /b 1

:fail
echo.
echo 启动失败：%~1
echo 日志位置：%LOG_FILE%
echo.
pause
exit /b 1
