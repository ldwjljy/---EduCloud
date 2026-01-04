from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Notice
from .serializers import NoticeSerializer
from accounts.permissions import IsAdminOnlyOrReadOnly


class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all().order_by('-created_at')
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated, IsAdminOnlyOrReadOnly]
    pagination_class = None  # 禁用分页，返回所有数据

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        
        # 超级管理员可以看到所有公告（即使没有profile）
        if user.is_superuser:
            return Notice.objects.all().order_by('-created_at')
        
        profile = getattr(user, 'profile', None)
        if not profile:
            return Notice.objects.none()
        
        role = profile.role
        params = self.request.query_params
        mine = params.get('mine')
        
        if mine in ('1', 'true', 'yes'):
            # 只看自己发布的
            base = Notice.objects.filter(created_by=user)
        else:
            # 根据用户角色和公告scope过滤
            if role == 'student':
                # 学生只能看到全校范围的公告
                base = Notice.objects.filter(scope='all')
            elif role in ['teacher', 'head_teacher']:
                # 教师/班主任可以看到全校和教师范围的公告
                base = Notice.objects.filter(scope__in=['all', 'role'])
            elif role in ['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean']:
                # 管理员可以看到所有范围的公告
                base = Notice.objects.filter(scope__in=['all', 'role', 'college', 'department'])
            else:
                # 其他角色只能看到全校范围的公告
                base = Notice.objects.filter(scope='all')

        pr = params.get('publisher_role')
        if pr == 'teacher':
            base = base.filter(created_by__profile__role__in=['teacher', 'head_teacher'])
        elif pr == 'admin':
            base = base.filter(created_by__profile__role__in=['super_admin', 'principal', 'vice_principal', 'dean', 'vice_dean'])

        q = (params.get('q') or '').strip()
        if q:
            base = base.filter(Q(title__icontains=q) | Q(content__icontains=q))
        return base.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
