"""SMTP e-mail sending. If SMTP is not configured the feature is reported as unavailable (never faked)."""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

log = logging.getLogger("communiai.email")


class EmailNotConfigured(Exception):
    pass


def send_email(to: str, subject: str, body: str) -> None:
    s = get_settings()
    if not s.email_enabled:
        raise EmailNotConfigured()
    msg = EmailMessage()
    msg["From"] = s.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(s.SMTP_HOST, s.SMTP_PORT, timeout=20) as smtp:
        if s.SMTP_USE_TLS:
            smtp.starttls()
        if s.SMTP_USER:
            smtp.login(s.SMTP_USER, s.SMTP_PASSWORD)
        smtp.send_message(msg)
