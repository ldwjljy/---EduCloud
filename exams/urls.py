from django.urls import path
from .views import list_exams, create_exam, edit_exam, delete_exam


urlpatterns = [
    path('', list_exams, name='exams_list'),
    path('create/', create_exam, name='exams_create'),
    path('edit/<int:pk>/', edit_exam, name='exams_edit'),
    path('delete/<int:pk>/', delete_exam, name='exams_delete'),
]
