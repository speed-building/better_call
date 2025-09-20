import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv

# Load project-level .env before importing modules that read env at import time
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Import old database for backward compatibility (will be replaced)
from .database.db import PromptDB
# Import new backend architecture
from .backend.repositories.call_repository import CallRepository
from .backend.core.config import settings
from .backend.api import router as backend_router
from .frontend.main import router as frontend_router
from .backend.openai_gateway.main import router as openai_gateway_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database with new repository pattern
    db_path = settings.db_path
    
    # Keep old DB for backward compatibility with OpenAI gateway
    app.state.db = PromptDB(db_path=db_path)
    
    # Add new repository for improved backend
    app.state.call_repository = CallRepository(db_path=db_path)
    
    try:
        yield
    finally:
        try:
            app.state.db.close()
            app.state.call_repository.close()
        except Exception:
            pass


app = FastAPI(title="Better Call", lifespan=lifespan)

# Frontend (forms + templates)
app.include_router(frontend_router)

# Backend (improved architecture)
app.include_router(backend_router)

# OpenAI Gateway (consume last prompt and call OpenAI)
app.include_router(openai_gateway_router)


