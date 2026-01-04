# Generated manually on 2025-12-08

from django.db import migrations


def update_class_ids(apps, schema_editor):
    """
    更新现有班级的class_id字段
    格式：年级ID(4位) + 学制数(1位) + 学院ID(2位) + 专业ID(2位) + 班级序号(1位，不补零)
    例如：2024301011 = 2024年 + 3年制 + 01学院 + 01专业 + 1班
    """
    Class = apps.get_model('organization', 'Class')
    
    # 定义学制数字映射
    duration_map = {
        '3_year': '3',
        '5_year': '5',
        '6_year': '6',
    }
    
    updated_count = 0
    for class_obj in Class.objects.all():
        try:
            # 获取专业和学院信息
            major = class_obj.major
            college = major.college
            
            # 获取学制数字
            duration_number = duration_map.get(major.duration_type, '3')
            
            # 生成class_id
            class_id = f"{class_obj.enrollment_year}{duration_number}{college.code}{major.code}{class_obj.class_number}"
            
            # 更新class_id字段
            class_obj.class_id = class_id
            class_obj.save(update_fields=['class_id'])
            updated_count += 1
            
            print(f"Updated: {class_obj.name} -> {class_id}")
        except Exception as e:
            print(f"Error updating class {class_obj.id}: {str(e)}")
    
    print(f"\n总计更新 {updated_count} 个班级")


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0006_alter_major_code'),
    ]

    operations = [
        migrations.RunPython(update_class_ids, reverse_code=migrations.RunPython.noop),
    ]
