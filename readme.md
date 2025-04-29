
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
- Human-in-the-loop QA approval & retry logic

Users can **create, edit, wear**, and **compose Hats** into Teams for orchestrated reasoning tasks.

---

## 🎯 Key Features (Current)

- **Multi-Agent Team Flow**: Chain Hats into teams like `Planner → Summarizer → Critic`.
- **Critic QA Loop**: Agents can retry based on Critic feedback (`#REVISION_REQUIRED` / `#APPROVED`).
- **User Approval**: Manually approve or retry agent output after Critic step.
- **Dynamic Hat Management**:
  - Create Hats from prompts (LLM-powered) or from blank templates.
  - Edit Hats via Chainlit UI or raw JSON.
  - Auto-generate **unique hat_id** per Hat.
- **Per-Hat Vector Memory**:
  - Stores conversations per Hat (with role/timestamp metadata).
  - Memory search & context injection into prompts.
  - Commands: `view memories`, `clear memories`, `export memories <hat_id>`.
- **Scheduled Hat Switching**:
  - Automatically switch Hats at specific times.
- **UI Enhancements**:
  - Sidebar showing Hats, Teams, and TODOs.
  - Wear, Edit, and Schedule Hats via action buttons.
  - JSON view of Hats for easy manual tweaking.
  - [x] **@Mention Hats**: User calls Hats via @name inline. 4/29/2025
  - [x] **Memory Tagging**: Allow tag-based retrieval and filtering. tag last as <tag name>
  - [x] **Agent Reflection**: Agents at the end of critic/qa loop critique and provide feedback and lessons learned. 
  - [x] **Mission Debrief at the end**: Shows agents summary of the conversation at the end
  - [x] **AGENT MVP AWARD**: We must reward our agents for their hard work!

---

## 🛠️ Tech Stack

- **Chainlit**: Frontend for AI interactions.
- **OpenAI API**: LLM backend for responses and team creation.
- **Ollama**: Local LLM for Hat creation.
- **ChromaDB**: Per-Hat memory persistence.
- **Python**: Backend orchestration logic.

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
- Start by typing `help` or use action buttons.

---

## 🧠 Core Concepts

### 🎩 **Hats**:
- Each Hat = a persona/agent.
- Fields: `hat_id`, `name`, `role`, `model`, `instructions`, `tools`, `qa_loop`, etc.
- Manage with: `wear <hat_id>`, `edit <hat_id>`, or action buttons.

### 👥 **Teams**:
- Compose Hats into sequential workflows.
- Auto-generate with: `create team`
- Save and run with: `save team`, `run team <team_id>`

### 🔁 **Critic QA Loop**:
- Critic Hats can trigger retries for prior Hats.
- Retry limits configurable per Hat.
- Supports nested retries + user approval fallback.

---

## 📸 Screenshots & GIFs (Suggested)

1. **🖥️ App UI Overview**  
   _Screenshot:_ Chainlit interface with sidebar + chat.

2. **🎩 Hat Editor UI**  
   _GIF:_ Editing Hat metadata via UI.

3. **👥 Team Flow Example**  
   _GIF:_ Planner → Summarizer → Critic → User approval loop.

4. **🧠 Memory Retrieval**  
   _Screenshot:_ Viewing per-Hat memories.

---

## 📋 Example Team Flow

```bash
run team auto_team_20250426
```

1. **Summarizing Agent**: Generates summary.
2. **Critic Agent**: Reviews, may request retry.
3. **User**: Manually approves or retries if needed.

---

## 📦 Commands Cheat Sheet

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

## 🛣️ Future TODOs (Upcoming)

- [ ] **Import Memories**: JSON/text memory ingestion.
- [ ] **Run Again**: Button to re-run team after approval.
- [ ] **Flow Visualizer**: Mermaid-based visual team editor.
- [ ] **@Mention Hats**: User calls Hats via @name inline.
- [ ] **Tool Integration**: Add real APIs/tools to Hats.
- [ ] **Azure AI Integration**: Copilot SDK, AI Foundry.
- [ ] **Memory Tagging**: Allow tag-based retrieval and filtering.
- [ ] **AutoGen Integration**: Support agent loops + tools.

---

## 🙌 Acknowledgments

- Built for the **Microsoft AI Agents Hackathon**.
- Powered by **Chainlit**, **OpenAI**, **Ollama**, **ChromaDB**.

---

## 📝 License

MIT License — Open to extend and build upon.



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
- Tagging currently is saved as a csv list of strings rather than a list of strings. WIll reformat memory so that the list is just a clean list
- Tagging has become alot more difficult. 
------------------------------------------------------------------------------------------
Absolutely! Here's a clean and professional `README.md` tailored to your GitHub Codespaces + Chainlit + Chroma + Python devcontainer setup:

---

