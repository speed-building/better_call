import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv

# Load project-level .env before importing modules that read env at import time
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from .database.db import PromptDB
from .backend.main import router as backend_router
from .frontend.main import router as frontend_router
from .backend.openai_gateway.main import router as openai_gateway_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = os.getenv(
        "DB_PATH",
        os.path.join(os.path.dirname(__file__), "banco.db"),
    )
    app.state.db = PromptDB(db_path=db_path)
    try:
        yield
    finally:
        try:
            app.state.db.close()
        except Exception:
            pass


app = FastAPI(title="Better Call - Unified App", lifespan=lifespan)

# Frontend (forms + templates)
app.include_router(frontend_router)

# Backend (Twilio call + saving to DB)
app.include_router(backend_router)

# OpenAI Gateway (consume last prompt and call OpenAI)
app.include_router(openai_gateway_router)


