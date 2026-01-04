from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CollegeViewSet, MajorViewSet, ClassViewSet, 
    OrganizationViewSet, SystemDictionaryViewSet, OperationLogViewSet,
    ClassroomViewSet, OrganizationImportView
)

# 创建路由器并注册视图集
router = DefaultRouter()
router.register(r'colleges', CollegeViewSet, basename='college')
router.register(r'majors', MajorViewSet, basename='major')
router.register(r'departments', MajorViewSet, basename='department')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'classrooms', ClassroomViewSet, basename='classroom')
router.register(r'organization', OrganizationViewSet, basename='organization')
router.register(r'system-dictionaries', SystemDictionaryViewSet, basename='systemdictionary')
router.register(r'operation-logs', OperationLogViewSet, basename='operationlog')

urlpatterns = [
    path('import', OrganizationImportView.as_view(), name='org-import'),
    path('', include(router.urls)),
]
