#!/usr/bin/env python3
"""
Email Sender Module

A reusable email sending module with pre-configured authentication for ProtonMail.
Extracted from the docker update script on zeus.

Usage:
    from email_sender import send_email
    
    success = send_email(
        subject="Test Subject",
        body="Test message body",
        recipient="custom@example.com"  # Optional, uses default if not provided
    )
"""

import configparser
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Union, List

_CONFIG_PATH = os.path.expanduser("~/.config/scripts/email.conf")


class EmailSender:
    """Email sender class with ProtonMail configuration"""

    def __init__(self):
        cfg = configparser.ConfigParser()
        if not cfg.read(_CONFIG_PATH):
            raise FileNotFoundError(
                f"Email config not found: {_CONFIG_PATH}\n"
                f"Copy lib/python/email.conf.example to {_CONFIG_PATH} and fill in credentials."
            )
        self.sender = cfg.get("smtp", "sender")
        self.password = cfg.get("smtp", "password")
        self.default_recipient = cfg.get("smtp", "default_recipient")
        self.server = cfg.get("smtp", "server")
        self.port = cfg.getint("smtp", "port")
    
    def send_email(self, 
                   subject: str, 
                   body: str, 
                   recipient: Optional[Union[str, List[str]]] = None,
                   html_body: Optional[str] = None) -> bool:
        """
        Send email with the configured ProtonMail settings
        
        Args:
            subject (str): Email subject line
            body (str): Plain text email body
            recipient (str or list, optional): Recipient email(s). Uses default if not provided.
            html_body (str, optional): HTML email body. If provided, creates multipart message.
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Use default recipient if none provided
            if recipient is None:
                recipient = self.default_recipient
            
            # Handle multiple recipients
            if isinstance(recipient, list):
                recipients = recipient
            else:
                recipients = [recipient]
            
            # Create message
            if html_body:
                # Create multipart message for HTML content
                msg = MIMEMultipart('alternative')
                text_part = MIMEText(body, 'plain')
                html_part = MIMEText(html_body, 'html')
                msg.attach(text_part)
                msg.attach(html_part)
            else:
                # Simple text message
                msg = MIMEText(body)
            
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = ', '.join(recipients) if isinstance(recipients, list) else recipients
            
            # Send email
            with smtplib.SMTP(self.server, self.port) as smtp_server:
                smtp_server.starttls()
                smtp_server.login(self.sender, self.password)
                smtp_server.send_message(msg)
            
            print(f"Email sent successfully to {', '.join(recipients)}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def send_notification(self, 
                         title: str, 
                         message: str, 
                         status: str = "INFO",
                         recipient: Optional[str] = None) -> bool:
        """
        Send a formatted notification email
        
        Args:
            title (str): Notification title
            message (str): Notification message
            status (str): Status level (INFO, SUCCESS, WARNING, ERROR)
            recipient (str, optional): Recipient email. Uses default if not provided.
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        # Format subject with status
        subject = f"[{status}] {title}"
        
        # Create formatted body
        body = f"""Notification: {title}
Status: {status}
Time: {self._get_timestamp()}

Message:
{message}

---
This is an automated notification from your system.
"""
        
        return self.send_email(subject, body, recipient)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Global instance for convenience
_email_sender = EmailSender()

# Convenience functions for easy import and use
def send_email(subject: str, 
               body: str, 
               recipient: Optional[Union[str, List[str]]] = None,
               html_body: Optional[str] = None) -> bool:
    """
    Convenience function to send email using the global EmailSender instance
    
    Args:
        subject (str): Email subject line
        body (str): Plain text email body
        recipient (str or list, optional): Recipient email(s). Uses default if not provided.
        html_body (str, optional): HTML email body. If provided, creates multipart message.
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    return _email_sender.send_email(subject, body, recipient, html_body)


def send_notification(title: str, 
                     message: str, 
                     status: str = "INFO",
                     recipient: Optional[str] = None) -> bool:
    """
    Convenience function to send notification using the global EmailSender instance
    
    Args:
        title (str): Notification title
        message (str): Notification message
        status (str): Status level (INFO, SUCCESS, WARNING, ERROR)
        recipient (str, optional): Recipient email. Uses default if not provided.
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    return _email_sender.send_notification(title, message, status, recipient)


if __name__ == "__main__":
    # Test the email functionality
    import sys
    
    if len(sys.argv) > 1:
        test_subject = sys.argv[1]
        test_body = sys.argv[2] if len(sys.argv) > 2 else "Test message from email_sender module"
        
        print("Testing email functionality...")
        success = send_email(test_subject, test_body)
        
        if success:
            print("✓ Email test successful")
            sys.exit(0)
        else:
            print("✗ Email test failed")
            sys.exit(1)
    else:
        print("Email sender module loaded successfully!")
        print("\nUsage examples:")
        print("  python email_sender.py 'Test Subject' 'Test Body'")
        print("  from email_sender import send_email, send_notification")
