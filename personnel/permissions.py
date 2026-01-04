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
            elif hasattr(obj, 'teacher'):
                return obj.teacher.college == teacher.college
        
        return False


class IsTeacher(permissions.BasePermission):
    """教师权限"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'teacher_profile')
    
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
        
        # 学院管理员可以管理本学院的数据
        if teacher.position_type in ['dean', 'vice_dean']:
            if hasattr(obj, 'college'):
                return obj.college == teacher.college
            elif hasattr(obj, 'teacher'):
                return obj.teacher.college == teacher.college
        
        # 普通教师只能查看和编辑自己的信息
        if teacher.position_type in ['teacher', 'head_teacher']:
            if isinstance(obj, Teacher):
                return obj == teacher
            elif hasattr(obj, 'teacher'):
                return obj.teacher == teacher
        
        return False


class TeacherPermission(permissions.BasePermission):
    """教师管理权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        teacher = request.user.teacher_profile
        
        # 系统管理员有所有权限
        if teacher.position_type == 'super_admin':
            return True
        
        # 学院管理员可以管理本学院的教师
        if teacher.position_type in ['dean', 'vice_dean']:
            if request.method in permissions.SAFE_METHODS:
                return True
            return True  # 可以创建、更新、删除本学院的教师
        
        # 教师/班主任不能访问教师管理功能（包括列表和详情）
        if teacher.position_type in ['teacher', 'head_teacher']:
            return False
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """检查用户是否有权限访问特定教师对象"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        current_teacher = request.user.teacher_profile
        
        # 系统管理员有所有权限
        if current_teacher.position_type == 'super_admin':
            return True
        
        # 学院管理员可以管理本学院的教师
        if current_teacher.position_type in ['dean', 'vice_dean']:
            return obj.college == current_teacher.college
        
        # 普通教师只能查看和编辑自己的信息
        if current_teacher.position_type in ['teacher', 'head_teacher']:
            return obj == current_teacher and request.method in permissions.SAFE_METHODS + ('PUT', 'PATCH')
        
        return False


class RolePermission(permissions.BasePermission):
    """角色管理权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        teacher = request.user.teacher_profile
        
        # 只有系统管理员可以管理角色
        return teacher.position_type == 'super_admin'


class UserRolePermission(permissions.BasePermission):
    """用户角色关联权限"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        teacher = request.user.teacher_profile
        
        # 系统管理员有所有权限
        if teacher.position_type == 'super_admin':
            return True
        
        # 学院管理员可以管理本学院的用户角色
        if teacher.position_type in ['dean', 'vice_dean']:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """检查用户是否有权限访问特定用户角色对象"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'teacher_profile'):
            return False
        
        current_teacher = request.user.teacher_profile
        
        # 系统管理员有所有权限
        if current_teacher.position_type == 'super_admin':
            return True
        
        # 学院管理员可以管理本学院的用户角色
        if current_teacher.position_type in ['dean', 'vice_dean']:
            # 检查目标用户是否属于本学院
            if hasattr(obj.user, 'teacher_profile'):
                return obj.user.teacher_profile.college == current_teacher.college
        
        return False