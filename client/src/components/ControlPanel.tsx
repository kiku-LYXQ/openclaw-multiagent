import React from "react";

interface ControlPanelProps {
  connection: string;
  statusMessage: string;
  onControl: (action: string) => Promise<void>;
  controlBase: string;
  controls: Array<{ label: string; action: string }>;
}

export function ControlPanel({ connection, statusMessage, onControl, controlBase, controls }: ControlPanelProps) {
  return (
    <div className="panel control-panel">
      <div className="hud-banner">
        <div>
          <p className="hud-label">REST 控制</p>
          <p className="hud-value" style={{ fontSize: "1rem" }}>{connection}</p>
        </div>
        <span className="status-pill" aria-live="polite" title={controlBase}>
          {controlBase}
        </span>
      </div>
      <div className="control-grid">
        {controls.map((control) => (
          <button
            key={control.action}
            className="button secondary"
            type="button"
            onClick={() => onControl(control.action)}
          >
            {control.label}
          </button>
        ))}
      </div>
      {statusMessage && <p className="control-status">{statusMessage}</p>}
    </div>
  );
}
