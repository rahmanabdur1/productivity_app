from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth.models import Group # Import Group for role management
from .models import User
from .serializers import UserSerializer, UserCreateSerializer

class CustomAuthToken(ObtainAuthToken):
    """
    Custom authentication view to return user role along with the token.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Determine user role based on superuser status or group membership
        role = 'employee' # Default role
        if user.is_superuser:
            role = 'admin'
        elif user.groups.filter(name='TeamHeads').exists():
            role = 'team_head'
        elif user.groups.filter(name='ProjectManagers').exists():
            role = 'project_manager'

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username,
            'role': role # Send role back to frontend
        })

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Set permissions based on the action.
        - 'create': Only admins can create users (or AllowAny if public registration).
        - 'list', 'retrieve': Admins can see all, authenticated users can see their own.
        - 'update', 'partial_update', 'destroy': Only admins can modify/delete users.
        """
        if self.action == 'create':
            self.permission_classes = [IsAdminUser] # Only admins can create users
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated] # Authenticated users can view
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser] # Only admins can modify/delete
        else:
            self.permission_classes = [IsAuthenticated] # Default for other actions
        return super().get_permissions()

    def get_queryset(self):
        """
        Admins can see all users. Other authenticated users can only see their own profile.
        """
        if self.request.user.is_superuser:
            return User.objects.all().order_by('id')
        return User.objects.filter(id=self.request.user.id)

    def perform_create(self, serializer):
        # Hash password during creation
        user = serializer.save()
        user.set_password(serializer.validated_data['password'])
        user.save()

        # Assign to default 'Employees' group
        employee_group, created = Group.objects.get_or_create(name='Employees')
        user.groups.add(employee_group)


    def perform_update(self, serializer):
        # Handle role assignment via groups if 'groups' field is in validated_data
        # This requires the 'groups' field to be writable in the serializer,
        # or you can create a custom endpoint for role updates.
        # For simplicity, we'll assume admin manages groups via Django admin or a separate API.
        # If 'password' is in validated_data, it's handled by serializer's update method.
        serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Custom endpoint to retrieve the profile of the currently authenticated user.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def set_role(self, request, pk=None):
        """
        Admin endpoint to set a user's role (by adding/removing from groups).
        Expected data: {"role": "employee" | "team_head" | "project_manager" | "admin"}
        """
        user = self.get_object()
        new_role = request.data.get('role')

        if not new_role or new_role not in ['employee', 'team_head', 'project_manager', 'admin']:
            return Response({"detail": "Invalid role provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Clear existing role groups
        user.groups.clear()

        if new_role == 'admin':
            user.is_superuser = True
            user.is_staff = True
        else:
            user.is_superuser = False
            user.is_staff = False
            if new_role == 'team_head':
                group, _ = Group.objects.get_or_create(name='TeamHeads')
                user.groups.add(group)
            elif new_role == 'project_manager':
                group, _ = Group.objects.get_or_create(name='ProjectManagers')
                user.groups.add(group)
            elif new_role == 'employee':
                group, _ = Group.objects.get_or_create(name='Employees')
                user.groups.add(group)

        user.save()
        serializer = self.get_serializer(user)
        return Response(serializer.data)
