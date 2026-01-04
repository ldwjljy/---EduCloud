@echo off
chcp 65001 >nul
echo ========================================
echo   EduCloud 一键部署脚本 (Windows)
echo ========================================
echo.

cd /d %~dp0

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo ✅ Python已安装
python --version

echo.
echo ========================================
echo 步骤 1: 检查环境配置
echo ========================================

REM 检查.env文件
if not exist .env (
    echo ⚠️  .env文件不存在
    if exist .env.example (
        echo 📝 正在从.env.example创建.env文件...
        copy .env.example .env >nul
        echo ✅ .env文件已创建
        echo ⚠️  请务必编辑.env文件，配置数据库等信息！
        pause
    ) else (
        echo ❌ 错误: 未找到.env.example模板文件
        pause
        exit /b 1
    )
) else (
    echo ✅ .env文件已存在
)

echo.
echo ========================================
echo 步骤 2: 安装/更新Python依赖
echo ========================================
echo 正在升级pip...
python -m pip install --upgrade pip --quiet

echo 正在安装依赖包...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖安装完成

echo.
echo ========================================
echo 步骤 3: 数据库检查
echo ========================================
echo ⚠️  请确保:
echo    1. MySQL服务已启动
echo    2. 数据库已创建（默认名称: educloud）
echo    3. .env文件中的数据库配置正确
echo.
set /p db_ready="是否已完成数据库配置？(Y/N): "
if /i not "%db_ready%"=="Y" (
    echo 请先配置数据库后再运行此脚本
    pause
    exit /b 0
)

echo.
echo ========================================
echo 步骤 4: 运行数据库迁移
echo ========================================
python manage.py migrate
if errorlevel 1 (
    echo ❌ 数据库迁移失败，请检查数据库配置
    pause
    exit /b 1
)
echo ✅ 数据库迁移完成

echo.
echo ========================================
echo 步骤 5: 收集静态文件
echo ========================================
python manage.py collectstatic --noinput
if errorlevel 1 (
    echo ⚠️  静态文件收集失败，但可以继续
) else (
    echo ✅ 静态文件收集完成
)

echo.
echo ========================================
echo 步骤 6: 创建超级管理员（可选）
echo ========================================
set /p create_admin="是否创建超级管理员账户？(Y/N): "
if /i "%create_admin%"=="Y" (
    python manage.py createsuperuser
)

echo.
echo ========================================
echo ✅ 部署完成！
echo ========================================
echo.
echo 下一步操作:
echo   1. 检查.env文件配置是否正确（特别是DEBUG和ALLOWED_HOSTS）
echo   2. 运行: python manage.py runserver
echo   3. 访问: http://127.0.0.1:8000
echo.
echo 生产环境部署建议:
echo   - 设置 DEBUG=False
echo   - 设置 ALLOWED_HOSTS=你的域名
echo   - 使用 Gunicorn + Nginx 部署
echo   - 配置SSL证书
echo.
pause

