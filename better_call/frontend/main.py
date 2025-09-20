import os
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
import httpx
from dotenv import load_dotenv


load_dotenv()  # reads frontend/.env if present

router = APIRouter()

# Where to send the API request
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:9001")

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/call", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    destination: str = Form(...),
    prompt: str = Form("")
):
    payload = {"name": name, "email": email, "destination": destination, "prompt": prompt}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Login or register (best-effort simple flow)
            token = None
            try:
                lr = await client.post(f"{BACKEND_BASE_URL}/api/auth/login", json={"email": email, "password": password})
                if lr.status_code == 200:
                    token = lr.json().get("access_token")
                else:
                    rr = await client.post(
                        f"{BACKEND_BASE_URL}/api/auth/register",
                        json={"email": email, "password": password, "initial_credits": 0}
                    )
                    if rr.status_code == 200:
                        token = rr.json().get("access_token")
            except Exception:
                pass

            headers = {"Authorization": f"Bearer {token}"} if token else {}
            r = await client.post(f"{BACKEND_BASE_URL}/api/call", json=payload, headers=headers)
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
            if r.status_code == 401:
                return templates.TemplateResponse(
                    "error.html",
                    {
                        "request": request,
                        "title": "Unauthorized",
                        "details": "Please sign in again.",
                    },
                    status_code=401,
                )
            if r.status_code == 402:
                try:
                    data = r.json()
                    checkout = data.get("details", {}).get("stripe_checkout_url")
                    if checkout:
                        return templates.TemplateResponse(
                            "error.html",
                            {
                                "request": request,
                                "title": "Insufficient credits",
                                "details": {
                                    "message": "Redirecting to checkout...",
                                    "checkout": checkout,
                                },
                            },
                            status_code=402,
                        )
                except Exception:
                    pass
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
