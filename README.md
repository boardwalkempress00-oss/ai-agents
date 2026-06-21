# AI Agents

Python agents built with [AgentSpan](https://www.agentspan.com/), with conversation memory and tool calling.

## Agent 1: Personal Assistant

A CLI personal assistant that answers questions and calls a `get_current_time` tool when asked for the time.

**Stack:** Python 3.12+, OpenAI GPT-5 (via AgentSpan), AgentSpan, python-dotenv

## Agent 2: Customer Support

A customer support agent that handles policy questions, order lookups, and refund requests with safety controls.

**Capabilities:**

- **Knowledge base search** — Answers questions about refunds, shipping, and account tiers from a mock support docs index.
- **Order lookup** — Retrieves order status and totals from a mock database by order ID.
- **Refund processing** — Issues refunds via a tool that pauses for human approval before execution.
- **Structured output** — Returns typed responses (`SupportResponse`) with stage, success flag, and message.
- **Input guardrails** — Blocks obvious prompt-injection phrases on user input.
- **Human-in-the-loop** — Streams agent events and prompts the operator to approve or reject pending refunds.

**Stack:** Python 3.12+, OpenAI GPT-5.4 (via AgentSpan), AgentSpan, Pydantic, python-dotenv

## Prerequisites

- Python 3.12+ (see `.python-version`)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- OpenAI API access (configured through AgentSpan)
- AgentSpan server running locally (default: `http://localhost:6767/api`)

## Setup

1. Clone the repository and enter the project directory.

2. Install dependencies:

   ```sh
   uv sync
   ```

   Or with pip:

   ```sh
   pip install -e .
   ```

3. Copy the environment template and fill in your values:

   ```sh
   cp .env.example .env
   ```

   Required variables:

   - `AGENTSPAN_SERVER_URL` — AgentSpan API base URL (default: `http://localhost:6767/api`)

4. Start the AgentSpan server if it is not already running.

## Run

**Agent 1 — personal assistant:**

```sh
uv run python agents/agent1.py
```

**Agent 2 — customer support:**

```sh
uv run python agents/agent2.py
```

Type your message at the `You:` prompt. Type `q` to quit.

For Agent 2, try prompts like:

- `What is your refund policy?`
- `Look up order A100 and process a refund.`

When a refund is requested, the agent pauses and asks `Approve? (y/n):` before executing.

## Project structure

```
.
├── agents/
│   ├── agent1.py      # Personal assistant CLI agent
│   └── agent2.py      # Customer support agent with guardrails and approval flow
├── .env.example       # Environment variable template (copy to .env)
├── pyproject.toml     # Dependencies and project metadata
├── uv.lock            # Locked dependency versions
└── README.md
```
