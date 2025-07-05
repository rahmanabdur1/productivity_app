from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views as authtoken_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include DRF's login/logout for browsable API (optional, but useful for testing)
    path('api-auth/', include('rest_framework.urls')),
    # API endpoints for your apps
    path('api/users/', include('users.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/timetracking/', include('timetracking.urls')),
]
