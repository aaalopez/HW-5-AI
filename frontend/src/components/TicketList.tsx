import type { Ticket } from "../api";
import { StatusBadge } from "./StatusBadge";

// Ticket-card background tint by status — a status's own fixed color family
// (good=green, warning=amber, critical/open=red), not the agent palette.
const TINT_CLASS: Record<string, string> = {
  open: "tint-red",
  blocked: "tint-red",
  needs_human_approval: "tint-amber",
  resolved: "tint-green",
  draft_ready: "tint-green",
};

export function TicketList({
  tickets,
  selectedId,
  onSelect,
}: {
  tickets: Ticket[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  if (tickets.length === 0) {
    return <p className="empty-state">No tickets loaded yet.</p>;
  }

  return (
    <div className="ticket-list">
      {tickets.map((t) => (
        <button
          key={t.id}
          className={`ticket-card ${TINT_CLASS[t.status] ?? ""}${t.id === selectedId ? " selected" : ""}`}
          onClick={() => onSelect(t.id)}
        >
          <span className="ticket-id">Ticket {t.id} · {t.type.replace(/_/g, " ")}</span>
          <span className="ticket-subject">{t.subject}</span>
          <span className="ticket-requester">From {t.requester}</span>
          <StatusBadge status={t.status} />
        </button>
      ))}
    </div>
  );
}
