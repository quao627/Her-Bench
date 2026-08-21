# Her-Bench Demo

**中文** · [English](README.en.md)

这里有两样东西：一个 dashboard，用来展开时间轴、题、判分配置和 agent 每一次调用的
输入输出；一个参考 agent 后端，由 Realtime API 负责说话、codex CLI 负责查证。两者之间
只有一个 HTTP 端点，换成别的后端实现也能接。

```bash
cd demo
python3 bench/fetch_videos.py                   # 把视频下到位（首次；--check 只看状态）
python3 server.py                               # dashboard → http://localhost:8080（推荐 Chrome）
python3 agent/agent_live.py                     # agent 后端 → :8787（另开终端，需先 codex login）
```

代码分成三块：`agent/` 是被测的 agent，`bench/` 负责数据获取、出题和判分，`server.py`
加 `app/index.html` 是 dashboard。agent 在浏览器这端的决策逻辑单独放在 `app/agent.js`，
由 dashboard 加载，但逻辑是独立的。哪个文件负责什么、关键函数在哪，见
[`CODEMAP.md`](CODEMAP.md)。

要用语音陪看，把 platform key 写进 `demo/.env`（`OPENAI_API_KEY=sk-...`，注意它和 codex
用的 ChatGPT 登录不是一套账号），重启 `server.py`，然后点右上角的 🎙 Live。不连 Live
也能跑完整流程，区别只是回答改由浏览器 TTS 念出来。

## 素材

当前有 8 个 container，从左上角下拉切换，长短搭配：

| container | 时长 | 类型 |
|---|---|---|
| `hff-p1` / `portal-e01` / `mc-e01` | 2.4h / 2.7h / 2.4h | 游戏盲玩（话多、话中、话少三档） |
| `rust-e01` / `blender-e01` | 3.8h / 5.0h | 直播编程 / 软件首次上手 |
| `blender-e02` | 9.4min | 教学复盘（一周自学 Blender，事后配音） |
| `slendytubbies-e01` | 20min | 恐怖游戏首次盲玩 |
| `stanleyparable-e01` | 46min | 叙事游戏首次盲玩（剧透红线最严） |

后三个是短视频，题的密度明显更高：

| container | 题数 | 密度 | 最小锚点间隔 |
|---|---|---|---|
| `blender-e02` | 9 | 63s/题 | 26s |
| `slendytubbies-e01` | 11 | 110s/题 | 63s |
| `stanleyparable-e01` | 22 | 125s/题 | 55s |
| 五个长 container | 14-18 | 573-1211s/题 | — |

锚点间隔低于 60 秒时要单独确认两道题不会互相干扰：主题不同、答案不重叠、触发时机不打架
才可以共存。触发时机这一条是因为 query 题会暂停视频等作答，而 proactive 题有 30 到 100 秒
的响应窗口。


## 一条命令跑完，不用开浏览器

两套题各有一个离线跑法，都不需要按视频时长等。

```bash
python3 agent/agent_live.py                     # 问答题要它在跑
python3 bench/run_query.py portal-e01           # 问答题
python3 bench/run_proactive.py slendytubbies-e01  # 纯 proactive
```

**问答题**根本不需要实时：每道题就是「在锚点这一刻主播问了这么一句，你怎么答」，
跟视频播到哪儿没关系。截锚点那一帧，连题包一起发给 agent 后端，拿回答案送去判分。
实测 portal-e01 的 11 道题 1.4 分钟跑完，瓶颈是 codex 每道 7 到 8 秒。

**纯 proactive** 没有音频，也不必按真实时间走：一次 ffmpeg 抽完帧，
再一格一格问「现在要不要开口」，几段并行。实测 20 分钟的视频 50 秒跑完，快 31 倍。

### harness 跟 agent 是分开的

评的是一套**有时间属性**的系统：前台一路看着，后台在背后跑 codex。所以 harness
只做三件事——按视频时间推画面、到锚点递问题、记下 agent 说了什么再判分。

