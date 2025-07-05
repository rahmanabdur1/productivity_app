from django.db import models
from users.models import User # Assuming User model is in users app

class TimeLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_logs')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    activity_description = models.TextField(blank=True, null=True)
    # Add foreign key to Project if applicable (requires projects app to be set up)
    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='time_logs')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity_description or 'No description'} ({self.start_time.date()})"

    class Meta:
        ordering = ['-start_time'] # Default ordering for time logs

class AppUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_usages')
    app_name = models.CharField(max_length=255)
    duration_seconds = models.IntegerField()
    timestamp = models.DateTimeField() # When this usage was recorded

    def __str__(self):
        return f"{self.user.username} - {self.app_name} ({self.duration_seconds}s) at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']

class ActivityMetric(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_metrics')
    metric_type = models.CharField(max_length=100) # e.g., 'keyboard_strokes', 'mouse_clicks', 'focus_score'
    value = models.FloatField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.metric_type}: {self.value} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
