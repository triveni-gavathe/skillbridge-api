from rest_framework import serializers
from users.models import User
from attendance.models import Institution


class UserSerializer(serializers.ModelSerializer):
    """Used for reading user data — never exposes password."""
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role', 'institution', 'created_at']
        read_only_fields = ['id', 'created_at']


class SignupSerializer(serializers.ModelSerializer):
    """Used for creating a new user."""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'role', 'institution']
        read_only_fields = ['id']

    def validate_role(self, value):
        """Anyone can signup as these roles. 
        Monitoring officer should be created by admin only."""
        allowed = ['student', 'trainer', 'institution', 'programme_manager', 'monitoring_officer']
        if value not in allowed:
            raise serializers.ValidationError(f'Role must be one of: {allowed}')
        return value

    def validate_email(self, value):
        """Check email is not already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        # Use our custom manager so password gets hashed properly
        return User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            role=validated_data['role'],
            institution=validated_data.get('institution'),
        )


class LoginSerializer(serializers.Serializer):
    """Plain Serializer here is correct — Login does not map to a model."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('Email is required.')
        return value

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError('Password is required.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Plain Serializer — no model needed, just two fields."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)


class MonitoringTokenSerializer(serializers.Serializer):
    """Validates the API key submission for monitoring officer."""
    key = serializers.CharField()

    def validate_key(self, value):
        if not value:
            raise serializers.ValidationError('API key is required.')
        return value