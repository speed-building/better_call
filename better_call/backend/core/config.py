import os
from typing import Optional


class Settings:
    """Application settings with environment variable support."""
    
    def __init__(self):
        # Twilio Configuration
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER", "+18576637141")
        self.twiml_url = os.getenv("TWIML_URL")
        
        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Stripe Configuration
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
        self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        
        # Payment Configuration
        self.payment_amount = float(os.getenv("PAYMENT_AMOUNT", "2.00"))
        self.payment_currency = os.getenv("PAYMENT_CURRENCY", "usd")
        self.payment_description = os.getenv("PAYMENT_DESCRIPTION", "Better Call Service")
        self.payment_success_url = os.getenv("PAYMENT_SUCCESS_URL", "http://localhost:9001/payment-confirmation")
        
        # Database Configuration
        self.db_path = os.getenv(
            "DB_PATH",
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "banco.db"
            )
        )
        
        # Backend Configuration
        self.backend_base_url = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:9001")

        # Stripe (placeholder for frontend redirect)
        self.stripe_checkout_url = os.getenv("STRIPE_CHECKOUT_URL", "")

        # JWT Auth
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "change-me-in-prod")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        try:
            self.jwt_access_token_exp_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXP_MINUTES", "1440"))
        except Exception:
            self.jwt_access_token_exp_minutes = 1440


# Global settings instance
settings = Settings()
