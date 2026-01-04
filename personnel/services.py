from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Teacher, TeacherPositionHistory
from organization.models import College, Major, Class
try:
    from accounts.models import UserProfile, TeacherProfile
except ImportError:
    UserProfile = None
    TeacherProfile = None


class TeacherService:
    """教师业务逻辑服务类"""
    
    def _ensure_user_account(self, teacher):
        """确保教师有用户账户，如果没有则自动创建"""
        if not teacher.user:
            # 检查是否已存在相同用户名的用户
            username = teacher.employee_id
            try:
                user = User.objects.get(username=username)
                # 如果用户已存在，更新姓名和邮箱
                user.first_name = teacher.name
                email = teacher.get_contact_email()
                if email:
                    user.email = email
                user.save()
            except User.DoesNotExist:
                # 创建新用户，默认密码为123456
                user = User.objects.create_user(
                    username=username,
                    password='123456',  # 默认密码为123456
                    first_name=teacher.name,
                    email=teacher.get_contact_email() or ''
                )
            
            # 关联用户到教师
            teacher.user = user
            teacher.save(update_fields=['user'])
            
            # 创建或更新 UserProfile
            if UserProfile:
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': teacher.position_type,
                        'phone': teacher.get_contact_phone() or ''
                    }
                )
                if not created:
                    # 更新现有profile
                    profile.role = teacher.position_type
                    if teacher.get_contact_phone():
                        profile.phone = teacher.get_contact_phone()
                    profile.save()
            
            # 创建或更新 TeacherProfile
            if TeacherProfile and UserProfile:
                try:
                    profile = UserProfile.objects.get(user=user)
                    TeacherProfile.objects.update_or_create(
                        user_profile=profile,
                        defaults={'teacher_id': teacher.employee_id}
                    )
                except UserProfile.DoesNotExist:
                    pass
    
    @transaction.atomic
    def create_teacher(self, validated_data, created_by):
        """创建教师记录"""
        # 创建教师对象
        teacher = Teacher.objects.create(**validated_data)
        
        # 自动创建用户账户（如果不存在）
        self._ensure_user_account(teacher)
        
        # 记录职务变更历史
        if validated_data.get('position_type') or validated_data.get('college'):
            TeacherPositionHistory.objects.create(
                teacher=teacher,
                new_position=validated_data.get('position_type'),
                new_college=validated_data.get('college'),
                changed_by=created_by,
                effective_date=timezone.now().date(),
                change_reason='新建教师记录'
            )
        
        # 处理班级班主任关联
        if validated_data.get('managed_class'):
            self._update_class_head_teacher(teacher, validated_data['managed_class'])
        
        # 同步关联用户的角色
        self._sync_user_role(teacher)

        return teacher
    
    @transaction.atomic
    def update_teacher(self, instance, validated_data, updated_by):
        """更新教师记录"""
        old_position = instance.position_type
        old_college = instance.college
        old_managed_class = instance.managed_class
        
        # 更新数据
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 自动创建用户账户（如果不存在）
        self._ensure_user_account(instance)
        
        # 记录职务变更历史
        if (validated_data.get('position_type') != old_position or 
            validated_data.get('college') != old_college):
            TeacherPositionHistory.objects.create(
                teacher=instance,
                old_position=old_position,
                new_position=validated_data.get('position_type', old_position),
                old_college=old_college,
                new_college=validated_data.get('college', old_college),
                changed_by=updated_by,
                effective_date=timezone.now().date()
            )
        
        # 处理班级班主任关联变更
        new_managed_class = validated_data.get('managed_class')
        if new_managed_class != old_managed_class:
            # 移除旧的班主任关联
            if old_managed_class and old_managed_class.head_teacher == instance:
                old_managed_class.head_teacher = None
                old_managed_class.save()
            
            # 设置新的班主任关联
            if new_managed_class:
                self._update_class_head_teacher(instance, new_managed_class)
        
        # 同步关联用户的角色
        self._sync_user_role(instance)

        return instance
    
    @transaction.atomic
    def change_teacher_position(self, teacher, new_position, new_college_id=None, change_reason='', changed_by=None):
        """变更教师职务，含状态机与唯一性约束"""
        if not new_position:
            raise ValueError('新职务不能为空')
        allowed = {
            'teacher': {'head_teacher', 'vice_dean'},
            'head_teacher': {'teacher', 'vice_dean'},
            'vice_dean': {'dean', 'teacher', 'head_teacher'},
            'dean': {'vice_dean'},
            'super_admin': {'dean', 'vice_dean', 'teacher', 'head_teacher'}
        }
        current = teacher.position_type or 'teacher'
        if current in allowed and new_position not in allowed[current]:
            raise ValueError('非法职务流转')
        old_position = teacher.position_type
        old_college = teacher.college
        new_college = None
        if new_college_id:
            try:
                new_college = College.objects.get(id=new_college_id, is_deleted=False)
            except College.DoesNotExist:
                raise ValueError(f'学院ID {new_college_id} 不存在')
        if new_position == 'dean':
            target_college = new_college or teacher.college
            if not target_college:
                raise ValueError('院长必须关联学院')
            exists = Teacher.objects.filter(college=target_college, position_type='dean', is_deleted=False).exclude(employee_id=teacher.employee_id).exists()
            if exists:
                raise ValueError('该学院已存在院长')
        teacher.position_type = new_position
        if new_college:
            teacher.college = new_college
        teacher.save()
        
        # 确保用户账户存在
        self._ensure_user_account(teacher)
        
        TeacherPositionHistory.objects.create(
            teacher=teacher,
            old_position=old_position,
            new_position=new_position,
            old_college=old_college,
            new_college=new_college or teacher.college,
            changed_by=changed_by,
            effective_date=timezone.now().date(),
            change_reason=change_reason
        )
        try:
            from organization.models import OperationLog
            OperationLog.objects.create(
                user_id=getattr(changed_by, 'id', None) or 0,
                operation_type='update',
                table_name='teachers',
                record_id=str(teacher.employee_id),
                old_data={'position_type': old_position, 'college_id': getattr(old_college, 'id', None)},
                new_data={'position_type': new_position, 'college_id': getattr(teacher.college, 'id', None)}
            )
        except Exception:
            pass
            
        # 同步关联用户的角色
        self._sync_user_role(teacher)
        
        return teacher
    
    def _sync_user_role(self, teacher):
        """同步用户的角色和Profile"""
        if teacher.user and UserProfile:
            # Sync UserProfile Role
            profile, created = UserProfile.objects.get_or_create(user=teacher.user)
            if profile.role != teacher.position_type:
                profile.role = teacher.position_type
                profile.save()
            
            # Sync TeacherProfile
            if TeacherProfile:
                # Check if TeacherProfile exists for this teacher_id to avoid duplicates if user changed
                # Ideally teacher_id is unique.
                
                defaults = {
                    'teacher_id': teacher.employee_id,
                }
                
                # If managed_majors has 1 item, we might map it to department?
                # But for now, leave department null as it's a College vs Major mismatch usually.
                
                tp, tp_created = TeacherProfile.objects.update_or_create(
                    user_profile=profile,
                    defaults=defaults
                )
    
    @transaction.atomic
    def delete_teacher(self, teacher, deleted_by):
        """删除教师记录（软删除）"""
        # 保存用户引用，以便后续删除
        user = teacher.user
        
        # 先断开用户关联，避免 CASCADE 导致硬删除
        teacher.user = None
        teacher.is_deleted = True
        teacher.save()
        
        # 移除相关关联
        if teacher.managed_class:
            teacher.managed_class.head_teacher = None
            teacher.managed_class.save()
        
        # 删除关联的用户账户
        if user:
            user.delete()
        
        # 记录操作日志
        # TODO: 实现操作日志记录
        
        return teacher
    
    def _update_class_head_teacher(self, teacher, school_class):
        """更新班级班主任关联"""
        # 检查班级是否存在
        if not isinstance(school_class, Class):
            try:
                school_class = Class.objects.get(id=school_class, is_deleted=False)
            except Class.DoesNotExist:
                raise ValidationError(f'班级不存在')
        
        # 检查该班级是否已有班主任
        if school_class.head_teacher and school_class.head_teacher != teacher:
            raise ValidationError(f'班级 "{school_class.name}" 已有班主任：{school_class.head_teacher.name}')
        
        # 设置班主任
        school_class.head_teacher = teacher
        school_class.save()
    
    def validate_teacher_data(self, data, instance=None):
        """验证教师数据"""
        errors = {}
        
        # 验证院长唯一性
        if data.get('position_type') == 'dean' and data.get('college'):
            existing_dean = Teacher.objects.filter(
                college=data['college'],
                position_type='dean',
                is_deleted=False
            )
            
            if instance:
                existing_dean = existing_dean.exclude(employee_id=instance.employee_id)
            
            if existing_dean.exists():
                errors['position_type'] = f'学院 "{data["college"].name}" 已存在院长：{existing_dean.first().name}'
        
        # 验证班主任班级关联
        if data.get('managed_class'):
            school_class = data['managed_class']
            if school_class.head_teacher and (not instance or school_class.head_teacher != instance):
                errors['managed_class'] = f'班级 "{school_class.name}" 已有班主任：{school_class.head_teacher.name}'
        
        # 验证管辖专业
        if data.get('managed_majors'):
            if not isinstance(data['managed_majors'], list):
                errors['managed_majors'] = '管辖专业必须是列表格式'
            else:
                existing_major_ids = set(Major.objects.filter(
                    id__in=data['managed_majors'],
                    is_deleted=False
                ).values_list('id', flat=True))
                
                invalid_ids = set(data['managed_majors']) - existing_major_ids
                if invalid_ids:
                    errors['managed_majors'] = f'以下专业ID不存在：{invalid_ids}'
        
        if errors:
            raise ValidationError(errors)
        
        return True


