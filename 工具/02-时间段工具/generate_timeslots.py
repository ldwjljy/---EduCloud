# -*- coding: utf-8 -*-
"""
生成标准时间段
"""
import os
import django
import sys

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)
os.chdir(project_root)

sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduCloud.settings')
django.setup()

from courses.models import TimeSlot

def generate_timeslots():
    """生成标准时间段"""
    print("=" * 70)
    print("生成标准时间段")
    print("=" * 70)
    print()
    
    # 上午课程时间 (4节课)
    morning_times = [
        (8, 30, 9, 15),    # 第1节: 08:30-09:15
        (9, 25, 10, 10),   # 第2节: 09:25-10:10
        (10, 35, 11, 20),  # 第3节: 10:35-11:20
        (11, 30, 12, 15),  # 第4节: 11:30-12:15
    ]
    
    # 下午课程时间 (4节课)
    afternoon_times = [
        (14, 0, 14, 45),   # 第5节: 14:00-14:45
        (14, 55, 15, 40),  # 第6节: 14:55-15:40
        (16, 5, 16, 50),   # 第7节: 16:05-16:50
        (17, 0, 17, 45),   # 第8节: 17:00-17:45
    ]
    
    all_times = morning_times + afternoon_times
    
    created_count = 0
    existing_count = 0
    
    weekday_names = {
        1: '周一',
        2: '周二',
        3: '周三',
        4: '周四',
        5: '周五',
        6: '周六',
        7: '周日'
    }
    
    # 为周一到周五生成时间段
    for weekday in range(1, 6):
        print(f"\n生成 {weekday_names[weekday]} 的时间段...")
        
        for index, (start_h, start_m, end_h, end_m) in enumerate(all_times, start=1):
            start_time = f'{start_h:02d}:{start_m:02d}:00'
            end_time = f'{end_h:02d}:{end_m:02d}:00'
            
            # 检查是否已存在
            existing = TimeSlot.objects.filter(
                weekday=weekday,
                index=index
            ).first()
            
            if existing:
                existing_count += 1
                print(f"  ○ 第{index}节 已存在: {start_time}-{end_time}")
            else:
                TimeSlot.objects.create(
                    weekday=weekday,
                    index=index,
                    start_time=start_time,
                    end_time=end_time
                )
                created_count += 1
                print(f"  ✓ 第{index}节 创建成功: {start_time}-{end_time}")
    
    # 为周六周日也生成（可选）
    for weekday in range(6, 8):
        print(f"\n生成 {weekday_names[weekday]} 的时间段...")
        
        for index, (start_h, start_m, end_h, end_m) in enumerate(all_times, start=1):
            start_time = f'{start_h:02d}:{start_m:02d}:00'
            end_time = f'{end_h:02d}:{end_m:02d}:00'
            
            existing = TimeSlot.objects.filter(
                weekday=weekday,
                index=index
            ).first()
            
            if existing:
                existing_count += 1
                print(f"  ○ 第{index}节 已存在: {start_time}-{end_time}")
            else:
                TimeSlot.objects.create(
                    weekday=weekday,
                    index=index,
                    start_time=start_time,
                    end_time=end_time
                )
                created_count += 1
                print(f"  ✓ 第{index}节 创建成功: {start_time}-{end_time}")
    
    print()
    print("=" * 70)
    print(f"时间段生成完成！")
    print(f"  - 新创建: {created_count} 个")
    print(f"  - 已存在: {existing_count} 个")
    print(f"  - 总计: {TimeSlot.objects.count()} 个")
    print("=" * 70)
    print()
    
    # 显示时间段概览
    print("📅 时间段概览:")
    print()
    print("上午课程:")
    for index, (start_h, start_m, end_h, end_m) in enumerate(morning_times, start=1):
        print(f"  第{index}节: {start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}")
    
    print()
    print("下午课程:")
    for index, (start_h, start_m, end_h, end_m) in enumerate(afternoon_times, start=5):
        print(f"  第{index}节: {start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}")
    
    print()

if __name__ == '__main__':
    try:
        generate_timeslots()
    except Exception as e:
        print(f"\n✗ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