```markdown
# 🧠 Hat Manager – Dev Container Setup

Welcome to the **Hat Manager** project! This repo uses a fully-configured [GitHub Codespaces](https://github.com/features/codespaces) development environment for seamless local or cloud-based Python AI development with **Chainlit**, **ChromaDB**, and **SQLite**.

---

## 🚀 Quick Start (in GitHub Codespaces)

1. Click **`Code > Codespaces > Create codespace on main`**
2. GitHub will:
   - Build a custom container with Python 3.11
   - Install SQLite ≥ 3.35
   - Auto-install all Python dependencies
3. Once it loads, run:
   ```bash
   chainlit run app.py
   ```

That’s it! You’re up and running in a reproducible AI dev environment.

---

## 🛠 DevContainer Overview

This project uses:

- **Python 3.11**
- **Chainlit** – LLM-powered UI framework
- **ChromaDB** – Local vector database
- **SQLite 3.35+** – Required for Chroma
- Fully preinstalled in a custom Codespace container

📁 `.devcontainer/` contains:

- `devcontainer.json` – Config for Codespaces + VS Code
- `Dockerfile` – Installs Python, SQLite, and system deps

---

## 🔍 Key Commands

### 🧪 Run your app:
```bash
chainlit run app.py
```

### 🔎 Check environment:
```bash
python --version
sqlite3 --version
which chainlit
```

### 💾 Install extra dependencies:
Add to your `postCreateCommand` or create a `requirements.txt`.

---

## 🧰 Requirements (if running locally)

To run without Codespaces:
- Python 3.11+
- SQLite ≥ 3.35
- Install dependencies:
  ```bash
  pip install chainlit chromadb
  ```

---

## 🧼 Reset Your Devcontainer

If something breaks:
- From GitHub: **Codespaces → ... → Rebuild Container**
- Or inside Codespaces:
  - `Cmd+Shift+P` (or `F1`) → “Dev Containers: Rebuild Container”

---

## 🤝 Contributing

1. Fork this repo
2. Clone & open in Codespaces
3. Make your changes in `/workspaces/hat-manager`
4. Push to your branch and open a PR

---

## 📦 Future Ideas

- Add `requirements.txt` or `poetry.lock` for more structured dependency control
- Add a frontend layer (React/Tailwind) for a custom Chainlit UI
- Use `start.sh` to auto-launch Chainlit on boot

---

## 💬 Need Help?

Feel free to open an issue or ping [@chin3](https://github.com/chin3) for setup support or ideas!

---
```

---

Would you like a one-liner badge at the top for “Open in GitHub Codespaces”? I can generate the exact markdown for that too.
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


🧢 Hats Project: Mission Flow & QA System
Our AI agent system is structured for clear mission-driven collaboration, with automatic quality control.

✅ Here's how it works:

🎯 Full Team Mission Flow
mermaid
Copy
Edit
flowchart TD
  Start["🎯 Mission Start (Goal Given)"]
  BuildTeam["🧢 Assemble Hats (Storyteller, Critic)"]
  Storyteller["📜 Storyteller Generates Output"]
  Critic["🧑‍⚖️ Critic Reviews Output"]
  RevisionNeeded{❓ Revision Needed?}
  Retry["🔄 Storyteller Retries Based on Feedback"]
  Approve["✅ Critic Approves"]
  Debrief["📜 Generate Mission Debrief"]
  Awards["🏆 Agent Awards Ceremony"]
  Reflections["🎤 Final Agent Reflections"]
  Archive["🗂️ Save Mission Archive (with Reflections)"]
  End["🏁 Mission Complete"]

  Start --> BuildTeam
  BuildTeam --> Storyteller
  Storyteller --> Critic
  Critic --> RevisionNeeded
  RevisionNeeded -- Yes --> Retry
  Retry --> Critic
  RevisionNeeded -- No --> Approve
  Approve --> Debrief
  Debrief --> Awards
  Awards --> Reflections
  Reflections --> Archive
  Archive --> End
🔁 QA Loop Detail (Critic Review and Retry Mechanism)
mermaid
Copy
Edit
flowchart TD
  StartQA["📜 Storyteller Output"]
  CriticQA["🧑‍⚖️ Critic Reviews"]
  RevisionNeededQA{❓ Revision Required?}
  RetryQA["🔄 Storyteller Retries"]
  ReCriticQA["🧑‍⚖️ Critic Re-Reviews"]
  ApprovedQA["✅ Critic Approves"]
  ManualReviewQA["👤 Manual User Review (Approve/Retry)"]

  StartQA --> CriticQA
  CriticQA --> RevisionNeededQA
  RevisionNeededQA -- Yes --> RetryQA
  RetryQA --> ReCriticQA
  ReCriticQA --> RevisionNeededQA
  RevisionNeededQA -- No --> ApprovedQA
  RevisionNeededQA -- No Tag/Error --> ManualReviewQA
🧠 Key System Features:
🎯 Goal-driven Missions: Every team works toward a defined user goal.

👥 Modular Agents (Hats): Each agent has a distinct role (Storyteller, Critic, Planner, etc).

🧠 Autonomous QA: Critic agents enforce quality, retry agents if needed, or request human review.

📜 Mission Logs: Full conversation history is saved.

📜 Mission Debrief: LLM summarizes how the mission went.

🏆 Agent Awards: MVP and Outstanding Contributor are recognized.

🎤 Final Reflections: Each agent shares a short reflection on the mission.

🗂️ Full Archive: Every mission (goal, log, debrief, agent reflections) is archived as a JSON file for history.

✅ This structure creates an autonomous, explainable, memory-enabled AI team —
perfect for future multi-mission orchestration.