class RoleService:
    """角色业务逻辑服务类"""
    
    def get_user_permissions(self, user):
        """获取用户权限列表"""
        if not hasattr(user, 'teacher_profile'):
            return []
        
        teacher = user.teacher_profile
        permissions = set()
        
        # 根据职务类型添加权限
        if teacher.position_type == 'super_admin':
            permissions.update(['*'])  # 所有权限
        elif teacher.position_type == 'dean':
            permissions.update([
                'college.view', 'college.update',
                'major.*',
                'class.*',
                'teacher.view', 'teacher.create', 'teacher.update', 'teacher.delete',
                'student.view', 'student.create', 'student.update', 'student.delete'
            ])
        elif teacher.position_type == 'vice_dean':
            permissions.update([
                'college.view',
                'major.view', 'major.create', 'major.update',
                'class.view', 'class.create', 'class.update',
                'teacher.view', 'teacher.create', 'teacher.update',
                'student.view', 'student.create', 'student.update'
            ])
        elif teacher.position_type == 'head_teacher':
            permissions.update([
                'class.view',
                'teacher.view',
                'student.view', 'student.create', 'student.update'
            ])
        elif teacher.position_type == 'teacher':
            permissions.update([
                'teacher.view',
                'student.view'
            ])
        
        return list(permissions)
    
    def check_permission(self, user, permission_code):
        """检查用户是否有指定权限"""
        user_permissions = self.get_user_permissions(user)
        
        # 超级管理员有所有权限
        if '*' in user_permissions:
            return True
        
        return permission_code in user_permissions


