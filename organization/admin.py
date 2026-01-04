from django.contrib import admin
from .models import College, Major, Class, SystemDictionary, OperationLog


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'status', 'establishment_date', 'created_at')
    list_filter = ('status', 'establishment_date')
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'college', 'duration_type', 'created_at')
    list_filter = ('college', 'duration_type')
    search_fields = ('code', 'name', 'description')
    ordering = ('college__code', 'code')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'major', 'enrollment_year', 'class_number', 'head_teacher', 'created_at')
    list_filter = ('major__college', 'major', 'enrollment_year')
    search_fields = ('name', 'major__name', 'major__college__name')
    ordering = ('-enrollment_year', 'major__code', 'class_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SystemDictionary)
class SystemDictionaryAdmin(admin.ModelAdmin):
    list_display = ('dict_type', 'dict_key', 'dict_value', 'sort_order', 'is_active')
    list_filter = ('dict_type', 'is_active')
    search_fields = ('dict_key', 'dict_value', 'description')
    ordering = ('dict_type', 'sort_order')


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'operation_type', 'table_name', 'record_id', 'created_at', 'ip_address')
    list_filter = ('operation_type', 'table_name', 'created_at')
    search_fields = ('table_name', 'record_id', 'user_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser