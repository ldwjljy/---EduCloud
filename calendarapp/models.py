from django.db import models
from django.contrib.auth.models import User
from organization.models import College


EVENT_TYPES = (
    ('campus', '全校活动'),
    ('teaching', '教学安排'),
    ('meeting', '会议'),
    ('custom', '自定义'),
)

VISIBILITY_CHOICES = (
    ('all', '全校'),
    ('college', '指定学院'),
    ('role', '指定职务'),
    ('personal', '个人'),
)


class CalendarEvent(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=16, choices=EVENT_TYPES)
    visibility = models.CharField(max_length=16, choices=VISIBILITY_CHOICES, default='all')
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True, related_name='events', help_text='当可见范围为学院时指定学院')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='events_created')
    remind_minutes_before = models.IntegerField(default=0)

    def __str__(self):
        return self.title
