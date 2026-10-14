import type { AgentEvent } from "../api";
import { agentColor } from "../theme";

const NUM_DOTS = 5;
const LOOP_SECONDS = 6;

/** Recent agents, newest first, deduped consecutively, capped at NUM_DOTS —
 * used to color the dots after whichever agent was active most recently. */
function recentAgentColors(events: AgentEvent[]): string[] {
  const colors: string[] = [];
  let last: string | null = null;
  for (const e of events) {
    if (e.agent === last) continue;
    colors.push(agentColor(e.agent).light);
    last = e.agent;
    if (colors.length >= NUM_DOTS) break;
  }
  const distinctCount = colors.length;
  for (let i = 0; distinctCount > 0 && colors.length < NUM_DOTS; i++) {
    colors.push(colors[i % distinctCount]);
  }
  return colors;
}

/** Dots that run clockwise around the page border, colored by whichever
 * agent was most recently active — a glanceable "the team is thinking"
 * indicator, only shown while a ticket is actively being resolved. */
export function BorderDots({ events }: { events: AgentEvent[] }) {
  const colors = recentAgentColors(events);
  if (colors.length === 0) return null;

  return (
    <div className="border-dots" aria-hidden="true">
      {colors.map((color, i) => (
        <span
          key={i}
          className="border-dot"
          style={{
            background: color,
            boxShadow: `0 0 6px ${color}`,
            animationDuration: `${LOOP_SECONDS}s`,
            animationDelay: `${-(i * LOOP_SECONDS) / colors.length}s`,
          }}
        />
      ))}
    </div>
  );
}
