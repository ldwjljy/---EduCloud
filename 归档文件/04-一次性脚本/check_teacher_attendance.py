"""
诊断脚本：检查教师账号T00001的考勤管理问题
使用方法: python manage.py shell < check_teacher_attendance.py
或: python manage.py shell，然后复制粘贴以下代码
"""

from django.contrib.auth.models import User
from accounts.models import UserProfile, TeacherProfile
from courses.models import CourseSchedule
from organization.models import Class
from accounts.models import StudentProfile

# 查找教师账号T00001
username = 'T00001'
print(f"\n{'='*60}")
print(f"检查教师账号: {username}")
print(f"{'='*60}\n")

try:
    user = User.objects.get(username=username)
    print(f"✓ 找到用户: {user.username} ({user.first_name or '无姓名'})")
    
    # 检查UserProfile
    try:
        profile = user.profile
        print(f"✓ 用户角色: {profile.role} ({profile.get_role_display()})")
    except UserProfile.DoesNotExist:
        print("✗ 错误: 用户没有UserProfile")
        exit(1)
    
    # 检查TeacherProfile
    try:
        teacher_profile = profile.teacher_profile
        print(f"✓ 教师工号: {teacher_profile.teacher_id}")
        print(f"✓ 教师ID: {teacher_profile.id}")
    except TeacherProfile.DoesNotExist:
        print("✗ 错误: 用户没有TeacherProfile")
        print("  该账号不是教师账号，无法进行考勤管理")
        exit(1)
    
    # 检查课程安排
    schedules = CourseSchedule.objects.filter(teacher=teacher_profile)
    print(f"\n课程安排数量: {schedules.count()}")
    
    if schedules.count() == 0:
        print("✗ 警告: 该教师没有课程安排")
        print("  可能的原因:")
        print("  1. 该教师还没有被分配到任何课程")
        print("  2. 课程安排中的teacher字段没有关联到该教师")
        print("  3. 需要管理员在课程管理中添加该教师为课程教师")
    else:
        print(f"\n课程安排列表:")
        for i, schedule in enumerate(schedules, 1):
            course_name = schedule.course.name if schedule.course else '未知课程'
            class_name = schedule.school_class.name if schedule.school_class else '未知班级'
            print(f"  {i}. {course_name} - {class_name} (ID: {schedule.id})")
            
            # 检查该班级是否有学生
            if schedule.school_class:
                students_count = StudentProfile.objects.filter(school_class=schedule.school_class).count()
                print(f"     班级学生数: {students_count}")
                if students_count == 0:
                    print(f"     ⚠ 警告: 该班级没有学生")
    
    # 检查班主任关联
    try:
        from personnel.models import Teacher as PersonnelTeacher
        personnel_teacher = PersonnelTeacher.objects.get(employee_id=teacher_profile.teacher_id)
        managed_classes = Class.objects.filter(head_teacher=personnel_teacher)
        print(f"\n班主任管理的班级数: {managed_classes.count()}")
        if managed_classes.count() > 0:
            print("班主任管理的班级:")
            for cls in managed_classes:
                students_count = StudentProfile.objects.filter(school_class=cls).count()
                print(f"  - {cls.name} (学生数: {students_count})")
    except Exception as e:
        print(f"\n班主任信息: 无法获取 (可能不是班主任)")
    
    print(f"\n{'='*60}")
    print("诊断完成")
    print(f"{'='*60}\n")
    
    # 给出建议
    if schedules.count() == 0:
        print("建议:")
        print("1. 检查课程管理页面，确认是否有课程安排给该教师")
        print("2. 确认课程安排中的'课程老师'字段是否正确关联到该教师")
        print("3. 如果该教师是班主任，可以通过班主任权限查看学生")
    
except User.DoesNotExist:
    print(f"✗ 错误: 找不到用户 {username}")
    print("  请确认用户名是否正确")

