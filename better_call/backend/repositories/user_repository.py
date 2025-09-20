import sqlite3
import threading
from typing import Optional

import bcrypt

from ..core.exceptions import DatabaseError


class UserRepository:
    """Repository for managing users and credits."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_database()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _initialize_database(self) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        credits INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    '''
                )
                conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to initialize users table: {e}")

    def create_user(self, email: str, password: str) -> int:
        with self.lock:
            try:
                password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "INSERT INTO users (email, password_hash, credits) VALUES (?, ?, ?)",
                        (email, password_hash, 0)
                    )
                    conn.commit()
                    return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"User already exists: {e}")
            except Exception as e:
                raise DatabaseError(f"Failed to create user: {e}")

    def get_user_by_email(self, email: str) -> Optional[dict]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            raise DatabaseError(f"Failed to fetch user: {e}")

    def verify_user(self, email: str, password: str) -> bool:
        user = self.get_user_by_email(email)
        if not user:
            return False
        try:
            return bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8"))
        except Exception:
            return False

    def get_credits(self, email: str) -> int:
        user = self.get_user_by_email(email)
        return int(user["credits"]) if user else 0

    def increment_credit(self, email: str, amount: int = 1) -> None:
        with self.lock:
            try:
                with self._get_connection() as conn:
                    conn.execute(
                        "UPDATE users SET credits = credits + ? WHERE email = ?",
                        (amount, email)
                    )
                    conn.commit()
            except Exception as e:
                raise DatabaseError(f"Failed to increment credits: {e}")

    def decrement_credit(self, email: str) -> bool:
        """Atomically decrement a single credit if available. Returns True if decremented."""
        with self.lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "UPDATE users SET credits = credits - 1 WHERE email = ? AND credits > 0",
                        (email,)
                    )
                    conn.commit()
                    return cursor.rowcount > 0
            except Exception as e:
                raise DatabaseError(f"Failed to decrement credits: {e}")


