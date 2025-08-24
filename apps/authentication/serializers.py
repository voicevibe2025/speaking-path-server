"""
Authentication serializers for VoiceVibe
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User
from apps.users.models import UserProfile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user data
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['email'] = user.email
        token['username'] = user.username
        token['is_verified'] = user.is_verified

        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    native_language = serializers.CharField(write_only=True, required=False, allow_blank=True)
    target_language = serializers.CharField(write_only=True, required=False, allow_blank=True)
    proficiency_level = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'password',
            'password_confirm', 'first_name', 'last_name',
            'native_language', 'target_language', 'proficiency_level'
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def create(self, validated_data):
        # Pop optional profile fields first so they aren't passed to create_user
        native_language = validated_data.pop('native_language', None)
        target_language = validated_data.pop('target_language', None)
        proficiency_level = validated_data.pop('proficiency_level', None)
        validated_data.pop('password_confirm')
        # If username not provided, derive from email (fallback to email itself)
        username = validated_data.get('username')
        if not username:
            email = validated_data.get('email', '')
            derived = email or (validated_data.get('first_name', '') + validated_data.get('last_name', ''))
            # Ensure max length similar to Django's username max_length (150)
            validated_data['username'] = (derived or 'user')[:150]
        user = User.objects.create_user(**validated_data)

        # Optionally create a UserProfile if any related fields were provided
        try:
            if native_language or target_language or proficiency_level:
                def _lang_code(v):
                    if not v:
                        return None
                    v = v.strip().lower()
                    mapping = {'indonesian': 'id', 'english': 'en', 'id': 'id', 'en': 'en'}
                    return mapping.get(v, (v[:2] if len(v) >= 2 else 'en'))

                def _prof(v):
                    if not v:
                        return None
                    v = v.strip().lower()
                    mapping = {
                        'a1': 'beginner', 'a2': 'elementary',
                        'b1': 'intermediate', 'b2': 'upper_intermediate',
                        'c1': 'advanced', 'c2': 'proficient'
                    }
                    return mapping.get(v, v)

                UserProfile.objects.create(
                    user=user,
                    native_language=_lang_code(native_language) or 'id',
                    target_language=_lang_code(target_language) or 'en',
                    current_proficiency=_prof(proficiency_level) or 'beginner'
                )
        except Exception:
            # Profile creation is best-effort; ignore failures to not block registration
            pass

        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,  # Using email as username
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Unable to authenticate with provided credentials.',
                    code='authentication'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='disabled'
                )
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='required'
            )

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details
    """
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_active', 'is_verified', 'date_joined'
        )
        read_only_fields = ('id', 'email', 'is_active', 'is_verified', 'date_joined')
