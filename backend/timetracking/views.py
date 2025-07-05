from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F, ExpressionWrapper, fields
from datetime import datetime, timedelta
import random

from .models import TimeLog, AppUsage, ActivityMetric
from .serializers import TimeLogSerializer, AppUsageSerializer, ActivityMetricSerializer
from users.models import User # For filtering by team/project manager roles

class IsOwnerOrAdminOrTeamHeadOrProjectManager(permissions.BasePermission):
    """
    Custom permission to allow:
    - Admin: Full access.
    - Owner: Full access to their own objects.
    - Team Head: Read-only access to objects of their team members.
    - Project Manager: Read-only access to objects related to their managed projects.
    """
    def has_object_permission(self, request, view, obj):
        # Allow read permissions for anyone if it's a safe method (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            # Admins have full read access
            if request.user.is_superuser:
                return True
            # Owners can read their own objects
            if obj.user == request.user:
                return True
            # Team Heads can read logs of their team members
            if request.user.groups.filter(name='TeamHeads').exists():
                if obj.user.teams.filter(head=request.user).exists():
                    return True
            # Project Managers can read logs related to their managed projects
            if request.user.groups.filter(name='ProjectManagers').exists():
                if hasattr(obj, 'project') and obj.project and obj.project.manager == request.user:
                    return True
            return False # Deny if not owner, admin, team head (for their team), or PM (for their project)
        
        # Write permissions (POST, PUT, PATCH, DELETE) only for owner or admin
        return obj.user == request.user or request.user.is_superuser

class TimeLogViewSet(viewsets.ModelViewSet):
    queryset = TimeLog.objects.all().order_by('-start_time')
    serializer_class = TimeLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOrTeamHeadOrProjectManager]

    def get_queryset(self):
        """
        Filter queryset based on user role:
        - Admin: All time logs.
        - Team Head: Time logs of their team members.
        - Project Manager: Time logs related to projects they manage.
        - Employee: Only their own time logs.
        """
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        elif user.groups.filter(name='TeamHeads').exists():
            # Get IDs of users in teams led by this team head
            team_member_ids = User.objects.filter(teams__head=user).values_list('id', flat=True)
            return self.queryset.filter(user__id__in=team_member_ids)
        elif user.groups.filter(name='ProjectManagers').exists():
            # Get IDs of projects managed by this project manager
            managed_project_ids = user.managed_projects.values_list('id', flat=True)
            return self.queryset.filter(project__id__in=managed_project_ids)
        else: # Employee
            return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """
        Returns daily working hours and app usage for the requesting user.
        Can be filtered by date range (e.g., ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD)
        """
        user = request.user
        queryset = self.get_queryset().filter(user=user) # Ensure only current user's data

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            queryset = queryset.filter(start_time__date__range=[start_date, end_date])
        else:
            # Default to last 7 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
            queryset = queryset.filter(start_time__date__range=[start_date, end_date])

        # Calculate total working hours per day
        daily_hours = queryset.annotate(
            duration=ExpressionWrapper(
                F('end_time') - F('start_time'),
                output_field=fields.DurationField()
            )
        ).values('start_time__date').annotate(
            total_working_hours=Sum('duration') / timedelta(hours=1)
        ).order_by('start_time__date')

        # Calculate total app usage hours per day
        app_usage_queryset = AppUsage.objects.filter(user=user, timestamp__date__range=[start_date, end_date])
        daily_app_usage = app_usage_queryset.values('timestamp__date').annotate(
            total_app_usage_hours=Sum('duration_seconds') / 3600
        ).order_by('timestamp__date')

        # Combine results
        results = []
        date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            working_hours = next((item['total_working_hours'] for item in daily_hours if item['start_time__date'] == date), 0.0)
            app_usage_hours = next((item['total_app_usage_hours'] for item in daily_app_usage if item['timestamp__date'] == date), 0.0)
            # Simulate productivity score for now
            productivity_score = random.randint(60, 100) # Replace with actual calculation
            results.append({
                'date': date_str,
                'working_hours': round(working_hours, 2),
                'app_usage_hours': round(app_usage_hours, 2),
                'productivity_score': productivity_score
            })

        return Response(results)


class AppUsageViewSet(viewsets.ModelViewSet):
    queryset = AppUsage.objects.all().order_by('-timestamp')
    serializer_class = AppUsageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOrTeamHeadOrProjectManager]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        elif user.groups.filter(name='TeamHeads').exists():
            team_member_ids = User.objects.filter(teams__head=user).values_list('id', flat=True)
            return self.queryset.filter(user__id__in=team_member_ids)
        elif user.groups.filter(name='ProjectManagers').exists():
            managed_project_ids = user.managed_projects.values_list('id', flat=True)
            return self.queryset.filter(timelogs__project__id__in=managed_project_ids).distinct() # App usage linked via timelogs
        else: # Employee
            return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Returns summary of app usage for the requesting user/team/project.
        Can be filtered by date range.
        """
        user = request.user
        queryset = self.get_queryset() # Use filtered queryset based on role

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            queryset = queryset.filter(timestamp__date__range=[start_date, end_date])
        else:
            # Default to last 30 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=29)
            queryset = queryset.filter(timestamp__date__range=[start_date, end_date])


        app_summary = queryset.values('app_name').annotate(
            total_usage_hours=Sum('duration_seconds') / 3600
        ).order_by('-total_usage_hours')

        return Response(list(app_summary))


class ActivityMetricViewSet(viewsets.ModelViewSet):
    queryset = ActivityMetric.objects.all().order_by('-timestamp')
    serializer_class = ActivityMetricSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOrTeamHeadOrProjectManager]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.queryset
        elif user.groups.filter(name='TeamHeads').exists():
            team_member_ids = User.objects.filter(teams__head=user).values_list('id', flat=True)
            return self.queryset.filter(user__id__in=team_member_ids)
        elif user.groups.filter(name='ProjectManagers').exists():
            managed_project_ids = user.managed_projects.values_list('id', flat=True)
            return self.queryset.filter(timelogs__project__id__in=managed_project_ids).distinct()
        else: # Employee
            return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)