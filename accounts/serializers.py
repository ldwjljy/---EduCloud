from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from .models import UserProfile, StudentProfile, TeacherProfile, AdministratorProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'avatar_url', 'phone', 'address']


class StudentProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user_profile.user.first_name', read_only=True)
    name_write = serializers.CharField(write_only=True, required=False)  # 用于写入
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    gender = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)  # 用于写入性别
    gender_display = serializers.CharField(source='user_profile.get_gender_display', read_only=True)  # 用于读取性别显示
    student_id = serializers.CharField(read_only=True)  # 学号只读，自动生成
    college_name = serializers.CharField(source='school_class.major.college.name', read_only=True)
    major_name = serializers.CharField(source='school_class.major.name', read_only=True)
    class_name = serializers.CharField(source='school_class.name', read_only=True)
    user_profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = ['id', 'user_profile', 'student_id', 'school_class', 'status', 'name', 'name_write', 'phone', 'gender', 'gender_display', 'college_name', 'major_name', 'class_name', 'dorm_number']
        extra_kwargs = {
            'school_class': {'required': True},
            'status': {'required': False},
            'dorm_number': {'required': False},
        }

    def validate(self, data):
        """验证必填字段"""
        if self.instance is None and not data.get('school_class'): # Only on create
            raise serializers.ValidationError({'school_class': '必须选择班级'})
        if self.instance is None and not data.get('name_write'): # Only on create
             raise serializers.ValidationError({'name_write': '必须填写姓名'})
        return data

    def validate_phone(self, value):
        if not value:
            return value
        if value == '无':
            return value
        
        import re
        if not re.match(r'^1[3-9]\d{9}$', value):
             raise serializers.ValidationError('手机号格式不正确，请输入有效的11位手机号或填写“无”')
        return value

    def validate_teacher_id(self, value):
        import re
        if not re.match(r'^[a-zA-Z0-9]+$', value):
            raise serializers.ValidationError('工号只能包含数字和字母')
        return value

    def create(self, validated_data):
        name = validated_data.pop('name_write')
        phone = validated_data.pop('phone', '')
        gender = validated_data.pop('gender', '')
        school_class = validated_data.get('school_class')
        
        if not school_class:
            raise serializers.ValidationError({'school_class': '必须选择班级'})
        
        # 自动生成学号：年级（4位）+ 学制类型数（1位）+ 学院ID（2位）+ 专业ID（2位）+ 班级ID（1位）+ 序号（2位）
        enrollment_year = school_class.enrollment_year  # 年级ID（4位数字）
        
        # 从学制类型中提取数字（如 '3_year' -> '3', '5_year' -> '5', '6_year' -> '6'）
        duration_type = school_class.major.duration_type
        duration_number = duration_type.split('_')[0] if '_' in duration_type else '3'  # 默认3年制
        
        college_code = school_class.major.college.code  # 学院ID（2位数字）
        major_code = school_class.major.code  # 专业ID（2位数字）
        class_number = school_class.class_number  # 班级ID（1位数字）
        
        # 生成学号前缀：年级+学制类型数+学院ID+专业ID+班级ID
        prefix = f"{enrollment_year}{duration_number}{college_code}{major_code}{class_number}"
        
        # 查找该班级下已有的学生，确定下一个序号
        existing_students = StudentProfile.objects.filter(school_class=school_class)
        # 提取已有的序号（学号的后两位）
        existing_numbers = []
        
        for student in existing_students:
            if student.student_id.startswith(prefix) and len(student.student_id) == len(prefix) + 2:
                try:
                    num = int(student.student_id[-2:])
                    existing_numbers.append(num)
                except ValueError:
                    pass
        
        # 找到下一个可用的序号（从01开始）
        next_num = 1
        while next_num in existing_numbers:
            next_num += 1
            if next_num > 99:  # 最多99个学生
                raise serializers.ValidationError({'school_class': '该班级学生数量已达上限（99人）'})
        
        # 生成学号
        student_id = f"{prefix}{next_num:02d}"
        
        # 确保学号唯一性（检查 User 表，因为 username 必须唯一）
        while User.objects.filter(username=student_id).exists():
            next_num += 1
            if next_num > 99:
                raise serializers.ValidationError({'school_class': '该班级学生数量已达上限（99人）'})
            student_id = f"{prefix}{next_num:02d}"
        
        validated_data['student_id'] = student_id
        
        with transaction.atomic():
            # Create User (username=student_id, password=123456)
            # 自动检查学生是否有账户没有就要创建，账号为学号，密码默认123456
            try:
                user = User.objects.get(username=student_id)
                # 如果用户已存在，更新姓名
                user.first_name = name
                user.save()
            except User.DoesNotExist:
                user = User.objects.create_user(username=student_id, password='123456', first_name=name)
            
            # Create UserProfile
            user_profile, created = UserProfile.objects.get_or_create(
                user=user, 
                defaults={'role': 'student', 'phone': phone, 'gender': gender}
            )
            if not created:
                user_profile.role = 'student'
                if phone:
                    user_profile.phone = phone
                if gender:
                    user_profile.gender = gender
                user_profile.save()
            
            # 设置创建者（如果有request.user）
            request = self.context.get('request')
            if request and request.user and request.user.is_authenticated:
                validated_data['created_by'] = request.user
            
            # Create StudentProfile
            student_profile = StudentProfile.objects.create(user_profile=user_profile, **validated_data)
        
        return student_profile

    def update(self, instance, validated_data):
        if 'name' in validated_data:
            instance.user_profile.user.first_name = validated_data.pop('name')
            instance.user_profile.user.save()
        if 'phone' in validated_data:
            instance.user_profile.phone = validated_data.pop('phone')
            instance.user_profile.save()
        if 'gender' in validated_data:
            instance.user_profile.gender = validated_data.pop('gender')
            instance.user_profile.save()
        return super().update(instance, validated_data)


class TeacherProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    name_display = serializers.CharField(source='user_profile.user.first_name', read_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    role = serializers.CharField(write_only=True)
    class_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    college_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    college_name = serializers.CharField(source='department.college.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    user_profile = UserProfileSerializer(read_only=True)
    managed_class_info = serializers.SerializerMethodField()
    position_type = serializers.SerializerMethodField()  # 从 personnel.Teacher 获取职务类型
    position_type_display = serializers.SerializerMethodField()  # 职务类型的中文显示

    class Meta:
        model = TeacherProfile
        fields = ['id', 'user_profile', 'teacher_id', 'title', 'position_type', 'position_type_display', 'department', 'subject', 'name', 'name_display', 'phone', 'role', 'class_id', 'college_id', 'college_name', 'department_name', 'managed_class_info']
    
    def get_position_type(self, obj):
        """从 personnel.Teacher 获取职务类型"""
        from personnel.models import Teacher
        try:
            personnel_teacher = Teacher.objects.get(employee_id=obj.teacher_id, is_deleted=False)
            return personnel_teacher.position_type
        except Teacher.DoesNotExist:
            return obj.title or obj.user_profile.role  # 如果找不到，使用 title 或 role 作为后备
    
    def get_position_type_display(self, obj):
        """获取职务类型的中文显示"""
        position_type = self.get_position_type(obj)
        position_type_map = {
            'super_admin': '超级管理员',
            'principal': '校长',
            'vice_principal': '副校长',
            'dean': '院长',
            'vice_dean': '副院长',
            'head_teacher': '班主任',
            'teacher': '教师'
        }
        return position_type_map.get(position_type, position_type or '-')

    def get_managed_class_info(self, obj):
        from personnel.models import Teacher
        from organization.models import Class
        try:
            # TeacherProfile.teacher_id matches Personnel.Teacher.employee_id
            personnel_teacher = Teacher.objects.get(employee_id=obj.teacher_id)
            
            # Use reverse relationship from Class to Teacher (related_name='managed_classes' on Class.head_teacher)
            # Or direct query on Class model
            managed_class = Class.objects.filter(head_teacher=personnel_teacher).first()
            
            if managed_class:
                return {
                    'id': managed_class.id,
                    'name': managed_class.name
                }
        except Teacher.DoesNotExist:
            pass
        return None
    
    def validate(self, data):
        """
        验证不同角色的必填字段要求：
        1. 教师（teacher）: 必填：工号、姓名；可选：学院-专业、联系电话
        2. 班主任（head_teacher）: 必填：工号、姓名、学院-专业、联系电话
        3. 院长/副院长（dean/vice_dean）: 必填：工号、姓名、学院；可选：专业、联系电话
        4. 校长（principal）: 必填：工号、姓名；可选：学院-专业、联系电话
        """
        role = data.get('role')
        is_create = self.instance is None
        
        # 工号和姓名在所有角色都是必填的
        if is_create:
            if not data.get('teacher_id'):
                raise serializers.ValidationError({'teacher_id': '工号是必填项'})
            if not data.get('name'):
                raise serializers.ValidationError({'name': '姓名是必填项'})
        
        # 班主任：必须填写学院-专业、联系电话、班级
        if role == 'head_teacher':
            if not data.get('department'):
                raise serializers.ValidationError({'department': '班主任必须选择专业'})
            if not data.get('phone'):
                raise serializers.ValidationError({'phone': '班主任必须填写联系电话'})
            if is_create and not data.get('class_id'):
                raise serializers.ValidationError({'class_id': '班主任必须选择管理的班级'})
        
        # 院长/副院长：必须填写学院
        if role in ['dean', 'vice_dean']:
            # 院长/副院长至少需要学院，专业可选
            if not data.get('department') and not data.get('college_id'):
                raise serializers.ValidationError({'college_id': '院长/副院长必须选择学院'})
        
        # 校长和普通教师：学院-专业和联系电话都是可选的，无需额外验证
        
        return data

    def create(self, validated_data):
        name = validated_data.pop('name')
        phone = validated_data.pop('phone', '')
        role = validated_data.pop('role')
        class_id = validated_data.pop('class_id', None)
        college_id = validated_data.pop('college_id', None)
        teacher_id = validated_data['teacher_id']
        
        # Check if user exists
        if User.objects.filter(username=teacher_id).exists():
            raise serializers.ValidationError({'teacher_id': '该工号已存在'})

        user = User.objects.create_user(username=teacher_id, password=teacher_id, first_name=name)
        user_profile = UserProfile.objects.create(user=user, role=role, phone=phone or '')
        teacher_profile = TeacherProfile.objects.create(user_profile=user_profile, **validated_data)
        
        # 同步创建/更新 Personnel Teacher
        from personnel.models import Teacher as PersonnelTeacher
        from organization.models import Gender, College
        from django.utils import timezone
        
        department = validated_data.get('department')
        college = department.college if department else None
        
        # 如果没有专业但有学院ID（院长/副院长可能只填学院），使用college_id
        if not college and college_id:
            try:
                college = College.objects.get(id=college_id)
            except College.DoesNotExist:
                pass
        
        personnel_teacher, created = PersonnelTeacher.objects.get_or_create(
            employee_id=teacher_id,
            defaults={
                'user': user,
                'name': name,
                'college': college,
                'position_type': role,
                'hire_date': timezone.now().date(),
                'gender': Gender.MALE, # 默认为男，因为表单没有性别选项
            }
        )
        
        if not created:
            personnel_teacher.user = user
            personnel_teacher.name = name
            personnel_teacher.college = college
            personnel_teacher.position_type = role
            personnel_teacher.save()

        if role == 'head_teacher' and class_id:
            from organization.models import Class
            try:
                cls = Class.objects.get(id=class_id)
                cls.head_teacher = personnel_teacher
                cls.save()
            except Class.DoesNotExist:
                pass
                
        return teacher_profile

    def update(self, instance, validated_data):
        if 'name' in validated_data:
            instance.user_profile.user.first_name = validated_data.pop('name')
            instance.user_profile.user.save()
        if 'phone' in validated_data:
            instance.user_profile.phone = validated_data.pop('phone') or ''
            instance.user_profile.save()
        if 'role' in validated_data:
            instance.user_profile.role = validated_data.pop('role')
            instance.user_profile.save()
            
        # 同步更新 Personnel Teacher
        from personnel.models import Teacher as PersonnelTeacher
        from organization.models import Gender, College
        from django.utils import timezone
        
        college_id = validated_data.pop('college_id', None)
        department = validated_data.get('department', instance.department)
        college = department.college if department else None
        
        # 如果没有专业但有学院ID（院长/副院长可能只填学院），使用college_id
        if not college and college_id:
            try:
                college = College.objects.get(id=college_id)
            except College.DoesNotExist:
                pass
        
        try:
            personnel_teacher = PersonnelTeacher.objects.get(employee_id=instance.teacher_id)
            personnel_teacher.name = instance.user_profile.user.first_name
            personnel_teacher.position_type = instance.user_profile.role
            personnel_teacher.college = college
            personnel_teacher.save()
        except PersonnelTeacher.DoesNotExist:
             personnel_teacher = PersonnelTeacher.objects.create(
                employee_id=instance.teacher_id,
                user=instance.user_profile.user,
                name=instance.user_profile.user.first_name,
                college=college,
                position_type=instance.user_profile.role,
                hire_date=timezone.now().date(),
                gender=Gender.MALE
             )
        
        if 'class_id' in validated_data:
            class_id = validated_data.pop('class_id')
            from organization.models import Class
            # 清除旧的班主任关联
            Class.objects.filter(head_teacher=personnel_teacher).update(head_teacher=None)
            if class_id:
                try:
                    cls = Class.objects.get(id=class_id)
                    cls.head_teacher = personnel_teacher
                    cls.save()
                except Class.DoesNotExist:
                    pass

        return super().update(instance, validated_data)


class AdministratorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdministratorProfile
        fields = ['id', 'user_profile', 'position']
