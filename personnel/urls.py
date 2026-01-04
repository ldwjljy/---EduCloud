from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet, RoleViewSet, UserRoleViewSet

# 创建路由器并注册视图集
router = DefaultRouter()
router.register(r'teachers', TeacherViewSet, basename='teacher')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'user-roles', UserRoleViewSet, basename='userrole')

urlpatterns = [
    path('api/', include(router.urls)),
]