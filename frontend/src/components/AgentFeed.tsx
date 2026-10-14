import type { AgentEvent } from "../api";
import { agentColor } from "../theme";
import { describeEvent } from "../eventText";

function FeedRow({ e }: { e: AgentEvent }) {
  const color = agentColor(e.agent);
  const time = new Date(e.ts).toLocaleTimeString();
  return (
    <div className="feed-row" style={{ borderLeftColor: color.light }}>
      <span className="agent-name" style={{ color: color.light }}>
        {color.label}
      </span>
      <span className="event-text">{describeEvent(e)}</span>
      <span className="ts">{time}</span>
    </div>
  );
}

export function AgentFeed({ events }: { events: AgentEvent[] }) {
  if (events.length === 0) {
    return <p className="feed-empty">No agent activity yet for this ticket — run the agent team to see it live.</p>;
  }
  // oldest first reads like a transcript
  const ordered = [...events].reverse();
  return (
    <div className="feed">
      {ordered.map((e, i) => (
        <FeedRow key={`${e.ts}-${i}`} e={e} />
      ))}
    </div>
  );
}
