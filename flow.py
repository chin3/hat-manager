import datetime
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


async def finalize_team_flow(conversation_log, mission_success, revision_required, goal_description, team_id):
    log_text = "\n\n".join([
        f"🧢 **{entry['hat_name']}**\n**Input:** {entry['input']}\n**Output:** {entry['output']}"
        for entry in conversation_log
    ])
    await cl.Message(content=f"📜 **Full Team Conversation Log:**\n\n{log_text}").send()
    await cl.Message(content="✅ **Team flow completed successfully!**").send()

    try:
        # Calculate mission status
        if mission_success and not revision_required:
            mission_status = "🎖️ Mission Status: SUCCESS"
        elif mission_success and revision_required:
            mission_status = "⚠️ Mission Status: PARTIAL SUCCESS (after revisions)"
        else:
            mission_status = "❌ Mission Status: FAILED"

        mission_debrief_prompt = (
            f"{mission_status}\n\n"
            f"You are an AI mission analyst.\n\n"
            f"Based on the following team conversation log, generate a clear, professional mission debrief.\n\n"
            f"Focus on:\n"
            f"- Goal Achievement\n"
            f"- Teamwork dynamics (Storyteller, Critic)\n"
            f"- Any improvements or challenges encountered\n"
            f"- Overall mission outcome.\n\n"
            f"Here is the conversation log:\n\n"
            f"{log_text}\n\n"
            f"Respond in a formal but friendly tone. Keep it concise."
        )

        debrief_summary = generate_openai_response(mission_debrief_prompt, hat={"name": "Mission Analyst", "model": "gpt-3.5-turbo", "instructions": ""})
        await cl.Message(content=f"📜 **Mission Debrief:**\n\n{debrief_summary}").send()

        # Awards Ceremony
        try:
            agent_contributions = {}
            for entry in conversation_log:
                hat_name = entry.get('hat_name', 'Unknown')
                agent_contributions[hat_name] = agent_contributions.get(hat_name, 0) + 1

            if agent_contributions:
                mvp_agent = max(agent_contributions.items(), key=lambda x: x[1])[0]
                awards_text = (
                    "🎉 **Agent Awards Ceremony** 🎉\n\n"
                    f"🏆 **MVP (Most Valuable Agent):** {mvp_agent}\n"
                )
                if len(agent_contributions) > 1:
                    sorted_agents = sorted(agent_contributions.items(), key=lambda x: x[1], reverse=True)
                    runner_up = sorted_agents[1][0]
                    awards_text += f"🥈 **Outstanding Contributor:** {runner_up}\n"

                awards_text += "\n🎖️ Thanks to all agents for their teamwork!"
                await cl.Message(content=awards_text).send()
        except Exception as e:
            await cl.Message(content=f"⚠️ Failed to generate Agent Awards: {e}").send()

    except Exception as e:
        await cl.Message(content=f"⚠️ Failed to generate Mission Debrief: {e}").send()
    cl.user_session.set("pending_conversation_log", None)
    cl.user_session.set("pending_mission_success", None)
    cl.user_session.set("pending_revision_required", None)
    cl.user_session.set("pending_goal_description", None)
    # 🎤 Final Agent Reflections
    try:
        await cl.Message(content="🎤 **Final Agent Reflections:**").send()
        team_id = cl.user_session.get("pending_team_id")
        
        agent_reflections = {}
        team_hats = list_hats_by_team(team_id)  # Re-load team hats
        for hat in team_hats:
            hat_name = hat.get('name', 'Unnamed Hat')

            reflection_prompt = (
                f"You are {hat_name}. The mission has completed.\n\n"
                f"Write a short (1-2 sentences) personal reflection about your experience during this mission.\n"
                f"Be professional but friendly. Highlight anything you enjoyed or found challenging."
            )

            reflection_response = generate_openai_response(reflection_prompt, hat)
            agent_reflections[hat_name] = reflection_response  # 🧠 Save reflection
            try:
                mission_record = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "goal_description": goal_description,
                    "mission_status": mission_status,
                    "conversation_log": conversation_log,
                    "debrief_summary": debrief_summary,
                    "agent_reflections": agent_reflections
                }

                MISSIONS_DIR = "./missions"
                if not os.path.exists(MISSIONS_DIR):
                    os.makedirs(MISSIONS_DIR)

                filename = os.path.join(MISSIONS_DIR, f"mission_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json")

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(mission_record, f, indent=2, ensure_ascii=False)

                await cl.Message(content=f"🗂️ Mission archived successfully to `{filename}`.").send()

            except Exception as e:
                await cl.Message(content=f"⚠️ Failed to archive mission: {e}").send()

            await cl.Message(content=f"🧢 **{hat_name}**: {reflection_response}").send()

    except Exception as e:
        await cl.Message(content=f"⚠️ Failed to generate agent reflections: {e}").send()


