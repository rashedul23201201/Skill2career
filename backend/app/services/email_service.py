import logging
import os
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger("notification.email")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailService:
    """Email delivery service with asynchronous/mock fallback for non-production environments (SKL-17)."""

    def __init__(self):
        # In-memory record of dispatched emails for unit testing and local audit
        self.dispatched_emails: List[Dict[str, Any]] = []

    def validate_email_syntax(self, email: str) -> bool:
        """Validate recipient email address syntax (Error Cases Handled)."""
        if not email or not isinstance(email, str):
            return False
        return bool(EMAIL_REGEX.match(email.strip()))

    def send_notification_email(
        self,
        to_email: str,
        recipient_name: str,
        subject: str,
        event_type: str,
        title: str,
        message: str,
        link_url: Optional[str] = None,
    ) -> bool:
        """Send an email notification for a platform activity (AC-4).
        Never raises unhandled exceptions to avoid failing parent HTTP transactions.
        """
        if not self.validate_email_syntax(to_email):
            logger.warning(
                "Cannot dispatch email: invalid recipient email address syntax '%s'",
                to_email,
            )
            return False

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
        action_url = f"{frontend_url}{link_url}" if link_url and link_url.startswith("/") else (link_url or frontend_url)

        plain_text = (
            f"Hello {recipient_name},\n\n"
            f"{title}\n\n"
            f"{message}\n\n"
            f"View details: {action_url}\n\n"
            f"— The Skill2Career Team\n"
        )

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }}
    .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background: #0f172a; padding: 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 800; letter-spacing: 0.5px; }}
    .content {{ padding: 32px 24px; }}
    .title {{ font-size: 18px; font-weight: 700; color: #1e293b; margin-top: 0; margin-bottom: 12px; }}
    .message {{ font-size: 14px; line-height: 1.6; color: #475569; margin-bottom: 24px; }}
    .button {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; text-align: center; }}
    .footer {{ padding: 20px 24px; background-color: #f1f5f9; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>SKILL<span style="color: #3b82f6;">2</span>CAREER</h1>
    </div>
    <div class="content">
      <p style="margin-top:0; font-size: 14px; color: #64748b;">Hello <strong>{recipient_name}</strong>,</p>
      <h2 class="title">{title}</h2>
      <div class="message">{message}</div>
      <div style="text-align: center; margin: 28px 0;">
        <a href="{action_url}" class="button">View in Skill2Career</a>
      </div>
    </div>
    <div class="footer">
      <p style="margin: 0;">You received this email because of activity on your Skill2Career account.</p>
      <p style="margin: 4px 0 0 0;">&copy; {datetime.now(timezone.utc).year} Skill2Career Bangladesh. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
"""

        email_payload = {
            "to_email": to_email,
            "recipient_name": recipient_name,
            "subject": subject,
            "event_type": event_type,
            "title": title,
            "message": message,
            "plain_text": plain_text,
            "html_content": html_content,
            "dispatched_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check for real SMTP configuration if provided, otherwise record in test transport
        smtp_host = os.getenv("SMTP_HOST")
        if smtp_host:
            try:
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText

                smtp_port = int(os.getenv("SMTP_PORT", "587"))
                smtp_user = os.getenv("SMTP_USER", "")
                smtp_pass = os.getenv("SMTP_PASSWORD", "")
                from_email = os.getenv("SMTP_FROM", "notifications@skill2career.com")

                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = from_email
                msg["To"] = to_email

                part1 = MIMEText(plain_text, "plain")
                part2 = MIMEText(html_content, "html")
                msg.attach(part1)
                msg.attach(part2)

                with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
                    if os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1"):
                        server.starttls()
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.sendmail(from_email, [to_email], msg.as_string())

                logger.info("Successfully delivered SMTP email to %s for event '%s'", to_email, event_type)
            except Exception as exc:
                # Catch SMTP timeouts or delivery errors without failing parent HTTP request (AC-4, Error handling)
                logger.error(
                    "SMTP email delivery failure for %s (event '%s'): %s. Notification saved.",
                    to_email,
                    event_type,
                    exc,
                )
                # Keep tracked in dispatched record marked as failed
                email_payload["error"] = str(exc)
                email_payload["success"] = False
                self.dispatched_emails.append(email_payload)
                return False

        # In development / CI / Sandbox mode, log and record payload
        logger.info(
            "[Email Delivery Dispatched] To: %s | Subject: %s | Event: %s",
            to_email,
            subject,
            event_type,
        )
        email_payload["success"] = True
        self.dispatched_emails.append(email_payload)
        return True

    def clear_dispatched(self) -> None:
        """Clear recorded test emails."""
        self.dispatched_emails.clear()


# Global singleton instance
email_service = EmailService()
