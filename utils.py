# utils.py
import uuid
from datetime import datetime

def generate_unique_hat_id(existing_ids):
    while True:
        new_id = f"hat_{uuid.uuid4().hex[:8]}"
        if new_id not in existing_ids:
            return new_id

def current_timestamp():
    """
    Returns the current timestamp in ISO format.
    """
    return datetime.now().isoformat()

def format_memory_entry(doc, meta):
    """
    Formats a memory document and metadata for UI display.
    """
    timestamp = meta.get('timestamp', 'unknown time')
    role = meta.get('role', 'unknown role').capitalize()
    return f"[{timestamp}][{role}] {doc}"