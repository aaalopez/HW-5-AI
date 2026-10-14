import { AGENT_COLORS } from "../theme";

export function AgentLegend() {
  return (
    <div className="legend">
      {(Object.keys(AGENT_COLORS) as (keyof typeof AGENT_COLORS)[]).map((key) => (
        <span className="swatch" key={key}>
          <span className="dot" style={{ background: AGENT_COLORS[key].light }} />
          {AGENT_COLORS[key].label}
        </span>
      ))}
    </div>
  );
}
