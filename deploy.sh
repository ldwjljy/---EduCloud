#!/bin/bash
# EduCloud 一键部署脚本 (Linux/Mac)

set -e  # 遇到错误立即退出

echo "========================================"
echo "  EduCloud 一键部署脚本 (Linux/Mac)"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.8或更高版本"
    exit 1
fi

echo "✅ Python已安装"
python3 --version

echo
echo "========================================"
echo "步骤 1: 检查环境配置"
echo "========================================"

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  .env文件不存在"
    if [ -f .env.example ]; then
        echo "📝 正在从.env.example创建.env文件..."
        cp .env.example .env
        echo "✅ .env文件已创建"
        echo "⚠️  请务必编辑.env文件，配置数据库等信息！"
        read -p "按回车键继续..."
    else
        echo "❌ 错误: 未找到.env.example模板文件"
        exit 1
    fi
else
    echo "✅ .env文件已存在"
fi

echo
echo "========================================"
echo "步骤 2: 安装/更新Python依赖"
echo "========================================"
echo "正在升级pip..."
python3 -m pip install --upgrade pip --quiet

echo "正在安装依赖包..."
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi
echo "✅ 依赖安装完成"

echo
echo "========================================"
echo "步骤 3: 数据库检查"
echo "========================================"
echo "⚠️  请确保:"
echo "   1. MySQL服务已启动"
echo "   2. 数据库已创建（默认名称: educloud）"
echo "   3. .env文件中的数据库配置正确"
echo
read -p "是否已完成数据库配置？(Y/N): " db_ready
if [[ ! $db_ready =~ ^[Yy]$ ]]; then
    echo "请先配置数据库后再运行此脚本"
    exit 0
fi

echo
echo "========================================"
echo "步骤 4: 运行数据库迁移"
echo "========================================"
python3 manage.py migrate
if [ $? -ne 0 ]; then
    echo "❌ 数据库迁移失败，请检查数据库配置"
    exit 1
fi
echo "✅ 数据库迁移完成"

echo
echo "========================================"
echo "步骤 5: 收集静态文件"
echo "========================================"
python3 manage.py collectstatic --noinput
if [ $? -ne 0 ]; then
    echo "⚠️  静态文件收集失败，但可以继续"
else
    echo "✅ 静态文件收集完成"
fi

echo
echo "========================================"
echo "步骤 6: 创建超级管理员（可选）"
echo "========================================"
read -p "是否创建超级管理员账户？(Y/N): " create_admin
if [[ $create_admin =~ ^[Yy]$ ]]; then
    python3 manage.py createsuperuser
fi

echo
echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo
echo "下一步操作:"
echo "  1. 检查.env文件配置是否正确（特别是DEBUG和ALLOWED_HOSTS）"
echo "  2. 运行: python3 manage.py runserver"
echo "  3. 访问: http://127.0.0.1:8000"
echo
echo "生产环境部署建议:"
echo "  - 设置 DEBUG=False"
echo "  - 设置 ALLOWED_HOSTS=你的域名"
echo "  - 使用 Gunicorn + Nginx 部署"
echo "  - 配置SSL证书"
echo

