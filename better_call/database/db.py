import sqlite3
import threading
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

class PromptDB:
    def __init__(self, db_path="banco.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.lock = threading.Lock()
        self._criar_tabela()

    def _criar_tabela(self):
        with self.lock:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS call_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    phone_to TEXT NOT NULL,
                    prompt TEXT NOT NULL
                )
            ''')
            
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stripe_payment_link_id TEXT UNIQUE,
                    amount DECIMAL(10,2) NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'usd',
                    status TEXT NOT NULL DEFAULT 'pending',
                    description TEXT,
                    customer_email TEXT,
                    success_url TEXT,
                    cancel_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()

    def insert_call_request(self, email: str, telefone: str, prompt: str):
        with self.lock:
            self.conn.execute(
                "INSERT INTO call_requests (email, phone_to, prompt) VALUES (?, ?, ?)",
                (email, telefone, prompt)
            )
            self.conn.commit()

    def get_last_prompt(self) -> str:
        with self.lock:
            cursor = self.conn.execute(
                "SELECT prompt FROM call_requests ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def insert_payment(self, stripe_payment_link_id: Optional[str], amount: Decimal, currency: str = "usd", 
                      description: Optional[str] = None, customer_email: Optional[str] = None,
                      success_url: Optional[str] = None, cancel_url: Optional[str] = None) -> int:
        """Insert a new payment record and return the payment ID."""
        with self.lock:
            cursor = self.conn.execute(
                """INSERT INTO payments 
                   (stripe_payment_link_id, amount, currency, description, customer_email, success_url, cancel_url) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (stripe_payment_link_id, float(amount), currency, description, customer_email, success_url, cancel_url)
            )
            self.conn.commit()
            return cursor.lastrowid

    def update_payment_status(self, stripe_payment_link_id: str, status: str) -> bool:
        """Update payment status by Stripe payment link ID."""
        with self.lock:
            cursor = self.conn.execute(
                "UPDATE payments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE stripe_payment_link_id = ?",
                (status, stripe_payment_link_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0

    def update_payment_stripe_id(self, payment_id: int, stripe_payment_link_id: str) -> bool:
        """Update payment with Stripe payment link ID by internal payment ID."""
        with self.lock:
            cursor = self.conn.execute(
                "UPDATE payments SET stripe_payment_link_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (stripe_payment_link_id, payment_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0

    def get_payment_by_stripe_id(self, stripe_payment_link_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by Stripe payment link ID."""
        with self.lock:
            cursor = self.conn.execute(
                "SELECT * FROM payments WHERE stripe_payment_link_id = ?",
                (stripe_payment_link_id,)
            )
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None

    def get_payment_by_id(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """Get payment by internal payment ID."""
        with self.lock:
            cursor = self.conn.execute(
                "SELECT * FROM payments WHERE id = ?",
                (payment_id,)
            )
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None

    def close(self) -> None:
        with self.lock:
            try:
                self.conn.close()
            except Exception:
                pass
