from typing import List, Dict, Optional
from datetime import datetime
from config import MAX_HISTORY_LENGTH
import json
import os


class ChatManager:
    def __init__(self):
        self.history: List[Dict] = []
        self.current_session_id: Optional[str] = None

    def new_session(self, url: str):
        """Start a new chat session"""
        self.current_session_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(url)}"
        self.history = []
        self._add_system_message(f"New session started for {url}")

    def _add_system_message(self, message: str):
        """Add system message to history"""
        self.history.append({
            "role": "system",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

    def add_message(self, role: str, content: str, sources: List[str] = None):
        """Add message to history"""
        if len(self.history) >= MAX_HISTORY_LENGTH:
            self.history.pop(0)  # Remove oldest message

        self.history.append({
            "role": role,
            "content": content,
            "sources": sources or [],
            "timestamp": datetime.now().isoformat()
        })

    def get_formatted_history(self, for_display: bool = True):
        """Get history in Gradio format"""
        if for_display:
            return [(msg["content"], None) if msg["role"] == "user"
                    else (None, msg["content"])
                    for msg in self.history if msg["role"] in ["user", "assistant"]]
        return self.history

    def save_session(self):
        """Save current session to file"""
        if not self.current_session_id:
            return

        os.makedirs("chat_sessions", exist_ok=True)
        with open(f"chat_sessions/{self.current_session_id}.json", "w") as f:
            json.dump({
                "history": self.history,
                "created_at": datetime.now().isoformat()
            }, f)

    def load_session(self, session_id: str):
        """Load session from file"""
        try:
            with open(f"chat_sessions/{session_id}.json", "r") as f:
                data = json.load(f)
                self.history = data["history"]
                self.current_session_id = session_id
        except FileNotFoundError:
            self.new_session("New Chat")

    def update_last_message(self, role: str, content: str):
        """Update the last message in history"""
        if self.history:
            self.history[-1] = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }