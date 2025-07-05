from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from users.models import User
from projects.models import Team, Project
from timetracking.models import TimeLog, AppUsage, ActivityMetric
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Set up initial data for the productivity app'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create groups
        self.create_groups()
        
        # Create users
        self.create_users()
        
        # Create teams and projects
        self.create_teams_and_projects()
        
        # Create sample time tracking data
        self.create_sample_timetracking_data()
        
        self.stdout.write(self.style.SUCCESS('Initial data setup completed successfully!'))

    def create_groups(self):
        groups = ['Employees', 'TeamHeads', 'ProjectManagers']
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'Created group: {group_name}')

    def create_users(self):
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@productivity.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created admin user: admin (password: admin123)')

        # Create team head
        team_head, created = User.objects.get_or_create(
            username='teamhead',
            defaults={
                'email': 'teamhead@productivity.com',
                'first_name': 'Team',
                'last_name': 'Head'
            }
        )
        if created:
            team_head.set_password('teamhead123')
            team_head.save()
            team_head_group = Group.objects.get(name='TeamHeads')
            team_head.groups.add(team_head_group)
            self.stdout.write('Created team head: teamhead (password: teamhead123)')

        # Create project manager
        project_manager, created = User.objects.get_or_create(
            username='projectmanager',
            defaults={
                'email': 'pm@productivity.com',
                'first_name': 'Project',
                'last_name': 'Manager'
            }
        )
        if created:
            project_manager.set_password('pm123')
            project_manager.save()
            pm_group = Group.objects.get(name='ProjectManagers')
            project_manager.groups.add(pm_group)
            self.stdout.write('Created project manager: projectmanager (password: pm123)')

        # Create employees
        employees_data = [
            {'username': 'employee1', 'email': 'emp1@productivity.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'employee2', 'email': 'emp2@productivity.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'employee3', 'email': 'emp3@productivity.com', 'first_name': 'Bob', 'last_name': 'Johnson'},
        ]
        
        employee_group = Group.objects.get(name='Employees')
        for emp_data in employees_data:
            employee, created = User.objects.get_or_create(
                username=emp_data['username'],
                defaults={
                    'email': emp_data['email'],
                    'first_name': emp_data['first_name'],
                    'last_name': emp_data['last_name']
                }
            )
            if created:
                employee.set_password('employee123')
                employee.save()
                employee.groups.add(employee_group)
                self.stdout.write(f'Created employee: {emp_data["username"]} (password: employee123)')

    def create_teams_and_projects(self):
        # Get users
        team_head = User.objects.get(username='teamhead')
        project_manager = User.objects.get(username='projectmanager')
        employees = User.objects.filter(groups__name='Employees')

        # Create team
        team, created = Team.objects.get_or_create(
            name='Development Team',
            defaults={'head': team_head}
        )
        if created:
            team.members.add(*employees)
            self.stdout.write('Created team: Development Team')

        # Create projects
        projects_data = [
            {
                'name': 'Website Redesign',
                'description': 'Redesign the company website with modern UI/UX',
                'manager': project_manager,
                'team': team,
                'estimated_hours': 80.0,
                'status': 'In Progress'
            },
            {
                'name': 'Mobile App Development',
                'description': 'Develop a mobile app for iOS and Android',
                'manager': project_manager,
                'team': team,
                'estimated_hours': 120.0,
                'status': 'Planning'
            }
        ]

        for project_data in projects_data:
            project, created = Project.objects.get_or_create(
                name=project_data['name'],
                defaults=project_data
            )
            if created:
                self.stdout.write(f'Created project: {project_data["name"]}')

    def create_sample_timetracking_data(self):
        users = User.objects.filter(groups__name='Employees')
        projects = Project.objects.all()
        
        # Create sample time logs for the last 7 days
        for user in users:
            for i in range(7):
                date = datetime.now().date() - timedelta(days=i)
                
                # Create 1-2 time logs per day
                for j in range(random.randint(1, 2)):
                    start_time = datetime.combine(date, datetime.min.time()) + timedelta(hours=9 + j * 4)
                    end_time = start_time + timedelta(hours=random.randint(2, 4))
                    
                    TimeLog.objects.create(
                        user=user,
                        start_time=start_time,
                        end_time=end_time,
                        activity_description=f'Sample activity {j+1}',
                        project=random.choice(projects) if projects.exists() else None
                    )

                # Create app usage data
                apps = ['VS Code', 'Chrome', 'Slack', 'Email', 'Terminal']
                for app in random.sample(apps, random.randint(2, 4)):
                    AppUsage.objects.create(
                        user=user,
                        app_name=app,
                        duration_seconds=random.randint(1800, 7200),  # 30 min to 2 hours
                        timestamp=datetime.combine(date, datetime.min.time()) + timedelta(hours=random.randint(9, 17))
                    )

                # Create activity metrics
                ActivityMetric.objects.create(
                    user=user,
                    metric_type='keyboard_strokes',
                    value=random.randint(500, 2000),
                    timestamp=datetime.combine(date, datetime.min.time()) + timedelta(hours=random.randint(9, 17))
                )

        self.stdout.write('Created sample time tracking data for the last 7 days') 