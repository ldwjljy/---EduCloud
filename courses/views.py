from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Course, TimeSlot, ScheduleTimeConfig, CourseSchedule
from accounts.permissions import IsTeacherOrAdminOrReadOnly, IsAdminOrDeanOrReadOnly
from accounts.models import StudentProfile
from .serializers import (
    CourseSerializer,
    TimeSlotSerializer,
    ScheduleTimeConfigSerializer,
    CourseScheduleSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeanOrReadOnly]
    pagination_class = None  # 禁用分页，返回所有数据

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        qs = Course.objects.select_related('teacher__user_profile__user', 'department__college').all()
        
        # 超级用户可以看所有课程
        if getattr(user, 'is_superuser', False):
            pass
        # 学生：不能查看课程管理列表
        elif profile and profile.role == 'student':
            return Course.objects.none()
        # 教师/班主任：只能看自己的课程
        elif profile and profile.role in ['teacher', 'head_teacher']:
            teacher = getattr(profile, 'teacher_profile', None)
            if teacher:
                qs = qs.filter(teacher=teacher)
            else:
                return Course.objects.none()
        # 管理人员可以看所有课程
        elif profile and profile.role not in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
            return Course.objects.none()
        
        params = self.request.query_params
        q = params.get('q')
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(teacher__teacher_id__icontains=q) |
                Q(teacher__user_profile__user__username__icontains=q) |
                Q(teacher__user_profile__user__first_name__icontains=q) |
                Q(department__name__icontains=q)
            )
        department = params.get('department')
        if department:
            qs = qs.filter(department_id=department)
        college = params.get('college')
        if college:
            qs = qs.filter(department__college_id=college)
        return qs


class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all().order_by('weekday', 'index')
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeanOrReadOnly]
    pagination_class = None  # 禁用分页，返回所有时间段


class GenerateStandardTimeSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import datetime
        def build_sessions(start_hour, start_minute, count):
            sessions = []
            current = datetime.datetime(2000, 1, 1, start_hour, start_minute)
            for i in range(count):
                end = current + datetime.timedelta(minutes=45)
                sessions.append((current.time(), end.time()))
                current = end + datetime.timedelta(minutes=10)
            return sessions

        morning = build_sessions(8, 30, 4)
        afternoon = build_sessions(14, 0, 4)
        created = 0
        # 为周一到周日（1-7）生成时间段
        for weekday in range(1, 8):  # 1-7 包括周六和周日
            index = 1
            for st, et in morning + afternoon:
                if not TimeSlot.objects.filter(weekday=weekday, index=index).exists():
                    TimeSlot.objects.create(weekday=weekday, index=index, start_time=st, end_time=et)
                    created += 1
                index += 1
        return Response({'created': created})


class ScheduleTimeConfigViewSet(viewsets.ModelViewSet):
    queryset = ScheduleTimeConfig.objects.all()
    serializer_class = ScheduleTimeConfigSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeanOrReadOnly]


