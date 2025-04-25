import json
import chainlit as cl
from chainlit.input_widget import TextInput, Select, Tags # Keep only one import
from chainlit.element import Text # Explicit imports can be clearer
from chainlit.action import Action # Explicit import
import re

from datetime import datetime

from hat_manager import get_vector_db_for_hat, search_memory, add_memory_to_hat, clear_memory

import openai

import os
from dotenv import load_dotenv

load_dotenv()
# Set your OpenAI API key
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ensure hat_manager.py exists and provides these functions/objects
# It should handle file operations, LLM calls, etc.
try:
    from hat_manager import (
        list_hats,
        load_hat,
        save_hat,
        create_hat_from_prompt,
        ollama_llm # Assuming this is your LLM instance
    )
except ImportError:
    print("Error: Could not import from hat_manager.py.")
    print("Please ensure hat_manager.py exists and provides necessary functions.")
    # You might want to exit or handle this more gracefully in a real app
    list_hats = lambda: []
    load_hat = lambda hat_id: {"hat_id": hat_id, "name": "Error Hat", "instructions": "Could not load hat_manager.py"}
    save_hat = lambda hat_id, hat: None
    create_hat_from_prompt = lambda prompt, llm: {"hat_id": "error", "name": "Error Hat"}
    ollama_llm = None
    



@cl.on_chat_start
async def main():
    """
    Main entry point for the chat. Sets up the UI and initial state.
    """
    # Initialize session state flags
    cl.user_session.set("editing_hat_id", None) # Tracks the currently active/target hat ID
    cl.user_session.set("awaiting_json_paste", False) # Tracks if waiting for JSON paste
    cl.user_session.set("awaiting_hat_prompt", False) # Tracks if waiting for new hat description

    await show_hat_sidebar()
    await show_hat_selector()
    await cl.Message(content="👋 Welcome! Select a Hat, use commands, or type `help`.").send()

# --- UI Update Functions ---

async def show_hat_sidebar():
    """
    Displays available Hats and commands in the sidebar.
    """
    hats = list_hats()
    elements = [Text(content="### 🎩 Hats")]

    if hats:
        for hat in hats:
            elements.append(Text(content=f"- `wear {hat}`"))
    else:
        elements.append(Text(content="_(No hats found yet)_"))

    elements += [
        Text(content="---"),
        Text(content="### ➕ Create"),
        Text(content="- `new blank` — Empty Hat"),
        Text(content="- `new from prompt` — Describe"),
        Text(content="---"),
        Text(content="### ✏️ Edit Active Hat"),
        Text(content="- `edit <hat_id>` — Start JSON edit"),
        Text(content="- *Use button after wearing*"),
        Text(content="---"),
        Text(content="### 🧠 Memory"),
        Text(content="- `view memories` — Show top memories"),
        Text(content="- `clear memories` — Delete all memories"),
        Text(content="- `debug memories` — Raw memory debug"),
        Text(content="---"),
        Text(content="### 🕒 Scheduling"),
        Text(content="- `set schedule` — Schedule Hat switching"),
        Text(content="- `view schedule` — View all schedules"),
        Text(content="- `current hat` — Show active Hat"),
        Text(content="---"),
        Text(content="### ℹ️ Other"),
        Text(content="- `help` — Show commands"),
    ]

    await cl.ElementSidebar.set_elements(elements)
    await cl.ElementSidebar.set_title("Hat Manager")

async def show_hat_selector():
    """
    Displays dynamic action buttons in chat to wear hats.
    """
    hats = list_hats()
    if not hats:
        return

    # Create actions, putting the hat_id into the payload
    actions = [
        Action(
            name="wear_hat_button",
            label=hat,                 # Text displayed on the button
            # value=hat,               # Remove or comment out - not used in callback
            payload={"hat_id": hat}    # Put the hat ID into the payload dictionary
        ) for hat in hats
    ]

    await cl.Message(
        content="🎩 Select a Hat to wear:",
        actions=actions
    ).send()
# --- Action Callbacks (Button Clicks & Custom UI Events) ---

@cl.action_callback("wear_hat_button")
async def wear_hat_action_button(action: Action):
    """Handles clicks on the 'wear hat' buttons."""
    # Retrieve hat_id from the payload dictionary using .get for safety
    hat_id = action.payload.get("hat_id")

    if not hat_id:
        # Handle case where payload might be missing the key
        await cl.Message(content="❌ Error: Could not retrieve hat_id from action payload.").send()
        return

    # hat_id = action.value # <<< This line caused the AttributeError

    # Proceed with the retrieved hat_id
    await wear_hat(hat_id)

