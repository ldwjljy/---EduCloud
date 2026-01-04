from rest_framework import serializers
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    # 学生信息
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    student_name = serializers.SerializerMethodField()
    # 课程信息
    course_name = serializers.CharField(source='schedule.course.name', read_only=True)
    course_id = serializers.IntegerField(source='schedule.course.id', read_only=True)
    schedule_id = serializers.IntegerField(source='schedule.id', read_only=True)
    # 班级信息
    class_name = serializers.CharField(source='student.school_class.name', read_only=True)
    college_name = serializers.CharField(source='student.school_class.major.college.name', read_only=True)
    major_name = serializers.CharField(source='student.school_class.major.name', read_only=True)
    # 状态显示
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_id', 'student_name',
            'schedule', 'schedule_id', 'course_name', 'course_id',
            'date', 'status', 'status_display', 'remark',
            'class_name', 'college_name', 'major_name'
        ]
        read_only_fields = ['status_display', 'student_id', 'student_name', 'course_name', 'course_id', 
                           'schedule_id', 'class_name', 'college_name', 'major_name']
    
    def get_student_name(self, obj):
        """获取学生姓名"""
        if obj.student and obj.student.user_profile:
            user = obj.student.user_profile.user
            return user.first_name or user.username
        return '-'
