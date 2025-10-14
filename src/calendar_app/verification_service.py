"""
Verification service for handling email and SMS verification codes
"""

import random
from datetime import datetime, timedelta
from typing import Optional, Literal
from sqlalchemy.orm import Session
import os

from .database import VerificationCode


class VerificationService:
    def __init__(self):
        # Email configuration (you'll need to set these environment variables)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        # Twilio configuration (you'll need to set these environment variables)
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER", "")
        
        # Twilio client will be None for now (can be implemented later)
        self.twilio_client = None

    def generate_verification_code(self) -> str:
        """Generate a 6-digit verification code"""
        return str(random.randint(100000, 999999))

    async def send_email_verification(
        self, 
        db: Session,
        email: str, 
        verification_type: Literal["registration", "login"] = "registration"
    ) -> bool:
        """Send verification code via email"""
        try:
            # Generate verification code
            code = self.generate_verification_code()
            
            # Store in database
            expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minute expiry
            verification = VerificationCode(
                email=email,
                code=code,
                verification_type=f"email_{verification_type}",
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                is_used=False
            )
            db.add(verification)
            db.commit()
            
            # Prepare email content
            subject = "Élite Platform - Verification Code"
            
            html_content = f"""
            <html>
                <body style="font-family: 'Inter', Arial, sans-serif; background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%); color: #ffffff; margin: 0; padding: 40px;">
                    <div style="max-width: 600px; margin: 0 auto; background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 40px; text-align: center;">
                        <div style="font-family: 'Playfair Display', serif; font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #FFD700, #FFA500); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px;">
                            Élite
                        </div>
                        
                        <h2 style="color: #ffffff; margin-bottom: 20px;">Verification Required</h2>
                        
                        <p style="color: rgba(255, 255, 255, 0.8); margin-bottom: 30px; font-size: 1.1rem;">
                            Your exclusive verification code for {'account creation' if verification_type == 'registration' else 'secure login'}:
                        </p>
                        
                        <div style="background: linear-gradient(135deg, #FFD700, #FFA500); color: #000; font-size: 2.5rem; font-weight: 700; padding: 20px; border-radius: 12px; margin: 30px 0; letter-spacing: 8px;">
                            {code}
                        </div>
                        
                        <p style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem; margin-top: 20px;">
                            This code will expire in 10 minutes for your security.
                        </p>
                        
                        <div style="border-top: 1px solid rgba(255, 255, 255, 0.1); margin-top: 30px; padding-top: 20px;">
                            <p style="color: rgba(255, 255, 255, 0.5); font-size: 0.8rem;">
                                If you didn't request this verification, please ignore this email.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # For development - just print the code (replace with real email sending in production)
            print(f"🔐 EMAIL VERIFICATION CODE for {email}: {code}")
            print(f"📧 Email would be sent with subject: {subject}")
            return True
                
        except Exception as e:
            print(f"Error sending email verification: {e}")
            return False

    async def send_sms_verification(
        self, 
        db: Session,
        phone: str, 
        verification_type: Literal["registration", "login"] = "registration"
    ) -> bool:
        """Send verification code via SMS"""
        try:
            # Generate verification code
            code = self.generate_verification_code()
            
            # Store in database
            expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minute expiry
            verification = VerificationCode(
                phone=phone,
                code=code,
                verification_type=f"sms_{verification_type}",
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                is_used=False
            )
            db.add(verification)
            db.commit()
            
            # Prepare SMS content
            message_body = f"""
Élite Platform 👑

Your verification code: {code}

This code expires in 10 minutes.

If you didn't request this, please ignore.
            """.strip()
            
            # For development - just print the code (replace with real SMS sending in production)
            print(f"📱 SMS VERIFICATION CODE for {phone}: {code}")
            print(f"📲 SMS content preview: {message_body}")
            return True
                
        except Exception as e:
            print(f"Error sending SMS verification: {e}")
            return False

    def verify_code(
        self, 
        db: Session,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        code: str = "",
        verification_type: str = ""
    ) -> bool:
        """Verify the provided code"""
        try:
            # Build query based on provided identifiers
            query = db.query(VerificationCode).filter(
                VerificationCode.code == code,
                VerificationCode.is_used == False,
                VerificationCode.expires_at > datetime.utcnow()
            )
            
            if email:
                query = query.filter(VerificationCode.email == email)
            if phone:
                query = query.filter(VerificationCode.phone == phone)
            if verification_type:
                query = query.filter(VerificationCode.verification_type.like(f"%{verification_type}%"))
            
            verification = query.first()
            
            if verification:
                # Mark as used
                verification.is_used = True
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error verifying code: {e}")
            return False

    def cleanup_expired_codes(self, db: Session):
        """Clean up expired verification codes"""
        try:
            db.query(VerificationCode).filter(
                VerificationCode.expires_at < datetime.utcnow()
            ).delete()
            db.commit()
        except Exception as e:
            print(f"Error cleaning up expired codes: {e}")


# Global instance
verification_service = VerificationService()