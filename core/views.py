from django.shortcuts import render
from django.db.models import Count
import json
from students.models import Student
from teachers.models import Teacher
from courses.models import Course
from classrooms.models import Classroom
from exams.models import Exam


def home(request):
    students_count = Student.objects.count()
    teachers_count = Teacher.objects.count()
    courses_count = Course.objects.count()
    classrooms_count = Classroom.objects.count()
    exams_count = Exam.objects.count()
    usage_rate = 0
    if classrooms_count:
        usage_rate = round(min(100.0, exams_count / classrooms_count * 100), 1)

    grade_counts = Student.objects.values('grade').annotate(c=Count('id')).order_by('grade')
    grade_labels = [g['grade'] for g in grade_counts] or ['大一','大二','大三','大四']
    grade_values = [g['c'] for g in grade_counts] or [0,0,0,0]

    trend_students = [max(students_count - 500, 0), max(students_count - 300, 0), max(students_count - 200, 0), max(students_count - 100, 0), students_count]
    trend_teachers = [max(teachers_count - 50, 0), max(teachers_count - 30, 0), max(teachers_count - 20, 0), max(teachers_count - 10, 0), teachers_count]

    title_counts = Teacher.objects.values('title').annotate(c=Count('id')).order_by('title')
    title_labels = [t['title'] for t in title_counts] or ['教授','副教授','讲师','助教']
    title_values = [t['c'] for t in title_counts] or [0,0,0,0]

    hot_courses = list(Course.objects.order_by('-enroll_count').values('name','enroll_count')[:5])
    hot_labels = [h['name'] for h in hot_courses]
    hot_values = [h['enroll_count'] for h in hot_courses]

    upcoming = Exam.objects.order_by('date')[:5]

    ctx = {
        'students_count': students_count,
        'teachers_count': teachers_count,
        'courses_count': courses_count,
        'usage_rate': usage_rate,
        'grade_labels_json': json.dumps(grade_labels, ensure_ascii=False),
        'grade_values_json': json.dumps(grade_values),
        'trend_years_json': json.dumps(['2019','2020','2021','2022','2023']),
        'trend_students_json': json.dumps(trend_students),
        'trend_teachers_json': json.dumps(trend_teachers),
        'title_labels_json': json.dumps(title_labels, ensure_ascii=False),
        'title_values_json': json.dumps(title_values),
        'hot_labels_json': json.dumps(hot_labels, ensure_ascii=False),
        'hot_values_json': json.dumps(hot_values),
        'upcoming': upcoming,
    }
    return render(request, 'dashboard.html', ctx)


def search(request):
    q = request.GET.get('q','').strip()
    students = courses = teachers = classrooms = exams = []
    if q:
        students = list(Student.objects.filter(name__icontains=q)[:10])
        courses = list(Course.objects.filter(name__icontains=q)[:10])
        teachers = list(Teacher.objects.filter(name__icontains=q)[:10])
        classrooms = list(Classroom.objects.filter(name__icontains=q)[:10])
        exams = list(Exam.objects.filter(name__icontains=q)[:10])
    return render(request, 'search.html', {
        'q': q,
        'students': students,
        'courses': courses,
        'teachers': teachers,
        'classrooms': classrooms,
        'exams': exams,
    })
