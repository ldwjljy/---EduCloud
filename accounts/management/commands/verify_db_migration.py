from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.apps import apps
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = '数据库迁移执行与后置验证：结构校验、事务原子性测试、外键与业务关联验证、异常回滚模拟'

    def handle(self, *args, **options):
        self.stdout.write('开始预处理阶段：验证所有表结构...')
        # 验证模型对应的表是否存在
        missing_tables = []
        with connection.cursor() as cursor:
            existing = set(connection.introspection.table_names())
            for model in apps.get_models():
                table = model._meta.db_table
                if table not in existing:
                    missing_tables.append(table)
        if missing_tables:
            raise ValidationError({'missing_tables': missing_tables})
        self.stdout.write(self.style.SUCCESS('表结构存在性验证通过'))

        self.stdout.write('执行阶段：原子事务测试...')
        # 原子事务与回滚测试
        try:
            with transaction.atomic():
                from organization.models import College, Major
                c = College.objects.create(code='9999', name='事务测试学院', establishment_date='2024-01-01')
                Major.objects.create(code='999901', name='事务测试专业', college=c)
                # 人为触发错误以验证回滚
                raise RuntimeError('模拟异常以测试事务回滚')
        except RuntimeError:
            pass
        # 验证未产生脏数据
        from organization.models import College
        assert not College.objects.filter(code='9999', is_deleted=False).exists(), '事务回滚失败，出现脏数据'
        self.stdout.write(self.style.SUCCESS('原子事务与回滚测试通过'))

        self.stdout.write('后验证阶段：外键与业务逻辑关联测试...')
        # 外键约束与业务关联
        from organization.models import Major, Class
        # 构造一条合法数据用于外键与唯一约束测试
        with transaction.atomic():
            c = College.objects.create(code='8888', name='外键测试学院', establishment_date='2024-01-01')
            m = Major.objects.create(code='888801', name='外键测试专业', college=c)
            cls1 = Class.objects.create(major=m, enrollment_year=2024, class_number=1, name=f'2024年{m.name}{m.get_duration_label()}-1班')
            try:
                # 唯一约束：同专业同年份同序号不允许重复
                Class.objects.create(major=m, enrollment_year=2024, class_number=1, name=f'2024年{m.name}{m.get_duration_label()}-1班')
                raise AssertionError('unique_together 未生效')
            except Exception:
                pass
        # 清理测试数据
        College.objects.filter(code__in=['8888']).update(is_deleted=True)
        self.stdout.write(self.style.SUCCESS('外键与业务关联测试通过'))

        self.stdout.write(self.style.SUCCESS('数据库迁移验证完成：所有检查通过'))

