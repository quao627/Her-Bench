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


## 纯 proactive 模式

跟主界面并行的另一套，入口 `app/proactive.html`（主界面右上角「👁 纯 Proactive」）。

一句话说清差别：**agent 只看得到画面，听不到任何声音，也没有人向它提问。**
什么时候开口、说什么，全由它自己判断。

```
python3 server.py                                  # 同一个服务，多一个 /app/proactive.html
open http://localhost:8080/app/proactive.html
```

### 题是怎么来的

```
python3 mine_proactive.py <container_id> <path/to/en.vtt>
python3 build_proactive_index.py
```

`mine_proactive.py` 分两段：

1. **从转写里提候选**。按分钟切段喂给模型，找「他这会儿确实需要帮助」的时刻：
   自言自语问这是啥、同一个地方反复试、翻半天找不到东西、理解错了规则、被吓到、
   刚做成一件事。每个候选带上让你这么判断的原话（`evidence`，原样抄的）。
   提候选的模型看不到画面，所以它只写 `look_for`：如果这事是真的，画面上应该能找到什么。

2. **截帧核**。在窗口内取八帧（外加两帧铺垫），让模型只看这串画面判断：
   一个听不到声音的人能不能察觉这里不太顺。能察觉才留下，`visible` 和 `scene`
   由这一步写，保证写进题里的是画面上真有的东西。核不过的进 `<id>.dropped.json`。

这一步刷掉的比留下的多，是有意的：只在嘴上抱怨、画面上完全没痕迹的时刻，
对一个只有画面的 agent 来说是无解题。

### 一道题长什么样

```jsonc
{
  "task_id": "slendytubbies-e01-p02",
  "type": "proactive",
  "window_sec": [361, 417],          // 这段时间里开口才算接住
  "kind": "卡住出不去",
  "need": "他不知道自己该往哪走，环境太相似",
  "visible": "这几帧一直在很像的夜晚树林里来回转视角，前后没有出现新地点",
  "evidence": [                       // 出题依据，判分时给判分员看，被测的 agent 看不到
    {"t": 361, "text": "where am I going I don't know everything looks so the same"}
  ],
  "grading": {
    "help_points": ["先选一个稳定策略：沿边走、认单一地标", "..."],
    "must_not_say": ["不要直接说最后一个收集物在哪"]
  }
}
```

### 怎么算分

- 窗口内开口 = 接住，同一个窗口只认第一句，记晚了多少秒
- 所有窗口之外的发言 = 多余，逐次记
- 接住之后再判说得有没有用：对着 `help_points` 逐条勾，另外看剧透、提示分级、是不是在念稿

判分走 `/api/judge`，跟主界面同一条：单独一个模型、单独一次调用。


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

## 后台面板 + 强制查证 + 自检 tick

右侧「后台」tab 记录每一次发给 codex 的请求和它的原始返回（含它实际收到的完整
prompt，可展开查看）：

- **HTTP** — Agent 陪玩模式下经过锚点直接调用 `/answer`
- **TOOL** — gpt-live 调用 `lookup_game_info` 走 `/lookup`（前台，有人等）。
  `grading.must_cite` 或 `tool_fit` 为真的 query 型任务，这个调用是**强制**的——
  用 Realtime API 的 per-response `tool_choice` 覆盖，不是靠它自己判断「够不够确定」
  （现场对话式模型几乎不会主动承认不确定，所以这条规则是硬性的，不是建议）
- **🔍 BG** — 同一个 `/lookup`，带 `background: true`（后台，没人等）。问题是 gpt-live
  在自检 tick 里**自己提的**
- **🔮 PRE** — 备料通道 `/research`（见下），问题是 codex 从最近几帧画面里**自己想的**。
  这两条都读不到任何预先写好的题目文本

面板为空时会给一个「发个测试请求看看效果」按钮，不用真触发任务也能验证链路通。

## 自检 tick：说什么、查什么都由它自己定

Realtime API 只有两种情况会让模型出声：显式发 `response.create`，或者 VAD 听到有人说话。
每 5 秒喂进去的画面帧只进上下文、不带 `response.create`，所以光看画面它永远不会自己开口——
以前能触发它说话的只有主播出声、或者视频走到题目锚点，也就是说开口时机其实是 harness 决定的。

