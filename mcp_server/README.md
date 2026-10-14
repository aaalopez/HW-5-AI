# Campus Customs MCP server

A FastMCP server that every agent in this assignment uses to read real shop data — no agent should ever invent prices, stock levels, vendor terms, or dates; they call these tools instead.

**Database:** [data/campus_customs_new.db](../data/campus_customs_new.db) (the working copy — the original [data/campus_customs.db](../data/campus_customs.db) is never touched, so it can be reset between runs).

Every agent in `backend/` (boss, inventory, accounting, facilities, customer_service) connects to this same server as its only source of shop facts — no agent reads the db directly.

Connected via [.mcp.json](../.mcp.json) at the project root, and used by `backend/config.py`'s `new_mcp_toolset()` for every agent.

## Tools (9 so far)

- **`get_inventory_status(sku, size)`** — real stock on hand for a sku+size from `inventory`. Returns `found=False` instead of guessing if the sku+size doesn't exist.
- **`get_vendor_shipping_status(vendor_id)`** — a vendor's lead time (`vendors.lead_days`) plus any open/unpaid invoices tied to them (`invoices`), with a `can_ship` flag — a vendor with an open invoice won't ship new product.
- **`get_lease_due_status(lease_id)`** — a lease's rent and due date (`leases`) compared against the shop's "today" (`desk.date_today`), returning `days_until_due` and `is_overdue`.
- **`get_invoice_status(invoice_id)`** — a real invoice looked up directly by id from `invoices` (vendor_id, amount, due_date, status). Added after a live test run showed agents had no way to resolve a ticket's `invoice_id` without already knowing its `vendor_id`.
- **`get_pricing(sku)`** — real unit cost and list price for a sku from `pricing`. Returns `found=False` instead of guessing if there's no pricing row.
- **`get_cash_balance(account="checking")`** — the shop's real cash balance from `cash_accounts`. Read-only — does not move money or check affordability itself.
- **`list_vendors()`** — every vendor with specialty and lead time from `vendors`, for matching a restock need to the right vendor before calling `get_vendor_shipping_status`.
- **`list_tickets()`** — every ticket on the desk from `tickets`, full real record. Backs the dashboard's ticket list and lets any agent pull a ticket's real fields instead of relying on a hand-typed summary.
- **`list_payments()`** — every real payment made, plus the running total, from `payments`. Backs the dashboard's "Funds spent" display — not scoped to any agent, since no ticket needs it.

Each agent only sees a scoped slice of these 8 agent-facing tools, not all of them — see `backend/config.py`'s `SCOPED_TOOLS` and [output/harness.md](../output/harness.md) for why.

**Payment execution now exists** (`execute_payment`, in this same file) but is deliberately **not** decorated as `@mcp.tool()` — it's a plain function that only `backend/main.py`'s `POST /payments/approve` route calls. That's what makes "agents can only prepare a payment, a human has to approve it" architectural rather than just a prompt rule: there's no tool-call path from any agent to it. It derives the amount from the real invoice/lease row, refuses outright on a closed invoice/missing approver/would-be-negative balance, and updates `payments` + `invoices.status` + `cash_accounts.balance` together in one transaction. `set_ticket_status(ticket_id, status)` is a similar plain, agent-inaccessible helper, used by the resolve route to persist an outcome.

See [output/harness.md](../output/harness.md) for the full tool → table → ticket mapping, the 5-agent team, the backend routes, and the safety guardrails.
