import smtplib
from typing import Optional

import requests
from app.core.config import EmailSettings, settings


class EmailService:
    def __init__(self, validate=False):
        self.settings: EmailSettings = settings
        if validate:
            self._validate_config(settings)

    def _validate_config(self, settings: EmailSettings) -> None:
        missing = [
            name
            for name, value in {
                "EMAIL_SMTP_HOST": settings.EMAIL_SMTP_HOST,
                "EMAIL_SMTP_USERNAME": settings.EMAIL_SMTP_USERNAME,
                "EMAIL_SMTP_PASSWORD": settings.EMAIL_SMTP_PASSWORD,
                "EMAIL_FROM_ADDRESS": settings.EMAIL_FROM_ADDRESS,
                "EMAIL_API_SEND_URL": settings.EMAIL_API_SEND_URL,
                "EMAIL_API_KEY": settings.EMAIL_API_KEY,
                "EMAIL_API_SECRET": settings.EMAIL_API_SECRET,
            }.items()
            if not value
        ]

        if missing:
            raise RuntimeError(
                f"EmailService misconfigured. Missing env vars: {', '.join(missing)}"
            )

    def _send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> None:
        message = self._build_message(
            subject=subject,
            to_email=to_email,
            html_body=html_body,
            text_body=text_body,
            from_address=self.from_address,
            from_name=self.from_name,
        )

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()

            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(
                self.from_address,
                [to_email],
                message.as_string(),
            )

    async def send_otp_email(self, to_email: str, otp_code: str):
        """Send simple OTP email"""

        # TODO: switch to template file system
        subject = "Password Reset Code"

        html_body = f"""
        <h2>Password Reset</h2>
        <p>Your verification code is:</p>
        <h1 style="color: #3498db; font-size: 32px;">{otp_code}</h1>
        <p>This code expires in 10 minutes.</p>
        <p>If you didn't request this, ignore this email.</p>
        """

        text_body = f"""
        Password Reset
        
        Your verification code is: {otp_code}
        
        This code expires in 10 minutes.
        """

        await EmailService._send_email(to_email, subject, html_body, text_body)

    def send_email_via_api(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> None:
        if not self.settings.email_api_key or not self.settings.email_api_secret:
            raise RuntimeError("Email API credentials not configured")

        payload = {
            "Messages": [
                {
                    "From": {
                        "Email": self.settings.EMAIL_FROM_ADDRESS,
                        "Name": self.settings.EMAIL_FROM_NAME,
                    },
                    "To": [{"Email": to_email}],
                    "Subject": subject,
                    "HTMLPart": html_body,
                    **({"TextPart": text_body} if text_body else {}),
                }
            ]
        }

        response = requests.post(
            self.settings.EMAIL_API_SEND_URL,
            auth=(
                self.settings.EMAIL_API_KEY,
                self.settings.EMAIL_API_SECRET,
            ),
            json=payload,
            timeout=10,
        )

        if not response.ok:
            raise RuntimeError(
                f"Email API send failed: {response.status_code} {response.text}"
            )
