from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from datetime import datetime


class BaseModel(models.Model):
    """基础模型，包含公共字段"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class CollegeStatus(models.TextChoices):
    """学院状态枚举"""
    ACTIVE = 'active', '启用'
    INACTIVE = 'inactive', '停用'


class DurationType(models.TextChoices):
    """学制类型枚举"""
    THREE_YEAR = '3_year', '3年制'
    FIVE_YEAR = '5_year', '5年制'
    SIX_YEAR = '6_year', '6年制'


class Gender(models.TextChoices):
    """性别枚举"""
    MALE = 'male', '男'
    FEMALE = 'female', '女'


class PositionType(models.TextChoices):
    """职务类型枚举"""
    SUPER_ADMIN = 'super_admin', '超级管理员'
    PRINCIPAL = 'principal', '校长'
    VICE_PRINCIPAL = 'vice_principal', '副校长'
    DEAN = 'dean', '院长'
    VICE_DEAN = 'vice_dean', '副院长'
    HEAD_TEACHER = 'head_teacher', '班主任'
    TEACHER = 'teacher', '教师'


def validate_college_code(value):
    """验证学院代码格式（2位数字）"""
    if not re.match(r'^\d{2}$', value):
        raise ValidationError('学院代码必须为2位数字')


def validate_major_code(value):
    """验证专业代码格式（2位数字）"""
    if not re.match(r'^\d{2}$', value):
        raise ValidationError('专业代码必须为2位数字')


def validate_enrollment_year(value):
    """验证入学年份（4位数字，合理范围）"""
    current_year = timezone.now().year
    if not (2000 <= value <= current_year + 5):
        raise ValidationError(f'入学年份必须在2000-{current_year + 5}之间')


def validate_class_number(value):
    """验证班级ID（1位数字）"""
    if not (1 <= value <= 9):
        raise ValidationError('班级ID必须是1-9之间的数字')


def validate_contact_info(value):
    """验证联系方式格式"""
    if not isinstance(value, dict):
        raise ValidationError('联系方式必须是JSON格式')

    # 验证手机号格式
    if 'phone' in value and value['phone']:
        if not re.match(r'^1[3-9]\d{9}$', value['phone']):
            raise ValidationError('手机号格式不正确')

    # 验证邮箱格式
    if 'email' in value and value['email']:
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value['email']):
            raise ValidationError('邮箱格式不正确')


class College(BaseModel):
    """学院模型"""
    code = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_college_code],
        help_text='学院ID，2位数字，唯一标识'
    )
    name = models.CharField(max_length=100, help_text='学院名称')
    establishment_date = models.DateField(help_text='成立日期', default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=CollegeStatus.choices,
        default=CollegeStatus.ACTIVE,
        help_text='学院状态'
    )

    class Meta:
        db_table = 'colleges'
        indexes = [
            models.Index(fields=['code', 'name']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.code}-{self.name}"

    def clean(self):
        """模型级验证"""
        pass


class Major(BaseModel):
    """专业模型"""
    code = models.CharField(
        max_length=20,
        unique=True,
        validators=[validate_major_code],
        help_text='专业ID，2位数字，唯一标识'
    )
    name = models.CharField(max_length=100, help_text='专业名称')
    college = models.ForeignKey(
        College,
        on_delete=models.PROTECT,
        related_name='majors',
        help_text='所属学院'
    )
    duration_type = models.CharField(
        max_length=20,
        choices=DurationType.choices,
        default=DurationType.THREE_YEAR,
        help_text='学制类型'
    )

    class Meta:
        db_table = 'majors'
        indexes = [
            models.Index(fields=['college', 'duration_type']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.code}-{self.name}"

    def get_duration_label(self):
        """获取学制标签"""
        duration_labels = {
            DurationType.THREE_YEAR: 'Z3',
            DurationType.FIVE_YEAR: 'G5',
            DurationType.SIX_YEAR: 'J6',
        }
        return duration_labels.get(self.duration_type, '')

    def get_duration_number(self):
        """获取学制数字（用于班级ID）"""
        duration_numbers = {
            DurationType.THREE_YEAR: '3',
            DurationType.FIVE_YEAR: '5',
            DurationType.SIX_YEAR: '6',
        }
        return duration_numbers.get(self.duration_type, '3')


class Class(BaseModel):
    """班级模型"""
    class_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text='班级ID，格式：年级ID+学制数+学院ID+专业ID+班级序号'
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='班级名称，自动生成公式：年级ID+学院ID+班级ID'
    )
    major = models.ForeignKey(
        Major,
        on_delete=models.PROTECT,
        related_name='classes',
        help_text='所属专业'
    )
    enrollment_year = models.IntegerField(
        validators=[validate_enrollment_year],
        default=2024,
        help_text='年级ID（4位数字）'
    )
    head_teacher = models.OneToOneField(
        'personnel.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_classes',
        help_text='班主任'
    )
    class_number = models.IntegerField(
        validators=[validate_class_number],
        default=1,
        help_text='班级序号（1位数字）'
    )

    class Meta:
        db_table = 'classes'
        # 班级名称使用字段级唯一约束；联合唯一仅对 (major, enrollment_year, class_number)
        unique_together = [['major', 'enrollment_year', 'class_number']]
        indexes = [
            models.Index(fields=['major', 'enrollment_year']),
            models.Index(fields=['enrollment_year']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """自动生成班级ID和班级名称"""
        self.class_id = self.generate_class_id()
        self.name = self.generate_class_name()
        super().save(*args, **kwargs)

    def generate_class_id(self):
        """生成班级ID
        格式：年级ID(4位) + 学制数(1位) + 学院ID(2位) + 专业ID(2位) + 班级序号(1位，不补零)
        例如：2024301011 = 2024年 + 3年制 + 01学院 + 01专业 + 1班
              2024301019 = 2024年 + 3年制 + 01学院 + 01专业 + 9班
        """
        duration_number = self.major.get_duration_number()
        college_code = self.major.college.code
        major_code = self.major.code
        return f"{self.enrollment_year}{duration_number}{college_code}{major_code}{self.class_number}"

    def generate_class_name(self):
        """生成班级名称"""
        # 格式：2023年人工智能应用G5-1班
        # 包含：年级、专业名称、学制标签、班级序号
        duration_label = self.major.get_duration_label()
        return f"{self.enrollment_year}年{self.major.name}{duration_label}-{self.class_number}班"

    def update_class_info(self):
        """更新班级ID和名称"""
        self.class_id = self.generate_class_id()
        self.name = self.generate_class_name()
        self.save(update_fields=['class_id', 'name'])


class OperationLog(BaseModel):
    """操作日志模型"""
    OPERATION_TYPES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('import', '导入'),
        ('export', '导出'),
    ]

    user_id = models.IntegerField(help_text='操作人ID')
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES, help_text='操作类型')
    table_name = models.CharField(max_length=50, help_text='表名')
    record_id = models.CharField(max_length=50, help_text='记录ID')
    old_data = models.JSONField(default=dict, help_text='修改前数据')
    new_data = models.JSONField(default=dict, help_text='修改后数据')
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text='IP地址')
    user_agent = models.TextField(blank=True, help_text='用户代理')

    class Meta:
        db_table = 'operation_logs'
        indexes = [
            models.Index(fields=['user_id', 'operation_type']),
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user_id}-{self.operation_type}-{self.table_name}"


class SystemDictionary(BaseModel):
    """系统字典表"""
    dict_type = models.CharField(max_length=50, help_text='字典类型')
    dict_key = models.CharField(max_length=50, help_text='字典键')
    dict_value = models.CharField(max_length=100, help_text='字典值')
    sort_order = models.IntegerField(default=0, help_text='排序')
    is_active = models.BooleanField(default=True, help_text='是否启用')

    class Meta:
        db_table = 'system_dictionaries'
        unique_together = ['dict_type', 'dict_key']
        indexes = [
            models.Index(fields=['dict_type']),
            models.Index(fields=['dict_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.dict_type}-{self.dict_key}: {self.dict_value}"
