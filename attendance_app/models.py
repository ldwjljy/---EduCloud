from django.db import models
from accounts.models import StudentProfile
from courses.models import CourseSchedule


ATTENDANCE_STATUS = (
    ('present', '正常'),
    ('late', '迟到'),
    ('absent', '缺勤'),
    ('leave', '请假'),
)


class Attendance(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance_records')
    schedule = models.ForeignKey(CourseSchedule, on_delete=models.CASCADE, related_name='attendance_records', verbose_name='课程安排')
    date = models.DateField(verbose_name='考勤日期')
    status = models.CharField(max_length=16, choices=ATTENDANCE_STATUS, default='present', verbose_name='考勤状态')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')

    class Meta:
        unique_together = ('student', 'schedule', 'date')
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['schedule', 'date']),
        ]
        verbose_name = '考勤记录'
        verbose_name_plural = '考勤记录'

    def __str__(self):
        return f"{self.student}-{self.schedule.course.name if self.schedule else 'N/A'}-{self.date}-{self.status}"
