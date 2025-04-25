


- Implemented Chat Logic, tried UI form field. Not effective in chainlit. 
- Added a Chroma Store and DB to each hat based on the hat id



NEXT STEPS:
UI:
    - Form Field freezes after first edit. Probably because of chain lit. Implement a seperate service for modifying the hat meta data or continue pasting the JSON. 
    - Based off the backend. Create a simple calendar app that runs a specific agent at a specific time. Seperate Memory, Seperate instructions/context

Memory Related:
    Bug:
        - Need to give each hat a unique id. I may need a databse or session for this unless you have any other reccomendations.
    Feature:
        - Add metadata tagging (timestamps, categories).
        - Provide UI elements for manual memory management.
        - Support importing/exporting memory snapshots.

Scalability:
    - Add Async AI calling to OPenAI, use a local model, or use Azure AI Foundry. We can also modify the entire backend to use the azure suite. 


Hat Memory System Documentation

Overview

The Hat Memory System integrates local vector databases (ChromaDB) into individual AI agents, known as "Hats". Each Hat maintains its own context and memory, allowing for personalized and contextually aware interactions. This memory system retrieves past interactions relevant to the user's input and injects them into AI prompts, enhancing the agent's responses.

How Memory Works

Per-Hat Vector Store:

Each Hat has a unique vector store implemented using ChromaDB.

Vector stores are managed using collections named after the hat_id.

Memory Retrieval:

When a user sends a message, the system queries the Hat's vector store for similar past interactions.

The top k relevant memories are retrieved using similarity search.

These memories are formatted and injected into the system prompt for OpenAI's language model.

Memory Injection:

Retrieved memories are added as part of the system prompt:

You are an AI agent with the '{hat_name}' persona.

Here are some relevant memories:
- Memory 1
- Memory 2
- Memory 3

This provides context to the model, enhancing response relevance.

Memory Storage:

After every user message and AI response, both are stored in the Hat's vector store.

Each memory is uniquely identified using a hash of its content.

Key Functions

get_vector_db_for_hat(hat_id): Retrieves or creates a ChromaDB collection for the given Hat.

add_memory_to_hat(hat_id, memory_text): Adds a memory entry to the Hat's vector DB.

search_memory(hat_id, query, k=3): Retrieves top k similar memories from the Hat's vector DB.

clear_memory(hat_id): Clears all memories from the Hat's vector DB.

User Commands

view memories:

Displays the top 5 memories for the current Hat.

Uses search_memory(hat_id, "", k=5) to fetch a sample.

clear memories:

Clears all stored memories for the current Hat.

Uses clear_memory(hat_id).

Persistence

ChromaDB uses a persistent directory (./chromadb_data) to ensure that memories are stored across sessions.

Example Flow

User sends a message: "Tell me about AI in healthcare."

System queries relevant memories from the Hat's vector DB.

Injects top 3 relevant memories into the OpenAI prompt.

AI responds.

Both the user message and AI response are stored back into the vector DB for future use.

Future Enhancements

Add metadata tagging (timestamps, categories).

Provide UI elements for manual memory management.

Support importing/exporting memory snapshots.

This memory system enables personalized and evolving AI interactions by ensuring each Hat retains and utilizes past context intelligently.