@cl.action_callback("edit_hat_ui")
async def edit_hat_action_ui(action: Action):
    """Handles click on the 'Edit This Hat' button, showing the custom UI."""
    hat_id = action.payload.get("hat_id")
    if not hat_id:
        await cl.Message(content="❌ Error: Missing hat_id in edit action payload.").send()
        return

    try:
        hat = load_hat(hat_id)
        if hat is None:
            await cl.Message(content=f"❌ Error: Could not load hat with ID '{hat_id}'.").send()
            return

        print(f"Hat data being passed as props (JSON encoded): {json.dumps(hat)}")

        await cl.Message(
            content="Testing basic HatEditor:",
            elements=[
                cl.CustomElement(
                    name="TestComponent",
                    display="inline",
                    props=hat
                )
            ]
        ).send()
    except Exception as e:
        await cl.Message(content=f"❌ Error loading hat '{hat_id}' for UI editing: {e}").send()


@cl.action_callback("save_hat")
async def save_hat_action_ui(action: Action):
    """
    Handles the 'save_hat' action emitted by the custom HatEditor UI component.
    """
    updated_hat = action.payload # Assumes payload is the complete updated hat dictionary
    print(f"Received updated hat from UI: {updated_hat}")
    hat_id = updated_hat.get("hat_id")

    if not hat_id or not isinstance(updated_hat, dict):
        await cl.Message(content="❌ Error: Invalid payload received from Hat Editor.").send()
        return

    try:
        save_hat(hat_id, updated_hat)
        cl.user_session.set("current_hat", updated_hat) # Update session
        cl.user_session.set("editing_hat_id", hat_id) # Keep track of active hat
        await cl.Message(content=f"✅ Hat '{updated_hat.get('name', hat_id)}' updated via UI.").send()
        await cl.Message(
    content="✅ Hat saved. Here’s the updated version for further edits:",
    elements=[
        cl.CustomElement(name="TestComponent", id="hat_editor", props=updated_hat, display="inline")
    ]
).send()
        await show_hat_sidebar() # Refresh sidebar
        await show_hat_selector() # Refresh buttons
    except Exception as e:
        await cl.Message(content=f"❌ Error saving hat '{hat_id}' from UI: {e}").send()
        
@cl.action_callback("save_schedule")
async def save_schedule_action(action: cl.Action):
    time_str = action.inputs.get("schedule_time")
    hat_id = action.inputs.get("schedule_hat")

    if time_str and hat_id:
        schedule = cl.user_session.get("hat_schedule", {})
        schedule[time_str] = hat_id
        cl.user_session.set("hat_schedule", schedule)

        await cl.Message(content=f"✅ Scheduled Hat `{hat_id}` for `{time_str}`!").send()
    else:
        await cl.Message(content="❌ Please provide both a time and a hat.").send()

@cl.action_callback("hat_selection")
async def handle_hat_selection(action: cl.Action):
    selected_hat = action.value
    schedule_time = cl.user_session.get("schedule_time_temp")

    if selected_hat and schedule_time:
        schedule = cl.user_session.get("hat_schedule", {})
        schedule[schedule_time] = selected_hat
        cl.user_session.set("hat_schedule", schedule)

        await cl.Message(content=f"✅ Scheduled Hat `{selected_hat}` for `{schedule_time}`!").send()
    else:
        await cl.Message(content="❌ Failed to schedule. Try again.").send()


# --- Core Logic Functions ---

