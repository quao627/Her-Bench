# Her-Bench Demo

两样东西：一个**查看器**（把时间轴、题、判分配置、以及 agent 每一次调用的输入输出全摊开），
和一个**参考 agent 后端**（Realtime API 说话 + codex CLI 查证）。两者用一个 HTTP 端点衔接，
换任何后端实现都能接。

```bash
cd demo
python3 bench/fetch_videos.py                   # 把视频下到位（首次；--check 只看状态）
python3 server.py                               # dashboard → http://localhost:8080（推荐 Chrome）
python3 agent/agent_live.py                     # agent 后端 → :8787（另开终端，需先 codex login）
```

代码分三块，各管各的：`agent/`（被测的 agent）、`bench/`（数据获取 + 出题 + 判分）、
`server.py` + `app/index.html`（dashboard）。agent 的决策那一半在 `app/agent.js`，
由 dashboard 加载但逻辑独立。谁在哪、哪个函数干什么，见 [`CODEMAP.md`](CODEMAP.md)。

要用语音陪看：把 platform key 写进 `demo/.env`（`OPENAI_API_KEY=sk-...`，和 codex 的
ChatGPT 登录不是一套账号），重启 `server.py`，点右上角 🎙 Live。不连 Live 也能跑完整流程，
只是回答改由浏览器 TTS 念。

## 素材

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

## 两套界面

| 入口 | 给 agent 什么 | 考什么 |
|---|---|---|
| `app/index.html`（主界面） | 画面 + 声音（原声或 TTS 提问） | 问答准不准 + 开口时机 |
| `app/proactive.html` | **只有画面**，没有声音也没人提问 | 纯粹的开口时机 |

主界面两种模式：

