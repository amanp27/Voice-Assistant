# db_driver.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path("conversations.db")

class ConversationDB:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    participant_identity TEXT,
                    participant_name TEXT,
                    message_count INTEGER DEFAULT 0,
                    duration_seconds INTEGER DEFAULT 0,
                    transcript TEXT,
                    cost REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)
    
    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def create_conversation(self, session_id, participant_identity="", participant_name=""):
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO conversations (session_id, start_time, participant_identity, participant_name)
                VALUES (?, ?, ?, ?)
            """, (session_id, datetime.now().isoformat(), participant_identity, participant_name))
            return cursor.lastrowid
    
    def add_message(self, conversation_id, role, content):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO messages (conversation_id, timestamp, role, content)
                VALUES (?, ?, ?, ?)
            """, (conversation_id, datetime.now().isoformat(), role, content))
            
            conn.execute("""
                UPDATE conversations 
                SET message_count = message_count + 1
                WHERE id = ?
            """, (conversation_id,))
    
    def end_conversation(self, conversation_id, cost=0.0):
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT start_time FROM conversations WHERE id = ?
            """, (conversation_id,))
            row = cursor.fetchone()
            
            if row:
                start = datetime.fromisoformat(row['start_time'])
                duration = int((datetime.now() - start).total_seconds())
                
                cursor = conn.execute("""
                    SELECT timestamp, role, content FROM messages 
                    WHERE conversation_id = ? ORDER BY timestamp
                """, (conversation_id,))
                
                transcript = "\n".join([
                    f"[{msg['timestamp']}] {msg['role']}: {msg['content']}"
                    for msg in cursor.fetchall()
                ])
                
                conn.execute("""
                    UPDATE conversations 
                    SET end_time = ?, duration_seconds = ?, transcript = ?, cost = ?, status = 'completed'
                    WHERE id = ?
                """, (datetime.now().isoformat(), duration, transcript, cost, conversation_id))
    
    def get_conversation(self, conversation_id):
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM conversations WHERE id = ?
            """, (conversation_id,))
            return dict(cursor.fetchone()) if cursor.fetchone() else None