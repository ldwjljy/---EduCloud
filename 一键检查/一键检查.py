#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键检查主入口脚本
整合所有检查功能，提供统一的检查入口
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
script_dir = Path(__file__).parent.parent
check_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
os.chdir(script_dir)

def print_menu():
    """打印菜单"""
    print("="*70)
    print("EduCloud 一键检查工具")
    print("="*70)
    print()
    print("请选择要执行的检查:")
    print()
    print("  1. 项目配置检查 (check_setup.py)")
    print("     - 检查文件是否存在")
    print("     - 检查环境变量配置")
    print("     - 检查Python依赖")
    print("     - 检查数据库连接")
    print()
    print("  2. 项目初始化 (setup.py)")
    print("     - 创建.env文件")
    print("     - 安装依赖")
    print("     - 运行数据库迁移")
    print("     - 创建超级管理员")
    print()
    print("  3. 导入前检查 (check_before_import.py)")
    print("     - 检查班级是否存在")
    print("     - 检查时间段是否初始化")
    print("     - 检查管理员用户")
    print("     - 检查已有数据")
    print()
    print("  4. 周五时间段检查 (check_friday_slots.py)")
    print("     - 检查周五的时间段配置")
    print("     - 显示各工作日时间段数量")
    print()
    print("  5. 执行所有检查")
    print()
    print("  0. 退出")
    print()
    print("="*70)

def run_check_setup():
    """运行配置检查"""
    print("\n" + "="*70)
    print("执行: 项目配置检查")
    print("="*70 + "\n")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_setup", check_dir / "check_setup.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.main()
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def run_setup():
    """运行项目初始化"""
    print("\n" + "="*70)
    print("执行: 项目初始化")
    print("="*70 + "\n")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup", check_dir / "setup.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main()
        return 0
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def run_check_before_import():
    """运行导入前检查"""
    print("\n" + "="*70)
    print("执行: 导入前检查")
    print("="*70 + "\n")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_before_import", check_dir / "check_before_import.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        success = module.main()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def run_check_friday_slots():
    """运行周五时间段检查"""
    print("\n" + "="*70)
    print("执行: 周五时间段检查")
    print("="*70 + "\n")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_friday_slots", check_dir / "check_friday_slots.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return 0
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def run_all_checks():
    """运行所有检查"""
    print("\n" + "="*70)
    print("执行: 所有检查")
    print("="*70 + "\n")
    
    results = []
    
    # 1. 配置检查
    print("\n【1/4】项目配置检查")
    print("-"*70)
    results.append(("项目配置检查", run_check_setup() == 0))
    
    # 2. 导入前检查（需要Django环境）
    print("\n【2/4】导入前检查")
    print("-"*70)
    try:
        results.append(("导入前检查", run_check_before_import() == 0))
    except Exception as e:
        print(f"⚠️  跳过导入前检查（需要Django环境）: {str(e)}")
        results.append(("导入前检查", None))
    
    # 3. 周五时间段检查（需要Django环境）
    print("\n【3/4】周五时间段检查")
    print("-"*70)
    try:
        results.append(("周五时间段检查", run_check_friday_slots() == 0))
    except Exception as e:
        print(f"⚠️  跳过周五时间段检查（需要Django环境）: {str(e)}")
        results.append(("周五时间段检查", None))
    
    # 总结
    print("\n" + "="*70)
    print("检查结果汇总")
    print("="*70)
    
    for name, result in results:
        if result is None:
            status = "⚠️  跳过"
        elif result:
            status = "✅ 通过"
        else:
            status = "❌ 失败"
        print(f"{status} {name}")
    
    print("="*70)
    
    # 返回结果
    passed = sum(1 for _, r in results if r is True)
    total = sum(1 for _, r in results if r is not None)
    
    if total > 0 and passed == total:
        return 0
    else:
        return 1

def main():
    """主函数"""
    while True:
        print_menu()
        try:
            choice = input("请输入选项 (0-5): ").strip()
            
            if choice == '0':
                print("\n退出程序")
                break
            elif choice == '1':
                run_check_setup()
            elif choice == '2':
                run_setup()
            elif choice == '3':
                run_check_before_import()
            elif choice == '4':
                run_check_friday_slots()
            elif choice == '5':
                run_all_checks()
            else:
                print("\n❌ 无效的选项，请重新选择")
                continue
            
            # 询问是否继续
            print("\n" + "-"*70)
            continue_choice = input("是否继续？(y/n): ").strip().lower()
            if continue_choice != 'y':
                break
                
        except KeyboardInterrupt:
            print("\n\n操作已取消")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            break
    
    print("\n感谢使用！")

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
