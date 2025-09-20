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

@router.get("/payments/confirmation", response_class=HTMLResponse)
async def payment_confirmation(request: Request):
    payment_id = request.query_params.get("payment_id") or request.cookies.get("payment_id")
    token = request.cookies.get("access_token")
    if not payment_id:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "title": "Missing payment_id", "details": "Payment ID not provided."},
            status_code=400,
        )
    # Poll payment status and trigger call when paid. Simple server-side implementation follows.
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Poll a few times quickly, then show a waiting page otherwise (simplified)
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            status_resp = await client.get(f"{BACKEND_BASE_URL}/payments/status", params={"payment_id": payment_id})
            if status_resp.status_code == 200 and status_resp.json().get("status") == "paid":
                # Fetch last call request
                last_resp = await client.get(f"{BACKEND_BASE_URL}/api/call/last", headers=headers)
                record = None
                if last_resp.status_code == 200:
                    record = last_resp.json().get("record")
                if record:
                    # Trigger the call automatically
                    call_payload = {
                        "name": request.query_params.get("name") or "",
                        "email": record.get("email"),
                        "destination": record.get("phone_to"),
                        "prompt": record.get("prompt") or "",
                    }
                    call_resp = await client.post(f"{BACKEND_BASE_URL}/api/call", json=call_payload, headers=headers)
                    if call_resp.status_code == 200 and call_resp.json().get("ok"):
                        data = call_resp.json()
                        return templates.TemplateResponse(
                            "success.html",
                            {
                                "request": request,
                                "sid": data.get("call_sid", ""),
                                "destination": call_payload["destination"],
                                "name": call_payload["name"],
                                "email": call_payload["email"],
                                "prompt": call_payload["prompt"],
                            },
                        )
            # If not paid yet, render a waiting page with simple auto-refresh
            return HTMLResponse(
                f"""
                <html><head>
                <meta http-equiv='refresh' content='3'>
                <title>Waiting for payment...</title>
                </head><body style='font-family: sans-serif; padding: 24px;'>
                <h2>Waiting for Stripe confirmation...</h2>
                <p>Payment ID: {payment_id}</p>
                <p>This page will refresh automatically.</p>
                </body></html>
                """,
                status_code=200,
            )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "title": "Payment confirmation error", "details": str(e)},
            status_code=500,
        )

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
                    payment_url = data.get("details", {}).get("payment_url") or data.get("payment_url")
                    payment_id = data.get("details", {}).get("payment_id") or data.get("payment_id")
                    if payment_url:
                        # Auto redirect to the payment URL, persisting token so we can confirm later
                        from starlette.responses import RedirectResponse
                        resp = RedirectResponse(url=payment_url, status_code=302)
                        if token:
                            resp.set_cookie("access_token", token, max_age=3600, path="/")
                        if payment_id:
                            resp.set_cookie("payment_id", str(payment_id), max_age=3600, path="/")
                        return resp
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
