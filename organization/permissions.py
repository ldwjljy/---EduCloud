from rest_framework import permissions
from django.contrib.auth.models import User


class IsSystemAdmin(permissions.BasePermission):
    """系统管理员权限"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'teacher_profile') and request.user.teacher_profile.position_type == 'super_admin'


class IsCollegeAdmin(permissions.BasePermission):
    """学院管理员权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        teacher = request.user.teacher_profile
        return teacher.position_type in ['dean', 'vice_dean']
    
    def has_object_permission(self, request, view, obj):
        """检查用户是否有权限访问特定对象"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        teacher = request.user.teacher_profile
        
        # 系统管理员有所有权限
        if teacher.position_type == 'super_admin':
            return True
        
        # 学院管理员只能管理本学院的数据
        if teacher.position_type in ['dean', 'vice_dean']:
            if hasattr(obj, 'college'):
                return obj.college == teacher.college
            elif hasattr(obj, 'major'):
                return obj.major.college == teacher.college
        
        return False


class OrganizationPermission(permissions.BasePermission):
    """组织架构管理权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # 允许 Django 超级用户
        if getattr(request.user, 'is_superuser', False):
            return True
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        teacher = request.user.teacher_profile
        
        # 系统管理员有所有权限
        if teacher.position_type == 'super_admin':
            return True
        
        # 学院管理员可以管理本学院的数据
        if teacher.position_type in ['dean', 'vice_dean']:
            return True
        
        # 教师/班主任不能访问组织架构
        if teacher.position_type in ['teacher', 'head_teacher']:
            return False
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """检查用户是否有权限访问特定对象"""
        if not request.user or not request.user.is_authenticated:
            return False

        # 允许 Django 超级用户
        if getattr(request.user, 'is_superuser', False):
            return True
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        teacher = request.user.teacher_profile
        
        # 系统管理员有所有权限
        if teacher.position_type == 'super_admin':
            return True
        
        # 学院管理员可以管理本学院的数据
        if teacher.position_type in ['dean', 'vice_dean']:
            if hasattr(obj, 'college'):
                return obj.college == teacher.college
            elif hasattr(obj, 'major'):
                return obj.major.college == teacher.college
        
        # 教师/班主任不能访问组织架构
        if teacher.position_type in ['teacher', 'head_teacher']:
            return False
        
        return False


class CollegePermission(permissions.BasePermission):
    """学院管理权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        # 兼容 Django 超级用户
        if getattr(request.user, 'is_superuser', False):
            return True
            
        # 优先使用通用用户档案中的角色
        role = None
        try:
            role = getattr(request.user.profile, 'role', None)
        except Exception:
            role = None

        # 教师/班主任不能访问组织架构
        if role in ['teacher', 'head_teacher']:
            return False

        # 允许管理员和院长查看学院列表（用于筛选器）
        if request.method in permissions.SAFE_METHODS:
            if role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
                return True
            # 兼容老的教师档案模型
            if hasattr(request.user, 'teacher_profile'):
                teacher = request.user.teacher_profile
                if getattr(teacher, 'position_type', None) in ['super_admin', 'dean', 'vice_dean']:
                    return True
            return False
            
        # 修改和删除操作需要管理权限
        if role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
            return True
            
        # 兼容老的教师档案模型
        if hasattr(request.user, 'teacher_profile'):
            teacher = request.user.teacher_profile
            if getattr(teacher, 'position_type', None) in ['super_admin', 'dean', 'vice_dean']:
                return True
                
        return False


class MajorPermission(permissions.BasePermission):
    """专业管理权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # 允许 Django 超级用户
        if getattr(request.user, 'is_superuser', False):
            return True
        
        role = getattr(request.user.profile, 'role', '') if hasattr(request.user, 'profile') else ''
        
        # 教师/班主任不能访问组织架构
        if role in ['teacher', 'head_teacher']:
            return False
        
        # 允许管理员和院长查看专业列表（用于筛选器）
        if request.method in permissions.SAFE_METHODS:
            if role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
                return True
            # Legacy check
            if hasattr(request.user, 'teacher_profile'):
                teacher = request.user.teacher_profile
                if getattr(teacher, 'position_type', None) in ['super_admin', 'dean', 'vice_dean']:
                    return True
            return False
        
        # 系统管理员有所有权限
        if role in ['super_admin', 'principal', 'vice_principal']:
            return True
        
        # 学院管理员可以管理本学院的专业
        if role in ['dean', 'vice_dean']:
            return True
            
        # Legacy check
        if hasattr(request.user, 'teacher_profile'):
            teacher = request.user.teacher_profile
            if getattr(teacher, 'position_type', None) in ['super_admin', 'dean', 'vice_dean']:
                return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """检查用户是否有权限访问特定专业对象"""
        if not request.user or not request.user.is_authenticated:
            return False

        # 允许 Django 超级用户
        if getattr(request.user, 'is_superuser', False):
            return True
            
        role = getattr(request.user.profile, 'role', '')
        
        # 系统管理员有所有权限
        if role in ['super_admin', 'principal', 'vice_principal']:
            return True
            
        teacher = getattr(request.user, 'teacher_profile', None)
        
        # 学院管理员可以管理本学院的专业
        if role in ['dean', 'vice_dean']:
             if teacher and teacher.department:
                 return obj.college == teacher.department.college
             return False # Or True if we assume they can manage all majors in their college but we don't know which college
        
        # 普通教师只能查看
        if role in ['teacher', 'head_teacher']:
            return request.method in permissions.SAFE_METHODS
            
        return False


