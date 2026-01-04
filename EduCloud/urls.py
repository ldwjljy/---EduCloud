"""
URL configuration for EduCloud project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import home
from .views import OverviewStatsView, DashboardDataView, ClaimMyDataView, GlobalSearchView
from django.views.decorators.csrf import csrf_exempt
from .views import accounts_page, org_page, courses_page, attendance_page, grades_page, grades_entry_page, notices_page, calendar_page, dashboard_page, students_page, teachers_page, login_page, forgot_password_page, register_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('api/stats/overview', OverviewStatsView.as_view()),
    path('api/stats/dashboard', DashboardDataView.as_view()),
    path('api/stats/claim-data', ClaimMyDataView.as_view()),
    path('api/search', GlobalSearchView.as_view(), name='global_search'),
    path('ui/accounts', accounts_page),
    path('ui/courses', courses_page),
    path('ui/org', org_page),
    path('ui/attendance', attendance_page),
    path('ui/grades', grades_page),
    path('ui/grades-entry', grades_entry_page),
    path('ui/notices', notices_page),
    path('ui/calendar', calendar_page),
    path('ui/dashboard', dashboard_page),
    path('ui/login', login_page),
    path('ui/forgot-password', forgot_password_page, name='forgot_password'),
    path('accounts/register/', register_page, name='register'),
    path('ui/students', students_page),
    path('ui/teachers', teachers_page),
    path('api/accounts/', include('accounts.urls')),
    path('api/org/', include('organization.urls')),
    path('api/personnel/', include('personnel.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/attendance/', include('attendance_app.urls')),
    path('api/grades/', include('grades.urls')),
    path('api/notices/', include('notices.urls')),
    path('api/calendar/', include('calendarapp.urls')),
    path('api-auth/', include('rest_framework.urls')),
]
