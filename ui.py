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

    elements += [
        Text(content="---"),
        Text(content="### ➕ Create"),
        Text(content="- `new blank` — Empty Hat"),
        Text(content="- `new from prompt` — Describe"),
        Text(content="- `create team` — Auto-build a team"),
        Text(content="---"),
        Text(content="### 👥 Teams"),
        Text(content="- `run team <team_id>` — Run multi-Hat flow"),
        Text(content="- `view team <team_id>` — Show team Hats"),
        Text(content="- `save team` — Save proposed team"),
        Text(content="- `show team json` — View team JSON"),
        Text(content="---"),
        Text(content="### 🧠 Memory"),
        Text(content="- `view memories` — Show top memories"),
        Text(content="- `clear memories` — Delete all memories"),
        Text(content="- `export memories <hat_id>` — Export JSON"),
        Text(content="- `debug memories` — Raw memory debug"),
        Text(content="---"),
        Text(content="### 🕒 Scheduling"),
        Text(content="- `set schedule` — Schedule Hat switching"),
        Text(content="- `view schedule` — View schedules"),
        Text(content="- `current hat` — Show active Hat"),
        Text(content="---"),
        Text(content="### ✅ Active Teams")
    ]

    for team_id in team_ids:
        team_hats = list_hats_by_team(team_id)
        hat_ids = ", ".join([hat.get("hat_id", "unknown_hat") for hat in team_hats])
        elements.append(Text(content=f"- `{team_id}`: {hat_ids}"))

    elements += [
        Text(content="---"),
        Text(content="### 🔥 TODOs / Next Steps"),
        Text(content="- `user approval` after Critic — Await 'approve'/'retry' ✔️"),
        Text(content="- Visual polish for logs (emojis/dividers) ✔️"),
        Text(content="- `import memories` command — #TODO"),
        Text(content="- Add `run again` / `create new team` buttons — #TODO"),
        Text(content="- QA edge fallback: prompt user after retry limit — #TODO"),
        Text(content="- Flow visualizer: plan graphical flow editor — #TODO"),
    ]

    await cl.ElementSidebar.set_elements(elements)
    await cl.ElementSidebar.set_title("Hat Manager")

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
