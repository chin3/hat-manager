import json
import chainlit as cl
from chainlit.input_widget import TextInput, Select, Tags # Keep only one import
from chainlit.element import Text # Explicit imports can be clearer
from chainlit.action import Action # Explicit import
import re
from hat_templates import clone_hat_template

from datetime import datetime

from hat_templates import clone_hat_template  # import at top if not already

from hat_manager import (
    list_hats,
    list_hats_by_team,
    load_hat,
    normalize_hat,
    save_hat,
    ollama_llm,
    get_vector_db_for_hat,
    search_memory,
    add_memory_to_hat,
    clear_memory
)


import os
from dotenv import load_dotenv

from prompts import generate_openai_response, generate_team_from_goal
from ui import show_hat_sidebar, show_hat_selector
from actions import (
    ask_for_prompt,
    handle_prompt,
    save_edited_json,
    save_team_action
)

from flow import finalize_team_flow, run_team_flow

from utils import format_tags_for_display, generate_unique_hat_id, current_timestamp, format_memory_entry, merge_tags

load_dotenv()
try:
    from hat_manager import (
        list_hats,
        load_hat,
        save_hat,
       # ollama_llm # Assuming this is your LLM instance
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
    
#HELPER FOR TEAMS saves the proposed team in the session so it can be reused. 
def load_team_from_ids(hat_ids):
    return [load_hat(hat_id) for hat_id in hat_ids]

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
                # f"• Click the **Edit This Hat** button below"
            ),
            # actions=[
            #     Action(
            #         name="edit_hat_ui", # Matches the callback name
            #         label="📝 Edit This Hat (UI)",
            #         value="edit", # Value isn't strictly needed if using payload
            #         payload={"hat_id": hat_id} # Send hat_id to the callback
            #     )
            # ]
        ).send()

        # Don't necessarily need to show selector again immediately after wearing,
        # but can be useful if the list is long. Comment out if too noisy.
        # await show_hat_selector()

    except FileNotFoundError:
        await cl.Message(content=f"❌ Error: Hat file for `{hat_id}` not found.").send()
    except Exception as e:
        await cl.Message(content=f"❌ Couldn't load hat `{hat_id}`: {e}").send()

async def create_blank_hat():
    """Creates and saves a new, empty hat with default enhanced schema."""
    existing_ids = list_hats()  # Get current hat IDs
    hat_id = generate_unique_hat_id(existing_ids)  # Pass them into the helper


    blank = {
        "hat_id": hat_id,
        "name": f"New Hat {hat_id}",
        "model": "gpt-3.5-turbo",  # Default model, you can change if needed
        "role": "agent",
        "instructions": "",
        "tools": [],
        "relationships": [],
        "team_id": None,
        "flow_order": None,
        "qa_loop": False,
        "critics": [],
        "active": True,
        "memory_tags": [],
        "retry_limit": 1,
        "description": ""
    }

    try:
        save_hat(blank["hat_id"], blank)
        await cl.Message(content=f"📄 Blank Hat `{blank['hat_id']}` created. You can now `wear {blank['hat_id']}`.").send()
        await show_hat_sidebar()
        await show_hat_selector()
    except Exception as e:
        await cl.Message(content=f"❌ Failed to save blank hat: {e}").send()


async def handle_hat_mention(trigger_hat_id, trigger_message, target_hat_id, hats_list):
    # Load target hat data
    target_hat = next((h for h in hats_list if h['hat_id'] == target_hat_id), None)
    if not target_hat:
        await cl.Message(content=f"❌ Hat `{target_hat_id}` not found.").send()
        return False

    # Generate response
    response = generate_openai_response(trigger_message, target_hat)

    # Save memory
    add_memory_to_hat(target_hat_id, trigger_message, role="user", tags=target_hat.get("memory_tags", []),session=cl.user_session)
    add_memory_to_hat(target_hat_id, response, role="bot", tags=target_hat.get("memory_tags", []), session=cl.user_session)

    await cl.Message(content=f"🧢 @{target_hat['name']} replied:\n{response}").send()
    return True
