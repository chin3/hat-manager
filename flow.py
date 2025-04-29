import re
import json
from hat_manager import list_hats_by_team, add_memory_to_hat, search_memory
from prompts import generate_openai_response, generate_openai_response_with_system
from utils import generate_unique_hat_id

import chainlit as cl
import openai
import os
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def run_team_flow(team_id, input_text):
    #log the state of the current hat
    current_hat = cl.user_session.get("current_hat")
    cl.user_session.set("previous_hat", current_hat)
    # Load and sort the team hats based on flow_order
    team_hats = list_hats_by_team(team_id)
    team_hats = sorted(team_hats, key=lambda h: h.get("flow_order", 0))

    current_input = input_text
    conversation_log = []
    retry_counts = {}

    for hat in team_hats:
        hat_name = hat.get("name", "Unnamed Hat")
        hat_id = hat.get("hat_id")
        qa_loop = hat.get("qa_loop", False)
        retry_limit = hat.get("retry_limit", 0)

        # --- Run the hat's response ---
        response_text = generate_openai_response(current_input, hat)

        # Save memory (input and output separately)
        add_memory_to_hat(hat_id, current_input, role="user")
        add_memory_to_hat(hat_id, response_text, role="bot")

        # Show the response in the chat
        await cl.Message(content=f"🧢 **{hat_name}** responded:\n{response_text}").send()

        # Log the conversation
        conversation_log.append({
            "hat_name": hat_name,
            "hat_id": hat_id,
            "input": current_input,
            "output": response_text
        })

        # Handle QA loop if enabled
        if qa_loop:
            handled = await handle_qa_loop(
                hat, team_hats, conversation_log, retry_counts, retry_limit, team_id
            )
            if handled:
                return  # Pause here if QA loop is triggered

        # Pass the output to the next hat
        current_input = response_text

    # # --- Final Summary ---
    # log_text = "\n\n".join([
    #     f"🧢 **{entry['hat_name']}**\n**Input:** {entry['input']}\n**Output:** {entry['output']}"
    #     for entry in conversation_log
    # ])
    # await cl.Message(content=f"📜 **Full Team Conversation Log:**\n\n{log_text}").send()
    await cl.Message(content="✅ **Team flow completed successfully!**").send()

async def handle_qa_loop(hat, team_hats, conversation_log, retry_counts, retry_limit, team_id):
    response_text = conversation_log[-1]['output']

    if "#REVISION_REQUIRED" in response_text:
        retry_target_index = len(conversation_log) - 2
        retry_target = conversation_log[retry_target_index] if retry_target_index >= 0 else None

        if retry_target:
            retry_counts[retry_target['hat_id']] = retry_counts.get(retry_target['hat_id'], 0) + 1

            if retry_counts[retry_target['hat_id']] <= retry_limit:
                await cl.Message(content=f"🔁 Critic requested revision. Retrying {retry_target['hat_name']} with feedback...").send()

                prev_hat = next(h for h in team_hats if h['hat_id'] == retry_target['hat_id'])

                # 🛠 Instead of resending original input blindly, attach Critic's feedback
                improved_input = (
                    f"{retry_target['input']}\n\n"
                    f"Critic Feedback: {response_text}"
                )

                # Generate new response using improved input
                retry_response = await generate_openai_response_with_system(
                    user_prompt=retry_target['input'],
                    system_prompt=f"Revision guidance: {response_text}",
                    hat=prev_hat
                )
                
                await cl.Message(content="🧠 **This was an improved attempt based on Critic feedback.**\n\nLet's see if it passes review this time!").send()
                prev_hat_tags = prev_hat.get('memory_tags', [])
                add_memory_to_hat(prev_hat['hat_id'], improved_input, role="user", tags=prev_hat_tags, session=cl.user_session)
                add_memory_to_hat(prev_hat['hat_id'], retry_response, role="bot", tags=prev_hat_tags, session=cl.user_session)
                
                await cl.Message(content=f"🧢 {prev_hat['name']} retry responded:\n{retry_response}").send()

                # Critic re-reviews the new retry
                critic_response = generate_openai_response(retry_response, hat)

                qa_tags = hat.get('memory_tags', [])
                add_memory_to_hat(hat['hat_id'], retry_response, role="user", tags=qa_tags, session=cl.user_session)
                add_memory_to_hat(hat['hat_id'], critic_response, role="bot", tags=qa_tags, session=cl.user_session)

                await cl.Message(content=f"🧢 {hat['name']} re-reviewed:\n{critic_response}").send()

                if "#APPROVED" in critic_response:
                    await cl.Message(content="✅ Critic approved after retry!").send()
                else:
                    await cl.Message(content="⚠️ Critic did not tag correctly. Manual review needed.").send()

                await cl.Message(content="🧑‍⚖️ Approve or Retry? Type `approve` or `retry`.").send()
                cl.user_session.set("awaiting_user_approval", True)
                cl.user_session.set("pending_critique_input", retry_response)
                cl.user_session.set("pending_team_id", team_id)
                return True  # Pause for user approval
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
