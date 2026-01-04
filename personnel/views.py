from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction, models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import Teacher, Role, UserRole, TeacherPositionHistory, Permission
from .serializers import (
    TeacherSerializer, TeacherListSerializer, TeacherCreateSerializer, TeacherUpdateSerializer,
    RoleSerializer, UserRoleSerializer, TeacherPositionHistorySerializer, PermissionSerializer
)
from .permissions import TeacherPermission, RolePermission, UserRolePermission
from .services import TeacherService


class TeacherViewSet(viewsets.ModelViewSet):
    """教师管理视图集"""
    queryset = Teacher.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, TeacherPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['position_type', 'college', 'gender']
    search_fields = ['employee_id', 'name', 'contact_info__phone', 'contact_info__email']
    ordering_fields = ['employee_id', 'name', 'hire_date', 'created_at']
    ordering = ['employee_id']
    pagination_class = None  # 禁用分页，返回所有数据
    
    def get_serializer_class(self):
        """根据操作类型返回不同的序列化器"""
        if self.action == 'list':
            return TeacherListSerializer
        elif self.action == 'create':
            return TeacherCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TeacherUpdateSerializer
        return TeacherSerializer
    
    def get_queryset(self):
        """根据用户权限过滤查询集"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_authenticated:
            return queryset.none()
        
        if not hasattr(self.request.user, 'teacher_profile'):
            return queryset.none()
        
        teacher = self.request.user.teacher_profile
        
        # 系统管理员可以查看所有教师
        if teacher.position_type == 'super_admin':
            return queryset
        
        # 学院管理员只能查看本学院的教师
        if teacher.position_type in ['dean', 'vice_dean']:
            return queryset.filter(college=teacher.college)
        
        # 普通教师只能查看自己的信息
        if teacher.position_type in ['teacher', 'head_teacher']:
            return queryset.filter(employee_id=teacher.employee_id)
        
        return queryset.none()
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """创建教师记录"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 使用服务层处理业务逻辑
        service = TeacherService()
        teacher = service.create_teacher(serializer.validated_data, request.user)
        
        # 返回完整数据
        result_serializer = TeacherSerializer(teacher)
        headers = self.get_success_headers(result_serializer.data)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """更新教师记录"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # 使用服务层处理业务逻辑
        service = TeacherService()
        teacher = service.update_teacher(instance, serializer.validated_data, request.user)
        
        # 返回完整数据
        result_serializer = TeacherSerializer(teacher)
        return Response(result_serializer.data)
    
    @transaction.atomic
    def perform_destroy(self, instance):
        """删除教师记录（使用服务层的软删除逻辑）"""
        service = TeacherService()
        service.delete_teacher(instance, self.request.user)
    
    @action(detail=True, methods=['post'])
    def change_position(self, request, pk=None):
        """变更教师职务"""
        teacher = self.get_object()
        
        new_position = request.data.get('position_type')
        new_college_id = request.data.get('college')
        change_reason = request.data.get('change_reason', '')
        
        if not new_position:
            return Response({'error': '新职务不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        service = TeacherService()
        try:
            teacher = service.change_teacher_position(
                teacher, new_position, new_college_id, 
                change_reason, request.user
            )
            
            serializer = TeacherSerializer(teacher)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """教师统计信息"""
        queryset = self.get_queryset()
        
        # 按职务类型统计
        position_stats = queryset.values('position_type').annotate(
            count=models.Count('employee_id')
        ).order_by('-count')
        
        # 按学院统计
        college_stats = queryset.values('college__name').annotate(
            count=models.Count('employee_id')
        ).order_by('-count')
        
        # 按性别统计
        gender_stats = queryset.values('gender').annotate(
            count=models.Count('employee_id')
        ).order_by('-count')
        
        data = {
            'total_count': queryset.count(),
            'position_stats': list(position_stats),
            'college_stats': list(college_stats),
            'gender_stats': list(gender_stats)
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def export_template(self, request):
        """导出教师信息导入模板"""
        import pandas as pd
        from io import BytesIO
        
        # 创建模板数据
        template_data = {
            '工号': ['必填，唯一标识'],
            '姓名': ['必填'],
            '性别': ['必填，可选值：male/female'],
            '联系电话': ['可选，手机号格式'],
            '联系邮箱': ['可选，邮箱格式'],
            '入职日期': ['必填，格式：YYYY-MM-DD'],
            '职务类型': ['必填，可选值：dean/vice_dean/head_teacher/teacher'],
            '所属学院代码': ['可选，学院代码'],
            '管辖专业IDs': ['可选，多个ID用逗号分隔'],
            '负责班级ID': ['可选，班主任的班级ID']
        }
        
        df = pd.DataFrame(template_data)
        
        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='教师信息模板')
        
        output.seek(0)
        
        response = Response(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="teacher_template.xlsx"'
        
        return response


class RoleViewSet(viewsets.ModelViewSet):
    """角色管理视图集"""
    queryset = Role.objects.filter(is_deleted=False)
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['code']
    pagination_class = None  # 禁用分页，返回所有数据


class UserRoleViewSet(viewsets.ModelViewSet):
    """用户角色关联视图集"""
    queryset = UserRole.objects.filter(is_deleted=False)
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, UserRolePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['role', 'user']
    search_fields = ['user__username', 'role__name']
    ordering_fields = ['assigned_at', 'created_at']
    ordering = ['-assigned_at']
    pagination_class = None  # 禁用分页，返回所有数据


class TeacherPositionHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """教师职务变更历史视图集"""
    queryset = TeacherPositionHistory.objects.filter(is_deleted=False)
    serializer_class = TeacherPositionHistorySerializer
    permission_classes = [IsAuthenticated, TeacherPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['teacher', 'old_position', 'new_position', 'changed_by']
    search_fields = ['teacher__name', 'teacher__employee_id', 'change_reason']
    ordering_fields = ['effective_date', 'created_at']
    ordering = ['-effective_date']
    pagination_class = None  # 禁用分页，返回所有数据
    
    def get_queryset(self):
        """根据用户权限过滤查询集"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_authenticated:
            return queryset.none()
        
        if not hasattr(self.request.user, 'teacher_profile'):
            return queryset.none()
        
        teacher = self.request.user.teacher_profile
        
        # 系统管理员可以查看所有历史
        if teacher.position_type == 'super_admin':
            return queryset
        
        # 学院管理员只能查看本学院的历史
        if teacher.position_type in ['dean', 'vice_dean']:
            return queryset.filter(
                models.Q(teacher__college=teacher.college) |
                models.Q(old_college=teacher.college) |
                models.Q(new_college=teacher.college)
            )
        
        # 普通教师只能查看自己的历史
        if teacher.position_type in ['teacher', 'head_teacher']:
            return queryset.filter(teacher=teacher)
        
        return queryset.none()


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """权限视图集"""
    queryset = Permission.objects.filter(is_active=True)
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['module']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['module', 'code']
    ordering = ['module', 'code']
    pagination_class = None  # 禁用分页，返回所有数据