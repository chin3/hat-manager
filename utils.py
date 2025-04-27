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

   # tags_display = f"[Tags: {', '.join(tags_list)}]" if tags_list else ""
    print(f"DEBUG META TAGS: {tags_str} → {tags_list}")
    
    tags_display = format_tags_for_display(meta.get("tags", []))
    tags_str = f"[Tags: {tags_display}]" if tags_display else ""
    return f"[{meta.get('timestamp')}][{meta.get('role').capitalize()}] {doc} {tags_str}"

#TAG UTILS
def merge_tags(existing, new_tags):
    # Ensure both are lists
    if isinstance(existing, str):
        if existing.strip().startswith("["):
            try:
                existing = json.loads(existing)
            except:
                existing = [t.strip() for t in existing.split(",") if t]
        else:
            existing = [t.strip() for t in existing.split(",") if t]
    elif not isinstance(existing, list):
        existing = []

    if isinstance(new_tags, str):
        new_tags = [new_tags]
    elif not isinstance(new_tags, list):
        new_tags = []

    merged = list(set(existing + new_tags))
    return merged

def format_tags_for_display(tags):
    if isinstance(tags, str):
        if tags.strip().startswith("["):
            try:
                tags = json.loads(tags)
            except:
                tags = [t.strip() for t in tags.split(",") if t]
        else:
            tags = [t.strip() for t in tags.split(",") if t]
    elif not isinstance(tags, list):
        tags = []

    return ", ".join(tags)