| 模式 | 行为 |
|---|---|
| 浏览 | 自由播放，点时间轴上的 ◆/◇ 看题和判分配置，agent 不说话 |
| Agent 陪玩 | 跟随时间轴：连着 Live 时视频不暂停，agent 边看边说；否则经过锚点暂停，把任务包 POST 给后端。往回拖进度条，锚点会重新武装 |

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
python3 bench/mine_proactive.py <container_id> <path/to/en.vtt>
python3 bench/build_proactive_index.py
```

`bench/mine_proactive.py` 分两段：

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

## 运行时：一个决策点，三条查证通道

陪看要同时做两件互相冲突的事：**实时出声**（几百毫秒内接得上话）和**查证**
（翻资料、搜网，一次 10–40 秒）。一个模型两头占不住，所以拆成两个引擎：

- **Realtime API** 常驻浏览器这端：听声音、每 5 秒看一帧画面、负责说话。全程唯一连续跟着直播的一端。
- **codex CLI**（`agent/agent_live.py`）在本地起 HTTP 服务：能读资料能搜网，但听不见、不常驻。**它只是工具，不做任何判断。**

### 自检 tick

Realtime 不会自发说话：往对话里塞 item 不触发生成，只有显式 `response.create`
或 VAD 听到人说完话才会。所以需要一个定期的判断入口——**自检**：每 5 秒（可调）
出一个纯文本响应（用户听不到），强制调用 `decide` 工具交回结论：

```
decide(speak: bool, say: str, lookup: str, need_frame: bool)
```

- `speak` 为真 → 再发一次语音响应把话说出来。判断「不说」时是真的安静，
  不会冒出一句「我觉得没什么好说的」——那一轮的 modality 就是纯文本，它想出声也出不了
- `lookup` 非空 → 走后台查证，结果塞回上下文当储备

触发自检的有两处：5 秒的定时器，和后台内容回来的那一刻。两处共用 5 秒最小间隔和
一个「上一次还没回来就不发」的标志，所以同一时刻不会判两次——多余发言罚得最狠，
宁可晚几秒也不能重复开口。刚说完话有 20 秒冷却。

> **必须用 `tool_choice: 'required'`。** 实测点名式 `{type:'function', name:'decide'}`
> 会被 API 收下（形状写错还会报错），但**并不强制执行**，模型照样返回一段文字。
> 那样自检就全靠文本兜底在撑，它一旦回一句人话，`speak` 和 `lookup` 一起丢。
> per-response 只传该调的那一个工具时，`'required'` 等价于点名而且真的生效。

### 三条查证通道

后端只有一件事要做：把问题连同**按进度挑出的资料原文**、提示分级、剧透红线拼成
prompt 交给 codex，拿回一段文字加一行 `SOURCES:`。三条路的区别只在问题是谁提的：

| 通道 | 问题从哪来 | 谁在等 | codex 会话 |
|---|---|---|---|
| `/answer` | 题目文件（不连 Live 时的 HTTP 通路） | 浏览器（要念出来，压到 3–6 句） | `fg` |
| `/lookup` | 主播问出声，Realtime 自己调工具 | 有人等 | `fg` |
| `/lookup {background}` | **它自己**在自检里提的 | 没人等 | `bg` |
| `/research` | **没有人提问**，codex 从最近十帧画面里自己想一个 | 没人等 | `bg` |

`/research` 是「备料」通道（设置面板可整条关掉）：每 30 秒把画面环形 buffer 里的
最近十帧交给 codex，让它自己找值得核实的东西。为什么需要它——实测前台 agent
**几乎从不主动提出要查东西**（对话式模型不肯承认自己不确定，跟 `must_cite` 要用
`tool_choice` 硬覆盖是同一个毛病），光靠自检那条路后台会长时间一片空白。

两条硬边界：

- **备料不触发自检。**查回来的只塞进上下文当储备。喂料可以由框架定时做，
  但什么时候说话必须完全由 agent 自己决定，否则测出来的时机是我们的节奏不是它的。
  只有它自己提的那条查证，回来时才触发下一次自检。
- **备料不备完整解法。**第一版实测直接备回了一整套通关步骤，这东西摆在前台 agent
  手上很容易提前说出去。现在只写方向性内容，也不写当前进度之后的关卡和剧情。

### 主播问话优先

主播一开口（`input_audio_buffer.speech_started` 是最早的信号，比它调工具早十几秒），
后台那条立刻让路：浏览器 abort 掉请求，同时 `POST /cancel` 让后端 **kill 掉 codex
子进程**——只掐请求没用，进程还在占着 CPU 和那条会话。被杀的会话一并作废，
下次从干净会话重开。这段时间不自检、不备料。实测打断到返回 0.8 秒。

### 截止线

codex 自己不会因为「查得太久」停手，只能从外面卡。超时返回一句能直接用的话
（「这个没查出来，别再等了，用你已经知道的说」），而不是把异常丢给前台：

| 路 | 截止线 | 为什么 |
|---|---|---|
| `/lookup` 前台 | 40s | 模型已经说了「我查查哈」，再久就是干等 |
| `/lookup` 后台 · `/research` | 90s | 没人等，但它占着 bg 会话和前端的「正在查」标志 |
| `/answer` | 120s | 判分要看真实 latency，留够时间 |

前端另有稍宽的截止线（前台 50s / 后台 100s，`AbortController`）：后端要是整个挂住，
「正在查」的标志会永远落不下来，从此一条查证都发不出去。

### 会话续接与过程回显

每次都开新 `codex exec` 的话，五分钟前查过的下一次用不上，只能从头再搜。改成
`codex exec resume <thread_id>` 接着上一轮，每个 container 两条会话（`fg`/`bg`）——
同一条会话只能串行 resume，合在一起会让有人等的查证排在后台后面。

codex `--json` 的事件流里能看到它在读什么、搜什么，后端按 `call_id` 攒着，前端轮询
`/progress` 显示在后台面板的 pending 卡片上。**只送过程不送半截答案**：最终答案在
codex 那边本来就是一次成型的，而半截事实一旦进了语音引擎的上下文，它可能直接念出去。

## 端点参考

agent 后端（默认 `http://localhost:8787`）：

