import type { CashBalance as CashBalanceType } from "../api";

export function CashBalance({
  cash,
  dropped,
}: {
  cash: CashBalanceType | null;
  dropped: boolean;
}) {
  return (
    <div className="cash-pill">
      <span className="label">Checking balance</span>
      <span className={`value${dropped ? " dropped" : ""}`}>
        {cash?.found && cash.balance !== undefined
          ? `$${cash.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
          : "—"}
      </span>
    </div>
  );
}
