from django.contrib import admin
from .models import Teacher, Role, UserRole, TeacherPositionHistory


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'name', 'college', 'position_type', 'created_at')
    list_filter = ('college', 'position_type', 'gender')
    search_fields = ('employee_id', 'name', 'phone', 'email')
    ordering = ('college__code', 'employee_id')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_by', 'assigned_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__username', 'role__role_name')
    ordering = ('-assigned_at',)
    readonly_fields = ('assigned_at',)


@admin.register(TeacherPositionHistory)
class TeacherPositionHistoryAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'effective_date', 'created_at')
    list_filter = ('effective_date', 'created_at')
    search_fields = ('teacher__name', 'teacher__employee_id')
    ordering = ('-effective_date',)
    readonly_fields = ('created_at',)