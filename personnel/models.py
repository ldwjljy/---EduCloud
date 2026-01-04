from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from organization.models import BaseModel, College, Major, Class, Gender, PositionType, validate_contact_info


class Teacher(BaseModel):
    """教师模型"""
    employee_id = models.CharField(
        max_length=20, 
        primary_key=True,
        help_text='工号，主键'
    )
    name = models.CharField(
        max_length=50, 
        help_text='姓名'
    )
    gender = models.CharField(
        max_length=10, 
        choices=Gender.choices,
        help_text='性别'
    )
    contact_info = models.JSONField(
        default=dict, 
        blank=True,
        validators=[validate_contact_info],
        help_text='联系方式，JSON格式，包含phone和email'
    )
    hire_date = models.DateField(
        help_text='入职日期'
    )
    position_type = models.CharField(
        max_length=20, 
        choices=PositionType.choices,
        help_text='职务类型'
    )
    college = models.ForeignKey(
        College,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='teachers',
        help_text='所属学院'
    )
    managed_majors = models.JSONField(
        default=list,
        blank=True,
        help_text='管辖专业IDs，JSON数组'
    )
    managed_class = models.OneToOneField(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='head_teacher_profile',
        help_text='负责班级'
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='teacher_profile',
        help_text='关联用户'
    )

    class Meta:
        db_table = 'teachers'
        indexes = [
            models.Index(fields=['college', 'position_type']),
            models.Index(fields=['name']),
            models.Index(fields=['position_type']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['college', 'position_type'],
                condition=models.Q(position_type='dean'),
                name='unique_college_dean'
            ),
        ]

    def __str__(self):
        return f"{self.employee_id}-{self.name}"

    def clean(self):
        """模型级验证"""
        if self.hire_date > timezone.now().date():
            raise ValidationError('入职日期不能大于当前日期')
        
        # 验证院长唯一性
        if self.position_type == 'dean' and self.college:
            existing_dean = Teacher.objects.filter(
                college=self.college,
                position_type='dean',
                is_deleted=False
            ).exclude(employee_id=self.employee_id).first()
            
            if existing_dean:
                raise ValidationError(f'学院 "{self.college.name}" 已存在院长：{existing_dean.name}')

    def save(self, *args, **kwargs):
        """保存前的处理"""
        self.full_clean()
        super().save(*args, **kwargs)
        
        # 自动创建用户账户（如果不存在且未删除）
        if not self.is_deleted and not self.user:
            from personnel.services import TeacherService
            service = TeacherService()
            service._ensure_user_account(self)

    def get_contact_phone(self):
        """获取联系电话"""
        return self.contact_info.get('phone', '')

    def get_contact_email(self):
        """获取联系邮箱"""
        return self.contact_info.get('email', '')

    def get_managed_majors_list(self):
        """获取管辖专业列表"""
        if not self.managed_majors:
            return []
        return Major.objects.filter(id__in=self.managed_majors, is_deleted=False)

    def set_managed_majors(self, major_ids):
        """设置管辖专业"""
        if not isinstance(major_ids, list):
            raise ValidationError('管辖专业必须是列表格式')
        
        # 验证专业ID是否存在
        existing_major_ids = Major.objects.filter(
            id__in=major_ids,
            is_deleted=False
        ).values_list('id', flat=True)
        
        invalid_ids = set(major_ids) - set(existing_major_ids)
        if invalid_ids:
            raise ValidationError(f'以下专业ID不存在：{invalid_ids}')
        
        self.managed_majors = major_ids

    def can_manage_major(self, major_id):
        """检查是否可以管理指定专业"""
        return major_id in self.managed_majors


class Role(BaseModel):
    """角色模型"""
    name = models.CharField(
        max_length=50, 
        unique=True,
        help_text='角色名称'
    )
    code = models.CharField(
        max_length=50, 
        unique=True,
        help_text='角色代码'
    )
    description = models.TextField(
        blank=True,
        help_text='角色描述'
    )
    permissions = models.JSONField(
        default=list,
        help_text='权限列表，JSON数组'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='是否启用'
    )

    class Meta:
        db_table = 'roles'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def has_permission(self, permission_code):
        """检查是否有指定权限"""
        return permission_code in self.permissions


class UserRole(BaseModel):
    """用户角色关联模型"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
        help_text='用户'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
        help_text='角色'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_roles',
        help_text='分配人'
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text='分配时间'
    )

    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.username}-{self.role.name}"


class TeacherPositionHistory(BaseModel):
    """教师职务变更历史"""
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='position_history',
        help_text='教师'
    )
    old_position = models.CharField(
        max_length=20,
        choices=PositionType.choices,
        null=True,
        blank=True,
        help_text='原职务'
    )
    new_position = models.CharField(
        max_length=20,
        choices=PositionType.choices,
        help_text='新职务'
    )
    old_college = models.ForeignKey(
        College,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='position_history_old',
        help_text='原学院'
    )
    new_college = models.ForeignKey(
        College,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='position_history_new',
        help_text='新学院'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='teacher_position_changes',
        help_text='变更人'
    )
    change_reason = models.TextField(
        blank=True,
        help_text='变更原因'
    )
    effective_date = models.DateField(
        help_text='生效日期'
    )

    class Meta:
        db_table = 'teacher_position_history'
        indexes = [
            models.Index(fields=['teacher', 'effective_date']),
            models.Index(fields=['changed_by']),
        ]

    def __str__(self):
        return f"{self.teacher.name}: {self.old_position} -> {self.new_position}"

    def clean(self):
        """模型级验证"""
        if self.effective_date > timezone.now().date():
            raise ValidationError('生效日期不能大于当前日期')
        
        if self.old_position == self.new_position and self.old_college == self.new_college:
            raise ValidationError('职务和学院未发生变化')


class Permission(BaseModel):
    """权限模型"""
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text='权限代码'
    )
    name = models.CharField(
        max_length=100,
        help_text='权限名称'
    )
    module = models.CharField(
        max_length=50,
        help_text='所属模块'
    )
    description = models.TextField(
        blank=True,
        help_text='权限描述'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='是否启用'
    )

    class Meta:
        db_table = 'permissions'
        indexes = [
            models.Index(fields=['module']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.module}.{self.code}"