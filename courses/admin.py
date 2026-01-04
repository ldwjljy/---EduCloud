from django.contrib import admin
from .models import Course, TimeSlot, ScheduleTimeConfig, CourseSchedule


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_type')
    list_filter = ('course_type',)
    search_fields = ('name',)


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('weekday', 'index', 'start_time', 'end_time')
    list_filter = ('weekday',)


@admin.register(ScheduleTimeConfig)
class ScheduleTimeConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'morning_sessions', 'afternoon_sessions', 'lesson_minutes', 'break_minutes')


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'course', 'teacher', 'timeslot', 'week_number')
    list_filter = ('week_number', 'school_class')
