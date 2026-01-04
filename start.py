#!/usr/bin/env python
"""
智能启动脚本 - 自动检查并安装依赖包
支持Windows、Linux、Mac
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"   当前版本: {sys.version}")
        return False
    print(f"✅ Python版本: {sys.version.split()[0]}")
    return True

def read_requirements():
    """读取requirements.txt文件"""
    req_file = Path('requirements.txt')
    if not req_file.exists():
        print("❌ 错误: 未找到requirements.txt文件")
        return None
    
    requirements = []
    with open(req_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if line and not line.startswith('#'):
                # 提取包名（去除版本号）
                package_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
                if package_name:
                    requirements.append({
                        'name': package_name,
                        'spec': line
                    })
    return requirements

def check_package_installed(package_name):
    """检查包是否已安装"""
    try:
        # 处理特殊的包名映射
        import_name = package_name
        if package_name == 'djangorestframework':
            import_name = 'rest_framework'
        elif package_name == 'django-filter':
            import_name = 'django_filters'
        elif package_name == 'python-dotenv':
            import_name = 'dotenv'
        
        __import__(import_name)
        return True
    except ImportError:
        return False

def upgrade_pip():
    """升级pip到最新版本"""
    try:
        print("   正在升级pip...")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def install_package(package_spec):
    """安装单个包"""
    print(f"   正在安装: {package_spec}")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package_spec],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 安装失败: {e.stderr}")
        return False

def check_and_install_requirements():
    """检查并安装所有依赖"""
    print("\n" + "="*60)
    print("检查Python依赖包")
    print("="*60)
    
    requirements = read_requirements()
    if not requirements:
        return False
    
    missing_packages = []
    installed_packages = []
    
    print(f"\n检查 {len(requirements)} 个依赖包...")
    
    for req in requirements:
        package_name = req['name']
        if check_package_installed(package_name):
            print(f"✅ {package_name}: 已安装")
            installed_packages.append(package_name)
        else:
            print(f"❌ {package_name}: 未安装")
            missing_packages.append(req['spec'])
    
    if not missing_packages:
        print(f"\n✅ 所有依赖包已安装！")
        return True
    
    print(f"\n发现 {len(missing_packages)} 个缺失的包，开始自动安装...")
    print("-"*60)
    
    # 先升级pip（可选，但有助于避免安装问题）
    print("   检查pip版本...")
    upgrade_pip()
    
    success_count = 0
    for package_spec in missing_packages:
        if install_package(package_spec):
            success_count += 1
            print(f"   ✅ 安装成功")
        else:
            print(f"   ❌ 安装失败")
    
    print("-"*60)
    if success_count == len(missing_packages):
        print(f"✅ 所有缺失的包已成功安装！")
        return True
    else:
        print(f"⚠️  有 {len(missing_packages) - success_count} 个包安装失败")
        print("   请手动运行: pip install -r requirements.txt")
        return False

def check_env_file():
    """检查.env文件是否存在"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("✅ .env文件已存在")
        return True
    elif env_example.exists():
        print("⚠️  .env文件不存在，正在从.env.example创建...")
        try:
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ .env文件已创建，请编辑.env文件配置数据库等信息")
            return True
        except Exception as e:
            print(f"❌ 创建.env文件失败: {e}")
            return False
    else:
        print("⚠️  .env文件不存在，且未找到.env.example模板")
        return False

def start_django_server():
    """启动Django开发服务器"""
    print("\n" + "="*60)
    print("启动Django开发服务器")
    print("="*60)
    print("\n服务器将在 http://127.0.0.1:8000 启动")
    print("按 Ctrl+C 停止服务器\n")
    
    try:
        # 切换到项目根目录
        os.chdir(Path(__file__).parent)
        
        # 启动Django服务器
        subprocess.run([sys.executable, 'manage.py', 'runserver'])
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
    except FileNotFoundError:
        print("❌ 错误: 未找到manage.py文件")
        print("   请确保在项目根目录运行此脚本")
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")

def main():
    """主函数"""
    print("="*60)
    print("EduCloud 智能启动脚本")
    print("="*60)
    
    # 1. 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 2. 检查.env文件
    print("\n检查环境配置...")
    check_env_file()
    
    # 3. 检查并安装依赖
    if not check_and_install_requirements():
        print("\n⚠️  依赖检查未完全通过，但将继续尝试启动服务器...")
    
    # 4. 启动Django服务器
    start_django_server()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
