import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from .models import ContactInquiry
from .serializers import ContactInquirySerializer, NewsletterSubscribeSerializer
from .services import send_contact_inquiry_emails

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class ContactInquiryCreateView(APIView):
    """
    Submits a contact inquiry, bespoke request, consultation request,
    or general thoughts/feedback from users.
    Sends instant email alerts to Gama Jewels administration.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = ContactInquirySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inquiry = serializer.save(ip_address=_get_client_ip(request))

        # Send alert emails asynchronously or synchronously with safe error catch
        try:
            send_contact_inquiry_emails(inquiry)
        except Exception as e:
            logger.error("Error triggering inquiry email notification: %s", e)

        return Response(
            {
                "success": True,
                "message": "Thank you! Your message has been received. Our diamond concierge will reach out to you shortly.",
                "id": inquiry.id,
            },
            status=status.HTTP_201_CREATED,
        )


class NewsletterSubscribeView(APIView):
    """
    Handles Private Circle newsletter subscriptions from the footer
    and sends notification alert to admin.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = NewsletterSubscribeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]

        # Save to ContactInquiry table with type 'newsletter'
        inquiry = ContactInquiry.objects.create(
            email=email,
            inquiry_type="newsletter",
            subject="Private Circle Newsletter Subscription",
            message="User subscribed to Private Circle newsletter from website footer.",
            ip_address=_get_client_ip(request),
        )

        try:
            send_contact_inquiry_emails(inquiry)
        except Exception as e:
            logger.error("Error triggering newsletter email notification: %s", e)

        return Response(
            {
                "success": True,
                "message": "Welcome to the Private Circle. You have been successfully subscribed.",
            },
            status=status.HTTP_201_CREATED,
        )

