import uuid
from typing import Dict, List, Optional
from app.config import logger

# Context history in-memory storage
chat_history: Dict[str, List[dict]] = {}

def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Retrieves an existing session ID or creates a new one with a default system prompt."""
    if not session_id or session_id not in chat_history:
        session_id = session_id or str(uuid.uuid4())
        chat_history[session_id] = [
            {"role": "system", "content": "You are a helpful assistant"}
        ]
        logger.info(f"Created new chat session: {session_id}")
    return session_id

def add_user_message(session_id: str, message: str):
    """Appends a new user message to the context."""
    chat_history[session_id].append({"role": "user", "content": message})

def create_empty_assistant_entry(session_id: str) -> dict:
    """
    Creates an empty assistant message entry in the history list.
    Returns a direct reference to the dictionary so it can be updated
    in real-time during streaming.
    """
    entry = {"role": "assistant", "content": ""}
    chat_history[session_id].append(entry)
    return entry