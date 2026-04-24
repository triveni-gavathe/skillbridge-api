from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.conf import settings

from users.models import User
from users.serializers import (
    SignupSerializer, LoginSerializer, UserSerializer,
    ChangePasswordSerializer, MonitoringTokenSerializer
)
from users.authentication import generate_token
from users.permissions import IsMonitoringOfficer


# POST /auth/signup
class SignupView(CreateAPIView):
    """
    CreateAPIView handles:
    - reading request.data
    - calling serializer.is_valid() → returns 422 automatically if invalid
    - calling serializer.save() → calls our custom create()
    We only override create() to add the token to the response.
    """
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = generate_token(user)
        return Response({
            'token': token,
            'user': UserSerializer(user).data,
        }, status=201)


# POST /auth/login
class LoginView(APIView):
    """
    APIView is correct here — login is an action, not a model operation.
    No generic view maps cleanly to this behavior.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # returns 400 if invalid

        user = authenticate(
            request,
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if not user:
            return Response(
                {'error': 'Invalid email or password.'},
                status=401
            )

        token = generate_token(user)
        return Response({
            'token': token,
            'user': UserSerializer(user).data,
        })


# POST /auth/monitoring-token
class MonitoringTokenView(APIView):
    """
    Monitoring officer exchanges their standard token + API key
    for a short-lived scoped token.
    APIView is correct — this is a custom action, not a model operation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'monitoring_officer':
            return Response({'error': 'Only monitoring officers can access this.'}, status=403)

        serializer = MonitoringTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data['key'] != settings.MONITORING_API_KEY:
            return Response({'error': 'Invalid API key.'}, status=401)

        token = generate_token(request.user, token_type='monitoring')
        return Response({
            'monitoring_token': token,
            'expires_in': '1 hour',
            'scope': 'read-only monitoring endpoints only',
        })


# GET /auth/me — get your own profile
class MeView(RetrieveUpdateAPIView):
    """
    RetrieveUpdateAPIView handles GET and PATCH/PUT automatically.
    get_object() tells it which object to retrieve — always the logged-in user.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Prevent role and password from being changed via this endpoint
        data = request.data.copy()
        data.pop('role', None)
        data.pop('password', None)
        serializer = self.get_serializer(
            self.get_object(), data=data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# POST /auth/change-password
class ChangePasswordView(APIView):
    """Plain APIView — password change is a custom action, not a model create."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Old password is incorrect.'}, status=400)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully.'})


# GET /users — list all users (admin/programme_manager use)
class UserListView(ListAPIView):
    """
    ListAPIView handles pagination, queryset, serializer automatically.
    We just define what to list and who can see it.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Programme manager sees everyone
        if user.role == 'programme_manager':
            return User.objects.all().order_by('role', 'name')
        # Institution sees only their own members
        if user.role == 'institution':
            return User.objects.filter(institution=user.institution).order_by('role', 'name')
        # Others can only see themselves
        return User.objects.filter(id=user.id)