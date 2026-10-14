// Talks to the FastAPI backend from Problem 7, at http://localhost:8000.

export const API_BASE = "http://localhost:8000";

export type AgentName =
  | "boss"
  | "inventory"
  | "accounting"
  | "facilities"
  | "customer_service";

export type Ticket = {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku: string | null;
  size: string | null;
  qty: number | null;
  lease_id: number | null;
  invoice_id: number | null;
  status: string;
  notes: string | null;
  created_at: string;
  is_open: boolean;
};

export type TicketResolution = {
  ticket_id: number;
  status: "resolved" | "blocked" | "needs_human_approval" | "draft_ready";
  summary: string;
  next_steps: string[];
};

export type AgentEvent = {
  ts: string;
  agent: AgentName | "human";
  event:
    | "run_start"
    | "run_end"
    | "tool_call"
    | "tool_return"
    | "delegation"
    | "stop";
  detail: Record<string, unknown>;
  stop_reason: string | null;
};

export type CashBalance = {
  found: boolean;
  name?: string;
  balance?: number;
  date?: string;
};

export type InvoiceDetail = {
  found: boolean;
  id?: number;
  vendor_id?: number;
  amount?: number;
  due_date?: string;
  status?: string;
  description?: string;
};

export type LeaseDetail = {
  found: boolean;
  lease_id?: number;
  space_name?: string;
  landlord?: string;
  monthly_rent?: number;
  next_due?: string;
  days_until_due?: number;
  is_overdue?: boolean;
};

export type PaymentApprovalResponse = {
  approved: boolean;
  reason: string | null;
  payment: Record<string, unknown> | null;
  new_balance: number | null;
};

export type PaymentsReport = {
  payments: {
    id: number;
    kind: string;
    ref_id: number;
    amount: number;
    account: string;
    paid_at: string;
    approved_by: string;
  }[];
  total_spent: number;
};

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getTickets: () => fetch(`${API_BASE}/tickets`).then((r) => json<Ticket[]>(r)),

  resolveTicket: (ticketId: number) =>
    fetch(`${API_BASE}/tickets/${ticketId}/resolve`, { method: "POST" }).then(
      (r) => json<TicketResolution>(r)
    ),

  getRecentEvents: (ticketId?: number, limit = 100) => {
    const params = new URLSearchParams();
    if (ticketId !== undefined) params.set("ticket_id", String(ticketId));
    params.set("limit", String(limit));
    return fetch(`${API_BASE}/events/recent?${params}`).then((r) =>
      json<AgentEvent[]>(r)
    );
  },

  approvePayment: (body: {
    kind: "invoice" | "lease";
    ref_id: number;
    approved_by: string;
    account?: string;
  }) =>
    fetch(`${API_BASE}/payments/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => json<PaymentApprovalResponse>(r)),

  getCash: () => fetch(`${API_BASE}/cash`).then((r) => json<CashBalance>(r)),

  resetDatabase: () =>
    fetch(`${API_BASE}/reset`, { method: "POST" }).then((r) => json(r)),

  getInvoice: (invoiceId: number) =>
    fetch(`${API_BASE}/invoices/${invoiceId}`).then((r) => json<InvoiceDetail>(r)),

  getLease: (leaseId: number) =>
    fetch(`${API_BASE}/leases/${leaseId}`).then((r) => json<LeaseDetail>(r)),

  getPayments: () => fetch(`${API_BASE}/payments`).then((r) => json<PaymentsReport>(r)),
};
