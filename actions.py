# actions.py
import chainlit as cl
from chainlit.action import Action
import json

from hat_manager import create_hat_from_prompt, load_hat, save_hat, normalize_hat
from ui import show_hat_sidebar, show_hat_selector

# --- Schedule Actions ---
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

@cl.action_callback("wear_hat_button")
async def wear_hat_action_button(action: Action):
    hat_id = action.payload.get("hat_id")
    if not hat_id:
        await cl.Message(content="❌ Error: Could not retrieve hat_id from action payload.").send()
        return
    await wear_hat(hat_id)

async def wear_hat(hat_id: str):
    try:
        hat = load_hat(hat_id)
        cl.user_session.set("current_hat", hat)
        cl.user_session.set("editing_hat_id", hat_id)
        cl.user_session.set("awaiting_json_paste", False)
        cl.user_session.set("awaiting_hat_prompt", False)
        await cl.Message(
            content=(
                f"🧢 Now wearing: `{hat.get('name', hat_id)}`\n\n"
                f"To edit this Hat, you can:\n"
                f"• Type `edit {hat_id}` then paste JSON\n"
                f"• Click the **Edit This Hat** button below"
            ),
            actions=[
                Action(
                    name="edit_hat_ui",
                    label="📝 Edit This Hat (UI)",
                    payload={"hat_id": hat_id}
                )
            ]
        ).send()
    except FileNotFoundError:
        await cl.Message(content=f"❌ Error: Hat file for `{hat_id}` not found.").send()
    except Exception as e:
        await cl.Message(content=f"❌ Couldn't load hat `{hat_id}`: {e}").send()
        
@cl.action_callback("save_team_action")
async def save_team_action(action: cl.Action):
    proposed_team = cl.user_session.get("proposed_team")
    if not proposed_team:
        await cl.Message(content="❌ No team to save.").send()
        return
    
    for hat in proposed_team:
        save_hat(hat["hat_id"], normalize_hat(hat))
    
    await cl.Message(content="✅ Team saved successfully! You can now `wear <hat_id>` or `run team <team_id>`.").send()
    await show_hat_sidebar()
    await show_hat_selector()

@cl.action_callback("edit_hat_ui")
async def edit_hat_action_ui(action: Action):
    hat_id = action.payload.get("hat_id")
    if not hat_id:
        await cl.Message(content="❌ Error: Missing hat_id in edit action payload.").send()
        return
    try:
        hat = load_hat(hat_id)
        if hat is None:
            await cl.Message(content=f"❌ Error: Could not load hat with ID '{hat_id}'.").send()
            return
        await cl.Message(
            content="📝 Editing Hat:",
            elements=[
                cl.CustomElement(
                    name="HatEditor",
                    display="inline",
                    props=hat
                )
            ]
        ).send()
    except Exception as e:
        await cl.Message(content=f"❌ Error loading hat '{hat_id}' for UI editing: {e}").send()

@cl.action_callback("save_hat")
async def save_hat_action_ui(action: Action):
    updated_hat = action.payload
    hat_id = updated_hat.get("hat_id")
    if not hat_id or not isinstance(updated_hat, dict):
        await cl.Message(content="❌ Error: Invalid payload received from Hat Editor.").send()
        return
    try:
        save_hat(hat_id, updated_hat)
        cl.user_session.set("current_hat", updated_hat)
        cl.user_session.set("editing_hat_id", hat_id)
        await cl.Message(content=f"✅ Hat '{updated_hat.get('name', hat_id)}' updated via UI.").send()
        await cl.Message(
            content="✅ Hat saved. Here’s the updated version for further edits:",
            elements=[
                cl.CustomElement(name="HatEditor", id="hat_editor", props=updated_hat, display="inline")
            ]
        ).send()
        await show_hat_sidebar()
        await show_hat_selector()
    except Exception as e:
        await cl.Message(content=f"❌ Error saving hat '{hat_id}' from UI: {e}").send()

# --- Hat Prompt Handling ---
async def ask_for_prompt():
    cl.user_session.set("awaiting_hat_prompt", True)
    cl.user_session.set("awaiting_json_paste", False)
    await cl.Message(content="🪄 Describe the new Hat you want to create (e.g., `A helpful assistant that can summarize text`).").send()

async def handle_prompt(message: cl.Message, ollama_llm):
    cl.user_session.set("awaiting_hat_prompt", False)
    prompt_content = message.content

    try:
        thinking_msg = cl.Message(content="⚙️ Creating Hat from your description...")
        await thinking_msg.send()

        hat = create_hat_from_prompt(prompt_content, ollama_llm)

        if not hat or not hat.get("hat_id") or not hat.get("name"):
            raise ValueError("LLM did not return a valid hat structure.")

        save_hat(hat["hat_id"], hat)

        await thinking_msg.remove()
        await cl.Message(content=f"✅ Created Hat: `{hat['name']}` (ID: `{hat['hat_id']}`). You can now `wear {hat['hat_id']}`.").send()
        
    except Exception as e:
        await cl.Message(content=f"❌ Failed to create Hat from prompt: {e}").send()

# --- Save Edited Hat JSON ---
async def save_edited_json(message: cl.Message, hat_id_to_edit: str):
    try:
        updated_hat = json.loads(message.content)
        if not isinstance(updated_hat, dict):
            raise TypeError("Pasted content is not a valid JSON object.")

        pasted_hat_id = updated_hat.get("hat_id")
        if not pasted_hat_id:
            raise ValueError("Pasted JSON is missing the 'hat_id' key.")

        if pasted_hat_id != hat_id_to_edit:
            await cl.Message(content=f"❌ Mismatch: Editing `{hat_id_to_edit}` but JSON has `{pasted_hat_id}`.").send()
            return

        save_hat(hat_id_to_edit, updated_hat)
        cl.user_session.set("current_hat", updated_hat)
        await cl.Message(content=f"✅ Hat `{hat_id_to_edit}` updated from pasted JSON.").send()
    except json.JSONDecodeError as e:
        await cl.Message(content=f"❌ Invalid JSON: {e}. Please paste valid JSON content.").send()
    except Exception as e:
        await cl.Message(content=f"❌ Error saving updated hat `{hat_id_to_edit}`: {e}").send()