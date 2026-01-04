#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目配置检查脚本
用于验证项目是否正确配置
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))
os.chdir(script_dir)

def check_file(filepath, description):
    """检查文件是否存在"""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_env_var(var_name, description):
    """检查环境变量"""
    value = os.getenv(var_name)
    if value:
        # 隐藏敏感信息
        if 'PASSWORD' in var_name or 'SECRET' in var_name:
            display_value = '*' * len(value)
        else:
            display_value = value
        print(f"✅ {description}: {display_value}")
        return True
    else:
        print(f"⚠️  {description}: 未设置（将使用默认值）")
        return False

def check_database_connection():
    """检查数据库连接"""
    try:
        import pymysql
        from dotenv import load_dotenv
        
        load_dotenv()
        
        db_name = os.getenv('DB_NAME', 'educloud')
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '123456')
        db_host = os.getenv('DB_HOST', '127.0.0.1')
        db_port = int(os.getenv('DB_PORT', '3306'))
        
        print(f"\n尝试连接数据库...")
        print(f"  主机: {db_host}:{db_port}")
        print(f"  数据库: {db_name}")
        print(f"  用户: {db_user}")
        
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        connection.close()
        print("✅ 数据库连接成功")
        return True
    except ImportError:
        print("❌ 未安装pymysql或python-dotenv，请运行: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print("   请检查:")
        print("   1. MySQL服务是否已启动")
        print("   2. 数据库是否已创建")
        print("   3. .env文件中的数据库配置是否正确")
        return False

def main():
    print("="*60)
    print("EduCloud 项目配置检查")
    print("="*60)
    
    all_ok = True
    
    # 检查关键文件
    print("\n【文件检查】")
    files_to_check = [
        ('manage.py', 'Django管理脚本'),
        ('requirements.txt', '依赖列表'),
        ('.env.example', '环境变量模板'),
        ('.env', '环境变量文件'),
        ('EduCloud/settings.py', 'Django设置文件'),
    ]
    
    for filepath, description in files_to_check:
        if not check_file(filepath, description):
            if filepath == '.env':
                print("   提示: 可以复制 .env.example 创建 .env 文件")
            else:
                all_ok = False
    
    # 检查环境变量
    print("\n【环境变量检查】")
    if Path('.env').exists():
        from dotenv import load_dotenv
        load_dotenv()
        
        env_vars = [
            ('SECRET_KEY', 'Django密钥'),
            ('DB_NAME', '数据库名称'),
            ('DB_USER', '数据库用户'),
            ('DB_PASSWORD', '数据库密码'),
            ('DB_HOST', '数据库主机'),
        ]
        
        for var_name, description in env_vars:
            check_env_var(var_name, description)
    else:
        print("⚠️  .env文件不存在，将使用settings.py中的默认值")
    
    # 检查Python依赖
    print("\n【Python依赖检查】")
    required_packages = ['django', 'djangorestframework', 'pymysql', 'dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            elif package == 'djangorestframework':
                __import__('rest_framework')
            else:
                __import__(package)
            print(f"✅ {package}: 已安装")
        except ImportError:
            print(f"❌ {package}: 未安装")
            missing_packages.append(package)
            all_ok = False
    
    if missing_packages:
        print(f"\n请运行以下命令安装缺失的包:")
        print(f"  pip install {' '.join(missing_packages)}")
        print("或:")
        print("  pip install -r requirements.txt")
    
    # 检查数据库连接
    print("\n【数据库连接检查】")
    if Path('.env').exists() or all_ok:
        db_ok = check_database_connection()
        if not db_ok:
            all_ok = False
    
    # 总结
    print("\n" + "="*60)
    if all_ok:
        print("✅ 所有检查通过！项目配置正确。")
        print("\n下一步:")
        print("  1. 运行数据库迁移: python manage.py migrate")
        print("  2. 创建超级管理员: python manage.py createsuperuser")
        print("  3. 启动服务器: python manage.py runserver")
    else:
        print("⚠️  发现一些问题，请根据上述提示进行修复。")
    print("="*60)
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
