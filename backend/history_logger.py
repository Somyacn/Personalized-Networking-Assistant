import os
import json
import datetime
from typing import List, Dict, Any

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "history.json")

def _ensure_dir_exists():
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

def log_generation(
    generation_id: str,
    event_description: str,
    user_interests: str,
    themes: List[str],
    starters: List[str]
) -> Dict[str, Any]:
    """Logs a conversation generation to history.json."""
    _ensure_dir_exists()
    
    new_entry = {
        "generation_id": generation_id,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event_description": event_description,
        "user_interests": user_interests,
        "themes": themes,
        "conversation_starters": starters
    }
    
    history = get_history()
    history.insert(0, new_entry)  # Add new entries to the top
    
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing history file: {e}")
        
    return new_entry

def get_history() -> List[Dict[str, Any]]:
    """Retrieves all conversation history."""
    if not os.path.exists(HISTORY_FILE):
        return []
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading history file: {e}")
        return []

def clear_history() -> bool:
    """Clears all conversation history."""
    _ensure_dir_exists()
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return True
    except IOError as e:
        print(f"Error clearing history file: {e}")
        return False
