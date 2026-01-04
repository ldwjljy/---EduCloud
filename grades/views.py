from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.db.models import Avg, Count, Q, Case, When, IntegerField

from .models import Grade
from .serializers import (
    GradeSerializer,
    GradeCreateUpdateSerializer,
    GradeStatisticsSerializer,
)
from accounts.permissions import IsTeacherOrAdminOrReadOnly
from accounts.models import StudentProfile, TeacherProfile
from courses.models import Course, CourseSchedule
from organization.models import College, Major, Class as SchoolClass


class GradeViewSet(viewsets.ModelViewSet):
    """成绩相关 API 视图集"""

    queryset = Grade.objects.select_related(
        'student__user_profile__user',
        'student__school_class__major__college',
        'course__teacher__user_profile__user',
    ).all()
    permission_classes = [IsAuthenticated, IsTeacherOrAdminOrReadOnly]
    pagination_class = None  # 禁用分页，返回所有数据

    # ------------------------ 基础配置 ------------------------

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GradeCreateUpdateSerializer
        return GradeSerializer

    def get_queryset(self):
        """根据用户角色过滤数据"""
        user = self.request.user
        queryset = Grade.objects.select_related(
            'student__user_profile__user',
            'student__school_class__major__college',
            'course__teacher__user_profile__user',
        ).all()

        # 超级管理员可以看到所有成绩
        if getattr(user, 'is_superuser', False):
            return self._apply_filters(queryset)

        profile = getattr(user, 'profile', None)
        if not profile:
            return Grade.objects.none()

        role = profile.role

        # 校长、副校长可以看所有成绩
        if role in ['super_admin', 'principal', 'vice_principal']:
            return self._apply_filters(queryset)

        # 院长、副院长可以看自己学院的成绩
        if role in ['dean', 'vice_dean']:
            admin_profile = getattr(profile, 'administrator_profile', None)
            if admin_profile and admin_profile.college:
                queryset = queryset.filter(
                    student__school_class__major__college=admin_profile.college
                )
                return self._apply_filters(queryset)
            return Grade.objects.none()

        # 班主任可以看自己班级的成绩
        if role == 'head_teacher':
            teacher = getattr(profile, 'teacher_profile', None)
            if not teacher:
                return Grade.objects.none()
            managed_classes = SchoolClass.objects.filter(head_teacher=teacher)
            queryset = queryset.filter(student__school_class__in=managed_classes)
            return self._apply_filters(queryset)

        # 教师可以看自己所教课程的成绩
        if role == 'teacher':
            teacher = getattr(profile, 'teacher_profile', None)
            if not teacher:
                return Grade.objects.none()
            course_ids = CourseSchedule.objects.filter(teacher=teacher).values_list(
                'course_id', flat=True
            ).distinct()
            queryset = queryset.filter(course_id__in=list(course_ids))
            return self._apply_filters(queryset)

        # 学生只能看自己的成绩
        if role == 'student':
            student = getattr(profile, 'student_profile', None)
            if not student:
                return Grade.objects.none()
            queryset = queryset.filter(student=student)
            return self._apply_filters(queryset)

        return Grade.objects.none()

    def _apply_filters(self, queryset):
        """通用查询参数过滤（学院/专业/班级/课程/学生名/是否及格/是否审核）"""
        params = self.request.query_params

        student_id = params.get('student_id')
        if student_id:
            queryset = queryset.filter(student__student_id=student_id)

        student_name = params.get('student_name')
        if student_name:
            queryset = queryset.filter(
                Q(student__user_profile__user__first_name__icontains=student_name)
                | Q(student__user_profile__user__last_name__icontains=student_name)
                | Q(student__user_profile__user__username__icontains=student_name)
            )

        course_id = params.get('course_id')
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        class_id = params.get('class_id')
        if class_id:
            queryset = queryset.filter(student__school_class__class_id=class_id)

        major_id = params.get('major_id')
        if major_id:
            queryset = queryset.filter(student__school_class__major_id=major_id)

        college_id = params.get('college_id')
        if college_id:
            queryset = queryset.filter(
                student__school_class__major__college_id=college_id
            )

        is_passed = params.get('is_passed')
        if is_passed == 'true':
            queryset = queryset.filter(score__gte=60)
        elif is_passed == 'false':
            queryset = queryset.filter(score__lt=60)

        approved = params.get('approved')
        if approved == 'true':
            queryset = queryset.filter(approved=True)
        elif approved == 'false':
            queryset = queryset.filter(approved=False)

        return queryset

    # ------------------------ 通用查询接口 ------------------------

    @action(detail=False, methods=['get'])
    def my_grades(self, request):
        """学生查看自己的成绩"""
        user = request.user
        profile = getattr(user, 'profile', None)

        if not profile or profile.role != 'student':
            return Response(
                {'error': '只有学生可以访问此接口'},
                status=status.HTTP_403_FORBIDDEN,
            )

        student = getattr(profile, 'student_profile', None)
        if not student:
            return Response(
                {'error': '学生信息不存在'},
                status=status.HTTP_404_NOT_FOUND,
            )

        grades = Grade.objects.filter(student=student).select_related(
            'course__teacher__user_profile__user',
            'student__school_class__major__college',
        )

        course_id = request.query_params.get('course_id')
        if course_id:
            grades = grades.filter(course_id=course_id)

        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def class_grades(self, request):
        """班主任 / 管理员查看班级成绩"""
        user = request.user
        profile = getattr(user, 'profile', None)

        if not profile:
            return Response(
                {'error': '用户信息不存在'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if profile.role not in [
            'head_teacher',
            'super_admin',
            'principal',
            'vice_principal',
            'dean',
            'vice_dean',
        ]:
            return Response(
                {'error': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if profile.role == 'head_teacher':
            teacher = getattr(profile, 'teacher_profile', None)
            if not teacher:
                return Response(
                    {'error': '教师信息不存在'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            managed_classes = SchoolClass.objects.filter(head_teacher=teacher)
            grades = Grade.objects.filter(
                student__school_class__in=managed_classes
            ).select_related(
                'student__user_profile__user',
                'student__school_class__major__college',
                'course__teacher__user_profile__user',
            )
        else:
            grades = Grade.objects.all().select_related(
                'student__user_profile__user',
                'student__school_class__major__college',
                'course__teacher__user_profile__user',
            )

        grades = self._apply_filters(grades)
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def teacher_grades(self, request):
        """教师管理自己课程的成绩（按单条成绩列表）"""
        user = request.user
        profile = getattr(user, 'profile', None)

        teacher = getattr(profile, 'teacher_profile', None)
        # 只要用户是任课教师（在课程表中有课），不再强制要求 role 必须是 teacher/head_teacher
        if not profile or not teacher:
            return Response(
                {'error': '教师信息不存在'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 检查该教师是否在课程表中实际授课
        if not CourseSchedule.objects.filter(teacher=teacher).exists():
            return Response(
                {'error': '当前账号未在课表中担任任课教师，无法通过教师端管理成绩'},
                status=status.HTTP_403_FORBIDDEN,
            )

        course_ids = CourseSchedule.objects.filter(teacher=teacher).values_list(
            'course_id', flat=True
        ).distinct()
        grades = Grade.objects.filter(course_id__in=list(course_ids)).select_related(
            'student__user_profile__user',
            'student__school_class__major__college',
            'course__teacher__user_profile__user',
        )

        grades = self._apply_filters(grades)
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)

    # ------------------------ 统计 ------------------------

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """成绩统计 - 按学院/专业/班级"""
        user = request.user
        profile = getattr(user, 'profile', None)

        if not profile:
            return Response(
                {'error': '用户信息不存在'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if profile.role not in [
            'super_admin',
            'principal',
            'vice_principal',
            'dean',
            'vice_dean',
        ]:
            return Response(
                {'error': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )

        level = request.query_params.get('level', 'college')
        college_id = request.query_params.get('college_id')
        major_id = request.query_params.get('major_id')
        class_id = request.query_params.get('class_id')

        # 院长仅能看自己学院
        if profile.role in ['dean', 'vice_dean']:
            admin_profile = getattr(profile, 'administrator_profile', None)
            if admin_profile and admin_profile.college:
                college_id = admin_profile.college.id

        statistics_data = []

        if level == 'college':
            colleges = College.objects.filter(is_deleted=False)
            if college_id:
                colleges = colleges.filter(id=college_id)
            for college in colleges:
                stats = self._calculate_statistics(college_id=college.id)
                if stats['total_grades'] > 0:
                    stats['level'] = 'college'
                    stats['college_id'] = college.id
                    stats['college_name'] = college.name
                    statistics_data.append(stats)
        elif level == 'major':
            majors = Major.objects.filter(is_deleted=False)
            if college_id:
                majors = majors.filter(college_id=college_id)
            if major_id:
                majors = majors.filter(id=major_id)
            for major in majors:
                stats = self._calculate_statistics(major_id=major.id)
                if stats['total_grades'] > 0:
                    stats['level'] = 'major'
                    stats['college_id'] = major.college.id
                    stats['college_name'] = major.college.name
                    stats['major_id'] = major.id
                    stats['major_name'] = major.name
                    statistics_data.append(stats)
        elif level == 'class':
            classes = SchoolClass.objects.filter(is_deleted=False).select_related(
                'major__college'
            )
            if college_id:
                classes = classes.filter(major__college_id=college_id)
            if major_id:
                classes = classes.filter(major_id=major_id)
            if class_id:
                classes = classes.filter(class_id=class_id)
            for school_class in classes:
                stats = self._calculate_statistics(class_id=school_class.class_id)
                if stats['total_grades'] > 0:
                    stats['level'] = 'class'
                    stats['college_id'] = school_class.major.college.id
                    stats['college_name'] = school_class.major.college.name
                    stats['major_id'] = school_class.major.id
                    stats['major_name'] = school_class.major.name
                    stats['class_id'] = school_class.class_id
                    stats['class_name'] = school_class.name
                    statistics_data.append(stats)

        serializer = GradeStatisticsSerializer(statistics_data, many=True)
        return Response(serializer.data)

    def _calculate_statistics(self, college_id=None, major_id=None, class_id=None):
        grades = Grade.objects.all()
        if college_id:
            grades = grades.filter(
                student__school_class__major__college_id=college_id
            )
        if major_id:
            grades = grades.filter(student__school_class__major_id=major_id)
        if class_id:
            grades = grades.filter(student__school_class__class_id=class_id)

        stats = grades.aggregate(
            total_grades=Count('id'),
            average_score=Avg('score'),
            passed_count=Count(
                Case(When(score__gte=60, then=1), output_field=IntegerField())
            ),
            failed_count=Count(
                Case(When(score__lt=60, then=1), output_field=IntegerField())
            ),
            excellent_count=Count(
                Case(When(score__gte=90, then=1), output_field=IntegerField())
            ),
            good_count=Count(
                Case(
                    When(score__gte=80, score__lt=90, then=1),
                    output_field=IntegerField(),
                )
            ),
        )

        if college_id:
            total_students = StudentProfile.objects.filter(
                school_class__major__college_id=college_id
            ).count()
        elif major_id:
            total_students = StudentProfile.objects.filter(
                school_class__major_id=major_id
            ).count()
        elif class_id:
            total_students = StudentProfile.objects.filter(
                school_class__class_id=class_id
            ).count()
        else:
            total_students = StudentProfile.objects.count()

        total_grades = stats['total_grades'] or 0
        average_score = float(stats['average_score'] or 0)
        passed_count = stats['passed_count'] or 0
        failed_count = stats['failed_count'] or 0
        excellent_count = stats['excellent_count'] or 0
        good_count = stats['good_count'] or 0

        pass_rate = (passed_count / total_grades * 100) if total_grades > 0 else 0
        excellent_rate = (
            excellent_count / total_grades * 100 if total_grades > 0 else 0
        )
        good_rate = good_count / total_grades * 100 if total_grades > 0 else 0

        return {
            'total_students': total_students,
            'total_grades': total_grades,
            'average_score': round(average_score, 2),
            'pass_rate': round(pass_rate, 2),
            'excellent_rate': round(excellent_rate, 2),
            'good_rate': round(good_rate, 2),
            'passed_count': passed_count,
            'failed_count': failed_count,
        }

    # ------------------------ 批量创建与导出 ------------------------

    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """批量创建成绩（单条模式使用）"""
        user = request.user
        profile = getattr(user, 'profile', None)

        if not profile or profile.role not in [
            'teacher',
            'head_teacher',
            'super_admin',
            'principal',
            'vice_principal',
        ]:
            return Response(
                {'error': '权限不足'},
                status=status.HTTP_403_FORBIDDEN,
            )

        grades_data = request.data.get('grades', [])
        if not grades_data:
            return Response(
                {'error': '没有提供成绩数据'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_grades = []
        errors = []

        for grade_data in grades_data:
            serializer = GradeCreateUpdateSerializer(data=grade_data)
            if serializer.is_valid():
                try:
                    grade = serializer.save()
                    created_grades.append(GradeSerializer(grade).data)
                except Exception as e:
                    errors.append({'data': grade_data, 'error': str(e)})
            else:
                errors.append({'data': grade_data, 'error': serializer.errors})

        return Response(
            {
                'created': len(created_grades),
                'failed': len(errors),
                'grades': created_grades,
                'errors': errors,
            }
        )

    @action(detail=False, methods=['get'])
    def export(self, request):
        """导出成绩数据（JSON 格式）"""
        queryset = self.get_queryset()
        serializer = GradeSerializer(queryset, many=True)
        return Response(serializer.data)

    # ------------------------ 教师端：授课班级概览 ------------------------

    @action(detail=False, methods=['get'])
    def teacher_classes(self, request):
        """教师查看自己授课的（课程 + 班级）列表及简要统计"""
        user = request.user
        profile = getattr(user, 'profile', None)

        teacher = getattr(profile, 'teacher_profile', None)
        # 只要用户是任课教师（在课程表中有课），不再强制要求 role 必须是 teacher/head_teacher
        if not profile or not teacher:
            return Response(
                {'error': '教师信息不存在'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 检查该教师是否在课程表中实际授课
        if not CourseSchedule.objects.filter(teacher=teacher).exists():
            return Response(
                {'error': '当前账号未在课表中担任任课教师，无法查看授课班级列表'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 所有课程表中该教师授课的 (课程, 班级) 组合
        schedules = CourseSchedule.objects.filter(teacher=teacher).select_related(
            'course', 'school_class'
        )

        combo_map = {}
        for cs in schedules:
            if not cs.course or not cs.school_class:
                continue
            key = (cs.course_id, cs.school_class.class_id)
            if key not in combo_map:
                combo_map[key] = {'course': cs.course, 'school_class': cs.school_class}

        if not combo_map:
            return Response([])

        # 班级学生人数
        class_ids = [info['school_class'].id for info in combo_map.values()]
        students_qs = StudentProfile.objects.filter(school_class_id__in=class_ids)
        students_count_map = (
            students_qs.values('school_class_id')
            .annotate(c=Count('id'))
            .order_by()
        )
        students_count_dict = {
            row['school_class_id']: row['c'] for row in students_count_map
        }

        result = []
        for (course_id, class_code), info in combo_map.items():
            course = info['course']
            school_class = info['school_class']

            student_total = students_count_dict.get(school_class.id, 0)

            grades = Grade.objects.filter(
                course_id=course_id, student__school_class=school_class
            )
            stats = grades.aggregate(
                total_grades=Count('id'),
                avg_score=Avg('score'),
                passed_count=Count(
                    Case(When(score__gte=60, then=1), output_field=IntegerField())
                ),
            )

            total_grades = stats['total_grades'] or 0
            avg_score = float(stats['avg_score'] or 0) if total_grades > 0 else 0.0
            passed_count = stats['passed_count'] or 0
            pass_rate = (
                passed_count / total_grades * 100 if total_grades > 0 else 0.0
            )

            result.append(
                {
                    'course_id': course.id,
                    'course_name': course.name,
                    'class_id': school_class.class_id,
                    'class_name': school_class.name,
                    'student_count': student_total,
                    'avg_score': round(avg_score, 2),
                    'pass_rate': round(pass_rate, 2),
                }
            )

        result.sort(key=lambda x: (x['course_name'], x['class_name']))
        return Response(result)

    # ------------------------ 班级学生成绩（批量录入用） ------------------------

    @action(detail=False, methods=['get'])
    def course_classes(self, request):
        """获取某课程对应的授课班级列表"""
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {'error': '请提供课程ID'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedules = CourseSchedule.objects.filter(course_id=course_id).select_related(
            'school_class__major__college'
        )

        classes = {}
        for sched in schedules:
            if not sched.school_class:
                continue
            cls = sched.school_class
            if cls.class_id not in classes:
                classes[cls.class_id] = {
                    'id': cls.id,
                    'class_id': cls.class_id,
                    'name': cls.name,
                    'major_name': cls.major.name if cls.major else '-',
                    'college_name': cls.major.college.name
                    if cls.major and cls.major.college
                    else '-',
                    'enrollment_year': cls.enrollment_year,
                }

        return Response(list(classes.values()))

    @action(detail=False, methods=['get'])
    def class_students_grades(self, request):
        """获取班级学生的成绩列表（用于批量录入/教师端录入）"""
        course_id = request.query_params.get('course_id')
        class_id = request.query_params.get('class_id')

        if not course_id or not class_id:
            return Response(
                {'error': '请提供课程ID和班级ID'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            school_class = SchoolClass.objects.get(class_id=class_id)
        except SchoolClass.DoesNotExist:
            return Response(
                {'error': '班级不存在'},
                status=status.HTTP_404_NOT_FOUND,
            )

        students = StudentProfile.objects.filter(
            school_class=school_class
        ).select_related('user_profile__user').order_by('student_id')

        result = []
        for stu in students:
            try:
                grade = Grade.objects.get(student=stu, course_id=course_id)
                grade_data = {
                    'grade_id': grade.id,
                    'regular_score': float(grade.regular_score)
                    if grade.regular_score is not None
                    else None,
                    'final_score': float(grade.final_score)
                    if grade.final_score is not None
                    else None,
                    'score': float(grade.score),
                    'regular_weight': float(grade.regular_weight),
                    'final_weight': float(grade.final_weight),
                    'approved': grade.approved,
                }
            except Grade.DoesNotExist:
                grade_data = {
                    'grade_id': None,
                    'regular_score': None,
                    'final_score': None,
                    'score': None,
                    'regular_weight': 60.0,
                    'final_weight': 40.0,
                    'approved': False,
                }
            
            result.append(
                {
                    'student_id': stu.id,
                    'student_number': stu.student_id,
                    'student_name': stu.user_profile.user.first_name
                    or stu.user_profile.user.username,
                    **grade_data,
                }
            )

        return Response(result)

    @action(detail=False, methods=['post'])
    def batch_save_grades(self, request):
        """批量保存/更新成绩（固定权重 60/40）"""
        course_id = request.data.get('course_id')
        class_id = request.data.get('class_id')
        grades_data = request.data.get('grades', [])

        regular_weight = 60
        final_weight = 40

        if not course_id or not class_id:
            return Response(
                {'error': '请提供课程ID和班级ID'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        saved_count = 0
        errors = []

        for gd in grades_data:
            student_pk = gd.get('student_id')
            regular_score = gd.get('regular_score')
            final_score = gd.get('final_score')

            if student_pk is None:
                continue
            if regular_score is None and final_score is None:
                continue

            try:
                student = StudentProfile.objects.get(id=student_pk)
            except StudentProfile.DoesNotExist:
                errors.append(
                    {'student_id': student_pk, 'error': '学生不存在'}
                )
                continue

            try:
                grade, _created = Grade.objects.get_or_create(
                    student=student,
                    course_id=course_id,
                    defaults={
                        'score': 0,
                        'regular_weight': regular_weight,
                        'final_weight': final_weight,
                    },
                )

                if regular_score is not None:
                    grade.regular_score = regular_score
                if final_score is not None:
                    grade.final_score = final_score

                grade.regular_weight = regular_weight
                grade.final_weight = final_weight

                grade.save()  # 模型中会按 60/40 重新计算总评
                saved_count += 1
            except Exception as e:
                errors.append(
                    {'student_id': student_pk, 'error': str(e)}
                )

        return Response(
            {
                'success': True,
                'saved_count': saved_count,
                'errors': errors,
            }
        )

    # ------------------------ Excel 导入/导出成绩表 ------------------------

    @action(detail=False, methods=['get'])
    def class_grades_export(self, request):
        """导出课程+班级的成绩表（Excel xlsx）"""
        course_id = request.query_params.get('course_id')
        class_id = request.query_params.get('class_id')

        if not course_id or not class_id:
            return Response(
                {'error': '请提供课程ID和班级ID'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course_id = int(course_id)
        except (ValueError, TypeError):
            return Response(
                {'error': '课程ID格式错误'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            school_class = SchoolClass.objects.get(class_id=class_id)
        except SchoolClass.DoesNotExist:
            return Response(
                {'error': '班级不存在'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            students = StudentProfile.objects.filter(
                school_class=school_class
            ).select_related('user_profile__user').order_by('student_id')

            grades_map = {
                g.student.id: g
                for g in Grade.objects.filter(
                    student__in=students, course_id=course_id
                ).select_related('student')
            }

            rows = []
            rows.append([f'{school_class.name}成绩表'])
            rows.append(['学号', '姓名', '平时分', '期末分', '总分'])

            for stu in students:
                grade = grades_map.get(stu.id)
                regular = (
                    grade.regular_score
                    if grade and grade.regular_score is not None
                    else ''
                )
                final = (
                    grade.final_score
                    if grade and grade.final_score is not None
                    else ''
                )
                # 总分：优先使用已保存的总分，如果没有则根据平时分和期末分计算（60% + 40%）
                total = ''
                if grade:
                    if grade.score is not None:
                        total = grade.score
                    elif grade.regular_score is not None and grade.final_score is not None:
                        # 计算总分 = 平时分 × 60% + 期末分 × 40%
                        total = round(float(grade.regular_score) * 0.6 + float(grade.final_score) * 0.4, 2)
                
                name = stu.user_profile.user.first_name or stu.user_profile.user.username
                rows.append([stu.student_id, name, regular, final, total])

            import pandas as pd
            from io import BytesIO
            from urllib.parse import quote
            from django.http import HttpResponse

            df = pd.DataFrame(rows)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, header=False, sheet_name='成绩表')
            output.seek(0)

            # 对于二进制文件（Excel），必须使用 HttpResponse 而不是 DRF 的 Response
            # 因为 DRF 的 Response 会尝试将二进制数据序列化为 JSON，导致编码错误
            filename = f'{school_class.name}_成绩表.xlsx'
            # 对文件名进行 URL 编码，确保中文文件名正确显示
            encoded_filename = quote(filename.encode('utf-8'))
            
            resp = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            resp['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
            return resp
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'导出失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def class_grades_import(self, request):
        """导入课程+班级的成绩表（Excel xlsx 文件）"""
        course_id = request.data.get('course_id')
        class_id = request.data.get('class_id')
        file_obj = request.FILES.get('file')

        if not course_id or not class_id or not file_obj:
            return Response(
                {'error': '请提供课程ID、班级ID和Excel文件'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            school_class = SchoolClass.objects.get(class_id=class_id)
        except SchoolClass.DoesNotExist:
            return Response(
                {'error': '班级不存在'},
                status=status.HTTP_404_NOT_FOUND,
            )

        import pandas as pd

        try:
            df = pd.read_excel(file_obj, header=None)
        except Exception as e:
            return Response(
                {'error': f'Excel 文件解析失败: {e}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if df.shape[0] <= 2:
            return Response(
                {'error': 'Excel 内容不足，缺少数据行'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_rows = df.iloc[2:]

        saved_count = 0
        errors = []

        for idx, row in enumerate(data_rows.itertuples(index=False), start=3):
            # row[0]: 学号, row[1]: 姓名, row[2]: 平时分, row[3]: 期末分
            try:
                student_number = str(row[0]).strip()
            except Exception:
                student_number = ''

            if not student_number:
                continue

            # 姓名目前仅作展示，不强校验
            regular_raw = ''
            if len(row) > 2 and row[2] is not None and str(row[2]).strip():
                regular_raw = str(row[2]).strip()
            final_raw = ''
            if len(row) > 3 and row[3] is not None and str(row[3]).strip():
                final_raw = str(row[3]).strip()

            try:
                student = StudentProfile.objects.get(
                    student_id=student_number, school_class=school_class
                )
            except StudentProfile.DoesNotExist:
                errors.append(
                    {
                        'row': idx,
                        'student_number': student_number,
                        'error': '学生不存在或不在该班级',
                    }
                )
                continue

            def parse_score(val):
                if not val:
                    return None
                try:
                    s = float(val)
                    if 0 <= s <= 100:
                        return s
                except Exception:
                    pass
                return None

            regular_score = parse_score(regular_raw)
            final_score = parse_score(final_raw)

            if regular_score is None and final_score is None:
                continue

            try:
                grade, _created = Grade.objects.get_or_create(
                    student=student,
                    course_id=course_id,
                    defaults={
                        'score': 0,
                        'regular_weight': 60,
                        'final_weight': 40,
                    },
                )

                if regular_score is not None:
                    grade.regular_score = regular_score
                if final_score is not None:
                    grade.final_score = final_score

                grade.save()  # 模型中会按 60/40 重新计算
                saved_count += 1
            except Exception as e:
                errors.append(
                    {
                        'row': idx,
                        'student_number': student_number,
                        'error': str(e),
                    }
                )

        return Response(
            {
                'success': True,
                'saved_count': saved_count,
                'errors': errors,
            }
        )
