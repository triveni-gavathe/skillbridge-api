import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.models import User


def generate_token(user, token_type='standard'):
    """Create a JWT for a user."""
    expiry_hours = 1 if token_type == 'monitoring' else 24
    payload = {
        'user_id': user.id,
        'role': user.role,
        'token_type': token_type,    # 'standard' or 'monitoring'
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')


def decode_token(token):
    """Decode and validate a JWT. Returns payload dict."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed('Token has expired.')
    except jwt.InvalidTokenError:
        raise AuthenticationFailed('Invalid token.')


class JWTAuthentication(BaseAuthentication):
    """DRF authentication class — reads Bearer token from Authorization header."""

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None   # No token — let permission class handle it

        token = auth_header.split(' ')[1]
        payload = decode_token(token)

        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')

        # Attach token_type to request so views can inspect it
        request.token_type = payload.get('token_type', 'standard')
        return (user, token)