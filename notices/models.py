from django.db import models
from django.contrib.auth.models import User


SCOPE_CHOICES = (
    ('all', '全校'),
    ('college', '学院'),
    ('department', '专业'),
    ('role', '职务'),
    ('personal', '个人'),
)


class Notice(models.Model):
    title = models.CharField(max_length=128)
    content = models.TextField()
    scope = models.CharField(max_length=16, choices=SCOPE_CHOICES, default='all')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='notices_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
