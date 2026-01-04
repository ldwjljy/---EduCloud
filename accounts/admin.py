from django.contrib import admin
from .models import UserProfile, StudentProfile, TeacherProfile, AdministratorProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    search_fields = ('user__username', 'phone')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'school_class', 'status')
    search_fields = ('student_id',)


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'title', 'department')
    search_fields = ('teacher_id',)


@admin.register(AdministratorProfile)
class AdministratorProfileAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'position')
    search_fields = ('user_profile__user__username',)
