from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.exceptions import ValidationError
from django.db import models

from .models import College, Major, Class, SystemDictionary, OperationLog
from classrooms.models import Classroom
from .serializers import (
    CollegeSerializer, CollegeListSerializer,
    MajorSerializer, MajorListSerializer,
    ClassSerializer, ClassListSerializer,
    OrganizationTreeSerializer, SystemDictionarySerializer, OperationLogSerializer,
    CollegeCreateSerializer, MajorCreateSerializer, ClassCreateSerializer,
    ClassroomSerializer
)
from .permissions import (
    CollegePermission, MajorPermission, ClassPermission, OrganizationPermission
)
from .services import OrganizationService


class CollegeViewSet(viewsets.ModelViewSet):
    """学院管理视图集"""
    queryset = College.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, CollegePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'establishment_date', 'created_at']
    ordering = ['code']
    
    def get_paginated_response(self, data):
        """如果请求中包含no_page参数，则不分页"""
        if 'no_page' in self.request.query_params or self.action == 'list' and not self.request.query_params.get('page'):
            return Response(data)
        return super().get_paginated_response(data)
    
    def paginate_queryset(self, queryset):
        """根据请求参数决定是否分页"""
        if 'no_page' in self.request.query_params:
            return None
        # 对于list操作且没有明确要求分页的，也不分页（用于下拉框等场景）
        if self.action == 'list' and not self.request.query_params.get('page'):
            return None
        return super().paginate_queryset(queryset)
    
    def get_serializer_class(self):
        """根据操作类型返回不同的序列化器"""
        if self.action == 'list':
            return CollegeListSerializer
        elif self.action == 'create':
            return CollegeCreateSerializer
        return CollegeSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """创建学院"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        college = serializer.save()
        
        # 记录操作日志
        self._log_operation('create', 'colleges', college.id, {}, serializer.data, request)
        
        result_serializer = CollegeSerializer(college)
        headers = self.get_success_headers(result_serializer.data)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """更新学院"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        old_data = CollegeSerializer(instance).data
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        college = serializer.save()
        
        # 记录操作日志
        new_data = CollegeSerializer(college).data
        self._log_operation('update', 'colleges', college.id, old_data, new_data, request)
        
        return Response(new_data)
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """删除学院（软删除）"""
        instance = self.get_object()
        
        # 检查是否可以删除
        service = OrganizationService()
        try:
            service.validate_college_deletion(instance)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        old_data = CollegeSerializer(instance).data
        
        # 软删除
        instance.is_deleted = True
        instance.save()
        
        # 记录操作日志
        self._log_operation('delete', 'colleges', instance.id, old_data, {}, request)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取学院树形结构"""
        service = OrganizationService()
        tree_data = service.get_college_tree()
        serializer = OrganizationTreeSerializer(tree_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export_template(self, request):
        """导出学院导入模板(Excel)"""
        import pandas as pd
        from io import BytesIO
        df = pd.DataFrame({
            '学院代码': ['四位数字，如 1001'],
            '学院名称': ['示例：计算机学院'],
            '成立日期': ['YYYY-MM-DD'],
            '状态': ['active/inactive']
        })
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='学院模板')
        output.seek(0)
        resp = Response(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="college_template.xlsx"'
        return resp

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def import_excel(self, request):
        """导入学院数据(Excel/CSV)，失败自动回滚"""
        f = request.FILES.get('file')
        if not f:
            return Response({'error': '请上传文件参数 file'}, status=status.HTTP_400_BAD_REQUEST)
        rows = []
        try:
            import pandas as pd
            df = pd.read_excel(f) if f.name.lower().endswith(('xlsx', 'xls')) else pd.read_csv(f)
            for _, row in df.iterrows():
                rows.append({
                    'code': str(row.get('学院代码')).strip(),
                    'name': str(row.get('学院名称')).strip(),
                    'establishment_date': str(row.get('成立日期')).strip(),
                    'status': str(row.get('状态')).strip() or 'active',
                })
        except Exception:
            return Response({'error': '文件解析失败，请使用标准模板'}, status=status.HTTP_400_BAD_REQUEST)
        errors = []
        created = 0
        for i, data in enumerate(rows, start=1):
            serializer = CollegeCreateSerializer(data=data)
            if not serializer.is_valid():
                errors.append({'row': i, 'errors': serializer.errors})
                continue
        if errors:
            transaction.set_rollback(True)
            return Response({'created': 0, 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        created_objs = []
        for data in rows:
            obj = College.objects.create(**serializer.__class__(data=data).validated_data)
            created_objs.append(obj)
            self._log_operation('import', 'colleges', obj.id, {}, CollegeSerializer(obj).data, request)
        return Response({'created': len(created_objs)})
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取学院统计信息"""
        college = self.get_object()
        
        # 统计专业数量
        major_count = college.majors.filter(is_deleted=False).count()
        
        # 统计班级数量
        class_count = Class.objects.filter(major__college=college, is_deleted=False).count()
        
        # 统计教师数量
        teacher_count = college.teachers.filter(is_deleted=False).count()
        
        # 按学制类型统计专业数量
        duration_stats = college.majors.filter(is_deleted=False).values('duration_type').annotate(
            count=models.Count('id')
        )
        
        data = {
            'college': CollegeSerializer(college).data,
            'major_count': major_count,
            'class_count': class_count,
            'teacher_count': teacher_count,
            'duration_stats': list(duration_stats)
        }
        
        return Response(data)
    
    def _log_operation(self, operation_type, table_name, record_id, old_data, new_data, request):
        """记录操作日志"""
        OperationLog.objects.create(
            user_id=request.user.id,
            operation_type=operation_type,
            table_name=table_name,
            record_id=str(record_id),
            old_data=old_data,
            new_data=new_data,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # 禁用分页，返回所有数据


class MajorViewSet(viewsets.ModelViewSet):
    """专业管理视图集"""
    queryset = Major.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, MajorPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['college', 'duration_type']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'college__name', 'created_at']
    ordering = ['college__code', 'code']
    
    def get_paginated_response(self, data):
        """如果请求中包含no_page参数，则不分页"""
        if 'no_page' in self.request.query_params or self.action == 'list' and not self.request.query_params.get('page'):
            return Response(data)
        return super().get_paginated_response(data)
    
    def paginate_queryset(self, queryset):
        """根据请求参数决定是否分页"""
        if 'no_page' in self.request.query_params:
            return None
        # 对于list操作且没有明确要求分页的，也不分页（用于下拉框等场景）
        if self.action == 'list' and not self.request.query_params.get('page'):
            return None
        return super().paginate_queryset(queryset)
    
    def get_serializer_class(self):
        """根据操作类型返回不同的序列化器"""
        if self.action == 'list':
            return MajorListSerializer
        elif self.action == 'create':
            return MajorCreateSerializer
        return MajorSerializer
    
    def get_queryset(self):
        """根据用户权限过滤查询集"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_authenticated:
            return queryset.none()
        
        # 系统管理员（Django超级用户）可以查看所有专业
        if getattr(self.request.user, 'is_superuser', False):
            return queryset

        if not hasattr(self.request.user, 'teacher_profile'):
            return queryset.none()
        
        teacher = self.request.user.teacher_profile
        role = getattr(self.request.user.profile, 'role', '')

        # 系统管理员可以查看所有专业
        if role in ['super_admin', 'principal', 'vice_principal']:
            return queryset
        
        # 学院管理员只能查看本学院的专业
        if role in ['dean', 'vice_dean']:
            if teacher.college:
                return queryset.filter(college=teacher.college)
            return queryset.none()
        
        # 普通教师只能查看所属学院的专业
        if role in ['teacher', 'head_teacher']:
            if teacher.college:
                return queryset.filter(college=teacher.college)
            return queryset.none()
        
        return queryset.none()
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """创建专业"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        major = serializer.save()
        
        # 记录操作日志
        self._log_operation('create', 'majors', major.id, {}, serializer.data, request)
        
        result_serializer = MajorSerializer(major)
        headers = self.get_success_headers(result_serializer.data)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """更新专业"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        old_data = MajorSerializer(instance).data
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        major = serializer.save()
        
        # 记录操作日志
        new_data = MajorSerializer(major).data
        self._log_operation('update', 'majors', major.id, old_data, new_data, request)
        
        return Response(new_data)
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """删除专业（软删除）"""
        instance = self.get_object()
        
        # 检查是否可以删除
        service = OrganizationService()
        try:
            service.validate_major_deletion(instance)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        old_data = MajorSerializer(instance).data
        
        # 软删除
        instance.is_deleted = True
        instance.save()
        
        # 记录操作日志
        self._log_operation('delete', 'majors', instance.id, old_data, {}, request)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def by_college(self, request):
        """按学院获取专业"""
        college_id = request.query_params.get('college_id')
        if not college_id:
            return Response({'error': 'college_id参数必填'}, status=status.HTTP_400_BAD_REQUEST)
        
        majors = self.get_queryset().filter(college_id=college_id)
        serializer = MajorListSerializer(majors, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export_template(self, request):
        """导出专业导入模板(Excel)"""
        import pandas as pd
        from io import BytesIO
        df = pd.DataFrame({
            '专业代码': ['六位数字，前四位为学院代码'],
            '专业名称': ['示例：软件技术'],
            '所属学院ID': ['学院表ID，外键'],
            '学制类型': ['3_year/5_year/6_year']
        })
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='专业模板')
        output.seek(0)
        resp = Response(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="major_template.xlsx"'
        return resp

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def import_excel(self, request):
        """导入专业数据(Excel/CSV)，失败自动回滚"""
        f = request.FILES.get('file')
        if not f:
            return Response({'error': '请上传文件参数 file'}, status=status.HTTP_400_BAD_REQUEST)
        rows = []
        try:
            import pandas as pd
            df = pd.read_excel(f) if f.name.lower().endswith(('xlsx', 'xls')) else pd.read_csv(f)
            for _, row in df.iterrows():
                rows.append({
                    'code': str(row.get('专业代码')).strip(),
                    'name': str(row.get('专业名称')).strip(),
                    'college': int(row.get('所属学院ID')) if row.get('所属学院ID') else None,
                    'duration_type': str(row.get('学制类型')).strip(),
                })
        except Exception:
            return Response({'error': '文件解析失败，请使用标准模板'}, status=status.HTTP_400_BAD_REQUEST)
        errors = []
        created_objs = []
        for i, data in enumerate(rows, start=1):
            try:
                college = College.objects.get(id=data['college'], is_deleted=False)
                data['college'] = college
            except Exception:
                errors.append({'row': i, 'errors': {'college': '所属学院不存在'}})
                continue
            serializer = MajorCreateSerializer(data=data)
            if not serializer.is_valid():
                errors.append({'row': i, 'errors': serializer.errors})
                continue
            obj = serializer.save()
            created_objs.append(obj)
            self._log_operation('import', 'majors', obj.id, {}, MajorSerializer(obj).data, request)
        if errors:
            transaction.set_rollback(True)
            return Response({'created': len(created_objs), 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'created': len(created_objs)})
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取专业统计信息"""
        major = self.get_object()
        
        # 统计班级数量
        class_count = major.classes.filter(is_deleted=False).count()
        
        # 按入学年份统计班级数量
        enrollment_stats = major.classes.filter(is_deleted=False).values('enrollment_year').annotate(
            count=models.Count('id')
        ).order_by('-enrollment_year')
        
        data = {
            'major': MajorSerializer(major).data,
            'class_count': class_count,
            'enrollment_stats': list(enrollment_stats)
        }
        
        return Response(data)
    
    def _log_operation(self, operation_type, table_name, record_id, old_data, new_data, request):
        """记录操作日志"""
        OperationLog.objects.create(
            user_id=request.user.id,
            operation_type=operation_type,
            table_name=table_name,
            record_id=str(record_id),
            old_data=old_data,
            new_data=new_data,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ClassViewSet(viewsets.ModelViewSet):
    """班级管理视图集"""
    queryset = Class.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, ClassPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['major', 'enrollment_year', 'major__college']
    search_fields = ['name']
    ordering_fields = ['name', 'enrollment_year', 'class_number', 'created_at']
    ordering = ['-enrollment_year', 'class_number']
    
    def get_paginated_response(self, data):
        """如果请求中包含no_page参数，则不分页"""
        if 'no_page' in self.request.query_params or self.action == 'list' and not self.request.query_params.get('page'):
            return Response(data)
        return super().get_paginated_response(data)
    
    def paginate_queryset(self, queryset):
        """根据请求参数决定是否分页"""
        if 'no_page' in self.request.query_params:
            return None
        # 对于list操作且没有明确要求分页的，也不分页（用于下拉框等场景）
        if self.action == 'list' and not self.request.query_params.get('page'):
            return None
        return super().paginate_queryset(queryset)
    
    def get_serializer_class(self):
        """根据操作类型返回不同的序列化器"""
        if self.action == 'list':
            return ClassListSerializer
        elif self.action == 'create':
            return ClassCreateSerializer
        return ClassSerializer
    
    def get_queryset(self):
        """根据用户权限过滤查询集"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_authenticated:
            return queryset.none()
        
        # 系统管理员（Django超级用户）可以查看所有班级
        if getattr(self.request.user, 'is_superuser', False):
            return queryset

        if not hasattr(self.request.user, 'teacher_profile'):
            return queryset.none()
        
        teacher = self.request.user.teacher_profile
        role = getattr(self.request.user.profile, 'role', '')
        
        # 系统管理员可以查看所有班级
        if role in ['super_admin', 'principal', 'vice_principal']:
            return queryset
        
        # 学院管理员只能查看本学院的班级
        if role in ['dean', 'vice_dean']:
            if teacher.college:
                return queryset.filter(major__college=teacher.college)
            return queryset.none()
        
        # 班主任只能查看自己管理的班级
        if role == 'head_teacher':
            return queryset.filter(head_teacher=teacher)
        
        # 普通教师只能查看所属学院的班级
        if role == 'teacher':
            if teacher.college:
                return queryset.filter(major__college=teacher.college)
            return queryset.none()
        
        return queryset.none()
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """创建班级"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        major = serializer.validated_data['major']
        enrollment_year = serializer.validated_data['enrollment_year']
        
        # 这里的 class_number 实际上是“班级数量”而不是“班级序号”
        quantity = serializer.validated_data.get('class_number', 1)
        
        # 获取该专业该年级当前已有的最大班级序号
        existing_classes = Class.objects.filter(
            major=major,
            enrollment_year=enrollment_year
        ).aggregate(max_num=models.Max('class_number'))
        
        current_max = existing_classes['max_num'] or 0
        created_classes = []
        
        duration_label = major.get_duration_label()
        
        for i in range(1, quantity + 1):
            next_num = current_max + i
            name = f"{enrollment_year}年{major.name}{duration_label}-{next_num}班"
            
            # 创建班级实例
            school_class = Class(
                major=major,
                enrollment_year=enrollment_year,
                class_number=next_num,
                name=name,
                head_teacher=serializer.validated_data.get('head_teacher')
            )
            school_class.save()
            created_classes.append(school_class)
            
            # 记录操作日志
            self._log_operation('create', 'classes', school_class.id, {}, ClassSerializer(school_class).data, request)
        
        # 如果只创建了一个，返回单个对象；否则返回列表（虽然 DRF create 默认返回单个，但这里为了兼容性，我们返回最后一个创建的，或者修改前端逻辑）
        # 为了保持 API 兼容性，如果 quantity=1，返回单个；如果 quantity > 1，返回列表（但标准 create 只期待一个）
        # 实际上，前端可能只期望 201。
        
        if len(created_classes) == 1:
            result_serializer = ClassSerializer(created_classes[0])
            headers = self.get_success_headers(result_serializer.data)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            result_serializer = ClassSerializer(created_classes, many=True)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """更新班级"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        old_data = ClassSerializer(instance).data
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # 如果专业或入学年份或序号发生变化，重新生成班级名称
        if any(key in serializer.validated_data for key in ['major', 'enrollment_year', 'class_number']):
            major = serializer.validated_data.get('major', instance.major)
            enrollment_year = serializer.validated_data.get('enrollment_year', instance.enrollment_year)
            class_number = serializer.validated_data.get('class_number', instance.class_number)
            
            duration_label = major.get_duration_label()
            name = f"{enrollment_year}年{major.name}{duration_label}-{class_number}班"
            serializer.validated_data['name'] = name
        
        school_class = serializer.save()
        
        # 记录操作日志
        new_data = ClassSerializer(school_class).data
        self._log_operation('update', 'classes', school_class.id, old_data, new_data, request)
        
        return Response(new_data)
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """删除班级（软删除）"""
        instance = self.get_object()
        
        # 检查是否可以删除
        service = OrganizationService()
        try:
            service.validate_class_deletion(instance)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        old_data = ClassSerializer(instance).data
        
        # 软删除
        instance.is_deleted = True
        instance.save()
        
        # 移除班主任关联
        if instance.head_teacher:
            instance.head_teacher = None
            instance.save()
        
        # 记录操作日志
        self._log_operation('delete', 'classes', instance.id, old_data, {}, request)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def by_major(self, request):
        """按专业获取班级"""
        major_id = request.query_params.get('major_id')
        if not major_id:
            return Response({'error': 'major_id参数必填'}, status=status.HTTP_400_BAD_REQUEST)
        
        classes = self.get_queryset().filter(major_id=major_id)
        serializer = ClassListSerializer(classes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def export_template(self, request):
        """导出班级导入模板(Excel)"""
        import pandas as pd
        from io import BytesIO
        df = pd.DataFrame({
            '所属专业ID': ['专业表ID，外键'],
            '入学年份': ['YYYY'],
            '班级序号': ['数字，从1开始'],
            '班主任工号': ['可选，对应教师工号']
        })
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='班级模板')
        output.seek(0)
        resp = Response(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="class_template.xlsx"'
        return resp

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def import_excel(self, request):
        """导入班级数据(Excel/CSV)，失败自动回滚"""
        f = request.FILES.get('file')
        if not f:
            return Response({'error': '请上传文件参数 file'}, status=status.HTTP_400_BAD_REQUEST)
        rows = []
        try:
            import pandas as pd
            df = pd.read_excel(f) if f.name.lower().endswith(('xlsx', 'xls')) else pd.read_csv(f)
            for _, row in df.iterrows():
                rows.append({
                    'major': int(row.get('所属专业ID')) if row.get('所属专业ID') else None,
                    'enrollment_year': int(row.get('入学年份')) if row.get('入学年份') else None,
                    'class_number': int(row.get('班级序号')) if row.get('班级序号') else 1,
                    'head_teacher': str(row.get('班主任工号')).strip() if row.get('班主任工号') else None,
                })
        except Exception:
            return Response({'error': '文件解析失败，请使用标准模板'}, status=status.HTTP_400_BAD_REQUEST)
        errors = []
        created_objs = []
        for i, data in enumerate(rows, start=1):
            try:
                major = Major.objects.get(id=data['major'], is_deleted=False)
                data['major'] = major
            except Exception:
                errors.append({'row': i, 'errors': {'major': '所属专业不存在'}})
                continue
            if data.get('head_teacher'):
                from personnel.models import Teacher
                try:
                    data['head_teacher'] = Teacher.objects.get(employee_id=data['head_teacher'], is_deleted=False)
                except Exception:
                    errors.append({'row': i, 'errors': {'head_teacher': '班主任工号不存在'}})
                    continue
            serializer = ClassCreateSerializer(data=data)
            if not serializer.is_valid():
                errors.append({'row': i, 'errors': serializer.errors})
                continue
            major = serializer.validated_data['major']
            enrollment_year = serializer.validated_data['enrollment_year']
            class_number = serializer.validated_data['class_number']
            duration_label = major.get_duration_label()
            name = f"{enrollment_year}年{major.name}{duration_label}-{class_number}班"
            obj = serializer.save(name=name)
            created_objs.append(obj)
            self._log_operation('import', 'classes', obj.id, {}, ClassSerializer(obj).data, request)
        if errors:
            transaction.set_rollback(True)
            return Response({'created': len(created_objs), 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'created': len(created_objs)})
    
    @action(detail=False, methods=['get'])
    def available_teachers(self, request):
        """获取可担任班主任的教师列表"""
        # 获取当前用户的学院
        if not hasattr(request.user, 'teacher_profile'):
            return Response({'error': '用户没有教师档案'}, status=status.HTTP_403_FORBIDDEN)
        
        teacher = request.user.teacher_profile
        
        # 获取本学院的教师
        from personnel.models import Teacher
        available_teachers = Teacher.objects.filter(
            college=teacher.college,
            is_deleted=False
        ).exclude(
            # 排除已经是其他班级班主任的教师
            employee_id__in=Class.objects.filter(
                is_deleted=False,
                head_teacher__isnull=False
            ).exclude(
                head_teacher__employee_id=teacher.employee_id
            ).values_list('head_teacher__employee_id', flat=True)
        )
        
        # 序列化教师数据
        from personnel.serializers import TeacherListSerializer
        serializer = TeacherListSerializer(available_teachers, many=True)
        return Response(serializer.data)
    
    def _log_operation(self, operation_type, table_name, record_id, old_data, new_data, request):
        """记录操作日志"""
        OperationLog.objects.create(
            user_id=request.user.id,
            operation_type=operation_type,
            table_name=table_name,
            record_id=str(record_id),
            old_data=old_data,
            new_data=new_data,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class OrganizationViewSet(viewsets.ViewSet):
    """组织架构综合视图集"""
    permission_classes = [IsAuthenticated, OrganizationPermission]
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取组织架构树"""
        college_id = request.query_params.get('college_id')
        
        service = OrganizationService()
        tree_data = service.get_organization_tree(college_id)
        
        serializer = OrganizationTreeSerializer(tree_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取组织架构统计信息"""
        # 统计学院数量
        college_count = College.objects.filter(is_deleted=False).count()
        
        # 统计专业数量
        major_count = Major.objects.filter(is_deleted=False).count()
        
        # 统计班级数量
        class_count = Class.objects.filter(is_deleted=False).count()
        
        # 按学院统计专业数量
        college_major_stats = College.objects.filter(is_deleted=False).annotate(
            major_count=models.Count('majors', filter=models.Q(majors__is_deleted=False))
        ).values('id', 'name', 'major_count').order_by('-major_count')
        
        # 按学制类型统计专业数量
        duration_stats = Major.objects.filter(is_deleted=False).values('duration_type').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        # 按入学年份统计班级数量
        enrollment_stats = Class.objects.filter(is_deleted=False).values('enrollment_year').annotate(
            count=models.Count('id')
        ).order_by('-enrollment_year')
        
        data = {
            'total_colleges': college_count,
            'total_majors': major_count,
            'total_classes': class_count,
            'college_major_stats': list(college_major_stats),
            'duration_stats': list(duration_stats),
            'enrollment_stats': list(enrollment_stats)
        }
        
        return Response(data)

    @action(detail=False, methods=['post'])
    def import_data(self, request):
        """导入数据 (This is a placeholder, actual logic is in import_view)"""
        # The frontend calls /api/org/import for imports, which is handled by OrganizationImportView
        # This method is kept for API compatibility if needed, or can be removed.
        pass


from rest_framework.views import APIView

class OrganizationImportView(APIView):
    """通用导入接口"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        import_type = request.data.get('type')
        csv_data = request.data.get('csv')
        
        if not import_type or not csv_data:
            return Response({'error': 'type和csv参数必填'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_count = 0
        skipped_count = 0
        errors = []
        
        lines = csv_data.strip().split('\n')
        
        try:
            with transaction.atomic():
                if import_type == 'colleges':
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        # Format: Name
                        name = line
                        if College.objects.filter(name=name, is_deleted=False).exists():
                            skipped_count += 1
                            continue
                            
                        # Generate code
                        existing = College.objects.filter(is_deleted=False).values_list('code', flat=True)
                        nums = [int(c) for c in existing if isinstance(c, str) and c.isdigit() and len(c)==2]
                        next_num = (max(nums) + 1) if nums else 1
                        code = f"{next_num:02d}"
                        
                        College.objects.create(name=name, code=code)
                        created_count += 1
                        
                elif import_type == 'departments':
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        # Format: Name,CollegeName
                        parts = line.split(',')
                        if len(parts) < 2:
                            errors.append(f'格式错误: {line}')
                            continue
                            
                        name = parts[0].strip()
                        college_name = parts[1].strip()
                        
                        college = College.objects.filter(name=college_name, is_deleted=False).first()
                        if not college:
                            errors.append(f'学院不存在: {college_name}')
                            continue
                            
                        if Major.objects.filter(name=name, college=college, is_deleted=False).exists():
                            skipped_count += 1
                            continue
                            
                        # Generate code
                        existing = Major.objects.filter(is_deleted=False).values_list('code', flat=True)
                        nums = [int(c) for c in existing if isinstance(c, str) and c.isdigit() and len(c)==3]
                        next_num = (max(nums) + 1) if nums else 1
                        code = f"{next_num:03d}"
                        while Major.objects.filter(code=code, is_deleted=False).exists():
                             next_num += 1
                             code = f"{next_num:03d}"
                        
                        Major.objects.create(name=name, college=college, code=code)
                        created_count += 1
                        
                else:
                    return Response({'error': '不支持的导入类型'}, status=status.HTTP_400_BAD_REQUEST)
                    
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'created': created_count,
            'skipped': skipped_count,
            'errors': errors
        })


class SystemDictionaryViewSet(viewsets.ReadOnlyModelViewSet):
    """系统字典视图集"""
    queryset = SystemDictionary.objects.filter(is_active=True)
    serializer_class = SystemDictionarySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['dict_type']
    search_fields = ['dict_key', 'dict_value']
    ordering_fields = ['dict_type', 'sort_order']
    ordering = ['dict_type', 'sort_order']
    
    @action(detail=False, methods=['get'])
    def duration_types(self, request):
        """获取学制类型字典"""
        duration_dicts = self.get_queryset().filter(dict_type='duration_type')
        serializer = self.get_serializer(duration_dicts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def position_types(self, request):
        """获取职务类型字典"""
        position_dicts = self.get_queryset().filter(dict_type='position_type')
        serializer = self.get_serializer(position_dicts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def gender_types(self, request):
        """获取性别类型字典"""
        gender_dicts = self.get_queryset().filter(dict_type='gender')
        serializer = self.get_serializer(gender_dicts, many=True)
        return Response(serializer.data)


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """操作日志视图集"""
    queryset = OperationLog.objects.all()
    serializer_class = OperationLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['operation_type', 'table_name', 'user_id']
    search_fields = ['table_name', 'record_id']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据用户权限过滤查询集"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_authenticated:
            return queryset.none()
        
        if not hasattr(self.request.user, 'teacher_profile'):
            return queryset.none()
        
        teacher = self.request.user.teacher_profile
        
        # 系统管理员可以查看所有日志
        if teacher.position_type == 'super_admin':
            return queryset
        
        # 学院管理员只能查看本学院相关的日志
        if teacher.position_type in ['dean', 'vice_dean']:
            # 这里需要更复杂的逻辑来过滤本学院相关的日志
            # 暂时返回用户自己的操作日志
            return queryset.filter(user_id=self.request.user.id)
        
        # 普通教师只能查看自己的操作日志
        if teacher.position_type in ['teacher', 'head_teacher']:
            return queryset.filter(user_id=self.request.user.id)
        
        return queryset.none()
    
    @action(detail=False, methods=['get'])
    def my_logs(self, request):
        """获取当前用户的操作日志"""
        logs = self.get_queryset().filter(user_id=request.user.id)
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
