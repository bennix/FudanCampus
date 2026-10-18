@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在生成彩色 GLB 并打开 Blender 预览（3=蓝 5=橙 7=绿）...
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\generate_north_modules.ps1"
if errorlevel 1 exit /b 1
echo.
echo 正在打开 Blender...
start "" "D:\blender\blender.exe" --python "%~dp0scripts\preview_north_buildings.py"
echo 已启动。也可在 Blender 中打开 output\preview_north_3_5_7.blend
pause
