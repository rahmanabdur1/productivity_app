from django.test import TestCase
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import date
from .models import Team, Project
from users.models import User

class TeamModelTest(TestCase):
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

    def test_team_creation(self):
        self.assertEqual(self.team.name, 'Test Team')
        self.assertEqual(self.team.head, self.user)
        self.assertEqual(str(self.team), 'Test Team')

    def test_team_members(self):
        member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='memberpass123'
        )
        self.team.members.add(member)
        self.assertIn(member, self.team.members.all())

class ProjectModelTest(TestCase):
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
            description='A test project',
            manager=self.user,
            team=self.team,
            estimated_hours=40.0,
            start_date=date.today(),
            status='Planning'
        )

    def test_project_creation(self):
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.manager, self.user)
        self.assertEqual(self.project.team, self.team)
        self.assertEqual(self.project.estimated_hours, 40.0)
        self.assertEqual(str(self.project), 'Test Project')

class ProjectSerializerTest(TestCase):
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
            description='A test project',
            manager=self.user,
            team=self.team,
            estimated_hours=40.0
        )

    def test_team_serializer(self):
        from .serializers import TeamSerializer
        serializer = TeamSerializer(self.team)
        data = serializer.data
        self.assertEqual(data['name'], 'Test Team')
        self.assertEqual(data['head_username'], 'testuser')

    def test_project_serializer(self):
        from .serializers import ProjectSerializer
        serializer = ProjectSerializer(self.project)
        data = serializer.data
        self.assertEqual(data['name'], 'Test Project')
        self.assertEqual(data['manager_username'], 'testuser')
        self.assertEqual(data['team_name'], 'Test Team')

class ProjectAPITest(APITestCase):
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
        self.team = Team.objects.create(
            name='Test Team',
            head=self.user
        )
        self.project = Project.objects.create(
            name='Test Project',
            description='A test project',
            manager=self.user,
            team=self.team,
            estimated_hours=40.0
        )

    def test_team_list(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('team-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_list(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_detail(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('project-detail', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Project')

    def test_project_progress_report(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('project-progress-report', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('project_id', response.data)
        self.assertIn('progress_percentage', response.data)
