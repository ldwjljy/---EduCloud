# -*- coding: utf-8 -*-
"""
检查周五时间段脚本
"""
import os
import django
import sys
from pathlib import Path

# 添加项目根目录到路径
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))
os.chdir(script_dir)

sys.path.append(str(script_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduCloud.settings')
django.setup()

from courses.models import TimeSlot

# 检查周五的时间段
friday_slots = TimeSlot.objects.filter(weekday=5).order_by('index')
print(f"周五时间段数量: {friday_slots.count()}")
print("\n周五的所有时间段:")
for slot in friday_slots:
    print(f"  第{slot.index}节: {slot.start_time}-{slot.end_time} (ID: {slot.id})")

# 检查所有工作日的时间段数量
print("\n各工作日时间段数量:")
for weekday in range(1, 8):
    count = TimeSlot.objects.filter(weekday=weekday).count()
    weekday_name = {1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日'}[weekday]
    print(f"  {weekday_name} (weekday={weekday}): {count} 个")
