#!/bin/bash
# EduCloud 一键检查工具 (Linux/Mac)

echo "========================================"
echo "  EduCloud 一键检查工具"
echo "========================================"
echo ""

# 切换到脚本所在目录的父目录（项目根目录）
cd "$(dirname "$0")/.."

# 检查Python是否安装
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到Python，请先安装Python 3.8或更高版本"
    exit 1
fi

# 优先使用python3，如果没有则使用python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

# 运行一键检查脚本
$PYTHON_CMD "一键检查/一键检查.py"
