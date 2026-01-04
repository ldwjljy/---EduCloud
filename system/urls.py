from django.urls import path
from .views import index


urlpatterns = [
    path('', index, name='system_index'),
]