class OrganizationService:
    """组织架构业务逻辑服务类"""
    
    def get_organization_tree(self, college_id=None):
        """获取组织架构树"""
        from organization.models import College, Major, Class
        
        if college_id:
            colleges = College.objects.filter(id=college_id, is_deleted=False)
        else:
            colleges = College.objects.filter(is_deleted=False)
        
        tree_data = []
        
        for college in colleges:
            college_data = {
                'id': college.id,
                'code': college.code,
                'name': college.name,
                'type': 'college',
                'status': college.status,
                'establishment_date': college.establishment_date,
                'children': []
            }
            
            # 获取学院下的专业
            majors = Major.objects.filter(college=college, is_deleted=False)
            
            for major in majors:
                major_data = {
                    'id': major.id,
                    'code': major.code,
                    'name': major.name,
                    'type': 'major',
                    'duration_type': major.duration_type,
                    'duration_label': major.get_duration_label(),
                    'children': []
                }
                
                # 获取专业下的班级
                classes = Class.objects.filter(major=major, is_deleted=False)
                
                for school_class in classes:
                    class_data = {
                        'id': school_class.id,
                        'name': school_class.name,
                        'type': 'class',
                        'enrollment_year': school_class.enrollment_year,
                        'class_number': school_class.class_number,
                        'head_teacher': {
                            'id': school_class.head_teacher.employee_id if school_class.head_teacher else None,
                            'name': school_class.head_teacher.name if school_class.head_teacher else None
                        } if school_class.head_teacher else None
                    }
                    major_data['children'].append(class_data)
                
                college_data['children'].append(major_data)
            
            tree_data.append(college_data)
        
        return tree_data
    
    def validate_organization_hierarchy(self, college_id=None, major_id=None, class_id=None):
        """验证组织架构层级关系"""
        errors = {}
        
        if class_id:
            try:
                school_class = Class.objects.get(id=class_id, is_deleted=False)
                if major_id and school_class.major_id != major_id:
                    errors['class'] = '班级不属于指定的专业'
                if college_id and school_class.major.college_id != college_id:
                    errors['class'] = '班级不属于指定的学院'
            except Class.DoesNotExist:
                errors['class'] = '班级不存在'
        
        if major_id:
            try:
                major = Major.objects.get(id=major_id, is_deleted=False)
                if college_id and major.college_id != college_id:
                    errors['major'] = '专业不属于指定的学院'
            except Major.DoesNotExist:
                errors['major'] = '专业不存在'
        
        if college_id:
            try:
                college = College.objects.get(id=college_id, is_deleted=False)
            except College.DoesNotExist:
                errors['college'] = '学院不存在'
        
        if errors:
            raise ValidationError(errors)
        
        return True
