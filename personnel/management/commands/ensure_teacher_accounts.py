"""
管理命令：确保所有教师都有用户账户
使用方法: python manage.py ensure_teacher_accounts
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from personnel.models import Teacher
from personnel.services import TeacherService


class Command(BaseCommand):
    help = '检查所有教师，为没有账户的教师自动创建用户账户'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要创建账户的教师，不实际创建',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # 获取所有未删除的教师
        teachers = Teacher.objects.filter(is_deleted=False)
        total_count = teachers.count()
        
        self.stdout.write(f'检查 {total_count} 位教师...')
        
        teachers_without_account = []
        teachers_with_account = []
        created_count = 0
        updated_count = 0
        error_count = 0
        
        service = TeacherService()
        
        for teacher in teachers:
            if not teacher.user:
                teachers_without_account.append(teacher)
                
                if not dry_run:
                    try:
                        with transaction.atomic():
                            service._ensure_user_account(teacher)
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✓ 为教师 {teacher.employee_id} ({teacher.name}) 创建了用户账户'
                                )
                            )
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ 为教师 {teacher.employee_id} ({teacher.name}) 创建账户失败: {str(e)}'
                            )
                        )
                else:
                    self.stdout.write(
                        f'  [待创建] 教师 {teacher.employee_id} ({teacher.name}) 没有用户账户'
                    )
            else:
                teachers_with_account.append(teacher)
                # 检查用户信息是否需要更新
                user = teacher.user
                needs_update = False
                
                if user.first_name != teacher.name:
                    needs_update = True
                    if not dry_run:
                        user.first_name = teacher.name
                
                email = teacher.get_contact_email()
                if email and user.email != email:
                    needs_update = True
                    if not dry_run:
                        user.email = email
                
                if needs_update:
                    if not dry_run:
                        user.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'↻ 更新了教师 {teacher.employee_id} ({teacher.name}) 的用户信息'
                            )
                        )
                    else:
                        self.stdout.write(
                            f'  [待更新] 教师 {teacher.employee_id} ({teacher.name}) 的用户信息需要更新'
                        )
        
        # 输出统计信息
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('统计信息:')
        self.stdout.write(f'  总教师数: {total_count}')
        self.stdout.write(f'  已有账户: {len(teachers_with_account)}')
        self.stdout.write(f'  缺少账户: {len(teachers_without_account)}')
        
        if not dry_run:
            self.stdout.write(f'  新创建账户: {created_count}')
            self.stdout.write(f'  更新账户信息: {updated_count}')
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'  创建失败: {error_count}')
                )
            
            if created_count > 0 or updated_count > 0:
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS('✓ 所有教师账户检查完成！')
                )
            else:
                self.stdout.write('')
                self.stdout.write('✓ 所有教师都已拥有账户，无需操作。')
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING('这是试运行模式，未实际创建或更新账户。')
            )
            self.stdout.write('运行时不加 --dry-run 参数将实际执行操作。')
