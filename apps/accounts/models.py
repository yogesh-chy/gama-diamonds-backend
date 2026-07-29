from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from .managers import UserManager


class User(AbstractUser):

    username = None  # dropped entirely — email is the login identifier
    email = models.EmailField("email address", unique=True)

    phone_regex = RegexValidator(
        regex=r"^\+?[1-9]\d{7,14}$",
        message="Enter phone number in international format, e.g. +919812345678.",
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=16, blank=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class Address(models.Model):
    user = models.ForeignKey(User, related_name="addresses", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=16)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="India")
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "addresses"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.city} ({self.user.email})"

    def save(self, *args, **kwargs):

        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)



class EmailOTP(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = "login", "Login / signup"

    email = models.EmailField(db_index=True)
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.LOGIN)
    code_hash = models.CharField(max_length=64)  # sha256 hex digest

    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    request_ip = models.GenericIPAddressField(null=True, blank=True)

    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "email_otps"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "purpose", "is_used", "-created_at"]),
        ]

    def __str__(self):
        return f"OTP({self.email}, {self.purpose}, used={self.is_used})"