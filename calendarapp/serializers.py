from rest_framework import serializers
from .models import CalendarEvent


class CalendarEventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    created_by_role = serializers.SerializerMethodField()
    college_name = serializers.SerializerMethodField()
    def validate(self, attrs):
        vis = attrs.get('visibility')
        col = attrs.get('college')
        if vis == 'college' and not col:
            raise serializers.ValidationError('学院范围必须选择学院')
        return attrs
    def get_created_by_name(self, obj):
        try:
            return getattr(obj.created_by, 'username', '')
        except Exception:
            return ''

    def get_created_by_role(self, obj):
        try:
            return getattr(getattr(obj.created_by, 'profile', None), 'role', '')
        except Exception:
            return ''

    def get_college_name(self, obj):
        try:
            return getattr(obj.college, 'name', '')
        except Exception:
            return ''

    class Meta:
        model = CalendarEvent
        fields = ['id', 'title', 'description', 'event_type', 'visibility', 'college', 'college_name', 'start_time', 'end_time', 'created_by', 'created_by_name', 'created_by_role', 'remind_minutes_before']
