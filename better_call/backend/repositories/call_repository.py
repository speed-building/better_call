import sqlite3
import threading
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from ..core.exceptions import DatabaseError


class CallRepository:
    """Repository for managing call request data."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database with required tables."""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS call_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        phone_to TEXT NOT NULL,
                        prompt TEXT NOT NULL,
                        user_id INTEGER,
                        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','fulfilled')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # Backward-compatible migration: add user_id column if missing
                try:
                    cursor = conn.execute("PRAGMA table_info(call_requests)")
                    columns = [row[1] for row in cursor.fetchall()]
                    if 'user_id' not in columns:
                        conn.execute("ALTER TABLE call_requests ADD COLUMN user_id INTEGER")
                    if 'status' not in columns:
                        conn.execute("ALTER TABLE call_requests ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")
                except Exception:
                    # Do not fail app startup if pragma/alter fails; table may already be correct
                    pass
                conn.commit()
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def insert_call_request(self, email: str, phone_to: str, prompt: str, user_id: Optional[int] = None, status: str = 'pending') -> int:
        """
        Insert a new call request.
        
        Args:
            email: Email of the requester
            phone_to: Destination phone number
            prompt: The enriched prompt
            
        Returns:
            The ID of the inserted record
            
        Raises:
            DatabaseError: If the insertion fails
        """
        with self.lock:
            try:
                with self._get_connection() as conn:
                    if user_id is not None:
                        cursor = conn.execute(
                            "INSERT INTO call_requests (email, phone_to, prompt, user_id, status) VALUES (?, ?, ?, ?, ?)",
                            (email, phone_to, prompt, user_id, status)
                        )
                    else:
                        cursor = conn.execute(
                            "INSERT INTO call_requests (email, phone_to, prompt, status) VALUES (?, ?, ?, ?)",
                            (email, phone_to, prompt, status)
                        )
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                raise DatabaseError(f"Failed to insert call request: {e}")
    
    def get_last_prompt(self) -> Optional[str]:
        """
        Get the most recent prompt from the database.
        
        Returns:
            The last prompt or None if no records exist
            
        Raises:
            DatabaseError: If the query fails
        """
        with self.lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT prompt FROM call_requests ORDER BY id DESC LIMIT 1"
                    )
                    row = cursor.fetchone()
                    return row["prompt"] if row else None
            except Exception as e:
                raise DatabaseError(f"Failed to get last prompt: {e}")
    
    def get_call_requests(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get call requests with pagination.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of call request dictionaries
            
        Raises:
            DatabaseError: If the query fails
        """
        with self.lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM call_requests ORDER BY id DESC LIMIT ? OFFSET ?",
                        (limit, offset)
                    )
                    return [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                raise DatabaseError(f"Failed to get call requests: {e}")
    
    def get_call_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific call request by ID.
        
        Args:
            request_id: The ID of the call request
            
        Returns:
            Call request dictionary or None if not found
            
        Raises:
            DatabaseError: If the query fails
        """
        with self.lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM call_requests WHERE id = ?",
                        (request_id,)
                    )
                    row = cursor.fetchone()
                    return dict(row) if row else None
            except Exception as e:
                raise DatabaseError(f"Failed to get call request by ID: {e}")

    def get_last_call_request_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent call request for a given email.
        """
        with self.lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM call_requests WHERE email = ? ORDER BY id DESC LIMIT 1",
                        (email,)
                    )
                    row = cursor.fetchone()
                    return dict(row) if row else None
            except Exception as e:
                raise DatabaseError(f"Failed to get last call request by email: {e}")
    
    def close(self):
        """Close any remaining connections. This is a no-op since we use context managers."""
        pass
