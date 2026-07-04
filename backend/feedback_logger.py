import os
import json
import datetime
from typing import List, Dict, Any

FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "feedback.json")

def _ensure_dir_exists():
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

def log_feedback(generation_id: str, feedback_value: str) -> Dict[str, Any]:
    """Logs user feedback (like/dislike) for a generation_id."""
    if feedback_value not in ("like", "dislike"):
        raise ValueError("Feedback value must be 'like' or 'dislike'")
        
    _ensure_dir_exists()
    
    new_entry = {
        "generation_id": generation_id,
        "feedback": feedback_value,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    # We update if feedback already exists for this generation_id, otherwise insert
    feedbacks = get_feedback()
    updated = False
    
    for entry in feedbacks:
        if entry["generation_id"] == generation_id:
            entry["feedback"] = feedback_value
            entry["timestamp"] = new_entry["timestamp"]
            updated = True
            break
            
    if not updated:
        feedbacks.insert(0, new_entry)
        
    try:
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing feedback file: {e}")
        
    return new_entry

def get_feedback() -> List[Dict[str, Any]]:
    """Retrieves all feedback records."""
    if not os.path.exists(FEEDBACK_FILE):
        return []
    
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading feedback file: {e}")
        return []

def get_feedback_stats() -> Dict[str, Any]:
    """Computes feedback statistics like positive ratio."""
    feedbacks = get_feedback()
    likes = sum(1 for f in feedbacks if f["feedback"] == "like")
    dislikes = sum(1 for f in feedbacks if f["feedback"] == "dislike")
    total = likes + dislikes
    
    return {
        "likes": likes,
        "dislikes": dislikes,
        "total": total,
        "like_ratio": likes / total if total > 0 else 0.0
    }

def clear_feedback() -> bool:
    """Clears all feedback records."""
    _ensure_dir_exists()
    try:
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return True
    except IOError as e:
        print(f"Error clearing feedback file: {e}")
        return False
