from django.test import TestCase
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta
from .models import TimeLog, AppUsage, ActivityMetric
from users.models import User
from projects.models import Project, Team

class TimeLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.team = Team.objects.create(
            name='Test Team',
            head=self.user
        )
        self.project = Project.objects.create(
            name='Test Project',
            manager=self.user,
            team=self.team
        )
        self.timelog = TimeLog.objects.create(
            user=self.user,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=2),
            activity_description='Test activity',
            project=self.project
        )

    def test_timelog_creation(self):
        self.assertEqual(self.timelog.user, self.user)
        self.assertEqual(self.timelog.activity_description, 'Test activity')
        self.assertEqual(self.timelog.project, self.project)
        self.assertTrue(self.timelog.start_time < self.timelog.end_time)

    def test_timelog_duration(self):
        duration = self.timelog.end_time - self.timelog.start_time
        self.assertEqual(duration.total_seconds(), 7200)  # 2 hours

class AppUsageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.app_usage = AppUsage.objects.create(
            user=self.user,
            app_name='Test App',
            duration_seconds=3600,
            timestamp=datetime.now()
        )

    def test_app_usage_creation(self):
        self.assertEqual(self.app_usage.user, self.user)
        self.assertEqual(self.app_usage.app_name, 'Test App')
        self.assertEqual(self.app_usage.duration_seconds, 3600)
        self.assertEqual(str(self.app_usage), f'{self.user.username} - Test App (3600s) at {self.app_usage.timestamp}')

class ActivityMetricModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.metric = ActivityMetric.objects.create(
            user=self.user,
            metric_type='keyboard_strokes',
            value=1000.0,
            timestamp=datetime.now()
        )

    def test_activity_metric_creation(self):
        self.assertEqual(self.metric.user, self.user)
        self.assertEqual(self.metric.metric_type, 'keyboard_strokes')
        self.assertEqual(self.metric.value, 1000.0)
        self.assertEqual(str(self.metric), f'{self.user.username} - keyboard_strokes: 1000.0 at {self.metric.timestamp}')

class TimetrackingSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.timelog = TimeLog.objects.create(
            user=self.user,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            activity_description='Test activity'
        )

    def test_timelog_serializer(self):
        from .serializers import TimeLogSerializer
        serializer = TimeLogSerializer(self.timelog)
        data = serializer.data
        self.assertEqual(data['user_username'], 'testuser')
        self.assertEqual(data['activity_description'], 'Test activity')

class TimetrackingAPITest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.timelog = TimeLog.objects.create(
            user=self.user,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            activity_description='Test activity'
        )

    def test_timelog_list(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('timelog-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_timelog_detail(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('timelog-detail', args=[self.timelog.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['activity_description'], 'Test activity')

    def test_timelog_create(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('timelog-list')
        data = {
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(hours=1)).isoformat(),
            'activity_description': 'New activity'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_daily_summary(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('timelog-daily-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
