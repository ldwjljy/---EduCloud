from django.contrib import admin
from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'scope', 'created_by', 'created_at')
    list_filter = ('scope', 'created_at')
