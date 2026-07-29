from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from . import services
from .models import Address
from .permissions import IsOwner
from .serializers import (
    AddressSerializer,
    LogoutSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    UserSerializer,
)
from .throttles import OTPRequestEmailThrottle, OTPRequestThrottle, OTPVerifyThrottle

User = get_user_model()


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh["is_staff"] = user.is_staff
    refresh["email"] = user.email
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }

class RequestOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPRequestThrottle, OTPRequestEmailThrottle]

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        services.request_otp(email, request_ip=_client_ip(request))

        return Response(
            {"detail": "If that email is valid, a login code has been sent."},
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        services.verify_otp(email, code)

        user, created = User.objects.get_or_create_for_otp_login(email)
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])

        data = _tokens_for_user(user)
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid or already-blacklisted refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AddressViewSet(viewsets.ModelViewSet):
    """
    /api/auth/addresses/ and /api/auth/addresses/{id}/

    Ownership is enforced twice on purpose: get_queryset() ensures a user
    can never *list* another user's address, and IsOwner ensures they can't
    reach one directly either by guessing/incrementing an id in the URL.
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
