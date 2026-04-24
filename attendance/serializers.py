from rest_framework import serializers
from attendance.models import Batch, Session, Attendance, BatchInvite, Institution


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ['id', 'name', 'institution', 'created_at']
        read_only_fields = ['created_at']


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'batch', 'trainer', 'title', 'date', 'start_time', 'end_time', 'created_at']
        read_only_fields = ['trainer', 'created_at']  # trainer set from request.user


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'session', 'student', 'status', 'marked_at']
        read_only_fields = ['student', 'marked_at']  # student set from request.user


class BatchInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchInvite
        fields = ['id', 'batch', 'token', 'expires_at', 'used', 'created_by']
        read_only_fields = ['token', 'expires_at', 'used', 'created_by']