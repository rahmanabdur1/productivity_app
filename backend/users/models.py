from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    # You can add custom fields here if needed, but for roles,
    # Django's built-in Group system is often more flexible.
    # For example:
    # phone_number = models.CharField(max_length=20, blank=True, null=True)

    # You can define a property to easily get the user's primary role
    @property
    def role(self):
        if self.is_superuser:
            return 'admin'
        if self.groups.filter(name='TeamHeads').exists():
            return 'team_head'
        if self.groups.filter(name='ProjectManagers').exists():
            return 'project_manager'
        return 'employee' # Default role


# Signal to create default groups if they don't exist
@receiver(post_save, sender=User)
def create_default_groups(sender, instance, created, **kwargs):
    if created:
        Group.objects.get_or_create(name='Employees')
        Group.objects.get_or_create(name='TeamHeads')
        Group.objects.get_or_create(name='ProjectManagers')

        # Assign new users to the 'Employees' group by default
        employee_group, _ = Group.objects.get_or_create(name='Employees')
        instance.groups.add(employee_group)