现在只有一个判断入口：**自检 tick**。让它出一个纯文本响应（`output_modalities: ["text"]`，
用户听不到），并用 per-response `tool_choice` 强制它调用 `decide` 工具，在这一轮里同时回答两件事：

```
decide(speak: bool, say: str, lookup: str, need_frame: bool)
```

**结论必须走工具，不能让它写 JSON。**Realtime API 没有 `response_format` 这类结构化输出开关，
在 instructions 里写「只回一行 JSON」没有任何约束力——实测它经常回一句人话，前端只能拿正则去猜，
于是每次自检都解析失败、一直跳过。工具调用的 `arguments` 由 API 按 schema 校验，
是这套 API 里唯一可靠的结构化出口。前端仍保留一个文本兜底分支，但正常不会走到。

- `speak` 为真 → 再发一个语音响应把话说出来；判断「不说」时是真的安静，
  不会冒出一句「我觉得没什么好说的」。第二轮**不把 `say` 递回去**——工具调用和返回本来
  就在对话历史里，它看得见自己刚写的要点；重新塞一遍再叮嘱「别念出来」，等于先制造念稿
  压力再花规则去压。第二轮只发语气和分寸的要求

为什么必须两轮：Realtime 没有「可能说」这种响应，一旦 `response.create` 它就一定出声。
判断和说话放一轮的话，判断为「不用说」时它会把这句**说出来**。代价是主动开口比被问就答
多一次纯文本往返（日志里 `🧠 decide(800ms)` 和 `⏱ 开口延迟` 两个打点就是量这个的），
而自检本身 5 秒一次，这点开销淹没在粒度里。**主播提问那条路不走自检**，VAD 听完直接回应，
一轮到底，不受影响。
- `lookup` 非空字符串 → POST `/lookup {background: true}`，走 bg thread，不阻塞。
  结果以 `[后台资料·时间] Q: … A: …` 塞回它的上下文，**不带 `response.create`**，
  所以不会直接出声——但紧接着触发一次自检，因为它手上刚多了具体信息

触发这次自检的有两处：**每 5 秒（可调）的定时器**，和**后台内容回来的那一刻**。
两处共用 `MIN_CHECK_GAP_MS`（5 秒）这道闸和 `live.checking` 标志，所以同一时刻不会判两次——
多余发言（`over_trigger`）罚得最狠，宁可晚几秒也不能重复开口。刚说完话有 20 秒冷却，
免得它自己接自己的话。

间隔为什么是 5 秒：卡关这种慢变化十秒二十秒都够，吃亏的是庆祝/惊吓/名场面这类情绪反应，
晚八秒的一句「漂亮」等于没说。代价不是钱，是每次自检都要重读一遍不断变长的会话上下文
（画面帧还在每 5 秒往里加）。

需要注意主播问出声这条路**不经过自检**：VAD 听完就直接回应，锚点触发的 query 题和
查证结果回来的那一轮也是显式 `response.create`。自检只管「没人问的时候要不要开口」。

**地板保护。** 全押它的自主性有个已知风险：对话式模型不肯承认自己不确定
（`must_cite` 要用 `tool_choice` 硬覆盖就是因为这个）。所以连续 3 次 tick 一个问题都没提时，
下一次 tick 会追加一句「这次 `lookup` 不许为空」——强制的是「你必须提问」，问题仍由它自己出。
另外后台忙的时候它提的问题会**排一个队**，忙完补上，不会丢——否则备料一占就是二三十秒，
它自己提的问题永远轮不上。

## 备料通道 `/research`（可关）

实测下来光靠自检那条路不够：**前台 agent 几乎从不主动提出要查东西**，后台会长时间一片空白。
所以保留了一条框架定时驱动的备料通道——每 30 秒（可调，设置面板「备料」一栏可整条关掉）
把画面环形 buffer 里的最近十帧交给 codex，让它自己从画面里想一个问题去查。
取帧间隔是 `0/-5/-10/-15/-20/-30/-45/-60/-120/-240` 秒——**近处密、远处稀**：
刚做成一件事、刚摔下去、还是原地转圈，全都发生在最近十几秒里，那一段必须密；
再往前几帧只是用来看这段时间总体有没有挪窝。buffer 本身 5 秒一帧（384px，留 5 分钟），
所以近处能给到 5 秒粒度。实测 10 帧一次约 16 秒，比 3 帧多 4-5 秒，换来的是它真的会说
「这几帧里他已经从叉车旁爬上脚手架、推进到更高的平台，属于明显有进展」这种跨帧判断：

