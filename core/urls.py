from django.urls import path
from .views import home, search
from students.views import student_list, student_add, student_edit, student_delete
from teachers.views import teacher_list, teacher_add, teacher_edit, teacher_delete
from courses.views import course_list, course_add, course_edit, course_delete
from classrooms.views import classroom_list, classroom_add, classroom_edit, classroom_delete
from exams.views import exam_list, exam_add, exam_edit, exam_delete

urlpatterns = [
    path('', home, name='home'),
    path('search/', search, name='search'),

    path('students/', student_list, name='student_list'),
    path('students/add/', student_add, name='student_add'),
    path('students/edit/<int:id>/', student_edit, name='student_edit'),
    path('students/delete/<int:id>/', student_delete, name='student_delete'),

    path('teachers/', teacher_list, name='teacher_list'),
    path('teachers/add/', teacher_add, name='teacher_add'),
    path('teachers/edit/<int:id>/', teacher_edit, name='teacher_edit'),
    path('teachers/delete/<int:id>/', teacher_delete, name='teacher_delete'),

    path('courses/', course_list, name='course_list'),
    path('courses/add/', course_add, name='course_add'),
    path('courses/edit/<int:id>/', course_edit, name='course_edit'),
    path('courses/delete/<int:id>/', course_delete, name='course_delete'),

    path('classrooms/', classroom_list, name='classroom_list'),
    path('classrooms/add/', classroom_add, name='classroom_add'),
    path('classrooms/edit/<int:id>/', classroom_edit, name='classroom_edit'),
    path('classrooms/delete/<int:id>/', classroom_delete, name='classroom_delete'),

    path('exams/', exam_list, name='exam_list'),
    path('exams/add/', exam_add, name='exam_add'),
    path('exams/edit/<int:id>/', exam_edit, name='exam_edit'),
    path('exams/delete/<int:id>/', exam_delete, name='exam_delete'),
]
