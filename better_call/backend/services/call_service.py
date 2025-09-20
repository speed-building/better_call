from typing import Optional, Dict, Any

from ..models.requests import CallRequest
from ..models.responses import CallResponse
from ..core.exceptions import CallServiceError, DatabaseError
from .openai_service import OpenAIService
from .twilio_service import TwilioService


class CallService:
    """Main service for handling call operations."""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.twilio_service = TwilioService()
    
    def process_call_request(
        self, 
        request: CallRequest, 
        db_instance: Optional[Any] = None,
        user_id: Optional[int] = None,
    ) -> CallResponse:
        """
        Process a complete call request including prompt enrichment, database storage, and call execution.
        
        Args:
            request: The call request data
            db_instance: Optional database instance for storing the request
            
        Returns:
            CallResponse with the result of the operation
            
        Raises:
            CallServiceError: If any step of the process fails
        """
        try:
            # Step 1: Enrich the prompt
            enriched_prompt = self.openai_service.enrich_prompt(
                request.name, 
                request.prompt or ""
            )
            
            # Step 2: Store in database (optional, don't fail if this fails)
            if db_instance:
                try:
                    db_instance.insert_call_request(
                        email=request.email,
                        phone_to=request.destination,
                        prompt=enriched_prompt,
                        user_id=user_id,
                    )
                except Exception as e:
                    # Log but don't fail the call
                    print(f"Database storage failed: {e}")
            
            # Step 3: Make the call
            call_result = self.twilio_service.make_call(request.destination)
            
            return CallResponse(
                ok=True,
                call_sid=call_result["call_sid"],
                to=call_result["to"]
            )
            
        except Exception as e:
            error_message = str(e)
            details = getattr(e, 'details', None)
            
            return CallResponse(
                ok=False,
                error=error_message,
                details=details
            )
