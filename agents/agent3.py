"""
Research & Publishing Agent

Demonstrates AgentSpan multi-agent orchestration for a portfolio project:
- Tool calling (web search and page fetch via Firecrawl)
- Sequential, parallel, and nested pipeline strategies
- Long-running worker mode for nested pipeline serving
- Markdown report export from agent output
"""

import logging
import os
import re
import warnings
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Silence Firecrawl's Pydantic "field name shadows attribute" warnings before
# the SDK is imported anywhere in the process.
warnings.filterwarnings("ignore", message='Field name "json" in .* shadows an attribute')

from agentspan.agents import Agent, AgentRuntime, run, tool

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(override=True)
logging.basicConfig(level=logging.WARNING, force=True)
logging.disable(logging.INFO)

AGENT_MODEL = "openai/gpt-5.4"
MODES = {"sequential", "parallel", "nested", "worker"}
DEFAULT_MODE = "nested"
DEFAULT_TOPIC = "AI agents in production in 2026"
REPORTS_DIR = Path("reports")
MAX_PAGE_CHARS = 4000

RESEARCHER_INSTRUCTIONS = (
    "Research the topic thoroughly. Call search_web first, then fetch_page on "
    "the most relevant results. Write factual notes citing each claim. "
    "Always end your output with a '## Sources' section listing every URL you "
    "actually fetched, one per line, as markdown links: '- [title](url)'."
)

WRITER_INSTRUCTIONS = (
    "Turn research notes into a clear, well-structured article. "
    "Preserve the '## Sources' section verbatim at the end."
)

EDITOR_INSTRUCTIONS = (
    "Polish the article for publication. Improve clarity and tighten writing. "
    "Do not modify or remove the '## Sources' section."
)

MARKET_ANALYST_INSTRUCTIONS = "Analyze market opportunity and adoption trends."

RISK_ANALYST_INSTRUCTIONS = "Analyze technical, security, and operational risks."

FINANCIAL_ANALYST_INSTRUCTIONS = "Analyze business model and financial impact."

ANALYSIS_TEAM_INSTRUCTIONS = "Synthesize the analyst outputs into one concise brief."

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def _get_firecrawl_client():
    """
    Return a Firecrawl client using the API key from the environment.

    Import is deferred so the module-level warning filter runs first.
    """
    from firecrawl import Firecrawl

    return Firecrawl(api_key=os.environ["FIRECRAWL_API_KEY"])


@tool(credentials=["FIRECRAWL_API_KEY"])
def search_web(query: str, limit: int = 5) -> list[dict]:
    """
    Search the web with Firecrawl.

    Args:
        query: Search terms for the web query.
        limit: Maximum number of results to return.

    Returns:
        A list of dicts with title, url, and description keys.
    """
    client = _get_firecrawl_client()
    response = client.search(query, limit=limit)
    return [
        {"title": r.title or "", "url": r.url or "", "description": r.description or ""}
        for r in (response.web or [])
    ]


@tool(credentials=["FIRECRAWL_API_KEY"])
def fetch_page(url: str) -> str:
    """
    Fetch a web page as markdown via Firecrawl.

    Content is truncated to fit within the LLM context window.

    Args:
        url: The page URL to scrape.

    Returns:
        Markdown content, or a not-found message when the page is empty.
    """
    client = _get_firecrawl_client()
    document = client.scrape(url, formats=["markdown"])
    markdown = document.markdown or ""
    return markdown[:MAX_PAGE_CHARS] if markdown else f"No content found at {url}."


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

researcher = Agent(
    name="researcher",
    model=AGENT_MODEL,
    instructions=RESEARCHER_INSTRUCTIONS,
    tools=[search_web, fetch_page],
)

writer = Agent(
    name="writer",
    model=AGENT_MODEL,
    instructions=WRITER_INSTRUCTIONS,
)

