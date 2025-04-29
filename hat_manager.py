import os, json, requests, re
import chromadb
from chromadb.config import Settings
import datetime

import chainlit as cl

import json

# Persistent ChromaDB client setup
chroma_client = chromadb.PersistentClient(path="./chromadb_data")

# --- Memory Functions ---

def get_vector_db_for_hat(hat_id):
    return chroma_client.get_or_create_collection(hat_id)

def add_memory_to_hat(hat_id, memory_text, role="user", tags=None, session=None):
    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []

    # Convert to CSV string for Chroma
    tag_string = ",".join(tags) if tags else ""

    collection = get_vector_db_for_hat(hat_id)
    timestamp = datetime.datetime.now().isoformat()
    memory_id = str(hash(memory_text + timestamp))

    collection.add(
        documents=[memory_text],
        ids=[memory_id],
        metadatas=[{"timestamp": timestamp, "role": role, "tags": tag_string}]
    )

    if session:
        session.set("last_memory_id", memory_id)
        session.set("last_memory_hat_id", hat_id)

def search_memory(hat_id, query, k=10, tag_filter=None):
    collection = get_vector_db_for_hat(hat_id)

    # Get ALL memories if k is None
    if k is None:
        total_docs = collection.count()
        if total_docs == 0:
            return []
        k = total_docs

    results = collection.query(
        query_texts=[query],
        n_results=k,
        include=["documents", "metadatas"]
    )

    docs_list = results.get('documents', [[]])[0]
    metas_list = results.get('metadatas', [[]])[0]

    if not docs_list or not metas_list:
        return []

    # Manual filtering on CSV tags until manaul based
    filtered_results = []
    for doc, meta in zip(docs_list, metas_list):
        tags_str = (meta or {}).get('tags', '')
        tags_list = [t.strip() for t in tags_str.split(",") if t] if isinstance(tags_str, str) else []

        if tag_filter is None or tag_filter in tags_list:
            filtered_results.append((doc, meta))

    return filtered_results

def clear_memory(hat_id):
    collection = get_vector_db_for_hat(hat_id)
    all_docs = collection.get()
    if 'ids' in all_docs and all_docs['ids']:
        collection.delete(ids=all_docs['ids'])

# --- Hat Management Functions ---

HAT_DIR = "./hats"

def load_hat(hat_id):
    path = os.path.join(HAT_DIR, f"{hat_id}.json")
    with open(path, "r", encoding="utf-8") as f:  # 💥 Force UTF-8
        return json.load(f)

def save_hat(hat_id, data):
    path = os.path.join(HAT_DIR, f"{hat_id}.json")
    with open(path, "w", encoding="utf-8") as f:  # 💥 Force UTF-8
        json.dump(data, f, indent=2, ensure_ascii=False)  # 💥 Prevent ASCII-only


def list_hats():
    return [f.replace(".json", "") for f in os.listdir(HAT_DIR) if f.endswith(".json")]

# --- LLM-Based Hat Creation ---

def create_hat_from_prompt(prompt, llm):
    # llm() now returns a validated dictionary directly!
    hat_data = llm(prompt)
    return ensure_schema_defaults(hat_data)

def list_hats_by_team(team_id):
    hats = []
    for hat_file in os.listdir(HAT_DIR):
        if hat_file.endswith(".json"):
            hat_path = os.path.join(HAT_DIR, hat_file)
            with open(hat_path, "r", encoding="utf-8") as f:  # 💥 Force UTF-8
                hat_data = json.load(f)
                if hat_data.get("team_id") == team_id and hat_data.get("active", True):
                    hats.append(hat_data)
    # Sort by flow_order
    hats.sort(key=lambda h: h.get("flow_order", 0))
    return hats

# --- Schema Enhancer ---

def ensure_schema_defaults(hat):
    """Ensure all enhanced schema fields exist, with defaults if missing."""
    defaults = {
        "role": "agent",
        "tools": [],
        "relationships": [],
        "team_id": None,
        "flow_order": None,
        "qa_loop": False,
        "critics": [],
        "active": True,
        "memory_tags": [],
        "retry_limit": 1,
        "description": hat.get("instructions", "")
    }
    for key, value in defaults.items():
        hat.setdefault(key, value)
    return hat

# --- Ollama LLM Call ---

def ollama_llm(prompt, model="llama3:8b", max_retries=3):
    system_message = """You are a helpful assistant that only outputs valid JSON.
Do not wrap your response in markdown or add explanations.

Expected JSON format:
{
  "hat_id": "summarizer",
  "name": "Article Summarizer",
  "model": "gpt-3.5-turbo",
  "role": "tool",
  "instructions": "Summarize input text into concise bullet points.",
  "tools": ["summarizer"],
  "relationships": [],
  "team_id": "team_1",
  "flow_order": 2,
  "qa_loop": false,
  "critics": [],
  "active": true,
  "memory_tags": ["summary"],
  "retry_limit": 1,
  "description": "Summarizes text into concise points."
}
"""

    retries = 0
    while retries < max_retries:
        response = requests.post("http://localhost:11434/api/chat", json={
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        })

        if response.status_code == 200:
            content = response.json()["message"]["content"]
            print("RAW RESPONSE TEXT:", content)

            # Extract and validate JSON
            try:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
                if match:
                    cleaned_json = match.group(1)
                else:
                    cleaned_json = re.search(r"(\{.*\})", content, re.DOTALL).group(1)

                hat_data = json.loads(cleaned_json)

                # Quick schema check for critical fields
                required_fields = ["hat_id", "name", "model", "instructions"]
                if all(field in hat_data for field in required_fields):
                    return hat_data  # Success
                else:
                    raise ValueError(f"Missing required fields: {required_fields}")

            except Exception as e:
                print(f"⚠️ JSON Parse/Validation Failed: {e}. Retrying...")
                retries += 1
        else:
            raise Exception(f"Ollama API Error: {response.status_code} - {response.text}")

    raise Exception(f"Failed to get valid JSON after {max_retries} attempts.")

# --- CLI Test ---
if __name__ == "__main__":
    prompt = "Make a Hat that writes poems about the weather."
    hat = create_hat_from_prompt(prompt, ollama_llm)
    print(json.dumps(hat, indent=2))
    save_hat(hat["hat_id"], hat)
    print("Saved Hats:", list_hats())