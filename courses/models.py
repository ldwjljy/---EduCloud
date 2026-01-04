from django.db import models
from organization.models import Class as SchoolClass, Major
from classrooms.models import Classroom
from accounts.models import TeacherProfile
from django.contrib.auth.models import User


COURSE_TYPES = (
    ('required', '必修'),
    ('elective', '选修'),
    ('practical', '实践'),
)


class Course(models.Model):
    subject_id = models.CharField(max_length=64, unique=True, default='SUB001')
    name = models.CharField(max_length=128)
    course_type = models.CharField(max_length=16, choices=COURSE_TYPES)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='courses')
    department = models.ForeignKey(Major, on_delete=models.CASCADE, null=True, blank=True, related_name='courses')
    classroom = models.CharField(max_length=100, blank=True, null=True, verbose_name='默认教室地址')

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """保存前记录旧的教师ID，用于同步更新课程表"""
        # 记录更新前的教师ID
        old_teacher_id = None
        if self.pk:  # 如果是更新操作
            try:
                old_instance = Course.objects.get(pk=self.pk)
                old_teacher_id = old_instance.teacher_id
            except Course.DoesNotExist:
                pass
        
        # 先保存课程信息
        super().save(*args, **kwargs)
        
        # 如果教师信息发生变化，同步更新所有相关的课程表记录
        if self.pk and old_teacher_id != self.teacher_id:
            # 使用 update() 方法批量更新，不会触发 save 信号，性能更好
            # 同步更新所有使用该课程的课程表记录的教师字段
            CourseSchedule.objects.filter(course=self).update(teacher=self.teacher)


class TimeSlot(models.Model):
    weekday = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    index = models.IntegerField()

    class Meta:
        unique_together = ('weekday', 'index')

    def __str__(self):
        return f"{self.weekday}-{self.index}"


class ScheduleTimeConfig(models.Model):
    name = models.CharField(max_length=64)
    morning_sessions = models.IntegerField(default=4)
    afternoon_sessions = models.IntegerField(default=4)
    lesson_minutes = models.IntegerField(default=45)
    break_minutes = models.IntegerField(default=10)

    def __str__(self):
        return self.name


class CourseSchedule(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='course_schedules')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='course_schedules')
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True, related_name='course_schedules')
    classroom_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='教室地址')
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='course_schedules')
    week_number = models.IntegerField(default=1)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='course_schedules_created')

    class Meta:
        unique_together = ('school_class', 'course', 'timeslot', 'week_number')
        indexes = [
            models.Index(fields=['teacher', 'week_number'], name='cs_teacher_week_idx'),
            models.Index(fields=['school_class', 'week_number'], name='cs_class_week_idx'),
            models.Index(fields=['week_number'], name='cs_week_idx'),
        ]

    def __str__(self):
        return f"{self.school_class}-{self.course}-{self.timeslot}"
    
    def get_classroom_display(self):
        """获取教室显示名称，优先使用自定义教室名称"""
        if self.classroom_name:
            return self.classroom_name
        if self.classroom:
            return self.classroom.name
        return '-'
