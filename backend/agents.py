"""The 5-agent Campus Customs team: boss, inventory, accounting, facilities,
customer_service.

Every agent shares the same model (config.get_model()) and talks to shop data
only through its own MCP toolset (config.new_mcp_toolset(), which connects to
mcp_server/server.py) — no agent touches the db directly or gets a second
tools layer. Agents have full connectivity: each one can delegate to any of
the other four via a delegate_to_<name> tool, bounded by TicketDeps.max_hops
so a ticket can't bounce between agents forever. Every agent run and every
delegation step is appended to output/audit_trail.json.
"""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from .audit import append_audit, now_iso
from .config import DEFAULT_USAGE_LIMITS, get_model, load_prompt, scoped_mcp_toolset
from .models import (
    AccountingFinding,
    CustomerServiceDraft,
    FacilitiesFinding,
    InventoryFinding,
    TicketDeps,
    TicketResolution,
)

MODEL = get_model()

boss_agent = Agent(
    name="boss",
    model=MODEL,
    system_prompt=load_prompt("boss"),
    deps_type=TicketDeps,
    output_type=TicketResolution,
    toolsets=[scoped_mcp_toolset("boss")],
)

inventory_agent = Agent(
    name="inventory",
    model=MODEL,
    system_prompt=load_prompt("inventory"),
    deps_type=TicketDeps,
    output_type=InventoryFinding,
    toolsets=[scoped_mcp_toolset("inventory")],
)

accounting_agent = Agent(
    name="accounting",
    model=MODEL,
    system_prompt=load_prompt("accounting"),
    deps_type=TicketDeps,
    output_type=AccountingFinding,
    toolsets=[scoped_mcp_toolset("accounting")],
)

facilities_agent = Agent(
    name="facilities",
    model=MODEL,
    system_prompt=load_prompt("facilities"),
    deps_type=TicketDeps,
    output_type=FacilitiesFinding,
    toolsets=[scoped_mcp_toolset("facilities")],
)

customer_service_agent = Agent(
    name="customer_service",
    model=MODEL,
    system_prompt=load_prompt("customer_service"),
    deps_type=TicketDeps,
    output_type=CustomerServiceDraft,
    toolsets=[scoped_mcp_toolset("customer_service")],
)

AGENTS: dict[str, Agent] = {
    "boss": boss_agent,
    "inventory": inventory_agent,
    "accounting": accounting_agent,
    "facilities": facilities_agent,
    "customer_service": customer_service_agent,
}


def _output_as_text(output) -> str:
    if hasattr(output, "model_dump_json"):
        return output.model_dump_json()
    return str(output)


def _log_agent_run(agent_name: str, deps: TicketDeps, prompt: str, result, stop_reason: str | None) -> None:
    """Append one audit entry per message part, plus one run_end summary."""
    for msg in result.new_messages():
        for part in getattr(msg, "parts", []):
            kind = type(part).__name__
            if "ToolCall" in kind:
                event = "tool_call"
            elif "ToolReturn" in kind:
                event = "tool_return"
            else:
                continue  # skip plain text/system parts — the run_end entry covers the final output

            detail: dict = {"ticket_id": deps.ticket_id, "part_kind": kind}
            if hasattr(part, "tool_name"):
                detail["tool_name"] = part.tool_name
            if hasattr(part, "args"):
                detail["args"] = part.args
            if hasattr(part, "content"):
                detail["result"] = str(part.content)[:500]

            append_audit(
                {
                    "ts": now_iso(),
                    "agent": agent_name,
                    "event": event,
                    "detail": detail,
                    "stop_reason": None,
                }
            )

    usage = result.usage
    append_audit(
        {
            "ts": now_iso(),
            "agent": agent_name,
            "event": "run_end",
            "detail": {
                "ticket_id": deps.ticket_id,
                "prompt": prompt[:500],
                "output": _output_as_text(result.output),
                "requests": usage.requests,
                "total_tokens": usage.input_tokens + usage.output_tokens,
            },
            "stop_reason": stop_reason,
        }
    )


def _make_delegation_tool(target_name: str, target_agent: Agent):
    async def delegate(ctx: RunContext[TicketDeps], message: str) -> str:
        deps = ctx.deps
        if deps.hop_count >= deps.max_hops:
            append_audit(
                {
                    "ts": now_iso(),
                    "agent": target_name,
                    "event": "stop",
                    "detail": {
                        "ticket_id": deps.ticket_id,
                        "reason": f"max_hops ({deps.max_hops}) reached before delegating to {target_name}",
                        "hop_count": deps.hop_count,
                    },
                    "stop_reason": "max_hops_exceeded",
                }
            )
            return (
                f"Delegation refused: max_hops ({deps.max_hops}) reached for ticket "
                f"{deps.ticket_id}. Resolve with what you already have."
            )

        child_deps = TicketDeps(
            ticket_id=deps.ticket_id,
            hop_count=deps.hop_count + 1,
            max_hops=deps.max_hops,
            visited=[*deps.visited, target_name],
        )
        append_audit(
            {
                "ts": now_iso(),
                "agent": target_name,
                "event": "delegation",
                "detail": {
                    "ticket_id": deps.ticket_id,
                    "message": message[:500],
                    "hop_count": child_deps.hop_count,
                },
                "stop_reason": None,
            }
        )
        result = await target_agent.run(
            message,
            deps=child_deps,
            usage=ctx.usage,
            usage_limits=DEFAULT_USAGE_LIMITS,
        )
        _log_agent_run(target_name, child_deps, message, result, stop_reason=None)
        return _output_as_text(result.output)

    delegate.__doc__ = f"Hand this request to the {target_name} agent and return its finding."
    return delegate


# Full connectivity: every agent can delegate to every other agent.
for _name, _agent in AGENTS.items():
    for _target_name, _target_agent in AGENTS.items():
        if _target_name == _name:
            continue
        _agent.tool(_make_delegation_tool(_target_name, _target_agent), name=f"delegate_to_{_target_name}")


async def resolve_ticket(ticket_id: int, ticket_summary: str) -> TicketResolution:
    """Run the boss agent end-to-end on one ticket, logging every step."""
    deps = TicketDeps(ticket_id=ticket_id)
    prompt = f"Resolve ticket {ticket_id}: {ticket_summary}"
    append_audit(
        {
            "ts": now_iso(),
            "agent": "boss",
            "event": "run_start",
            "detail": {"ticket_id": ticket_id, "prompt": prompt},
            "stop_reason": None,
        }
    )
    result = await boss_agent.run(prompt, deps=deps, usage_limits=DEFAULT_USAGE_LIMITS)
    _log_agent_run("boss", deps, prompt, result, stop_reason="final_output")
    return result.output
