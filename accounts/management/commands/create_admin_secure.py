from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from accounts.models import UserProfile


class Command(BaseCommand):
    help = '创建安全管理员账户：admin/admin，附加超级管理员权限与角色，并提示首次登录强制改密（需结合前端实现）'

    def handle(self, *args, **options):
        with transaction.atomic():
            user, created = User.objects.get_or_create(username='admin', defaults={
                'is_staff': True,
                'is_superuser': True,
            })
            user.set_password('admin')
            user.is_staff = True
            user.is_superuser = True
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'super_admin'})
            if profile.role != 'super_admin':
                profile.role = 'super_admin'
                profile.save()

        self.stdout.write(self.style.SUCCESS('管理员账户创建完成：username=admin, password=admin, role=super_admin'))
        self.stdout.write('请在首次登录后立即修改密码，并启用多因素认证（MFA）准备项。')

