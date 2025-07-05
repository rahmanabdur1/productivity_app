from django.contrib import admin
from .models import TimeLog, AppUsage, ActivityMetric

@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_time', 'end_time', 'duration', 'project', 'activity_description')
    list_filter = ('user', 'project', 'start_time')
    search_fields = ('user__username', 'activity_description', 'project__name')
    date_hierarchy = 'start_time'
    readonly_fields = ('created_at', 'updated_at')
    
    def duration(self, obj):
        if obj.end_time:
            duration = obj.end_time - obj.start_time
            hours = duration.total_seconds() / 3600
            return f"{hours:.2f} hours"
        return "Ongoing"
    duration.short_description = 'Duration'

@admin.register(AppUsage)
class AppUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'app_name', 'duration_seconds', 'duration_hours', 'timestamp')
    list_filter = ('user', 'app_name', 'timestamp')
    search_fields = ('user__username', 'app_name')
    date_hierarchy = 'timestamp'
    
    def duration_hours(self, obj):
        return f"{obj.duration_seconds / 3600:.2f} hours"
    duration_hours.short_description = 'Duration (Hours)'

@admin.register(ActivityMetric)
class ActivityMetricAdmin(admin.ModelAdmin):
    list_display = ('user', 'metric_type', 'value', 'timestamp')
    list_filter = ('user', 'metric_type', 'timestamp')
    search_fields = ('user__username', 'metric_type')
    date_hierarchy = 'timestamp'
