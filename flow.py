import re
import json
from hat_manager import list_hats_by_team, add_memory_to_hat, search_memory
from utils import generate_unique_hat_id

import chainlit as cl
import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def run_team_flow(team_id, input_text):
    team_hats = list_hats_by_team(team_id)
    current_input = input_text
    conversation_log = []
    retry_counts = {}

    i = 0
    while i < len(team_hats):
        hat = team_hats[i]
        hat_name = hat.get('name')
        hat_id = hat.get('hat_id')
        qa_loop = hat.get('qa_loop', False)
        retry_limit = hat.get('retry_limit', 0)

        response_text = generate_openai_response(current_input, hat)

        add_memory_to_hat(hat_id, current_input, role="user")
        add_memory_to_hat(hat_id, response_text, role="bot")

        await cl.Message(content=f"🧢 {hat_name} responded:\n{response_text}").send()

        conversation_log.append({
            "hat_name": hat_name,
            "hat_id": hat_id,
            "input": current_input,
            "output": response_text
        })

        if qa_loop:
            handled = await handle_qa_loop(
                hat, team_hats, conversation_log, retry_counts, retry_limit, team_id
            )
            if handled:
                return  # Exit or pause here for user approval

        current_input = response_text
        i += 1

    log_text = "\n\n".join([
        f"🧢 {entry['hat_name']}:\nInput: {entry['input']}\nOutput: {entry['output']}"
        for entry in conversation_log
    ])
    await cl.Message(content=f"📜 **Full Conversation Log:**\n\n{log_text}").send()
    await cl.Message(content="✅ Team flow complete!").send()


def generate_openai_response(prompt: str, hat: dict):
    hat_name = hat.get('name', 'Unnamed Agent')
    hat_id = hat.get('hat_id')
    instructions = hat.get('instructions', '')
    role = hat.get('role', 'agent')
    tools = ", ".join(hat.get('tools', [])) or "none"

    memory_context = ""
    relevant_memories = search_memory(hat_id, prompt, k=3)
    if relevant_memories:
        formatted = "\n".join([
            f"{meta.get('role', 'unknown').capitalize()} ({meta.get('timestamp', 'no time')}): {doc}"
            for doc, meta in relevant_memories if meta and doc
        ])
        memory_context = f"\n\nRelevant Memories:\n{formatted}"

    system_prompt = f"""
You are a {role} agent named '{hat_name}'.
Your tools: {tools}.
Instructions: {instructions}.
{memory_context if memory_context else ''}
""".strip()

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


async def handle_qa_loop(hat, team_hats, conversation_log, retry_counts, retry_limit, team_id):
    response_text = conversation_log[-1]['output']
    if "#REVISION_REQUIRED" in response_text:
        retry_target_index = len(conversation_log) - 2
        retry_target = conversation_log[retry_target_index] if retry_target_index >= 0 else None

        if retry_target:
            retry_counts[retry_target['hat_id']] = retry_counts.get(retry_target['hat_id'], 0) + 1

            if retry_counts[retry_target['hat_id']] <= retry_limit:
                await cl.Message(content=f"🔁 Critic requested revision. Retrying {retry_target['hat_name']}...").send()

                prev_hat = next(h for h in team_hats if h['hat_id'] == retry_target['hat_id'])
                retry_response = generate_openai_response(retry_target['input'], prev_hat)

                add_memory_to_hat(prev_hat['hat_id'], retry_target['input'], role="user")
                add_memory_to_hat(prev_hat['hat_id'], retry_response, role="bot")

                await cl.Message(content=f"🧢 {prev_hat['name']} retry responded:\n{retry_response}").send()

                critic_response = generate_openai_response(retry_response, hat)

                add_memory_to_hat(hat['hat_id'], retry_response, role="user")
                add_memory_to_hat(hat['hat_id'], critic_response, role="bot")

                await cl.Message(content=f"🧢 {hat['name']} re-reviewed:\n{critic_response}").send()

                if "#APPROVED" in critic_response:
                    await cl.Message(content="✅ Critic approved after retry!").send()
                else:
                    await cl.Message(content="⚠️ Critic did not tag correctly. Manual review needed.").send()

                await cl.Message(content="🧑‍⚖️ Approve or Retry? Type `approve` or `retry`.").send()
                cl.user_session.set("awaiting_user_approval", True)
                cl.user_session.set("pending_critique_input", retry_response)
                cl.user_session.set("pending_team_id", team_id)
                return True  # Indicate we paused for approval
            else:
                await cl.Message(content="⚠️ Retry limit reached. Proceeding.").send()
    elif "#APPROVED" in response_text:
        await cl.Message(content="✅ Critic approved!").send()
        await cl.Message(content="🧑‍⚖️ Approve or Retry? Type `approve` or `retry`.").send()
        cl.user_session.set("awaiting_user_approval", True)
        cl.user_session.set("pending_critique_input", conversation_log[-1]['input'])
        cl.user_session.set("pending_team_id", team_id)
        return True
    else:
        await cl.Message(content="⚠️ No valid tag from Critic. Manual review needed.").send()
        await cl.Message(content="🧑‍⚖️ Approve or Retry? Type `approve` or `retry`.").send()
        cl.user_session.set("awaiting_user_approval", True)
        cl.user_session.set("pending_critique_input", conversation_log[-1]['input'])
        cl.user_session.set("pending_team_id", team_id)
        return True
    return False


def generate_team_from_goal(goal):
    system_prompt = """
    You are an AI that creates AI agent teams for complex tasks. Each agent (Hat) has a unique role.
    
    Based on the goal, define a team with:
    - hat_id
    - name
    - role (planner, summarizer, critic, tool_agent)
    - model (gpt-3.5 or gpt-4)
    - instructions
    - tools (list)
    - flow_order (number)
    - qa_loop (true/false)
    - team_id ("auto_team")

    Output valid JSON. Example:
    [
      {
        "hat_id": "planner",
        "name": "Planning Agent",
        "role": "planner",
        "model": "gpt-3.5",
        "instructions": "Break tasks into steps and assign to the summarizer.",
        "tools": [],
        "flow_order": 1,
        "qa_loop": false,
        "team_id": "auto_team"
      }
    ]
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"My goal: {goal}"}
        ],
        temperature=0.5,
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