```
POST /answer    { task_id, type, question, anchor_sec, hint_level, context_window_sec,
                  container_id, frame_jpeg_base64, transcript_excerpt,
                  context_frames?,      // 仅 proactive：[{offset_sec, b64}, ...]
                  recent_research?, call_id? }
             →  { text, citations[], latency_ms, debug_prompt }

POST /lookup    { query, game, container_id, current_sec,
                  background?,          // true = 自检提的，没人等，走 bg 会话
                  frames?, call_id? }   // frames 仅在它要求看画面时带
             →  { text, citations[], latency_ms, timeout?, cancelled? }

POST /research  { game, container_id, current_sec, frames, call_id? }
             →  { noteworthy, question, text, citations[], latency_ms }

POST /cancel    { container_id, kind }        → { cancelled }
POST /progress  { call_id }                   → { lines[], done }
```

查看器服务（`server.py`，默认 `:8080`）：

```
POST /api/realtime/token  { container_id }  → { value, model }   // ephemeral key，浏览器拿不到真 key
POST /api/judge           { task, run, frame_jpeg_base64? }      // 独立判分，见下
GET  /...                 静态文件（带 HTTP Range，视频拖动需要）
```

`context_frames` 是**主动型任务专用的时间线**：锚点前 240/180/120/60/20 秒各一张
448px 缩图。没有它 proactive 基本无法判断——「该不该开口」的依据全是时间性的，
而单张锚点帧看不出来：Human Fall Flat 通关那一帧是小人在云里下坠，跟「掉出地图」
几乎无法区分。实测 5 道主动型题，单帧只对 1 道，加时间线后 5 道全对。

## 设置项与默认值

| 项 | 默认 | 说明 |
|---|---|---|
| 音频档位 | 🗣 合成语音 | 主播原声对模型静音，只在锚点播放预生成的 TTS 提问。📺 原声那档留作对照——原声不停触发 VAD，开口时机就糊在里面测不干净了 |
| 自检 tick | 5s | 情绪类时刻（庆祝/惊吓）晚 8 秒等于没说，所以粒度定在 5 秒。代价是每次自检都要重读一遍不断变长的上下文 |
| 备料 | 开 · 30s | 整条关掉即可跑「它完全自力更生」的对照 |
| 画面帧 | 5s | 喂给 Realtime 的图像流；同一张顺手存进环形 buffer（384px，留 5 分钟） |
| 取帧间隔 | 备料 10 帧 / 查证 6 帧 | `0/-5/-10/-15/-20/-30/-45/-60/-120/-240` 秒，近处密远处稀。隔一分钟才一帧看不出动态——刚做成一件事、刚摔下去、还是原地打转，都发生在最近十几秒里 |
| 语音 | `cedar` | `OPENAI_REALTIME_VOICE` 可换（`alloy/ash/ballad/coral/echo/sage/shimmer/verse/marin/cedar`）；模型用 `OPENAI_REALTIME_MODEL` 覆盖 |

Realtime API 没有语速/语气参数，只能靠 instructions 里的文字引导；效果不满意时
换 voice 比改措辞更直接。codex 本身没有语音模式（纯文本 coding agent），
语音这层只能走 Realtime。

## 出题与判分工具链

```bash
python3 bench/fetch_videos.py [--check] [container_id ...]     # 按清单下载视频到 media/
python3 bench/mine_proactive.py <container_id> <en.vtt>        # 从转写+画面挖 proactive 题
python3 bench/build_proactive_index.py                         # 刷新 proactive 界面的索引
python3 bench/gen_tts.py                                       # 为 query 题生成提问语音
python3 bench/vtt.py <file.vtt> [n]                            # 把 YouTube 自动字幕转成 {t,text}
```

判分（`bench/judge.py`）是**跟陪看 agent 完全分开的一次 LLM 调用**：不碰 codex、不碰
Realtime 会话、不共享任何上下文，只拿「题面 + agent 到底说了什么」去问一个纯文本
模型。让同一条会话既作答又给自己打分等于自己验自己。前端一道题跑完自动打一次分，
走 `POST /api/judge`；模型用 `HERBENCH_JUDGE_MODEL` 覆盖。

### 出题的硬性要求：锚点必须截帧核对

只读转写定锚点会出错，而且不是小概率。给三条新视频出题时全量截帧核验，逮到两类真实错误：

