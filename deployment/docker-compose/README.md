# AgentSpan Docker Compose Deployment

Production-style stack for this portfolio project: **AgentSpan server + PostgreSQL 16**.

Python agents in `agents/` run on your host machine as workers and connect to the server over HTTP.

## Why PostgreSQL?

AgentSpan's default dev mode uses SQLite (single file, single process). For a production-style setup, PostgreSQL provides:

- **Durability** — execution state survives server restarts
- **Concurrent access** — multiple workers can connect safely
- **Portfolio signal** — shows you understand real deployment patterns, not just local scripts

This compose stack mirrors the [official AgentSpan deployment](https://github.com/agentspan-ai/agentspan/tree/main/deployment/docker-compose).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- An LLM provider API key (this project uses OpenAI via AgentSpan)

Verify:

```sh
docker --version
docker compose version
```

## Quick start

From the repository root:

```sh
cd deployment/docker-compose
cp .env.example .env
```

Edit `.env` and set at minimum:

1. **`AGENTSPAN_MASTER_KEY`** — generate with `openssl rand -base64 32`
2. **`POSTGRES_PASSWORD`** — change from the default `changeme`
3. **`OPENAI_API_KEY`** — your OpenAI key (required for the agents in this repo)

Start the stack:

```sh
docker compose up -d
```

## Verify the stack

| Check | URL / command |
|-------|----------------|
| AgentSpan UI | http://localhost:6767 |
| Health endpoint | http://localhost:6767/actuator/health |
| Service status | `docker compose ps` |
| Server logs | `docker compose logs --tail=100 agentspan` |

A healthy response from the health endpoint looks like `{"status":"UP"}`.

## Connect local Python workers

Return to the repository root, point workers at the running server, and run an agent:

```sh
cd ../..
export AGENTSPAN_SERVER_URL=http://localhost:6767
uv run python agents/agent3.py
```

You can also set `AGENTSPAN_SERVER_URL` in the root `.env` file (see root `.env.example`).

Worker-only secrets (e.g. `FIRECRAWL_API_KEY` for Agent 3) belong in the **root** `.env`, not in this compose `.env`.

## Stop and cleanup

```sh
# Stop services, keep database data
docker compose down

# Stop services and delete the PostgreSQL volume (irreversible)
docker compose down -v
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 6767 already in use | Set `AGENTSPAN_PORT=16767` in `.env` and use that port in `AGENTSPAN_SERVER_URL` |
| `agentspan` container exits on start | Check logs: `docker compose logs agentspan`. Often missing `AGENTSPAN_MASTER_KEY` or DB credentials |
| Python agent connection error | Confirm stack is up (`docker compose ps`) and `AGENTSPAN_SERVER_URL` matches the host port |
| Postgres health check failing | Wait ~30s on first boot; check `docker compose logs postgres` |

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | AgentSpan server + PostgreSQL 16 services |
| `.env.example` | Template for stack configuration (copy to `.env`) |
| `.env` | Local secrets — **never commit** |
