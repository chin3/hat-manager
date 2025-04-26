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

## 📸 Screenshots & GIFs

1. **🖥️ App UI Overview**  
   > _Screenshot:_ Chainlit app with Sidebar, Hat Selector, Chat Interface.

2. **🎩 Hat Editor (UI)**  
   > _GIF or Screenshot:_ Creating/editing a Hat with the form interface.

3. **👥 Team Flow in Action**  
   > _GIF:_ Multi-Hat team running with Summarizer → Critic → Approval loop.

4. **🧠 Memory View**  
   > _Screenshot:_ Top retrieved memories for a Hat.

5. **📊 Flow Visualizer (Planned)**  
   > _Placeholder for Future:_ Visual representation of team flow.

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
- [ ] **Microsoft Copilot SDK** integration for enhanced workflow.

---

## 🙌 Acknowledgments
- Inspired by the **Microsoft AI Agents Hackathon**.
- Powered by **Chainlit**, **OpenAI**, and **Ollama**.

---

## 📝 License
MIT License. Free to use, modify, and extend.

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

### ***LLM Robustness***
- Ollama doesnt generate Unique GUIDS, and currently creates it using a prompt. Need to figure out a better ID and name structure that maintains uniquness for both. 

------------------------------------------------------------------------------------------ 

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

------------------------------------------------------------------------------------------ 
### 📝 **Summary: How to Integrate Critic to Any Agent for Retry Loops**

Here’s a concise step-by-step **guide** on how you integrated the **Critic Agent** with **any Hat** to enable **QA loops** (retry logic), **assuming Critic is hardcoded** for now.

---

## 🎯 **1️⃣ Enable QA Loop for Target Hat**
- In the target Hat's JSON:
  ```json
  "qa_loop": true,
  "critics": ["critic_auto_team_test"]  // Reference to the hardcoded Critic
  ```

---

## 🎯 **2️⃣ Add the Critic Agent to the Team**
- Ensure the **Critic Agent** is also part of the same `team_id`.
- Critic's `flow_order` must come **after** the target Hat it reviews.

---

## 🎯 **3️⃣ Runtime Flow Logic (What Happens Behind the Scenes):**

1. **Run Team Flow**: 
   - Target Hat generates output.
   
2. **Critic Agent Executes**: 
   - Receives **input** from the previous Hat's **output**.
   - Responds with either:
     - **`#APPROVED`** → Flow continues or ends.
     - **`#REVISION_REQUIRED`** → Triggers **retry logic**.

3. **Retry Logic**:
   - Re-executes the **previous Hat** (target Hat).
   - Re-runs the **Critic** on the new output.
   - Retries **up to `retry_limit`**.
   - If still failing, **asks human to approve/retry manually**.

---

## 🛠 **Required Fields in Hat JSON for QA Loop:**
```json
{
  "qa_loop": true,
  "critics": ["critic_auto_team_test"],  // Hardcoded critic for now
  "retry_limit": 2,                      // How many times to retry before asking the user
  "flow_order": 1                        // Must run before the Critic
}
```

---

## 💡 **Key Points to Remember:**
- **Critic Hat** doesn’t need to be dynamic for testing.
  - Just ensure the `hat_id` matches what’s hardcoded in your **logic**.
- **Critic logic** is **generic** — it works for any Hat that opts-in with `qa_loop: true`.
- You can have **multiple Hats** reviewed by **one Critic**, if desired.

---

## ✅ **Why This Works:**
- Hats now support **self-contained QA logic** without needing external logic.
- You can **easily plug** any Hat into this system by:
  - Enabling **`qa_loop`**
  - Adding the **Critic’s ID** to **`critics`**

---

Let me know if you want to automate critic detection or make it more dynamic next! 🔄💡