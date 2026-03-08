# HUD 控制台 (new-app/client)

这个前端项目基于 **Vite + React + TypeScript**，为节奏引擎构建了一个“游戏 HUD”控制台：

- **实时 WebSocket GameState**：连接后端提供的 `GameState` JSON（BPM、beat、得分、Agent、timeline、近期评判），并用横幅/时间线/Agent 表/日志卡片实时刷新数据。
- **节拍同步粒子与动效**：`ParticleCanvas` 通过 `requestAnimationFrame` 渲染玻璃质感背景 与流动粒子，beat 触发时候激活亮度/密度，配合 `beatPulse` 变量调节亮度。
- **Web Audio 合成**：`AudioContext` 在接收新的评判时播放合成音序（Perfect/Great/Miss 分别对应三角波/自定义频率）；首次播放会提示用户触发（按任意键或按钮）以唤醒音频上下文。
- **主题切换**：支持 `Nebula`、`Aurora`、`Dawn` 三主题，采用 CSS 变量控制 bg/panel/光晕，状态存入 `localStorage`；通过 `ThemeToggle` 按钮组切换。
- **帮助 & 暂停叠层**：点击 `?` 或 `Pause` 按钮显示操作说明，Help 叠层呈现 WebSocket/REST 说明，Pause 叠层模拟暂停反馈。
- **REST 控制 + 日志显示**：底部控制面板通过 POST 方式命令后端 `resume`/`pause`/`reset`，最近评判和 timeline 列表用来还原 CLI 体验。

## 准备环境

```bash
cd new-app/client
npm install
```

## 本地调试

```bash
npm run dev   # 启动 Vite 开发服务器
npm run build # 运行 tsc + vite build，以验证 HUD 可以编译并打包
```

## 可配置环境变量

| 环境变量 | 说明 | 默认值 |
| --- | --- | --- |
| `VITE_GAME_STATE_WS` | WebSocket GameState 来源（后端默认暴露在 `/ws/state`） | `ws://localhost:8000/ws/state` |
| `VITE_CONTROL_API` | REST 控制基地址（会自动拼接 `/resume`、`/pause`、`/reset`） | `http://localhost:8000` |

例如：

## 音乐模式
前端额外提供一个音乐图标按钮（♫），用于唤醒并切换浏览器端的 Ambient 背景音。HUD 连接成功后点击该按钮即可播放近似 Ludovico Einaudi 《Nuvole Bianche》风格的三角波 pad（也可继续点击关闭），该按钮会保留状态并与 AudioContext 内的 oscillator/gain 自动同步。此音乐模式可与粒子/节拍的动效共同渲染出更强的仪式感。


```bash
VITE_GAME_STATE_WS=ws://localhost:8000/ws/state VITE_CONTROL_API=http://localhost:8000 npm run dev
```

## WebSocket 数据结构

```ts
interface GameState {
  bpm: number;
  current_beat: number;
  score_state: { score: number; combo: number; high_score: number; last_judgement: string };
  agent_states: AgentState[];
  beat_timeline: BeatTimelineEntry[];
  recent_judgements: string[];
}
```

前端会使用 `recent_judgements` 触发音频、timeline/agents 还原 HUD、`bpm` 控制粒子强度。若 WebSocket 拒绝连接，HUD 会自动切换到内建模拟数据，并持续推进 `current_beat`。

## REST 控制示例

```bash
curl -X POST http://localhost:8000/resume
curl -X POST http://localhost:8000/pause
curl -X POST http://localhost:8000/reset
curl http://localhost:8000/logs
curl http://localhost:8000/history
```

控制按钮会依次调用 `resume`/`pause`/`reset`，并在 UI 下方显示请求状态。

## 其他说明

- 首次播放音效需点击 HUD 界面或按任意键以唤醒 `AudioContext`。
- `ThemeToggle` 状态储存在 `localStorage`，刷新后自动恢复。
- 如果后端尚未启动，HUD 会在 1.2s 后进入模拟模式（并在顶部显示“模拟数据”）。
- 生产/部署时可以 `npm run build` 并将 `dist/` 目录交给静态服务器，客户端仍然通过环境变量连接后端。 

### 自定义背景音乐
如果你想播放自定义的纯音乐（例如你自己的 mp3），把音频文件放到 `client/public/ambient.mp3`，Ambient 按钮会在点击后自动加载并循环播放它。只要后端保持运行，按下 ♫ 即可听到你提供的背景音乐；再点击一次会让音量渐弱并停止播放。

- 你可以用 `client/public/ambient-placeholder.txt` 查看如何替换文件。
