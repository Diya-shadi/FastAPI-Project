from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config import settings
from typing import List

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_verification_email(email: str, token: str):
    verification_url = f"http://localhost:8000/auth/verify-email?token={token}"
    
    html = f"""
    <html>
        <body>
            <h2>Verify Your Email Address</h2>
            <p>Thank you for registering! Please click the link below to verify your email address:</p>
            <a href="{verification_url}">Verify Email</a>
            <p>If you didn't create an account, please ignore this email.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Verify Your Email Address",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_password_reset_email(email: str, token: str):
    reset_url = f"http://localhost:8000/auth/reset-password?token={token}"
    
    html = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested a password reset. Click the link below to reset your password:</p>
            <a href="{reset_url}">Reset Password</a>
            <p>If you didn't request this, please ignore this email.</p>
            <p>This link will expire in 1 hour.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)