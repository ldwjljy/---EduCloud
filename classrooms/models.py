from django.db import models


class Classroom(models.Model):
    name = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=100, blank=True)
    capacity = models.IntegerField(default=50)
    status = models.CharField(max_length=20, default='可用')

    def __str__(self):
        return self.name
