from django.urls import path
from .views import list_classrooms, create_classroom, edit_classroom, delete_classroom


urlpatterns = [
    path('', list_classrooms, name='classrooms_list'),
    path('create/', create_classroom, name='classrooms_create'),
    path('edit/<int:pk>/', edit_classroom, name='classrooms_edit'),
    path('delete/<int:pk>/', delete_classroom, name='classrooms_delete'),
]
