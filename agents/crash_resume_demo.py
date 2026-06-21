"""
Crash & Resume Demo

Demonstrates AgentSpan durable execution:
- Start a long-running multi-step workflow
- Resume a prior run by execution ID after interruption
"""

import logging
import time

from dotenv import load_dotenv

from agentspan.agents import Agent, AgentHandle, AgentRuntime, EventType, start, tool

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(override=True)
logging.basicConfig(level=logging.WARNING, force=True)
logging.disable(logging.INFO)

AGENT_NAME = "durable_demo_agent"
AGENT_MODEL = "openai/gpt-5.4"
MAX_TURNS = 20
WORKFLOW_STEPS = 10
SLOW_STEP_TIMEOUT_SECONDS = 30
SLOW_STEP_SLEEP_SECONDS = 3
WORKFLOW_PROMPT = "Run the 10-step workflow."

MODE_START = "start"
MODE_RESUME = "resume"

# Edit MODE before running: "start" for a new workflow, "resume" to reconnect.
MODE = MODE_RESUME

# Paste the execution ID printed by a prior "start" run when MODE is "resume".
EXECUTION_ID = "paste the printed execution ID here for resume mode"

AGENT_INSTRUCTIONS = (
    f"Run a {WORKFLOW_STEPS}-step workflow by calling slow_step once for each step, "
    f"from 1 through {WORKFLOW_STEPS}, in order. Do not skip steps."
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@tool(timeout_seconds=SLOW_STEP_TIMEOUT_SECONDS)
def slow_step(step: int) -> str:
    """
    Run one slow workflow step.

    Args:
        step: Step number in the workflow (1 through ``WORKFLOW_STEPS``).

    Returns:
        Confirmation message when the step finishes.
    """
    time.sleep(SLOW_STEP_SLEEP_SECONDS)
    return f"Finished step {step}"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

durable_agent = Agent(
    name=AGENT_NAME,
    model=AGENT_MODEL,
    instructions=AGENT_INSTRUCTIONS,
    tools=[slow_step],
    max_turns=MAX_TURNS,
)

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------


def stream_handle(handle: AgentHandle) -> None:
    """
    Stream agent events until the run completes.

    Prints the execution ID (for resume) and each event type/message.
    """
    print("Execution ID:", handle.execution_id)
    for event in handle.stream():
        print(event.type, getattr(event, "message", ""))
        if event.type == EventType.DONE:
            break


def run_start(runtime: AgentRuntime) -> None:
    """Start a fresh durable workflow and stream events until done."""
    handle = start(durable_agent, WORKFLOW_PROMPT, runtime=runtime)
    stream_handle(handle)


def run_resume(runtime: AgentRuntime) -> None:
    """Reconnect to a prior execution by ID and stream remaining events."""
    runtime.serve(durable_agent, blocking=False)
    handle = AgentHandle(execution_id=EXECUTION_ID, runtime=runtime)
    stream_handle(handle)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Dispatch start or resume mode inside an AgentRuntime context."""
    with AgentRuntime() as runtime:
        if MODE == MODE_START:
            run_start(runtime)
        elif MODE == MODE_RESUME:
            run_resume(runtime)
        else:
            raise ValueError(f"Unknown MODE: {MODE}")


if __name__ == "__main__":
    main()
