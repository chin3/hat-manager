# utils.py
import uuid
from datetime import datetime
import json

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
    import json  # Make sure this is imported

    tags_str = meta.get("tags", "")

    tags_list = []

    if isinstance(tags_str, list):
        tags_list = tags_str
    elif isinstance(tags_str, str):
        tags_str_clean = tags_str.strip()
        if tags_str_clean.startswith("[") and tags_str_clean.endswith("]"):
            try:
                tags_list = json.loads(tags_str_clean)
            except json.JSONDecodeError:
                tags_list = [t.strip() for t in tags_str_clean.strip("[]").split(",") if t]
        elif tags_str_clean:
            tags_list = [t.strip() for t in tags_str_clean.split(",") if t]

    tags_display = f"[Tags: {', '.join(tags_list)}]" if tags_list else ""
    print(f"DEBUG META TAGS: {tags_str} → {tags_list}")
    return f"[{meta.get('timestamp')}][{meta.get('role').capitalize()}] {doc} {tags_display}"