# 音乐游戏 Agent 项目设计

## 1. 项目概览
目标是构建一套基于节奏（BPM）的多 agent 游戏：每个 agent 代表一种乐器（如钢琴、小提琴），通过文本方式表现声音与动作。游戏以命令行/terminal 为界面，展示节奏线、agent 状态、combo、分数和帮助提示，突出钢琴/小提琴等乐器元素的“节奏感”。

## 2. 模块与接口
### 2.1 Agent 模块（`agents/agent.py`）
- **接口**：
  - `tick(timestamp: float)`：在每个 beat 更新内部状态。
  - `input(event: RhythmEvent)`：接收 `RhythmEvent(action='hit'/'hold'/'release', timestamp)` 并返回 `RhythmResult(success, timing, status_label)`。
  - `state()`：返回`{name, role, status, next_window, combo}`供 UI 展示。
- **状态机**：Idle → Ready → Action → Cooldown，包含 timing tolerance 与 strictness。
- **继承**：`PianoAgent` 和 `ViolinAgent` 继承 `BaseAgent`，分别设置不同 `sound_label`, `color`, `timing_tolerance`。

### 2.2 节奏引擎（`engine/beat_engine.py`）
- **接口**：
  - `subscribe(agent)` 注册 agent。
  - `start(pattern: RhythmPattern, bpm: float)` 启动 timer。
  - `stop()` 停止。
- **输出**：每个 beat 触发 `beat_signal(Time, index)`，供 scheduler 与 renderer 使用。

### 2.3 调度器与评分（`engine/scheduler.py`）
- **输入**：agents、current beat、player inputs。
- **功能**：
  - 根据 pattern 在 beat 时刻 dispatch `RhythmEvent`。
  - 汇总每个 agent 返回的 `RhythmResult`，计算 score/combo、记录 `fail_reason`。
- **接口**：`scoreboard()` 返回 `ScoreState(score, combo, last_judgement)`。

### 2.4 界面渲染（`ui/console.py`）
- 使用 `rich`（或 `blessed`/`curses`）输出：
  - 顶部条：当前 BPM、score、combo、High Score。
  - 主区：节奏线（`|` 代表 beat）、音符指示（Color-coded bars for Piano & Violin）。
  - 右侧/底部：agent 状态卡（含 `sound_label`）与历史 judgement。
  - Overlay：暂停（P/p）提示、帮助（H/h）说明按键 + 当前 high score。支持窗口 resize。
- **接口**：`render(state: GameState)`、`show_help()`、`toggle_pause()`。

## 3. 数据与配置
- `RhythmPattern` 描述一个 song 中的 beat 节奏，如 `[{'time':0.5, 'agent':'piano', 'action':'hit'} ...]`。
- `game_config.yml` 或 Python constants 定义 BPM、agents 组合、color mapping。
- 高分存储：`highscore.json` 记录历史最高分、最佳 combo。

## 4. 开发流程建议
1. 先落实 agent + beat engine + scheduler 接口；每个模块编写 tests 说明 expected inputs/outputs。2. 再实现 UI rendering 模块，逐步加 overlay/pause/help/visual cues。3. 同时撰写 `new-app/README.md` 与 `INTERFACES.md`，记录每个模块的参数与预期行为，方便其他 coder 跟进。

## 5. 视觉/界面思路
- 采用彩色色块表示钢琴（蓝）与小提琴（紫），用 `rich` progress bar 模拟节奏通道。  
- 每个 beat 出现时在图形上短暂闪烁，用 `sound_label` 文字（如 `♪ PIANO` / `♪ VIOLIN`）。  
- 高分 banner 使用粗体 + box drawing characters，增强视觉层次。  
- 帮助 overlay 以半透明效果遮罩当前界面，列出 key legend。  

## 6. 接口文档准备
- `INTERFACES.md` 以表格形式列出每个 module 的 functions + expected input/output + dependencies。
- 每个 coder task prompt 会引用该文档，确保实现遵循统一契约。
