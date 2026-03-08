# HUD 项目开发脉络

## 一、需求起点
- 目标是将 WSL2 上运行的 CLI 节奏游戏（`BeatEngine` + `Scheduler`）替换为前后端分离的 Web HUD 控制台。主要要求包括：
  - 实时展示 BPM/score/combo、agent 状态、时间线、评判日志；
  - 提供 REST 控制（pause/resume/reset/logs/history）；
  - 浏览器播放粒子、主题、Web Audio，而非依赖 WSL 本地声卡；
  - Web 客户端可配置 WS/REST 接口并支持模拟数据回退。

## 二、架构与流程确认
- **后端**：保持 Python 引擎，新增 FastAPI 服务：
  - `GameServer` 管理 `BeatEngine`/`Scheduler`、日志、历史缓存、WebSocket 广播；
  - REST 接口：`/pause`/`/resume`/`/reset` 控制节奏，`/logs`/`/history` 查询记录；
  - WebSocket：默认 `/ws/state`，同时保留 legacy `/ws/game-state`；
  - 生命周期：使用 FastAPI `lifespan` 取代 `@app.on_event`，避免弃用警告；
  - 文档与测试：Makefile 添加 `run-server`/`test`，`README` 说明接口格式，`tests/test_server.py` 覆盖 REST & WS。
- **前端**：Vite + React + TypeScript SPA：
  - WebSocket `VITE_GAME_STATE_WS` 默认 `ws://localhost:8000/ws/state`，订阅 `GameState`；
  - REST 控制：通过 `VITE_CONTROL_API` 生成 `CONTROL_BASE`（默认 `http://localhost:8000`）；
  - HUD UI：Banner、Timeline、Agent、Logs、Control、Help/Pause 层；
  - 视觉/音频：粒子 Canvas 与 beat 脉冲联动、主题切换、Web Audio 判定音、模拟数据 fallback；
  - 文档：README 描述环境变量、接口格式、运行脚本。

## 三、技术栈选型
| 层 | 技术 | 说明 |
|---|---|---|
| 后端 | Python 3.12 + FastAPI + uvicorn | WebSocket + REST，`GameServer` 驱动 BeatEngine。 |
| 应用逻辑 | BeatEngine、Scheduler、GameService | 提供日志、历史、状态广播。 |
| 前端 | Vite + React + TypeScript | SPA 设计，环境变量配置灵活。 |
| 音频 | Web Audio API | judgement 事件触发不同频率 oscillator，避免 mp3。 |
| 动效 | Canvas + requestAnimationFrame | ParticleCanvas 根据 BPM/beat 创建粒子特效。 |
| 测试 | pytest | `tests/test_agents.py`、`tests/test_server.py` 分别覆盖逻辑与接口。 |

## 四、接口与配置确定流程
1. 使用 `models.py` 定义 `GameState`（含 bpm、current_beat、score_state、agent_states、beat_timeline、recent_judgements）。
2. REST 接口：控制（pause/resume/reset）与查询（logs/history）。
3. WebSocket：默认 `/ws/state` 发送 `{ "beat": ..., "timestamp": ..., "state": {...}}`，兼容 `/ws/game-state`。
4. 前端读取 `import.meta.env.VITE_GAME_STATE_WS` + `VITE_CONTROL_API`，`CONTROL_BASE` 拼接 action。

## 五、交付与验证
- `cd new-app && make test`（包含 agents/server tests）通过。
- `cd new-app/client && npm run build`（tsc + Vite build）通过。
- Reviewer hud-review-001（rerun）确认 webs/REST/构建命令一致、blocking issue 清除。

## 六、后续建议
- README 继续强调 `VITE_*` 环境变量和 WebSocket alias。 
- 若需部署，可添加 `make run-server`、Dockerfile 或部署说明。 
- 需要进一步演示或监控集成可单独拆出任务。
