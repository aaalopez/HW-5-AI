"""Campus Customs MCP server (FastMCP). Not run yet — see mcp_server/README.md."""

import os
import sqlite3

from fastmcp import FastMCP

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "campus_customs_new.db")

mcp = FastMCP("campus-customs")


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


@mcp.tool()
def get_inventory_status(sku: str, size: str) -> dict:
    """Look up real stock on hand for a sku+size from the inventory table.

    Returns the matching row (name, qty, location) or found=False if no such
    sku+size exists — never guesses a quantity.
    """
    con = _connect()
    try:
        row = con.execute(
            "SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? AND size = ?",
            (sku, size),
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return {"found": False, "sku": sku, "size": size}
    return {"found": True, **dict(row)}


@mcp.tool()
def get_vendor_shipping_status(vendor_id: int) -> dict:
    """Check whether a vendor will currently ship new product.

    Reads the vendors table for name/lead_days and the invoices table for any
    open (unpaid) invoices tied to that vendor. A vendor with at least one
    open invoice will not ship new product, per shop policy.
    """
    con = _connect()
    try:
        vendor = con.execute(
            "SELECT id, name, specialty, lead_days FROM vendors WHERE id = ?",
            (vendor_id,),
        ).fetchone()
        if vendor is None:
            return {"found": False, "vendor_id": vendor_id}

        open_invoices = con.execute(
            "SELECT id, amount, due_date, status, description FROM invoices "
            "WHERE vendor_id = ? AND status = 'open'",
            (vendor_id,),
        ).fetchall()
    finally:
        con.close()

    open_invoices = [dict(r) for r in open_invoices]
    return {
        "found": True,
        "vendor_id": vendor["id"],
        "name": vendor["name"],
        "specialty": vendor["specialty"],
        "lead_days": vendor["lead_days"],
        "open_invoices": open_invoices,
        "can_ship": len(open_invoices) == 0,
    }


@mcp.tool()
def get_lease_due_status(lease_id: int) -> dict:
    """Check a lease's rent amount and how it sits relative to the shop's 'today'.

    Reads the leases table for rent/next_due and the desk table for
    date_today (the shop's "today" — not the real calendar date), then
    reports days_until_due and whether the lease is overdue.
    """
    con = _connect()
    try:
        lease = con.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due, notes "
            "FROM leases WHERE id = ?",
            (lease_id,),
        ).fetchone()
        if lease is None:
            return {"found": False, "lease_id": lease_id}

        desk = con.execute("SELECT date_today FROM desk").fetchone()
    finally:
        con.close()

    from datetime import date

    today = date.fromisoformat(desk["date_today"])
    due = date.fromisoformat(lease["next_due"])
    days_until_due = (due - today).days

    return {
        "found": True,
        "lease_id": lease["id"],
        "space_name": lease["space_name"],
        "landlord": lease["landlord"],
        "monthly_rent": lease["monthly_rent"],
        "next_due": lease["next_due"],
        "date_today": desk["date_today"],
        "days_until_due": days_until_due,
        "is_overdue": days_until_due < 0,
    }


