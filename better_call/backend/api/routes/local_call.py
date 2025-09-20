from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Dict, Any, Optional
import json
import asyncio
import uuid

from ...models.requests import CallRequest
from ...models.responses import CallResponse
from ...services.local_call_simulator import LocalCallSimulator
from ...core.exceptions import BetterCallException, OpenAIServiceError

router = APIRouter()

active_sessions: Dict[str, Dict[str, Any]] = {}

@router.post("/local-call/simulate", response_model=CallResponse)
async def simulate_call(request: CallRequest):
    """
    Simulate a call locally without using Twilio.
    This creates a local WebSocket endpoint that connects directly to OpenAI Realtime API.
    """
    try:
        print(f"Simulating call for {request.name} to {request.destination} with prompt {request.prompt}")
        simulator = LocalCallSimulator()
        
        # Simulate the call request
        result = simulator.simulate_call_request(
            name=request.name,
            destination=request.destination,
            prompt=request.prompt or ""
        )
        
        if not result["ok"]:
            return JSONResponse(
                content=CallResponse(
                    ok=False,
                    error=result["error"]
                ).dict(),
                status_code=500
            )
        
        # Store session info for WebSocket connection
        call_id = result["call_id"]
        active_sessions[call_id] = {
            "session_config": result["session_config"],
            "call_info": result,
            "created_at": result["created_at"]
        }
        
        return CallResponse(
            ok=True,
            call_sid=call_id,  # Use our simulated call ID
            to=request.destination,
            details={
                "simulated": True,
                "websocket_url": result["local_websocket_url"],
                "message": "Call simulated locally. Use the WebSocket URL to test the conversation.",
                "instructions": "Open the test interface at /api/local-call/interface to start testing"
            }
        )
        
    except OpenAIServiceError as e:
        return JSONResponse(
            content=CallResponse(
                ok=False,
                error=e.message,
                details=e.details
            ).dict(),
            status_code=500
        )
    except Exception as e:
        return JSONResponse(
            content=CallResponse(
                ok=False,
                error=f"Unexpected error: {str(e)}"
            ).dict(),
            status_code=500
        )


@router.websocket("/local-call/websocket/{call_id}")
async def local_call_websocket(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint that simulates a phone call by connecting to OpenAI Realtime API.
    This replaces the actual phone call with a browser-based interface.
    """
    await websocket.accept()
    
    try:
        # Get session info
        if call_id not in active_sessions:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": f"Call session {call_id} not found. Create a session first using /api/local-call/simulate"
            }))
            return
        
        session_info = active_sessions[call_id]
        session_config = session_info["session_config"]
        
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "call_started",
            "call_id": call_id,
            "message": "Connecting to OpenAI Realtime API...",
            "session_config": session_config
        }))
        
        # Create connection to OpenAI
        simulator = LocalCallSimulator()
        openai_ws = await simulator.create_openai_realtime_connection(session_config)
        
        if not openai_ws:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": "Failed to connect to OpenAI Realtime API"
            }))
            return
        
        # Send connection success
        await websocket.send_text(json.dumps({
            "type": "openai_connected",
            "message": "Connected to OpenAI! You can now start the conversation.",
            "instructions": "Send audio data or text messages to interact with the AI"
        }))
        
        # Relay messages between client and OpenAI
        try:
            await simulator.relay_websocket_messages(websocket, openai_ws)
        finally:
            await openai_ws.close()
            
    except WebSocketDisconnect:
        print(f"Client disconnected from call {call_id}")
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": f"WebSocket error: {str(e)}"
            }))
        except:
            pass
        print(f"WebSocket error in call {call_id}: {e}")
    finally:
        # Clean up session
        if call_id in active_sessions:
            del active_sessions[call_id]




@router.get("/local-call/sessions")
async def list_active_sessions():
    """List all active call sessions for debugging."""
    return {
        "active_sessions": len(active_sessions),
        "sessions": {
            call_id: {
                "created_at": session["created_at"],
                "destination": session["call_info"]["destination"]
            }
            for call_id, session in active_sessions.items()
        }
    }
