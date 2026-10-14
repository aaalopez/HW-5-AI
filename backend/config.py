"""Shared model + MCP toolset configuration for every Campus Customs agent.

Every agent in this project uses the same model (Portkey-gateway "gpt-6-luna")
and the same MCP toolset (mcp_server/server.py) as its only source of shop
facts — no agent reads data/campus_customs_new.db directly or gets a second,
hand-rolled tools layer.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.toolsets import AbstractToolset, FilteredToolset
from pydantic_ai.usage import UsageLimits

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
PROMPTS_DIR = BACKEND_DIR / "prompts"
MCP_SERVER_PATH = PROJECT_ROOT / "mcp_server" / "server.py"

load_dotenv(PROJECT_ROOT / ".env")

# Only this model is allowed for every agent in this assignment. The rule was
# stated as both "gpt 6 luna" and "gpt-g-luna" — normalized to one slug here.
# If your Portkey model id is spelled differently, this is the one place to
# fix it.
MODEL_NAME = "gpt-6-luna"

PORTKEY_BASE_URL = os.environ.get("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
PORTKEY_API_KEY = os.environ.get("PORTKEY_API_KEY")
PORTKEY_VIRTUAL_KEY = os.environ.get("PORTKEY_VIRTUAL_KEY")

# Every delegated sub-run shares one `usage` object (see agents.py), so these
# limits apply to the *whole* multi-agent chain for one ticket, not just a
# single agent's turn — keeps runaway token/tool spend in check.
# request_limit/tool_calls_limit raised 20/15->30 after live-testing: a
# genuinely successful ticket 101 resolution used 18 requests, and ticket 103
# kept getting blocked at 17 tool calls against a 15 cap — too tight to
# reliably finish a legitimate resolution in one try. 30 gives real headroom
# above every observed real run rather than just barely more than needed.
# total_tokens_limit raised 50_000->70_000 after a genuinely successful
# ticket 103 run used 48,978 — only 2% headroom, close enough that a slightly
# longer run would have tipped over for no real reason.
DEFAULT_USAGE_LIMITS = UsageLimits(
    request_limit=30,
    tool_calls_limit=30,
    total_tokens_limit=70_000,
)

# Hard ceiling on delegation hops for one ticket, enforced in agents.py's
# delegate_to_* tools (via TicketDeps.max_hops, which defaults to this value —
# see models.py). Independent of (and tighter than) the usage caps above, so a
# cheap infinite ping-pong between two agents can't hide under budget.
# Raised from 4->5 after live-testing real tickets: a genuine capability gap
# (missing get_invoice_status) caused one unproductive loop at 4, but every
# run since that fix has finished within 4 anyway — 5 is just a small buffer,
# not a fix for a recurring problem.
MAX_DELEGATION_HOPS = 5


def get_model() -> OpenAIResponsesModel:
    """The one model every agent must use, routed through Portkey.

    Uses the Responses API model class, not the Chat Completions one — Portkey
    rejects function tools + reasoning_effort on /v1/chat/completions for this
    model ("gpt-6-luna-global"), and explicitly says to use /v1/responses
    instead if you need function tools, which is exactly what every agent here
    needs (they're all tool-calling agents).
    """
    if not PORTKEY_API_KEY:
        raise RuntimeError(
            "PORTKEY_API_KEY is not set in .env — every agent in this project "
            "must call the model through Portkey, never directly."
        )
    headers = {}
    if PORTKEY_VIRTUAL_KEY:
        headers["x-portkey-virtual-key"] = PORTKEY_VIRTUAL_KEY
    client = AsyncOpenAI(
        base_url=PORTKEY_BASE_URL,
        api_key=PORTKEY_API_KEY,
        default_headers=headers or None,
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def load_prompt(name: str) -> str:
    """Read an agent's system prompt from backend/prompts/<name>.md."""
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def new_mcp_toolset() -> MCPToolset:
    """A fresh toolset pointed at our MCP server — the only source of shop facts.

    init_timeout is bumped well past the 5s default: when several agents
    delegate to each other, multiple server subprocesses can spawn around the
    same time (each paying Python + fastmcp import cost), which blows past 5s
    under load and otherwise fails the handshake with a TimeoutError.
    """
    return MCPToolset(MCP_SERVER_PATH, init_timeout=30)


# Each agent only sees the MCP tools its own role actually needs. Added after
# live-testing showed real waste: accounting calling list_tickets (not its
# table), and the same get_pricing/get_cash_balance facts getting re-fetched
# by agents that were just told those exact numbers by whoever delegated to
# them. Scoping tools narrows what a model *can* reach for, which cuts out a
# lot of that "let me just double check with a tool anyway" behavior — on top
# of the prompt rule (below) asking agents to trust facts they're given.
SCOPED_TOOLS: dict[str, set[str]] = {
    "boss": {"list_tickets"},
    "inventory": {"get_inventory_status", "list_vendors", "get_vendor_shipping_status", "get_pricing"},
    "accounting": {
        "get_cash_balance",
        "get_invoice_status",
        "get_vendor_shipping_status",
        "get_pricing",
        "list_vendors",
    },
    "facilities": {"get_lease_due_status"},
    "customer_service": {"get_inventory_status", "get_pricing"},
}


def scoped_mcp_toolset(agent_name: str) -> AbstractToolset:
    """new_mcp_toolset(), filtered down to the tools SCOPED_TOOLS[agent_name] allows."""
    allowed = SCOPED_TOOLS[agent_name]
    return FilteredToolset(
        new_mcp_toolset(),
        filter_func=lambda ctx, tool_def: tool_def.name in allowed,
    )
