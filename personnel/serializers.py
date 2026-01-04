from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Teacher, Role, UserRole, TeacherPositionHistory, Permission
from organization.models import College, Major, Class


class TeacherSerializer(serializers.ModelSerializer):
    """教师序列化器"""
    college_name = serializers.CharField(source='college.name', read_only=True)
    managed_class_name = serializers.CharField(source='managed_class.name', read_only=True)
    contact_phone = serializers.SerializerMethodField()
    contact_email = serializers.SerializerMethodField()
    managed_majors_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'name', 'gender', 'contact_info', 'contact_phone', 'contact_email',
            'hire_date', 'position_type', 'college', 'college_name', 'managed_majors',
            'managed_majors_info', 'managed_class', 'managed_class_name',
            'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_contact_phone(self, obj):
        return obj.get_contact_phone()
    
    def get_contact_email(self, obj):
        return obj.get_contact_email()
    
    def get_managed_majors_info(self, obj):
        """获取管辖专业的详细信息"""
        majors = obj.get_managed_majors_list()
        return [
            {
                'id': major.id,
                'code': major.code,
                'name': major.name,
                'college_name': major.college.name
            }
            for major in majors
        ]
    
    def validate_contact_info(self, value):
        """验证联系方式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('联系方式必须是对象格式')
        
        # 验证手机号
        if 'phone' in value and value['phone']:
            import re
            if not re.match(r'^1[3-9]\d{9}$', value['phone']):
                raise serializers.ValidationError('手机号格式不正确')
        
        # 验证邮箱
        if 'email' in value and value['email']:
            import re
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value['email']):
                raise serializers.ValidationError('邮箱格式不正确')
        
        return value
    
    def validate_managed_majors(self, value):
        """验证管辖专业"""
        if not isinstance(value, list):
            raise serializers.ValidationError('管辖专业必须是列表格式')
        
        # 验证专业ID是否存在
        if value:
            existing_ids = set(Major.objects.filter(
                id__in=value,
                is_deleted=False
            ).values_list('id', flat=True))
            
            invalid_ids = set(value) - existing_ids
            if invalid_ids:
                raise serializers.ValidationError(f'以下专业ID不存在：{invalid_ids}')
        
        return value
    
    def validate(self, data):
        """模型级验证"""
        # 验证院长唯一性
        if data.get('position_type') == 'dean' and data.get('college'):
            existing_dean = Teacher.objects.filter(
                college=data['college'],
                position_type='dean',
                is_deleted=False
            ).exclude(employee_id=self.instance.employee_id if self.instance else None).first()
            
            if existing_dean:
                raise serializers.ValidationError(f'学院 "{data["college"].name}" 已存在院长：{existing_dean.name}')
        
        return data


class TeacherListSerializer(serializers.ModelSerializer):
    """教师列表序列化器（简化版）"""
    college_name = serializers.CharField(source='college.name', read_only=True)
    managed_class_name = serializers.CharField(source='managed_class.name', read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'name', 'gender', 'position_type',
            'college', 'college_name', 'managed_class', 'managed_class_name',
            'hire_date', 'is_deleted'
        ]


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'permissions', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserRoleSerializer(serializers.ModelSerializer):
    """用户角色关联序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'username', 'role', 'role_name', 'assigned_by', 'assigned_by_username', 'assigned_at', 'is_deleted']
        read_only_fields = ['assigned_at']


class TeacherPositionHistorySerializer(serializers.ModelSerializer):
    """教师职务变更历史序列化器"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    teacher_employee_id = serializers.CharField(source='teacher.employee_id', read_only=True)
    old_college_name = serializers.CharField(source='old_college.name', read_only=True)
    new_college_name = serializers.CharField(source='new_college.name', read_only=True)
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = TeacherPositionHistory
        fields = [
            'id', 'teacher', 'teacher_name', 'teacher_employee_id',
            'old_position', 'new_position', 'old_college', 'old_college_name',
            'new_college', 'new_college_name', 'change_reason', 'changed_by',
            'changed_by_username', 'effective_date', 'created_at'
        ]
        read_only_fields = ['created_at']


class PermissionSerializer(serializers.ModelSerializer):
    """权限序列化器"""
    
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'module', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class TeacherCreateSerializer(serializers.ModelSerializer):
    """教师创建序列化器"""
    
    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'name', 'gender', 'contact_info',
            'hire_date', 'position_type', 'college', 'managed_majors', 'managed_class'
        ]
    
    def create(self, validated_data):
        """创建教师记录"""
        teacher = super().create(validated_data)
        
        # 记录职务变更历史
        if validated_data.get('position_type') or validated_data.get('college'):
            TeacherPositionHistory.objects.create(
                teacher=teacher,
                new_position=validated_data.get('position_type'),
                new_college=validated_data.get('college'),
                changed_by=self.context['request'].user,
                effective_date=timezone.now().date()
            )
        
        return teacher


class TeacherUpdateSerializer(serializers.ModelSerializer):
    """教师更新序列化器"""
    
    class Meta:
        model = Teacher
        fields = [
            'name', 'gender', 'contact_info', 'hire_date',
            'position_type', 'college', 'managed_majors', 'managed_class'
        ]
    
    def update(self, instance, validated_data):
        """更新教师记录"""
        old_position = instance.position_type
        old_college = instance.college
        
        # 更新数据
        teacher = super().update(instance, validated_data)
        
        # 记录职务变更历史
        if (validated_data.get('position_type') != old_position or 
            validated_data.get('college') != old_college):
            TeacherPositionHistory.objects.create(
                teacher=teacher,
                old_position=old_position,
                new_position=validated_data.get('position_type', old_position),
                old_college=old_college,
                new_college=validated_data.get('college', old_college),
                changed_by=self.context['request'].user,
                effective_date=timezone.now().date()
            )
        
        return teacher