editor = Agent(
    name="editor",
    model=AGENT_MODEL,
    instructions=EDITOR_INSTRUCTIONS,
)

market_analyst = Agent(
    name="market",
    model=AGENT_MODEL,
    instructions=MARKET_ANALYST_INSTRUCTIONS,
)

risk_analyst = Agent(
    name="risk",
    model=AGENT_MODEL,
    instructions=RISK_ANALYST_INSTRUCTIONS,
)

financial_analyst = Agent(
    name="financial",
    model=AGENT_MODEL,
    instructions=FINANCIAL_ANALYST_INSTRUCTIONS,
)

analysis_team = Agent(
    name="analysis_team",
    model=AGENT_MODEL,
    instructions=ANALYSIS_TEAM_INSTRUCTIONS,
    agents=[market_analyst, risk_analyst, financial_analyst],
    strategy="parallel",
)

# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------

publish_pipeline = researcher >> writer >> editor
nested_pipeline = analysis_team >> researcher >> writer >> editor

PIPELINES = {
    "sequential": publish_pipeline,
    "parallel": analysis_team,
    "nested": nested_pipeline,
}

# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------


def slugify(text: str) -> str:
    """Convert a topic into a safe filename slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "report"


def render_output(output: str | dict[str, Any]) -> str:
    """
    Render the agent's output dict (or string) as clean markdown.

    For parallel runs, sub-agent results from ``subResults`` are appended
    as separate sections below the primary result.
    """
    if isinstance(output, str):
        return output
    if not isinstance(output, dict):
        return str(output)

    sections = []
    primary_result = output.get("result")
    if primary_result:
        sections.append(str(primary_result).strip())

    sub_results = output.get("subResults") or {}
    for name, sub_body in sub_results.items():
        if sub_body:
            sections.append(f"## {name.title()}\n\n{str(sub_body).strip()}")

    return "\n\n---\n\n".join(sections) if sections else str(output)


def save_report(mode: str, topic: str, output: str | dict[str, Any]) -> Path:
    """
    Write the final report to ``reports/<mode>-<slug>.md``.

    Args:
        mode: Pipeline mode used for the run (e.g. ``nested``).
        topic: Original research topic, used as the report title.
        output: Raw agent output to render as markdown body content.

    Returns:
        Path to the written report file.
    """
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{mode}-{slugify(topic)}.md"
    report_body = render_output(output)
    path.write_text(f"# {topic}\n\n_Mode: {mode}_\n\n{report_body}\n")
    return path


# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------


def run_pipeline(mode: str, topic: str) -> None:
    """
    Run the selected pipeline for a topic and save the report.

    Args:
        mode: One of ``sequential``, ``parallel``, or ``nested``.
        topic: Research topic passed to the pipeline.
    """
    with AgentRuntime() as runtime:
        result = run(PIPELINES[mode], topic, runtime=runtime)
        print("Execution ID:", result.execution_id)
        print("Status:", result.status)
        path = save_report(mode, topic, result.output)
        print(f"Report saved to {path}")


def serve_worker() -> None:
    """Block and serve the nested pipeline via AgentRuntime worker mode."""
    with AgentRuntime() as runtime:
        runtime.serve(nested_pipeline, blocking=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def prompt_mode() -> str:
    """
    Prompt the user to select a pipeline mode.

    Returns:
        A validated mode string from ``MODES``.
    """
    while True:
        choice = input(f"Mode {sorted(MODES)}: ").strip().lower() or DEFAULT_MODE
        if choice in MODES:
            return choice
        print(f"Invalid mode. Pick one of {sorted(MODES)}.")


def main() -> None:
    """Entry point: select a mode, then run a pipeline or start the worker."""
    mode = prompt_mode()
    if mode == "worker":
        serve_worker()
    else:
        topic = input("Topic: ").strip() or DEFAULT_TOPIC
        run_pipeline(mode, topic)


if __name__ == "__main__":
    main()
