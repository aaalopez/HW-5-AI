import { useEffect, useState } from "react";
import { api, type InvoiceDetail, type LeaseDetail, type Ticket } from "../api";

export function ApprovalPanel({
  ticket,
  onApproved,
}: {
  ticket: Ticket;
  onApproved: () => void;
}) {
  const kind: "invoice" | "lease" | null = ticket.invoice_id
    ? "invoice"
    : ticket.lease_id
    ? "lease"
    : null;
  const refId = ticket.invoice_id ?? ticket.lease_id ?? null;

  const [detail, setDetail] = useState<InvoiceDetail | LeaseDetail | null>(null);
  const [approvedBy, setApprovedBy] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ approved: boolean; reason: string | null } | null>(null);

  useEffect(() => {
    setResult(null);
    if (kind === "invoice" && refId) {
      api.getInvoice(refId).then(setDetail);
    } else if (kind === "lease" && refId) {
      api.getLease(refId).then(setDetail);
    }
  }, [kind, refId]);

  if (!kind || !refId) {
    return (
      <div className="approval-panel">
        <span className="title">Needs human approval</span>
        <p className="empty-state">
          This ticket doesn't have a linked invoice or lease, so there's nothing to approve a
          payment against yet — check the agents' summary above for what they need next.
        </p>
      </div>
    );
  }

  const amount =
    kind === "invoice"
      ? (detail as InvoiceDetail | null)?.amount
      : (detail as LeaseDetail | null)?.monthly_rent;

  async function handleApprove() {
    setSubmitting(true);
    try {
      const res = await api.approvePayment({
        kind: kind!,
        ref_id: refId!,
        approved_by: approvedBy,
      });
      setResult({ approved: res.approved, reason: res.reason });
      if (res.approved) onApproved();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="approval-panel">
      <span className="title">Needs human approval</span>
      <p>
        The agents recommend paying{" "}
        <strong>
          {kind} #{refId}
        </strong>
        {amount !== undefined ? (
          <>
            {" "}
            for <strong>${amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
          </>
        ) : null}
        . Nothing has been paid — agents can only prepare this, not send it.
      </p>
      <input
        placeholder="Your name (approver)"
        value={approvedBy}
        onChange={(e) => setApprovedBy(e.target.value)}
      />
      <div className="approval-actions">
        <button
          className="approve-btn"
          disabled={submitting || approvedBy.trim().length === 0}
          onClick={handleApprove}
        >
          {submitting ? "Approving…" : "Approve payment"}
        </button>
        {result && (
          <span className={`approval-result ${result.approved ? "ok" : "refused"}`}>
            {result.approved ? "Paid." : `Refused: ${result.reason}`}
          </span>
        )}
      </div>
    </div>
  );
}
