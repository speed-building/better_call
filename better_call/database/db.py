import sqlite3
import threading

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

    def close(self) -> None:
        with self.lock:
            try:
                self.conn.close()
            except Exception:
                pass
