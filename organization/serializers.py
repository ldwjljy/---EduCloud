from rest_framework import serializers
from .models import College, Major, Class, SystemDictionary, OperationLog
from classrooms.models import Classroom

class ClassroomSerializer(serializers.ModelSerializer):
    building = serializers.CharField(source='location', read_only=True)
    room_number = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Classroom
        fields = ['id', 'name', 'location', 'capacity', 'status', 'building', 'room_number']

class CollegeSerializer(serializers.ModelSerializer):
    """学院序列化器"""
    major_count = serializers.SerializerMethodField()
    teacher_count = serializers.SerializerMethodField()
    
    class Meta:
        model = College
        fields = [
            'id', 'code', 'name', 'establishment_date', 'status',
            'major_count', 'teacher_count',
            'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_major_count(self, obj):
        """获取学院下的专业数量"""
        return obj.majors.filter(is_deleted=False).count()
    
    def get_teacher_count(self, obj):
        """获取学院下的教师数量"""
        return obj.teachers.filter(is_deleted=False).count()


class CollegeListSerializer(serializers.ModelSerializer):
    """学院列表序列化器（简化版）"""
    
    class Meta:
        model = College
        fields = ['id', 'code', 'name', 'status', 'establishment_date']


class MajorSerializer(serializers.ModelSerializer):
    """专业序列化器"""
    college_name = serializers.CharField(source='college.name', read_only=True)
    college_code = serializers.CharField(source='college.code', read_only=True)
    class_count = serializers.SerializerMethodField()
    duration_label = serializers.SerializerMethodField()
    
    class Meta:
        model = Major
        fields = [
            'id', 'code', 'name', 'college', 'college_name', 'college_code',
            'duration_type', 'duration_label', 'class_count',
            'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_class_count(self, obj):
        """获取专业下的班级数量"""
        return obj.classes.filter(is_deleted=False).count()
    
    def get_duration_label(self, obj):
        """获取学制标签"""
        return obj.get_duration_label()


class MajorListSerializer(serializers.ModelSerializer):
    """专业列表序列化器（简化版）"""
    college_name = serializers.CharField(source='college.name', read_only=True)
    duration_label = serializers.SerializerMethodField()
    
    class Meta:
        model = Major
        fields = ['id', 'code', 'name', 'college', 'college_name', 'duration_type', 'duration_label', 'is_deleted']
    
    def get_duration_label(self, obj):
        return obj.get_duration_label()


class ClassSerializer(serializers.ModelSerializer):
    """班级序列化器"""
    major_name = serializers.CharField(source='major.name', read_only=True)
    major_code = serializers.CharField(source='major.code', read_only=True)
    college_name = serializers.CharField(source='major.college.name', read_only=True)
    college_code = serializers.CharField(source='major.college.code', read_only=True)
    duration_type = serializers.CharField(source='major.duration_type', read_only=True)
    duration_label = serializers.SerializerMethodField()
    head_teacher_name = serializers.SerializerMethodField()
    head_teacher_employee_id = serializers.SerializerMethodField()
    
    grade_year = serializers.IntegerField(source='enrollment_year', read_only=True)
    department = serializers.IntegerField(source='major_id', read_only=True)

    class Meta:
        model = Class
        fields = [
            'id', 'class_id', 'name', 'major', 'department', 'major_name', 'major_code',
            'college_name', 'college_code', 'duration_type', 'duration_label',
            'enrollment_year', 'grade_year', 'class_number', 'head_teacher',
            'head_teacher_name', 'head_teacher_employee_id',
            'created_at', 'updated_at', 'is_deleted'
        ]
        read_only_fields = ['created_at', 'updated_at', 'class_id']
        
    def validate(self, data):
        """
        自定义验证逻辑，捕获唯一性约束错误并提供更友好的提示。
        DRF 的 unique_together 验证器通常会产生默认错误消息。
        我们可以在这里先检查一下，提供更好的消息。
        """
        # 注意：如果 class_number 是用来表示“数量”而不是“序号”，
        # 那么这里不需要校验唯一性，因为 view 会处理批量创建。
        # 但如果是 update 操作，或者是 create 单个班级（数量=1），
        # 这里的逻辑可能仍然适用，但也可能与 view 中的自动递增逻辑冲突。
        
        # 如果是创建操作，View 层会负责计算 class_number，这里可以跳过唯一性检查。
        if not self.instance:
            return data
            
        # 如果是更新操作，需要合并实例数据
        major = data.get('major')
        enrollment_year = data.get('enrollment_year')
        class_number = data.get('class_number')
        
        if not major: major = self.instance.major
        if not enrollment_year: enrollment_year = self.instance.enrollment_year
        if not class_number: class_number = self.instance.class_number
            
        # 检查唯一性约束: major + enrollment_year + class_number
        qs = Class.objects.filter(
            major=major,
            enrollment_year=enrollment_year,
            class_number=class_number
        )
        qs = qs.exclude(pk=self.instance.pk)
            
        if qs.exists():
            raise serializers.ValidationError(
                f"提交失败：该专业（{major.name}，ID={major.id}）{enrollment_year}级已存在序号为 {class_number} 的班级"
            )
            
        return data
    
    def get_duration_label(self, obj):
        """获取学制标签"""
        return obj.major.get_duration_label()
    
    def get_head_teacher_name(self, obj):
        """获取班主任姓名"""
        return obj.head_teacher.name if obj.head_teacher else None
    
    def get_head_teacher_employee_id(self, obj):
        """获取班主任工号"""
        return obj.head_teacher.employee_id if obj.head_teacher else None


class ClassListSerializer(serializers.ModelSerializer):
    """班级列表序列化器（简化版）"""
    major_name = serializers.CharField(source='major.name', read_only=True)
    duration_label = serializers.SerializerMethodField()
    head_teacher_name = serializers.SerializerMethodField()
    
    grade_year = serializers.IntegerField(source='enrollment_year', read_only=True)
    department = serializers.IntegerField(source='major_id', read_only=True)

    class Meta:
        model = Class
        fields = [
            'id', 'class_id', 'name', 'major', 'department', 'major_name', 'duration_label',
            'enrollment_year', 'grade_year', 'class_number', 'head_teacher', 'head_teacher_name'
        ]
    
    def get_duration_label(self, obj):
        return obj.major.get_duration_label()
    
    def get_head_teacher_name(self, obj):
        return obj.head_teacher.name if obj.head_teacher else None


class OrganizationTreeSerializer(serializers.Serializer):
    """组织架构树序列化器"""
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField(required=False)
    establishment_date = serializers.DateField(required=False)
    duration_type = serializers.CharField(required=False)
    duration_label = serializers.CharField(required=False)
    enrollment_year = serializers.IntegerField(required=False)
    class_number = serializers.IntegerField(required=False)
    head_teacher = serializers.DictField(required=False)
    children = serializers.ListField(child=serializers.DictField(), required=False)


class SystemDictionarySerializer(serializers.ModelSerializer):
    """系统字典序列化器"""
    
    class Meta:
        model = SystemDictionary
        fields = ['id', 'dict_type', 'dict_key', 'dict_value', 'sort_order', 'is_active']


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器"""
    username = serializers.SerializerMethodField()
    operation_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = OperationLog
        fields = [
            'id', 'user_id', 'username', 'operation_type', 'operation_type_display',
            'table_name', 'record_id', 'old_data', 'new_data',
            'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_username(self, obj):
        """获取用户名"""
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=obj.user_id)
            return user.username
        except User.DoesNotExist:
            return None
    
    def get_operation_type_display(self, obj):
        """获取操作类型显示名称"""
        operation_types = dict(OperationLog.OPERATION_TYPES)
        return operation_types.get(obj.operation_type, obj.operation_type)


class CollegeCreateSerializer(serializers.ModelSerializer):
    """学院创建序列化器"""
    class Meta:
        model = College
        fields = ['code', 'name', 'establishment_date', 'status']
        extra_kwargs = {
            'code': {'required': False},
            'establishment_date': {'required': False},
            'status': {'required': False},
        }

    def validate_code(self, value):
        """验证学院代码"""
        if value and College.objects.filter(code=value, is_deleted=False).exists():
            raise serializers.ValidationError('学院代码已存在')
        return value

    def create(self, validated_data):
        from django.utils import timezone
        import re
        code = validated_data.get('code')
        if not code:
            # 自动生成2位数字代码
            existing = College.objects.filter(is_deleted=False).values_list('code', flat=True)
            nums = [int(c) for c in existing if isinstance(c, str) and re.fullmatch(r"\d{2}", c)]
            next_num = (max(nums) + 1) if nums else 1
            code = f"{next_num:02d}"
            validated_data['code'] = code
        if 'establishment_date' not in validated_data or not validated_data.get('establishment_date'):
            validated_data['establishment_date'] = timezone.now().date()
        if 'status' not in validated_data or not validated_data.get('status'):
            validated_data['status'] = 'active'
        return College.objects.create(**validated_data)


class MajorCreateSerializer(serializers.ModelSerializer):
    """专业创建序列化器"""
    class Meta:
        model = Major
        fields = ['code', 'name', 'college', 'duration_type']
        validators = []
    
    def validate_code(self, value):
        """验证专业代码"""
        # 如果code为空字符串或None，返回None（表示不提供代码，将自动生成）
        if not value or (isinstance(value, str) and not value.strip()):
            return None
        return value

    def validate(self, data):
        college = data.get('college')
        if not college:
            raise serializers.ValidationError({'college': '所属学院必填'})
        code = data.get('code')
        if code:
            if len(code) != 2 or not code.isdigit():
                raise serializers.ValidationError({'code': '专业代码必须为2位数字'})
            
            # 验证全局唯一性 (根据用户要求：专业ID（2位数字，唯一标识）)
            if Major.objects.filter(code=code, is_deleted=False).exists():
                raise serializers.ValidationError({'code': f'已存在代码为 {code} 的专业'})
        return data

    def create(self, validated_data):
        code = validated_data.get('code')
        if not code:
            # 自动生成2位数字代码
            existing_codes = Major.objects.filter(is_deleted=False).values_list('code', flat=True)
            nums = [int(c) for c in existing_codes if isinstance(c, str) and c.isdigit() and len(c) == 2]
            next_num = (max(nums) + 1) if nums else 1
            code = f"{next_num:02d}"    
            while Major.objects.filter(code=code, is_deleted=False).exists():
                next_num += 1
                code = f"{next_num:02d}"    
            validated_data['code'] = code
        if not validated_data.get('duration_type'):
            from .models import DurationType
            validated_data['duration_type'] = DurationType.THREE_YEAR
        return Major.objects.create(**validated_data)


class ClassCreateSerializer(serializers.ModelSerializer):
    """班级创建序列化器"""
    
    class Meta:
        model = Class
        fields = ['major', 'enrollment_year', 'class_number', 'head_teacher']
    
    def validate(self, data):
        """验证班级数据"""
        # 验证班主任是否已管理其他班级
        if data.get('head_teacher'):
            existing_class = Class.objects.filter(
                head_teacher=data['head_teacher'],
                is_deleted=False
            ).first()
            
            if existing_class:
                raise serializers.ValidationError(f'该教师已是班级 "{existing_class.name}" 的班主任')
        
        return data