```
POST /research { game, container_id, current_sec, frames:[{offset_sec, b64}, ...] }
  →  { noteworthy, question, text, citations[], latency_ms }
```

它**读不到任何题目文本**，只能从画面出发。实测一次约 11-13 秒，会自己提出诸如
「这台黄色叉车怎么开，旁边的操纵杆分别管什么」这样的问题，并给出带出处的答案。

两条硬边界：

- **备料不触发自检。**查回来的内容只塞进前台的上下文当储备。喂料可以由框架定时做，
  但什么时候说话必须完全由 agent 自己决定，否则测出来的时机是我们的节奏不是它的。
  只有 agent 自己在自检里提的那条查证，回来时才会触发下一次自检。
- **备料不备完整解法。**第一版实测直接备回了一整套通关步骤（搭木板、升货叉、爬脚手架……），
  这东西摆在前台 agent 手上很容易提前说出去。现在 prompt 里明确只写方向性内容，
  也不写当前进度之后的关卡和剧情。

想看它完全自力更生的表现，把这条通道关掉跑一遍即可，这也是最直接的 A/B。

**画面环形 buffer。** live 模式视频在播，没法像 HTTP 模式那样暂停回溯 seek 抓历史帧，
所以每 5 秒喂给 Realtime 的那张帧顺手留一份（最近 4 分钟）。只有它把 `need_frame` 标成
真时，才从 buffer 里取 -180/-60/0 秒三张附给这次查证。这是补它上下文被截断的洞，
不是再造一个眼睛。

试过拿帧差当另一个扳机（画面突变=有进展、长时间不变=卡住），实测不成立：
Human Fall Flat 是自由视角，人站着不动镜头也在晃，卡关 60 秒的帧差 54.9 比真实换关的 45.8 还大。
帧差量的是镜头运动，跟进展无关，已去掉。

tick 打开时（设置面板「自检 tick」，默认开），proactive 题的锚点不再强行催它说话，
退化成评分窗口：只记录它自己有没有在 `response_window_sec` 内开口。

## 主播问话优先：后台立刻让路

主播一开口，后台那条（备料 / 它自己提的查证）必须马上停：

- **信号取最早的**：`input_audio_buffer.speech_started`，比它调 `lookup_game_info` 早十几秒
- **两头一起停**：浏览器 `AbortController` 掐掉请求，同时 `POST /cancel {container_id, kind:"bg"}`
  让后端把 codex 子进程 kill 掉。只掐请求是没用的——进程还在那儿跑，占着 CPU 和那条 codex 会话，
  前台的查证只会更慢
- **被杀的会话作废**：进程是硬杀的，会话文件可能写了一半，所以 thread id 一并清掉，
  下次从干净的会话重开（实测打断后下一次 bg 调用 13.6s 正常返回，带引用）
- 这段时间**不自检、不备料**（`live.userTurn`），直到它把主播的问题答完

实测：`/cancel` 发出到调用返回 **0.8 秒**，被打断的那次返回 `{cancelled: true}`。

## 过程实时回显

codex `--json` 的事件流长这样：

```
thread.started → turn.started → item.completed(agent_message，口头计划)
→ item.started/completed(command_execution，真正在读什么搜什么) → …
→ item.completed(agent_message，最终答案) → turn.completed
```

后端边跑边解析这条流，按 `call_id` 攒进度；前端轮询 `POST /progress {call_id}`，
把「在查：sed -n '1,180p' mechanics.md」这种显示在后台面板的 pending 卡片上。

**只送过程，不送半截答案**：最终答案在 codex 那边是一次成型的（没有 token 级增量），
而且半截事实一旦进了语音引擎的上下文，它可能直接念出去。