async def run_team_flow(team_id, goal_description):
    #flags
    mission_success = False
    revision_required = False
    #log the state of the current hat
    current_hat = cl.user_session.get("current_hat")
    cl.user_session.set("previous_hat", current_hat)
    # Load and sort the team hats based on flow_order
    team_hats = list_hats_by_team(team_id)
    team_hats = sorted(team_hats, key=lambda h: h.get("flow_order", 0))

    current_input = goal_description
    conversation_log = []
    retry_counts = {}
    await cl.Message(
    content=f"🎯 **Mission Briefing:**\n\n> {goal_description}\n\n🧠 Deploying team agents to complete the mission..."
).send()

    for hat in team_hats:
        hat_name = hat.get("name", "Unnamed Hat")
        hat_id = hat.get("hat_id")
        qa_loop = hat.get("qa_loop", False)
        retry_limit = hat.get("retry_limit", 0)

        # --- Run the hat's response ---
        if hat.get('role') == 'critic':
            critic_input = (
                f"## Goal\n"
                f"{goal_description}\n\n"
                f"## Storyteller Output\n"
                f"{current_input}\n\n"
                f"## Instructions\n"
                "First, rate the output across three categories from 1 to 10:\n"
                "- 🎯 Goal Coverage\n"
                "- 🧹 Language Clarity\n"
                "- 💡 Creativity\n\n"
                "Format your scores like this:\n"
                "Goal Coverage: X/10\nLanguage Clarity: Y/10\nCreativity: Z/10\n\n"
                "Then, briefly summarize if and how the output satisfies the goal.\n"
                "Finally, respond with one of these tags at the start of a new paragraph:\n"
                "- #APPROVED (excellent overall)\n"
                "- #REVISION_REQUIRED (minor improvements needed)\n"
                "- #REJECTED (major issues).\n\n"
                "Be strict: Only approve if Goal Coverage is 9/10 or higher, and other categories are reasonably strong (8+/10). Otherwise, request revision."
            )
            response_text = generate_openai_response(critic_input, hat)
            if "#REVISION_REQUIRED" in response_text:
                revision_required = True
            if "#APPROVED" in response_text:
                mission_success = True
                        
        else:
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
                                # --- Save state before pausing for user approval ---
                cl.user_session.set("pending_conversation_log", conversation_log)
                cl.user_session.set("pending_mission_success", mission_success)
                cl.user_session.set("pending_revision_required", revision_required)
                cl.user_session.set("pending_goal_description", goal_description)
                cl.user_session.set("pending_team_id", team_id)
                return  # Pause here if QA loop is triggered

        # Pass the output to the next hat
        current_input = response_text

    # --- Final Summary ---
    log_text = "\n\n".join([
        f"🧢 **{entry['hat_name']}**\n**Input:** {entry['input']}\n**Output:** {entry['output']}"
        for entry in conversation_log
    ])
    await cl.Message(content=f"📜 **Full Team Conversation Log:**\n\n{log_text}").send()
    await cl.Message(content="✅ **Team flow completed successfully!**").send()
    try:
        mission_debrief_prompt = (
            f"You are an AI mission analyst.\n\n"
            f"Based on the following team conversation log, generate a clear, professional mission debrief.\n\n"
            f"Focus on:\n"
            f"- Goal Achievement\n"
            f"- Teamwork dynamics (Storyteller, Critic)\n"
            f"- Any improvements or challenges encountered\n"
            f"- Overall mission outcome.\n\n"
            f"Here is the conversation log:\n\n"
            f"{log_text}\n\n"
            f"Respond in a formal but friendly tone. Keep it concise."
        )

        debrief_summary = generate_openai_response(mission_debrief_prompt, hat={"name": "Mission Analyst", "model": "gpt-3.5-turbo", "instructions": ""})

        await cl.Message(content=f"📜 **Mission Debrief:**\n\n{debrief_summary}").send()
        try:
            # Count number of outputs from each agent
            agent_contributions = {}
            for entry in conversation_log:
                hat_name = entry.get('hat_name', 'Unknown')
                agent_contributions[hat_name] = agent_contributions.get(hat_name, 0) + 1

            # Decide awards
            if agent_contributions:
                mvp_agent = max(agent_contributions.items(), key=lambda x: x[1])[0]  # Most active agent

                awards_text = (
                    "🎉 **Agent Awards Ceremony** 🎉\n\n"
                    f"🏆 **MVP (Most Valuable Agent):** {mvp_agent}\n"
                )

                if len(agent_contributions) > 1:
                    sorted_agents = sorted(agent_contributions.items(), key=lambda x: x[1], reverse=True)
                    runner_up = sorted_agents[1][0]
                    awards_text += f"🥈 **Outstanding Contributor:** {runner_up}\n"

                awards_text += "\n🎖️ Thanks to all agents for their teamwork!"

                await cl.Message(content=awards_text).send()
        except Exception as e:
            await cl.Message(content=f"⚠️ Failed to generate Agent Awards: {e}").send()        

    except Exception as e:
        await cl.Message(content=f"⚠️ Failed to generate Mission Debrief: {e}").send()

async def handle_qa_loop(hat, team_hats, conversation_log, retry_counts, retry_limit, team_id):
    response_text = conversation_log[-1]['output']

    if "#REVISION_REQUIRED" in response_text:
        revision_required = True
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
                    mission_success = True
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
