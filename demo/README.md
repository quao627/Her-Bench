# Her-Bench Task Viewer (Demo)

单个 container 的可视化查看器：像视频剪辑软件一样展示一条游戏实况时间轴、
上面挂的任务锚点、每个任务的判分配置，以及三种运行模式（浏览 / 人玩 / Agent）。

## 快速开始

```bash
cd demo
python3 server.py            # → http://localhost:8080
python3 agent_stub.py        # 可选：agent 模式的演示端点（另开一个终端）
```

打开 http://localhost:8080（推荐 Chrome，语音输入依赖 Web Speech API）。

## 三种模式

| 模式 | 行为 |
|---|---|
| 浏览 | 自由播放，点时间轴上的 ◆/◇ 标记查看任务与判分配置，agent 不说话 |
| Agent 陪玩 | 严格跟随视频时间轴：连着 gpt-live 时视频不暂停，陪玩边看边说（听得到直播原声）；否则经过锚点暂停，把任务包 POST 给 HTTP 后端（codex/claude）。往回拖进度条，锚点会重新武装再次触发 |

## 接入后台 agent

查看器对 agent 的全部要求是一个 HTTP 端点（默认 `http://localhost:8787/answer`）：

```
POST { task_id, type, question, anchor_sec, hint_level,
       context_window_sec, frame_jpeg_base64, transcript_excerpt }
  →  { text, citations[], latency_ms }
```

三档实现，按需选：

```bash
python3 agent_stub.py                     # 罐头回答，秒回，演示协议用
python3 agent_live.py                     # 真 agent：claude CLI 无头模式（已验证，~20s/题）
python3 agent_live.py --backend codex     # 真 agent：codex CLI（需先 codex login）
```

`agent_live.py` 把帧截图存成文件，连同问题、提示分级规则、resources/ 目录
一起交给 CLI agent——agent 自己 Read 图片和攻略资料后作答，并汇报引用来源。
HTTP agent 的语音播报由查看器端 TTS 完成。

## gpt-live（OpenAI Realtime 语音陪看）

查看器内置了 Realtime API 的 WebRTC 客户端（头部 🎙 Live 按钮）：

```bash
export OPENAI_API_KEY=sk-...   # platform key（platform.openai.com，按用量计费，
                               # 和 codex 的 ChatGPT 登录不是一套账号）
python3 server.py              # 重启后点 🎙 Live
```

连上后自动进入「Agent 陪玩」。音频输入分两个评测条件（头部下拉切换）：

- **📺 原声**：全程听主播直播原声，跟着节奏接话/安慰/庆祝；锚点任务走 data channel
- **🗣 合成语音**：主播原声对模型静音，只在任务锚点播放预生成的 TTS 提问
  （`data/tts/*.m4a`，OpenAI gpt-4o-mini-tts 合成，重新生成见 git log 里的脚本），
  模型靠语音活动检测听完问题自动作答——干净、可控、时间对齐的音频条件

画面通道独立：播放中每 5 秒喂一帧（🖼 可关）。回答字幕在画面左下角，可点「判分」入库。
token 由 server.py 的 `/api/realtime/token` 用 master key 换取 ephemeral key，
浏览器拿不到真 key。模型默认 `gpt-realtime`，用 `OPENAI_REALTIME_MODEL` 覆盖。
注意：codex CLI 本身没有语音模式（纯文本 coding agent），语音这层只能走 Realtime API。

## 目录

```
demo/
  server.py          静态服务器（带 HTTP Range，视频拖进度条必需）
  agent_stub.py      agent 端点示例
  app/index.html     整个查看器（单文件，无依赖）
  data/container.json  container 定义：视频、章节、任务、判分、资源索引
  data/resources/    资料快照（wiki/攻略 markdown，评测时 search() 只命中这里）
  data/thumbs/       时间轴缩略图（每 5 分钟一张）
  media/             浏览器兼容版视频（AAC 音轨 remux）
```

## 已知简化（demo ≠ 正式 harness）

- 主动型任务在响应窗口起点直接触发，正式评测应流式喂视频让 agent 自己决定时机；
- 判分是人工勾选 rubric，正式评测由规则脚本 + LLM/VLM judge 完成；
- `transcript_excerpt` 暂为空，跑完 ASR 后接入。