async def wear_hat(hat_id: str):
    """Loads a hat, sets it as active in the session, and informs the user."""
    try:
        hat = load_hat(hat_id)
        cl.user_session.set("current_hat", hat)
        cl.user_session.set("editing_hat_id", hat_id) # Set this hat as the active/target one
        cl.user_session.set("awaiting_json_paste", False) # Reset JSON paste flag when wearing anew
        cl.user_session.set("awaiting_hat_prompt", False) # Reset prompt flag
        await cl.Message(
            content=(
                f"🧢 Now wearing: `{hat.get('name', hat_id)}`\n\n"
                f"To edit this Hat, you can:\n"
                f"• Type `edit {hat_id}` then paste JSON\n"
                f"• Click the **Edit This Hat** button below"
            ),
            actions=[
                Action(
                    name="edit_hat_ui", # Matches the callback name
                    label="📝 Edit This Hat (UI)",
                    value="edit", # Value isn't strictly needed if using payload
                    payload={"hat_id": hat_id} # Send hat_id to the callback
                )
            ]
        ).send()

        # Don't necessarily need to show selector again immediately after wearing,
        # but can be useful if the list is long. Comment out if too noisy.
        # await show_hat_selector()

    except FileNotFoundError:
        await cl.Message(content=f"❌ Error: Hat file for `{hat_id}` not found.").send()
    except Exception as e:
        await cl.Message(content=f"❌ Couldn't load hat `{hat_id}`: {e}").send()

async def create_blank_hat():
    """Creates and saves a new, empty hat."""
    # Find a unique ID (e.g., new_hat_1, new_hat_2)
    i = 1
    hat_id = "new_hat"
    hats = list_hats()
    while hat_id in hats:
        hat_id = f"new_hat_{i}"
        i += 1

    blank = {
        "hat_id": hat_id,
        "name": f"New Hat {i-1 if i>1 else ''}".strip(),
        "model": "default", # Or get from config
        "instructions": "",
        "tools": [],
        "relationships": []
    }
    try:
        save_hat(blank["hat_id"], blank)
        await cl.Message(content=f"📄 Blank Hat `{blank['hat_id']}` created. You can now `wear {blank['hat_id']}`.").send()
        await show_hat_sidebar()
        await show_hat_selector()
    except Exception as e:
        await cl.Message(content=f"❌ Failed to save blank hat: {e}").send()

async def ask_for_prompt():
    """Prompts the user to describe the hat they want to create."""
    cl.user_session.set("awaiting_hat_prompt", True)
    cl.user_session.set("awaiting_json_paste", False) # Ensure other states are off
    await cl.Message(content="🪄 Describe the new Hat you want to create (e.g., `A helpful assistant that can summarize text`).").send()

async def handle_prompt(message: cl.Message):
    """Handles the user's description to create a hat using an LLM."""
    cl.user_session.set("awaiting_hat_prompt", False) # Consume the flag
    prompt_content = message.content

    if not ollama_llm:
         await cl.Message(content=f"❌ Cannot create from prompt: LLM (ollama_llm) is not configured.").send()
         return

    try:
        # Show thinking indicator
        thinking_msg = cl.Message(content="⚙️ Creating Hat from your description...")
        await thinking_msg.send()

        hat = create_hat_from_prompt(prompt_content, ollama_llm) # External function call

        # Basic validation
        if not hat or not hat.get("hat_id") or not hat.get("name"):
             raise ValueError("LLM did not return a valid hat structure.")

        save_hat(hat["hat_id"], hat)

        await thinking_msg.update(content=f"✅ Created Hat: `{hat['name']}` (ID: `{hat['hat_id']}`). You can now `wear {hat['hat_id']}`.")
        await show_hat_sidebar()
        await show_hat_selector()
    except Exception as e:
        await cl.Message(content=f"❌ Failed to create Hat from prompt: {e}").send()


async def save_edited_json(message: cl.Message, hat_id_to_edit: str):
    """Parses pasted JSON, validates, and saves the hat."""
    try:
        updated_hat = json.loads(message.content)

        if not isinstance(updated_hat, dict):
            raise TypeError("Pasted content is not a valid JSON object.")

        # --- Validation ---
        pasted_hat_id = updated_hat.get("hat_id")
        if not pasted_hat_id:
            raise ValueError("Pasted JSON is missing the 'hat_id' key.")

        if pasted_hat_id != hat_id_to_edit:
            await cl.Message(content=f"❌ Mismatch: You are editing `{hat_id_to_edit}`, but the pasted JSON has `hat_id`: `{pasted_hat_id}`. Paste the correct JSON.").send()
            return # Keep awaiting_json_paste as True

        # --- Save ---
        save_hat(hat_id_to_edit, updated_hat)
        cl.user_session.set("current_hat", updated_hat) # Update active hat in session
        # Keep editing_hat_id pointing to the current hat
        await cl.Message(content=f"✅ Hat `{hat_id_to_edit}` updated from pasted JSON.").send()
        await show_hat_sidebar() # Refresh UI
        await show_hat_selector()

    except json.JSONDecodeError as e:
        await cl.Message(content=f"❌ Invalid JSON: {e}. Please paste valid JSON content.").send()
        # Keep awaiting_json_paste as True, let user try again
    except Exception as e:
        await cl.Message(content=f"❌ Error saving updated hat `{hat_id_to_edit}`: {e}").send()
        # Optionally reset awaiting_json_paste here if the error is unrecoverable
        # cl.user_session.set("awaiting_json_paste", False)


