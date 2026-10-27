"""Multi-Turn Conversational Session Manager."""

from typing import List, Dict


class SessionManager:
    """Maintains token-limited conversational sliding window per session."""

    def __init__(self, max_history_turns: int = 5):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.max_turns = max_history_turns

    def add_user_message(self, session_id: str, message: str) -> None:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({"role": "user", "content": message})
        self._trim(session_id)

    def add_assistant_message(self, session_id: str, message: str) -> None:
        if session_id in self.sessions:
            self.sessions[session_id].append({"role": "assistant", "content": message})
            self._trim(session_id)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return self.sessions.get(session_id, [])

    def _trim(self, session_id: str) -> None:
        if len(self.sessions[session_id]) > self.max_turns * 2:
            self.sessions[session_id] = self.sessions[session_id][-self.max_turns * 2 :]
