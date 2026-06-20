"""
Personal Assistant Agent

This script defines a concise personal assistant agent using the agentspan library.
The agent is capable of responding to questions about the current local time, utilizing a registered tool function.
Interaction is handled via the command line, with conversation memory preserved for context.
"""

import logging
from datetime import datetime
from dotenv import load_dotenv

from agentspan.agents import (
    Agent,
    AgentRuntime,
    ConversationMemory,
    run,
    tool,
)

# Load environment variables from .env file for configuration
load_dotenv()

# Configure logging to minimize log noise; warnings or higher will be displayed
logging.basicConfig(level=logging.WARNING)
logging.getLogger("agentspan").setLevel(logging.WARNING)
logging.getLogger("conductor").setLevel(logging.WARNING)

@tool
def get_current_time() -> str:
    """
    Get the current local time.

    This tool should be called whenever the user asks what time it is.
    Returns:
        str: The current local time formatted as 'YYYY-MM-DD HH:MM:SS'.
    """
    return f"The current local time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

# Initialize conversation memory with a limit of 50 messages
conversation_memory = ConversationMemory(max_messages=50)

# Instantiate the agent with specific instructions and tools
assistant = Agent(
    name="personal_assistant",
    model="openai/gpt-5",
    instructions=(
        "You are a concise personal assistant. "
        "If the user asks what time it is, call get_current_time and answer using the tool result. "
        "Do not say you need more context."
    ),
    tools=[get_current_time],
    memory=conversation_memory,
)

def main():
    """
    Entry point for running the personal assistant agent in an interactive CLI loop.
    The user can enter queries, and the agent will respond accordingly.
    Type 'q' to exit the session.
    """
    print("Starting agent...")

    with AgentRuntime() as runtime:
        while True:
            prompt = input("You: ").strip()
            if prompt.lower() == "q":
                break  # Exit on 'q'
            if not prompt:
                continue  # Skip empty input

            # Run the agent with the user's prompt and get the result
            result = runtime.run(assistant, prompt)
            readable_result = result.output.get('result')

            # Update the conversation memory
            conversation_memory.add_user_message(prompt)
            conversation_memory.add_assistant_message(readable_result)

            # Print the agent's output
            result.print_result()

if __name__ == "__main__":
    main()