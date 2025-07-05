from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F, ExpressionWrapper, fields

from .models import Team, Project
from .serializers import TeamSerializer, ProjectSerializer
from users.models import User # For filtering based on user roles

class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all().order_by('name')
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated] # Base permission

    def get_permissions(self):
        """
        Only Admins and Team Heads can create/update/delete teams.
        All authenticated users can list/retrieve.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser | permissions.DjangoObjectPermissions] # Or custom permission for TeamHeads
            # A more robust way would be to check if request.user is a TeamHead
            # self.permission_classes = [permissions.IsAdminUser | IsTeamHead]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        elif user.groups.filter(name='TeamHeads').exists():
            # Team heads can see their own team and its members
            return self.queryset.filter(head=user) | self.queryset.filter(members=user).distinct()
        elif user.groups.filter(name='ProjectManagers').exists():
            # Project managers can see teams associated with their projects
            managed_project_teams = user.managed_projects.values_list('team__id', flat=True)
            return self.queryset.filter(id__in=managed_project_teams).distinct()
        else: # Employee
            # Employees can see teams they are a member of
            return self.queryset.filter(members=user).distinct()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('name')
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated] # Base permission

    def get_permissions(self):
        """
        Only Admins and Project Managers can create/update/delete projects.
        All authenticated users can list/retrieve.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser | permissions.DjangoObjectPermissions] # Or custom permission for ProjectManagers
            # self.permission_classes = [permissions.IsAdminUser | IsProjectManager]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        elif user.groups.filter(name='ProjectManagers').exists():
            # Project managers can see projects they manage
            return self.queryset.filter(manager=user)
        elif user.groups.filter(name='TeamHeads').exists():
            # Team heads can see projects associated with their teams
            led_team_projects = user.led_teams.values_list('projects__id', flat=True)
            return self.queryset.filter(id__in=led_team_projects).distinct()
        else: # Employee
            # Employees can see projects they have time logs for
            return self.queryset.filter(time_logs__user=user).distinct()

    @action(detail=True, methods=['get'])
    def progress_report(self, request, pk=None):
        """
        Returns progress report for a specific project.
        Calculates total time spent and compares to estimated hours.
        """
        project = self.get_object()
        total_time_spent_seconds = project.time_logs.aggregate(
            total_duration=Sum(
                ExpressionWrapper(
                    F('end_time') - F('start_time'),
                    output_field=fields.DurationField()
                )
            )
        )['total_duration']

        total_time_spent_hours = total_time_spent_seconds.total_seconds() / 3600 if total_time_spent_seconds else 0

        progress_percentage = (total_time_spent_hours / project.estimated_hours) * 100 if project.estimated_hours > 0 else 0

        return Response({
            'project_id': project.id,
            'project_name': project.name,
            'estimated_hours': project.estimated_hours,
            'total_time_spent_hours': round(total_time_spent_hours, 2),
            'progress_percentage': round(progress_percentage, 2),
            'status': project.status,
        })