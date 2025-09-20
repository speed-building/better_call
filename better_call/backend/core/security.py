import datetime as dt
from typing import Optional, Tuple

import jwt

from .config import settings


def create_access_token(email: str) -> str:
    now = dt.datetime.utcnow()
    exp = now + dt.timedelta(minutes=settings.jwt_access_token_exp_minutes)
    payload = {"sub": email, "exp": exp, "iat": now}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except Exception:
        return None


