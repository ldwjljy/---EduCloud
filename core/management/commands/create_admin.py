"""
创建管理员账号的管理命令
使用方法: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = '创建管理员账号（用户名：admin，密码：admin）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='管理员用户名（默认：admin）',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin',
            help='管理员密码（默认：admin）',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='管理员邮箱（默认：admin@example.com）',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        # 检查用户是否已存在
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'用户 "{username}" 已存在，正在更新密码...')
            )
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.email = email
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✓ 已更新用户 "{username}" 的密码为 "{password}"')
            )
        else:
            # 创建新用户
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ 成功创建管理员账号！\n'
                    f'  用户名: {username}\n'
                    f'  密码: {password}\n'
                    f'  邮箱: {email}'
                )
            )

