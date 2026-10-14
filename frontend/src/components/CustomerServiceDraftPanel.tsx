export function CustomerServiceDraftPanel({
  draft,
}: {
  draft: { draft_message: string; requires_followup: boolean } | null;
}) {
  if (!draft) {
    return <p className="empty-state">No customer-service draft yet for this ticket.</p>;
  }
  return (
    <div className="draft-panel">
      <div className="draft-note">Draft only — stays on the board, never sent automatically.</div>
      <pre className="draft-text">{draft.draft_message}</pre>
      {draft.requires_followup && (
        <div className="draft-followup">Needs a human follow-up before this can go out.</div>
      )}
    </div>
  );
}