- **理解反了**：字幕 `"there's a pop-up in front of your face, but nothing happens"`
  读起来像「UI 弹窗点了没反应」，截帧一看是反派贴脸的 jump-scare，整道题方向写反了。
- **时间戳漂移**：把 `mm:ss` 心算成 `anchor_sec` 时，小半数锚点跟实际画面差了 25–50 秒。

所以每个候选锚点都要 `ffmpeg -ss <t> -frames:v 1` 截帧肉眼核对，`scene` 写的必须是
「这一帧画面上有什么」。还有一条容易忽略：**锚点要落在证据已经出现的那一刻**。
`hff-p1-t18`（Water 关通关）原本定在下坠瞬间，而「过关了」只能靠场景切换看出来——
往后挪 14 秒到新场景可见处，这道题才真正可答。

## 目录

```
demo/
  CODEMAP.md                谁在哪、哪个函数干什么

  agent/                    ① 被测的 agent
    agent_live.py             后端：/answer /lookup /research /cancel /progress
                              （决策那一半在 app/agent.js，见 CODEMAP）

  bench/                    ② 数据获取 + 出题 + 判分
    fetch_videos.py           按 container 清单下载视频
    vtt.py                    VTT 转写解析
    mine_proactive.py         从转写+画面挖 proactive 题
    build_proactive_index.py  生成 proactive 界面的索引
    gen_tts.py                合成语音条件用的提问音频
    judge.py                  独立判分（单独一个模型、单独一次调用）

  server.py                 ③ dashboard 入口：静态文件 + /api/realtime/token + /api/judge
  app/agent.js                agent 的决策那一半：自检 / 说不说 / 查什么（只有声明，无副作用）
  app/index.html              主界面：时间轴、面板、判分，以及把 agent 接线拉起来
  app/proactive.html          纯 proactive 界面

  data/containers/*.json    每个 container：视频、章节、题、判分、资料索引
  data/proactive/*.json     proactive 题库（含被复核刷掉的 .dropped.json）
  data/resources/           资料快照（wiki/攻略 markdown）
  data/thumbs/              时间轴缩略图（每 5 分钟一张）
  data/tts/                 合成语音条件用的提问音频
  media/                    浏览器兼容版视频（720p remux，不入库）
```

## 踩过的坑

留在这儿是因为它们都不是拍脑袋能避开的，得测了才知道：

- **`tool_choice` 点名式不生效**（见上）。受影响的不只是自检，`must_cite` 那条
  「这类题硬性要求先查证」的规则也一直在空转。
- **帧差不能当开口信号**。试过用画面突变=有进展、长时间不变=卡住，实测不成立：
  Human Fall Flat 是自由视角，人站着不动镜头也在晃，卡关 60 秒的帧差 54.9
  比真实换关的 45.8 还大。帧差量的是镜头运动，跟进展无关。
- **不能提前把题目发给 codex 预热**。早期版本在锚点前 150 秒把题目原文发过去查，
  锚点触发时缓存命中 ~4ms——但那不是预测，是查看器偷看了未来的题目文本，
  违反 `context_window_sec` 契约，还会让延迟类指标全部失真。
- **判断和说话分两轮，第二轮没有否决权**。`speak=true` 一写下，那一轮必然出声。
  A/B 实测（每边 20 轮）：两轮版在平淡场景误开口 3/10，一轮版（用一个「闭嘴工具」
  让它自己选）0/10，且到出声快 3.3 倍（448ms vs 1473ms），70 次沉默判断 0 次漏音。
  数据支持换成一轮，但沉默会从结构保证变成行为自觉，尚未切换。

## 已知简化（demo ≠ 正式 harness）

- HTTP 模式（不连 Live）下主动型任务仍在响应窗口起点直接触发，只是拿到了
  `context_frames`；真正由 agent 自己决定时机和查什么，只在 Live 那条路上生效——
  HTTP 模式没有常驻连接，做不了定期自检。
- `transcript_excerpt` 暂为空，跑完 ASR 后接入。
- 判分已接自动 judge，但规则类指标（`window_hit` / `time_diff` / `over_trigger`）
  还没做成离线脚本，现在只在界面里记。
