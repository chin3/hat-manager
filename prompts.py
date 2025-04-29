


import openai
from hat_manager import load_hat, search_memory
import os
from datetime import datetime
import re
import json
from dotenv import load_dotenv   

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def generate_openai_response(prompt: str, hat: dict):
    """
    Generates an AI response using the Hat schema for context.
    Supports instructions, tools, role, and memory injection.
    """

    hat_name = hat.get('name', 'Unnamed Agent')
    hat_id = hat.get('hat_id', None)  # 🛡️ Allow missing hat_id
    instructions = hat.get('instructions', '')
    role = hat.get('role', 'agent')
    tools_list = hat.get('tools', []) or []
    relationships = hat.get('relationships', []) or []

    tools = ", ".join(tools_list) if tools_list else "none"

    # 🧠 Fetch relevant memories (only if hat_id exists)
    memory_context = ""
    if hat_id:
        relevant_memories = search_memory(hat_id, prompt, k=3)
        if relevant_memories:
            formatted = "\n".join([
                f"{meta.get('role', 'unknown').capitalize()} ({meta.get('timestamp', 'no time')}): {doc}"
                for doc, meta in relevant_memories if meta and doc
            ])
            memory_context = f"\n\nRelevant Memories:\n{formatted}"

    # 🧠 Fetch relationship info (only if relationships exist)
    relationship_context = ""
    if relationships:
        related_hats_info = []
        for rel_id in relationships:
            try:
                rel_hat = load_hat(rel_id)
                rel_name = rel_hat.get("name", rel_id)
                rel_desc = rel_hat.get("description", "No description provided.")
                rel_tools_list = rel_hat.get("tools", [])
                rel_tools = ", ".join(rel_tools_list) if rel_tools_list else "none"

                related_hats_info.append(f"- @{rel_id}: \"{rel_desc}\" (Tools: {rel_tools})")
            except Exception as e:
                related_hats_info.append(f"- @{rel_id}: (Details not found)")

        if related_hats_info:
            relationship_context = "\n\nYou have collaborators available:\n" + "\n".join(related_hats_info) + "\nMention them using @ if you need assistance!"

    # 🧠 Assemble system prompt
    system_prompt = f"""
You are a {role} agent named '{hat_name}'.
Your tools: {tools}.
Instructions: {instructions}.
{relationship_context}
{memory_context if memory_context else ''}
""".strip()

    print("RAW PROMPT for Agent Context:", system_prompt)

    response = client.chat.completions.create(
        model=hat.get("model", "gpt-3.5-turbo"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )

    return response.choices[0].message.content


def generate_team_from_goal(goal):

    # Dynamic team_id
    team_id = f"auto_team_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    system_prompt = f"""
    You are an AI that builds specialized multi-agent teams ("Hats") for complex tasks.

    Each Hat must include:
    - hat_id: short and unique (e.g., planner_{team_id})
    - name: human-friendly name
    - model: gpt-3.5-turbo
    - role: planner, summarizer, critic, tool, researcher
    - instructions: specific task details
    - tools: [] or tool names
    - relationships: [] or related hat_ids this agent collaborates with
    - team_id: "{team_id}"
    - flow_order: 1, 2, 3...
    - qa_loop: true/false
    - critics: hat_ids that review this hat
    - active: true/false
    - memory_tags: ["tag1", "tag2"]
    - retry_limit: 1-3
    - description: 1-line purpose

    ### Goal:
    {goal}

    ### Example:
    [
      {{
        "hat_id": "planner_{team_id}",
        "name": "Planning Agent",
        "model": "gpt-3.5-turbo",
        "role": "planner",
        "instructions": "Break down tasks.",
        "tools": [],
        "relationships": ["summarizer_{team_id}"],
        "team_id": "{team_id}",
        "flow_order": 1,
        "qa_loop": false,
        "critics": [],
        "active": true,
        "memory_tags": ["planning"],
        "retry_limit": 1, 
        "description": "Plans tasks for the team."
      }},
      ...
    ]

    Output valid JSON. Include diverse roles/tools relevant to the goal.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"My goal: {goal}"}
        ],
        temperature=0.7,
        max_tokens=1200
    )

    result_text = response.choices[0].message.content

    try:
        match = re.search(r"\[.*\]", result_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            raise ValueError("No valid JSON team found in response.")
    except Exception as e:
        print("Error parsing team:", e)
        return []
    
#For Critic to pass system prompt to agent    
async def generate_openai_response_with_system(user_prompt: str, system_prompt: str, hat):
    response = client.chat.completions.create(
        model=hat.get("model", "gpt-3.5-turbo"),
        messages=[
            {"role": "system", "content": f"You are {hat.get('name', 'an AI agent')}. {hat.get('instructions', '')} {system_prompt}"},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content