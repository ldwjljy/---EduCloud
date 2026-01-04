from rest_framework import serializers
from .models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    created_by_role = serializers.SerializerMethodField()
    def validate_scope(self, value):
        if value not in ('all', 'role'):
            raise serializers.ValidationError('公告范围仅支持全校或教师范围')
        return value

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
    class Meta:
        model = Notice
        fields = ['id', 'title', 'content', 'scope', 'created_by', 'created_by_name', 'created_by_role', 'created_at']