**它不知道 agent 有没有后台、备不备料、备多密。** 换一个只有前台的 agent，或者
一个每秒备一次的，`bench/harness.py` 一行都不用改。

```bash
python3 bench/run_live.py portal-e01 --agent reactive   # 只有前台，被问才现查
python3 bench/run_live.py portal-e01 --agent prepared   # 前台 + 后台备料
```

唯一被强制的是时间。agent 花掉的墙钟时间折算成视频时间：视频 10:00 发起、真跑了
18 秒的活，产出要到 10:18 才存在。后台通道由 harness 提供，一次只能跑一个活，
主播开口时正在跑的那条按打断规则作废。想得慢的 agent 在真实场景里就是会错过时机，
这条绕不过去。

写一个新 agent 就是实现三个方法（见 `bench/agents/__init__.py`）：

```python
on_frame(ctx, sec, frame)        # 每帧一次；返回字符串 = 此刻主动开口
on_question(ctx, sec, q, task)   # 主播开口了
# ctx.bg.submit(fn) 往后台扔活，ctx.bg.ready() 取已经回来的
```

三个 agent 是一条消融线，每一档只多一样东西：

| | reactive | watching | prepared |
|---|---|---|---|
| 看画面 | ✗ | ✓ 回看条 | ✓ 回看条 |
| 后台备料 | ✗ | ✗ | ✓ |
| | | | |
| rubric | 9/9 | 7/9 | 8/9 |
| 延迟中位 | 6.1s | 2.8s | **2.6s** |
| 不用查就答上 | 0/3 | 3/3 | 2/3 |
| 后台跑了几个活 | 0 | 0 | 10 |
| 跑完 | 0.8 分钟 | 0.6 分钟 | 2.9 分钟 |

portal-e01 前 22 分钟，同一个 harness、同一批题、同一套判分，只换传进去的对象。

**延迟那一半的功劳基本全在「看画面」上**：reactive → watching 就从 6.1s 掉到 2.8s，
再加后台只多省 0.2s。因为看过就敢直接答，不用等 codex。

**但看过不等于答得对**：watching 掉到 7/9——它三道全都直接答了，其中两道答浅了。
prepared 回到 8/9，因为有笔记撑着的时候它答得实，没笔记的那道（t02）它老老实实
去查了。

所以后台真正买到的不是速度，是**在该查的时候还知道要查**。这个结论是测出来的，
不是 harness 替谁定的。

## 两套界面

| 入口 | 给 agent 什么 | 考什么 |
|---|---|---|
| `app/index.html`（主界面） | 画面加声音（原声或 TTS 提问） | 问答准不准，以及开口时机 |
| `app/proactive.html` | 只有画面，没有声音也没有人提问 | 开口时机 |

主界面有两种模式：

| 模式 | 行为 |
|---|---|
| 浏览 | 自由播放，点时间轴上的 ◆/◇ 看题和判分配置，agent 不说话 |
| Agent 陪玩 | 跟随时间轴。连着 Live 时视频不暂停，agent 边看边说；不连 Live 时经过锚点会暂停，把任务包 POST 给后端。往回拖进度条，锚点会重新武装 |

## 纯 proactive 模式

跟主界面并行的另一套，入口是 `app/proactive.html`，也可以从主界面右上角的
「👁 纯 Proactive」进去。

差别在于 agent 只看得到画面，听不到任何声音，也没有人向它提问。什么时候开口、说什么，
全部由它自己判断。

```
python3 server.py                                  # 同一个服务，多一个 /app/proactive.html
open http://localhost:8080/app/proactive.html
```

### 题是怎么来的

```
python3 bench/mine_proactive.py <container_id> <path/to/en.vtt>
python3 bench/build_proactive_index.py
```

`bench/mine_proactive.py` 分两段跑：

