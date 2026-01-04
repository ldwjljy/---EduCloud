#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键导出Django数据库完整备份（包括创建数据库、表结构和所有数据）
支持：
1. 创建数据库SQL
2. 创建表结构SQL
3. 导出所有数据INSERT语句
4. 导出多对多关系表
"""
import os
import sys
import django
from django.conf import settings
from django.db import connection
from django.apps import apps
from datetime import datetime, date, time
from decimal import Decimal

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)
os.chdir(project_root)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduCloud.settings')
django.setup()

def escape_sql_string(value):
    """转义SQL字符串"""
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
    if isinstance(value, date):
        return f"'{value.strftime('%Y-%m-%d')}'"
    if isinstance(value, time):
        return f"'{value.strftime('%H:%M:%S')}'"
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='ignore')
    # 转义单引号和反斜杠
    value = str(value).replace('\\', '\\\\').replace("'", "\\'")
    return f"'{value}'"

def get_table_name(model):
    """获取模型的数据库表名"""
    return model._meta.db_table

def export_model_data(model, output_file):
    """导出单个模型的所有数据"""
    table_name = get_table_name(model)
    
    try:
        # 获取所有数据库字段（排除多对多和反向关系）
        fields = []
        field_names = []
        for f in model._meta.get_fields():
            # 跳过多对多和反向关系
            if f.many_to_many or f.one_to_many:
                continue
            # 获取数据库字段名
            if hasattr(f, 'column'):
                fields.append(f)
                field_names.append(f.column)
            elif hasattr(f, 'attname'):
                fields.append(f)
                field_names.append(f.attname)
        
        # 查询所有数据
        queryset = model.objects.all()
        count = queryset.count()
        
        if count == 0:
            print(f"  - {table_name}: 无数据")
            return 0
        
        print(f"  - {table_name}: {count} 条记录")
        
        # 写入表结构注释
        output_file.write(f"\n-- ============================================\n")
        output_file.write(f"-- 表: {table_name} ({model.__name__})\n")
        output_file.write(f"-- 记录数: {count}\n")
        output_file.write(f"-- ============================================\n\n")
        
        # 批量处理，避免内存问题
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, count, batch_size):
            batch = queryset[i:i+batch_size]
            
            # 构建INSERT语句
            values_list = []
            for obj in batch:
                row_values = []
                for field in fields:
                    try:
                        # 获取字段值
                        if hasattr(field, 'attname'):
                            value = getattr(obj, field.attname, None)
                        else:
                            value = getattr(obj, field.name, None)
                        
                        # 处理外键字段
                        if hasattr(field, 'remote_field') and field.remote_field:
                            if value is not None:
                                # 外键值已经是ID
                                pass
                        
                        row_values.append(escape_sql_string(value))
                    except Exception as e:
                        row_values.append('NULL')
                
                values_list.append(f"({', '.join(row_values)})")
            
            # 写入INSERT语句
            if values_list:
                field_names_str = ', '.join([f"`{f}`" for f in field_names])
                values_str = ',\n    '.join(values_list)
                output_file.write(f"INSERT INTO `{table_name}` ({field_names_str}) VALUES\n    {values_str};\n\n")
                total_inserted += len(values_list)
        
        return total_inserted
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"  - {table_name}: 导出失败 - {str(e)}")
        output_file.write(f"\n-- 错误: 表 {table_name} 导出失败 - {str(e)}\n\n")
        return 0

def export_database_create(output_file):
    """导出创建数据库的SQL语句"""
    db_config = settings.DATABASES['default']
    db_name = db_config['NAME']
    db_charset = db_config.get('OPTIONS', {}).get('charset', 'utf8mb4')
    db_collation = 'utf8mb4_unicode_ci'
    
    output_file.write("-- ============================================\n")
    output_file.write("-- 创建数据库\n")
    output_file.write("-- ============================================\n\n")
    output_file.write(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET {db_charset} COLLATE {db_collation};\n")
    output_file.write(f"USE `{db_name}`;\n\n")
    print(f"✓ 数据库创建语句: {db_name}")

def export_table_structure(output_file):
    """导出所有表的结构（CREATE TABLE语句）"""
    print("\n导出表结构...")
    output_file.write("-- ============================================\n")
    output_file.write("-- 表结构定义\n")
    output_file.write("-- ============================================\n\n")
    
    try:
        with connection.cursor() as cursor:
            # 获取所有表名
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                print("  警告: 未找到任何表")
                return
            
            print(f"  找到 {len(tables)} 个表")
            
            for table_name in tables:
                try:
                    # 获取表的CREATE TABLE语句
                    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                    result = cursor.fetchone()
                    if result:
                        create_table_sql = result[1]
                        # 添加注释
                        output_file.write(f"\n-- ============================================\n")
                        output_file.write(f"-- 表: {table_name}\n")
                        output_file.write("-- ============================================\n")
                        output_file.write(f"{create_table_sql};\n\n")
                        print(f"  ✓ {table_name}")
                except Exception as e:
                    print(f"  ✗ {table_name}: 导出失败 - {str(e)}")
                    output_file.write(f"\n-- 错误: 表 {table_name} 结构导出失败 - {str(e)}\n\n")
    except Exception as e:
        print(f"  导出表结构时出错: {str(e)}")
        output_file.write(f"\n-- 错误: 导出表结构失败 - {str(e)}\n\n")

def export_many_to_many_tables(output_file):
    """导出多对多关系表"""
    print("\n导出多对多关系表...")
    
    installed_apps = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'rest_framework.authtoken',
        'core',
        'accounts',
        'organization',
        'personnel',
        'courses',
        'attendance_app',
        'grades',
        'notices',
        'calendarapp',
        'classrooms',
        'students',
        'exams',
        'teachers',
        'system',
    ]
    
    total_m2m_records = 0
    
    for app_label in installed_apps:
        try:
            app_config = apps.get_app_config(app_label.split('.')[-1])
            models = app_config.get_models()
            
            for model in models:
                if model._meta.abstract or model._meta.proxy:
                    continue
                
                # 检查多对多字段
                for field in model._meta.get_fields():
                    if field.many_to_many and not field.auto_created:
                        # 获取中间表名
                        m2m_table = field.m2m_db_table()
                        
                        try:
                            # 查询多对多关系数据
                            with connection.cursor() as cursor:
                                cursor.execute(f"SELECT * FROM `{m2m_table}`")
                                rows = cursor.fetchall()
                                
                                if rows:
                                    # 获取列名
                                    columns = [col[0] for col in cursor.description]
                                    
                                    print(f"  - {m2m_table}: {len(rows)} 条记录")
                                    
                                    output_file.write(f"\n-- ============================================\n")
                                    output_file.write(f"-- 多对多关系表: {m2m_table}\n")
                                    output_file.write(f"-- 模型: {model.__name__}.{field.name}\n")
                                    output_file.write(f"-- 记录数: {len(rows)}\n")
                                    output_file.write(f"-- ============================================\n\n")
                                    
                                    # 构建INSERT语句
                                    values_list = []
                                    for row in rows:
                                        row_values = [escape_sql_string(val) for val in row]
                                        values_list.append(f"({', '.join(row_values)})")
                                    
                                    if values_list:
                                        column_names_str = ', '.join([f"`{col}`" for col in columns])
                                        values_str = ',\n    '.join(values_list)
                                        output_file.write(f"INSERT INTO `{m2m_table}` ({column_names_str}) VALUES\n    {values_str};\n\n")
                                        total_m2m_records += len(values_list)
                        except Exception as e:
                            print(f"  - {m2m_table}: 导出失败 - {str(e)}")
                            continue
                            
        except LookupError:
            continue
        except Exception as e:
            print(f"应用 {app_label} 的多对多表处理出错: {str(e)}")
            continue
    
    return total_m2m_records

def export_all_data(output_filename='database_export.sql', include_structure=True):
    """
    导出完整的数据库备份（包括创建数据库、表结构和所有数据）
    
    参数:
        output_filename: 输出文件名
        include_structure: 是否包含表结构（默认True）
    """
    print("=" * 60)
    print("开始导出完整数据库备份...")
    print("=" * 60)
    
    # 获取所有已安装的应用
    installed_apps = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'django.contrib.messages',
        'rest_framework.authtoken',
        'core',
        'accounts',
        'organization',
        'personnel',
        'courses',
        'attendance_app',
        'grades',
        'notices',
        'calendarapp',
        'classrooms',
        'students',
        'exams',
        'teachers',
        'system',
    ]
    
    # 输出文件路径（项目根目录）
    output_path = os.path.join(project_root, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入文件头
        f.write("-- ============================================\n")
        f.write(f"-- MySQL数据库完整备份文件\n")
        f.write(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- 数据库: {settings.DATABASES['default']['NAME']}\n")
        f.write(f"-- Django版本: {django.get_version()}\n")
        f.write("-- ============================================\n\n")
        
        # 1. 创建数据库
        export_database_create(f)
        
        # 2. 导出表结构
        if include_structure:
            export_table_structure(f)
        
        # 3. 开始事务并禁用外键检查
        f.write("\n-- ============================================\n")
        f.write("-- 开始数据导入\n")
        f.write("-- ============================================\n\n")
        f.write("SET FOREIGN_KEY_CHECKS=0;\n")
        f.write("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n")
        f.write("SET AUTOCOMMIT=0;\n")
        f.write("START TRANSACTION;\n\n")
        
        total_records = 0
        
        # 4. 遍历所有应用导出数据
        print("\n导出数据...")
        for app_label in installed_apps:
            try:
                app_config = apps.get_app_config(app_label.split('.')[-1])
                models = app_config.get_models()
                
                app_models = list(models)
                if app_models:
                    print(f"\n应用: {app_label}")
                    f.write(f"\n-- ============================================\n")
                    f.write(f"-- 应用: {app_label}\n")
                    f.write("-- ============================================\n\n")
                    
                    for model in app_models:
                        # 跳过抽象模型和代理模型
                        if model._meta.abstract or model._meta.proxy:
                            continue
                        
                        records = export_model_data(model, f)
                        total_records += records
                        
            except LookupError:
                # 应用不存在，跳过
                continue
            except Exception as e:
                print(f"应用 {app_label} 处理出错: {str(e)}")
                continue
        
        # 5. 导出多对多关系表
        m2m_records = export_many_to_many_tables(f)
        total_records += m2m_records
        
        # 6. 提交事务并恢复外键检查
        f.write("\n-- ============================================\n")
        f.write("-- 数据导入完成\n")
        f.write("-- ============================================\n\n")
        f.write("COMMIT;\n")
        f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        f.write("SET AUTOCOMMIT=1;\n\n")
        
        # 写入文件尾
        f.write("-- ============================================\n")
        f.write("-- 备份完成\n")
        f.write(f"-- 总记录数: {total_records}\n")
        f.write("-- ============================================\n")
    
    print("\n" + "=" * 60)
    print("✓ 导出完成！")
    print(f"  总记录数: {total_records}")
    print(f"  输出文件: {output_path}")
    print(f"  文件大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    print("=" * 60)
    print("\n使用说明:")
    print(f"  1. 在MySQL中执行: mysql -u用户名 -p < {output_filename}")
    print(f"  2. 或者使用MySQL客户端导入该SQL文件")
    print("=" * 60)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='导出Django数据库完整备份（包括创建数据库、表结构和所有数据）')
    parser.add_argument('output_file', nargs='?', default='database_export.sql', 
                       help='输出文件名（默认: database_export.sql）')
    parser.add_argument('--no-structure', action='store_true', 
                       help='不包含表结构，只导出数据')
    parser.add_argument('--data-only', action='store_true', 
                       help='只导出数据，不包含创建数据库和表结构（等同于--no-structure）')
    
    args = parser.parse_args()
    
    include_structure = not (args.no_structure or args.data_only)
    
    if args.data_only:
        print("⚠ 警告: 使用 --data-only 模式，将不包含创建数据库和表结构")
    
    export_all_data(args.output_file, include_structure=include_structure)
