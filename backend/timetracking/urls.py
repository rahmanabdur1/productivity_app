from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TimeLogViewSet, AppUsageViewSet, ActivityMetricViewSet

router = DefaultRouter()
router.register(r'timelogs', TimeLogViewSet)
router.register(r'appusages', AppUsageViewSet)
router.register(r'activitymetrics', ActivityMetricViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 