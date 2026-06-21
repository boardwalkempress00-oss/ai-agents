"""
Agent 2 mock tests

Uses AgentSpan's mock_run harness to verify the support agent handles
refund policy questions via knowledge base search without a live LLM.
"""

from agentspan.agents.testing import MockEvent, expect, mock_run

from agent2 import SupportResponse, support_agent

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KB_TOOL = "search_knowledge_base"
REFUND_POLICY_QUERY = "refund policy"
USER_PROMPT = "What is the refund policy?"

MOCK_KB_RESULT = (
    "Source: support-policy.txt\nRefunds are processed within 5 business days."
)

MOCK_REPLY = "Based on our policy, refunds are processed within 5 business days."

# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------


def _refund_policy_events() -> list:
    """Build the mocked tool-call sequence for a refund policy question."""
    return [
        MockEvent.tool_call(KB_TOOL, {"query": REFUND_POLICY_QUERY}),
        MockEvent.tool_result(KB_TOOL, MOCK_KB_RESULT),
        MockEvent.done(
            SupportResponse(
                stage="answered",
                successful=True,
                approval_required=False,
                message=MOCK_REPLY,
            )
        ),
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_support_bot_refund_policy() -> None:
    """
    Verify the support agent answers refund policy questions via the KB tool.

    Mocks a search_knowledge_base call and asserts the run completes with
    refund-related output and no errors.
    """
    result = mock_run(
        support_agent,
        USER_PROMPT,
        events=_refund_policy_events(),
    )

    expect(result).completed().output_contains("refund").used_tool(
        KB_TOOL, args={"query": REFUND_POLICY_QUERY}
    ).no_errors()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Run mock tests manually without pytest."""
    test_support_bot_refund_policy()
    print("Mock test passed.")


if __name__ == "__main__":
    main()