async def handle_multiple_mentions(trigger_hat_id, trigger_message, hats_list):
    """
    Finds and triggers all mentioned Hats in a message.
    - trigger_hat_id: ID of the initiator (user or agent).
    - trigger_message: The full message containing @mentions.
    - hats_list: List of all available hat IDs.
    """
    mentioned_hat_ids = re.findall(r"@(\w+)", trigger_message)
    if not mentioned_hat_ids:
        return False  # No mentions found

    handled_any = False
    for target_hat_id in set(mentioned_hat_ids):  # Avoid duplicate mentions
        success = await handle_hat_mention(trigger_hat_id, trigger_message, target_hat_id, hats_list)
        handled_any = handled_any or success  # Track if at least one was valid

    return handled_any

async def handle_mentions_if_any(message: cl.Message, hats: list):
    content = message.content.strip()
    mentioned = re.findall(r"@(\w+)", content)
    hats_obj = [load_hat(hat_id) for hat_id in list_hats()]
    if mentioned:
        await handle_multiple_mentions("user", content, hats_obj)
        return True  # Mentions handled
    return False  # No mentions found


@cl.on_message
async def handle_message(message: cl.Message):
    """
    Main message handler routing user input to appropriate functions.
    """
    current_hat = cl.user_session.get("current_hat")
    allhats = list_hats()
    if await handle_mentions_if_any(message, allhats):
        return  # Skip rest if handled mentions
    
    content = message.content.strip()
    content_lower = content.lower()
    
    # --- User Approval Handling ---
    if cl.user_session.get("awaiting_user_approval"):
        cl.user_session.set("awaiting_user_approval", False)
        if content_lower == "retry":
            await cl.Message(content="🔄 User requested retry. Re-running team...").send()
            await run_team_flow(cl.user_session.get("pending_team_id"), cl.user_session.get("pending_goal_description"))
            return
        elif content_lower == "approve":      
            team_id = cl.user_session.get("pending_team_id")
             
            await cl.Message(content="✅ Output approved by user! Team flow complete.").send()
            previous_hat = cl.user_session.get("previous_hat")
            if previous_hat:
                cl.user_session.set("current_hat", previous_hat)
                cl.user_session.set("editing_hat_id", previous_hat.get("hat_id"))
                await cl.Message(content=f"🎩 Resuming with hat: `{previous_hat.get('name', 'Unknown Hat')}`.").send()
            else:
                await cl.Message(content="⚠️ No previous hat found.").send()
                # 🚀 NEW: Finalize team flow after approval
            conversation_log = cl.user_session.get("pending_conversation_log", [])
            mission_success = cl.user_session.get("pending_mission_success", False)
            revision_required = cl.user_session.get("pending_revision_required", False)
            goal_description = cl.user_session.get("pending_goal_description", "No goal provided.")

            if conversation_log:
                await finalize_team_flow(conversation_log, mission_success, revision_required, goal_description, team_id)
            else:
                await cl.Message(content="⚠️ No saved conversation log. Cannot finalize mission.").send()

            return
        else:
            await cl.Message(content="❓ Invalid response. Please type `approve` or `retry`.").send()
            cl.user_session.set("awaiting_user_approval", True)
            return

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
        await handle_prompt(message, ollama_llm)

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
            await wear_hat(hat_id)
            if cl.user_session.get("editing_hat_id") == hat_id:
                cl.user_session.set("awaiting_json_paste", True)
                current_hat = cl.user_session.get("current_hat")

                # First Message: Instruction
                await cl.Message(content=f"📝 OK. Paste the full updated JSON for `{hat_id}` now. Below is the current JSON for reference.").send()

                # Second Message: Copyable JSON Block (Markdown Styled)
                await cl.Message(content="```json\n" + json.dumps(current_hat, indent=2) + "\n```").send()
        else:
            await cl.Message(content="Usage: `edit <hat_id>`").send()
    elif content_lower.startswith("add qa to "):
        parts = content.split(" ", 3)
        if len(parts) < 4:
            await cl.Message(content="❌ Usage: `add qa to <hat_id>`").send()
            return

        target_hat_id = parts[3].strip()
        try:
            target_hat = load_hat(target_hat_id)
            team_id = target_hat.get("team_id")
            if not team_id:
                await cl.Message(content="❌ Hat is not part of a team. Add it to a team first.").send()
                return

            # Add QA loop settings
            target_hat["qa_loop"] = True
            target_hat["retry_limit"] = target_hat.get("retry_limit", 2)
            critic_id = f"critic_{team_id}"
            if "critics" not in target_hat or not isinstance(target_hat["critics"], list):
                target_hat["critics"] = []

            if critic_id not in target_hat["critics"]:  # 🔧 Add critic reference if missing
                target_hat["critics"].append(critic_id)

            save_hat(target_hat_id, normalize_hat(target_hat, team_id=team_id, flow_order=target_hat.get("flow_order", 1)))
            await cl.Message(content=f"✅ QA loop enabled for `{target_hat_id}` with critic `{critic_id}`.").send()

            # Add critic hat if not already in disk
            if critic_id not in list_hats():
                new_critic = clone_hat_template("critic", new_suffix=team_id, team_id=team_id, flow_order=99)
                save_hat(new_critic["hat_id"], new_critic)
                await cl.Message(content=f"🎩 Cloned and saved Critic Hat: `{new_critic['hat_id']}`").send()

            await show_hat_sidebar()
            await show_hat_selector()

        except Exception as e:
            await cl.Message(content=f"❌ Failed to add QA loop to `{target_hat_id}`: {e}").send() 
    elif content_lower.startswith("remove critic from team "):
        parts = content.split(" ", 4)
        if len(parts) < 5:
            await cl.Message(content="❌ Usage: `remove critic from team <team_id>`").send()
            return

        team_id = parts[4].strip()
        try:
            hats = list_hats_by_team(team_id)
            critic_id = f"critic_{team_id}"
            filtered_hats = [hat for hat in hats if hat["hat_id"] != critic_id]

            if len(filtered_hats) == len(hats):
                await cl.Message(content=f"⚠️ No critic found in team `{team_id}`.").send()
            else:
                path = f"./hats/{critic_id}.json"
                if os.path.exists(path):
                    os.remove(path)
                    await cl.Message(content=f"🗑️ Removed Critic Hat `{critic_id}` from disk.").send()
                else:
                    await cl.Message(content=f"⚠️ Critic file `{critic_id}.json` not found.").send()

            await show_hat_sidebar()
            await show_hat_selector()

        except Exception as e:
            await cl.Message(content=f"❌ Failed to remove critic from team `{team_id}`: {e}").send()
    
    elif content_lower.startswith("view memories"):
        parts = content.split(" ", 2)
        tag = parts[2].strip() if len(parts) > 2 else None

        hat_id = current_hat.get('hat_id') if current_hat else None
        if not hat_id:
            await cl.Message(content="❌ No active hat. Wear a hat first.").send()
        else:
            memories = search_memory(hat_id, "", k=None, tag_filter=tag)
            if memories:
                formatted = "\n".join([format_memory_entry(doc, meta) for doc, meta in memories])
                await cl.Message(content=f"🧠 Memories for `{hat_id}`{f' with tag `{tag}`' if tag else ''}:\n{formatted}").send()
            else:
                await cl.Message(content=f"🧠 No memories stored for `{hat_id}`{f' with tag `{tag}`' if tag else ''}.").send()
    
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
    
    elif content_lower.startswith("run team "):
        parts = message.content.split(" ", 2)  # Do not lowercase here, keep original case
        if len(parts) < 3:
            await cl.Message(content="❌ Usage: `run team <team_id> [optional team goal]`").send()
            return

        team_id = parts[2].strip().split(" ")[0]  # First word after 'run team' = team_id
        goal_description = " ".join(parts[2].strip().split(" ")[1:]).strip()  # The rest is optional goal

        if not team_id:
            await cl.Message(content="❌ Usage: `run team <team_id> [optional team goal]`").send()
            return

        # Default fallback goal if none specified
        if not goal_description:
            goal_description = "Start a research summary on AI in healthcare"

        await cl.Message(content=f"🚀 Running team flow for `{team_id}`...\n\n**Goal:** {goal_description}").send()
        await run_team_flow(team_id, goal_description)
        return
    
    elif content_lower.startswith("view team "):
        team_id = content.split(" ", 2)[2].strip()
        if not team_id:
            await cl.Message(content="❌ Usage: `view team <team_id>`").send()
            return

        team_hats = list_hats_by_team(team_id)
        if not team_hats:
            await cl.Message(content=f"❌ No Hats found for team `{team_id}`.").send()
            return

        team_summary = "\n".join([
            f"- `{hat['name']}` (`{hat['hat_id']}`) → Role: `{hat.get('role', 'N/A')}`, Flow Order: {hat.get('flow_order', 'N/A')}"
            for hat in team_hats
        ])
        await cl.Message(content=f"👥 Team `{team_id}` Hats:\n{team_summary}").send()
        return
    ##Team short cuts
    elif content_lower.startswith("new story team"):
        parts = message.content.split(" ", 3)  # Keep original casing
        if len(parts) < 4:
            await cl.Message(content="❌ Usage: `new story team <story prompt>`").send()
            return

        story_prompt = parts[3].strip()

        # Create a unique team_id based on time
        team_id = f"story_team_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        storyteller_hat = load_hat("storyteller_hat")
        critic_hat = load_hat("critic")
        # Build the team hats dynamically
        storyteller_hat = normalize_hat(storyteller_hat, team_id=team_id, flow_order=1)
        critic_hat = normalize_hat(critic_hat, team_id=team_id, flow_order=2)
        critic_hat["qa_loop"] = True

        save_hat(storyteller_hat["hat_id"], storyteller_hat)
        save_hat(critic_hat["hat_id"], critic_hat)

        await cl.Message(content=f"✨ Created new Story Team: `{team_id}`.\n\n**Mission:** {story_prompt}").send()
        await run_team_flow(team_id, story_prompt)
        return
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
    elif content_lower.startswith("create team"):
        await cl.Message(content="🎯 What is your goal? Describe what you'd like the AI team to accomplish.").send()
        cl.user_session.set("awaiting_team_goal", True)
        return
    elif cl.user_session.get("awaiting_team_goal"):
        cl.user_session.set("awaiting_team_goal", False)
        goal_description = content.strip()
        
        # After user describes their goal
        await cl.Message(content="🤖 Building your AI team based on your goal...").send()

        # 🧹 Step 1: Generate team
        team_hat_ids = await generate_team_from_goal(goal_description)

        # 🧹 Step 2: Load full hats now (only once)
        proposed_team = load_team_from_ids(team_hat_ids)
        cl.user_session.set("proposed_team", proposed_team)

        team_summary = "\n".join(
            f"- {hat['name']} ({hat['hat_id']}) → Role: {hat.get('role', 'N/A')}"
            for hat in proposed_team
        )
        await cl.Message(content=f"📋 Proposed Team:\n{team_summary}\n\nApprove with `save team`, or modify manually.").send()
        await cl.Message(
                content="✅ Team ready! Would you like to save it?",
                actions=[
                    Action(
                        name="save_team_action",
                        label="💾 Save Team",
                        payload={"action": "save_team"}
                    )
                ]
            ).send()

        return
    elif content_lower == "save team":
        proposed_team = cl.user_session.get("proposed_team")

        if not proposed_team:
            await cl.Message(content="❌ No team proposal found. Use `create team` first.").send()
        else:
            for hat in proposed_team:
                save_hat(hat["hat_id"], normalize_hat(hat))
            await cl.Message(content="✅ Team saved! Use `wear <hat_id>` to activate a Hat, or `view schedule` to assign times.").send()
            await show_hat_sidebar()
            await show_hat_selector()
        return
    elif content_lower == "show team json":
        proposed_team = cl.user_session.get("proposed_team")
        if proposed_team:
            await cl.Message(content=f"```json\n{json.dumps(proposed_team, indent=2)}\n```").send()
        else:
            await cl.Message(content="No team proposal to show.").send()
    elif content_lower == "help":
        await cl.Message(content=(
            "**Available Commands:**\n"
            "- `wear <hat_id>`: Load and activate a hat.\n"
            "- `new blank`: Create an empty hat.\n"
            "- `new from prompt`: Create a hat by describing it.\n"
            "- `edit <hat_id>`: Start editing by pasting JSON for the specified hat.\n"
            "- `run team <team_id>`: Run a full flow of Hats based on team configuration.\n"
            "- `view memories`, `clear memories`, `view schedule`, etc."
        )).send()
        
    elif content_lower.startswith("tag last as "):
        tag = content.split("tag last as ", 1)[1].strip()
        last_memory_id = cl.user_session.get("last_memory_id")
        last_memory_hat_id = cl.user_session.get("last_memory_hat_id")

        if last_memory_id and last_memory_hat_id:
            collection = get_vector_db_for_hat(last_memory_hat_id)
            try:
                memory_data = collection.get(ids=[last_memory_id], include=["metadatas"])
                current_meta = memory_data["metadatas"][0]

                # 💡 Use your utility here!
                merged_tags = merge_tags(current_meta.get("tags", ""), tag)
                merged_tags_csv = ",".join(merged_tags)

                collection.update(
                    ids=[last_memory_id],
                    metadatas=[{
                        "timestamp": current_meta.get("timestamp", datetime.now().isoformat()),
                        "role": current_meta.get("role", "user"),
                        "tags": merged_tags_csv  # ✅ CSV format
                    }]
                )
                formatted_tags = format_tags_for_display(merged_tags)
                await cl.Message(content=f"🏷️ Memory tagged as `{tag}` in `{last_memory_hat_id}`! Now tagged: {formatted_tags}").send()
            except Exception as e:
                await cl.Message(content=f"❌ Failed to tag memory: {e}").send()
        else:
            await cl.Message(content="❌ No memory to tag.").send()
    elif content_lower == "view missions":
        MISSIONS_DIR = "./missions"
        if not os.path.exists(MISSIONS_DIR):
            await cl.Message(content="📂 No mission archives found yet.").send()
            return

        mission_files = [f for f in os.listdir(MISSIONS_DIR) if f.endswith(".json")]
        if not mission_files:
            await cl.Message(content="📂 No saved missions yet.").send()
            return

        mission_list = "\n".join([f"- `{f}`" for f in sorted(mission_files)])
        await cl.Message(content=f"🗂️ **Saved Missions:**\n\n{mission_list}").send()
        return
    #Clone a hat using hat_templates.py establish parent child relationship with basehat.
    elif content_lower.startswith("new from base "):
        base_hat_id = content.split(" ", 3)[3].strip()
        if not base_hat_id:
            await cl.Message(content="❌ Usage: new from base <base_hat_id>").send()
            return

        try:

            new_hat = clone_hat_template(base_hat_id)
            await cl.Message(content=f"🎩 Cloned Hat `{base_hat_id}` ➔ `{new_hat['hat_id']}`\nYou can now `wear {new_hat['hat_id']}`.").send()
            await show_hat_sidebar()
            await show_hat_selector()
        except Exception as e:
            await cl.Message(content=f"❌ Failed to clone base Hat: {e}").send()

        # --- Fallback / General Chat ---
    else:
        current_hat = cl.user_session.get("current_hat")
        if current_hat:
            # --- Time-Based Hat Switching ---
            current_time = datetime.now().strftime("%H:%M")
            schedule = cl.user_session.get("hat_schedule", {})

            if current_time in schedule:
                scheduled_hat = schedule[current_time]
                await wear_hat(scheduled_hat)
                await cl.Message(content=f"🕒 Auto-switched to Hat `{scheduled_hat}` based on your schedule!").send()
                current_hat = cl.user_session.get("current_hat")


            response_text = generate_openai_response(message.content, current_hat)
            # Save both user message and bot response into memory
            tags = current_hat.get("memory_tags", [])
            add_memory_to_hat(current_hat.get('hat_id'), message.content, role="user", tags=tags, session=cl.user_session)
            add_memory_to_hat(current_hat.get('hat_id'), response_text, role="bot", tags=tags, session=cl.user_session)
            
            await cl.Message(content=response_text).send()

            await handle_multiple_mentions(trigger_hat_id=current_hat.get("hat_id"), trigger_message=response_text, hats_list=[load_hat(hid) for hid in list_hats()])
            #Save mentioned hats in memory of main hat
            mentioned_hat_ids = set(re.findall(r"@(\w+)", response_text))
            for target_hat_id in mentioned_hat_ids:
                mentioned_hat = next((h for h in [load_hat(hid) for hid in list_hats()] if h['hat_id'] == target_hat_id), None)
                if mentioned_hat:
                    add_memory_to_hat(
                        current_hat.get('hat_id'),
                        f"@{mentioned_hat['name']} replied: {response_text}",
                        role="bot",
                        tags=current_hat.get("memory_tags", [])
                        , session=cl.user_session
                    )
                    print(f"🔗 Saved @{mentioned_hat['hat_id']}'s reply ALSO in {current_hat.get('hat_id')}'s memory.")
        else:
            await cl.Message(content="No hat is currently active. Use `wear <hat_id>` or select one.").send()