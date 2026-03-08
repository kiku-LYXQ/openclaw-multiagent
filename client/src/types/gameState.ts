export interface ScoreState {
  score: number;
  combo: number;
  high_score: number;
  last_judgement: string;
}

export interface AgentState {
  name: string;
  role: string;
  status: string;
  next_window: number;
  combo: number;
  sound_label: string;
  color: string;
}

export interface BeatTimelineEntry {
  beat_index: number;
  agent_name: string;
  label: string;
  color: string;
  success: boolean;
  timestamp: number;
}

export interface GameState {
  bpm: number;
  current_beat: number;
  score_state: ScoreState;
  agent_states: AgentState[];
  beat_timeline: BeatTimelineEntry[];
  recent_judgements: string[];
}
