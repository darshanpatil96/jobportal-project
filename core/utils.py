from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings


def send_activation_email(request, user):
    current_site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    activation_link = request.build_absolute_uri(f"/accounts/activate/{uid}/{token}/")
    subject = "Verify your email for JobPortal"
    message = (
        f"Hi {user.username},\n\n"
        f"Please click the link below to verify your email address:\n\n"
        f"{activation_link}\n\n"
        f"If you did not sign up, you can ignore this email."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    return True


def decode_uid(uidb64):
    try:
        return force_str(urlsafe_base64_decode(uidb64))
    except (ValueError, TypeError):
        return None
