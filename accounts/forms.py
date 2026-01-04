from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=50)
    role = forms.ChoiceField(choices=[('student','学生'),('teacher','教师'),('admin','管理员')])

    class Meta:
        model = User
        fields = ('username','full_name','email','password1','password2','role')
