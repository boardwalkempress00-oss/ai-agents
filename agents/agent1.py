"""
Personal Assistant Agent

Demonstrates AgentSpan patterns for a portfolio project:
- Tool calling (current local time)
- Conversation memory across multi-turn CLI sessions
"""

import logging
from datetime import datetime

from dotenv import load_dotenv

from agentspan.agents import Agent, AgentRuntime, ConversationMemory, run, tool

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(override=True)
logging.basicConfig(level=logging.WARNING, force=True)
logging.disable(logging.INFO)

AGENT_NAME = "personal_assistant"
AGENT_MODEL = "openai/gpt-5"
MAX_MEMORY_MESSAGES = 50
EXIT_COMMAND = "q"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

ASSISTANT_INSTRUCTIONS = (
    "You are a concise personal assistant. "
    "If the user asks what time it is, call get_current_time and answer using the tool result. "
    "Do not say you need more context."
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@tool
def get_current_time() -> str:
    """
    Get the current local time.

    This tool should be called whenever the user asks what time it is.

    Returns:
        The current local time formatted as ``YYYY-MM-DD HH:MM:SS``.
    """
    return f"The current local time is {datetime.now().strftime(DATETIME_FORMAT)}"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

conversation_memory = ConversationMemory(max_messages=MAX_MEMORY_MESSAGES)

assistant = Agent(
    name=AGENT_NAME,
    model=AGENT_MODEL,
    instructions=ASSISTANT_INSTRUCTIONS,
    tools=[get_current_time],
    memory=conversation_memory,
)

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------


def run_turn(prompt: str, runtime: AgentRuntime) -> None:
    """
    Run one assistant turn and print the result.

    Args:
        prompt: The user's message for this turn.
        runtime: Active AgentSpan runtime for the session.
    """
    result = run(assistant, prompt, runtime=runtime)
    result.print_result()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the personal assistant REPL until the user types 'q'."""
    print("Starting agent...")

    with AgentRuntime() as runtime:
        while True:
            prompt = input("You: ").strip()
            if prompt.lower() == EXIT_COMMAND:
                break
            if not prompt:
                continue
            run_turn(prompt, runtime)

    print("Agent shutting down...")


if __name__ == "__main__":
    main()
