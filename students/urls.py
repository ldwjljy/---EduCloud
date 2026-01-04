from django.urls import path
from .views import list_students, create_student, edit_student, delete_student


urlpatterns = [
    path('', list_students, name='students_list'),
    path('create/', create_student, name='students_create'),
    path('edit/<int:pk>/', edit_student, name='students_edit'),
    path('delete/<int:pk>/', delete_student, name='students_delete'),
]
