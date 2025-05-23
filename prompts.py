import openai
import os
import re
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

from hat_manager import build_hat_schema_prompt, ensure_schema_defaults, load_hat, normalize_hat, search_memory, save_hat
import chainlit as cl

load_dotenv()

# -----------------------------
# LLM Clients
# -----------------------------

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




def parse_llm_response_to_hat(content):
    try:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            cleaned_json = match.group(1)
        else:
            cleaned_json = re.search(r"(\{.*\})", content, re.DOTALL).group(1)

        hat_data = json.loads(cleaned_json)

        required_fields = ["hat_id", "name", "model", "instructions"]
        if all(field in hat_data for field in required_fields):
            return hat_data
        else:
            raise ValueError(f"Missing required fields: {required_fields}")

    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {e}")


def call_ollama_llm(prompt, model="llama3:8b", max_retries=3):
    system_message = build_hat_schema_prompt()

    for _ in range(max_retries):
        res = requests.post("http://localhost:11434/api/chat", json={
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        })

        if res.status_code == 200:
            try:
                return parse_llm_response_to_hat(res.json()["message"]["content"])
            except Exception:
                continue
        else:
            raise Exception(f"Ollama API Error: {res.status_code} - {res.text}")

    raise Exception("Failed to get valid response from Ollama after retries.")

##For use with Hat Generation
def call_openai_llm(messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=1000):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    ).choices[0].message.content


def openai_hat_generator(prompt):
    system = build_hat_schema_prompt()
    response = call_openai_llm([
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ])
    raw_hat = parse_llm_response_to_hat(response)
    return ensure_schema_defaults(raw_hat)

# -----------------------------
# Application Logic
# -----------------------------

async def handle_prompt(message: cl.Message, ollama_llm):
    cl.user_session.set("awaiting_hat_prompt", False)
    prompt_content = message.content

    thinking_msg = cl.Message(content="⚙️ Creating Hat from your description...")
    await thinking_msg.send()

    try:
        hat = create_hat_from_prompt(prompt_content, ollama_llm)
        if not hat or not hat.get("hat_id") or not hat.get("name"):
            raise ValueError("LLM did not return a valid hat structure.")

        save_hat(hat["hat_id"], hat)

        await thinking_msg.remove()
        await cl.Message(
            content=f"✅ Created Hat: `{hat['name']}` (ID: `{hat['hat_id']}`). You can now `wear {hat['hat_id']}`."
        ).send()

    except Exception as e:
        await cl.Message(content=f"❌ Failed to create Hat from prompt: {e}").send()


def generate_openai_response(prompt: str, hat: dict):
    hat_name = hat.get('name', 'Unnamed Agent')
    hat_id = hat.get('hat_id')
    tools = ", ".join(hat.get('tools', [])) or "none"
    instructions = hat.get('instructions', '')
    role = hat.get('role', 'agent')

    memory_context = ""
    if hat_id:
        relevant = search_memory(hat_id, prompt, k=3)
        if relevant:
            memory_context = "\n\nRelevant Memories:\n" + "\n".join([
                f"{m.get('role', 'unknown').capitalize()} ({m.get('timestamp', 'no time')}): {d}"
                for d, m in relevant
            ])

    relationship_context = ""
    if hat.get("relationships"):
        info = []
        for rel in hat["relationships"]:
            try:
                h = load_hat(rel)
                info.append(
                    f"- To call this helper, include `@{rel}` in your reply.\n"
                    f"  • @{rel} = {h.get('name')}: {h.get('description', '...')} (Tools: {', '.join(h.get('tools', [])) or 'none'})"
                )
            except:
                info.append(f"- @{rel}: (Details not found)")
        relationship_context = (
            "\n\nYou can collaborate with the following agents by @mentioning their ID in your response:\n"
            + "\n".join(info)
        )
        

    system_prompt = f"""
You are a {role} agent named '{hat_name}'.
Your tools: {tools}.
Instructions: {instructions}.{relationship_context}{memory_context}
""".strip()

    print(system_prompt)
    return call_openai_llm([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ], model=hat.get("model", "gpt-3.5-turbo"))


async def generate_openai_response_with_system(user_prompt: str, system_prompt: str, hat):
    return call_openai_llm([
        {"role": "system", "content": f"You are {hat.get('name', 'an AI agent')}. {hat.get('instructions', '')} {system_prompt}"},
        {"role": "user", "content": user_prompt}
    ], model=hat.get("model", "gpt-3.5-turbo"))



async def generate_team_from_goal(goal: str):
    """
    Generates a team of Hats from a goal using OpenAI and saves them.
    Enforces at least 3 Hats with unique roles. Retries up to 3x, falls back to default if needed.
    """

    team_id = f"auto_team_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    system_prompt = f"""
{build_hat_schema_prompt()}

You are an AI responsible for designing a specialized multi-agent team ("Hats") to achieve a goal.

✅ Requirements:
- Create **at least 3 Hats**.
- Each Hat must have a **different role**.
- Roles can be planner, researcher, critic, summarizer, strategist, etc.
- Each Hat must have a unique hat_id (e.g., planner_{team_id}).
- Use the provided team_id: {team_id}.
- Output an **array** (`[...]`) of valid JSON objects.
- **DO NOT write explanations**.
- **DO NOT use markdown formatting** like ```.

### Goal:
{goal}

Respond ONLY with a valid JSON array [] of Hats.
""".strip()

    for attempt in range(3):  # Retry up to 3x
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"My goal: {goal}"}
                ],
                temperature=0.5,
                max_tokens=1800
            )
            result_text = response.choices[0].message.content

            match = re.search(r"\[.*\]", result_text, re.DOTALL)
            if not match:
                raise ValueError("No valid JSON array found.")
            hats = json.loads(match.group(0))

            # ✅ Check constraints
            roles = [hat.get("role", "") for hat in hats]
            if len(hats) >= 3 and len(set(roles)) >= 3:
                saved_ids = []
                for hat in hats:
                    normalized = normalize_hat(hat, team_id=team_id)
                    save_hat(normalized["hat_id"], normalized)
                    saved_ids.append(normalized["hat_id"])
                return saved_ids

        except Exception as e:
            print(f"⚠️ Team generation attempt {attempt+1} failed: {e}")

    # ⛑️ Fallback — use templates
    fallback_ids = []
    base_ids = ["planner", "researcher", "critic"]
    for i, base in enumerate(base_ids):
        try:
            base_hat = load_hat(base)
            normalized = normalize_hat(base_hat, team_id=team_id, flow_order=i + 1)
            save_hat(normalized["hat_id"], normalized)
            fallback_ids.append(normalized["hat_id"])
        except Exception as e:
            print(f"❌ Failed to load fallback hat `{base}`: {e}")

    return fallback_ids

def create_hat_from_prompt(prompt, llm_function):
    return llm_function(prompt)

