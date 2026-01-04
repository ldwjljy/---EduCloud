from rest_framework import serializers
from .models import Course, TimeSlot, ScheduleTimeConfig, CourseSchedule
from accounts.models import StudentProfile


class CourseSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()
    subject_id = serializers.CharField(required=False)
    teacher_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    college_name = serializers.CharField(source='department.college.name', read_only=True)
    course_type_display = serializers.CharField(source='get_course_type_display', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'subject_id', 'name', 'course_type', 'course_type_display', 
                 'teacher', 'teacher_name', 'department', 'department_name', 'college_name', 
                 'classroom', 'student_count']

    def create(self, validated_data):
        if 'subject_id' not in validated_data:
            import uuid
            validated_data['subject_id'] = 'SUB' + str(uuid.uuid4())[:8].upper()
        return super().create(validated_data)

    def get_student_count(self, obj):
        if not obj.department_id:
            return 0
        return StudentProfile.objects.filter(school_class__major=obj.department).count()
    
    def get_teacher_name(self, obj):
        """获取教师姓名"""
        if obj.teacher and obj.teacher.user_profile:
            user = obj.teacher.user_profile.user
            return user.first_name or user.username
        return '-'

    def validate(self, attrs):
        if self.instance is None:
            name = attrs.get('name')
            course_type = attrs.get('course_type')
            teacher = attrs.get('teacher')
            # 专业改为可选，支持跨学院专业班级的排课
            if not name or not course_type or not teacher:
                raise serializers.ValidationError('课程名称、课程老师、必修/选修为必填')
            if course_type not in ['required', 'elective']:
                raise serializers.ValidationError('课程类型仅支持必修或选修')
        return attrs


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'weekday', 'start_time', 'end_time', 'index']


class ScheduleTimeConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleTimeConfig
        fields = ['id', 'name', 'morning_sessions', 'afternoon_sessions', 'lesson_minutes', 'break_minutes']


class CourseScheduleSerializer(serializers.ModelSerializer):
    classroom_display = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    # timeslot字段在创建/更新时接受ID，在读取时返回完整对象
    
    class Meta:
        model = CourseSchedule
        fields = ['id', 'school_class', 'class_name', 'course', 'course_name', 'teacher', 'teacher_name', 
                 'classroom', 'classroom_name', 'classroom_display', 'timeslot', 'week_number']
    
    def get_classroom_display(self, obj):
        """获取教室显示名称"""
        return obj.get_classroom_display()
    
    def get_class_name(self, obj):
        """获取班级名称 - 优化：使用select_related已加载的数据"""
        # school_class 已经通过 select_related 加载，直接访问
        return obj.school_class.name if obj.school_class else '-'
    
    def get_course_name(self, obj):
        """获取课程名称 - 优化：使用select_related已加载的数据"""
        # course 已经通过 select_related 加载，直接访问
        return obj.course.name if obj.course else '-'
    
    def get_teacher_name(self, obj):
        """获取教师姓名 - 优化：使用select_related已加载的数据"""
        if obj.teacher:
            try:
                # teacher 已经通过 select_related('teacher__user_profile__user') 加载
                # 直接访问，不会触发额外查询
                user_profile = obj.teacher.user_profile
                if user_profile:
                    user = user_profile.user
                    return user.first_name or user.username
            except (AttributeError, TypeError):
                # 如果关系未加载或出错，返回默认值
                pass
        return '-'
    
    def to_representation(self, instance):
        """重写to_representation以确保timeslot信息完整（包含weekday和index）"""
        representation = super().to_representation(instance)
        # 确保timeslot返回完整的对象信息，而不仅仅是ID
        # 注意：由于使用了select_related('timeslot')，instance.timeslot应该已经被加载
        if hasattr(instance, 'timeslot') and instance.timeslot:
            try:
                # 如果timeslot已经被加载（通过select_related），直接使用
                representation['timeslot'] = {
                    'id': instance.timeslot.id,
                    'weekday': instance.timeslot.weekday,
                    'index': instance.timeslot.index,
                    'start_time': instance.timeslot.start_time.strftime('%H:%M:%S') if instance.timeslot.start_time else None,
                    'end_time': instance.timeslot.end_time.strftime('%H:%M:%S') if instance.timeslot.end_time else None
                }
            except AttributeError:
                # 如果timeslot没有被加载，尝试从representation中获取ID并查询
                timeslot_id = representation.get('timeslot')
                if timeslot_id:
                    from .models import TimeSlot
                    try:
                        timeslot = TimeSlot.objects.get(pk=timeslot_id)
                        representation['timeslot'] = {
                            'id': timeslot.id,
                            'weekday': timeslot.weekday,
                            'index': timeslot.index,
                            'start_time': timeslot.start_time.strftime('%H:%M:%S') if timeslot.start_time else None,
                            'end_time': timeslot.end_time.strftime('%H:%M:%S') if timeslot.end_time else None
                        }
                    except TimeSlot.DoesNotExist:
                        pass
        return representation

    def validate(self, attrs):
        instance = self.instance
        
        # Get values from attrs or fallback to instance (for partial updates)
        school_class = attrs.get('school_class') or (instance.school_class if instance else None)
        course = attrs.get('course') or (instance.course if instance else None)
        teacher = attrs.get('teacher') or (instance.teacher if instance else None)
        classroom = attrs.get('classroom') or (instance.classroom if instance else None)
        timeslot = attrs.get('timeslot') or (instance.timeslot if instance else None)
        week_number = attrs.get('week_number') or (instance.week_number if instance else None)

        # 1. Check Teacher Conflict
        if teacher:
            qs = CourseSchedule.objects.filter(teacher=teacher, timeslot=timeslot, week_number=week_number)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError('教师在该时间段已有课程安排')

        # 2. Check Class Conflict
        if school_class:
            qs = CourseSchedule.objects.filter(school_class=school_class, timeslot=timeslot, week_number=week_number)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError('班级在该时间段已有课程安排')

        # 3. Check Classroom Conflict
        if classroom:
            qs = CourseSchedule.objects.filter(classroom=classroom, timeslot=timeslot, week_number=week_number)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError('教室在该时间段已被占用')
            
            # 4. Check Capacity
            if school_class:
                from accounts.models import StudentProfile
                students_count = StudentProfile.objects.filter(school_class=school_class).count()
                if classroom.capacity < students_count:
                    raise serializers.ValidationError(f'教室容量不足({classroom.capacity})，班级人数为{students_count}')

        # 5. Check Daily Course Limit (可选：限制一天内同一课程的节数)
        # 默认不限制，如需限制可在此处添加配置
        # MAX_DAILY_COURSE_SESSIONS = 999  # 设置为999表示不限制
        # if school_class and course and timeslot:
        #     # 获取同一天该班级该课程的所有安排
        #     daily_schedules = CourseSchedule.objects.filter(
        #         school_class=school_class,
        #         course=course,
        #         week_number=week_number,
        #         timeslot__weekday=timeslot.weekday
        #     )
        #     if instance:
        #         daily_schedules = daily_schedules.exclude(pk=instance.pk)
        #     
        #     daily_count = daily_schedules.count()
        #     if daily_count >= MAX_DAILY_COURSE_SESSIONS:
        #         raise serializers.ValidationError(
        #             f'该课程在当天已安排{daily_count}节，超过每天最多{MAX_DAILY_COURSE_SESSIONS}节的限制'
        #         )

        return attrs
