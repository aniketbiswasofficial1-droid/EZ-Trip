"""
Email notification service for EZ-Trip
Handles sending email notifications to trip members
"""

import os
import logging
from typing import List
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Email configuration from environment variables
# For Microsoft Outlook/Office 365:
# SMTP_HOST should be 'smtp.office365.com' or 'smtp-mail.outlook.com'
# SMTP_PORT should be 587
# SMTP_USE_TLS should be True
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.office365.com')  # Default to Outlook
SMTP_PORT = int(os.getenv('SMTP_PORT') or '587')  # Handle empty string
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')  # Your Outlook email
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')  # Your Outlook password or app password
EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS', 'EZ Trip <noreply@eztrip.com>')
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME', 'EZ Trip')

class EmailService:
    """Email service for sending notifications"""
    
    @staticmethod
    async def send_email(to_emails: List[str], subject: str, html_body: str, text_body: str = None):
        """
        Send an email to multiple recipients
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
        """
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("Email credentials not configured. Skipping email send.")
            return False
            
        try:
            message = MIMEMultipart('alternative')
            message['From'] = EMAIL_FROM_ADDRESS
            message['To'] = ', '.join(to_emails)
            message['Subject'] = subject
            
            # Add plain text version if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                message.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                start_tls=SMTP_USE_TLS,
                username=SMTP_USERNAME,
                password=SMTP_PASSWORD,
            )
            
            logger.info(f"Email sent successfully to {len(to_emails)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    async def send_settlement_notification(
        trip_name: str,
        from_user_name: str,
        to_user_name: str,
        amount: float,
        currency: str,
        recipient_emails: List[str],
        note: str = None
    ):
        """Send notification when a settlement is recorded"""
        subject = f"💰 Payment Recorded in {trip_name}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; margin-bottom: 20px;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">💰 Payment Recorded</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <p style="font-size: 16px; margin: 0 0 10px 0;">
                        <strong>{from_user_name}</strong> paid <strong>{to_user_name}</strong>
                    </p>
                    <p style="font-size: 32px; font-weight: bold; color: #667eea; margin: 10px 0;">
                        {currency} {amount:.2f}
                    </p>
                    {f'<p style="font-size: 14px; color: #666; margin: 10px 0;"><em>Note: {note}</em></p>' if note else ''}
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    Trip: <strong>{trip_name}</strong>
                </p>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    Check your trip balance for updated details.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px; text-align: center;">
                    EZ Trip - Split expenses, not friendships
                </p>
            </body>
        </html>
        """
        
        text_body = f"""
Payment Recorded in {trip_name}

{from_user_name} paid {to_user_name}: {currency} {amount:.2f}
{f'Note: {note}' if note else ''}

Check your trip balance for updated details.

---
EZ Trip - Split expenses, not friendships
        """
        
        return await EmailService.send_email(recipient_emails, subject, html_body, text_body)
    
    @staticmethod
    async def send_expense_added_notification(
        trip_name: str,
        expense_description: str,
        amount: float,
        currency: str,
        payer_names: List[str],
        recipient_emails: List[str]
    ):
        """Send notification when an expense is added"""
        subject = f"📝 New Expense in {trip_name}"
        
        payers_text = ", ".join(payer_names)
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; margin-bottom: 20px;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">📝 New Expense Added</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <p style="font-size: 18px; margin: 0 0 10px 0; font-weight: bold;">
                        {expense_description}
                    </p>
                    <p style="font-size: 32px; font-weight: bold; color: #667eea; margin: 10px 0;">
                        {currency} {amount:.2f}
                    </p>
                    <p style="font-size: 14px; color: #666; margin: 10px 0;">
                        Paid by: <strong>{payers_text}</strong>
                    </p>
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    Trip: <strong>{trip_name}</strong>
                </p>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    Your balances have been updated.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px; text-align: center;">
                    EZ Trip - Split expenses, not friendships
                </p>
            </body>
        </html>
        """
        
        text_body = f"""
New Expense Added to {trip_name}

{expense_description}
Amount: {currency} {amount:.2f}
Paid by: {payers_text}

Your balances have been updated.

---
EZ Trip - Split expenses, not friendships
        """
        
        return await EmailService.send_email(recipient_emails, subject, html_body, text_body)
    
    @staticmethod
    async def send_member_added_notification(
        trip_name: str,
        new_member_name: str,
        new_member_email: str,
        added_by_name: str
    ):
        """Send notification when someone is added to a trip"""
        subject = f"👋 You've been added to {trip_name}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; margin-bottom: 20px;">
                    <h1 style="color: white; margin: 0; font-size: 24px;">👋 Welcome to the Trip!</h1>
                </div>
                
                <p style="font-size: 16px;">Hi {new_member_name},</p>
                
                <p style="font-size: 16px;">
                    <strong>{added_by_name}</strong> has added you to <strong>{trip_name}</strong> on EZ Trip.
                </p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <p style="font-size: 14px; margin: 0;">
                        Sign in with your email (<strong>{new_member_email}</strong>) to view trip details and track expenses.
                    </p>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    EZ Trip makes it easy to split expenses and settle up with friends.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px; text-align: center;">
                    EZ Trip - Split expenses, not friendships
                </p>
            </body>
        </html>
        """
        
        text_body = f"""
Welcome to {trip_name}!

Hi {new_member_name},

{added_by_name} has added you to {trip_name} on EZ Trip.

Sign in with your email ({new_member_email}) to view trip details and track expenses.

EZ Trip makes it easy to split expenses and settle up with friends.

---
EZ Trip - Split expenses, not friendships
        """
        
        return await EmailService.send_email([new_member_email], subject, html_body, text_body)
