"""
Environment configuration for the calendar application.

This module handles environment variables and application settings.
"""

import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    # Security settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

    # Database settings
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # Application settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # CORS settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    # Yelp API settings
    YELP_API_KEY: Optional[str] = os.getenv("YELP_API_KEY")
    YELP_API_URL: str = "https://api.yelp.com/v3"

    def __init__(self):
        """Initialize settings and validate required environment variables."""
        if not self.JWT_SECRET_KEY:
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "JWT_SECRET_KEY environment variable is required in production"
                )
            else:
                # Generate a random key for development
                import secrets

                self.JWT_SECRET_KEY = secrets.token_urlsafe(32)
                print(
                    "⚠️  WARNING: Using auto-generated JWT secret. Set JWT_SECRET_KEY environment variable for production."
                )


# Global settings instance
settings = Settings()
