from rest_framework import serializers
from .models import ContactInquiry


class ContactInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInquiry
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "subject",
            "inquiry_type",
            "message",
            "timeframe",
            "attachment_url",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def validate_email(self, value):
        if not value or "@" not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value.strip().lower()


class NewsletterSubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not value or "@" not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value.strip().lower()

