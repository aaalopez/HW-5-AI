import type { AgentEvent } from "./api";

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function parseOutput(output: unknown): Record<string, unknown> | null {
  if (typeof output !== "string") return null;
  try {
    return JSON.parse(output);
  } catch {
    return null;
  }
}

/** One short, plain-English line for a single audit event — used by the live feed. */
export function describeEvent(e: AgentEvent): string {
  const d = e.detail ?? {};
  switch (e.event) {
    case "run_start":
      return `started on ticket ${d.ticket_id}`;
    case "delegation":
      return `asked to help: "${truncate(String(d.message ?? ""), 110)}"`;
    case "tool_call": {
      const args = d.args ? JSON.stringify(d.args) : "{}";
      if (d.tool_name === "final_result") return "finishing up its finding";
      return `called ${d.tool_name}(${truncate(args, 70)})`;
    }
    case "tool_return": {
      if (d.tool_name === "final_result") return "submitted its finding";
      return `got a result back from ${d.tool_name}`;
    }
    case "run_end": {
      const parsed = parseOutput(d.output);
      const text =
        (parsed?.summary as string) ??
        (parsed?.recommendation as string) ??
        (parsed?.notes as string) ??
        (parsed?.draft_message as string) ??
        truncate(String(d.output ?? ""), 160);
      return `finished: ${truncate(String(text), 160)}`;
    }
    case "stop":
      return `stopped — ${d.reason ?? e.stop_reason ?? "limit reached"}`;
    default:
      return e.event;
  }
}

/** Last run_end per agent for a ticket — the "what each agent concluded" recap.
 * `events` arrives newest-first (see api.ts's getRecentEvents) — keep only the
 * FIRST run_end seen per agent, which is therefore the most recent one. */
export function summarizeByAgent(events: AgentEvent[]): { agent: AgentEvent["agent"]; text: string }[] {
  const latestByAgent = new Map<AgentEvent["agent"], AgentEvent>();
  for (const e of events) {
    if (e.event === "run_end" && !latestByAgent.has(e.agent)) latestByAgent.set(e.agent, e);
  }
  return Array.from(latestByAgent.entries()).map(([agent, e]) => {
    const parsed = parseOutput(e.detail.output);
    const text =
      (parsed?.summary as string) ??
      (parsed?.recommendation as string) ??
      (parsed?.notes as string) ??
      (parsed?.draft_message as string) ??
      truncate(String(e.detail.output ?? ""), 220);
    return { agent, text: truncate(String(text), 220) };
  });
}

/** The most recent top-level boss resolution for this ticket, reconstructed
 * from its last `run_end`, so it stays visible when revisiting an
 * already-resolved ticket (not only right after a fresh run). */
export function deriveResolution(
  events: AgentEvent[]
): { ticket_id: number; status: string; summary: string; next_steps: string[] } | null {
  for (const e of events) {
    if (e.agent === "boss" && e.event === "run_end") {
      const parsed = parseOutput(e.detail.output);
      if (parsed && "status" in parsed && "summary" in parsed) {
        return {
          ticket_id: parsed.ticket_id as number,
          status: parsed.status as string,
          summary: parsed.summary as string,
          next_steps: (parsed.next_steps as string[]) ?? [],
        };
      }
    }
  }
  return null;
}

/** The most recent customer_service draft for this ticket, in full (not truncated). */
export function deriveCustomerServiceDraft(
  events: AgentEvent[]
): { draft_message: string; requires_followup: boolean } | null {
  for (const e of events) {
    if (e.agent === "customer_service" && e.event === "run_end") {
      const parsed = parseOutput(e.detail.output);
      if (parsed && "draft_message" in parsed) {
        return {
          draft_message: parsed.draft_message as string,
          requires_followup: Boolean(parsed.requires_followup),
        };
      }
    }
  }
  return null;
}
