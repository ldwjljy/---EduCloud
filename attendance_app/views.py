from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Attendance
from django.db.models import Q
from django.utils import timezone
from datetime import date
from .serializers import AttendanceSerializer
from accounts.permissions import IsTeacherOrAdminOrReadOnly
from accounts.models import StudentProfile
from courses.models import CourseSchedule


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('student', 'schedule').all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdminOrReadOnly]
    pagination_class = None  # 禁用分页，返回所有数据

    def _ensure_default_attendance(self, schedule, attendance_date):
        """
        确保课程中所有学生都有默认的考勤记录
        为没有记录的学生自动创建"正常"状态的考勤记录
        优化：使用更高效的查询方式
        """
        if not schedule or not schedule.school_class:
            return
        
        # 使用exists()快速检查是否需要创建记录
        existing_count = Attendance.objects.filter(
            schedule=schedule,
            date=attendance_date
        ).count()
        
        # 获取班级学生数量
        student_count = StudentProfile.objects.filter(
            school_class=schedule.school_class
        ).count()
        
        # 如果已有记录数等于学生数，说明所有学生都有记录，直接返回
        if existing_count >= student_count:
            return
        
        # 只获取需要创建记录的学生ID
        existing_student_ids = Attendance.objects.filter(
            schedule=schedule,
            date=attendance_date
        ).values_list('student_id', flat=True)
        
        students_to_create = StudentProfile.objects.filter(
            school_class=schedule.school_class
        ).exclude(id__in=existing_student_ids).only('id')
        
        if students_to_create.exists():
            attendance_list = [
                Attendance(
                    student_id=student.id,
                    schedule=schedule,
                    date=attendance_date,
                    status='present',
                    remark=''
                )
                for student in students_to_create
            ]
            
            if attendance_list:
                try:
                    Attendance.objects.bulk_create(attendance_list, ignore_conflicts=True)
                except Exception:
                    # 如果批量创建失败，使用get_or_create逐个创建
                    for att in attendance_list:
                        Attendance.objects.get_or_create(
                            student_id=att.student_id,
                            schedule=att.schedule,
                            date=att.date,
                            defaults={'status': att.status, 'remark': att.remark}
                        )

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        if not profile:
            return Attendance.objects.none()
        params = self.request.query_params
        college = params.get('college')
        department = params.get('department')
        klass = params.get('class')
        student_id = params.get('student')
        date_param = params.get('date')
        status_param = params.get('status')

        def apply_filters(qs):
            schedule_id = params.get('schedule')
            if schedule_id:
                # 支持多个schedule ID（用逗号分隔）
                if ',' in str(schedule_id):
                    schedule_ids = [int(sid.strip()) for sid in str(schedule_id).split(',') if sid.strip().isdigit()]
                    if schedule_ids:
                        qs = qs.filter(schedule_id__in=schedule_ids)
                else:
                    try:
                        qs = qs.filter(schedule_id=int(schedule_id))
                    except (ValueError, TypeError):
                        pass
            if student_id:
                qs = qs.filter(student_id=student_id)
            if klass:
                qs = qs.filter(student__school_class_id=klass)
            if department:
                qs = qs.filter(student__school_class__major_id=department)
            if college:
                qs = qs.filter(student__school_class__major__college_id=college)
            if date_param:
                qs = qs.filter(date=date_param)
            if status_param:
                qs = qs.filter(status=status_param)
            q = params.get('q')
            if q:
                qs = qs.filter(
                    Q(student__student_id__icontains=q) |
                    Q(student__user_profile__user__username__icontains=q) |
                    Q(student__user_profile__user__first_name__icontains=q) |
                    Q(student__school_class__name__icontains=q) |
                    Q(student__school_class__major__name__icontains=q) |
                    Q(student__school_class__major__college__name__icontains=q) |
                    Q(schedule__course__name__icontains=q)
                )
            return qs

        role = profile.role
        if role in ['super_admin', 'principal', 'vice_principal']:
            # 管理员查看时，如果传入了课程和日期，也自动为对应课程的所有学生生成默认考勤记录
            schedule_id_param = params.get('schedule')
            attendance_date = None
            if date_param:
                try:
                    if isinstance(date_param, str):
                        attendance_date = date.fromisoformat(date_param)
                    else:
                        attendance_date = date_param
                except (ValueError, TypeError):
                    attendance_date = timezone.now().date()

            if self.request.method == 'GET' and schedule_id_param and attendance_date:
                try:
                    # 支持多个 schedule ID
                    schedule_ids_to_process = []
                    if ',' in str(schedule_id_param):
                        schedule_ids_to_process = [
                            int(sid.strip())
                            for sid in str(schedule_id_param).split(',')
                            if sid.strip().isdigit()
                        ]
                    else:
                        try:
                            schedule_ids_to_process = [int(schedule_id_param)]
                        except (ValueError, TypeError):
                            schedule_ids_to_process = []

                    # 管理员不受教师限制，可以为选中的所有排课生成记录
                    schedules_to_process = CourseSchedule.objects.filter(
                        id__in=schedule_ids_to_process
                    ).select_related('school_class')

                    for schedule in schedules_to_process:
                        try:
                            self._ensure_default_attendance(schedule, attendance_date)
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(
                                f"管理员自动生成考勤记录失败 (schedule_id={schedule.id}): {e}",
                                exc_info=True
                            )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"管理员自动生成考勤记录失败: {e}", exc_info=True)

            qs = Attendance.objects.select_related('student', 'schedule', 'schedule__course',
                                                  'student__school_class', 'student__school_class__major',
                                                  'student__school_class__major__college',
                                                  'student__user_profile', 'student__user_profile__user').all()
            # 确保去重
            qs = qs.distinct()
            return apply_filters(qs)
        if role in ['teacher', 'head_teacher']:
            teacher = getattr(profile, 'teacher_profile', None)
            if not teacher:
                return Attendance.objects.none()
            # 获取教师的所有课程安排（schedule）
            allowed_schedules = CourseSchedule.objects.filter(teacher=teacher)
            schedule_ids = list(allowed_schedules.values_list('id', flat=True))
            
            # 如果是查询操作且有schedule和date，自动生成默认记录
            # 优化：只在必要时生成，避免每次查询都执行
            schedule_id_param = params.get('schedule')
            attendance_date = None
            if date_param:
                try:
                    if isinstance(date_param, str):
                        attendance_date = date.fromisoformat(date_param)
                    else:
                        attendance_date = date_param
                except (ValueError, TypeError):
                    attendance_date = timezone.now().date()
            
            # 优化：只在明确需要时才生成默认记录，并且使用缓存避免重复生成
            if self.request.method == 'GET' and schedule_id_param and attendance_date:
                try:
                    # 支持多个schedule ID
                    schedule_ids_to_process = []
                    if ',' in str(schedule_id_param):
                        schedule_ids_to_process = [int(sid.strip()) for sid in str(schedule_id_param).split(',') if sid.strip().isdigit()]
                    else:
                        try:
                            schedule_ids_to_process = [int(schedule_id_param)]
                        except (ValueError, TypeError):
                            pass
                    
                    # 只为教师有权限的schedule生成记录
                    # 优化：批量处理，减少数据库查询
                    schedules_to_process = allowed_schedules.filter(
                        id__in=[sid for sid in schedule_ids_to_process if sid in schedule_ids]
                    ).select_related('school_class')
                    
                    for schedule in schedules_to_process:
                        try:
                            self._ensure_default_attendance(schedule, attendance_date)
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.error(f"自动生成考勤记录失败 (schedule_id={schedule.id}): {e}", exc_info=True)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"自动生成考勤记录失败: {e}", exc_info=True)
            
            # 直接通过schedule查询考勤记录
            if schedule_ids:
                qs = Attendance.objects.filter(schedule_id__in=schedule_ids).select_related(
                    'student', 'schedule', 'schedule__course',
                    'student__school_class', 'student__school_class__major',
                    'student__school_class__major__college',
                    'student__user_profile', 'student__user_profile__user'
                )
            else:
                qs = Attendance.objects.none()
            
            # 如果是班主任，还要包含其管理的班级的所有考勤记录
            # 优化：使用更高效的查询方式，避免union
            try:
                from personnel.models import Teacher as PersonnelTeacher
                from organization.models import Class
                try:
                    pt = PersonnelTeacher.objects.get(employee_id=teacher.teacher_id)
                    head_class_ids = list(Class.objects.filter(head_teacher=pt).values_list('id', flat=True))
                    if head_class_ids:
                        # 将班主任管理的班级的考勤记录也加入查询
                        if schedule_ids:
                            # 合并schedule和班级条件
                            qs = Attendance.objects.filter(
                                Q(schedule_id__in=schedule_ids) | Q(student__school_class_id__in=head_class_ids)
                            ).select_related(
                                'student', 'schedule', 'schedule__course',
                                'student__school_class', 'student__school_class__major',
                                'student__school_class__major__college',
                                'student__user_profile', 'student__user_profile__user'
                            )
                        else:
                            qs = Attendance.objects.filter(
                                student__school_class_id__in=head_class_ids
                            ).select_related(
                                'student', 'schedule', 'schedule__course',
                                'student__school_class', 'student__school_class__major',
                                'student__school_class__major__college',
                                'student__user_profile', 'student__user_profile__user'
                            )
                except PersonnelTeacher.DoesNotExist:
                    pass
            except Exception:
                # 如果导入失败或查询失败，忽略班主任的班级
                pass
            
            # 确保去重
            qs = qs.distinct()
            return apply_filters(qs)
        if role == 'student':
            student = getattr(profile, 'student_profile', None)
            if not student:
                return Attendance.objects.none()
            qs = Attendance.objects.filter(student=student).select_related(
                'student', 'schedule', 'schedule__course',
                'student__school_class', 'student__school_class__major',
                'student__school_class__major__college',
                'student__user_profile', 'student__user_profile__user'
            )
            # 确保去重
            qs = qs.distinct()
            return apply_filters(qs)
        return Attendance.objects.none()
