from django.urls import path
from .views import list_teachers, create_teacher, edit_teacher, delete_teacher


urlpatterns = [
    path('', list_teachers, name='teachers_list'),
    path('create/', create_teacher, name='teachers_create'),
    path('edit/<int:pk>/', edit_teacher, name='teachers_edit'),
    path('delete/<int:pk>/', delete_teacher, name='teachers_delete'),
]
