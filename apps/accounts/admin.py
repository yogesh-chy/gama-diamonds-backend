from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Address, EmailOTP, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-created_at",)
    list_display = ("email", "phone_number", "is_staff", "is_active", "is_email_verified", "created_at")
    list_filter = ("is_staff", "is_active", "is_email_verified")
    search_fields = ("email", "phone_number")
    readonly_fields = ("created_at", "updated_at", "last_login", "is_email_verified")

    # Shopper accounts are created via OTP verification and never have a
    # usable password (accounts/managers.py get_or_create_for_otp_login),
    # so the password field here is really only exercised for
    # `createsuperuser`/staff accounts — it's kept for that reason.
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("phone_number",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active", "is_staff", "is_superuser",
                    "groups", "user_permissions",
                )
            },
        ),
        ("Login", {"fields": ("is_email_verified",)}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    """
    Read-only by design — this table exists for abuse investigation
    (accounts/models.py EmailOTP docstring), not for admin edits. Codes are
    never shown: only the hash is stored, and even that isn't displayed
    here, since there's no legitimate admin workflow that needs it.
    """
    list_display = ("email", "purpose", "attempts", "is_used", "request_ip", "created_at", "expires_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("email", "request_ip")
    readonly_fields = (
        "email", "purpose", "attempts", "is_used", "request_ip",
        "created_at", "expires_at", "consumed_at",
    )
    exclude = ("code_hash",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "city", "country", "is_default")
    list_filter = ("is_default", "country")
    search_fields = ("full_name", "user__email", "city", "postal_code")
