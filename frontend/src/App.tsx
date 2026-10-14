import { useEffect, useRef, useState } from "react";
import "./App.css";
import { api, type AgentEvent, type CashBalance as CashBalanceType, type PaymentsReport, type Ticket } from "./api";
import { TicketList } from "./components/TicketList";
import { AgentFeed } from "./components/AgentFeed";
import { AgentSummaryList } from "./components/AgentSummaryList";
import { AgentLegend } from "./components/AgentLegend";
import { ApprovalPanel } from "./components/ApprovalPanel";
import { CashBalance } from "./components/CashBalance";
import { FundsSpent } from "./components/FundsSpent";
import { CustomerServiceDraftPanel } from "./components/CustomerServiceDraftPanel";
import { BorderDots } from "./components/BorderDots";
import { deriveResolution, deriveCustomerServiceDraft } from "./eventText";

const POLL_MS = 1500;

type DetailTab = "activity" | "draft";

function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [cash, setCash] = useState<CashBalanceType | null>(null);
  const [cashDropped, setCashDropped] = useState(false);
  const [payments, setPayments] = useState<PaymentsReport | null>(null);
  const [detailTab, setDetailTab] = useState<DetailTab>("activity");
  const [showApproval, setShowApproval] = useState(false);
  const prevBalance = useRef<number | null>(null);
  const pollRef = useRef<number | null>(null);

  const selectedTicket = tickets.find((t) => t.id === selectedId) ?? null;
  const resolution = deriveResolution(events);
  const draft = deriveCustomerServiceDraft(events);

  function refreshTickets() {
    api.getTickets().then(setTickets).catch(console.error);
  }

  function refreshCash() {
    api.getCash().then((c) => {
      if (prevBalance.current !== null && c.balance !== undefined && c.balance < prevBalance.current) {
        setCashDropped(true);
      }
      if (c.balance !== undefined) prevBalance.current = c.balance;
      setCash(c);
    });
  }

  function refreshPayments() {
    api.getPayments().then(setPayments).catch(console.error);
  }

  useEffect(() => {
    refreshTickets();
    refreshCash();
    refreshPayments();
  }, []);

  useEffect(() => {
    setCashDropped(false);
    setDetailTab("activity");
    setShowApproval(false);
    if (selectedId !== null) {
      api.getRecentEvents(selectedId).then(setEvents).catch(console.error);
    } else {
      setEvents([]);
    }
  }, [selectedId]);

  useEffect(() => {
    if (running && selectedId !== null) {
      pollRef.current = window.setInterval(() => {
        api.getRecentEvents(selectedId).then(setEvents).catch(console.error);
      }, POLL_MS);
      return () => {
        if (pollRef.current) window.clearInterval(pollRef.current);
      };
    }
  }, [running, selectedId]);

  async function handleRun(ticketId: number) {
    setSelectedId(ticketId);
    setRunning(true);
    try {
      await api.resolveTicket(ticketId);
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
      const finalEvents = await api.getRecentEvents(ticketId);
      setEvents(finalEvents);
      refreshTickets();
      refreshCash();
      refreshPayments();
    }
  }

  function handleReset() {
    api.resetDatabase().then(() => {
      refreshTickets();
      refreshCash();
      refreshPayments();
      setEvents([]);
      setShowApproval(false);
    });
  }

  function handleApproved() {
    refreshCash();
    refreshTickets();
    refreshPayments();
  }

  return (
    <div className="app-shell">
      {running && <BorderDots events={events} />}
      <div className="app-header">
        <div>
          <h1>Campus Customs — Desk</h1>
          <p>Pick a ticket, run the agent team, and watch them work.</p>
        </div>
        <div className="toolbar">
          <button className="reset-btn" onClick={handleReset}>
            Reset database
          </button>
          <FundsSpent report={payments} />
          <CashBalance cash={cash} dropped={cashDropped} />
        </div>
      </div>

      <div className="layout">
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Tickets</h3>
          <TicketList tickets={tickets} selectedId={selectedId} onSelect={setSelectedId} />
        </div>

        <div className="card detail-panel">
          {!selectedTicket && <p className="empty-state">Select a ticket to get started.</p>}

          {selectedTicket && (
            <>
              <div className="detail-header">
                <div>
                  <h3>
                    Ticket {selectedTicket.id} — {selectedTicket.subject}
                  </h3>
                  <p style={{ margin: "4px 0 0", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                    {selectedTicket.notes}
                  </p>
                </div>
                <button
                  className="run-btn"
                  disabled={running}
                  onClick={() => handleRun(selectedTicket.id)}
                >
                  {running ? "Running…" : "Run agent team"}
                </button>
              </div>

              {resolution && (
                <div className="summary-box">
                  <h4>Resolution</h4>
                  <p>{resolution.summary}</p>
                  {resolution.next_steps.length > 0 && (
                    <ul>
                      {resolution.next_steps.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {selectedTicket.status === "needs_human_approval" && !showApproval && (
                <button className="approve-toggle-btn" onClick={() => setShowApproval(true)}>
                  Review &amp; approve payment
                </button>
              )}

              {selectedTicket.status === "needs_human_approval" && showApproval && (
                <ApprovalPanel ticket={selectedTicket} onApproved={handleApproved} />
              )}

              <AgentLegend />

              <div className="detail-tabs">
                <button
                  className={detailTab === "activity" ? "active" : ""}
                  onClick={() => setDetailTab("activity")}
                >
                  Activity
                </button>
                <button className={detailTab === "draft" ? "active" : ""} onClick={() => setDetailTab("draft")}>
                  Customer Service Draft
                </button>
              </div>

              {detailTab === "activity" && (
                <>
                  <div>
                    <h4 style={{ marginBottom: 8 }}>Agent activity</h4>
                    <AgentFeed events={events} />
                  </div>

                  {events.length > 0 && (
                    <div>
                      <h4 style={{ marginBottom: 8 }}>What each agent said</h4>
                      <AgentSummaryList events={events} />
                    </div>
                  )}
                </>
              )}

              {detailTab === "draft" && <CustomerServiceDraftPanel draft={draft} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
