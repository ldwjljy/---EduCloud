"""
Django管理命令：更新班级ID
格式：年级ID(4位) + 学制数(1位) + 学院ID(2位) + 专业ID(2位) + 班级序号(1位，不补零)
例如：2024301011 = 2024年 + 3年制 + 01学院 + 01专业 + 1班
"""
from django.core.management.base import BaseCommand
from organization.models import Class


class Command(BaseCommand):
    help = '更新所有班级的class_id字段'

    def handle(self, *args, **options):
        # 学制数字映射
        duration_map = {
            '3_year': '3',
            '5_year': '5',
            '6_year': '6',
        }
        
        classes = Class.objects.all()
        updated_count = 0
        error_count = 0
        
        self.stdout.write(self.style.SUCCESS(f'找到 {classes.count()} 个班级需要更新'))
        self.stdout.write('=' * 80)
        
        for class_obj in classes:
            try:
                # 获取相关信息
                major = class_obj.major
                college = major.college
                duration_number = duration_map.get(major.duration_type, '03')
                
                # 生成新的class_id
                old_id = getattr(class_obj, 'class_id', None)
                new_class_id = f"{class_obj.enrollment_year}{duration_number}{college.code}{major.code}{class_obj.class_number}"
                
                # 更新
                class_obj.class_id = new_class_id
                class_obj.save()
                
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 班级: {class_obj.name}'))
                self.stdout.write(f'  学院: {college.name} ({college.code})')
                self.stdout.write(f'  专业: {major.name} ({major.code})')
                self.stdout.write(f'  年级: {class_obj.enrollment_year}')
                self.stdout.write(f'  学制: {major.get_duration_type_display()} ({duration_number})')
                self.stdout.write(f'  班级序号: {class_obj.class_number}')
                if old_id:
                    self.stdout.write(f'  旧ID: {old_id}')
                self.stdout.write(f'  新ID: {new_class_id}')
                self.stdout.write('-' * 80)
                
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'✗ 错误更新班级 {class_obj.id}: {str(e)}'))
                self.stdout.write('-' * 80)
        
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS(f'更新完成！'))
        self.stdout.write(self.style.SUCCESS(f'成功: {updated_count} 个'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'失败: {error_count} 个'))
        
        return f'更新了 {updated_count} 个班级'
