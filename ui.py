# ui.py
import chainlit as cl
from chainlit.element import Text
from chainlit.action import Action

from hat_manager import list_hats, load_hat, list_hats_by_team

async def show_hat_sidebar():
    hat_ids = list_hats()
    hats = [load_hat(hat_id) for hat_id in hat_ids]
    team_ids = list(set([hat.get("team_id") for hat in hats if hat.get("team_id")]))

    elements = [Text(content="### 🎩 Hats")]

    if hat_ids:
        for hat_id in hat_ids:
            elements.append(Text(content=f"- `wear {hat_id}`"))
    else:
        elements.append(Text(content="_(No hats found yet)_"))
    current_hat = cl.user_session.get("current_hat")
    # hat_display = ( [WIP]
    #     f"🎩 **Currently Wearing:** `{current_hat.get('name', current_hat.get('hat_id'))}`"
    #     if current_hat else "🎩 **Currently Wearing:** _None_"
    # )
    elements += [
        # Text(content=hat_display),
        Text(content="---"),
        Text(content="### 🎩 Hat Management"),
        Text(content="- `wear <hat_id>` — Activate a specific Hat"),
        Text(content="- `new blank` — Create an empty Hat"),
        Text(content="- `new from prompt` — Generate Hat from a description"),
        Text(content="- `new from base <base_hat_id>` — Clone a Hat template"),
        Text(content="- `edit <hat_id>` — Paste JSON to edit a Hat"),
        Text(content="- `current hat` — Show which Hat you're wearing"),
        Text(content="- `@hat_id` — Trigger another Hat via inline mention ex. `@hat_id <prompt>`"),

        Text(content="---"),
        Text(content="### 👥 Team Commands"),
        Text(content="- `create team` — Auto-generate Hats for a goal"),
        Text(content="- `new story team <prompt>` — Build Storyteller + Critic team"),
        Text(content="- `run team <team_id> [goal]` — Execute multi-Hat mission"),
        Text(content="- `view team <team_id>` — See Hats in a team"),
        Text(content="- `save team` — Save the currently proposed team"),
        Text(content="- `show team json` — Show JSON of proposed team"),

        Text(content="---"),
        Text(content="### 🧠 Memory Commands"),
        Text(content="- `view memories` — Show memory for current Hat"),
        Text(content="- `view memories <tag>` — Filter memories by tag"),
        Text(content="- `tag last as <tag>` — Tag the last memory entry"),
        Text(content="- `clear memories` — Delete all memory for current Hat"),
        Text(content="- `debug memories` — Show raw memory data in CLI"),

        Text(content="---"),
        Text(content="### 🕒 Scheduling & Utilities"),
        Text(content="- `set schedule` — Schedule Hat activation by time"),
        Text(content="- `view schedule` — See your Hat schedule"),
        Text(content="- `view missions` — Show archived team missions"),
        Text(content="- `help` — List all available commands"),

        Text(content="---"),
        Text(content="### ✅ Active Teams")  # This is dynamically populated below
    ]

    for team_id in team_ids:
        team_hats = list_hats_by_team(team_id)
        hat_ids = ", ".join([hat.get("hat_id", "unknown_hat") for hat in team_hats])
        elements.append(Text(content=f"- `{team_id}`: {hat_ids}"))

    elements += [
        Text(content="---"),
        Text(content="### 🔥 TODOs / Next Steps"),

        # ✅ Implemented
        Text(content="✅ `user approval` after Critic — Await 'approve'/'retry'"),
        Text(content="✅ Visual polish for logs (emojis/dividers)"),
        Text(content="✅ @Mention chaining between Hats"),
        Text(content="✅ Memory tagging and retrieval (`tag last as <tag>`)"),
        Text(content="✅ `export memories <hat_id>` via UI"),
        Text(content="✅ Per-Hat schedule support (`set schedule`)"),
        Text(content="✅ Multi-Hat reflections + MVP Awards"),
        Text(content="✅ Support `new from base <base_hat_id>` command"),

        # 🔄 In Progress / Working
        Text(content="🔄 QA fallback: Prompt user if retries exhausted"),
        Text(content="🔄 `further run team enhancements"),

        # ⏳ Planned
        Text(content="⏳ `export memories` json? command"),
        Text(content="⏳ `import memories` command"),
        Text(content="⏳ `run again` button after team flow"),
        Text(content="⏳ `create new team` button from goal"),
        Text(content="⏳ Better error handling for failed JSON parsing"),
        Text(content="⏳ Flow Chart Generator — Mermaid.js visualization of team structure"),
        Text(content="⏳ Parallel Execution for Hats with same `flow_order`"),
        Text(content="⏳ Tool integration (tools field schema is ready but not hydrated)"),
        Text(content="⏳ Dynamic LLM usage per Hat (e.g. OpenAI vs Ollama hybrid flow)"),
        Text(content="⏳ Copilot SDK / Agent Framework extension support (wear a Hat externally)")
    ]

    await cl.ElementSidebar.set_elements(elements)
    await cl.ElementSidebar.set_title("Mad 🎩 Hatter")

async def show_hat_selector():
    hats = list_hats()
    if not hats:
        return

    actions = [
        Action(
            name="wear_hat_button",
            label=hat,
            payload={"hat_id": hat}
        ) for hat in hats
    ]

    await cl.Message(
        content="🎩 Select a Hat to wear:",
        actions=actions
    ).send()
