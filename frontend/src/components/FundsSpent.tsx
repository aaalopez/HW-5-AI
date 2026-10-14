import type { PaymentsReport } from "../api";

export function FundsSpent({ report }: { report: PaymentsReport | null }) {
  return (
    <div className="cash-pill">
      <span className="label">Funds spent</span>
      <span className="value">
        {report ? `$${report.total_spent.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "—"}
      </span>
    </div>
  );
}