class CourseScheduleViewSet(viewsets.ModelViewSet):
    queryset = CourseSchedule.objects.select_related('school_class', 'course', 'teacher', 'classroom', 'timeslot').all()
    serializer_class = CourseScheduleSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdminOrReadOnly]
    pagination_class = None  # 禁用分页，返回所有课程安排

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        # 优化：使用select_related预加载所有关联对象，减少数据库查询
        qs = CourseSchedule.objects.select_related(
            'school_class',
            'course',
            'teacher',
            'teacher__user_profile',
            'teacher__user_profile__user',
            'classroom',
            'timeslot'
        ).all()
        params = self.request.query_params
        
        # 超级用户可以看所有内容
        if getattr(user, 'is_superuser', False):
            school_class = params.get('school_class')
            if school_class:
                try:
                    school_class = int(school_class)
                except (ValueError, TypeError):
                    pass
                qs = qs.filter(school_class_id=school_class)
            teacher_id = params.get('teacher')
            if teacher_id:
                qs = qs.filter(teacher_id=teacher_id)
            classroom_id = params.get('classroom')
            if classroom_id:
                qs = qs.filter(classroom_id=classroom_id)
            week_number = params.get('week_number')
            if week_number:
                try:
                    week_number = int(week_number)
                    qs = qs.filter(week_number=week_number)
                except (ValueError, TypeError):
                    pass
            return qs.distinct()  # 确保没有重复记录
            
        if not profile:
            return CourseSchedule.objects.none()
        
        role = profile.role

        # 学生：只能看自己班级的课程表
        if role == 'student':
            student = getattr(profile, 'student_profile', None)
            if student and student.school_class_id:
                qs = qs.filter(school_class_id=student.school_class_id)
            else:
                return CourseSchedule.objects.none()
        
        # 教师/班主任：只能看自己的课程
        elif role in ['teacher', 'head_teacher']:
            teacher = getattr(profile, 'teacher_profile', None)
            if not teacher:
                return CourseSchedule.objects.none()
            
            # 只显示该教师自己的课程安排
            qs = qs.filter(teacher=teacher).distinct()  # 确保没有重复记录
        
        # 管理人员：可以看所有内容
        elif role not in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
            return CourseSchedule.objects.none()

        # Query Parameter Filtering (for everyone)
        # params 已经在上面获取过了，这里直接使用
        school_class = params.get('school_class')
        if school_class:
            # 确保 school_class 是整数类型
            try:
                school_class = int(school_class)
            except (ValueError, TypeError):
                pass
            qs = qs.filter(school_class_id=school_class)
        
        teacher_id = params.get('teacher')
        if teacher_id:
            qs = qs.filter(teacher_id=teacher_id)
            
        classroom_id = params.get('classroom')
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
            
        # 周次过滤：必须提供，默认第1周
        week_number = params.get('week_number')
        if week_number:
            try:
                week_number = int(week_number)
            except (ValueError, TypeError):
                week_number = 1
        else:
            week_number = 1  # 默认第1周
        
        # 必须按周次过滤，避免加载所有周的数据
        qs = qs.filter(week_number=week_number)

        # 确保返回的数据没有重复
        return qs.distinct()

    def create(self, request, *args, **kwargs):
        from rest_framework.exceptions import ValidationError
        import json, time
        
        # #region agent log
        try:
            with open(r'c:\Users\ldwjl\Desktop\EduCloud\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"create_request","location":"courses/views.py:create","message":"Create request","data":{"request_data": request.data}, "timestamp": int(time.time()*1000)}) + "\n")
        except Exception: pass
        # #endregion
        
        data = request.data
        
        # 在创建前，先删除该班级在该时间段的重复课程（保留最新的）
        if data.get('school_class') and data.get('timeslot') and data.get('week_number'):
            # 确保 week_number 是整数类型
            try:
                week_number = int(data.get('week_number'))
            except (ValueError, TypeError):
                week_number = data.get('week_number')
            
            # 删除同一班级、同一时间段、同一周的所有旧课程（为新课程让路）
            deleted_count = CourseSchedule.objects.filter(
                school_class_id=data.get('school_class'),
                timeslot_id=data.get('timeslot'),
                week_number=week_number
            ).delete()[0]
            
            # 调试：打印删除信息（使用print）
            if deleted_count > 0:
                print(f'[DEBUG CourseSchedule.create] 删除了 {deleted_count} 个重复课程: school_class={data.get("school_class")}, timeslot={data.get("timeslot")}, week_number={week_number}')
        
        try:
            response = super().create(request, *args, **kwargs)
            
            # 调试：打印创建结果（使用print）
            if hasattr(response, 'data'):
                created_id = response.data.get('id')
                created_week_number = response.data.get('week_number')
                created_timeslot = response.data.get('timeslot')
                print(f'[DEBUG CourseSchedule.create] 创建成功: id={created_id}, week_number={created_week_number}, timeslot={created_timeslot}')
                
                # 验证创建的数据是否真的存在
                try:
                    created_obj = CourseSchedule.objects.get(pk=created_id)
                    print(f'[DEBUG CourseSchedule.create] 验证: 数据库中确实存在 id={created_id}, week_number={created_obj.week_number}, timeslot_id={created_obj.timeslot_id}')
                    # 检查timeslot的weekday
                    if created_obj.timeslot:
                        print(f'[DEBUG CourseSchedule.create] timeslot weekday={created_obj.timeslot.weekday}, index={created_obj.timeslot.index}')
                except CourseSchedule.DoesNotExist:
                    print(f'[ERROR CourseSchedule.create] 错误: 创建后立即查询不到 id={created_id} 的记录！')
            
            # #region agent log
            try:
                with open(r'c:\Users\ldwjl\Desktop\EduCloud\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"create_response","location":"courses/views.py:create","message":"Create response","data":{"response_data": response.data if hasattr(response, 'data') else str(response)}, "timestamp": int(time.time()*1000)}) + "\n")
            except Exception: pass
            # #endregion
            return response
        except ValidationError as e:
            error_str = str(e.detail)
            data = request.data
            
            # 1. 处理唯一性约束冲突（同一班级、同一课程、同一时间） -> 视为更新操作
            # 错误信息可能是: {"non_field_errors": ["字段 school_class, course, timeslot, week_number 必须能构成唯一集合。"]}
            is_unique_error = False
            if isinstance(e.detail, dict) and 'non_field_errors' in e.detail:
                for err in e.detail['non_field_errors']:
                    if '唯一集合' in str(err) or 'unique set' in str(err):
                        is_unique_error = True
                        break
            
            if is_unique_error:
                try:
                    instance = CourseSchedule.objects.get(
                        school_class_id=data.get('school_class'),
                        course_id=data.get('course'),
                        timeslot_id=data.get('timeslot'),
                        week_number=data.get('week_number')
                    )
                    
                    # 检查是否需要更新额外字段 (Teacher, Classroom)
                    needs_save = False
                    new_teacher = data.get('teacher')
                    if new_teacher and str(instance.teacher_id) != str(new_teacher):
                        instance.teacher_id = new_teacher
                        needs_save = True
                        
                    new_classroom = data.get('classroom')
                    if new_classroom and str(instance.classroom_id) != str(new_classroom):
                        instance.classroom_id = new_classroom
                        needs_save = True
                    
                    if needs_save:
                        instance.save()
                        
                    serializer = self.get_serializer(instance)
                    return Response(serializer.data)
                except CourseSchedule.DoesNotExist:
                    # 如果找不到，说明可能是其他原因导致的唯一性错误，或者并发删除了
                    pass

            # 2. 处理班级冲突（同一班级、不同课程、同一时间） -> 删除旧课程，创建新课程
            # 错误信息: {'non_field_errors': ['班级在该时间段已有课程安排']} (如果是抛出的ValidationError(string)会被DRF封装)
            # 或者在 validated_data 中抛出的 ValidationError 会在 e.detail 中
            if '班级在该时间段已有课程安排' in error_str:
                # 删除该班级在该时间段的冲突课程
                deleted_count, _ = CourseSchedule.objects.filter(
                    school_class_id=data.get('school_class'),
                    timeslot_id=data.get('timeslot'),
                    week_number=data.get('week_number')
                ).delete()
                
                if deleted_count > 0:
                    # 再次尝试创建
                    return super().create(request, *args, **kwargs)

            # 其他错误正常抛出
            raise e

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        ids = request.data.get('ids') or []
        teacher = request.data.get('teacher')
        classroom = request.data.get('classroom')
        if not ids or (not teacher and not classroom):
            return Response({'detail': '缺少参数'}, status=400)
        qs = CourseSchedule.objects.filter(id__in=ids)
        updated = 0
        for obj in qs:
            data = {}
            if teacher:
                data['teacher'] = teacher
            if classroom:
                data['classroom'] = classroom
            ser = CourseScheduleSerializer(obj, data=data, partial=True)
            if ser.is_valid():
                ser.save()
                updated += 1
        return Response({'updated': updated, 'total': qs.count()})

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """批量删除课程安排"""
        school_class = request.data.get('school_class')
        week_number = request.data.get('week_number')  # 可选，如果提供则只删除指定周的
        
        if not school_class:
            return Response({'detail': '缺少班级参数'}, status=400)
        
        # 构建查询条件
        qs = CourseSchedule.objects.filter(school_class_id=school_class)
        
        # 如果指定了周次，只删除该周的
        if week_number:
            qs = qs.filter(week_number=week_number)
        
        # 获取要删除的数量
        count = qs.count()
        
        # 执行删除
        qs.delete()
        
        return Response({
            'deleted': count,
            'message': f'已删除 {count} 条课程安排'
        })

    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        qs = self.get_queryset()
        data = {}
        schedule_map = {}  # 用于后续查询详细信息
        
        for row in qs.values('timeslot_id', 'week_number', 'id', 'teacher_id', 'school_class_id', 'classroom_id', 'course_id'):
            schedule_map[row['id']] = row
            key = (row['timeslot_id'], row['week_number'])
            arr = data.setdefault(key, [])
            arr.append(row)
        
        res = []
        for (ts, wk), arr in data.items():
            if len(arr) <= 1:
                continue
            teachers = {}
            classes = {}
            rooms = {}
            for r in arr:
                t = r['teacher_id']
                c = r['school_class_id']
                rm = r['classroom_id']
                if t:
                    teachers[t] = teachers.get(t, 0) + 1
                classes[c] = classes.get(c, 0) + 1
                if rm:
                    rooms[rm] = rooms.get(rm, 0) + 1
            
            conflict_types = []
            if any(v > 1 for v in teachers.values()):
                conflict_types.append('教师冲突')
            if any(v > 1 for v in classes.values()):
                conflict_types.append('班级冲突')
            if any(v > 1 for v in rooms.values()):
                conflict_types.append('教室冲突')
            
            res.append({
                'timeslot': ts,
                'week_number': wk,
                'count': len(arr),
                'schedule_ids': [r['id'] for r in arr],
                'teacher_conflicts': [k for k, v in teachers.items() if v > 1],
                'class_conflicts': [k for k, v in classes.items() if v > 1],
                'room_conflicts': [k for k, v in rooms.items() if v > 1],
                'conflict_types': conflict_types,
            })
        return Response({'items': res, 'count': len(res)})


class OptimizeConflictsView(APIView):
    """自动优化课程表冲突"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        school_class_id = request.data.get('school_class')
        if not school_class_id:
            return Response({'error': '缺少班级参数'}, status=400)
        
        # 获取该班级的所有课程安排
        schedules = CourseSchedule.objects.filter(school_class_id=school_class_id).select_related('course', 'teacher', 'classroom', 'timeslot')
        
        # 检测冲突
        conflicts = {}
        for schedule in schedules:
            key = (schedule.timeslot_id, schedule.week_number)
            if key not in conflicts:
                conflicts[key] = []
            conflicts[key].append(schedule)
        
        # 找出有冲突的课程
        conflicted_schedules = []
        for key, scheds in conflicts.items():
            if len(scheds) > 1:
                # 保留第一个，其他的需要重新安排
                conflicted_schedules.extend(scheds[1:])
        
        if not conflicted_schedules:
            return Response({'success': True, 'message': '没有发现冲突', 'optimized': 0})
        
        # 获取所有可用时间段（周一至周五）
        available_slots = list(TimeSlot.objects.filter(weekday__in=[1, 2, 3, 4, 5]).order_by('weekday', 'index'))
        
        optimized_count = 0
        failed = []
        
        for schedule in conflicted_schedules:
            # 找到一个不冲突的时间段
            found = False
            for slot in available_slots:
                # 检查是否存在冲突
                if CourseSchedule.objects.filter(
                    school_class_id=school_class_id,
                    timeslot=slot,
                    week_number=schedule.week_number
                ).exists():
                    continue
                
                # 检查教师冲突
                if schedule.teacher and CourseSchedule.objects.filter(
                    teacher=schedule.teacher,
                    timeslot=slot,
                    week_number=schedule.week_number
                ).exists():
                    continue
                
                # 检查教室冲突
                if schedule.classroom and CourseSchedule.objects.filter(
                    classroom=schedule.classroom,
                    timeslot=slot,
                    week_number=schedule.week_number
                ).exists():
                    continue
                
                # 找到可用时间段，更新
                schedule.timeslot = slot
                schedule.save()
                optimized_count += 1
                found = True
                break
            
            if not found:
                failed.append({
                    'schedule_id': schedule.id,
                    'course': schedule.course.name if schedule.course else 'Unknown',
                    'week': schedule.week_number
                })
        
        if failed:
            return Response({
                'success': False,
                'message': f'部分课程无法自动优化',
                'optimized': optimized_count,
                'failed': failed
            })
        
        return Response({
            'success': True,
            'message': '所有冲突已成功优化',
            'optimized': optimized_count
        })


class AutoScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data or {}
        course_ids = data.get('courses') or []
        school_class = data.get('school_class')
        teacher_param = data.get('teacher')
        classroom = data.get('classroom')
        start_week = int(data.get('start_week') or data.get('week_number') or 1)
        end_week = int(data.get('end_week') or 20)  # 默认20周
        week_mode = (data.get('week_mode') or 'all').strip()

        if not school_class or not course_ids:
            return Response({'error': '缺少必要参数'}, status=400)

        weeks = []
        for wk in range(start_week, end_week + 1):
            if week_mode == 'odd' and wk % 2 == 0:
                continue
            if week_mode == 'even' and wk % 2 == 1:
                continue
            weeks.append(wk)
        if not weeks:
            weeks = [start_week]

        cfg = ScheduleTimeConfig.objects.first()
        morning_count = cfg.morning_sessions if cfg else 4

        # 只获取周一到周五的时间段
        slots = list(TimeSlot.objects.filter(weekday__in=[1, 2, 3, 4, 5]).order_by('weekday', 'index'))
        results = []
        for wk in weeks:
            for cid in course_ids:
                course_obj = None
                try:
                    course_obj = Course.objects.get(pk=cid)
                except Course.DoesNotExist:
                    results.append({'course': cid, 'week': wk, 'schedule_id': None, 'reason': '课程不存在'})
                    continue

                teacher_eff = teacher_param or (course_obj.teacher_id or None)

                best_slot = None
                best_score = -1
                any_class_conflict = True
                any_teacher_conflict = True
                any_room_conflict = True
                any_capacity_conflict = False

                for s in slots:
                    if CourseSchedule.objects.filter(school_class_id=school_class, timeslot=s, week_number=wk).exists():
                        continue
                    any_class_conflict = False

                    if teacher_eff and CourseSchedule.objects.filter(teacher_id=teacher_eff, timeslot=s, week_number=wk).exists():
                        continue
                    any_teacher_conflict = False

                    if classroom and CourseSchedule.objects.filter(classroom_id=classroom, timeslot=s, week_number=wk).exists():
                        continue
                    any_room_conflict = False

                    score = 0
                    # 必修课优先安排在上午
                    if course_obj.course_type == 'required' and s.index <= morning_count:
                        score += 5
                    # 优先安排在早期时间段
                    score += max(0, 10 - s.index)
                    # 均匀分布：周一到周五
                    score += (5 - abs(s.weekday - 3)) * 0.5  # 周三得分最高

                    if score > best_score:
                        best_score = score
                        best_slot = s

                if best_slot:
                    payload = {
                        'school_class': school_class,
                        'course': cid,
                        'teacher': teacher_eff,
                        'classroom': classroom,
                        'timeslot': best_slot.id,
                        'week_number': wk,
                    }
                    ser = CourseScheduleSerializer(data=payload)
                    if ser.is_valid():
                        obj = ser.save(created_by=request.user)
                        results.append({'course': cid, 'week': wk, 'schedule_id': obj.id, 'reason': None})
                    else:
                        results.append({'course': cid, 'week': wk, 'schedule_id': None, 'reason': '校验失败'})
                else:
                    reason = '无可用时间'
                    if any_class_conflict and any_teacher_conflict and any_room_conflict:
                        reason = '全部冲突'
                    elif any_class_conflict:
                        reason = '班级冲突'
                    elif any_teacher_conflict:
                        reason = '教师冲突'
                    elif any_room_conflict:
                        reason = '教室冲突'
                    results.append({'course': cid, 'week': wk, 'schedule_id': None, 'reason': reason})

        created_ids = [x['schedule_id'] for x in results if x['schedule_id']]
        return Response({'created_count': len(created_ids), 'items': results})
