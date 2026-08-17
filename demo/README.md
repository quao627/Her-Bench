# Her-Bench Task Viewer (Demo)

多 container 的可视化查看器：像视频剪辑软件一样展示一条实况/直播时间轴、
上面挂的任务锚点、每个任务的判分配置，两种运行模式（浏览 / Agent 陪玩），
以及一个「后台」面板把 agent 收到什么、返回什么全部摊开看。

当前有 8 个 container（左上角下拉切换），长短搭配：

| container | 时长 | 类型 |
|---|---|---|
| `hff-p1` / `portal-e01` / `mc-e01` | 2.4h / 2.7h / 2.4h | 游戏盲玩（话多/话中/话少三档） |
| `rust-e01` / `blender-e01` | 3.8h / 5.0h | 直播编程 / 软件首次上手 |
| `blender-e02` | 9.4min | 教学复盘（一周自学 Blender，事后配音） |
| `slendytubbies-e01` | 20min | 恐怖游戏首次盲玩 |
| `stanleyparable-e01` | 46min | 叙事游戏首次盲玩（剧透红线最严） |

后三个是短视频，任务密度明显更高：

| container | 题数 | 密度 | 最小锚点间隔 |
|---|---|---|---|
| `blender-e02` | 9 | 63s/题 | 26s |
| `slendytubbies-e01` | 11 | 110s/题 | 63s |
| `stanleyparable-e01` | 22 | 125s/题 | 55s |
| 五个长 container | 14-18 | 573-1211s/题 | — |

锚点间隔低于 60 秒时要单独确认两道题不冲突：不同主题、答案不重叠、
触发时机不打架（query 会暂停视频等作答，proactive 有 30-100 秒响应窗口）才可以共存。

## 快速开始

```bash
cd demo
python3 server.py                       # → http://localhost:8080
python3 agent_live.py --backend codex   # 真 agent 后端（另开一个终端，需先 codex login）
```

打开 http://localhost:8080（推荐 Chrome）。

## 两种模式

| 模式 | 行为 |
|---|---|
| 浏览 | 自由播放，点时间轴上的 ◆/◇ 标记查看任务与判分配置，agent 不说话 |
| Agent 陪玩 | 严格跟随视频时间轴：连着 gpt-live 时视频不暂停，陪玩边看边说（听得到直播原声）；否则经过锚点暂停，把任务包 POST 给 HTTP 后端（codex/claude）。往回拖进度条，锚点会重新武装再次触发 |

## 后台面板 + 强制查证 + 自主预研

右侧「后台」tab 记录每一次发给 codex 的请求和它的原始返回（含它实际收到的完整
prompt，可展开查看）：

- **HTTP** — Agent 陪玩模式下经过锚点直接调用 `/answer`
- **TOOL** — gpt-live 调用 `lookup_game_info` 走 `/lookup`。`grading.must_cite`
  或 `tool_fit` 为真的 query 型任务，这个调用是**强制**的——用 Realtime API
  的 per-response `tool_choice` 覆盖，不是靠它自己判断「够不够确定」（现场
  对话式模型几乎不会主动承认不确定，所以这条规则是硬性的，不是建议）
- **🔮 PRE（自主预研）** — 头部按钮开关，默认关。开着时 Agent 陪玩模式下
  每 60 秒自己看一眼当前画面（`/research`），自主判断有没有什么值得顺手
  核实的具体事实，自己造问题去查——**不会读到任何预先写好的题目文本**。
  查到的东西存成「研究笔记」，真有人问起来时作为可选参考带给它，它自己判断
  笔记用不用得上，用不上就还是老老实实现查，延迟是真实的。

  这里有个设计上的教训：最早的版本是「播放到任务锚点前 150 秒，直接把
  container.json 里那道题的原文提前发给 codex 查」，锚点触发时缓存命中显示
  ~4ms——但那不是预测，是查看器偷看了未来的题目文本，违反了每个任务
  `context_window_sec` 只能看到锚点之前内容的契约，而且会让延迟类指标
  （`window_hit`/`time_diff`/`latency`）全部失真。现在的版本改成 agent
  只能从自己看到的画面出发，自己决定查什么——实测在 Rust 视频某一帧，
  我们预写的题目是关于 snake_case 警告的，但 agent 自己注意到的是画面里
  完全不同的一条 `assertion failed` 报错信息，说明它真的是在自己观察，
  不是在背题。

面板为空时会给一个「发个测试请求看看效果」按钮，不用真触发任务也能验证链路通。

## 接入后台 agent

查看器对 agent 的全部要求是一个 HTTP 端点（默认 `http://localhost:8787/answer`）：

