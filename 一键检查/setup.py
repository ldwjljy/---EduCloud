#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目初始化脚本
用于在新环境中快速设置项目
"""
import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到路径
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))
os.chdir(script_dir)

def run_command(command, description):
    """运行命令并显示进度"""
    print(f"\n{'='*50}")
    print(f"正在执行: {description}")
    print(f"命令: {command}")
    print('='*50)
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 错误: {result.stderr}")
        return False
    print(f"✅ 完成: {description}")
    return True

def check_file_exists(filepath):
    """检查文件是否存在"""
    return Path(filepath).exists()

def main():
    print("="*50)
    print("EduCloud 项目初始化脚本")
    print("="*50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    print(f"✅ Python版本: {sys.version}")
    
    # 检查是否在项目根目录
    if not check_file_exists('manage.py'):
        print("❌ 错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 1. 检查并创建.env文件
    if not check_file_exists('.env'):
        if check_file_exists('.env.example'):
            print("\n📝 创建.env文件...")
            if os.name == 'nt':  # Windows
                os.system('copy .env.example .env')
            else:  # Linux/Mac
                os.system('cp .env.example .env')
            print("✅ .env文件已创建，请编辑.env文件配置数据库等信息")
        else:
            print("⚠️  警告: 未找到.env.example文件")
    else:
        print("✅ .env文件已存在")
    
    # 2. 安装依赖
    if not run_command('pip install -r requirements.txt', '安装Python依赖'):
        print("❌ 依赖安装失败，请检查网络连接和requirements.txt文件")
        sys.exit(1)
    
    # 3. 检查数据库连接（可选）
    print("\n" + "="*50)
    print("数据库配置检查")
    print("="*50)
    print("请确保:")
    print("1. MySQL服务已启动")
    print("2. 已创建数据库（默认: educloud）")
    print("3. .env文件中的数据库配置正确")
    
    confirm = input("\n是否已配置好数据库？(y/n): ")
    if confirm.lower() != 'y':
        print("请先配置数据库后再继续")
        sys.exit(0)
    
    # 4. 运行数据库迁移
    if not run_command('python manage.py migrate', '运行数据库迁移'):
        print("❌ 数据库迁移失败，请检查数据库配置")
        sys.exit(1)
    
    # 5. 询问是否创建超级管理员
    print("\n" + "="*50)
    create_admin = input("是否创建超级管理员账户？(y/n): ")
    if create_admin.lower() == 'y':
        print("\n请按照提示输入管理员信息...")
        run_command('python manage.py createsuperuser', '创建超级管理员')
    
    # 6. 收集静态文件
    run_command('python manage.py collectstatic --noinput', '收集静态文件')
    
    print("\n" + "="*50)
    print("✅ 项目初始化完成！")
    print("="*50)
    print("\n下一步:")
    print("1. 确保.env文件配置正确")
    print("2. 运行: python manage.py runserver")
    print("3. 访问: http://127.0.0.1:8000")
    print("="*50)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        sys.exit(1)
