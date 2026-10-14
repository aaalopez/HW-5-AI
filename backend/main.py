"""FastAPI backend for the Campus Customs desk dashboard.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000

All shop facts/mutations go through mcp_server/server.py (the same file the
agent team's MCP toolset connects to) — this app imports its functions
directly (in-process, not over the MCP stdio protocol) rather than touching
data/campus_customs_new.db itself, so there is still only one place in the
project that knows how to read or write the db.

Payment execution (mcp_server.server.execute_payment) is a plain function,
NOT an @mcp.tool() — it is never in any agent's toolset, so the only way to
actually move money is through POST /payments/approve below, which only runs
after a human clicks approve in the dashboard. Agents can only *propose* a
payment in their findings; they can't call this themselves.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_ai.exceptions import UsageLimitExceeded

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server import server as shop  # noqa: E402  (path must be set up first)

from backend.agents import resolve_ticket  # noqa: E402
from backend.audit import _load as load_audit  # noqa: E402
from backend.audit import append_audit, now_iso  # noqa: E402
from backend.models import (  # noqa: E402
    PaymentApprovalRequest,
    PaymentApprovalResponse,
    TicketOut,
    TicketResolution,
)

ORIGINAL_DB = PROJECT_ROOT / "data" / "campus_customs.db"
WORKING_DB = PROJECT_ROOT / "data" / "campus_customs_new.db"

app = FastAPI(title="Campus Customs Desk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ticket_summary_text(ticket: dict) -> str:
    """Build the plain-text summary resolve_ticket() needs, from the ticket's
    own real fields — never hand-typed, so it can't drift from the db."""
    parts = [f"{ticket['type']} from {ticket['requester']}: {ticket['subject']}."]
    if ticket.get("sku"):
        parts.append(f"Item: {ticket['sku']} size {ticket.get('size')}, qty {ticket.get('qty')}.")
    if ticket.get("lease_id") is not None:
        parts.append(f"Linked lease_id={ticket['lease_id']}.")
    if ticket.get("invoice_id") is not None:
        parts.append(f"Linked invoice_id={ticket['invoice_id']}.")
    if ticket.get("notes"):
        parts.append(f"Notes: {ticket['notes']}")
    return " ".join(parts)


@app.get("/tickets", response_model=list[TicketOut])
def get_tickets():
    """1) Every ticket, and whether it's open or resolved."""
    tickets = shop.list_tickets()["tickets"]
    return [TicketOut(**t, is_open=(t["status"] == "open")) for t in tickets]


@app.post("/tickets/{ticket_id}/resolve", response_model=TicketResolution)
async def resolve_ticket_route(ticket_id: int):
    """2) Run the agent team on one ticket and record its outcome."""
    tickets = {t["id"]: t for t in shop.list_tickets()["tickets"]}
    ticket = tickets.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"No such ticket: {ticket_id}")

    try:
        resolution = await resolve_ticket(ticket_id, _ticket_summary_text(ticket))
    except UsageLimitExceeded as e:
        # A real outcome, not a server bug: say plainly that this is partial
        # rather than crash the route (per the "be explicit when a result is
        # partial" safety rule in output/harness.md). Also record it in the
        # audit trail — this used to be invisible there (a usage-limit stop
        # happens mid-run, before resolve_ticket's own run_end logging), so a
        # blocked ticket had no trace of *why* in output/audit_trail.json.
        append_audit(
            {
                "ts": now_iso(),
                "agent": "boss",
                "event": "stop",
                "detail": {"ticket_id": ticket_id, "reason": str(e)},
                "stop_reason": "usage_limit_exceeded",
            }
        )
        resolution = TicketResolution(
            ticket_id=ticket_id,
            status="blocked",
            summary=f"Stopped before finishing: hit a usage limit ({e}).",
            next_steps=["Re-run with a higher usage limit, or resolve manually."],
        )

    shop.set_ticket_status(ticket_id, resolution.status)
    return resolution


@app.get("/events/recent")
def get_recent_events(ticket_id: int | None = None, limit: int = 50):
    """3) Recent agent events — what each agent said and which tools it used,
    so the dashboard can refresh. Newest first."""
    entries = load_audit()
    if ticket_id is not None:
        entries = [e for e in entries if e.get("detail", {}).get("ticket_id") == ticket_id]
    return list(reversed(entries))[:limit]


@app.post("/payments/approve", response_model=PaymentApprovalResponse)
def approve_payment(req: PaymentApprovalRequest):
    """4) Approve a payment/purchase after a human clicks approve.

    Agents can only ever *prepare* (recommend) a payment in their findings —
    this is the only route that can actually move money, and it only runs
    when a human explicitly calls it with their own name as approved_by."""
    try:
        payment = shop.execute_payment(
            kind=req.kind, ref_id=req.ref_id, approved_by=req.approved_by, account=req.account
        )
    except shop.PaymentRefused as e:
        return PaymentApprovalResponse(approved=False, reason=str(e))

    return PaymentApprovalResponse(
        approved=True, payment=payment, new_balance=payment["new_balance"]
    )


@app.get("/cash")
def get_cash():
    """5) Current checking balance from cash_accounts."""
    return shop.get_cash_balance()


@app.get("/payments")
def get_payments():
    """Every real payment made, plus the running total — backs the dashboard's
    "funds spent" display (added for dashboard styling, not one of the 6
    Problem 7 routes)."""
    return shop.list_payments()


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int):
    """Real invoice detail — lets the dashboard show a human the actual
    amount/vendor before they approve a payment against it (added for the
    dashboard's approval panel, not one of the 6 Problem 7 routes)."""
    return shop.get_invoice_status(invoice_id)


@app.get("/leases/{lease_id}")
def get_lease(lease_id: int):
    """Real lease detail — same purpose as /invoices/{id}, for rent payments."""
    return shop.get_lease_due_status(lease_id)


@app.post("/reset")
def reset_database():
    """6) Reset the working db back to the original seed values."""
    shutil.copyfile(ORIGINAL_DB, WORKING_DB)
    return {"reset": True, "message": "data/campus_customs_new.db restored from the original seed."}
