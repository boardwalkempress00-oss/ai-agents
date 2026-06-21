# AI Agents

A progressive portfolio of CLI agents built with [AgentSpan](https://www.agentspan.com/). Each demo adds a layer of real-world complexity — from tool calling and memory, to guardrails and human approval, to multi-agent orchestration with web research.

The three agents are **standalone entry points**, not a runtime chain. Clone the repo, start the AgentSpan server, and run any agent to explore that pattern in isolation.

## Skills demonstrated

- **Tool calling** — Custom Python tools registered with AgentSpan (`get_current_time`, knowledge base search, Firecrawl web search/scrape)
- **Conversation memory** — Multi-turn context via `ConversationMemory`
- **Structured output** — Pydantic schemas for typed agent responses (`SupportResponse`)
- **Input guardrails** — Prompt-injection filtering on user input before the LLM runs
- **Human-in-the-loop** — Streaming events with operator approval for sensitive actions (refunds)
- **Multi-agent orchestration** — Sequential (`>>`), parallel, and nested pipelines across specialized agents
- **External integrations** — Firecrawl for live web research; environment-based credential handling

## Author

- **GitHub:** [@boardwalkempress00-oss](https://github.com/boardwalkempress00-oss)

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

## Agent 3: Research & Publishing

A multi-agent research pipeline that searches the web, drafts articles, and exports markdown reports.

**Capabilities:**

- **Web search & fetch** — Uses Firecrawl tools to search the web and scrape pages as markdown.
- **Sequential pipeline** — Researcher → writer → editor for end-to-end article production.
- **Parallel analysis** — Market, risk, and financial analysts run concurrently, then synthesize.
- **Nested pipeline** — Parallel analysis feeds into the full research-and-publish chain.
- **Worker mode** — Serves the nested pipeline as a long-running AgentRuntime worker.
- **Report export** — Saves output to `reports/<mode>-<topic-slug>.md`.

**Modes:**

| Mode | Behavior |
|------|----------|
| `sequential` | Research → write → edit |
| `parallel` | Run the three-analyst team only |
| `nested` | Analyst team → research → write → edit (default) |
| `worker` | Serve the nested pipeline (blocking) |

**Stack:** Python 3.12+, OpenAI GPT-5.4 (via AgentSpan), AgentSpan, Firecrawl, python-dotenv

## Data flow summary

| Stage | Input | Processing | Output |
|-------|--------|------------|--------|
| **Agent 1** | User prompt | Memory + `get_current_time` tool via AgentRuntime | Conversational reply |
| **Agent 2** | User prompt | Guardrail → RAG-style KB search → order lookup → optional refund with human approval | `SupportResponse` (Pydantic) |
| **Agent 3** | Mode + topic | Parallel analysts and/or sequential research → write → edit pipeline | Markdown report in `reports/` |

## Prerequisites

- Python 3.12+ (see `.python-version`)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- OpenAI API access (configured through AgentSpan)
- AgentSpan server — local dev (`agentspan server start`) or [Docker Compose + PostgreSQL](#production-deployment-with-postgresql--docker-compose)
- Firecrawl API key (required for Agent 3)

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
   - `FIRECRAWL_API_KEY` — Firecrawl API key (Agent 3 only)

4. Start the AgentSpan server:
   - **Dev:** [AgentSpan server](https://www.agentspan.com/) with SQLite (`agentspan server start`)
   - **Production-style:** [Docker Compose + PostgreSQL](#production-deployment-with-postgresql--docker-compose)

## Run

**Agent 1 — personal assistant:**

```sh
uv run python agents/agent1.py
```

**Agent 2 — customer support:**

```sh
uv run python agents/agent2.py
```

**Agent 3 — research & publishing:**

```sh
uv run python agents/agent3.py
```

For Agents 1 and 2, type your message at the `You:` prompt. Type `q` to quit.

For Agent 2, try prompts like:

- `What is your refund policy?`
- `Look up order A100 and process a refund.`

When a refund is requested, the agent pauses and asks `Approve? (y/n):` before executing.

For Agent 3, pick a mode at the prompt (`sequential`, `parallel`, `nested`, or `worker`), then enter a research topic. Reports are written to the `reports/` directory (created automatically, gitignored).

## Production Deployment with PostgreSQL + Docker Compose

For a production-style setup, run the AgentSpan server with **PostgreSQL 16** instead of the default SQLite dev server. PostgreSQL persists execution state across restarts and supports multiple Python workers connecting concurrently — the pattern used in real deployments.

### Why PostgreSQL?

| Dev (SQLite) | Production-style (PostgreSQL) |
|--------------|-------------------------------|
| Zero config, single process | Durable, ACID-compliant storage |
| Fine for local experimentation | Survives server restarts |
| | Safe for multiple workers |

The compose stack lives in `deployment/docker-compose/` and is based on the [official AgentSpan deployment](https://github.com/agentspan-ai/agentspan/tree/main/deployment/docker-compose).

### Start the stack

```sh
cd deployment/docker-compose
cp .env.example .env
```

Edit `.env` and set:

- `AGENTSPAN_MASTER_KEY` — run `openssl rand -base64 32`
- `POSTGRES_PASSWORD` — change from the default
- `OPENAI_API_KEY` — your OpenAI key

Then start the services:

```sh
docker compose up -d
```

This starts:

- **agentspan** — AgentSpan server on port **6767**
- **postgres** — PostgreSQL 16 with a persistent Docker volume

### Check the AgentSpan UI

Open **http://localhost:6767** in your browser to view the execution dashboard.

Verify health:

```sh
curl http://localhost:6767/actuator/health
```

See `deployment/docker-compose/README.md` for logs, stop/cleanup, and troubleshooting.

### Run local Python workers against the stack

From the repository root, point your agents at the running server:

```sh
export AGENTSPAN_SERVER_URL=http://localhost:6767
uv run python agents/agent3.py
```

Worker secrets (`FIRECRAWL_API_KEY`, etc.) stay in the root `.env` — only server and database config go in `deployment/docker-compose/.env`.

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|----------------|-----|
| Connection error / agent won't start | AgentSpan server not running | Start the [AgentSpan server](https://www.agentspan.com/) and confirm `AGENTSPAN_SERVER_URL` in `.env` |
| `KeyError: FIRECRAWL_API_KEY` | Missing Firecrawl key (Agent 3 only) | Add `FIRECRAWL_API_KEY` to `.env` — get a key at [firecrawl.dev](https://www.firecrawl.dev/) |
| Agent 2 refund prompt shows `$0.00` | Order lookup didn't run before refund | Ask for order ID first, e.g. `Look up order A100 and process a refund` |
| Empty or blocked Agent 2 response | Input guardrail triggered | Rephrase without injection phrases (`ignore`, `jailbreak`, `system prompt`, etc.) |
| Agent 3 worker mode hangs | Expected behavior | Worker mode blocks to serve the nested pipeline; use `Ctrl+C` to stop |

## Project structure

```
.
├── agents/
│   ├── agent1.py           # Personal assistant CLI agent
│   ├── agent2.py           # Customer support agent with guardrails and approval flow
│   ├── agent3.py           # Multi-agent research pipeline with Firecrawl tools
│   ├── crash_resume_demo.py # Durable execution crash/resume demo
│   └── test_agent2.py      # Mock tests for Agent 2
├── deployment/
│   └── docker-compose/     # AgentSpan server + PostgreSQL 16 stack
├── .env.example            # Worker environment template (copy to .env)
├── pyproject.toml          # Dependencies and project metadata
├── uv.lock                 # Locked dependency versions
└── README.md
```
