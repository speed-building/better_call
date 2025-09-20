from typing import Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

from ..core.config import settings
from ..core.exceptions import TwilioConfigurationError, CallServiceError


class TwilioService:
    """Service for handling Twilio API interactions."""
    
    def __init__(self):
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            raise TwilioConfigurationError(
                "Twilio credentials are not properly configured",
                details={
                    "account_sid_present": bool(settings.twilio_account_sid),
                    "auth_token_present": bool(settings.twilio_auth_token)
                }
            )
        
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    
    def make_call(self, destination: str) -> Dict[str, Any]:
        """
        Make a call using Twilio API.
        
        Args:
            destination: Phone number to call in international format
            
        Returns:
            Dictionary containing call information (sid, to, etc.)
            
        Raises:
            CallServiceError: If the call fails
        """
        try:
            call = self.client.calls.create(
                to=destination,
                from_=settings.twilio_from_number,
                url=settings.twiml_url,
            )
            
            return {
                "call_sid": call.sid,
                "to": destination,
                "status": call.status,
                "from_": settings.twilio_from_number
            }
            
        except TwilioException as e:
            raise CallServiceError(
                f"Failed to make call to {destination}",
                details={
                    "twilio_error": str(e),
                    "destination": destination,
                    "from_number": settings.twilio_from_number
                }
            )
        except Exception as e:
            raise CallServiceError(
                f"Unexpected error making call to {destination}",
                details={"error": str(e), "destination": destination}
            )