1. 从转写里提候选。按分钟切段喂给模型，找他这会儿确实需要帮助的时刻：自言自语问这是啥、
   同一个地方反复试、翻半天找不到东西、理解错了规则、被吓到、刚做成一件事。每个候选都带上
   让人这么判断的原话，也就是 `evidence`，原样抄下来。提候选的模型看不到画面，所以它只写
   `look_for`：如果这件事是真的，画面上应该能找到什么。

2. 截帧核对。在窗口内取八帧，另外加两帧铺垫，让模型只看这串画面判断一个听不到声音的人
   能不能察觉这里不太顺。能察觉才留下，`visible` 和 `scene` 由这一步写，保证写进题里的是
   画面上真有的东西。核不过的进 `<id>.dropped.json`。

这一步刷掉的比留下的多，是有意的。只在嘴上抱怨、画面上完全没痕迹的时刻，对一个只有画面的
agent 来说是无解题。

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

- 窗口内开口算接住，同一个窗口只认第一句，同时记下晚了多少秒
- 窗口之外的发言算多余，逐次记
- 接住之后再看说得有没有用：对着 `help_points` 逐条勾，另外检查剧透、提示分级，以及是不是在念稿

判分走 `/api/judge`，和主界面用的是同一条路：单独一个模型、单独一次调用。


### 一条命令跑完，不用开浏览器

```bash
python3 bench/run_proactive.py slendytubbies-e01
```

浏览器那条路是实时的：视频放多久就得等多久。但纯 proactive 这一套没有音频，
agent 收到的只是每隔几秒一张画面，没有任何东西必须按真实时间走。所以离线跑是这样：
一次 ffmpeg 把帧全抽出来，再按视频时间一格一格问「现在要不要开口」，
几段并行。快多少取决于 API，跟视频多长没关系。

实测 20 分钟的 slendytubbies 跑完用 50 秒，比实时快 31 倍。

| 参数 | 默认 | 说明 |
|---|---|---|
| `--tick N` | 8 | 多少秒问一次。越小越细，也越贵 |
| `--workers N` | 4 | 并行几段。段之间各记各的说过什么，换来能并行 |
| `--limit N` | 0 | 只跑前 N 秒，先看看效果 |
| `--verbose` | | 每一格都打印它的判断，用来看它为什么不说 |
| `--no-judge` | | 只跑不判，省钱 |

跑完在 `data/runs/` 落一份 JSON：它在哪些时刻开了口、命中了哪些窗口、
漏了哪些、多说了几次，以及每次命中的判分结果。

## 运行时：一个决策点，三条查证通道

陪看要同时做两件互相冲突的事。一件是实时出声，几百毫秒内要接得上话；另一件是查证，
翻资料、搜网，一次要 10 到 40 秒。一个模型两头都占不住，所以拆成两个引擎：

- Realtime API 常驻在浏览器这端，听声音、每 5 秒看一帧画面、负责说话，是全程唯一连续
  跟着直播的一端。
- codex CLI 在本地起 HTTP 服务（`agent/agent_live.py`），能读资料能搜网，但听不见也不常驻。
  它只执行被交给它的问题，不做任何判断。

### 自检 tick

Realtime 不会自发说话。往对话里塞 item 不会触发生成，只有显式发 `response.create`，
或者 VAD 判定有人把话说完了才会。所以需要一个定期的判断入口，也就是自检：每 5 秒
（可调）出一个纯文本响应，用户听不到，并强制它调用 `decide` 工具交回结论。

```
decide(speak: bool, say: str, lookup: str, need_frame: bool)
```

`speak` 为真时再发一次语音响应把话说出来。判断不说的时候是真的安静，不会冒出一句
「我觉得没什么好说的」，因为那一轮的 modality 就是纯文本，它想出声也出不了。
`lookup` 非空时走后台查证，结果塞回上下文当储备。

触发自检的有两处：5 秒的定时器，以及后台内容回来的那一刻。两处共用 5 秒的最小间隔和
一个「上一次还没回来就不发」的标志，所以同一时刻不会判两次。多余发言在评分里罚得最狠，
宁可晚几秒也不能重复开口。刚说完话之后有 20 秒冷却。

