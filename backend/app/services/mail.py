from __future__ import annotations

import asyncio
from email.message import EmailMessage
import logging
import smtplib

from app.core.config import Settings


logger = logging.getLogger(__name__)


async def send_auth_email(*, recipient: str, subject: str, body: str, settings: Settings) -> None:
    if not settings.smtp_host:
        logger.warning("smtp_not_configured recipient=%s subject=%s", recipient, subject)
        return

    message = EmailMessage()
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    await asyncio.to_thread(_send_message, message, settings)


def _send_message(message: EmailMessage, settings: Settings) -> None:
    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
            _login_and_send(smtp, message, settings)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        _login_and_send(smtp, message, settings)


def _login_and_send(smtp, message: EmailMessage, settings: Settings) -> None:
    if settings.smtp_username:
        smtp.login(settings.smtp_username, settings.smtp_password)
    smtp.send_message(message)


async def send_verification_code_email(*, recipient: str, code: str, settings: Settings) -> None:
    await send_auth_email(
        recipient=recipient,
        subject="Код подтверждения email",
        body=f"Код подтверждения email: {code}",
        settings=settings,
    )


async def send_password_reset_code_email(*, recipient: str, code: str, settings: Settings) -> None:
    await send_auth_email(
        recipient=recipient,
        subject="Код сброса пароля",
        body=f"Код сброса пароля: {code}",
        settings=settings,
    )
