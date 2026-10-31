from django.urls import path
from .views import ContactInquiryCreateView, NewsletterSubscribeView

app_name = "contacts"

urlpatterns = [
    path("", ContactInquiryCreateView.as_view(), name="contact-create"),
    path("inquire/", ContactInquiryCreateView.as_view(), name="contact-inquire"),
    path("newsletter/", NewsletterSubscribeView.as_view(), name="newsletter-subscribe"),
]