`tool_choice` 必须写 `'required'`。实测点名式的 `{type:'function', name:'decide'}` 会被 API
收下（写错形状还会报错），但并不强制执行，模型照样返回一段文字。那样自检就完全靠文本
兜底在撑，它一旦回一句人话，`speak` 和 `lookup` 就一起丢了。per-response 只传该调的那一个
工具时，`'required'` 的效果等价于点名，而且真的生效。

### 三条查证通道

后端要做的事只有一件：把问题连同按进度挑出的资料原文、提示分级和剧透红线拼成 prompt
交给 codex，拿回一段文字和一行 `SOURCES:`。三条路的区别只在问题是谁提的。

| 通道 | 问题从哪来 | 谁在等 | codex 会话 |
|---|---|---|---|
| `/answer` | 题目文件，用在不连 Live 的通路上 | 浏览器要念出来，所以压到 3 到 6 句 | `fg` |
| `/lookup` | 主播问出声，Realtime 自己调工具 | 有人等 | `fg` |
| `/lookup {background}` | 它自己在自检里提的 | 没人等 | `bg` |
| `/research` | 没有人提问，codex 从最近十帧画面里自己想一个 | 没人等 | `bg` |

`/research` 是备料通道，可以在设置面板里整条关掉。它每 30 秒把画面环形 buffer 里的最近
十帧交给 codex，让它自己找值得核实的东西。之所以需要这条路，是因为实测下来前台 agent
几乎从不主动提出要查东西，跟 `must_cite` 要用 `tool_choice` 硬覆盖是同一个毛病：对话式
模型不肯承认自己不确定。只靠自检那条路，后台会长时间一片空白。

备料有两条边界：

- 备料不触发自检。查回来的内容只塞进上下文当储备。喂料可以由框架定时做，但什么时候说话
  必须完全由 agent 自己决定，否则测出来的时机是我们的节奏，不是它的。只有它自己提的那条
  查证，回来时才会触发下一次自检。
- 备料不备完整解法。第一版实测直接备回了一整套通关步骤，这种东西摆在前台 agent 手上很容易
  提前说出去。现在只写方向性内容，也不写当前进度之后的关卡和剧情。

### 主播问话优先

主播一开口，后台正在跑的那条就要停下。最早能拿到的信号是
`input_audio_buffer.speech_started`，比它调工具早十几秒。浏览器 abort 掉请求，同时
`POST /cancel` 让后端结束 codex 子进程，因为只掐请求没有用，进程还在占着 CPU 和那条会话。
被结束的会话一并作废，下次从干净会话重开。这段时间不自检也不备料。实测从发出打断到调用
返回是 0.8 秒。

### 截止线

codex 不会因为查得太久自己停手，只能从外面卡时间。超时后返回一句 agent 能直接用的话
（「这个没查出来，别再等了，用你已经知道的说」），而不是把异常丢给前台。

| 路 | 截止线 | 为什么是这个数 |
|---|---|---|
| `/lookup` 前台 | 40s | 模型已经说了「我查查哈」，再久就是让人干等 |
| `/lookup` 后台 · `/research` | 90s | 没人等，但它占着 bg 会话和前端的「正在查」标志 |
| `/answer` | 120s | 判分要看真实 latency，留够时间 |

前端另有一条稍宽的截止线（前台 50s、后台 100s，用 `AbortController`）。后端要是整个挂住，
「正在查」的标志会一直落不下来，之后一条查证都发不出去。

### 会话续接与过程回显

每次都开新的 `codex exec`，五分钟前查过的东西下一次就用不上，只能从头再搜。改成
`codex exec resume <thread_id>` 接着上一轮，每个 container 维持两条会话（`fg` 和 `bg`）。
分开是因为同一条会话只能串行 resume，合在一起会让有人等的查证排在后台查证后面。

codex 的 `--json` 事件流里能看到它在读什么、搜什么。后端按 `call_id` 攒着，前端轮询
`/progress`，显示在后台面板的 pending 卡片上。这里只送过程，不送半截答案：最终答案在
codex 那边本来就是一次成型的，而半截事实一旦进了语音引擎的上下文，它可能直接念出去。

