import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
import httpx
from dotenv import load_dotenv

load_dotenv()  # reads frontend/.env if present

app = FastAPI(title="Call Frontend")

# Where to send the API request
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:9001")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/call", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    destination: str = Form(...),
    prompt: str = Form("")
):
    payload = {"name": name, "email": email, "destination": destination, "prompt": prompt}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{BACKEND_BASE_URL}/api/call", json=payload)
        if r.status_code == 200:
            data = r.json()
            if data.get("ok"):
                return templates.TemplateResponse(
                    "success.html",
                    {
                        "request": request,
                        "sid": data.get("call_sid", ""),
                        "destination": destination,
                        "name": name,
                        "email": email,
                        "prompt": prompt,
                    },
                )
            else:
                return templates.TemplateResponse(
                    "error.html",
                    {"request": request, "title": "Backend Error", "details": data},
                    status_code=500,
                )
        else:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "title": "HTTP Error",
                    "details": f"Status: {r.status_code}\n{r.text}",
                },
                status_code=r.status_code,
            )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "title": "Exception", "details": str(e)},
            status_code=500,
        )
