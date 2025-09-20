import json
import asyncio
import websockets
from typing import Optional, Dict, Any
import requests
from datetime import datetime
import uuid

from ..core.config import settings
from ..core.exceptions import OpenAIServiceError
from .openai_service import OpenAIService


class LocalCallSimulator:
    """
    Simulates the entire call flow locally without making actual Twilio calls.
    This allows testing OpenAI Realtime API changes without incurring call costs.
    """
    
    def __init__(self):
        if not settings.openai_api_key:
            raise OpenAIServiceError("OpenAI API key is not configured")
        
        self.openai_service = OpenAIService()
        self.base_url = "https://api.openai.com/v1/realtime"
        self.headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "realtime=v1"
        }
    
    def simulate_call_request(self, name: str, destination: str, prompt: str) -> Dict[str, Any]:
        """
        Simulate the entire call request flow without actually making a Twilio call.
        
        Args:
            name: Name of the caller
            destination: Phone number (for simulation only)
            prompt: The prompt to use for the AI
            
        Returns:
            Simulated call information with WebSocket URL for local testing
        """
        try:
            # Step 1: Enrich the prompt (same as production)
            enriched_prompt = self.openai_service.enrich_prompt(name, prompt)
            
            # Step 2: Create a simulated call ID
            call_id = f"sim_call_{uuid.uuid4().hex[:8]}"
            
            # Step 3: Create OpenAI Realtime session configuration
            session_config = {
                "model": "gpt-4o-realtime-preview-2024-10-01",
                "modalities": ["text", "audio"],
                "instructions": enriched_prompt,
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": [],
                "tool_choice": "auto",
                "temperature": 0.8,
                "max_response_output_tokens": "inf"
            }
            
            return {
                "ok": True,
                "call_id": call_id,
                "simulated": True,
                "destination": destination,
                "enriched_prompt": enriched_prompt,
                "session_config": session_config,
                "local_websocket_url": f"ws://localhost:8000/api/local-call/websocket/{call_id}",
                "openai_websocket_url": "wss://api.openai.com/v1/realtime",
                "created_at": datetime.now().isoformat(),
                "message": "Call simulated locally - use the WebSocket URL to test the conversation"
            }
            
        except Exception as e:
            return {
                "ok": False,
                "error": f"Failed to simulate call: {str(e)}",
                "call_id": None
            }
    
    async def create_openai_realtime_connection(self, session_config: Dict[str, Any]) -> Optional[websockets.WebSocketServerProtocol]:
        """
        Create a connection to OpenAI's Realtime API.
        
        Args:
            session_config: Configuration for the OpenAI session
            
        Returns:
            WebSocket connection to OpenAI or None if failed
        """
        try:
            websocket_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
            
            websocket = await websockets.connect(
                websocket_url,
                extra_headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "OpenAI-Beta": "realtime=v1"
                },
                timeout=10
            )
            
            # Send session configuration
            session_update = {
                "type": "session.update",
                "session": session_config
            }
            
            await websocket.send(json.dumps(session_update))
            
            # Wait for session confirmation
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            
            if response_data.get("type") == "session.updated":
                return websocket
            else:
                await websocket.close()
                return None
                
        except Exception as e:
            print(f"Failed to connect to OpenAI Realtime API: {e}")
            return None
    
    async def relay_websocket_messages(self, client_ws, openai_ws):
        """
        Relay messages between client WebSocket and OpenAI WebSocket.
        
        Args:
            client_ws: WebSocket connection to the local client
            openai_ws: WebSocket connection to OpenAI
        """
        async def client_to_openai():
            try:
                async for message in client_ws:
                    if isinstance(message, str):
                        data = json.loads(message)
                        print(f"Client -> OpenAI: {data.get('type', 'unknown')}")
                        await openai_ws.send(message)
            except websockets.exceptions.ConnectionClosed:
                pass
            except Exception as e:
                print(f"Error relaying client to OpenAI: {e}")
        
        async def openai_to_client():
            try:
                async for message in openai_ws:
                    if isinstance(message, str):
                        data = json.loads(message)
                        print(f"OpenAI -> Client: {data.get('type', 'unknown')}")
                        await client_ws.send(message)
            except websockets.exceptions.ConnectionClosed:
                pass
            except Exception as e:
                print(f"Error relaying OpenAI to client: {e}")
        
        # Run both relay directions concurrently
        await asyncio.gather(
            client_to_openai(),
            openai_to_client(),
            return_exceptions=True
        )
