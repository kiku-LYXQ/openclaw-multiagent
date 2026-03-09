import { BeatTimelineEntry } from "../types/gameState";

interface TimelinePanelProps {
  entries: BeatTimelineEntry[];
  currentBeat: number;
  headerLabel?: string;
  statusText?: string;
}

export function TimelinePanel({ entries, currentBeat, headerLabel, statusText }: TimelinePanelProps) {
  const label = headerLabel ?? "Upcoming beats";
  const status = statusText ?? `Rolling ${entries.length}`;
  const display = entries.slice(0, 8);
  return (
    <div className="panel" aria-live="polite">
      <div className="hud-banner" style={{ marginBottom: "0.5rem" }}>
        <div>
          <p className="hud-label">{label}</p>
          <p className="hud-value" style={{ fontSize: "1.15rem" }}>
            Beat {currentBeat + 1}
          </p>
        </div>
        <span className="status-pill">{status}</span>
      </div>
      <div className="timeline">
        {display.map((entry) => (
          <div
            key={`${entry.beat_index}-${entry.agent_name}-${entry.timestamp}`}
            className={`timeline-card ${entry.success ? "success" : ""}`}
            style={{ borderColor: entry.success ? entry.color : undefined }}
          >
            <span className="beat">{entry.beat_index}</span>
            <span>
              <strong>{entry.agent_name}</strong>
            </span>
            <span>{entry.label}</span>
            <span>{entry.success ? "Hit" : "Miss"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
