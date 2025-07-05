from rest_framework import serializers
from .models import Team, Project
from users.models import User # Import User for related fields

class TeamSerializer(serializers.ModelSerializer):
    head_username = serializers.ReadOnlyField(source='head.username')
    # Use SlugRelatedField to display usernames of members, or PrimaryKeyRelatedField
    members = serializers.SlugRelatedField(
        many=True,
        slug_field='username',
        queryset=User.objects.all(), # Ensure queryset is provided for writable fields
        required=False # Members are optional during team creation/update
    )

    class Meta:
        model = Team
        fields = ['id', 'name', 'head', 'head_username', 'members']

class ProjectSerializer(serializers.ModelSerializer):
    manager_username = serializers.ReadOnlyField(source='manager.username')
    team_name = serializers.ReadOnlyField(source='team.name')

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'manager', 'manager_username', 'team', 'team_name', 'estimated_hours', 'start_date', 'end_date', 'status']
