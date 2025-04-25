# 🎩 Hat Manager – Multi-Agent AI Framework

Hat Manager is a **modular AI agent orchestration framework** built on **Chainlit**, designed for flexible persona-based interactions with **per-agent memory**, **dynamic scheduling**, and a **custom UI** for editing agent behavior.

---

## 🚀 Features

- **🎩 Hats**: Define unique AI personas ("Hats") with specific instructions, tools, and models.
- **🧠 Memory**: Each Hat stores past interactions in a local vector database (ChromaDB).
- **🗕️ Scheduling**: Automatically switch Hats based on a time-based schedule.
- **🛠️ Custom UI**: Intuitive React interface to edit Hat settings (model, tools, relationships).
- **💡 LLM-Generated Hats**: Create new Hats dynamically from a description using Ollama LLM.
- **⚡ Chainlit Integration**: Real-time, conversational AI with embedded UI elements.

---

## 📂 Project Structure

```
├── app.py               # Main Chainlit app logic
├── hat_manager.py       # Handles Hat storage, memory, LLM interaction
├── hats/                # Folder storing individual Hat JSON files
├── chromadb_data/       # Persistent vector memory storage for each Hat
├── components/
│   └── TestComponent.jsx  # React UI for editing Hats in real-time
├── .gitignore
├── README.md
```

---

## 🔧 Setup Instructions

1. **Clone the Repo**
   ```bash
   git clone https://github.com/your-username/hat-manager.git
   cd hat-manager
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node Dependencies (for Custom UI)**
   ```bash
   cd components
   npm install
   ```

4. **Start Ollama (Local LLM Backend)**
   Ensure Ollama is running locally (default port `11434`):
   ```bash
   ollama serve
   ```

5. **Run Chainlit App**
   ```bash
   chainlit run app.py
   ```

---

## ⚙️ Key Commands (Chat Interface)

| Command            | Description                                      |
|--------------------|--------------------------------------------------|
| `new blank`        | Create an empty Hat                              |
| `new from prompt`  | Generate a Hat from a natural language prompt    |
| `wear <hat_id>`    | Activate a specific Hat                          |
| `edit <hat_id>`    | Edit a Hat via JSON                              |
| `view memories`    | Show top memory entries for the current Hat      |
| `clear memories`   | Clear all memories for the current Hat           |
| `set schedule`     | Schedule a Hat to activate at a certain time     |
| `view schedule`    | List all scheduled Hat switches                  |
| `current hat`      | Show which Hat is currently active               |
| `debug memories`   | Raw debug output of all stored memories          |

---

## 🛠️ Editing Hats with Custom UI

1. After wearing a Hat, click **Edit This Hat (UI)**.
2. Modify the **name**, **model**, **instructions**, **tools**, and **relationships**.
3. Save changes live via the embedded React interface.

---

## 🧠 Memory System

- ChromaDB stores interaction history **per Hat**.
- Automatically fetches **contextual memories** when responding.
- Memories can be **viewed**, **cleared**, or **searched**.

---

## 🗕️ Scheduling Logic

- Schedule Hats to activate at specific **HH:MM** times.
- Auto-switches Hats during conversation based on schedule.
- **Future**: Support for **recurring schedules**, **calendar UI**, or **API sync**.

---

## 🔗 Future Enhancements

- Full **calendar widget** for managing schedules visually.
- Integration with **Google Calendar** or **Notion Calendar**.
- Advanced **multi-Hat team collaboration** flows.
- Persistent **user-level settings** and **Hat sharing**.

---

## 📜 License

MIT License – free for personal and commercial use.

---

## 🙌 Credits

- Built with [Chainlit](https://www.chainlit.io/), [ChromaDB](https://www.trychroma.com/), and [Ollama](https://ollama.com/).
- UI powered by **React + Tailwind** via **Chainlit Custom Components**.

---

# 📝 NOTES:

- Implemented Chat Logic, tried UI form field. Not fully effective in Chainlit.
- Added a Chroma Store and DB to each Hat based on the `hat_id`.

---

# 📈 NEXT STEPS:

### **UI:**
- Form field freezes after first edit (Chainlit issue). Consider a separate service for modifying Hat metadata or continue JSON pasting.
- Build a simple calendar app to run specific agents at specific times with separate memory and context.

### **Memory Related:**
- **Bug**: Each Hat needs a **unique ID**. Consider a DB or session strategy.
- **Feature**:
  - Add **metadata tagging** (timestamps, categories).
  - Provide UI for **manual memory management**.
  - Support **import/export** of memory snapshots.

### **Scalability:**
- Add **Async AI calling** to OpenAI or local models.
- Explore **Azure AI Foundry** or full backend migration to Azure.

---

# 🧠 Hat Memory System Documentation

### **Overview**
The Hat Memory System integrates local vector databases (ChromaDB) into individual AI agents, known as "Hats". Each Hat maintains its own context and memory, allowing for personalized and contextually aware interactions.

### **How Memory Works**

- **Per-Hat Vector Store**:
  - Each Hat has a unique vector store using ChromaDB.
  - Collections named after `hat_id`.

- **Memory Retrieval**:
  - Queries Hat’s vector store for similar past interactions.
  - Top **k** relevant memories retrieved and injected into system prompt.

- **Memory Injection**:
  ```
  You are an AI agent with the '{hat_name}' persona.

  Here are some relevant memories:
  - Memory 1
  - Memory 2
  - Memory 3
  ```

- **Memory Storage**:
  - After every message, both **user input** and **AI response** are stored.

### **Key Functions**
- `get_vector_db_for_hat(hat_id)`
- `add_memory_to_hat(hat_id, memory_text)`
- `search_memory(hat_id, query, k=3)`
- `clear_memory(hat_id)`

### **User Commands**
- `view memories`
- `clear memories`

### **Persistence**
- ChromaDB uses `./chromadb_data` for session persistence.

---

### **Example Flow**
1. User sends: **"Tell me about AI in healthcare."**
2. System queries past memories.
3. Injects top 3 into the prompt.
4. AI responds.
5. Both message & response stored for future queries.

---

### **Future Enhancements**
- Add **metadata tagging**.
- Provide UI for manual memory control.
- Support **memory snapshot import/export**.

> This memory system enables **personalized and evolving AI** by ensuring each Hat retains and utilizes past context intelligently.

