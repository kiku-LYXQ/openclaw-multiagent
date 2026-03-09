import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AgentPanel } from "./components/AgentPanel";
import { ControlPanel } from "./components/ControlPanel";
import { LogsPanel } from "./components/LogsPanel";
import { ParticleCanvas } from "./components/ParticleCanvas";
import { ThemeToggle } from "./components/ThemeToggle";
import { TimelinePanel } from "./components/TimelinePanel";
import { GameState, BeatTimelineEntry } from "./types/gameState";
import "./styles.css";

const DEFAULT_GAME_STATE: GameState = {
  bpm: 128,
  current_beat: 0,
  score_state: {
    score: 812_450,
    combo: 56,
    high_score: 990_000,
    last_judgement: "Perfect",
  },
  agent_states: [
    {
      name: "Echo",
      role: "Scout",
      status: "Ready",
      next_window: 0.6,
      combo: 12,
      sound_label: "Pulse",
      color: "#f472b6",
    },
    {
      name: "Northwind",
      role: "Support",
      status: "Standby",
      next_window: 0.9,
      combo: 9,
      sound_label: "Chime",
      color: "#34d399",
    },
    {
      name: "Argus",
      role: "Tank",
      status: "Guard",
      next_window: 1.15,
      combo: 6,
      sound_label: "Ground",
      color: "#60a5fa",
    },
  ],
  beat_timeline: [
    {
      beat_index: 1,
      agent_name: "Echo",
      label: "Pulse strip",
      color: "#f472b6",
      success: true,
      timestamp: Date.now() + 300,
    },
    {
      beat_index: 2,
      agent_name: "Northwind",
      label: "Halo weave",
      color: "#34d399",
      success: false,
      timestamp: Date.now() + 700,
    },
    {
      beat_index: 3,
      agent_name: "Argus",
      label: "Shield drop",
      color: "#60a5fa",
      success: true,
      timestamp: Date.now() + 1100,
    },
  ],
  recent_judgements: ["Awaiting signal", "Echo Perfect", "Northwind Great"],
};

const JUDGEMENT_LABELS = ["Perfect", "Great", "Good", "Miss", "Late", "Early"];
const CONTROL_BUTTONS = [
  { label: "Resume Engine", action: "resume" },
  { label: "Pause Engine", action: "pause" },
  { label: "Reset Engine", action: "reset" },
];

const instrumentSampleMap: Record<string, string> = {
  Echo: "/samples/violin.mp3",
  Northwind: "/samples/piano.mp3",
  Argus: "/samples/cello.mp3",
};
const defaultSample = "/samples/pad.mp3";
const THEME_KEY = "hud-theme";
const WS_URL = import.meta.env.VITE_GAME_STATE_WS ?? "ws://localhost:8000/ws/state";
const CONTROL_BASE = (import.meta.env.VITE_CONTROL_API ?? "http://localhost:8000").replace(/\/+$/, "");

function clampHistory(prev: string[], next: string, limit = 8) {
  return [next, ...prev].slice(0, limit);
}

