"""
Customer Support Agent

Demonstrates AgentSpan patterns for a portfolio project:
- Tool calling (knowledge base search, order lookup, refund processing)
- Structured output via Pydantic (SupportResponse)
- Input guardrails against prompt injection
- Human-in-the-loop approval for sensitive tool calls (process_refund)
"""

import logging

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agentspan.agents import (
    Agent,
    AgentRuntime,
    ConversationMemory,
    EventType,
    Guardrail,
    GuardrailResult,
    OnFail,
    Position,
    guardrail,
    start,
    tool,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(override=True)
logging.basicConfig(level=logging.WARNING, force=True)
logging.disable(logging.INFO)

AGENT_NAME = "support_agent"
AGENT_MODEL = "openai/gpt-5.4"
MAX_TURNS = 10
MAX_MEMORY_MESSAGES = 50
EXIT_COMMAND = "q"
APPROVAL_PROMPT = "Approve? (y/n): "
GUARDRAIL_FAIL_MESSAGE = "Please ask a normal question, this is blocked."

BLOCKED_PROMPT_PHRASES = (
    "ignore",
    "ignore previous",
    "system prompt",
    "jailbreak",
)

MOCK_DB = {
    "orders": {"A100": {"status": "delivered", "total": 149.99}},
    "accounts": {"cindy@example.com": {"status": "active", "tier": "pro"}},
}

DOCS = {
    "refund policy": "Refunds are processed within 5 business days.",
    "shipping": "Standard shipping takes 3 to 7 business days.",
    "account": "Pro accounts include priority support.",
}

# ---------------------------------------------------------------------------
# Structured output
# ---------------------------------------------------------------------------


class SupportResponse(BaseModel):
    """Structured response returned by the support agent."""

    stage: str = Field(description="Stage like answered, refunded or rejected")
    successful: bool
    message: str


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search support documentation by keyword.

    Performs a simple substring match against document titles.

    Args:
        query: The user's question or search terms.

    Returns:
        Matching document body, or a not-found message.
    """
    for title, body in DOCS.items():
        if title in query.lower():
            return body
    return "No matching support docs found."


@tool
def lookup_order(order_id: str) -> dict:
    """
    Look up an order in the mock database by ID.

    Args:
        order_id: The order identifier (e.g. "A100").

    Returns:
        Order details dict, or {"error": "Order not found"} if missing.
    """
    return MOCK_DB["orders"].get(order_id, {"error": "Order not found"})


@tool(approval_required=True)
def process_refund(order_id: str, amount: float) -> str:
    """
    Request a refund for an order.

    This tool pauses for human approval before execution.

    Args:
        order_id: The order to refund.
        amount: The refund amount.

    Returns:
        Confirmation message after approval.
    """
    return f"Refunded {amount:.2f} for order {order_id}"


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


@guardrail
def safe_support_request(prompt: str) -> GuardrailResult:
    """
    Block obvious prompt injection attempts on user input.

    Args:
        prompt: Raw user message.

    Returns:
        GuardrailResult with passed=False when a blocked phrase is detected.
    """
    passed = not any(phrase in prompt.lower() for phrase in BLOCKED_PROMPT_PHRASES)
    return GuardrailResult(passed=passed, message=GUARDRAIL_FAIL_MESSAGE)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

conversation_memory = ConversationMemory(max_messages=MAX_MEMORY_MESSAGES)

support_agent = Agent(
    name=AGENT_NAME,
    model=AGENT_MODEL,
    instructions=(
        "You are a customer support agent. Use the knowledge base first. "
        "If the customer wants a refund: when you know the order ID, call "
        "lookup_order to get the amount. Before calling process_refund, "
        "write a short plain-English sentence describing exactly what refund "
        "you are about to issue, for example: 'I am going to refund 149.99 DKK "
        "for order A100.' Then call process_refund. The tool will pause for "
        "human approval automatically. If the order ID is missing, ask the "
        "customer for it. Always populate the message field with a clear reply."
    ),
    output_type=SupportResponse,
    tools=[lookup_order, search_knowledge_base, process_refund],
    memory=conversation_memory,
    guardrails=[
        Guardrail(safe_support_request, position=Position.INPUT, on_fail=OnFail.RAISE)
    ],
    max_turns=MAX_TURNS,
)

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------


def _track_refund_context(
    event,
    order_id: str | None,
    amount: float | None,
) -> tuple[str | None, float | None]:
    """Extract order_id and amount from agent stream events."""
    if event.type == EventType.TOOL_CALL and event.args:
        order_id = event.args.get("order_id") or order_id
    elif event.type == EventType.TOOL_RESULT and isinstance(event.result, dict):
        amount = event.result.get("total") or amount
    return order_id, amount


def _handle_approval_prompt(handle, order_id: str | None, amount: float | None) -> None:
    """Prompt the operator to approve or reject a pending refund."""
    print(f"\nApproval required: refund ${amount:.2f} for order {order_id}")
    decision = input(APPROVAL_PROMPT).strip().lower()
    if decision == "y":
        handle.approve()
    else:
        handle.reject("user rejected")


def run_interactive(prompt: str) -> None:
    """
    Run one support conversation turn with streaming and approval handling.

    Args:
        prompt: The customer's message for this turn.
    """
    with AgentRuntime() as runtime:
        handle = start(support_agent, prompt, runtime=runtime)
        stream = handle.stream()

        order_id: str | None = None
        amount: float | None = None

        for event in stream:
            order_id, amount = _track_refund_context(event, order_id, amount)
            if event.type == EventType.WAITING:
                _handle_approval_prompt(handle, order_id, amount)

        agent_result = stream.get_result()
        output = agent_result.output.get("result")
        print(f"\n{output}\n")


def main() -> None:
    """Run the support bot REPL until the user types 'q'."""
    print("Support bot starting..")
    while True:
        prompt = input("You: ").strip()
        if prompt.lower() == EXIT_COMMAND:
            break
        if not prompt:
            continue
        run_interactive(prompt)
    print("Support bot shutting down...")


if __name__ == "__main__":
    main()
