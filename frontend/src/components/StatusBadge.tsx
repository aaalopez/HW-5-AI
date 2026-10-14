import { STATUS_COLORS } from "../theme";

const STATUS_META: Record<string, { color: string; label: string }> = {
  open: { color: "#898781", label: "Open" },
  resolved: { color: STATUS_COLORS.good, label: "Resolved" },
  draft_ready: { color: STATUS_COLORS.good, label: "Draft ready" },
  needs_human_approval: { color: STATUS_COLORS.warning, label: "Needs approval" },
  blocked: { color: STATUS_COLORS.critical, label: "Blocked" },
};

export function StatusBadge({ status }: { status: string }) {
  const meta = STATUS_META[status] ?? { color: "#898781", label: status };
  return (
    <span
      className="status-badge"
      style={{ background: `${meta.color}22`, color: meta.color }}
    >
      <span className="dot" style={{ background: meta.color }} />
      {meta.label}
    </span>
  );
}
