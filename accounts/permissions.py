from rest_framework.permissions import BasePermission
import logging

logger = logging.getLogger(__name__)


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        try:
            user = request.user
            if not user or not user.is_authenticated:
                return False
            if getattr(user, 'is_superuser', False):
                return True
            profile = getattr(user, 'profile', None)
            if not profile:
                return False
            return profile.role in ['super_admin', 'principal', 'vice_principal']
        except Exception:
            return False


class IsTeacherOrAdminOrReadOnly(BasePermission):
    """
    权限类：教师或管理员可读写，其他已认证用户只读
    GET/HEAD/OPTIONS请求：所有已认证用户都可以访问
    其他请求：需要是教师或管理员
    """
    def has_permission(self, request, view):
        # 对于GET、HEAD、OPTIONS请求，允许所有已认证用户访问
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            # 只要用户已认证即可
            try:
                is_auth = bool(request.user and request.user.is_authenticated)
                if not is_auth:
                    logger.warning(f"GET请求权限检查失败: user={request.user}, is_authenticated={getattr(request.user, 'is_authenticated', None)}")
                return is_auth
            except Exception as e:
                logger.error(f"GET请求权限检查异常: {str(e)}")
                return False
        
        # 对于其他请求（POST、PUT、DELETE等），需要是教师或管理员
        user = request.user
        try:
            if not user or not user.is_authenticated:
                return False
            if getattr(user, 'is_superuser', False):
                return True
            profile = getattr(user, 'profile', None)
            if not profile:
                logger.warning(f"{request.method}请求权限不足: user={user.username}, 没有profile")
                return False
            allowed = profile.role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'teacher', 'head_teacher']
            if not allowed:
                logger.warning(f"{request.method}请求权限不足: user={user.username}, role={profile.role}")
            return allowed
        except Exception as e:
            logger.error(f"{request.method}请求权限检查异常: {str(e)}")
            return False


class IsAdminOrDeanOrReadOnly(BasePermission):
    """
    权限类：管理员或院长可读写，其他已认证用户只读
    GET/HEAD/OPTIONS请求：所有已认证用户都可以访问
    其他请求：需要是管理员或院长
    """
    def has_permission(self, request, view):
        # 对于GET、HEAD、OPTIONS请求，允许所有已认证用户访问
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            try:
                return bool(request.user and request.user.is_authenticated)
            except Exception:
                return False
        
        # 对于其他请求，需要是管理员或院长
        user = request.user
        try:
            if not user or not user.is_authenticated:
                return False
            if getattr(user, 'is_superuser', False):
                return True
            profile = getattr(user, 'profile', None)
            if not profile:
                return False
            return profile.role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']
        except Exception:
            return False


class IsTeacherOnlyOrReadOnly(BasePermission):
    """
    权限类：教师可读写，其他已认证用户只读
    GET/HEAD/OPTIONS请求：所有已认证用户都可以访问
    其他请求：需要是教师
    """
    def has_permission(self, request, view):
        # 对于GET、HEAD、OPTIONS请求，允许所有已认证用户访问
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            try:
                return bool(request.user and request.user.is_authenticated)
            except Exception:
                return False
        
        # 对于其他请求，需要是教师
        user = request.user
        try:
            if not user or not user.is_authenticated:
                return False
            profile = getattr(user, 'profile', None)
            if not profile:
                return False
            return profile.role == 'teacher'
        except Exception:
            return False


class IsAdminOnlyOrReadOnly(BasePermission):
    """
    权限类：只有管理员可读写，其他已认证用户只读
    GET/HEAD/OPTIONS请求：所有已认证用户都可以访问（查看列表）
    其他请求（POST/PUT/DELETE）：需要是管理员
    """
    def has_permission(self, request, view):
        # 对于GET、HEAD、OPTIONS请求，允许所有已认证用户访问
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            try:
                return bool(request.user and request.user.is_authenticated)
            except Exception:
                return False
        
        # 对于其他请求，需要是管理员
        user = request.user
        try:
            if not user or not user.is_authenticated:
                return False
            if getattr(user, 'is_superuser', False):
                return True
            profile = getattr(user, 'profile', None)
            if not profile:
                return False
            return profile.role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']
        except Exception:
            return False
