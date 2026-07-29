from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Address, EmailOTP

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Used for /me/ and embedded in the OTP-verify response."""

    class Meta:
        model = User
        fields = ("id", "email", "phone_number", "is_staff", "is_email_verified", "created_at")
        read_only_fields = ("id", "email", "is_staff", "is_email_verified", "created_at")


class OTPRequestSerializer(serializers.Serializer):
    """POST /api/auth/otp/request/ — the only input needed to start login."""

    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class OTPVerifySerializer(serializers.Serializer):
    """
    POST /api/auth/otp/verify/ — completes login (and, for a first-time
    email, signup) once the code from the OTP email is supplied.
    """

    email = serializers.EmailField()
    code = serializers.CharField(min_length=4, max_length=8, trim_whitespace=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Code must be numeric.")
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "id", "full_name", "phone_number", "street_address",
            "city", "state", "postal_code", "country", "is_default",
        )
        read_only_fields = ("id",)
