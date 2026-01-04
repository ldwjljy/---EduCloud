# Generated migration to update Attendance model
# 修改考勤模型：支持按课程+学生+日期管理考勤

from django.db import migrations, models
import django.db.models.deletion


def clear_existing_attendance(apps, schema_editor):
    """清理现有的考勤记录，因为它们没有schedule关联"""
    Attendance = apps.get_model('attendance_app', 'Attendance')
    # 删除所有没有schedule的记录（因为新模型要求schedule必须存在）
    Attendance.objects.filter(schedule__isnull=True).delete()


def reverse_clear(apps, schema_editor):
    """反向操作：不做任何事"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('attendance_app', '0002_initial'),
        ('courses', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        # 先清理现有数据
        migrations.RunPython(clear_existing_attendance, reverse_clear),
        
        # 修改schedule字段：从nullable改为required，从SET_NULL改为CASCADE
        migrations.AlterField(
            model_name='attendance',
            name='schedule',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='attendance_records',
                to='courses.courseschedule',
                verbose_name='课程安排'
            ),
        ),
        
        # 修改status字段：添加默认值
        migrations.AlterField(
            model_name='attendance',
            name='status',
            field=models.CharField(
                choices=[('present', '正常'), ('late', '迟到'), ('absent', '缺勤'), ('leave', '请假')],
                default='present',
                max_length=16,
                verbose_name='考勤状态'
            ),
        ),
        
        # 修改date字段：添加verbose_name
        migrations.AlterField(
            model_name='attendance',
            name='date',
            field=models.DateField(verbose_name='考勤日期'),
        ),
        
        # 修改remark字段：添加verbose_name
        migrations.AlterField(
            model_name='attendance',
            name='remark',
            field=models.CharField(blank=True, max_length=255, verbose_name='备注'),
        ),
        
        # 修改unique_together：从(student, date)改为(student, schedule, date)
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together={('student', 'schedule', 'date')},
        ),
        
        # 添加索引
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['date', 'status'], name='attendance_app_date_status_idx'),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['schedule', 'date'], name='attendance_app_schedule_date_idx'),
        ),
    ]

