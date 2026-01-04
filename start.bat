@echo off
chcp 65001 >nul
echo ========================================
echo   EduCloud 智能启动脚本
echo ========================================
echo.
echo 正在检查环境并启动服务器...
echo.

cd /d %~dp0

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 运行Python启动脚本
python start.py

pause
