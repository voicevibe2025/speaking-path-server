"""
Authentication views for VoiceVibe
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
import logging
import os
import firebase_admin
from firebase_admin import auth as fb_auth
from firebase_admin import credentials as fb_credentials

from .models import User, RefreshTokenBlacklist
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view with additional user data
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    User login endpoint
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        login(request, user)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    """
    Verify a Firebase ID token from Google Sign-In and return our JWTs.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'error': 'id_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize Firebase app if not already
        try:
            firebase_admin.get_app()
        except ValueError:
            try:
                cred = None
                options = {}
                # Prefer explicit service account if provided
                sa_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                if sa_path and os.path.exists(sa_path):
                    cred = fb_credentials.Certificate(sa_path)
                # Accept project id via several env vars
                project_id = (
                    os.environ.get('GOOGLE_CLOUD_PROJECT')
                    or os.environ.get('GCLOUD_PROJECT')
                    or os.environ.get('FIREBASE_PROJECT_ID')
                )
                if project_id:
                    options['projectId'] = project_id
                firebase_admin.initialize_app(cred, options or None)
            except Exception:
                logging.exception("Failed to initialize Firebase Admin")
                return Response({'error': 'Firebase initialization failed: project id/credentials missing'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            decoded = fb_auth.verify_id_token(id_token)
            email = decoded.get('email')
            uid = decoded.get('uid')
            name = decoded.get('name', '') or ''
            first_name, last_name = '', ''
            if name:
                parts = name.split(' ', 1)
                first_name = parts[0]
                if len(parts) > 1:
                    last_name = parts[1]

            if not email:
                return Response({'error': 'Email not present in token'}, status=status.HTTP_400_BAD_REQUEST)

            # Get or create the user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    email=email,
                    username=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=User.objects.make_random_password(),
                )
                user.is_verified = True
                user.save(update_fields=['is_verified'])

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserSerializer(user, context={'request': request}).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)

        except fb_auth.InvalidIdTokenError:
            return Response({'error': 'Invalid ID token'}, status=status.HTTP_400_BAD_REQUEST)
        except fb_auth.ExpiredIdTokenError:
            return Response({'error': 'Expired ID token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.exception("Google login error")
            return Response({'error': 'Google login failed'}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    User logout endpoint - blacklists the refresh token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                # Add token to blacklist
                RefreshTokenBlacklist.objects.create(
                    token=refresh_token,
                    user=request.user
                )

            logout(request)

            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update user profile
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyTokenView(APIView):
    """
    Verify if token is valid
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'valid': True,
            'user': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Request password reset email
    """
    email = request.data.get('email')

    try:
        user = User.objects.get(email=email)
        # TODO: Implement email sending with reset token
        return Response({
            'message': 'Password reset email sent'
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        # Return success even if user doesn't exist (security)
        return Response({
            'message': 'Password reset email sent'
        }, status=status.HTTP_200_OK)