def generate_openai_response(prompt: str, hat_name: str, hat_id: str):
    memory_context = ""
    relevant_memories = search_memory(hat_id, prompt, k=3)
    if relevant_memories:
        formatted = "\n".join([
            f"{meta['role'].capitalize()} ({meta['timestamp']}): {doc}"
            for doc, meta in relevant_memories
        ])
        memory_context = f"\n\nHere are some relevant memories:\n{formatted}"
    else:
        memory_context = "\n\nNo relevant memories found for this prompt."

    system_prompt = f"You are an AI agent with the '{hat_name}' persona."
    if memory_context:
        system_prompt += memory_context

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content

@cl.on_message
async def handle_message(message: cl.Message):
    """
    Main message handler routing user input to appropriate functions.
    """
    current_hat = cl.user_session.get("current_hat")
    
    
    content = message.content.strip()
    content_lower = content.lower()

    # Get current state flags
    editing_hat_id = cl.user_session.get("editing_hat_id")
    awaiting_json_paste = cl.user_session.get("awaiting_json_paste")
    awaiting_hat_prompt = cl.user_session.get("awaiting_hat_prompt")

    # --- State-Based Handling ---
    if awaiting_json_paste and editing_hat_id:
        # Expecting JSON paste for the currently edited hat
        cl.user_session.set("awaiting_json_paste", False) # Consume the flag (attempt save once)
        await save_edited_json(message, editing_hat_id)

    elif awaiting_hat_prompt:
        # Expecting description for a new hat
        # handle_prompt will set awaiting_hat_prompt to False
        await handle_prompt(message)

    # --- Command Handling ---
    elif content_lower == "new blank":
        await create_blank_hat()

    elif content_lower == "new from prompt":
        await ask_for_prompt()

    elif content_lower.startswith("wear "):
        hat_id = content.split(" ", 1)[1].strip()
        if hat_id:
            await wear_hat(hat_id)
        else:
            await cl.Message(content="Usage: `wear <hat_id>`").send()

    elif content_lower.startswith("edit "):
        hat_id = content.split(" ", 1)[1].strip()
        if hat_id:
            # First, wear the hat to make it active
            await wear_hat(hat_id)
            # Check if wearing was successful (editing_hat_id is now set)
            if cl.user_session.get("editing_hat_id") == hat_id:
                 # Now, set the flag and prompt for JSON
                cl.user_session.set("awaiting_json_paste", True)
                await cl.Message(content=f"📝 OK. Paste the full updated JSON for `{hat_id}` now.").send()
        else:
            await cl.Message(content="Usage: `edit <hat_id>`").send()

    elif content_lower == "help":
         await cl.Message(content=(
             "**Available Commands:**\n"
             "- `wear <hat_id>`: Load and activate a hat.\n"
             "- `new blank`: Create an empty hat.\n"
             "- `new from prompt`: Create a hat by describing it.\n"
             "- `edit <hat_id>`: Start editing by pasting JSON for the specified hat.\n"
             "- *Button*: Click 'Edit This Hat (UI)' after wearing a hat to use the form.\n"
             "- `help`: Show this message."
         )).send()
    elif content_lower.startswith("view memories"):
        hat_id = current_hat.get('hat_id') if current_hat else None
        if not hat_id:
            await cl.Message(content="❌ No active hat. Wear a hat first.").send()
        else:
            memories = search_memory(hat_id, "", k=5)
            if memories:
                formatted = "\n".join([
                    f"- [{meta['timestamp']}][{meta['role']}] {doc}"
                    for doc, meta in memories
                ])
                await cl.Message(content=f"🧠 Top memories for `{hat_id}`:\n{formatted}").send()
            else:
                await cl.Message(content=f"🧠 No memories stored for `{hat_id}` yet.").send()
    elif content_lower.startswith("clear memories"):
        hat_id = current_hat.get('hat_id') if current_hat else None
        if not hat_id:
            await cl.Message(content="❌ No active hat. Wear a hat first.").send()
        else:
            clear_memory(hat_id)
            await cl.Message(content=f"🧹 Cleared all memories for `{hat_id}`.").send()
    elif content_lower == "debug memories":
        hat_id = current_hat.get('hat_id')
        collection = get_vector_db_for_hat(hat_id)
        all_data = collection.get(include=["documents", "metadatas"])
        print("DEBUG COLLECTION DATA:", all_data)
        await cl.Message(content=f"🔍 Debug: {len(all_data['documents']) if all_data and all_data.get('documents') else 0} memories found in raw collection.").send()
    elif content_lower == "set schedule":
        await cl.Message(content="⏰ Please enter the time (HH:MM) for the Hat schedule:").send()
        cl.user_session.set("awaiting_schedule_time", True)
        return
    elif content_lower == "view schedule":
        schedule = cl.user_session.get("hat_schedule", {})
        if schedule:
            formatted = "\n".join([f"- {time}: {hat}" for time, hat in schedule.items()])
            await cl.Message(content=f"📅 Your current Hat schedule:\n{formatted}").send()
        else:
            await cl.Message(content="📅 No Hats scheduled yet.").send()
    elif cl.user_session.get("awaiting_schedule_time"):
        cl.user_session.set("awaiting_schedule_time", False)
        schedule_time = content.strip()

        # Validate time format (HH:MM)
        if not re.match(r"^\d{2}:\d{2}$", schedule_time):
            await cl.Message(content="❌ Invalid time format. Please use HH:MM (e.g., 09:00)").send()
            return

        cl.user_session.set("schedule_time_temp", schedule_time)

        hats = list_hats()
        if not hats:
            await cl.Message(content="❌ No Hats available to schedule.").send()
            return

        await cl.Message(
            content=(
                f"🎩 Please type the **Hat name** you'd like to schedule for **{schedule_time}** from the list below:\n\n" +
                "\n".join([f"- `{hat}`" for hat in hats])
            )
        ).send()

        cl.user_session.set("awaiting_schedule_hat", True)
        return
    elif cl.user_session.get("awaiting_schedule_hat"):
        cl.user_session.set("awaiting_schedule_hat", False)
        schedule_time = cl.user_session.get("schedule_time_temp")
        hat_id = content.strip().lower()  # make it case-insensitive

        hats = list_hats()
        hats_lower = [h.lower() for h in hats]

        if hat_id in hats_lower:
            real_hat_id = hats[hats_lower.index(hat_id)]  # get actual case-sensitive hat name
            schedule = cl.user_session.get("hat_schedule", {})
            schedule[schedule_time] = real_hat_id
            cl.user_session.set("hat_schedule", schedule)

            await cl.Message(content=f"✅ Scheduled Hat `{real_hat_id}` for `{schedule_time}`!").send()
        else:
            await cl.Message(content=f"❌ Hat `{hat_id}` not found. Please try `set schedule` again.").send()
        return
    elif content_lower == "current hat":
        current_hat = cl.user_session.get("current_hat")
        if current_hat:
            await cl.Message(content=f"🎩 You are currently wearing: `{current_hat.get('name')}` (ID: `{current_hat.get('hat_id')}`)").send()
        else:
            await cl.Message(content="❌ No Hat is currently active.").send()
    # --- Fallback / General Chat ---
    else:
        current_hat = cl.user_session.get("current_hat")
        if current_hat:
            # --- Time-Based Hat Switching ---
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M")
            schedule = cl.user_session.get("hat_schedule", {})

            if current_time in schedule:
                scheduled_hat = schedule[current_time]
                await wear_hat(scheduled_hat)
                await cl.Message(content=f"🕒 Auto-switched to Hat `{scheduled_hat}` based on your schedule!").send()


            response_text = generate_openai_response(message.content, current_hat.get('name'), current_hat.get('hat_id'))
            # Save both user message and bot response into memory
            add_memory_to_hat(current_hat.get('hat_id'), message.content, role="user")
            add_memory_to_hat(current_hat.get('hat_id'), response_text, role="bot")

            await cl.Message(content=response_text).send()
        else:
            await cl.Message(content="No hat is currently active. Use `wear <hat_id>` or select one.").send()