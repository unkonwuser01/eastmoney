"""
Email notification service for sending push notifications via SMTP.
"""
import os
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""
    
    def __init__(self):
        """Initialize email service with configuration from environment."""
        self._load_config()
    
    def _load_config(self):
        """Load SMTP configuration from environment variables."""
        self.enabled = os.getenv("EMAIL_ENABLED", "").lower() == "true"
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "") or self.smtp_user
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.recipient_email = os.getenv("NOTIFICATION_RECIPIENT_EMAIL", "")
        
        # Feature toggles
        self.notify_on_report = os.getenv("NOTIFY_ON_REPORT", "true").lower() == "true"
        self.notify_on_alert = os.getenv("NOTIFY_ON_ALERT", "true").lower() == "true"
        self.notify_daily_summary = os.getenv("NOTIFY_DAILY_SUMMARY", "").lower() == "true"
        
        # Timing settings
        self.quiet_hours_enabled = os.getenv("QUIET_HOURS_ENABLED", "").lower() == "true"
        self.quiet_hours_start = os.getenv("QUIET_HOURS_START", "22:00")
        self.quiet_hours_end = os.getenv("QUIET_HOURS_END", "08:00")
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)
    
    def is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_enabled:
            return False
        
        try:
            now = datetime.now().time()
            start_parts = self.quiet_hours_start.split(":")
            end_parts = self.quiet_hours_end.split(":")
            
            start_time = time(int(start_parts[0]), int(start_parts[1]))
            end_time = time(int(end_parts[0]), int(end_parts[1]))
            
            # Handle overnight quiet hours (e.g., 22:00 - 08:00)
            if start_time > end_time:
                return now >= start_time or now <= end_time
            else:
                return start_time <= now <= end_time
        except Exception as e:
            logger.warning(f"Error checking quiet hours: {e}")
            return False
    
    def _create_smtp_connection(self):
        """Create SMTP connection with proper security."""
        if self.smtp_use_tls:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
        
        server.login(self.smtp_user, self.smtp_password)
        return server
    
    def _send_email_sync(self, recipient: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Send email synchronously."""
        if not self.is_configured():
            logger.warning("Email service not configured, skipping send")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_from_email
            msg["To"] = recipient
            
            # Add text version
            if text_body:
                msg.attach(MIMEText(text_body, "plain", "utf-8"))
            
            # Add HTML version
            msg.attach(MIMEText(html_body, "html", "utf-8"))
            
            with self._create_smtp_connection() as server:
                server.sendmail(self.smtp_from_email, recipient, msg.as_string())
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_email(self, recipient: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Send email asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._send_email_sync, recipient, subject, html_body, text_body)
    
    async def send_test_email(self, recipient: str) -> bool:
        """Send a test email to verify configuration."""
        subject = "🔔 VibeAlpha - 测试邮件 / Test Email"
        
        html_body = """
        <html>
        <head>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center; }
                .content { background: #f8fafc; padding: 30px; border-radius: 0 0 12px 12px; }
                .success { color: #059669; font-size: 48px; margin-bottom: 16px; }
                .footer { text-align: center; color: #64748b; margin-top: 20px; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">VibeAlpha Terminal</h1>
                    <p style="margin:10px 0 0 0; opacity:0.9;">邮件推送配置测试</p>
                </div>
                <div class="content">
                    <div style="text-align:center;">
                        <div class="success">✅</div>
                        <h2 style="color:#1e293b;">配置成功！</h2>
                        <p style="color:#475569;">
                            恭喜！您的邮件推送服务已正确配置。<br>
                            Congratulations! Your email notification service is properly configured.
                        </p>
                        <p style="color:#64748b; font-size:14px; margin-top:24px;">
                            发送时间 / Sent at: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
                        </p>
                    </div>
                </div>
                <div class="footer">
                    <p>© 2026 VibeAlpha Terminal. Powered by AI Intelligence.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        VibeAlpha Terminal - 邮件推送配置测试
        =====================================
        
        ✅ 配置成功！
        
        恭喜！您的邮件推送服务已正确配置。
        Congratulations! Your email notification service is properly configured.
        
        发送时间 / Sent at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        © 2026 VibeAlpha Terminal
        """
        
        return await self.send_email(recipient, subject, html_body, text_body)
    
    async def send_report_notification(
        self, 
        fund_code: str, 
        fund_name: str, 
        mode: str,
        report_summary: Optional[str] = None
    ) -> bool:
        """Send notification when a report is generated."""
        if not self.enabled or not self.notify_on_report:
            return False
        
        if self.is_quiet_hours():
            logger.info("Quiet hours active, skipping report notification")
            return False
        
        recipient = self.recipient_email
        if not recipient:
            return False
        
        mode_text = "盘前分析" if mode == "pre" else "盘后分析"
        subject = f"📊 {fund_name} ({fund_code}) - {mode_text}报告已生成"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 24px; border-radius: 12px 12px 0 0; }}
                .content {{ background: #f8fafc; padding: 24px; border-radius: 0 0 12px 12px; }}
                .badge {{ display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-top: 8px; }}
                .fund-info {{ background: white; padding: 16px; border-radius: 8px; margin-bottom: 16px; }}
                .footer {{ text-align: center; color: #64748b; margin-top: 20px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin:0;">📊 分析报告已生成</h2>
                    <span class="badge">{mode_text}</span>
                </div>
                <div class="content">
                    <div class="fund-info">
                        <div style="color:#64748b; font-size:12px;">基金信息</div>
                        <div style="font-size:18px; font-weight:600; color:#1e293b;">{fund_name}</div>
                        <div style="color:#3b82f6; font-family:monospace;">{fund_code}</div>
                    </div>
                    {f'<div style="color:#475569; line-height:1.6;">{report_summary}</div>' if report_summary else ''}
                    <p style="color:#64748b; font-size:14px; margin-top:20px;">
                        请登录 VibeAlpha 终端查看完整报告。
                    </p>
                </div>
                <div class="footer">
                    <p>© 2026 VibeAlpha Terminal</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recipient, subject, html_body)
    
    async def send_alert_notification(
        self,
        alert_title: str,
        alert_message: str,
        severity: str = "warning"
    ) -> bool:
        """Send notification for portfolio alerts."""
        if not self.enabled or not self.notify_on_alert:
            return False
        
        if self.is_quiet_hours():
            logger.info("Quiet hours active, skipping alert notification")
            return False
        
        recipient = self.recipient_email
        if not recipient:
            return False
        
        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(severity, "⚠️")
        severity_color = {"info": "#3b82f6", "warning": "#f59e0b", "critical": "#ef4444"}.get(severity, "#f59e0b")
        
        subject = f"{severity_emoji} VibeAlpha 预警: {alert_title}"
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {severity_color}; color: white; padding: 24px; border-radius: 12px 12px 0 0; }}
                .content {{ background: #f8fafc; padding: 24px; border-radius: 0 0 12px 12px; }}
                .alert-box {{ background: white; border-left: 4px solid {severity_color}; padding: 16px; border-radius: 0 8px 8px 0; }}
                .footer {{ text-align: center; color: #64748b; margin-top: 20px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin:0;">{severity_emoji} 投资预警</h2>
                </div>
                <div class="content">
                    <div class="alert-box">
                        <div style="font-size:16px; font-weight:600; color:#1e293b; margin-bottom:8px;">{alert_title}</div>
                        <div style="color:#475569; line-height:1.6;">{alert_message}</div>
                    </div>
                    <p style="color:#64748b; font-size:14px; margin-top:20px;">
                        请登录 VibeAlpha 终端查看详情并采取相应措施。
                    </p>
                </div>
                <div class="footer">
                    <p>发送时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p>© 2026 VibeAlpha Terminal</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(recipient, subject, html_body)


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def reload_email_service():
    """Reload email service configuration."""
    global _email_service
    _email_service = EmailService()
