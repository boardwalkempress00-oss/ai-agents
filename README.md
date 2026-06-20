# AI Agents

Python agents built with [AgentSpan](https://www.agentspan.com/), with conversation memory and tool calling.

## Agent 1: Personal Assistant

A CLI personal assistant that answers questions and calls a `get_current_time` tool when asked for the time.

**Stack:** Python 3.12+, OpenAI GPT-5 (via AgentSpan), AgentSpan, python-dotenv

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

```sh
uv run python agents/agent1.py
```

Type your message at the `You:` prompt. Type `q` to quit.

## Project structure

```
.
├── agents/
│   └── agent1.py      # Personal assistant CLI agent
├── .env.example       # Environment variable template (copy to .env)
├── pyproject.toml     # Dependencies and project metadata
├── uv.lock            # Locked dependency versions
└── README.md
```
