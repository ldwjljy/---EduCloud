from django.db import models


class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10)
    class_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='在读')
    grade = models.CharField(max_length=10, default='大一')

    def __str__(self):
        return f"{self.student_id} {self.name}"
