import type { AgentEvent } from "../api";
import { agentColor } from "../theme";
import { summarizeByAgent } from "../eventText";

export function AgentSummaryList({ events }: { events: AgentEvent[] }) {
  const rows = summarizeByAgent(events);
  if (rows.length === 0) {
    return <p className="empty-state">No agent findings yet for this ticket.</p>;
  }
  return (
    <div className="agent-summary-list">
      {rows.map(({ agent, text }) => {
        const color = agentColor(agent);
        return (
          <div className="agent-summary-row" key={agent} style={{ borderLeftColor: color.light }}>
            <span className="agent-name" style={{ color: color.light }}>
              {color.label}
            </span>
            <span className="text">{text}</span>
          </div>
        );
      })}
    </div>
  );
}
