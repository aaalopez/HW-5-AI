// Agent colors — fixed categorical assignment (never cycled/re-ranked),
// validated with the dataviz skill's palette validator (adjacent CVD + normal
// -vision checks pass in both light and dark; see output/design.md for the
// full rationale). Color is always paired with the agent's name as text —
// never the only way to tell agents apart (contrast WARN relief rule).
import { useEffect, useState } from "react";
import type { AgentName } from "./api";

export function usePrefersDark(): boolean {
  const [dark, setDark] = useState(
    () => window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false
  );
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => setDark(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return dark;
}

export function useAgentHex(agent: AgentName | "human"): string {
  const dark = usePrefersDark();
  const c = agentColor(agent);
  return dark ? c.dark : c.light;
}

export const AGENT_COLORS: Record<AgentName, { light: string; dark: string; label: string }> = {
  boss: { light: "#2a78d6", dark: "#3987e5", label: "Boss" },
  inventory: { light: "#eb6834", dark: "#d95926", label: "Inventory" },
  accounting: { light: "#1baf7a", dark: "#199e70", label: "Accounting" },
  facilities: { light: "#eda100", dark: "#c98500", label: "Facilities" },
  customer_service: { light: "#e87ba4", dark: "#d55181", label: "Customer Service" },
};

export const HUMAN_COLOR = { light: "#52514e", dark: "#c3c2b7", label: "Human" };

export function agentColor(agent: AgentName | "human"): { light: string; dark: string; label: string } {
  if (agent === "human") return HUMAN_COLOR;
  return AGENT_COLORS[agent];
}

// Fixed status palette (never themed/reused for anything else).
export const STATUS_COLORS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
};
