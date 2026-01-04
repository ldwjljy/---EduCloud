"""
检查考勤记录中的重复数据
使用方法: python manage.py shell < check_duplicate_attendance.py
"""

from attendance_app.models import Attendance
from django.db.models import Count
from datetime import date

print("\n" + "="*60)
print("检查考勤记录中的重复数据")
print("="*60 + "\n")

# 检查今天是否有重复记录
today = date.today()
print(f"检查日期: {today}\n")

# 查找重复的记录（相同学生+相同课程+相同日期）
duplicates = Attendance.objects.filter(date=today).values(
    'student_id', 'schedule_id', 'date'
).annotate(
    count=Count('id')
).filter(count__gt=1)

if duplicates.exists():
    print(f"⚠ 发现 {duplicates.count()} 组重复记录:\n")
    for dup in duplicates:
        print(f"  学生ID: {dup['student_id']}, 课程安排ID: {dup['schedule_id']}, 日期: {dup['date']}, 重复次数: {dup['count']}")
        
        # 显示具体的重复记录
        records = Attendance.objects.filter(
            student_id=dup['student_id'],
            schedule_id=dup['schedule_id'],
            date=dup['date']
        )
        print(f"  具体记录:")
        for r in records:
            print(f"    - ID: {r.id}, 状态: {r.status}, 备注: {r.remark}")
        print()
else:
    print("✓ 没有发现重复记录\n")

# 统计总记录数
total = Attendance.objects.filter(date=today).count()
print(f"今天总共有 {total} 条考勤记录")

# 按课程安排统计
print("\n按课程安排统计:")
schedules = Attendance.objects.filter(date=today).values('schedule_id', 'schedule__course__name').annotate(
    count=Count('id')
).order_by('-count')
for s in schedules[:10]:  # 只显示前10个
    print(f"  课程: {s['schedule__course__name']}, 记录数: {s['count']}")

print("\n" + "="*60)
print("检查完成")
print("="*60 + "\n")