function generateMockState(prev: GameState): GameState {
  const nextBeat = prev.current_beat + 1;
  const judgement = JUDGEMENT_LABELS[Math.floor(Math.random() * JUDGEMENT_LABELS.length)];
  const agentIndex = nextBeat % prev.agent_states.length;
  const agent = prev.agent_states[agentIndex];
  const scoreDelta = judgement === "Perfect" ? 450 : judgement === "Great" ? 240 : judgement === "Miss" ? -120 : 180;
  const nextScore = Math.max(0, prev.score_state.score + scoreDelta);
  const combo = judgement === "Miss" ? 0 : prev.score_state.combo + 1;
  const nextAgents = prev.agent_states.map((state, index) => ({
    ...state,
    status: index === agentIndex ? (judgement === "Miss" ? "Recovering" : "Running") : state.status,
    combo: Math.max(0, state.combo + (index === agentIndex && judgement !== "Miss" ? 1 : 0)),
    next_window: parseFloat((Math.max(0.25, state.next_window + (Math.random() - 0.5) * 0.08)).toFixed(2)),
  }));
  const timeline = new Array(6).fill(null).map((_, index) => {
    const offsetAgent = nextAgents[(agentIndex + index) % nextAgents.length];
    return {
      beat_index: nextBeat + index,
      agent_name: offsetAgent.name,
      label: index % 2 === 0 ? "Pulse surge" : "Field weave",
      color: offsetAgent.color,
      success: Math.random() > 0.3,
      timestamp: Date.now() + (index + 1) * 450,
    };
  });
  const judgementLine = `${agent.name} • ${judgement}`;

  return {
    bpm: 110 + Math.round(Math.sin(nextBeat / 3) * 12),
    current_beat: nextBeat,
    score_state: {
      score: nextScore,
      combo,
      high_score: Math.max(prev.score_state.high_score, nextScore),
      last_judgement: judgementLine,
    },
    agent_states: nextAgents,
    beat_timeline: timeline,
    recent_judgements: clampHistory(prev.recent_judgements, judgementLine, 8),
  };
}

