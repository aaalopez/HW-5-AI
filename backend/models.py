"""Shared pydantic types for the Campus Customs agent team.

Deps carry per-ticket delegation bookkeeping; the Finding/Draft/Resolution
types are each worker agent's structured output_type.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from .config import MAX_DELEGATION_HOPS

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]


class TicketOut(BaseModel):
    id: int
    type: str
    requester: str
    subject: str
    sku: str | None = None
    size: str | None = None
    qty: int | None = None
    lease_id: int | None = None
    invoice_id: int | None = None
    status: str
    notes: str | None = None
    created_at: str
    is_open: bool


class PaymentApprovalRequest(BaseModel):
    kind: Literal["invoice", "lease"]
    ref_id: int
    approved_by: str
    account: str = "checking"


class PaymentApprovalResponse(BaseModel):
    approved: bool
    reason: str | None = None
    payment: dict | None = None
    new_balance: float | None = None


@dataclass
class TicketDeps:
    """Passed to every agent via RunContext.deps for one ticket's resolution.

    hop_count/max_hops/visited exist so delegation can't loop forever — each
    delegate_to_* tool call increments hop_count and refuses once max_hops is
    hit, independent of the token/request usage caps in backend/config.py.
    """

    ticket_id: int
    hop_count: int = 0
    max_hops: int = MAX_DELEGATION_HOPS
    visited: list[AgentName] = field(default_factory=list)


class InventoryFinding(BaseModel):
    sku: str | None = None
    size: str | None = None
    qty_requested: int | None = None
    qty_available: int | None = None
    can_fulfill_from_stock: bool
    restock_needed: bool
    notes: str


class AccountingFinding(BaseModel):
    subject: str
    amount: float | None = None
    cash_balance: float | None = None
    would_overdraw: bool | None = None
    blocking_open_invoices: list[int] = Field(default_factory=list)
    requires_human_approval: bool = True
    recommendation: str


class FacilitiesFinding(BaseModel):
    lease_id: int
    monthly_rent: float
    days_until_due: int
    is_overdue: bool
    recommendation: str


class CustomerServiceDraft(BaseModel):
    ticket_id: int
    draft_message: str
    stays_on_board: bool = True
    requires_followup: bool = False


class TicketResolution(BaseModel):
    ticket_id: int
    status: Literal["resolved", "blocked", "needs_human_approval", "draft_ready"]
    summary: str
    next_steps: list[str] = Field(default_factory=list)