```
POST { task_id, type, question, anchor_sec, hint_level,
       context_window_sec, frame_jpeg_base64, transcript_excerpt,
       context_frames? }          // 仅 proactive：[{offset_sec, b64}, ...]
  →  { text, citations[], latency_ms }
```

`context_frames` 是**主动型任务专用的时间线**：锚点前 240/180/120/60/20 秒各一张
448px 低分辨率截图，按时间顺序排在当前帧之前。没有它，proactive 任务基本无法判断——
「该不该开口」的依据全是时间性的（卡了多久、刚完成了什么），而单张锚点帧看不出这些：
Human Fall Flat 通关那一帧是小人在云里下坠，跟「掉出地图」几乎无法区分；
Stanley Parable 的 Beat the Game 成就弹窗在它自己的锚点上都还没出现。
实测 5 道主动型任务，只给单帧时 1 道答对，加上时间线后 5 道全对。

前端不用改播放逻辑：HTTP 模式经过锚点时视频本来就已经 pause，可以安全地回溯 seek
抓帧再复位（实测复位精确、不会意外恢复播放，开销 177ms）。codex 侧 `-i` 可重复传多图。

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
浏览器拿不到真 key。模型默认 `gpt-realtime`，用 `OPENAI_REALTIME_MODEL` 覆盖；
语音默认 `cedar`（OpenAI 官方描述 marin 是"专业清晰"、cedar 是"自然对话感"——
默认换成了 cedar，嫌机械可以用 `OPENAI_REALTIME_VOICE` 试试别的：
`alloy/ash/ballad/coral/echo/sage/shimmer/verse/marin/cedar`）。
Realtime API 本身没有语速/语气的直接参数，只能靠 instructions 里的文字描述去引导
（已经在里面加了"像真人反应、别一个调子念稿"的要求），效果有限时换 voice 是更直接的杠杆。
注意：codex CLI 本身没有语音模式（纯文本 coding agent），语音这层只能走 Realtime API。

**关于信息量**：codex 的输出（`/lookup`、`/research`）现在故意不限制长度——具体步骤、数值、
常见坑都会写全，因为这段内容是喂给 gpt-live 当"备好的干货"，由它自己在说话时提炼压缩成
口语，而不是从源头就把信息掐死成两三句话。`/answer`（HTTP 模式的最终回答，直接给浏览器
TTS 朗读）适度放宽到 3-6 句，避免真变成一堵墙。

## 目录

```
demo/
  server.py                    静态服务器（HTTP Range + /api/realtime/token）
  agent_stub.py                罐头回答端点示例
  agent_live.py                真 agent 后端（codex/claude），/answer + /lookup
  app/index.html               整个查看器（单文件，无依赖）
  data/containers/index.json   container 列表
  data/containers/*.json       每个 container：视频、章节、任务、判分、资源索引
  data/resources/              资料快照（wiki/攻略 markdown，agent 的 search() 只命中这里）
  data/thumbs/                 时间轴缩略图（每 5 分钟一张）
  data/tts/                    合成语音条件用的提问音频（OpenAI gpt-4o-mini-tts）
  media/                       浏览器兼容版视频（720p，H.264+AAC remux）
```

## 出题时的硬性要求：锚点必须截帧核对

只读字幕转写来定锚点会出错，而且不是小概率——给三条新视频出题时全量截帧核验，
逮到两类真实错误：

- **理解反了**：字幕 `"there's a pop-up in front of your face, but nothing happens"`
  读起来像「UI 弹窗点了没反应」，截帧一看是反派贴脸的 jump-scare 镜头，
  整道题的 rubric 方向写反了。
- **时间戳漂移**：把 `mm:ss` 心算成 `anchor_sec` 时，小半数锚点跟实际画面差了 25~50 秒，
  画面早就翻篇了。

所以每个候选锚点都要 `ffmpeg -ss <t> -frames:v 1` 截一帧肉眼核对，
`scene` 字段写的必须是「这一帧画面上有什么」，而不是「转写大概讲了什么」。

还有一条容易忽略的：**锚点要落在证据已经出现的那一刻**，不能落在证据即将出现的前一刻。
`context_window_sec` 只能看到锚点之前，`hff-p1-t18`（Water 关通关）原本定在下坠瞬间，
而「过关了」只能靠场景切换看出来——锚点往后挪 14 秒到新场景可见处，这道题才真正可答。

## 已知简化（demo ≠ 正式 harness）

- 主动型任务在响应窗口起点直接触发，正式评测应流式喂视频让 agent 自己决定时机
  （现在靠 `context_frames` 时间线补上了「这段时间发生了什么」，但仍不是真正的流式）；
- 判分是人工勾选 rubric，正式评测由规则脚本 + LLM/VLM judge 完成；
- `transcript_excerpt` 暂为空，跑完 ASR 后接入。
