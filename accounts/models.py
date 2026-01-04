from django.db import models
from django.contrib.auth.models import User
from organization.models import Class as SchoolClass, Major


USER_ROLES = {
    'super_admin': '超级管理员',
    'principal': '校长',
    'vice_principal': '副校长',
    'dean': '院长',
    'vice_dean': '副院长',
    'head_teacher': '班主任',
    'teacher': '教师',
    'student': '学生',
}

ROLE_CHOICES = [(k, v) for k, v in USER_ROLES.items()]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    avatar_url = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True, verbose_name="性别")

    def __str__(self):
        return f"{self.user.username}-{self.get_role_display()}"
    
    def get_gender_display(self):
        """返回性别的中文显示"""
        from organization.models import Gender
        if self.gender == Gender.MALE:
            return '男'
        elif self.gender == Gender.FEMALE:
            return '女'
        return '-'


class StudentProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=32, unique=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, related_name='students')
    status = models.CharField(max_length=32, default='在读')
    dorm_number = models.CharField(max_length=32, blank=True, null=True, verbose_name="宿舍号")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='students_created')

    def __str__(self):
        return self.student_id


class TeacherProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=64, blank=True, verbose_name='职务')
    department = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True, related_name='teachers')
    subject = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, related_name='teachers')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='teachers_created')

    def __str__(self):
        return self.teacher_id


class AdministratorProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='administrator_profile')
    position = models.CharField(max_length=64)
    college = models.ForeignKey('organization.College', on_delete=models.SET_NULL, null=True, blank=True, related_name='administrators')
    department = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True, blank=True, related_name='administrators')

    def __str__(self):
        return f"{self.user_profile.user.username}-{self.position}"
