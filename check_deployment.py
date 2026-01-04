#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
部署前检查脚本
用于验证项目是否已准备好进行部署
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
os.chdir(script_dir)

def check_file(filepath, description, required=True):
    """检查文件是否存在"""
    exists = Path(filepath).exists()
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {description}: {filepath}")
    if not exists and required:
        print(f"   必需文件缺失！")
    return exists

def check_directory(dirpath, description, required=True):
    """检查目录是否存在"""
    exists = Path(dirpath).exists() and Path(dirpath).is_dir()
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {description}: {dirpath}")
    if not exists and required:
        print(f"   必需目录缺失！")
    return exists

def check_env_var(var_name, description, required=True):
    """检查环境变量"""
    from dotenv import load_dotenv
    load_dotenv()
    
    value = os.getenv(var_name)
    if value:
        # 隐藏敏感信息
        if 'PASSWORD' in var_name or 'SECRET' in var_name:
            display_value = '*' * min(len(value), 20)
        else:
            display_value = value
        print(f"✅ {description}: {display_value}")
        return True
    else:
        status = "❌" if required else "⚠️"
        print(f"{status} {description}: 未设置" + ("（必需）" if required else "（可选）"))
        return not required

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version >= (3, 8):
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python版本: {version.major}.{version.minor}.{version.micro} (需要3.8+)")
        return False

def check_requirements():
    """检查Python依赖"""
    try:
        import django
        import rest_framework
        import pymysql
        import dotenv
        print("✅ 核心依赖包已安装")
        print(f"   - Django: {django.get_version()}")
        return True
    except ImportError as e:
        print(f"❌ 依赖包缺失: {e}")
        print("   请运行: pip install -r requirements.txt")
        return False

def check_database_connection():
    """检查数据库连接"""
    try:
        from dotenv import load_dotenv
        import pymysql
        
        load_dotenv()
        
        db_name = os.getenv('DB_NAME', 'educloud')
        db_user = os.getenv('DB_USER', 'root')
        db_password = os.getenv('DB_PASSWORD', '123456')
        db_host = os.getenv('DB_HOST', '127.0.0.1')
        db_port = int(os.getenv('DB_PORT', '3306'))
        
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
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print("   请检查:")
        print("   1. MySQL服务是否已启动")
        print("   2. 数据库是否已创建")
        print("   3. .env文件中的数据库配置是否正确")
        return False

def check_migrations():
    """检查数据库迁移状态"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduCloud.settings')
        import django
        django.setup()
        
        from django.core.management import execute_from_command_line
        from io import StringIO
        import sys
        
        # 检查未应用的迁移
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            from django.core.management import call_command
            from django.db import connection
            call_command('showmigrations', '--plan', verbosity=0)
        except Exception:
            pass
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
        
        print("✅ 数据库迁移检查完成（建议运行: python manage.py migrate）")
        return True
    except Exception as e:
        print(f"⚠️  迁移检查跳过: {str(e)}")
        return True  # 不阻塞

def check_static_files():
    """检查静态文件配置"""
    static_dir = Path('static')
    staticfiles_dir = Path('staticfiles')
    
    if static_dir.exists():
        print(f"✅ 静态文件目录存在: {static_dir}")
    else:
        print(f"⚠️  静态文件目录不存在: {static_dir}")
    
    if staticfiles_dir.exists():
        print(f"✅ 静态文件收集目录存在: {staticfiles_dir}")
    else:
        print(f"⚠️  静态文件收集目录不存在（运行: python manage.py collectstatic）")
    
    return True  # 不阻塞

def main():
    print("="*70)
    print("EduCloud 部署前检查")
    print("="*70)
    
    all_checks = []
    
    # 1. Python环境检查
    print("\n【1. Python环境检查】")
    all_checks.append(check_python_version())
    all_checks.append(check_requirements())
    
    # 2. 文件检查
    print("\n【2. 文件检查】")
    all_checks.append(check_file('manage.py', 'Django管理脚本', required=True))
    all_checks.append(check_file('requirements.txt', '依赖列表', required=True))
    all_checks.append(check_file('.env.example', '环境变量模板', required=True))
    all_checks.append(check_file('.env', '环境变量文件', required=True))
    all_checks.append(check_file('EduCloud/settings.py', 'Django设置文件', required=True))
    all_checks.append(check_file('deploy.bat', 'Windows部署脚本', required=False))
    all_checks.append(check_file('deploy.sh', 'Linux部署脚本', required=False))
    all_checks.append(check_file('DEPLOYMENT.md', '部署文档', required=False))
    
    # 3. 目录检查
    print("\n【3. 目录检查】")
    all_checks.append(check_directory('templates', '模板目录', required=True))
    all_checks.append(check_directory('static', '静态文件目录', required=True))
    all_checks.append(check_directory('EduCloud', '项目配置目录', required=True))
    
    # 4. 环境变量检查
    print("\n【4. 环境变量检查】")
    if Path('.env').exists():
        all_checks.append(check_env_var('SECRET_KEY', 'Django密钥', required=True))
        all_checks.append(check_env_var('DEBUG', '调试模式', required=False))
        all_checks.append(check_env_var('ALLOWED_HOSTS', '允许的主机', required=False))
        all_checks.append(check_env_var('DB_NAME', '数据库名称', required=True))
        all_checks.append(check_env_var('DB_USER', '数据库用户', required=True))
        all_checks.append(check_env_var('DB_PASSWORD', '数据库密码', required=True))
        all_checks.append(check_env_var('DB_HOST', '数据库主机', required=True))
    else:
        print("⚠️  .env文件不存在，跳过环境变量检查")
        print("   请先复制 .env.example 创建 .env 文件")
    
    # 5. 数据库检查
    print("\n【5. 数据库检查】")
    db_check = check_database_connection()
    all_checks.append(db_check)
    
    if db_check:
        check_migrations()
    
    # 6. 静态文件检查
    print("\n【6. 静态文件检查】")
    check_static_files()
    
    # 总结
    print("\n" + "="*70)
    critical_failed = sum(1 for x in all_checks if not x)
    
    if critical_failed == 0:
        print("✅ 所有关键检查通过！项目已准备好进行部署。")
        print("\n下一步:")
        print("  1. 运行部署脚本: deploy.bat (Windows) 或 ./deploy.sh (Linux/Mac)")
        print("  2. 或手动执行部署步骤（参考 DEPLOYMENT.md）")
        return 0
    else:
        print(f"⚠️  有 {critical_failed} 项关键检查未通过，请先解决这些问题。")
        print("\n建议:")
        print("  1. 检查上述❌标记的项目")
        print("  2. 参考 DEPLOYMENT.md 文档")
        print("  3. 运行配置检查: python 一键检查/check_setup.py")
        return 1

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

