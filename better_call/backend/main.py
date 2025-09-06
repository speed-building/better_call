import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if present

app = FastAPI(title="Call Backend")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "+18576637141")
TWIML_URL = os.getenv(
    "TWIML_URL",
    "https://handler.twilio.com/twiml/EH0ccb7a1d231ca96f31859460f376465d",
)

class CallRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str  # keep simple (no extra deps); validate upstream if needed
    destination: str = Field(pattern=r"^\+\d{8,15}$")  # E.164 like +5533...
    prompt: Optional[str] = ""

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/call")
def make_call(req: CallRequest):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return JSONResponse(
            {"ok": False, "error": "Missing TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN"}, status_code=500
        )
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=req.destination,
            from_=TWILIO_FROM_NUMBER,
            url=TWIML_URL,
        )
        # req.prompt is captured for future use (e.g., to build dynamic TwiML)
        return {"ok": True, "call_sid": call.sid, "to": req.destination}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
