@echo off
chcp 65001 >nul
echo ========================================
echo Django数据库完整备份工具
echo ========================================
echo.

cd /d %~dp0\..\..

python "工具\01-数据库工具\export_database_to_mysql.py" %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✓ 备份完成！
) else (
    echo.
    echo ✗ 备份失败，请检查错误信息
    pause
    exit /b %ERRORLEVEL%
)

pause
