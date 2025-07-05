from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomAuthToken

router = DefaultRouter()
router.register(r'', UserViewSet)

urlpatterns = [
    path('auth/', CustomAuthToken.as_view(), name='auth_token'),
    path('', include(router.urls)),
] 