@mcp.tool()
def get_invoice_status(invoice_id: int) -> dict:
    """Look up a real invoice directly by id from the invoices table.

    Tickets often link to an invoice_id (e.g. a customer_order tied to the
    reprint that would restock it) without saying which vendor it belongs
    to — use this first, then get_vendor_shipping_status(vendor_id) with the
    vendor_id it returns. Returns found=False if no such invoice exists.
    """
    con = _connect()
    try:
        row = con.execute(
            "SELECT id, vendor_id, amount, due_date, status, description FROM invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return {"found": False, "invoice_id": invoice_id}
    return {"found": True, **dict(row)}


@mcp.tool()
def get_pricing(sku: str) -> dict:
    """Look up real unit cost and list price for a sku from the pricing table.

    Returns found=False if the sku has no pricing row — never guesses a price.
    """
    con = _connect()
    try:
        row = con.execute(
            "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?",
            (sku,),
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return {"found": False, "sku": sku}
    return {"found": True, **dict(row)}


@mcp.tool()
def get_cash_balance(account: str = "checking") -> dict:
    """Look up the shop's real cash balance from the cash_accounts table.

    Returns found=False if no such account exists — never invents a balance.
    This is read-only: it does not move money or check payment feasibility by
    itself, it just reports what's actually there.
    """
    con = _connect()
    try:
        row = con.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name = ?",
            (account,),
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return {"found": False, "account": account}
    return {"found": True, **dict(row)}


@mcp.tool()
def list_vendors() -> dict:
    """List every vendor with their specialty and lead time, from the vendors table.

    Use this to match a restock need (e.g. "apparel reprint") to the right
    vendor id before calling get_vendor_shipping_status.
    """
    con = _connect()
    try:
        rows = con.execute("SELECT id, name, specialty, lead_days FROM vendors").fetchall()
    finally:
        con.close()

    return {"vendors": [dict(r) for r in rows]}


@mcp.tool()
def list_payments() -> dict:
    """List every real payment that has actually been made, from the payments table.

    Read-only — reports what has already happened, never a projection or a
    pending/proposed amount. Backs the dashboard's "funds spent" display.
    """
    con = _connect()
    try:
        rows = con.execute(
            "SELECT id, kind, ref_id, amount, account, paid_at, approved_by "
            "FROM payments ORDER BY id"
        ).fetchall()
    finally:
        con.close()

    payments = [dict(r) for r in rows]
    return {"payments": payments, "total_spent": sum(p["amount"] for p in payments)}


@mcp.tool()
def list_tickets() -> dict:
    """List every ticket on the desk, from the tickets table.

    Gives the full real record (type, requester, sku/size/qty, lease_id,
    invoice_id, status, notes) for every ticket — used by the dashboard
    backend to show what's open/resolved, and available to agents too so
    they can pull a ticket's real fields instead of relying on a hand-typed
    summary.
    """
    con = _connect()
    try:
        rows = con.execute(
            "SELECT id, type, requester, subject, sku, size, qty, lease_id, "
            "invoice_id, status, notes, created_at FROM tickets ORDER BY id"
        ).fetchall()
    finally:
        con.close()

    return {"tickets": [dict(r) for r in rows]}


# --- Backend-only helpers below this line -----------------------------------
#
# These are plain functions, NOT decorated with @mcp.tool(), so they never
# appear in any agent's MCP toolset — only backend/main.py imports and calls
# them directly. This is what makes "agents can only prepare a payment, a
# human has to approve it" an architectural guarantee rather than just a
# prompt instruction: there is no tool call path from an agent to these.


def set_ticket_status(ticket_id: int, status: str) -> None:
    """Update a ticket's status after it's been resolved (or re-blocked)."""
    con = _connect()
    try:
        con.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
        con.commit()
    finally:
        con.close()


def _get_desk_today(con: sqlite3.Connection) -> str:
    return con.execute("SELECT date_today FROM desk").fetchone()["date_today"]


class PaymentRefused(Exception):
    """Raised when execute_payment refuses — e.g. it would overdraw the account."""


def execute_payment(kind: str, ref_id: int, approved_by: str, account: str = "checking") -> dict:
    """Actually move money: insert a payment row, update the invoice/lease,
    and debit cash_accounts — all in one transaction, or none of it at all.

    kind is "invoice" or "lease". The amount is always derived from the real
    invoice/lease row itself (never trusted from the caller), so this can't
    be tricked into paying the wrong amount. Refuses outright (raises
    PaymentRefused) if the account doesn't exist, the invoice/lease doesn't
    exist (or the invoice isn't open), or paying would take the balance
    negative — no negative balances, no exceptions. approved_by must be a
    real human name; this function has no notion of "the agent approved it".
    """
    if not approved_by or not approved_by.strip():
        raise PaymentRefused("approved_by is required — a human must be named as the approver.")

    con = _connect()
    try:
        account_row = con.execute(
            "SELECT name, balance FROM cash_accounts WHERE name = ?", (account,)
        ).fetchone()
        if account_row is None:
            raise PaymentRefused(f"No such cash account: {account!r}")

        if kind == "invoice":
            ref_row = con.execute(
                "SELECT id, vendor_id, amount, status FROM invoices WHERE id = ?", (ref_id,)
            ).fetchone()
            if ref_row is None:
                raise PaymentRefused(f"No such invoice: {ref_id}")
            if ref_row["status"] != "open":
                raise PaymentRefused(f"Invoice {ref_id} is not open (status={ref_row['status']!r})")
            amount = ref_row["amount"]
        elif kind == "lease":
            ref_row = con.execute(
                "SELECT id, monthly_rent FROM leases WHERE id = ?", (ref_id,)
            ).fetchone()
            if ref_row is None:
                raise PaymentRefused(f"No such lease: {ref_id}")
            amount = ref_row["monthly_rent"]
        else:
            raise PaymentRefused(f"Unknown payment kind: {kind!r} (expected 'invoice' or 'lease')")

        new_balance = account_row["balance"] - amount
        if new_balance < 0:
            raise PaymentRefused(
                f"Refused: paying {amount} from {account!r} (balance {account_row['balance']}) "
                f"would overdraw to {new_balance}. No negative balances allowed."
            )

        paid_at = _get_desk_today(con)  # the shop's "today", not the real calendar date

        cur = con.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (kind, ref_id, amount, account, paid_at, approved_by),
        )
        payment_id = cur.lastrowid

        if kind == "invoice":
            con.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref_id,))

        con.execute(
            "UPDATE cash_accounts SET balance = ? WHERE name = ?", (new_balance, account)
        )

        con.commit()
    except PaymentRefused:
        con.rollback()
        raise
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    return {
        "payment_id": payment_id,
        "kind": kind,
        "ref_id": ref_id,
        "amount": amount,
        "account": account,
        "paid_at": paid_at,
        "approved_by": approved_by,
        "new_balance": new_balance,
    }


if __name__ == "__main__":
    mcp.run()
