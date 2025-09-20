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


# Global settings instance
settings = Settings()
