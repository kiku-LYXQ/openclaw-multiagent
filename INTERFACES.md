# 接口契约文档

本文档列出音乐游戏核心模块（Agent、节奏引擎、调度器、渲染器）的函数/信号契约，方便各 coder 依据相同约定实现行为。所有契约均参照 `DESIGN_DOC.md` 中的第 2 节和第 6 节说明。

## 1. Agent（`agents/agent.py`）
| 接口 | 输入 | 输出 | 说明 |
| --- | --- | --- | --- |
| `tick(timestamp: float)` | 当前 tick 时间（秒） | `None` | 更新内部状态机：Idle → Ready → Action → Cooldown；根据 timing tolerance 判断是否进入准备状态。 |
| `input(event: RhythmEvent)` | `RhythmEvent(action='hit'/'hold'/'release', timestamp: float, agent: str)` | `RhythmResult(success: bool, timing: float, status_label: str)` | Agent 接收调度器下发的事件，返回结果：`success` 供 score 计算，`timing` 提供精准误差，`status_label` 用于 UI 状态卡。 |
| `state()` | `None` | `dict`（包含 `name`, `role`, `status`, `next_window`, `combo`） | 渲染器获取 agent 当前状态；内容必须包含 color/sound_label/strictness 以支持 HUD。 |
| `reset()`（可选） | `None` | `None` | 重置 combo 与 cooldown，便于重赛或测试。 |

## 2. 节奏引擎（`engine/beat_engine.py`）
| 接口 | 输入 | 输出 | 说明 |
| --- | --- | --- | --- |
| `subscribe(agent)` | Agent 实例 | `None` | 注册 agent，让引擎在每个 beat 调用其 `tick`。 |
| `start(pattern: RhythmPattern, bpm: float)` | 节奏模式（List of dict）、BPM | `None` | 启动定时器；每个 beat 发出 `beat_signal(time: float, index: int)`。 |
| `stop()` | `None` | `None` | 停止 beat 线程并清理状态。 |
| `beat_signal`（信号） | `timestamp: float`, `index: int` | `None` | 内部定时器每拍触发，供调度器/渲染器监听；信号需携带节奏索引与时间戳。 |

## 3. 调度器与评分（`engine/scheduler.py`）
| 接口 | 输入 | 输出 | 说明 |
| --- | --- | --- | --- |
| `dispatch(current_beat: dict, agents: Sequence[Agent])` | 当前节奏事件（包含 agent/action）、agent 列表 | `List[RhythmResult]` | 在对应 beat 触发 `RhythmEvent`，调用 agent.input，并聚合结果用于 scoring。 |
| `scoreboard()` | `None` | `ScoreState(score: int, combo: int, last_judgement: str, fail_reason: Optional[str])` | 返回当前得分态势，供 Renderer 显示。 |
| `register_input(player_event: RhythmEvent)` | 玩家输入事件 | `None` | 输入由调度器转发至对应 Agent，或用作 combo 计算。 |
| `reset()` | `None` | `None` | 重置 score/combo/high score；用于新 song/测试循环。 |

## 4. 渲染器（`ui/console.py`）
| 接口 | 输入 | 输出 | 说明 |
| --- | --- | --- | --- |
| `render(state: GameState)` | `GameState`（包含 BPM、score、combo、agents states、history） | `None` | 绘制节奏线、agent 状态卡、banner；应适配终端宽度，支持颜色区分（rich）和 beat flash。 |
| `show_help()` | `None` | `None` | 展示帮助 overlay（键位说明、high score、暂停提示），覆盖当前视图但不清除已有状态。 |
| `toggle_pause()` | `None` | `bool`（是否处于暂停） | 切换暂停状态，并让 engine/renderer 进入等待／恢复。 |
| `flush_history(history: Sequence[str])`（可选） | 历史 judgment | `None` | 将 judgement log 输出到右侧/底部面板，便于追踪 combo 变化。 |

## 5. 信号与数据结构（跨模块契约）
| 名称 | 生产者 | 消费者 | 说明 |
| --- | --- | --- | --- |
| `RhythmEvent` | Scheduler / Player Input | Agent | 包含字段 `agent`, `action`, `timestamp`, `priority`；用于指示何时命中。 |
| `RhythmResult` | Agent | Scheduler | `success` 表示命中，`timing`（误差 ms），`status_label` 用作 UI 状态提示。 |
| `GameState` | Scheduler/Engine | Renderer | 汇总 BPM、score/combo、agent state、history、pause 状态，供 `render` 捕获并画面更新。 |
| `beat_signal` | Beat Engine | Scheduler / Renderer | 每拍发生，包含 `timestamp`, `index`，供调度器生成事件与渲染器闪烁节奏线。

> 本文档即为各 coder 协作时的接口参照，所有新增模块与信号均应在此处补充，确保 `new-app/README.md` 与 `Design Doc` 的流程一致。
