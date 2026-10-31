import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape

logger = logging.getLogger(__name__)


def _get_admin_recipients():
    """Returns a list of email addresses that should receive form alert notifications."""
    recipients = []
    admin_email = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", "gama.diamond10@gmail.com")
    if admin_email:
        if isinstance(admin_email, (list, tuple)):
            recipients.extend(admin_email)
        else:
            recipients.append(str(admin_email).strip())

    # Ensure default from email or official email is also notified if distinct
    fallback_email = "gama.diamond10@gmail.com"
    if fallback_email not in recipients:
        recipients.append(fallback_email)

    return list(set(r for r in recipients if r and "@" in r))


def send_contact_inquiry_emails(inquiry) -> bool:
    """
    Sends:
    1. An alert email to the admin with full inquiry details, user message/suggestion,
       and convenient reply-to set directly to the customer.
    2. An automated confirmation acknowledgment to the customer (if an email is provided).
    """
    alert_sent = _send_admin_alert_email(inquiry)
    _send_customer_confirmation_email(inquiry)
    return alert_sent


def _send_admin_alert_email(inquiry) -> bool:
    recipients = _get_admin_recipients()
    if not recipients:
        logger.warning("No admin recipients configured for contact notifications.")
        return False

    type_label = inquiry.get_inquiry_type_display() if hasattr(inquiry, "get_inquiry_type_display") else inquiry.inquiry_type
    sender_name = inquiry.name.strip() or "Valued Guest"
    subject_title = inquiry.subject.strip() or type_label

    # Email Subject
    email_subject = f"[Gama Jewels Alert] New {type_label}: {sender_name}"
    if inquiry.inquiry_type == "newsletter":
        email_subject = f"[Gama Jewels Alert] New Private Circle Subscriber: {inquiry.email}"

    # Plain Text Fallback
    text_content = (
        f"GAMA JEWELS - NEW INQUIRY / FORM SUBMISSION\n"
        f"--------------------------------------------\n"
        f"Form Type: {type_label}\n"
        f"Name: {inquiry.name or 'N/A'}\n"
        f"Email: {inquiry.email}\n"
        f"Phone: {inquiry.phone or 'N/A'}\n"
        f"Subject / Request: {subject_title}\n"
    )
    if inquiry.timeframe:
        text_content += f"Timeframe: {inquiry.timeframe}\n"
    if inquiry.attachment_url:
        text_content += f"Attachment: {inquiry.attachment_url}\n"
    if inquiry.message:
        text_content += f"\nCustomer Message / Thoughts:\n{inquiry.message}\n"
    text_content += f"\nSubmitted at: {inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}\n"

    # Luxury HTML Template
    timeframe_row = (
        f'<tr><td style="padding:10px 14px;color:#888;font-size:12px;border-bottom:1px solid #222;">Timeframe</td>'
        f'<td style="padding:10px 14px;color:#fff;font-size:13px;border-bottom:1px solid #222;">{escape(inquiry.timeframe)}</td></tr>'
        if inquiry.timeframe else ""
    )
    attachment_row = (
        f'<tr><td style="padding:10px 14px;color:#888;font-size:12px;border-bottom:1px solid #222;">Attachment</td>'
        f'<td style="padding:10px 14px;font-size:13px;border-bottom:1px solid #222;">'
        f'<a href="{escape(inquiry.attachment_url)}" target="_blank" style="color:#c6a45f;text-decoration:underline;">View Uploaded File</a></td></tr>'
        if inquiry.attachment_url else ""
    )
    message_section = (
        f'<div style="margin-top:20px;padding:16px;background:#111;border-left:3px solid #c6a45f;border-radius:4px;">'
        f'<div style="font-size:11px;color:#c6a45f;letter-spacing:1px;text-transform:uppercase;font-weight:700;margin-bottom:8px;">Customer Thoughts / Requirements</div>'
        f'<div style="font-size:13.5px;color:#eee;line-height:1.6;white-space:pre-wrap;">{escape(inquiry.message)}</div>'
        f'</div>'
        if inquiry.message else ""
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{escape(email_subject)}</title>
    </head>
    <body style="margin:0;padding:24px;background-color:#080808;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#ffffff;">
      <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:620px;margin:0 auto;background:#0d0d0d;border:1px solid rgba(198,164,95,0.3);border-radius:8px;overflow:hidden;">
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#000000 0%,#181510 100%);padding:28px 24px;text-align:center;border-bottom:1px solid rgba(198,164,95,0.25);">
            <div style="color:#c6a45f;font-size:11px;letter-spacing:3px;text-transform:uppercase;margin-bottom:4px;">✦ GAMA JEWELS ✦</div>
            <h1 style="margin:0;font-size:20px;color:#ffffff;letter-spacing:1px;font-weight:600;font-family:Georgia,serif;">New Website Form Submission</h1>
            <div style="display:inline-block;margin-top:10px;padding:4px 12px;background:rgba(198,164,95,0.15);border:1px solid rgba(198,164,95,0.4);border-radius:12px;color:#e6c987;font-size:11px;letter-spacing:1px;text-transform:uppercase;font-weight:600;">
              {escape(type_label)}
            </div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:28px 24px;">
            <p style="margin:0 0 16px;font-size:14px;color:#cccccc;line-height:1.5;">
              A customer has submitted a message / inquiry through the Gama Jewels website. Here are their details:
            </p>

            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:20px;background:#090909;border:1px solid #1a1a1a;border-radius:6px;overflow:hidden;">
              <tr>
                <td style="padding:10px 14px;color:#888;font-size:12px;border-bottom:1px solid #222;width:30%;">Name</td>
                <td style="padding:10px 14px;color:#fff;font-size:13px;border-bottom:1px solid #222;font-weight:600;">{escape(sender_name)}</td>
              </tr>
              <tr>
                <td style="padding:10px 14px;color:#888;font-size:12px;border-bottom:1px solid #222;">Email</td>
                <td style="padding:10px 14px;font-size:13px;border-bottom:1px solid #222;">
                  <a href="mailto:{escape(inquiry.email)}" style="color:#c6a45f;text-decoration:none;font-weight:600;">{escape(inquiry.email)}</a>
                </td>
              </tr>
              <tr>
                <td style="padding:10px 14px;color:#888;font-size:12px;border-bottom:1px solid #222;">Phone / WhatsApp</td>
                <td style="padding:10px 14px;font-size:13px;border-bottom:1px solid #222;">
                  {f'<a href="tel:{escape(inquiry.phone)}" style="color:#fff;text-decoration:none;">{escape(inquiry.phone)}</a>' if inquiry.phone else '<span style="color:#666;">Not provided</span>'}
                </td>
              </tr>
              <tr>
                <td style="padding:10px 14px;color:#888;font-size:12px;border-bottom:1px solid #222;">Subject / Inquiry</td>
                <td style="padding:10px 14px;color:#fff;font-size:13px;border-bottom:1px solid #222;">{escape(subject_title)}</td>
              </tr>
              {timeframe_row}
              {attachment_row}
            </table>

            {message_section}

            <!-- Quick Action Button -->
            <div style="margin-top:24px;text-align:center;">
              <a href="mailto:{escape(inquiry.email)}?subject=Re:%20{escape(subject_title)}%20-%20Gama%20Jewels" style="display:inline-block;padding:12px 28px;background:linear-gradient(135deg,#c6a45f,#a88738);color:#000000;text-decoration:none;font-weight:700;font-size:12px;letter-spacing:1px;text-transform:uppercase;border-radius:4px;">
                Reply Directly to Customer
              </a>
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:16px 24px;background:#050505;border-top:1px solid #1a1a1a;text-align:center;font-size:11px;color:#666666;">
            Gama Jewels Flagship Atelier • Marol, Andheri(E), Mumbai 400059 • +91 9869800084<br>
            Submitted on {inquiry.created_at.strftime('%Y-%m-%d at %H:%M:%S UTC')}
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "Gama Diamonds <gama.diamond10@gmail.com>")
        headers = {}
        if inquiry.email and "@" in inquiry.email:
            headers["Reply-To"] = f"{inquiry.name} <{inquiry.email}>" if inquiry.name else inquiry.email

        msg = EmailMultiAlternatives(
            subject=email_subject,
            body=text_content,
            from_email=from_email,
            to=recipients,
            headers=headers,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("Admin alert email sent successfully for inquiry %s to %s", inquiry.id, recipients)
        return True
    except Exception as e:
        logger.exception("Failed to send admin alert email for inquiry %s: %s", inquiry.id, e)
        return False


def _send_customer_confirmation_email(inquiry) -> bool:
    """Sends an automated confirmation to the customer acknowledging their submission."""
    if not inquiry.email or "@" not in inquiry.email:
        return False

    # Do not send confirmation for silent newsletter if you prefer only sending for inquiries,
    # but a welcome email is very pleasant.
    sender_name = inquiry.name.strip() or "Valued Client"
    is_newsletter = inquiry.inquiry_type == "newsletter"

    if is_newsletter:
        subject = "Welcome to the Gama Jewels Private Circle"
        greeting = f"Dear {sender_name},"
        message_intro = "Thank you for subscribing to the Gama Jewels Private Circle. You will now receive private previews of our new bespoke releases, diamond guides, and atelier updates."
    else:
        subject = "Thank you for reaching out to Gama Jewels"
        greeting = f"Dear {sender_name},"
        message_intro = "Thank you for contacting Gama Jewels. We have received your inquiry and our diamond specialists and atelier artisans will review your requirements and reach out to you shortly."

    text_content = (
        f"{greeting}\n\n"
        f"{message_intro}\n\n"
        f"If you need immediate assistance or would like to visit our Mumbai atelier, please feel free to call or WhatsApp us at +91 9869800084.\n\n"
        f"Warm regards,\n"
        f"Gama Jewels Atelier\n"
        f"Mumbai, India\n"
        f"https://gamadiamonds.com"
    )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:24px;background-color:#080808;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#ffffff;">
      <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;margin:0 auto;background:#0d0d0d;border:1px solid rgba(198,164,95,0.3);border-radius:8px;overflow:hidden;">
        <tr>
          <td style="background:linear-gradient(135deg,#000000 0%,#181510 100%);padding:28px 24px;text-align:center;border-bottom:1px solid rgba(198,164,95,0.25);">
            <div style="color:#c6a45f;font-size:11px;letter-spacing:3px;text-transform:uppercase;margin-bottom:6px;">✦ GAMA JEWELS ✦</div>
            <h1 style="margin:0;font-size:19px;color:#ffffff;letter-spacing:1px;font-weight:600;font-family:Georgia,serif;">Bespoke Atelier Consultation</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 24px;font-size:14px;color:#cccccc;line-height:1.7;">
            <p style="margin:0 0 16px;color:#ffffff;font-size:15px;font-weight:600;">{escape(greeting)}</p>
            <p style="margin:0 0 16px;">{escape(message_intro)}</p>
            <div style="padding:16px;background:#111;border-left:3px solid #c6a45f;margin:20px 0;border-radius:3px;">
              <p style="margin:0;font-size:12.5px;color:#aaa;">
                <strong style="color:#c6a45f;">Need immediate assistance?</strong><br>
                Call or WhatsApp our concierge: <a href="tel:+919869800084" style="color:#fff;text-decoration:none;">+91 9869800084</a><br>
                Direct Email: <a href="mailto:info@gamajewels.com" style="color:#c6a45f;text-decoration:none;">info@gamajewels.com</a>
              </p>
            </div>
            <p style="margin:20px 0 0;font-size:13px;color:#888;">
              Warm regards,<br>
              <strong style="color:#c6a45f;">The Gama Jewels Team</strong>
            </p>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "Gama Diamonds <gama.diamond10@gmail.com>")
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[inquiry.email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("Customer confirmation email sent to %s", inquiry.email)
        return True
    except Exception as e:
        logger.warning("Could not send confirmation email to customer %s: %s", inquiry.email, e)
        return False

