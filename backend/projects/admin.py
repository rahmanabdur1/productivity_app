from django.contrib import admin
from .models import Team, Project

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'head', 'member_count')
    list_filter = ('head',)
    search_fields = ('name', 'head__username', 'head__email')
    filter_horizontal = ('members',)
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Number of Members'

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'team', 'status', 'estimated_hours', 'start_date', 'end_date')
    list_filter = ('status', 'team', 'manager')
    search_fields = ('name', 'description', 'manager__username', 'team__name')
    date_hierarchy = 'start_date'
