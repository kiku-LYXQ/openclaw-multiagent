import React from "react";

interface ControlPanelProps {
  connection: string;
  statusMessage: string;
  onControl: (action: string) => Promise<void>;
  controlBase: string;
  controls: Array<{ label: string; action: string }>;
  volumeSettings: {
    background: number;
    judgement: number;
  };
  onVolumeChange: (background: number, judgement: number) => void;
}

export function ControlPanel({ connection, statusMessage, onControl, controlBase, controls, volumeSettings, onVolumeChange }: ControlPanelProps) {
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
      <div className="volume-grid">
        <label>背景音乐音量
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={volumeSettings.background}
            onChange={(event) => onVolumeChange(parseFloat(event.target.value), volumeSettings.judgement)}
          />
        </label>
        <label>判定音音量
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={volumeSettings.judgement}
            onChange={(event) => onVolumeChange(volumeSettings.background, parseFloat(event.target.value))}
          />
        </label>
      </div>
      {statusMessage && <p className="control-status">{statusMessage}</p>}
    </div>
  );
}
