"""
清空数据库的管理命令
使用方法: python manage.py clear_db
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = '清空数据库中的所有数据（保留表结构）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='跳过确认提示',
        )

    def handle(self, *args, **options):
        if not options['noinput']:
            confirm = input(
                '⚠️  警告：此操作将清空数据库中的所有数据！\n'
                '此操作不可恢复，请确认是否继续？(yes/no): '
            )
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('操作已取消'))
                return

        self.stdout.write(self.style.WARNING('开始清空数据库...'))
        
        try:
            # 使用Django的flush命令清空所有数据
            # 这会删除所有数据但保留表结构
            call_command('flush', '--noinput', verbosity=0)
            
            self.stdout.write(self.style.SUCCESS('✓ 数据库已成功清空！'))
            self.stdout.write(self.style.SUCCESS('所有表结构已保留，可以重新开始使用。'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ 清空数据库时出错: {str(e)}'))
            raise

