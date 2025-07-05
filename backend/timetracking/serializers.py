from rest_framework import serializers
from .models import TimeLog, AppUsage, ActivityMetric
from projects.models import Project # Import Project model if linked

class TimeLogSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username') # To display username
    project_name = serializers.ReadOnlyField(source='project.name') # To display project name

    class Meta:
        model = TimeLog
        fields = ['id', 'user', 'user_username', 'start_time', 'end_time', 'activity_description', 'project', 'project_name', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at'] # User should be set automatically by view

class AppUsageSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = AppUsage
        fields = ['id', 'user', 'user_username', 'app_name', 'duration_seconds', 'timestamp']
        read_only_fields = ['user']

class ActivityMetricSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = ActivityMetric
        fields = ['id', 'user', 'user_username', 'metric_type', 'value', 'timestamp']
        read_only_fields = ['user']
