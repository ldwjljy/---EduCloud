from rest_framework import serializers
from .models import Grade
from accounts.models import StudentProfile
from courses.models import Course


class GradeSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    student_name = serializers.CharField(source='student.user_profile.user.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.user_profile.user.username', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_type = serializers.CharField(source='course.get_course_type_display', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    class_name = serializers.CharField(source='student.school_class.name', read_only=True)
    class_id = serializers.CharField(source='student.school_class.class_id', read_only=True)
    major_name = serializers.CharField(source='student.school_class.major.name', read_only=True)
    college_name = serializers.CharField(source='student.school_class.major.college.name', read_only=True)
    is_passed = serializers.SerializerMethodField()
    
    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_id', 'student_name', 'student_username',
            'course', 'course_name', 'course_type',
            'teacher_name', 'class_name', 'class_id', 'major_name', 'college_name',
            'score', 'gpa', 'approved', 'is_passed',
            'regular_score', 'final_score', 'regular_weight', 'final_weight'
        ]
        
    def get_teacher_name(self, obj):
        if obj.course.teacher:
            return obj.course.teacher.user_profile.user.get_full_name() or obj.course.teacher.user_profile.user.username
        return '-'
    
    def get_is_passed(self, obj):
        return obj.score >= 60


class GradeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'student', 'course', 'score', 'gpa', 'approved', 
                 'regular_score', 'final_score', 'regular_weight', 'final_weight']
    
    def validate_score(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("成绩必须在0-100之间")
        return value
    
    def validate_regular_score(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("平时分必须在0-100之间")
        return value
    
    def validate_final_score(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("期末分必须在0-100之间")
        return value
    
    def validate(self, data):
        # 验证占比之和是否为100%
        regular_weight = data.get('regular_weight', 50)
        final_weight = data.get('final_weight', 50)
        if regular_weight + final_weight != 100:
            raise serializers.ValidationError("平时分占比和期末分占比之和必须等于100%")
        return data
    
    def validate_gpa(self, value):
        if value is not None and (value < 0 or value > 5):
            raise serializers.ValidationError("GPA必须在0-5之间")
        return value

    def create(self, validated_data):
        """
        创建成绩时，如果只提供了总评成绩 score 而没有提供平时分/期末分，
        则保留 score，且不依赖 regular_score/final_score 进行重新计算。
        """
        # 教师端批量录入会显式提供 regular_score/final_score，这里不做特殊处理
        grade = super().create(validated_data)
        return grade

    def update(self, instance, validated_data):
        """
        更新成绩时，区分两类场景：
        1）管理员/校长在“编辑成绩”弹窗中仅修改总分（score）
           - 前端只传 score，不传 regular_score/final_score
           - 此时认为总分是最终结果，应直接以 score 为准，并清空原有平时分/期末分，避免再次按 60/40 计算覆盖。
        2）教师端按平时分/期末分录入
           - 会同时传 regular_score/final_score，由模型的 save() 按 60/40 重新计算总分。
        """
        only_change_total_score = (
            'score' in validated_data
            and 'regular_score' not in validated_data
            and 'final_score' not in validated_data
        )

        if only_change_total_score:
            # 只改总评成绩：清空平时分和期末分，避免 save() 用旧的平时/期末分覆盖新的 score
            instance.score = validated_data['score']
            instance.regular_score = None
            instance.final_score = None
            instance.save()
            return instance

        # 其他情况（例如教师端录入 regular_score / final_score），走默认逻辑
        return super().update(instance, validated_data)


class GradeStatisticsSerializer(serializers.Serializer):
    """成绩统计序列化器"""
    level = serializers.CharField()  # college, major, class
    college_id = serializers.IntegerField(required=False)
    college_name = serializers.CharField(required=False)
    major_id = serializers.IntegerField(required=False)
    major_name = serializers.CharField(required=False)
    class_id = serializers.CharField(required=False)
    class_name = serializers.CharField(required=False)
    total_students = serializers.IntegerField()
    total_grades = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    pass_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    excellent_rate = serializers.DecimalField(max_digits=5, decimal_places=2)  # >=90
    good_rate = serializers.DecimalField(max_digits=5, decimal_places=2)  # 80-89
    passed_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
