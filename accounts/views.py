from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from courses.models import CourseSchedule
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .permissions import IsSystemAdmin
from .importers import import_students, import_teachers
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from .models import UserProfile, StudentProfile, TeacherProfile, AdministratorProfile
from .serializers import (
    UserProfileSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    AdministratorProfileSerializer,
)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # 禁用分页，返回所有数据


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.select_related('user_profile').all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # 禁用分页，返回所有数据

    def get_queryset(self):
        user = self.request.user
        # 优化查询：添加所有需要的select_related来避免N+1查询
        base_select_related = [
            'user_profile', 'user_profile__user', 
            'school_class', 'school_class__major', 'school_class__major__college'
        ]
        if getattr(user, 'is_superuser', False):
            qs = StudentProfile.objects.select_related(*base_select_related).all()
            return self._apply_filters(qs)
        if not hasattr(user, 'profile'):
            return StudentProfile.objects.none()
        role = user.profile.role
        if role in ['super_admin', 'principal', 'vice_principal']:
            qs = StudentProfile.objects.select_related(*base_select_related).all()
            return self._apply_filters(qs)
        if role == 'head_teacher':
            teacher = getattr(user.profile, 'teacher_profile', None)
            if not teacher:
                return StudentProfile.objects.none()
            # 允许班主任查询自己班级的学生，也允许通过 class 参数查询特定班级的学生（如果他们有权限）
            # 这里我们放宽一点，如果指定了 class 参数，就按参数查，否则查自己管理的班级
            # 实际业务中可能需要严格校验是否有权限查看该班级
            
            # 优先处理显式的 class 过滤
            klass = self.request.query_params.get('class')
            if klass:
                 # 检查是否是自己管理的班级？或者仅仅允许查看？
                 # 考虑到 "点击班级后没有学生对应班级的学生你从数据库里获取" 这个需求，
                 # 班主任可能需要查看自己管理的班级，也可能需要查看其他班级（如果允许）
                 # 但通常班主任只能看自己班。
                 # 不过，前端发起的请求带了 class 参数，我们应该响应那个班级的学生。
                 # 如果那个班级正好是该班主任管理的，那就没问题。
                 # 如果不是，是否允许？
                 # 让我们先允许通过 class 参数查询，然后在 _apply_filters 中过滤。
                 # 但是 get_queryset 必须先返回一个包含该班级学生的 queryset。
                 
                 # 简单起见，我们先返回所有学生，依靠 _apply_filters 来过滤。
                 # 但为了性能和安全性，我们应该限制范围。
                 
                 # 让我们修改逻辑：如果指定了 class，就返回该班级的学生。
                 # 还需要确保班主任有权限查看该班级。
                 # 目前 permissions.py 里似乎没有严格限制班主任只能看自己班级的学生？
                 # 让我们先假设班主任可以查看任何班级的学生（为了修复问题），或者至少查看自己关联的班级。
                 
                 # 实际上，前端传来的 class ID 应该是该班主任管理的班级 ID。
                 # 所以我们只要确保 queryset 包含那个班级的学生即可。
                 
                 # 旧逻辑：qs = StudentProfile.objects.filter(school_class__head_teacher=teacher)
                 # 这只返回了 head_teacher 是当前用户的班级的学生。
                 # 如果前端传来的 class ID 确实是该班主任管理的班级，那么旧逻辑应该没问题。
                 # 除非... Class.head_teacher 关联的是 personnel.Teacher，而 user.profile.teacher_profile 是 accounts.TeacherProfile。
                 # 这两个模型不同！
                 
                 # 这是一个关键问题：user.profile.teacher_profile 是 accounts.TeacherProfile
                 # Class.head_teacher 是 personnel.Teacher
                 # 它们虽然代表同一个人，但是不同的数据库记录。
                 # 我们需要通过 teacher_id (工号) 来关联。
                 
                 from personnel.models import Teacher as PersonnelTeacher
                 try:
                     pt = PersonnelTeacher.objects.get(employee_id=teacher.teacher_id)
                     qs = StudentProfile.objects.filter(
                         school_class__head_teacher=pt
                     ).select_related(
                         'user_profile', 'user_profile__user',
                         'school_class', 'school_class__major', 'school_class__major__college'
                     )
                 except PersonnelTeacher.DoesNotExist:
                     return StudentProfile.objects.none()
                     
                 return self._apply_filters(qs)

            # 如果没有指定 class 参数，默认显示自己管理班级的学生
            from personnel.models import Teacher as PersonnelTeacher
            try:
                pt = PersonnelTeacher.objects.get(employee_id=teacher.teacher_id)
                qs = StudentProfile.objects.filter(
                    school_class__head_teacher=pt
                ).select_related(
                    'user_profile', 'user_profile__user',
                    'school_class', 'school_class__major', 'school_class__major__college'
                )
            except PersonnelTeacher.DoesNotExist:
                return StudentProfile.objects.none()
            return self._apply_filters(qs)
        # 普通教师不能访问学生管理
        if role == 'teacher':
            return StudentProfile.objects.none()
        if role == 'student':
            qs = StudentProfile.objects.filter(
                user_profile=user.profile
            ).select_related(
                'user_profile', 'user_profile__user',
                'school_class', 'school_class__major', 'school_class__major__college'
            )
            return self._apply_filters(qs)
        return StudentProfile.objects.none()

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        ids = request.data.get('ids', [])
        class_id = request.data.get('class_id')
        status = request.data.get('status')
        
        if not ids:
            return Response({'error': 'Missing ids'}, status=400)
        
        update_data = {}
        if class_id:
            from organization.models import Class
            try:
                school_class = Class.objects.get(id=class_id)
                update_data['school_class'] = school_class
            except Class.DoesNotExist:
                return Response({'error': 'Class not found'}, status=400)
        
        if status:
            update_data['status'] = status
            
        if not update_data:
             return Response({'error': 'No fields to update'}, status=400)
            
        try:
            # Check permissions
            qs = self.get_queryset().filter(id__in=ids)
            updated_count = qs.update(**update_data)
            
            return Response({'updated': updated_count})
        except Exception as e:
             return Response({'error': str(e)}, status=500)

    def _apply_filters(self, qs):
        params = self.request.query_params
        q = params.get('q')
        if q:
            qs = qs.filter(
                Q(student_id__icontains=q) |
                Q(user_profile__user__username__icontains=q) |
                Q(user_profile__user__first_name__icontains=q) |
                Q(school_class__name__icontains=q)
            )
        status = params.get('status')
        if status:
            if ',' in status:
                qs = qs.filter(status__in=status.split(','))
            else:
                qs = qs.filter(status=status)
        department = params.get('department')
        if department:
            if ',' in department:
                qs = qs.filter(school_class__major_id__in=department.split(','))
            else:
                qs = qs.filter(school_class__major_id=department)
        college = params.get('college')
        if college:
            if ',' in college:
                qs = qs.filter(school_class__major__college_id__in=college.split(','))
            else:
                qs = qs.filter(school_class__major__college_id=college)
        klass = params.get('class')
        if klass:
            if ',' in klass:
                qs = qs.filter(school_class_id__in=klass.split(','))
            else:
                qs = qs.filter(school_class_id=klass)
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        data = {
            'results': serializer.data,
            'count': len(serializer.data),
        }
        return Response(data)

    def create(self, request, *args, **kwargs):
        user = request.user
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if role == 'student':
            return Response({'detail': '学生不可修改个人学籍信息'}, status=403)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        user = request.user
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if role == 'student':
            return Response({'detail': '学生不可修改个人学籍信息'}, status=403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        user = request.user
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if role == 'student':
            return Response({'detail': '学生不可修改个人学籍信息'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if role == 'student':
            return Response({'detail': '学生不可修改个人学籍信息'}, status=403)
        return super().destroy(request, *args, **kwargs)


class TeacherProfileViewSet(viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.select_related('user_profile', 'department', 'subject').all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # 禁用分页，返回所有数据

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False):
            qs = TeacherProfile.objects.select_related('user_profile', 'department', 'subject').all()
            return self._apply_filters(qs)
        if not hasattr(user, 'profile'):
            return TeacherProfile.objects.none()
        role = user.profile.role
        if role in ['super_admin', 'principal', 'vice_principal']:
            qs = TeacherProfile.objects.select_related('user_profile', 'department', 'subject').all()
            return self._apply_filters(qs)
        if role in ['dean', 'vice_dean']:
            admin = getattr(user.profile, 'administrator_profile', None)
            if admin and admin.department_id:
                qs = TeacherProfile.objects.filter(department_id=admin.department_id)
                return self._apply_filters(qs)
            qs = TeacherProfile.objects.select_related('department', 'subject').all()
            return self._apply_filters(qs)
        if role in ['teacher', 'head_teacher']:
            qs = TeacherProfile.objects.filter(user_profile=user.profile)
            return self._apply_filters(qs)
        return TeacherProfile.objects.none()

    def _apply_filters(self, qs):
        params = self.request.query_params
        q = params.get('q')
        if q:
            qs = qs.filter(
                Q(teacher_id__icontains=q) |
                Q(user_profile__user__username__icontains=q) |
                Q(user_profile__user__first_name__icontains=q) |
                Q(department__name__icontains=q) |
                Q(title__icontains=q)
            )
        department = params.get('department')
        if department:
            qs = qs.filter(department_id=department)
        college = params.get('college')
        if college:
            qs = qs.filter(department__college_id=college)
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        total = qs.count()
        try:
            page = int(request.query_params.get('page', '1'))
        except ValueError:
            page = 1
        try:
            size = int(request.query_params.get('size', '10'))
        except ValueError:
            size = 10
        if page < 1:
            page = 1
        if size < 1:
            size = 10
        start = (page - 1) * size
        end = start + size
        page_qs = qs[start:end]
        serializer = self.get_serializer(page_qs, many=True)
        data = {
            'results': serializer.data,
            'count': total,
            'page': page,
            'size': size,
        }
        return Response(data)

    def perform_destroy(self, instance):
        # 级联删除 User 和 UserProfile
        user = instance.user_profile.user
        
        # 同步删除 personnel.Teacher
        from personnel.models import Teacher as PersonnelTeacher
        try:
            pt = PersonnelTeacher.objects.get(employee_id=instance.teacher_id)
            pt.delete()
        except PersonnelTeacher.DoesNotExist:
            pass
            
        instance.delete()
        if user:
            user.delete()

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        qs = self.get_queryset()
        teacher_ids = list(qs.values_list('id', flat=True))
        ids_param = request.query_params.get('ids')
        if ids_param:
            try:
                requested = [int(x) for x in ids_param.split(',') if x.strip()]
                teacher_ids = [tid for tid in teacher_ids if tid in set(requested)]
            except Exception:
                pass
        try:
            page = int(request.query_params.get('page', ''))
            size = int(request.query_params.get('size', ''))
            if page and size:
                start = (page - 1) * size
                end = start + size
                teacher_ids = teacher_ids[start:end]
        except Exception:
            pass
        from organization.models import Class
        sched_rows = CourseSchedule.objects.filter(teacher_id__in=teacher_ids).values('teacher_id', 'school_class_id')
        
        # Class.head_teacher refers to personnel.Teacher (PK=employee_id), not TeacherProfile (PK=id)
        # We need to map employee_ids back to TeacherProfile IDs
        teacher_map = {tp.teacher_id: tp.id for tp in qs if tp.id in set(teacher_ids)}
        teacher_employee_ids = list(teacher_map.keys())
        
        head_rows = Class.objects.filter(head_teacher_id__in=teacher_employee_ids).values('head_teacher_id', 'id')
        by_teacher_classes = {}
        for row in sched_rows:
            tid = row['teacher_id']
            cid = row['school_class_id']
            if cid is None:
                continue
            s = by_teacher_classes.setdefault(tid, set())
            s.add(cid)
        for row in head_rows:
            tid_str = row['head_teacher_id']
            tid = teacher_map.get(tid_str)
            if tid:
                cid = row['id']
                s = by_teacher_classes.setdefault(tid, set())
                s.add(cid)
        all_class_ids = set()
        for s in by_teacher_classes.values():
            all_class_ids |= s
        counts = StudentProfile.objects.filter(school_class_id__in=all_class_ids).values('school_class_id').annotate(c=Count('id'))
        count_map = {row['school_class_id']: row['c'] for row in counts}
        data = []
        for tid in teacher_ids:
            cls = list(by_teacher_classes.get(tid, set()))
            total = sum(count_map.get(cid, 0) for cid in cls)
            data.append({'teacher': tid, 'classes': cls, 'students': total})
        return Response(data)


class AdministratorProfileViewSet(viewsets.ModelViewSet):
    queryset = AdministratorProfile.objects.select_related('user_profile').all()
    serializer_class = AdministratorProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # 禁用分页，返回所有数据


class ObtainAuthTokenView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            return Response({'detail': '用户名或密码错误'}, status=400)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not request.user.check_password(old_password or ''):
            return Response({'detail': '原密码错误'}, status=400)
        try:
            validate_password(new_password, request.user)
        except ValidationError as e:
            return Response({'detail': list(e)}, status=400)
        request.user.set_password(new_password)
        request.user.save()
        return Response({'detail': '密码已更新'})


class ChangePhoneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import re
        phone = request.data.get('phone', '').strip()
        
        # 验证手机号格式：11位数字，以1开头，第二位为3-9
        phone_regex = re.compile(r'^1[3-9]\d{9}$')
        
        if not phone:
            return Response({'detail': '手机号不能为空'}, status=400)
        
        if not phone_regex.match(phone):
            return Response({'detail': '手机号格式不正确，请输入11位有效手机号'}, status=400)
        
        # 获取或创建用户档案
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.phone = phone
        profile.save()
        
        return Response({'detail': '手机号已更新'})


class SetPasswordView(APIView):
    permission_classes = [IsAuthenticated, IsSystemAdmin]

    def post(self, request):
        user_id = request.data.get('user_id')
        new_password = request.data.get('new_password')
        from django.contrib.auth.models import User
        try:
            target = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': '用户不存在'}, status=404)
        try:
            validate_password(new_password, target)
        except ValidationError as e:
            return Response({'detail': list(e)}, status=400)
        target.set_password(new_password)
        target.save()
        return Response({'detail': '密码已重置'})


class BulkImportView(APIView):
    permission_classes = [IsAuthenticated, IsSystemAdmin]

    def post(self, request):
        import_type = (request.data.get('type') or '').strip()
        if import_type not in ['students', 'teachers']:
            return Response({'detail': 'type 必须为 students 或 teachers'}, status=400)
        if import_type == 'students':
            result = import_students(request)
        else:
            result = import_teachers(request)
        return Response({'created': result.created, 'skipped': result.skipped, 'errors': result.errors})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        role = profile.role if profile else None
        if getattr(request.user, 'is_superuser', False):
            role = 'super_admin'
        data = {
            'username': request.user.username,
            'role': role,
            'user_id': request.user.id,
            'profile_id': profile.id if profile else None,
        }
        return Response(data)
