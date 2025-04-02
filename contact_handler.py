from fastapi import HTTPException
from supabase import create_client, Client
import os
from typing import Optional
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Set up logging
logger = logging.getLogger("smallhappiness")

class ContactHandler:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_KEY", "")
        )
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "info@smallhappiness.com")

    async def store_contact(self, name: str, email: str, message: str, user_id: Optional[str] = None) -> dict:
        """Store contact form submission in Supabase"""
        try:
            data = {
                "name": name,
                "email": email,
                "message": message,
                "user_id": user_id
            }
            result = self.supabase.table("contacts").insert(data).execute()
            return result.data[0]
        except Exception as e:
            logger.error(f"Error storing contact: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to store contact message")

    async def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    async def handle_contact_submission(
        self,
        name: str,
        email: str,
        message: str,
        copy: bool = False,
        user_id: Optional[str] = None
    ) -> dict:
        """Handle contact form submission"""
        try:
            # Store in database
            contact = await self.store_contact(name, email, message, user_id)

            # Send notification to admin
            admin_email = os.getenv("ADMIN_EMAIL", "info@smallhappiness.com")
            admin_subject = f"New Contact Form Submission from {name}"
            admin_body = f"""
            New contact form submission:
            
            Name: {name}
            Email: {email}
            Message: {message}
            """
            await self.send_email(admin_email, admin_subject, admin_body)

            # Send copy to user if requested
            if copy:
                user_subject = "Copy of your message to Small Happiness Club"
                user_body = f"""
                Dear {name},

                Thank you for contacting Small Happiness Club. Here's a copy of your message:

                {message}

                We'll get back to you soon!

                Best regards,
                Small Happiness Club Team
                """
                await self.send_email(email, user_subject, user_body)

            return {"success": True, "message": "Message sent successfully"}
        except Exception as e:
            logger.error(f"Error handling contact submission: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to process contact submission") 