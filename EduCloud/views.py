from django.shortcuts import render, redirect
from django.db.models import Count
from accounts.models import UserProfile, StudentProfile, TeacherProfile
from organization.models import College, Major, Class
from courses.models import Course, CourseSchedule
from classrooms.models import Classroom
from attendance_app.models import Attendance
from grades.models import Grade
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from calendarapp.models import CalendarEvent
from django.db.models.functions import ExtractMonth, TruncDate
from django.db.models import Q
from datetime import timedelta
from notices.models import Notice
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from urllib.parse import quote


@login_required
def home(request):
    students_count = UserProfile.objects.filter(role='student').count()
    teachers_count = UserProfile.objects.filter(role__in=['teacher', 'head_teacher']).count()
    courses_count = Course.objects.count()
    sessions_count = CourseSchedule.objects.count()
    from courses.models import TimeSlot
    timeslots_total = TimeSlot.objects.count()
    classrooms_count = Classroom.objects.count()
    context = {
        'students_count': students_count,
        'teachers_count': teachers_count,
        'courses_count': courses_count,
        'classrooms_count': classrooms_count,
        'sessions_count': sessions_count,
    }
    return render(request, 'index.html', context)


class OverviewStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            'students': UserProfile.objects.filter(role='student').count(),
            'teachers': UserProfile.objects.filter(role__in=['teacher', 'head_teacher']).count(),
            'courses': Course.objects.count(),

            'sessions': CourseSchedule.objects.count(),
            'grades': Grade.objects.count(),
            'attendance_records': Attendance.objects.count(),
        }
        return Response(data)


@login_required
def accounts_page(request):
    return render(request, 'accounts.html', {'current_username': getattr(request.user, 'username', '')})


@login_required
def org_page(request):
    # 只有管理员和院长可以访问组织架构页面
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('无权访问组织架构页面')
    
    role = profile.role
    if role not in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('教师/班主任无权访问组织架构页面')
    
    return render(request, 'org.html')

@login_required
def courses_page(request):
    # 学生无权访问课程管理页面 -> 改为允许访问，但只能看课程表
    profile = getattr(request.user, 'profile', None)
    # if profile and profile.role == 'student':
    #     from django.http import HttpResponseForbidden
    #     return HttpResponseForbidden('学生无权访问课程管理页面')
    
    # 获取用户角色信息
    user_role = profile.role if profile else None
    
    # 权限检查：允许所有已登录用户访问，但不同角色看到的内容不同
    # 学生只允许查看自己的课程表
    
    is_teacher = user_role in ['teacher', 'head_teacher']
    is_admin = user_role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']
    is_student = user_role == 'student'
    
    context = {
        'current_username': getattr(request.user, 'username', ''),
        'user_role': user_role,
        'is_teacher': is_teacher,
        'is_admin': is_admin,
        'is_student': is_student,
    }
    return render(request, 'courses.html', context)


@login_required
def attendance_page(request):
    return render(request, 'attendance.html')


@login_required
def grades_page(request):
    # 教师/班主任使用专用的成绩管理界面，其它角色继续使用原有页面
    profile = getattr(request.user, 'profile', None)
    role = getattr(profile, 'role', None)
    if role in ['teacher', 'head_teacher']:
        return render(request, 'grades-teacher.html')
    return render(request, 'grades.html')


@login_required
def grades_entry_page(request):
    return render(request, 'grades-entry.html')


@login_required
def notices_page(request):
    # 所有已认证用户都可以访问通知公告页面，但只能看到允许他们看到的内容
    return render(request, 'notices.html')


@login_required
def calendar_page(request):
    return render(request, 'calendar.html')

@login_required
def dashboard_page(request):
    return render(request, 'dashboard.html')

@login_required
def students_page(request):
    # 只有管理员、院长和班主任可以访问学生管理页面，普通教师不能访问
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('无权访问学生管理页面')
    
    role = profile.role
    if role == 'teacher':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('普通教师无权访问学生管理页面')
    
    if role not in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'head_teacher', 'student']:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('无权访问学生管理页面')
    
    return render(request, 'students.html')

@login_required
def teachers_page(request):
    # 只有管理员和院长可以访问教师管理页面，教师/班主任不能访问
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('无权访问教师管理页面')
    
    role = profile.role
    if role in ['teacher', 'head_teacher']:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('教师/班主任无权访问教师管理页面')
    
    if role not in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('无权访问教师管理页面')
    
    return render(request, 'teachers.html')

def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username') or ''
        password = request.POST.get('password') or ''
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                # 如果没有勾选"记住我"，会话在浏览器关闭时失效
                request.session.set_expiry(0)
            # 如果勾选了，使用默认的 SESSION_COOKIE_AGE（通常是2周）
            
            # 登录成功后重定向到首页
            return redirect('/')
        return render(request, 'accounts/login.html', {'error': '用户名或密码错误'})
    if getattr(request, 'user', None) and request.user.is_authenticated:
        # 已登录用户访问登录页面时重定向到首页
        return redirect('/')
    return render(request, 'accounts/login.html')


