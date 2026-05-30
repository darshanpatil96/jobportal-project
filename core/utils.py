from urllib.parse import quote

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from .models import account_activation_token


def build_activation_link(request, user, next_path: str = "") -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    link = request.build_absolute_uri(f"/accounts/activate/{uid}/{token}/")
    if next_path and next_path.startswith("/"):
        link = f"{link}?next={quote(next_path, safe='/')}"
    return link


def send_activation_email(request, user) -> str:
    """Send verification email. Returns the activation URL (for dev console display)."""
    activation_link = build_activation_link(request, user)
    subject = "Verify your email for ARTISAN Job Portal"
    message = (
        f"Hi {user.username},\n\n"
        f"Please click the link below to verify your email address:\n\n"
        f"{activation_link}\n\n"
        f"If you did not sign up, you can ignore this email."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    return activation_link


def decode_uid(uidb64):
    try:
        return force_str(urlsafe_base64_decode(uidb64))
    except (ValueError, TypeError):
        return None
