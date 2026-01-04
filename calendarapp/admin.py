from django.contrib import admin
from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'visibility', 'start_time', 'end_time')
    list_filter = ('event_type', 'visibility')
