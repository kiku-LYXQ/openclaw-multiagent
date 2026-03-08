interface LogsPanelProps {
  judgements: string[];
}

export function LogsPanel({ judgements }: LogsPanelProps) {
  const hasEntries = judgements.length > 0;
  const headline = hasEntries ? judgements[0] : "Awaiting GameState feed";
  return (
    <div className="panel">
      <div className="hud-banner" style={{ marginBottom: "0.5rem" }}>
        <div>
          <p className="hud-label">Recent judgements</p>
          <p className="hud-value" style={{ fontSize: "1.15rem" }}>{headline}</p>
        </div>
      </div>
      {hasEntries ? (
        <ul className="logs-list">
          {judgements.map((entry, index) => (
            <li key={`${entry}-${index}`} className="log-pill">
              <span>{entry}</span>
              <span aria-hidden="true">•</span>
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ color: "var(--text-muted)" }}>Waiting for rhythm data...</p>
      )}
    </div>
  );
}
