from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from notices.models import Notice
from calendarapp.models import CalendarEvent

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        username = (options.get('username') or '').strip()
        dry = bool(options.get('dry_run'))
        target = None
        if username:
            try:
                target = User.objects.get(username=username)
            except User.DoesNotExist:
                pass
        if target is None:
            target = User.objects.filter(is_superuser=True).order_by('id').first()
        if target is None:
            try:
                from accounts.models import UserProfile
                p = UserProfile.objects.filter(role='super_admin').order_by('id').first()
                target = getattr(p, 'user', None)
            except Exception:
                target = None
        if target is None:
            target = User.objects.order_by('id').first()
        if target is None:
            self.stdout.write('no user available')
            return
        n_qs = Notice.objects.filter(created_by__isnull=True)
        e_qs = CalendarEvent.objects.filter(created_by__isnull=True)
        n_count = n_qs.count()
        e_count = e_qs.count()
        if dry:
            self.stdout.write(f'will update notices: {n_count}, events: {e_count}, user: {target.username}')
            return
        n_qs.update(created_by=target)
        e_qs.update(created_by=target)
        self.stdout.write(f'updated notices: {n_count}, events: {e_count}, user: {target.username}')