## 端点参考

agent 后端，默认 `http://localhost:8787`：

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

dashboard 服务（`server.py`，默认 `:8080`）：

```
POST /api/realtime/token  { container_id }  → { value, model }   // ephemeral key，浏览器拿不到真 key
POST /api/judge           { task, run, frame_jpeg_base64? }      // 独立判分，见下
GET  /...                 静态文件（带 HTTP Range，视频拖动需要）
```

`context_frames` 只给主动型任务用，是锚点前 240、180、120、60、20 秒各一张 448px 缩图组成的
时间线。没有它 proactive 基本判断不了，因为该不该开口的依据全是时间性的，单张锚点帧看不出来：
Human Fall Flat 通关那一帧是小人在云里下坠，和掉出地图几乎无法区分。实测 5 道主动型题，
只给单帧时对 1 道，加上时间线后 5 道全对。

## 设置项与默认值

| 项 | 默认 | 说明 |
|---|---|---|
| 音频档位 | 🗣 合成语音 | 主播原声对模型静音，只在锚点播放预生成的 TTS 提问。📺 原声那档留作对照，因为原声会不停触发 VAD，开口时机就测不干净了 |
| 自检 tick | 5s | 庆祝、惊吓这类情绪反应晚 8 秒等于没说，所以粒度定在 5 秒。代价是每次自检都要重读一遍不断变长的上下文 |
| 备料 | 开 · 30s | 整条关掉就可以跑「它完全自力更生」的对照 |
| 画面帧 | 5s | 喂给 Realtime 的图像流，同一张顺手存进环形 buffer（384px，保留 5 分钟） |
| 取帧间隔 | 备料 10 帧 / 查证 6 帧 | 备料取 `0/-5/-10/-15/-20/-30/-45/-60/-120/-240` 秒，近处密远处稀。隔一分钟才一帧看不出动态，刚做成一件事、刚摔下去、还是原地打转，都发生在最近十几秒里 |
| 语音 | `cedar` | 用 `OPENAI_REALTIME_VOICE` 换（`alloy/ash/ballad/coral/echo/sage/shimmer/verse/marin/cedar`），模型用 `OPENAI_REALTIME_MODEL` 覆盖 |

Realtime API 没有语速和语气的直接参数，只能在 instructions 里用文字引导，效果不满意时
换 voice 比改措辞更直接。codex 是纯文本的 coding agent，没有语音模式，所以语音这层只能
走 Realtime。

## 出题与判分工具链

```bash
python3 bench/fetch_videos.py [--check] [container_id ...]     # 按清单下载视频到 media/
python3 bench/mine_proactive.py <container_id> <en.vtt>        # 从转写和画面挖 proactive 题
python3 bench/build_proactive_index.py                         # 刷新 proactive 界面的索引
python3 bench/gen_tts.py                                       # 为 query 题生成提问语音
python3 bench/vtt.py <file.vtt> [n]                            # 把 YouTube 自动字幕转成 {t,text}
```

判分（`bench/judge.py`）是跟陪看 agent 完全分开的一次 LLM 调用：不碰 codex，不碰 Realtime
会话，不共享任何上下文，只拿题面和 agent 实际说出的话去问一个纯文本模型。让同一条会话既
作答又给自己打分等于自己验自己。前端在一道题跑完后自动打一次分，走 `POST /api/judge`，
模型用 `HERBENCH_JUDGE_MODEL` 覆盖。

### 出题的硬性要求：锚点必须截帧核对

只读转写来定锚点会出错，而且不是小概率。给三条新视频出题时做了全量截帧核验，逮到两类
真实错误：

- 理解反了。字幕 `"there's a pop-up in front of your face, but nothing happens"` 读起来像
  「UI 弹窗点了没反应」，截帧一看是反派贴脸的 jump-scare，整道题的方向都写反了。
