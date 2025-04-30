# 📈 NEXT STEPS:

### **UI:**
- Form field freezes after first edit (Chainlit issue). Consider a separate service for modifying Hat metadata or continue JSON pasting.( disbaled feature for now due to many changes in the hat schema during this hackathon period)
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