## 查证的截止线

codex 自己不会因为「查得太久」停手，所以只能从外面卡。三条路各有各的截止线
（`agent_live.py` 的 `DEADLINES`），超时就返回一句能直接用的话
（「这个没查出来，别再等了，用你已经知道的说」），而不是把异常文本丢给前台：

| 路 | 截止线 | 为什么是这个数 |
|---|---|---|
| `/lookup` 前台 | 40s | 模型已经说了「我查查哈」，再久就是干等 |
| `/lookup` 后台 | 90s | 没人等，但它一直占着 bg thread 和前端的 `bgBusy`，期间发不出第二条 |
| `/answer` | 120s | 判分要看真实 latency，留够时间，超时按降档处理 |

前端另有自己的截止线（前台 50s / 后台 100s，`AbortController`），比后端略宽一点：
后端要是整个挂住，`bgBusy` 会永远是 true，从此一条查证都发不出去。
prompt 里也加了一句「最多两三次检索就收，没查到就直说」——外面卡时间，里面也要求节制。

## codex 会话续接

每次调用如果都是全新的 `codex exec`，五分钟前查过的东西下一次完全用不上，只能从头再搜，
这是「我查查哈」之后又查不到的主要原因。现在用 `codex exec resume <thread_id>` 接着上一轮，
每个 container 维持两条 thread：

| thread | 谁在用 | 为什么分开 |
|---|---|---|
| `fg` | `/answer` + `/lookup`（主播问到了） | 有人在等结果，多次查证之间能接上 |
| `bg` | `/lookup {background: true}`（自检 tick 提的） | 没人等。跟前台分开是因为同一 thread 只能串行 resume，合在一起会让前台排在 20 秒的后台查证后面 |

首次调用带 `--json`，从 `thread.started` 事件取 thread_id 存下来，之后走 resume。
每条 thread 各自一把锁，并发 resume 同一 thread 会让两个 codex 进程写同一份会话文件。

## 接入后台 agent

查看器对 agent 的全部要求是一个 HTTP 端点（默认 `http://localhost:8787/answer`）：

```
POST { task_id, type, question, anchor_sec, hint_level,
       context_window_sec, frame_jpeg_base64, transcript_excerpt,
       context_frames? }          // 仅 proactive：[{offset_sec, b64}, ...]
  →  { text, citations[], latency_ms }
```

`/lookup` 是另一个端点，前台后台共用：

```
POST { query, game, container_id, current_sec,
       background?,               // true = 自检 tick 提的，没人等，走 bg thread
       frames? }                  // 仅 need_frame 时：[{offset_sec, b64}, ...]
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

- **🗣 合成语音（默认）**：主播原声对模型静音，只在任务锚点播放预生成的 TTS 提问
- **📺 原声**：全程听主播直播原声，跟着节奏接话/安慰/庆祝；锚点任务走 data channel。
  这档留作对照——原声会不停触发 VAD，「什么时候开口」就糊在里面测不干净了
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

**关于信息量**：codex 的输出（`/lookup`，前台后台都算）现在故意不限制长度——具体步骤、数值、
常见坑都会写全，因为这段内容是喂给 gpt-live 当"备好的干货"，由它自己在说话时提炼压缩成
口语，而不是从源头就把信息掐死成两三句话。`/answer`（HTTP 模式的最终回答，直接给浏览器
TTS 朗读）适度放宽到 3-6 句，避免真变成一堵墙。

## 目录

```
demo/
  server.py                    静态服务器（HTTP Range + /api/realtime/token）
  agent_stub.py                罐头回答端点示例
  agent_live.py                真 agent 后端（codex/claude），/answer + /lookup（fg/bg 两种）
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

- HTTP 模式（不连 gpt-live）下主动型任务仍在响应窗口起点直接触发，只是拿到了
  `context_frames` 时间线；真正由 agent 自己决定时机（和自己决定查什么）只在 gpt-live
  那条路上生效，因为 HTTP 模式没有常驻连接，做不了定期自检；
- 判分是人工勾选 rubric，正式评测由规则脚本 + LLM/VLM judge 完成；
- `transcript_excerpt` 暂为空，跑完 ASR 后接入。
