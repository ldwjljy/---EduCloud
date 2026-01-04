from django.db import models
from accounts.models import StudentProfile
from courses.models import Course


class Grade(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grades')
    
    # 总评成绩（最终显示的成绩）
    score = models.DecimalField(max_digits=5, decimal_places=2)
    
    # 平时分和期末分
    regular_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='平时分')
    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='期末分')
    
    # 平时分和期末分的占比（百分比，默认各占50%）
    regular_weight = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, verbose_name='平时分占比(%)')
    final_weight = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, verbose_name='期末分占比(%)')
    
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    approved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student}-{self.course}-{self.score}"
    
    def calculate_total_score(self):
        """根据平时分、期末分和占比计算总评成绩"""
        if self.regular_score is not None and self.final_score is not None:
            # 计算总评 = 平时分 × 平时分占比% + 期末分 × 期末分占比%
            total = (float(self.regular_score) * float(self.regular_weight) / 100 + 
                    float(self.final_score) * float(self.final_weight) / 100)
            return round(total, 2)
        return None
    
    def save(self, *args, **kwargs):
        """保存时自动根据固定 60/40 占比计算总评成绩"""
        # 无论外部传入什么占比，这里统一强制为 60% / 40%
        self.regular_weight = 60
        self.final_weight = 40

        calculated_score = self.calculate_total_score()
        if calculated_score is not None:
            self.score = calculated_score
        super().save(*args, **kwargs)
