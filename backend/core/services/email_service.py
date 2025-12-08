"""
Email service for sending transactional emails.
Supports SendGrid, AWS SES, and SMTP.
"""
import logging
import os
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    """Supported email providers."""
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"
    SMTP = "smtp"


class EmailService:
    """
    Email service for sending transactional emails.
    
    Supports multiple providers:
    - SendGrid (recommended for production)
    - AWS SES
    - SMTP (for development/testing)
    """
    
    def __init__(self, provider: Optional[EmailProvider] = None):
        """
        Initialize email service.
        
        Args:
            provider: Email provider to use. If None, auto-detects from environment.
        """
        self.provider = provider or self._detect_provider()
        self.client = self._initialize_client()
        logger.info(f"Email service initialized with provider: {self.provider}")
    
    def _detect_provider(self) -> EmailProvider:
        """Detect email provider from environment variables."""
        if os.getenv("SENDGRID_API_KEY"):
            return EmailProvider.SENDGRID
        elif os.getenv("AWS_SES_REGION"):
            return EmailProvider.AWS_SES
        elif os.getenv("SMTP_HOST"):
            return EmailProvider.SMTP
        else:
            # Default to SMTP for development
            logger.warning("No email provider configured, using SMTP fallback")
            return EmailProvider.SMTP
    
    def _initialize_client(self):
        """Initialize the email client based on provider."""
        if self.provider == EmailProvider.SENDGRID:
            try:
                from sendgrid import SendGridAPIClient
                api_key = os.getenv("SENDGRID_API_KEY")
                if not api_key:
                    raise ValueError("SENDGRID_API_KEY not set")
                return SendGridAPIClient(api_key)
            except ImportError:
                logger.error("sendgrid package not installed. Install with: pip install sendgrid")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}")
                return None
        
        elif self.provider == EmailProvider.AWS_SES:
            try:
                import boto3
                region = os.getenv("AWS_SES_REGION", "us-east-1")
                return boto3.client('ses', region_name=region)
            except ImportError:
                logger.error("boto3 package not installed. Install with: pip install boto3")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize AWS SES client: {e}")
                return None
        
        elif self.provider == EmailProvider.SMTP:
            # SMTP client will be created per-request
            return None
        
        return None
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            from_email: Sender email (defaults to configured sender)
            from_name: Sender name (optional)
            reply_to: Reply-to email address (optional)
            attachments: List of attachments (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.client and self.provider != EmailProvider.SMTP:
            logger.error("Email client not initialized")
            return False
        
        try:
            if self.provider == EmailProvider.SENDGRID:
                return await self._send_via_sendgrid(
                    to_email, subject, html_content, text_content,
                    from_email, from_name, reply_to, attachments
                )
            elif self.provider == EmailProvider.AWS_SES:
                return await self._send_via_ses(
                    to_email, subject, html_content, text_content,
                    from_email, from_name, reply_to, attachments
                )
            elif self.provider == EmailProvider.SMTP:
                return await self._send_via_smtp(
                    to_email, subject, html_content, text_content,
                    from_email, from_name, reply_to, attachments
                )
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False
        
        return False
    
    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: Optional[str],
        from_name: Optional[str],
        reply_to: Optional[str],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> bool:
        """Send email via SendGrid."""
        from sendgrid.helpers.mail import Mail, Email, Content, Attachment
        
        default_from = os.getenv("EMAIL_FROM", "noreply@powerhouse.ai")
        from_addr = from_email or default_from
        from_name_str = from_name or os.getenv("EMAIL_FROM_NAME", "Powerhouse Platform")
        
        message = Mail(
            from_email=Email(from_addr, from_name_str),
            to_emails=to_email,
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        if text_content:
            message.add_content(Content("text/plain", text_content))
        
        if reply_to:
            message.reply_to = Email(reply_to)
        
        if attachments:
            for att in attachments:
                attachment = Attachment()
                attachment.file_content = att.get("content")
                attachment.file_name = att.get("filename")
                attachment.file_type = att.get("type", "application/octet-stream")
                attachment.disposition = att.get("disposition", "attachment")
                message.add_attachment(attachment)
        
        try:
            response = self.client.send(message)
            if response.status_code in [200, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"SendGrid API returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return False
    
    async def _send_via_ses(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: Optional[str],
        from_name: Optional[str],
        reply_to: Optional[str],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> bool:
        """Send email via AWS SES."""
        default_from = os.getenv("EMAIL_FROM", "noreply@powerhouse.ai")
        from_addr = from_email or default_from
        
        destination = {"ToAddresses": [to_email]}
        
        message = {
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Html": {"Data": html_content, "Charset": "UTF-8"}
            }
        }
        
        if text_content:
            message["Body"]["Text"] = {"Data": text_content, "Charset": "UTF-8"}
        
        try:
            response = self.client.send_email(
                Source=from_addr,
                Destination=destination,
                Message=message,
                ReplyToAddresses=[reply_to] if reply_to else []
            )
            logger.info(f"Email sent successfully to {to_email}, MessageId: {response['MessageId']}")
            return True
        except Exception as e:
            logger.error(f"AWS SES error: {e}")
            return False
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: Optional[str],
        from_name: Optional[str],
        reply_to: Optional[str],
        attachments: Optional[List[Dict[str, Any]]]
    ) -> bool:
        """Send email via SMTP."""
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        default_from = os.getenv("EMAIL_FROM", "noreply@powerhouse.ai")
        from_addr = from_email or default_from
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name or 'Powerhouse'} <{from_addr}>" if from_name else from_addr
        msg["To"] = to_email
        if reply_to:
            msg["Reply-To"] = reply_to
        
        # Add text and HTML parts
        if text_content:
            msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Add attachments
        if attachments:
            for att in attachments:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(att.get("content"))
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {att.get('filename')}"
                )
                msg.attach(part)
        
        try:
            server = smtplib.SMTP(smtp_host, smtp_port)
            if smtp_use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email sent successfully to {to_email} via SMTP")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

