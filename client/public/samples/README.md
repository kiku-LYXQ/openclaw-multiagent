# Instrument Sample Instructions
为了让 Agent 判定音使用真实的乐器，HUD 默认会尝试从 `client/public/samples/` 加载以下文件：
- `violin.mp3`（Echo）
- `piano.mp3`（Northwind）
- `cello.mp3`（Argus）
- `pad.mp3`（默认/备选）

把你要的纯音乐（或片段）放到上述文件名路径即可自动播放，若某个文件缺失，系统会回退到默认三角波合成音。替换完成后重新加载 HUD 页面并点击 ♫ 即可体验。