def forgot_password_page(request):
    error = None
    success = None
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        student_id = request.POST.get('student_id', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # 验证必填字段
        if not name or not student_id:
            error = '请填写姓名和学号'
        elif not new_password or not confirm_password:
            error = '请填写新密码和确认密码'
        elif new_password != confirm_password:
            error = '两次输入的密码不一致'
        else:
            # 验证姓名和学号是否匹配
            try:
                # 查找学生档案
                student_profile = StudentProfile.objects.get(student_id=student_id)
                user = student_profile.user_profile.user
                
                # 验证姓名是否匹配
                if user.first_name != name:
                    error = '姓名与学号不匹配，请检查后重试'
                else:
                    # 验证新密码
                    try:
                        validate_password(new_password, user)
                        # 设置新密码
                        user.set_password(new_password)
                        user.save()
                        success = '密码重置成功！请使用新密码登录。'
                    except ValidationError as e:
                        error = '密码不符合要求：' + '; '.join(e.messages)
            except StudentProfile.DoesNotExist:
                error = '未找到该学号对应的学生信息'
            except Exception as e:
                error = '重置密码失败：' + str(e)
    
    return render(request, 'accounts/forgot_password.html', {
        'error': error,
        'success': success
    })


def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')
        role = request.POST.get('role', 'student')
        name = request.POST.get('full_name', '')
        
        # 基本验证
        if not username or not password:
            return render(request, 'accounts/register.html', {'error': '用户名和密码不能为空'})
        
        if password != confirm_password:
            return render(request, 'accounts/register.html', {'error': '两次输入的密码不一致'})
            
        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/register.html', {'error': '用户名已存在'})
            
        try:
            # 创建用户
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = name
            user.save()
            
            # 创建用户档案
            profile = UserProfile.objects.create(user=user, role=role)
            
            # 根据角色创建对应档案
            if role == 'student':
                # 生成临时学号: S + 年月 + 随机4位数
                import random
                from datetime import datetime
                suffix = str(random.randint(1000, 9999))
                student_id = f"S{datetime.now().strftime('%Y%m')}{suffix}"
                StudentProfile.objects.create(
                    user_profile=profile,
                    student_id=student_id,
                    status='在读'
                )
            elif role in ['teacher', 'head_teacher']:
                # 生成临时工号: T + 年月 + 随机4位数
                import random
                from datetime import datetime
                suffix = str(random.randint(1000, 9999))
                teacher_id = f"T{datetime.now().strftime('%Y%m')}{suffix}"
                TeacherProfile.objects.create(
                    user_profile=profile,
                    teacher_id=teacher_id
                )
            
            # 注册成功后自动登录
            login(request, user)
            return redirect('/')
            
        except Exception as e:
            return render(request, 'accounts/register.html', {'error': f'注册失败: {str(e)}'})
            
    return render(request, 'accounts/register.html')
class DashboardDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取真实的北京时间
        now = timezone.localtime(timezone.now())
        year = now.year
        
        params = request.query_params
        college_id = params.get('college')
        department_id = params.get('department')
        
        # 从数据库直接获取所有数据（确保数据准确，不受任何过滤条件影响）
        # 学生总数：统计所有StudentProfile记录（真实数据）
        students_total = StudentProfile.objects.all().count()
        # 教师总数：统计所有TeacherProfile记录（真实数据）
        teachers_total = TeacherProfile.objects.all().count()
        # 课程总数：统计所有Course记录（真实数据）
        courses_total = Course.objects.all().count()
        
        # Build filtered querysets based on college/department filters（用于其他统计）
        base_students = StudentProfile.objects.select_related('user_profile', 'school_class').all()
        base_teachers = TeacherProfile.objects.select_related('user_profile', 'department').all()
        base_courses = Course.objects.select_related('teacher', 'department').all()
        
        if department_id:
            # Filter by department (Major)
            base_students = base_students.filter(school_class__major_id=department_id)
            base_teachers = base_teachers.filter(department_id=department_id)
            base_courses = base_courses.filter(department_id=department_id)
        elif college_id:
            # Filter by college
            base_students = base_students.filter(school_class__major__college_id=college_id)
            base_teachers = base_teachers.filter(department__college_id=college_id)
            base_courses = base_courses.filter(department__college_id=college_id)
        
        timeslots_total = 0
        from courses.models import TimeSlot
        timeslots_total = TimeSlot.objects.count()

        base_students_for_grades = base_students.filter(created_by=request.user) if not (college_id or department_id) else base_students
        grade_rows = list(
            base_students_for_grades
            .values('school_class__enrollment_year')
            .annotate(c=Count('id'))
            .order_by('-school_class__enrollment_year')[:4]
        )
        grade_counts = [
            {'label': f"{str(r['school_class__enrollment_year'])[-2:]}届", 'value': r['c']}
            for r in grade_rows
        ]

        # 统计教师职务分布（基于UserProfile的role字段）
        from accounts.models import USER_ROLES
        position_counts = {'院长': 0, '副院长': 0, '班主任': 0, '教师': 0, '其他': 0}
        for tp in base_teachers.select_related('user_profile'):
            role = tp.user_profile.role if tp.user_profile else None
            if role == 'dean':
                position_counts['院长'] += 1
            elif role == 'vice_dean':
                position_counts['副院长'] += 1
            elif role == 'head_teacher':
                position_counts['班主任'] += 1
            elif role == 'teacher':
                position_counts['教师'] += 1
            else:
                position_counts['其他'] += 1

        # 课程安排查询（用于统计本周课程数）
        # 为了确保数据准确，使用所有课程安排进行统计
        base_schedules_all = CourseSchedule.objects.select_related('course', 'timeslot', 'school_class').all()
        
        # 如果指定了过滤条件，创建过滤后的查询集（用于其他统计，但不影响总数）
        if department_id:
            base_schedules_filtered = base_schedules_all.filter(course__department_id=department_id)
        elif college_id:
            base_schedules_filtered = base_schedules_all.filter(course__department__college_id=college_id)
        else:
            base_schedules_filtered = base_schedules_all
        
        # 用于统计本周课程数，使用所有课程安排
        base_schedules = base_schedules_all
        
        # 获取今天的星期几（使用北京时间，Python weekday: 0=周一, 6=周日，系统 weekday: 1=周一, 7=周日）
        today_weekday = now.weekday() + 1
        
        # 计算当前是第几周（根据学期开始日期计算，使用北京时间）
        from django.conf import settings
        from datetime import datetime, date
        # 获取当前北京时间的日期
        beijing_date = now.date()
        
        try:
            # 解析学期开始日期（假设为北京时间）
            semester_start_str = settings.SEMESTER_START_DATE
            configured_start = datetime.strptime(semester_start_str, '%Y-%m-%d').date()
            
            # 自动确定当前应该使用的学期开始日期
            # 规则：如果当前日期已经过了今年9月1日，使用今年的9月1日；否则使用配置的日期
            this_year_sept = date(beijing_date.year, 9, 1)
            
            if beijing_date >= this_year_sept:
                # 当前日期已经过了今年9月1日，使用今年的9月1日作为学期开始
                semester_start = this_year_sept
            else:
                # 当前日期在9月1日之前，检查是否应该使用上一年的9月1日
                # 或者如果配置的日期是今年的，但还没到9月，使用上一年的
                if configured_start.year == beijing_date.year and beijing_date < this_year_sept:
                    # 配置的是今年的日期，但还没到，使用上一年的9月1日
                    semester_start = date(beijing_date.year - 1, 9, 1)
                else:
                    # 使用配置的日期（可能是跨年学期的情况）
                    semester_start = configured_start
        except (AttributeError, ValueError):
            # 如果没有配置，默认使用9月1日（秋季学期开始）
            semester_start = date(beijing_date.year, 9, 1)
            # 如果当前日期在9月之前，使用上一年的9月1日
            if beijing_date < date(beijing_date.year, 9, 1):
                semester_start = date(beijing_date.year - 1, 9, 1)
        
        # 计算从学期开始到现在的天数（使用北京时间）
        days_since_start = (beijing_date - semester_start).days
        
        # 计算当前是第几周（从第1周开始）
        if days_since_start < 0:
            # 如果还没到学期开始，返回第1周
            current_week = 1
        else:
            # 计算周次：天数除以7，加1（第1周从第0天开始）
            # 例如：第0-6天是第1周，第7-13天是第2周
            current_week = (days_since_start // 7) + 1
        
        # 获取学期总周数
        try:
            max_weeks = settings.SEMESTER_TOTAL_WEEKS
        except AttributeError:
            max_weeks = 20
        
        # 记录计算出的原始周数（用于调试）
        calculated_week = current_week
        
        # 如果计算出的周数超过学期总周数，说明学期已经结束，但仍显示最后一周
        # 或者如果周数小于1，设为1
        if current_week < 1:
            current_week = 1
        elif current_week > max_weeks:
            # 学期已结束，显示最后一周
            current_week = max_weeks
        
        # 获取当前周次对应星期几的所有课程安排（只显示当前周次的课程）
        # 使用过滤后的查询集（如果用户选择了学院/专业）
        if department_id or college_id:
            this_weekday_schedules = base_schedules_filtered.filter(
                timeslot__weekday=today_weekday,
                week_number=current_week
            )
        else:
            this_weekday_schedules = base_schedules_all.filter(
                timeslot__weekday=today_weekday,
                week_number=current_week
            )
        
        # 计算当前周次这一天总共有多少节课程（真实的课程节数）
        today_total_classes = this_weekday_schedules.count()
        
        # 按当前周次这一天的课程数量排名（每个课程名称对应的课程节数）
        hot = list(this_weekday_schedules.values('course__name').annotate(count=Count('id')).order_by('-count')[:5])
        hot_courses = [{'name': h['course__name'], 'count': h['count']} for h in hot]

        # 统计每天全校的课程总数（按星期几统计，仅统计周一到周五）- 从数据库直接获取真实数据
        # 使用所有课程安排，确保数据准确
        week_course_distribution = []
        weekday_names = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        # 统计所有课程安排（按星期几），仅统计周一到周五（5天），不受周次限制，确保数据准确
        # 这样可以显示所有课程的真实分布情况
        for weekday in range(1, 6):  # 1-5 对应周一到周五
            # 从数据库直接查询该星期几的所有课程安排（所有周次）
            weekday_schedules = base_schedules_all.filter(timeslot__weekday=weekday)
            # 统计课程节数（真实数据）
            course_count = weekday_schedules.count()
            week_course_distribution.append({
                'label': weekday_names[weekday],
                'value': course_count
            })
        
        # 计算课程总数（周一到周五的课程节数之和）- 真实数据
        total_week_courses = sum(item['value'] for item in week_course_distribution)
        
        # 调试信息：确保数据正确
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'Dashboard数据统计: 学生={students_total}, 教师={teachers_total}, 课程={courses_total}, 课程安排总数={total_week_courses}')
        
        # 如果当前周次在有效范围内，也提供本周的课程统计
        if 1 <= current_week <= max_weeks:
            # 可选：如果需要显示本周的课程分布，可以单独统计
            # 但为了数据准确性，我们使用所有课程的数据
            pass

        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)
        def _user_college(user):
            profile = getattr(user, 'profile', None)
            role = getattr(profile, 'role', None)
            if role in ['teacher', 'head_teacher']:
                tp = getattr(profile, 'teacher_profile', None)
                if tp and tp.department:
                    return getattr(tp.department, 'college', None)
            if role == 'student':
                sp = getattr(profile, 'student_profile', None)
                if sp and sp.school_class and sp.school_class.major:
                    return getattr(sp.school_class.major, 'college', None)
            return None
        role = getattr(getattr(request.user, 'profile', None), 'role', None)
        base_qs = CalendarEvent.objects.filter(start_time__gte=month_start, start_time__lt=next_month)
        if role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
            month_events = base_qs.order_by('start_time')
        elif role in ['teacher', 'head_teacher']:
            col = _user_college(request.user)
            if col:
                month_events = base_qs.filter(Q(visibility='all') | (Q(visibility='college') & Q(college=col)) | Q(created_by=request.user)).order_by('start_time')
            else:
                month_events = base_qs.filter(Q(visibility='all') | Q(created_by=request.user)).order_by('start_time')
        elif role == 'student':
            col = _user_college(request.user)
            if col:
                month_events = base_qs.filter(Q(visibility='all') | (Q(visibility='college') & Q(college=col))).order_by('start_time')
            else:
                month_events = base_qs.filter(visibility='all').order_by('start_time')
        else:
            month_events = base_qs.filter(visibility='all').order_by('start_time')
        days_with_events = list(set([e.start_time.day for e in month_events]))
        upcoming = [{'title': e.title, 'time': e.start_time.strftime('%m月%d日 %H:%M')} for e in month_events[:5]]

        qs = base_students.filter(user_profile__user__date_joined__year=year)
        month_counts = {m: 0 for m in range(1, 13)}
        for row in qs.annotate(m=ExtractMonth('user_profile__user__date_joined')).values('m').annotate(c=Count('id')):
            month_counts[row['m']] = row['c']

        days_param = request.query_params.get('days')
        try:
            # 统一使用 days_window 控制时间窗口，后面考勤趋势也共用这个窗口
            days_window = max(1, min(180, int(days_param))) if days_param is not None else 30
        except Exception:
            days_window = 30
        end_date = now.date()
        start_date = end_date - timedelta(days=days_window - 1)
        day_qs = base_students.filter(
            user_profile__user__date_joined__date__gte=start_date,
            user_profile__user__date_joined__date__lte=end_date,
        )
        day_counts_map = {}
        for row in day_qs.annotate(d=TruncDate('user_profile__user__date_joined')).values('d').annotate(c=Count('id')):
            day_counts_map[row['d']] = row['c']
        daily_dates = []
        daily_counts = []
        cur = start_date
        while cur <= end_date:
            daily_dates.append(cur.strftime('%Y-%m-%d'))
            daily_counts.append(day_counts_map.get(cur, 0))
            cur += timedelta(days=1)

        # 改进的课程分类逻辑，增加公共课等分类
        cats = {
            '公共课': [
                '历史', '商务英语', '英语', '大学英语', '公共英语', '思想政治', '思修', '毛概', 
                '马克思主义', '毛泽东', '邓小平', '体育', '军事', '国防', '心理健康', '心理', 
                '就业指导', '职业生涯', '创新创业', '创业', '通识', '人文', '艺术', '音乐', 
                '美术', '书法', '文学', '写作', '应用文', '公文', '礼仪', '沟通', '演讲',
                '法律基础', '法学', '经济法', '劳动法', '形势与政策', '形势政策', '安全教育'
            ],
            '计算机科学': [
                '计', '软件', '人工智能', '数据', '网络', '算法', '编程', '程序', '开发', 
                '系统', '数据库', '网页', '网站', '前端', '后端', 'Java', 'Python', 'C++',
                'C语言', '操作系统', '编译', '计算机', '信息', '电子', '通信'
            ],
            '数学': [
                '数学', '高数', '高等数学', '线性代数', '概率', '统计', '微积分', '离散',
                '数理', '运筹', '几何', '代数'
            ],
            '物理': [
                '物理', '力学', '电学', '光学', '热学', '量子', '原子', '核物理'
            ],
            '化学': [
                '化学', '有机', '无机', '分析', '物化', '生化', '高分子'
            ],
            '生物': [
                '生物', '细胞', '遗传', '分子', '生态', '生理', '解剖'
            ],
            '外语': [
                '法语', '日语', '德语', '俄语', '西班牙语', '韩语', '阿拉伯语', '翻译',
                '口译', '笔译', '商务', '专业英语', '科技英语'
            ],
            '经济管理': [
                '经济', '管理', '会计', '财务', '金融', '市场', '营销', '人力', '物流',
                '工商', '商务', '贸易', '投资', '证券', '保险', '银行', '审计', '统计',
                '国际商务', '电子商务', '企业管理', '项目管理'
            ],
            '工程': [
                '工程', '机械', '电气', '自动化', '建筑', '土木', '材料', '化工', '环境',
                '能源', '交通', '车辆', '航空', '航天'
            ],
        }
        cat_counts = {k: 0 for k in list(cats.keys()) + ['其他']}
        
        # 按优先级匹配（公共课优先，避免被其他分类误判）
        for name in base_courses.values_list('name', flat=True):
            n = (name or '').strip()
            matched = False
            
            # 先检查公共课（优先级最高）
            for cat, keys in cats.items():
                if cat == '公共课':
                    # 公共课使用更精确的匹配
                    for key in keys:
                        if key in n:
                            cat_counts[cat] += 1
                            matched = True
                            break
                    if matched:
                        break
            
            # 如果公共课未匹配，检查其他分类
            if not matched:
                for cat, keys in cats.items():
                    if cat != '公共课':  # 跳过公共课，已经检查过了
                        if any(k in n for k in keys):
                            cat_counts[cat] += 1
                            matched = True
                            break
            
            if not matched:
                cat_counts['其他'] += 1

        # 使用北京时间获取当前时间戳
        now_ts = timezone.localtime(timezone.now())
        notices = Notice.objects.all().order_by('-created_at')[:5]
        recent = []
        for n in notices:
            t = getattr(n, 'created_at', now_ts)
            # 如果时间有时区信息，转换为本地时间
            if hasattr(t, 'astimezone'):
                t = timezone.localtime(t)
            title = getattr(n, 'title', '')
            status = '已完成'
            s = title
            if any(k in s for k in ['审核', '申请', '待', '审批']):
                status = '待处理'
            recent.append({'title': title, 'time': t.strftime('%m月%d日 %H:%M'), 'status': status})
        for e in month_events[:5]:
            # 确保事件时间也使用本地时间进行比较和格式化
            event_time = e.start_time
            if hasattr(event_time, 'astimezone'):
                event_time = timezone.localtime(event_time)
            status = '进行中' if event_time >= now_ts else '已完成'
            recent.append({'title': e.title, 'time': event_time.strftime('%m月%d日 %H:%M'), 'status': status})

        # 确保数据完全准确：直接从数据库统计，不受任何过滤条件影响
        # 如果传入了college或department参数，cards中的总数仍然显示全部数据
        # 但week_course_distribution会按过滤条件显示
        
        # 直接从数据库获取真实数据
        students_total_final = StudentProfile.objects.all().count()
        teachers_total_final = TeacherProfile.objects.all().count()
        courses_total_final = Course.objects.all().count()
        
        # 确保total_week_courses是整数
        total_week_courses_final = int(total_week_courses) if total_week_courses else 0
        
        # 根据同一个 days_window 计算考勤趋势
        # 口径：按“学生人数”统计，每天每个学生只算一次，并按最严重状态归类
        # 严重程度优先级：absent > late > leave > present
        att_end_date = now.date()
        att_start_date = att_end_date - timedelta(days=days_window - 1)

        att_qs = Attendance.objects.filter(
            date__gte=att_start_date,
            date__lte=att_end_date,
        )
        if department_id:
            att_qs = att_qs.filter(student__school_class__major_id=department_id)
        elif college_id:
            att_qs = att_qs.filter(student__school_class__major__college_id=college_id)

        # 统计口径：同一天同一学生，根据“当前所有课程状态”取最严重状态
        # 严重程度优先级：absent > late > leave > present
        status_priority = {'present': 0, 'leave': 1, 'late': 2, 'absent': 3}
        per_day_student_status = {}
        for row in att_qs.values('date', 'student', 'status', 'id').order_by('date', 'student', 'id'):
            d = row['date']
            s_id = row['student']
            s = row['status']
            day_map = per_day_student_status.setdefault(d, {})
            if s_id not in day_map:
                day_map[s_id] = s
            else:
                old = day_map[s_id]
                # 如果新状态更严重，则覆盖
                if status_priority.get(s, 0) > status_priority.get(old, 0):
                    day_map[s_id] = s

        # 统计每天各状态的学生人数
        att_map_data = {}
        for d, stu_map in per_day_student_status.items():
            day_counts = {'present': 0, 'late': 0, 'absent': 0, 'leave': 0}
            for _sid, st in stu_map.items():
                if st in day_counts:
                    day_counts[st] += 1
            att_map_data[d] = day_counts

        # 补齐时间窗口内没有记录的日期
        curr_d = att_start_date
        while curr_d <= att_end_date:
            if curr_d not in att_map_data:
                att_map_data[curr_d] = {'present': 0, 'late': 0, 'absent': 0, 'leave': 0}
            curr_d += timedelta(days=1)
                
        att_dates_list = []
        att_present_list = []
        att_late_list = []
        att_absent_list = []
        att_leave_list = []
        
        curr_d = att_start_date
        while curr_d <= att_end_date:
            counts = att_map_data.get(curr_d, {'present': 0, 'late': 0, 'absent': 0, 'leave': 0})
            att_dates_list.append(curr_d.strftime('%m-%d'))
            att_present_list.append(counts['present'])
            att_late_list.append(counts['late'])
            att_absent_list.append(counts['absent'])
            att_leave_list.append(counts['leave'])
            curr_d += timedelta(days=1)

        # Calculate Today's Attendance Stats（按学生人数，按严重程度优先级合并所有课程）
        today_date = now.date()
        att_today_qs = Attendance.objects.filter(date=today_date)
        if department_id:
            att_today_qs = att_today_qs.filter(student__school_class__major_id=department_id)
        elif college_id:
            att_today_qs = att_today_qs.filter(student__school_class__major__college_id=college_id)

        today_status_by_student = {}
        for row in att_today_qs.values('student', 'status', 'id').order_by('student', 'id'):
            s_id = row['student']
            s = row['status']
            if s_id not in today_status_by_student:
                today_status_by_student[s_id] = s
            else:
                old = today_status_by_student[s_id]
                if status_priority.get(s, 0) > status_priority.get(old, 0):
                    today_status_by_student[s_id] = s

        att_today_map = {'present': 0, 'late': 0, 'absent': 0, 'leave': 0}
        for _sid, st in today_status_by_student.items():
            if st in att_today_map:
                att_today_map[st] += 1

        # 统计每个学院的学生人数
        college_student_counts = []
        for college in College.objects.filter(is_deleted=False):
            # 统计该学院下的所有学生（通过专业->班级->学生）
            student_count = StudentProfile.objects.filter(
                school_class__major__college=college,
                school_class__major__is_deleted=False,
                school_class__is_deleted=False
            ).count()
            if student_count > 0:  # 只返回有学生的学院
                college_student_counts.append({
                    'label': college.name,
                    'value': student_count
                })
        # 按人数降序排序
        college_student_counts.sort(key=lambda x: x['value'], reverse=True)

        data = {
            'cards': {
                'students_total': students_total_final,  # 从数据库直接统计的学生总数（不受过滤影响）
                'teachers_total': teachers_total_final,  # 从数据库直接统计的教师总数（不受过滤影响）
                'courses_total': courses_total_final,  # 从数据库直接统计的课程总数（不受过滤影响）
            },
            'total_week_courses': total_week_courses_final,  # 本周课程总节数（从数据库直接统计的真实数据）
            'grade_distribution': grade_counts,
            'college_student_distribution': college_student_counts,  # 每个学院的学生人数
            'teacher_position_distribution': position_counts,
            'hot_courses_top5': hot_courses,
            'today_total_classes': today_total_classes,  # 当前周次这一天总课程节数
            'current_week': current_week,  # 当前周次（根据学期开始日期计算）
            'today_weekday': today_weekday,  # 今天是星期几（1-7）
            'semester_total_weeks': max_weeks,  # 学期总周数
            'week_course_distribution': week_course_distribution,  # 本周课程分布（按星期几）
            'calendar': {
                'days_with_events': days_with_events,
                'upcoming': upcoming,
                'month': month_start.strftime('%Y-%m'),
            },
            'monthly_students': {
                'months': list(range(1, 13)),
                'counts': [month_counts[m] for m in range(1, 13)],
            },
            'daily_students': {
                'dates': daily_dates,
                'counts': daily_counts,
            },
            'attendance_trend': {
                'dates': att_dates_list,
                'series': {
                    'present': att_present_list,
                    'late': att_late_list,
                    'absent': att_absent_list,
                    'leave': att_leave_list
                }
            },
            'attendance_today': att_today_map,
            'course_distribution': [{'label': k, 'value': v} for k, v in cat_counts.items()],
            'recent': recent,
        }
        return Response(data)


class ClaimMyDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        types = request.data.get('types') or ['students', 'teachers', 'schedules']
        res = {}
        if 'students' in types:
            res['students'] = StudentProfile.objects.filter(created_by__isnull=True).update(created_by=request.user)
        from accounts.models import TeacherProfile
        if 'teachers' in types:
            res['teachers'] = TeacherProfile.objects.filter(created_by__isnull=True).update(created_by=request.user)
        if 'schedules' in types:
            res['schedules'] = CourseSchedule.objects.filter(created_by__isnull=True).update(created_by=request.user)
        return Response({'claimed': res})


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 5))
        
        if not q or len(q) < 2:
            return Response({
                'students': [],
                'teachers': [],
                'courses': [],
                'classes': [],
                'classrooms': [],
                'notices': [],
                'pages': []
            })
        
        results = {
            'students': [],
            'teachers': [],
            'courses': [],
            'classes': [],
            'classrooms': [],
            'notices': [],
            'pages': []
        }
        
        # 根据用户权限定义可访问的管理页面列表
        user_role = None
        if hasattr(request.user, 'profile'):
            user_role = request.user.profile.role
        
        # 定义所有管理页面
        all_pages = [
            {'name': '学生管理', 'url': '/ui/students', 'keywords': ['学生', '学生管理', 'student', 'students'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'head_teacher', 'student']},
            {'name': '教师管理', 'url': '/ui/teachers', 'keywords': ['教师', '教师管理', 'teacher', 'teachers'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']},
            {'name': '课程管理', 'url': '/ui/courses', 'keywords': ['课程', '课程管理', 'course', 'courses'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'teacher', 'head_teacher']},
            {'name': '组织架构', 'url': '/ui/org', 'keywords': ['组织', '组织架构', 'org', 'organization', '架构'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']},
            {'name': '考勤管理', 'url': '/ui/attendance', 'keywords': ['考勤', '考勤管理', 'attendance', '出勤'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'teacher', 'head_teacher']},
            {'name': '成绩管理', 'url': '/ui/grades', 'keywords': ['成绩', '成绩管理', 'grade', 'grades', '分数'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'teacher', 'head_teacher']},
            {'name': '日程安排', 'url': '/ui/calendar', 'keywords': ['日程', '日程安排', 'calendar', '日历', '安排'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'teacher', 'head_teacher', 'student']},
            {'name': '通知公告', 'url': '/ui/notices', 'keywords': ['通知', '通知公告', 'notice', 'notices', '公告'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'teacher', 'head_teacher', 'student']},
            {'name': '仪表盘', 'url': '/ui/dashboard', 'keywords': ['仪表盘', 'dashboard', '看板', '数据'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'teacher', 'head_teacher']},
            {'name': '个人设置', 'url': '/ui/accounts', 'keywords': ['个人', '个人设置', '设置', 'account', 'accounts', '配置'], 'roles': ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean', 'teacher', 'head_teacher', 'student']},
        ]
        
        # 根据用户角色过滤可访问的页面
        if getattr(request.user, 'is_superuser', False):
            management_pages = all_pages
        elif user_role:
            management_pages = [p for p in all_pages if user_role in p['roles']]
        else:
            management_pages = []
        
        # 搜索管理页面
        q_lower = q.lower()
        for page in management_pages:
            # 检查关键词匹配
            if any(keyword.lower() in q_lower or q_lower in keyword.lower() for keyword in page['keywords']):
                results['pages'].append({
                    'name': page['name'],
                    'url': page['url'],
                    'description': f'跳转到{page["name"]}页面'
                })
                if len(results['pages']) >= limit:
                    break
        
        # 根据用户权限获取可搜索的学生范围
        user = request.user
        
        # 获取基础查询集
        if getattr(user, 'is_superuser', False):
            base_qs = StudentProfile.objects.all()
        elif hasattr(user, 'profile'):
            role = user.profile.role
            if role in ['super_admin', 'principal', 'vice_principal']:
                base_qs = StudentProfile.objects.all()
            elif role == 'head_teacher':
                from personnel.models import Teacher as PersonnelTeacher
                teacher = getattr(user.profile, 'teacher_profile', None)
                if teacher:
                    try:
                        pt = PersonnelTeacher.objects.get(employee_id=teacher.teacher_id)
                        base_qs = StudentProfile.objects.filter(school_class__head_teacher=pt)
                    except PersonnelTeacher.DoesNotExist:
                        base_qs = StudentProfile.objects.none()
                else:
                    base_qs = StudentProfile.objects.none()
            elif role == 'teacher':
                # 普通教师不能搜索学生
                base_qs = StudentProfile.objects.none()
            elif role == 'student':
                base_qs = StudentProfile.objects.filter(user_profile=user.profile)
            else:
                base_qs = StudentProfile.objects.none()
        else:
            base_qs = StudentProfile.objects.none()
        
        # 搜索学生
        students = base_qs.filter(
            Q(student_id__icontains=q) |
            Q(user_profile__user__first_name__icontains=q) |
            Q(user_profile__user__username__icontains=q)
        ).select_related('user_profile__user', 'school_class')[:limit]
        
        for s in students:
            results['students'].append({
                'id': s.id,
                'student_id': s.student_id,
                'name': s.user_profile.user.first_name or s.user_profile.user.username,
                'class_name': s.school_class.name if s.school_class else '-',
                'url': f'/ui/students?q={quote(q)}'
            })
        
        # 搜索教师（只有管理员和院长可以搜索教师管理页面）
        if user_role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean'] or getattr(request.user, 'is_superuser', False):
            teachers = TeacherProfile.objects.filter(
                Q(teacher_id__icontains=q) |
                Q(user_profile__user__first_name__icontains=q) |
                Q(user_profile__user__username__icontains=q)
            ).select_related('user_profile__user', 'department')[:limit]
            
            for t in teachers:
                results['teachers'].append({
                    'id': t.id,
                    'teacher_id': t.teacher_id,
                    'name': t.user_profile.user.first_name or t.user_profile.user.username,
                    'title': t.title or '-',
                    'url': f'/ui/teachers?q={quote(q)}'
                })
        
        # 搜索课程
        courses = Course.objects.filter(
            Q(name__icontains=q) |
            Q(subject_id__icontains=q)
        ).select_related('department', 'teacher__user_profile__user')[:limit]
        
        for c in courses:
            results['courses'].append({
                'id': c.id,
                'name': c.name,
                'code': c.subject_id,
                'department': c.department.name if c.department else '-',
                'url': f'/ui/courses?q={quote(q)}'
            })
        
        # 搜索班级（只有管理员和院长可以搜索组织架构页面）
        if user_role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean'] or getattr(request.user, 'is_superuser', False):
            classes = Class.objects.filter(
                Q(name__icontains=q)
            ).select_related('major', 'major__college')[:limit]
            
            for cls in classes:
                results['classes'].append({
                    'id': cls.id,
                    'name': cls.name,
                    'major': cls.major.name if cls.major else '-',
                    'college': cls.major.college.name if cls.major and cls.major.college else '-',
                    'url': f'/ui/org'
                })
        
        # 搜索教室
        classrooms = Classroom.objects.filter(
            Q(name__icontains=q) |
            Q(location__icontains=q)
        )[:limit]
        
        results['classrooms'] = []
        for room in classrooms:
            results['classrooms'].append({
                'id': room.id,
                'name': room.name,
                'location': getattr(room, 'location', '-'),
                'capacity': getattr(room, 'capacity', '-'),
                'url': f'/ui/org'
            })
        
        # 搜索通知（所有用户都可以搜索，但需要根据scope过滤）
        notices_query = Notice.objects.filter(
            Q(title__icontains=q) | Q(content__icontains=q)
        )
        
        # 根据用户角色和公告scope过滤
        if user_role == 'student':
            # 学生只能看到全校范围的公告
            notices_query = notices_query.filter(scope='all')
        elif user_role in ['teacher', 'head_teacher']:
            # 教师/班主任可以看到全校和教师范围的公告
            notices_query = notices_query.filter(scope__in=['all', 'role'])
        elif user_role not in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
            # 其他角色只能看到全校范围的公告
            notices_query = notices_query.filter(scope='all')
        # 管理员可以看到所有范围的公告，不需要额外过滤
        
        notices = notices_query.order_by('-created_at')[:limit]
        results['notices'] = []
        for notice in notices:
            results['notices'].append({
                'id': notice.id,
                'title': notice.title,
                'content': (notice.content or '')[:50] + '...' if notice.content and len(notice.content) > 50 else (notice.content or ''),
                'url': f'/ui/notices?q={quote(q)}'
            })
        
        return Response(results)