export function App() {
  const [gameState, setGameState] = useState<GameState>(DEFAULT_GAME_STATE);
  const [connection, setConnection] = useState<"connecting" | "connected" | "disconnected" | "mock">("connecting");
  const [theme, setTheme] = useState(() => {
    if (typeof window !== "undefined") {
      return window.localStorage.getItem(THEME_KEY) ?? "nebula";
    }
    return "nebula";
  });

  const [helpOpen, setHelpOpen] = useState(false);
  const [pauseOpen, setPauseOpen] = useState(false);
  const [controlMessage, setControlMessage] = useState<string>("");
  const [musicEnabled, setMusicEnabled] = useState(false);
  const [backgroundVolume, setBackgroundVolume] = useState(0.08);
  const [judgementVolume, setJudgementVolume] = useState(0.4);
  const [engineStatus, setEngineStatus] = useState<"running" | "paused" | "reset">("running");
  const [pausedTimeline, setPausedTimeline] = useState<BeatTimelineEntry[]>([]);
  const [beatPulse, setBeatPulse] = useState(0);
  const lastBeatRef = useRef<number>(gameState.current_beat);
  const beatTimerRef = useRef<number>();
  const judgementRef = useRef<string>(gameState.score_state.last_judgement);
  const audioContextRef = useRef<AudioContext | null>(null);
  const musicNodesRef = useRef<{
    gain: GainNode;
    source: AudioNode | null;
  } | null>(null);
  const ambientBufferRef = useRef<AudioBuffer | null>(null);
  const ambientSourceRef = useRef<AudioBufferSourceNode | null>(null);

  const initAudioContext = useCallback(() => {
    if (typeof window === "undefined") return null;
    const AudioCtor = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtor) return null;
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioCtor();
    }
    return audioContextRef.current;
  }, []);

  const loadAmbientBuffer = useCallback(async () => {
    if (ambientBufferRef.current) {
      return ambientBufferRef.current;
    }
    const ctx = initAudioContext();
    if (!ctx) return null;
    try {
      const response = await fetch("/ambient.mp3");
      const array = await response.arrayBuffer();
      const buffer = await ctx.decodeAudioData(array);
      ambientBufferRef.current = buffer;
      return buffer;
    } catch (error) {
      console.warn("无法加载 ambient 音乐", error);
      ambientBufferRef.current = null;
      return null;
    }
  }, [initAudioContext]);
  const sampleBuffersRef = useRef<Record<string, AudioBuffer | null>>({});
  const parseJudgementLabel = useCallback((label: string) => {
    const [agentPart, judgementPart] = label.split("•").map((part) => part.trim());
    return { agent: agentPart || "", judgement: judgementPart || "" };
  }, []);
  const loadInstrumentSample = useCallback(async (ctx: AudioContext, agent: string) => {
    const key = agent || "default";
    if (sampleBuffersRef.current[key]) {
      return sampleBuffersRef.current[key];
    }
    const url = instrumentSampleMap[agent] ?? defaultSample;
    try {
      const response = await fetch(url);
      const array = await response.arrayBuffer();
      const buffer = await ctx.decodeAudioData(array);
      sampleBuffersRef.current[key] = buffer;
      return buffer;
    } catch (error) {
      console.warn("无法加载乐器样本", url, error);
      sampleBuffersRef.current[key] = null;
      return null;
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(THEME_KEY, theme);
    }
  }, [theme]);

  useEffect(() => {
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => undefined);
        audioContextRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!musicEnabled) {
      const nodes = musicNodesRef.current;
      if (nodes) {
        nodes.gain.gain.setTargetAtTime(0.0001, audioContextRef.current?.currentTime ?? 0, 0.05);
      }
      if (ambientSourceRef.current) {
        const source = ambientSourceRef.current;
        source.stop();
        ambientSourceRef.current = null;
      }
      return;
    }
    const ctx = initAudioContext();
    if (!ctx) return;
    const filter = ctx.createBiquadFilter();
    const gain = ctx.createGain();
    filter.type = "lowpass";
    filter.frequency.value = 800;
    gain.gain.value = 0;
    filter.connect(gain);
    gain.connect(ctx.destination);
    let source: AudioNode | null = null;
    const startAmbient = async () => {
      const buffer = await loadAmbientBuffer();
      if (buffer) {
        const bufferSource = ctx.createBufferSource();
        bufferSource.buffer = buffer;
        bufferSource.loop = true;
        bufferSource.connect(filter);
        bufferSource.start();
        ambientSourceRef.current = bufferSource;
        source = bufferSource;
      } else {
        const oscillator = ctx.createOscillator();
        oscillator.type = "triangle";
        oscillator.frequency.value = 200;
        oscillator.connect(filter);
        oscillator.start();
        source = oscillator;
      }
      musicNodesRef.current = { gain, source };
      gain.gain.setTargetAtTime(backgroundVolume, ctx.currentTime, 0.2);
    };
    startAmbient();
    return () => {
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.5);
      if (source instanceof OscillatorNode || source instanceof AudioBufferSourceNode) {
        source.stop(ctx.currentTime + 0.5);
      }
      ambientSourceRef.current = null;
      musicNodesRef.current = null;
    };
  }, [musicEnabled, loadAmbientBuffer, initAudioContext]);

  const playJudgementTone = useCallback(async (label: string) => {
    const ctx = initAudioContext();
    if (!ctx) return;
    const { agent } = parseJudgementLabel(label);
    const buffer = await loadInstrumentSample(ctx, agent);
    if (!buffer) {
      return;
    }
    const now = ctx.currentTime;
    const gain = ctx.createGain();
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.loop = false;
    source.connect(gain);
    gain.connect(ctx.destination);
    gain.gain.setValueAtTime(judgementVolume, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.8);
    source.start(now);
    source.stop(now + 1.1);
  }, [initAudioContext, loadInstrumentSample, parseJudgementLabel, judgementVolume]);
  useEffect(() => {
    const latest = gameState.recent_judgements[0] ?? "";
    if (!latest) return;
    if (latest !== judgementRef.current) {
      judgementRef.current = latest;
      playJudgementTone(latest);
    }
  }, [gameState.recent_judgements, playJudgementTone]);

  useEffect(() => {
    if (gameState.current_beat !== lastBeatRef.current) {
      lastBeatRef.current = gameState.current_beat;
      setBeatPulse(1);
      if (beatTimerRef.current) {
        window.clearTimeout(beatTimerRef.current);
      }
      beatTimerRef.current = window.setTimeout(() => {
        setBeatPulse(0);
      }, 220);
    }
  }, [gameState.current_beat]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let mockHandle: number | null = null;
    let fallbackTimer: number | null = null;
    let liveConnected = false;

    const startMock = () => {
      if (mockHandle) return;
      setConnection("mock");
      mockHandle = window.setInterval(() => {
        setGameState((prev) => generateMockState(prev));
      }, 1400);
    };

    try {
      ws = new WebSocket(WS_URL);
    } catch (error) {
      startMock();
    }

    if (ws) {
      ws.addEventListener("open", () => {
        liveConnected = true;
        setConnection("connected");
        if (mockHandle) {
          window.clearInterval(mockHandle);
          mockHandle = null;
        }
      });

      ws.addEventListener("message", (event) => {
        try {
          const payload = JSON.parse(event.data);
          setGameState((prev) => ({
            ...prev,
            ...payload,
            agent_states: payload.agent_states ?? prev.agent_states,
            beat_timeline: payload.beat_timeline ?? prev.beat_timeline,
            recent_judgements: payload.recent_judgements ?? prev.recent_judgements,
          }));
          setConnection("connected");
        } catch (error) {
          console.warn("无法解析 GameState", error);
        }
      });

      ws.addEventListener("close", () => {
        setConnection("disconnected");
        startMock();
      });

      ws.addEventListener("error", () => {
        setConnection("disconnected");
        startMock();
      });
    }

    fallbackTimer = window.setTimeout(() => {
      if (!liveConnected) {
        setConnection("mock");
        startMock();
      }
    }, 1200);

    return () => {
      ws?.close();
      if (fallbackTimer) {
        window.clearTimeout(fallbackTimer);
      }
      if (mockHandle) {
        window.clearInterval(mockHandle);
      }
    };
  }, []);

  const connectionLabel = useMemo(() => {
    switch (connection) {
      case "connected":
        return "实时连接";
      case "mock":
        return "模拟数据";
      case "disconnected":
        return "失去连接";
      default:
        return "连接中";
    }
  }, [connection]);

  const handleVolumeChange = (background: number, judgement: number) => {
    setBackgroundVolume(background);
    setJudgementVolume(judgement);
  };

  const updateEngineStatus = (status: "running" | "paused" | "reset") => {
    setEngineStatus(status);
  };

  useEffect(() => {
    if (engineStatus === "paused") {
      setPausedTimeline(gameState.beat_timeline);
    } else {
      setPausedTimeline([]);
    }
  }, [engineStatus, gameState.beat_timeline]);

  const sendControl = async (action: string) => {
    setControlMessage("发送中...");
    try {
      const response = await fetch(`${CONTROL_BASE}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "hud-client" }),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = await response.json();
      const status = payload.status as "running" | "paused" | "reset" | undefined;
      if (status) {
        updateEngineStatus(status);
      } else if (action === "pause") {
        updateEngineStatus("paused");
      } else {
        updateEngineStatus("running");
      }
      setControlMessage(`控制指令 ${action} 已发送`);
    } catch (error) {
      setControlMessage(`控制失败: ${error instanceof Error ? error.message : "未知"}`);
    }
    window.setTimeout(() => {
      setControlMessage("");
    }, 2600);
  };

  const timelineEntries = engineStatus === "paused" && pausedTimeline.length ? pausedTimeline : gameState.beat_timeline;
  const timelineLabel = engineStatus === "paused" ? "Recent beats (paused)" : "Upcoming beats";
  const timelineStatus = engineStatus === "paused" ? `Timeline frozen at beat ${gameState.current_beat}` : `Rolling ${gameState.beat_timeline.length}`;

  const particleIntensity = Math.min(1, beatPulse + Math.max(0, (gameState.bpm - 90) / 200));

  return (
    <div className="app-shell">
      <ParticleCanvas intensity={particleIntensity} />
      <div className="hud-header">
        <div className="hud-header-info">
          <p className="hud-label">Raid HUD</p>
          <h1>Sentinel Command</h1>
          <p className="hud-subtitle">BPM {gameState.bpm} · Beat {gameState.current_beat}</p>
        </div>
        <div className="hud-score">
          <div className="hud-score-value">{gameState.score_state.score.toLocaleString()}</div>
          <div className="hud-score-details">
            <span>Combo {gameState.score_state.combo}</span>
            <span>High {gameState.score_state.high_score.toLocaleString()}</span>
            <span>Last {gameState.score_state.last_judgement}</span>
          </div>
        </div>
        <div className="hud-header-actions">
          <ThemeToggle value={theme} onChange={(value) => setTheme(value)} />
          <button
            className={`icon-button${musicEnabled ? " active" : ""}`}
            onClick={() => {
              const ctx = initAudioContext();
              if (ctx && ctx.state === "suspended") {
                ctx.resume().catch(() => undefined);
              }
              setMusicEnabled((prev) => !prev);
            }}
            aria-label="Toggle ambient music"
          >
            ♫
          </button>
          <button className="icon-button" onClick={() => setHelpOpen(true)} aria-label="Help">
            ?
          </button>
          <button className="icon-button secondary" onClick={() => setPauseOpen(true)}>
            Pause
          </button>
          <span className="connection-badge">{connectionLabel}</span>
        </div>
      </div>

      <div className="hud-layout">
        <aside className="hud-side">
          <section className="panel agent-card">
            <h3>Agents</h3>
            <AgentPanel agents={gameState.agent_states} />
          </section>
          <section className="panel logs-card">
            <h3>Judgements</h3>
            <LogsPanel judgements={gameState.recent_judgements} />
          </section>
        </aside>
        <main className="hud-main">
          <section className="panel timeline-card">
            <div className="timeline-header">
              <h3>{timelineLabel}</h3>
              <span className="timeline-status">{timelineStatus}</span>
            </div>
            <TimelinePanel entries={timelineEntries} currentBeat={gameState.current_beat} headerLabel={timelineLabel} statusText={timelineStatus} />
          </section>
          <section className="panel control-card">
            <h3>Controls & Stats</h3>
            <ControlPanel
              connection={connectionLabel}
              controlBase={CONTROL_BASE}
              statusMessage={controlMessage}
              onControl={sendControl}
              controls={CONTROL_BUTTONS}
              volumeSettings={{ background: backgroundVolume, judgement: judgementVolume }}
              onVolumeChange={handleVolumeChange}
              engineStatus={engineStatus}
            />
          </section>
        </main>
      </div>

      {helpOpen && (
        <div className="overlay">
          <div className="overlay-panel">
            <h2>操作指南</h2>
            <p>HUD 会尝试连接到 <strong>{WS_URL}</strong>，如果连接失败会显示模拟数据。</p>
            <div className="help-grid">
              <div>
                <strong>WebSocket 期望格式</strong>
                <pre>
{`{
  bpm: number,
  current_beat: number,
  score_state: { ... },
  agent_states: [...],
  beat_timeline: [...],
  recent_judgements: [...]
}`}
                </pre>
              </div>
              <div>
                <strong>REST 控制</strong>
                <p>POST {CONTROL_BASE}/resume</p>
                <p>POST {CONTROL_BASE}/pause</p>
                <p>POST {CONTROL_BASE}/reset</p>
              </div>
            </div>
            <button className="button" onClick={() => setHelpOpen(false)}>
              关闭
            </button>
          </div>
        </div>
      )}

      {pauseOpen && (
        <div className="overlay">
          <div className="overlay-panel">
            <h2>已暂停</h2>
            <p>HUD 会在恢复后重新同步。按 Resume 或在控制面板手动刷新接口。</p>
            <button className="button" onClick={() => setPauseOpen(false)}>
              Resume
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
