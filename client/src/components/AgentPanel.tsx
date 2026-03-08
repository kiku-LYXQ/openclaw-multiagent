import { AgentState } from "../types/gameState";

interface AgentPanelProps {
  agents: AgentState[];
}

export function AgentPanel({ agents }: AgentPanelProps) {
  return (
    <div className="panel">
      <div className="hud-banner" style={{ marginBottom: "0.75rem" }}>
        <div>
          <p className="hud-label">Agent roster</p>
          <p className="hud-value" style={{ fontSize: "1.15rem" }}>{agents.length}</p>
        </div>
      </div>
      <table className="agent-table">
        <thead>
          <tr>
            <th>Agent</th>
            <th>Role</th>
            <th>Status</th>
            <th>Combo</th>
            <th>Window</th>
          </tr>
        </thead>
        <tbody>
          {agents.map((agent) => (
            <tr key={agent.name} className="agent-row">
              <td>
                <strong>{agent.name}</strong>
                <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>{agent.sound_label}</div>
              </td>
              <td>{agent.role}</td>
              <td>
                <span className="agent-chip" style={{ borderColor: agent.color, color: agent.color }}>
                  {agent.status}
                </span>
              </td>
              <td>{agent.combo}</td>
              <td>{agent.next_window.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
