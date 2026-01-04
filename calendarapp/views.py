from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import CalendarEvent
from .serializers import CalendarEventSerializer
from accounts.permissions import IsAdminOrDeanOrReadOnly


class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeanOrReadOnly]

    def get_queryset(self):
        """根据用户权限过滤日程安排"""
        queryset = super().get_queryset()
        user = self.request.user
        
        # 超级管理员可以看到所有事件
        if getattr(user, 'is_superuser', False):
            return queryset
        
        profile = getattr(user, 'profile', None)
        if not profile:
            return queryset.none()
        
        role = profile.role
        
        # 管理员和院长可以看到所有事件
        if role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
            return queryset
        
        # 获取用户所属学院
        user_college = None
        if role in ['teacher', 'head_teacher']:
            teacher_profile = getattr(profile, 'teacher_profile', None)
            if teacher_profile and teacher_profile.department:
                user_college = getattr(teacher_profile.department, 'college', None)
        elif role == 'student':
            student_profile = getattr(profile, 'student_profile', None)
            if student_profile and student_profile.school_class and student_profile.school_class.major:
                user_college = student_profile.school_class.major.college
        
        # 构建过滤条件：可以看到的事件
        # 1. 全校可见的事件
        # 2. 指定学院的事件（如果用户属于该学院）
        # 3. 个人创建的事件
        filter_q = Q(visibility='all')
        if user_college:
            filter_q |= Q(visibility='college', college=user_college)
        filter_q |= Q(created_by=user)
        
        return queryset.filter(filter_q)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
