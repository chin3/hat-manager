import os, json, requests, re


import chromadb
from chromadb.config import Settings

import datetime

#Persistent ChromaDB client setup\
# Ensure the chromadb_data directory exists
chroma_client = chromadb.PersistentClient(path="./chromadb_data")

#non persistent in-memory client setup
# chroma_client = chromadb.EphemeralClient()


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
    # Retrieve all document IDs in the collection
    all_docs = collection.get()
    if 'ids' in all_docs and all_docs['ids']:
        collection.delete(ids=all_docs['ids'])


HAT_DIR = "./hats"



def load_hat(hat_id):
    path = os.path.join(HAT_DIR, f"{hat_id}.json")
    with open(path, "r") as f:
        return json.load(f)

def save_hat(hat_id, data):

    path = os.path.join(HAT_DIR, f"{hat_id}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def list_hats():
    return [f.replace(".json", "") for f in os.listdir(HAT_DIR) if f.endswith(".json")]

def create_hat_from_prompt(prompt, llm):
    full_prompt = f"Create a Hat identity JSON from this description:\n\n{prompt}"
    response = llm(full_prompt)

    # Extract JSON from markdown code block (```json ... ```)
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if match:
        cleaned_json = match.group(1)
    else:
        # Fallback: try to find the first valid JSON-looking chunk
        cleaned_json = re.search(r"(\{.*\})", response, re.DOTALL).group(1)

    return json.loads(cleaned_json)

def ollama_llm(prompt, model="llama3:8b"):
    system_message = """You are a helpful assistant that only outputs valid JSON. 
Do not wrap your response in markdown or add explanations.

Here is the expected JSON format:

{
  "hat_id": "summarizer",
  "name": "Article Summarizer",
  "model": "gpt-4",
  "instructions": "Summarize input text into concise bullet points.",
  "tools": ["summarizer"],
  "relationships": ["researcher"]
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

if __name__ == "__main__":
    #HatFactoryTemplate "AI Generated Hat Framework"
    prompt = "Make a Hat that plans and can reach out to a summarizer"
    
    hat = create_hat_from_prompt(prompt, ollama_llm)
    print(json.dumps(hat, indent=2))
    save_hat(hat["hat_id"], hat)
    print(list_hats())
    #Next Steps 