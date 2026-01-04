from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet,
    StudentProfileViewSet,
    TeacherProfileViewSet,
    AdministratorProfileViewSet,
    ObtainAuthTokenView,
    ChangePasswordView,
    ChangePhoneView,
    SetPasswordView,
    BulkImportView,
    MeView,
)

router = DefaultRouter()
router.register('profiles', UserProfileViewSet)
router.register('students', StudentProfileViewSet)
router.register('teachers', TeacherProfileViewSet)
router.register('admins', AdministratorProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/', ObtainAuthTokenView.as_view(), name='obtain_token'),
    path('password/change', ChangePasswordView.as_view(), name='change_password'),
    path('phone/change', ChangePhoneView.as_view(), name='change_phone'),
    path('password/set', SetPasswordView.as_view(), name='set_password'),
    path('import', BulkImportView.as_view(), name='bulk_import'),
    path('me', MeView.as_view(), name='me'),
]