- 时间戳漂移。把 `mm:ss` 心算成 `anchor_sec` 的时候，小半数锚点跟实际画面差了 25 到 50 秒。

所以每个候选锚点都要用 `ffmpeg -ss <t> -frames:v 1` 截一帧肉眼核对，`scene` 里写的必须是
这一帧画面上有什么。还有一条容易忽略：锚点要落在证据已经出现的那一刻。`hff-p1-t18`
（Water 关通关）原本定在下坠瞬间，而「过关了」这件事只能靠场景切换看出来，锚点往后挪
14 秒到新场景可见的位置，这道题才真正可答。

## 目录

```
demo/
  CODEMAP.md                哪个文件负责什么、关键函数在哪

  agent/                    ① 被测的 agent
    agent_live.py             后端：/answer /lookup /research /cancel /progress
                              （决策那一半在 app/agent.js，见 CODEMAP）

  bench/                    ② 数据获取、出题、判分
    fetch_videos.py           按 container 清单下载视频
    vtt.py                    VTT 转写解析
    mine_proactive.py         从转写和画面挖 proactive 题
    build_proactive_index.py  生成 proactive 界面的索引
    gen_tts.py                合成语音条件用的提问音频
    judge.py                  独立判分，单独一个模型、单独一次调用

  server.py                 ③ dashboard 入口：静态文件 + /api/realtime/token + /api/judge
  app/agent.js                agent 的决策部分：自检、说不说、查什么（只有声明，无副作用）
  app/index.html              主界面：时间轴、面板、判分，以及把 agent 接线拉起来
  app/proactive.html          纯 proactive 界面

  data/containers/*.json    每个 container：视频、章节、题、判分、资料索引
  data/proactive/*.json     proactive 题库，含被复核刷掉的 .dropped.json
  data/resources/           资料快照（wiki 和攻略的 markdown）
  data/thumbs/              时间轴缩略图，每 5 分钟一张
  data/tts/                 合成语音条件用的提问音频
  media/                    浏览器兼容版视频（720p remux，不入库）
```

## 踩过的坑

这几条都是测了才知道的，写在这里免得再踩一次。

`tool_choice` 点名式不生效，细节见前面自检那一节。受影响的不只是自检，`must_cite` 那条
「这类题必须先查证」的规则也一直在空转。

帧差不能当开口信号。试过用画面突变代表有进展、长时间不变代表卡住，实测不成立：Human
Fall Flat 是自由视角，人站着不动镜头也在晃，卡关 60 秒的帧差是 54.9，比真实换关的 45.8
还大。帧差量的是镜头运动，跟有没有进展无关。

不能提前把题目发给 codex 预热。早期版本在锚点前 150 秒把题目原文发过去查，锚点触发时
缓存命中只要 4ms 左右，但那不是预测，是 dashboard 偷看了未来的题目文本，违反
`context_window_sec` 的约定，还会让延迟类指标全部失真。

判断和说话分成两轮之后，第二轮没有否决权：`speak=true` 一旦写下，那一轮必然出声。
做过一次 A/B，每边 20 轮：两轮版在平淡场景误开口 3/10，一轮版（给它一个「闭嘴工具」
让它自己选）是 0/10，到出声的延迟快 3.3 倍（448ms 对 1473ms），70 次沉默判断没有一次
漏音。数据支持换成一轮，但那样沉默会从结构保证变成行为自觉，所以还没切换。

## 已知简化（demo ≠ 正式 harness）

- 不连 Live 的 HTTP 模式下，主动型任务仍然在响应窗口起点直接触发，只是拿到了
  `context_frames`。真正由 agent 自己决定时机和查什么，只在 Live 那条路上生效，因为
  HTTP 模式没有常驻连接，做不了定期自检。
- `transcript_excerpt` 暂时为空，跑完 ASR 之后接入。
- 判分已经接上自动 judge，但规则类指标（`window_hit`、`time_diff`、`over_trigger`）还没做成
  离线脚本，现在只在界面里记录。