class ClassPermission(permissions.BasePermission):
    """班级管理权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # 允许 Django 超级用户
        if getattr(request.user, 'is_superuser', False):
            return True

        # 优先使用统一的用户角色字段
        role = getattr(getattr(request.user, 'profile', None), 'role', '')

        # 1）GET/HEAD/OPTIONS 等只读请求：
        #    允许管理员/院长查看班级列表，用于筛选器等场景
        if request.method in permissions.SAFE_METHODS:
            if role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
                return True

            # 兼容老的 teacher_profile.position_type 方案
            if hasattr(request.user, 'teacher_profile'):
                teacher = request.user.teacher_profile
                if getattr(teacher, 'position_type', None) in ['super_admin', 'dean', 'vice_dean']:
                    return True

            # 保持原有逻辑：普通教师/班主任不能通过“组织架构”页面访问班级管理
            return False

        # 2）写操作（POST/PUT/DELETE）：需要管理员或学院管理员权限
        if role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
            return True

        # 兼容老的 teacher_profile.position_type 方案
        if hasattr(request.user, 'teacher_profile'):
            teacher = request.user.teacher_profile
            if getattr(teacher, 'position_type', None) in ['super_admin', 'dean', 'vice_dean']:
                return True

        # 普通教师/班主任等没有通过组织架构管理班级的权限
        return False
    
    def has_object_permission(self, request, view, obj):
        """检查用户是否有权限访问特定班级对象"""
        if not request.user or not request.user.is_authenticated:
            return False

        # 允许 Django 超级用户
        if getattr(request.user, 'is_superuser', False):
            return True

        role = getattr(getattr(request.user, 'profile', None), 'role', '')

        # 系统级管理员 / 校领导拥有全部班级对象权限
        if role in ['super_admin', 'principal', 'vice_principal']:
            return True

        # 兼容老的 teacher_profile.position_type 逻辑
        if hasattr(request.user, 'teacher_profile'):
            teacher = request.user.teacher_profile

            # 老的“系统管理员”
            if getattr(teacher, 'position_type', None) == 'super_admin':
                return True

            # 学院管理员只能管理本学院的班级
            if teacher.position_type in ['dean', 'vice_dean']:
                return obj.major.college == teacher.college

            # 教师/班主任不能通过组织架构页面访问班级管理
            if teacher.position_type in ['teacher', 'head_teacher']:
                return False

        return False
