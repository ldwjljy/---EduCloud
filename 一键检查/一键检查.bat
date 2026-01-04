@echo off
chcp 65001 >nul
echo ========================================
echo   EduCloud 一键检查工具
echo ========================================
echo.

cd /d %~dp0\..

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 运行一键检查脚本
python "一键检查\一键检查.py"

pause
