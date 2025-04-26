Got it! Here's the **README.md** content cleanly formatted for direct copy-paste, **without spilling out of the markdown block**:

---

# 🎩 Hat Manager — Multi-Agent AI Orchestration Framework

> **Microsoft AI Agents Hackathon Submission**  
> This project was created as a submission for the [Microsoft AI Agents Hackathon](https://microsoft.github.io/AI_Agents_Hackathon). It demonstrates a modular, human-in-the-loop AI agent system designed for research, summarization, and interactive multi-agent workflows.

---

## 🚀 Overview

**Hat Manager** is a local-first AI orchestration framework where each "Hat" is an independent AI agent with:
- A unique identity (`hat_id`, name, role, model, instructions)
- Its own vector memory (text + context search)
- Custom tools (integrations/extensions)
- Flow logic (for chaining in multi-agent teams)

Users can **create, edit, wear**, and **compose Hats** into Teams for orchestrated reasoning tasks.

---

## 🎯 Key Features
- **Multi-Agent Team Flow**: Chain Hats into teams like `Planner → Summarizer → Critic`.
- **QA Loop with Critic Agent**: Auto-retries based on Critic feedback (`#REVISION_REQUIRED` / `#APPROVED`).
- **Human-in-the-Loop Approval**: After Critic, the user decides to approve or retry output manually.
- **Dynamic Hat Management**:
  - Create Hats from prompts or blank templates.
  - Edit Hats via UI form or JSON.
- **Per-Hat Memory**:
  - Vector-based memory retrieval and context injection.
  - Commands: `view memories`, `clear memories`, `export memories <hat_id>`.
- **UI Enhancements (Chainlit)**:
  - Sidebar with active Hats, Teams, and TODO roadmap.
  - Buttons for quick actions: Wear, Edit, Schedule.

---

## 🛠️ Tech Stack
- **Chainlit**: Frontend for AI interactions.
- **OpenAI API**: LLM backend (supports `gpt-3.5` and `gpt-4`).
- **ChromaDB / Vector Store**: Per-Hat context retrieval.
- **Python**: Backend orchestration logic.
- **Ollama-Ready**: Future-ready for local LLMs.

---

## 🧑‍💻 Usage Guide

### 1. 🔧 Setup
```bash
git clone https://github.com/yourname/hat-manager.git
cd hat-manager
pip install -r requirements.txt
```
- Set your **OpenAI API Key** in `.env`:
```
OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

### 2. ▶️ Run the App
```bash
chainlit run app.py
```
- Visit [http://localhost:8000](http://localhost:8000)
- Start by typing `help` or using sidebar buttons.

---

## 🧠 Core Concepts

### 🎩 **Hats**:
- Represent AI agents with identity + memory.
- Editable JSON or UI form.
- Switch using: `wear <hat_id>`

### 👥 **Teams**:
- Chains of Hats working in sequence.
- Auto-generated via: `create team`
- Run with: `run team <team_id>`

### 🔁 **QA Loop**:
- Critic agent can trigger retry of previous Hat.
- Retry limit controlled per Hat.

### 🧑‍⚖️ **User Approval**:
- After Critic, user decides:
  ```
  Approve or Retry? Type approve or retry.
  ```

---

## 📸 Screenshots (To Add)
- Sidebar showing Hats and Teams
- Team Flow conversation
- Hat Editor UI
- Memory View (Top Memories)

---

## 📋 Example Team Flow
```bash
run team research_team
```
1. **Summarizing Agent**:
   - Generates initial summary based on input.
2. **Critic Agent**:
   - Reviews summary.
   - Tags as `#APPROVED` or `#REVISION_REQUIRED`.
3. **User**:
   - Decides to approve or retry manually.

---

## 📦 Available Commands

| Command                   | Description                                      |
|---------------------------|--------------------------------------------------|
| `wear <hat_id>`           | Load and activate a Hat                         |
| `new blank`               | Create a new empty Hat                          |
| `new from prompt`         | Generate Hat from a description                 |
| `edit <hat_id>`           | Paste updated JSON for a Hat                    |
| `create team`             | Generate a multi-Hat team from a goal           |
| `run team <team_id>`      | Run a multi-agent team flow                     |
| `view memories`           | View recent memories for active Hat             |
| `clear memories`          | Delete all memories for active Hat              |
| `export memories <hat_id>`| Export full memory as JSON                      |
| `set schedule`            | Schedule Hat switching by time                  |
| `view schedule`           | View scheduled Hat switches                     |
| `current hat`             | Show current active Hat                         |
| `save team`               | Save proposed team to disk                      |
| `show team json`          | View raw JSON for proposed team                 |

---

## 🛣️ Future TODOs
- [ ] **Import Memories** from JSON or text files.
- [ ] **Run Again / Create New Team** buttons post-flow.
- [ ] **Flow Visualizer** for graphical team composition.
- [ ] **Tool Integration**: Add custom tool-enabled agents.
- [ ] **AutoGen / Microsoft AI Foundry** compatibility layers.

---

## 🙌 Acknowledgments
- Inspired by the **Microsoft AI Agents Hackathon**.
- Powered by **Chainlit**, **OpenAI**, and **Ollama**.

---

## 📝 License
MIT License. Free to use, modify, and extend.

---

You can now copy this cleanly for your README.md file! Let me know if you'd like to save it as a file next.

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


Multi Agent Orchestration
{
    "hat_id": "fact_checker",
    "name": "Research Summary Fact-Checker",
    "model": "gpt-4",
    "role": "tool",
    "instructions": "Verify the accuracy of research summaries by cross-checking against credible sources.",
    "tools": [
      "fact_checker"
    ], 
    "relationships": [], // TODO: Implement relationship-based agent handoffs (e.g., this Hat works directly with summarizer Hat)
    "team_id": "team_1", // TODO: Use team_id to coordinate multi-agent flows, e.g., filter agents by team during execution
    "flow_order": 3, // TODO: Enforce this execution order in your multi-agent pipeline (planner → summarizer → fact_checker)
    "qa_loop": false, // TODO: If true, allow this Hat to loop back for QA/fix suggestions before finalizing output
    "critics": [], // TODO: Add IDs of critic Hats that should review this Hat's output (auto-trigger feedback loops)
    "active": true, // TODO: Use this to toggle whether a Hat participates in flows without deleting the file
    "memory_tags": [
      "summary",
      "fact_checking"
    ], // TODO: Tag stored memories with these categories for better search/filtering during memory retrieval
    "retry_limit": 2, // TODO: After failed outputs, allow up to 2 retries (based on critic feedback or validation rules)
    "description": "Fact-checks research summaries against credible sources."
  }