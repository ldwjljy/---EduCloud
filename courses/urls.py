from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    TimeSlotViewSet,
    ScheduleTimeConfigViewSet,
    CourseScheduleViewSet,
    GenerateStandardTimeSlotsView,
    AutoScheduleView,
    OptimizeConflictsView,
)

router = DefaultRouter()
router.register('courses', CourseViewSet)
router.register('timeslots', TimeSlotViewSet)
router.register('time-configs', ScheduleTimeConfigViewSet)
router.register('schedules', CourseScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('timeslots/generate', GenerateStandardTimeSlotsView.as_view(), name='generate_timeslots'),
    path('schedules/auto', AutoScheduleView.as_view(), name='auto_schedule'),
    path('schedules/optimize-conflicts', OptimizeConflictsView.as_view(), name='optimize_conflicts'),
]
