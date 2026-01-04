from django.db import models


class Teacher(models.Model):
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=20, default='讲师')
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, default='在职')

    def __str__(self):
        return self.name
