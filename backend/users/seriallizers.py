from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password # For hashing passwords

class UserSerializer(serializers.ModelSerializer):
    # Add a role field for display, derived from the model's property
    role = serializers.CharField(source='role', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'role', 'groups']
        read_only_fields = ['is_staff', 'is_active'] # These are usually managed by admin
        extra_kwargs = {'password': {'write_only': True, 'required': False}} # Password is write-only and optional for updates

    def update(self, instance, validated_data):
        # Handle password update separately if provided
        if 'password' in validated_data:
            instance.password = make_password(validated_data.pop('password'))
        return super().update(instance, validated_data)

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        # Hash the password before creating the user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user
