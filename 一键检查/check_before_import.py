# -*- coding: utf-8 -*-
"""
导入前检查脚本
检查系统是否满足导入课表的前置条件
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

from django.contrib.auth.models import User
from courses.models import TimeSlot
from organization.models import Class as SchoolClass, Major, College

def check_class_exists():
    """检查班级是否存在"""
    print("【检查1】班级是否存在...")
    try:
        school_class = SchoolClass.objects.get(class_id='2023502701')
        print(f"  ✓ 班级存在: {school_class.name}")
        print(f"    - 班级ID: {school_class.class_id}")
        print(f"    - 年级: {school_class.enrollment_year}")
        
        if school_class.major:
            print(f"    - 专业: {school_class.major.name}")
            if school_class.major.college:
                print(f"    - 学院: {school_class.major.college.name}")
        else:
            print("    ⚠ 警告: 班级未关联专业")
            return False
        
        return True
    except SchoolClass.DoesNotExist:
        print("  ✗ 班级不存在！")
        print("  解决方法:")
        print("    1. 访问系统管理界面创建班级")
        print("    2. 或运行以下命令:")
        print("       python manage.py shell")
        print("       >>> from organization.models import Class, Major")
        print("       >>> major = Major.objects.first()")
        print("       >>> Class.objects.create(")
        print("       ...     class_id='2023502701',")
        print("       ...     name='23移动互联网应用技术G5-1班',")
        print("       ...     major=major,")
        print("       ...     enrollment_year=2023,")
        print("       ...     class_number=1")
        print("       ... )")
        return False

def check_timeslots():
    """检查时间段是否初始化"""
    print("\n【检查2】时间段是否初始化...")
    count = TimeSlot.objects.count()
    
    if count == 0:
        print("  ✗ 时间段未初始化！")
        print("  解决方法:")
        print("    访问: http://localhost:8000/courses")
        print("    点击\"生成标准时间段\"按钮")
        print("    或运行: curl -X POST http://localhost:8000/api/courses/timeslots/generate")
        return False
    
    print(f"  ✓ 时间段已就绪 (共 {count} 个)")
    
    # 检查必需的时间段
    required_slots = [
        (1, 1), (1, 3), (1, 5),  # 周一
        (2, 1), (2, 3), (2, 5),  # 周二
        (3, 2), (3, 5),          # 周三
        (4, 1), (4, 5),          # 周四
        (5, 2),                  # 周五
    ]
    
    missing = []
    for weekday, index in required_slots:
        if not TimeSlot.objects.filter(weekday=weekday, index=index).exists():
            missing.append(f"周{weekday}第{index}节")
    
    if missing:
        print(f"  ⚠ 警告: 缺少时间段: {', '.join(missing)}")
        return False
    
    print("  ✓ 所有必需的时间段都存在")
    return True

def check_admin_user():
    """检查管理员用户"""
    print("\n【检查3】管理员用户...")
    admin = User.objects.filter(is_superuser=True).first()
    
    if not admin:
        print("  ⚠ 警告: 没有超级管理员用户")
        print("  脚本会自动创建一个管理员用户")
        return True
    
    print(f"  ✓ 管理员用户存在: {admin.username}")
    return True

def check_existing_data():
    """检查是否已有相关数据"""
    print("\n【检查4】检查已有数据...")
    
    from accounts.models import TeacherProfile
    from courses.models import Course, CourseSchedule
    
    # 检查教师
    teachers = TeacherProfile.objects.filter(teacher_id__in=[
        'T2024001', 'T2024002', 'T2024003', 'T2024004', 'T2024005', 'T2024006'
    ])
    
    if teachers.exists():
        print(f"  ℹ 发现 {teachers.count()} 位教师已存在:")
        for t in teachers:
            print(f"    - {t.user_profile.user.first_name} ({t.teacher_id})")
        print("  脚本将跳过已存在的教师")
    else:
        print("  ✓ 没有教师冲突")
    
    # 检查课程
    course_names = [
        'ArkTS基础应用开发', '历史', '移动web开发',
        '商务英语', '数据库技术与应用', 'Python项目开发'
    ]
    
    courses = Course.objects.filter(name__in=course_names)
    
    if courses.exists():
        print(f"  ℹ 发现 {courses.count()} 门课程已存在:")
        for c in courses:
            print(f"    - {c.name}")
        print("  脚本将使用已存在的课程")
    else:
        print("  ✓ 没有课程冲突")
    
    # 检查排课
    try:
        school_class = SchoolClass.objects.get(class_id='2023502701')
        schedules = CourseSchedule.objects.filter(school_class=school_class, week_number=1)
        
        if schedules.exists():
            print(f"  ⚠ 发现 {schedules.count()} 条排课记录已存在")
            print("  脚本将跳过已存在的排课")
        else:
            print("  ✓ 没有排课冲突")
    except SchoolClass.DoesNotExist:
        pass
    
    return True

def main():
    print("=" * 70)
    print("导入前系统检查")
    print("班级: 2023502701 (23移动互联网应用技术G5-1班)")
    print("=" * 70)
    print()
    
    checks = [
        check_class_exists,
        check_timeslots,
        check_admin_user,
        check_existing_data
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"  ✗ 检查失败: {str(e)}")
            results.append(False)
    
    print()
    print("=" * 70)
    print("检查结果汇总")
    print("=" * 70)
    
    if all(results):
        print("✓ 所有检查通过！可以开始导入课表")
        print()
        print("执行导入:")
        print("  Windows: 双击 import_schedule_2023502701.bat")
        print("  命令行: python import_class_2023502701_schedule.py")
        return True
    else:
        print("✗ 存在问题，请先解决上述问题后再导入")
        print()
        print("常见问题解决:")
        print("  1. 班级不存在 → 先创建班级")
        print("  2. 时间段未初始化 → 访问系统生成时间段")
        print("  3. 数据冲突 → 检查是否重复导入")
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
