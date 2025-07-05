from django.db import models
from users.models import User # Assuming User model is in users app

class Team(models.Model):
    name = models.CharField(max_length=255, unique=True)
    head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_teams')
    members = models.ManyToManyField(User, related_name='teams', blank=True) # Members can be many users

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    estimated_hours = models.FloatField(default=0.0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, default='Planning') # e.g., 'Planning', 'In Progress', 'Completed', 'On Hold'

    def __str__(self):
        return self.name
