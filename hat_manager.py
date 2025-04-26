import os, json, requests, re
import chromadb
from chromadb.config import Settings
import datetime

# Persistent ChromaDB client setup
chroma_client = chromadb.PersistentClient(path="./chromadb_data")

# --- Memory Functions ---

def get_vector_db_for_hat(hat_id):
    return chroma_client.get_or_create_collection(hat_id)

def add_memory_to_hat(hat_id, memory_text, role="user"):
    collection = get_vector_db_for_hat(hat_id)
    timestamp = datetime.datetime.now().isoformat()
    collection.add(
        documents=[memory_text],
        ids=[str(hash(memory_text + timestamp))],
        metadatas=[{"timestamp": timestamp, "role": role}]
    )

def search_memory(hat_id, query, k=3):
    collection = get_vector_db_for_hat(hat_id)
    results = collection.query(query_texts=[query], n_results=k, include=["documents", "metadatas"])
    if not results:
        return []

    docs_list = results.get('documents')
    metas_list = results.get('metadatas')
    if not docs_list or not metas_list or not docs_list[0] or not metas_list[0]:
        return []

    docs = docs_list[0]
    metas = metas_list[0]
    return [(doc, meta) for doc, meta in zip(docs, metas)]

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
    full_prompt = f"Create a Hat identity JSON from this description:\n\n{prompt}\n\nMake sure to include all enhanced fields like role, team_id, flow_order, etc."
    response = llm(full_prompt)

    # Extract JSON from markdown code block (```json ... ```)
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if match:
        cleaned_json = match.group(1)
    else:
        cleaned_json = re.search(r"(\{.*\})", response, re.DOTALL).group(1)

    hat_data = json.loads(cleaned_json)
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

def ollama_llm(prompt, model="llama3:8b"):
    system_message = """You are a helpful assistant that only outputs valid JSON. 
Do not wrap your response in markdown or add explanations.

Expected JSON format:
{
  "hat_id": "summarizer",
  "name": "Article Summarizer",
  "model": "gpt-4",
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

    response = requests.post("http://localhost:11434/api/chat", json={
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
    })

    print("RAW RESPONSE TEXT:", response.text)

    if response.status_code == 200:
        return response.json()["message"]["content"]
    else:
        raise Exception(f"Ollama API Error: {response.status_code} - {response.text}")

# --- CLI Test ---
if __name__ == "__main__":
    prompt = "Make a Hat that acts as a fact-checker for research summaries."
    hat = create_hat_from_prompt(prompt, ollama_llm)
    print(json.dumps(hat, indent=2))
    save_hat(hat["hat_id"], hat)
    print("Saved Hats:", list_hats())