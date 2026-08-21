# 代码地图

代码分成三部分：被测的 agent、出题和判分用的 bench、给人看的 dashboard。下面的锚点
用函数名而不是行号，行号会随着修改漂移，名字不会（`grep -n <名字> <文件>`）。

```
demo/
  agent/     被测的 agent：说话的一端和查证的一端
  bench/     数据获取、出题、判分：把视频变成题，把回答变成分
  server.py  dashboard 入口，发静态文件，另外提供两个 API
  app/       前端。agent.js 是 agent 的决策逻辑，index.html 和 proactive.html 是 dashboard
  data/      素材与题库，三部分共用
```

流程是 bench 出题，dashboard 把题喂给 agent 并记录它说了什么，再由 bench 判分。
agent 看不到题是怎么出的，判分也拿不到 agent 的任何上下文，这两处隔离是有意设计的。

---

## 一、agent

agent 由两个引擎组成，中间用一次 HTTP 调用衔接。判断全部发生在说话的那一端，
查证的那一端只执行被交给它的问题。

```
浏览器 ──原声/画面帧──► Realtime API ──┬──► 说出来（用户听得到）
                        （常驻，会说话） │
                                        └──► HTTP ──► agent/agent_live.py ──► codex CLI
                                                      （无状态，能读资料和搜网）
```

### 决策部分：`app/agent.js`

这个文件里只有声明，没有任何顶层副作用。定时器、按钮绑定和初始化都写在
`app/index.html` 里，由 dashboard 负责拉起，所以 agent.js 先加载，两个文件共享同一个
全局作用域。它用到的 `$`、`video`、`C`、`liveLine`、`bcallStart`、`captureFrame` 等都在
index.html 里定义，运行时才解析，文件头的注释列出了完整清单。

| 环节 | 函数 | 说明 |
|---|---|---|
| 定期自检 | `selfCheck()` | 每 5 秒发一个纯文本响应，用户听不到。参数是 `tools:[DECIDE_TOOL]` 加 `tool_choice:'required'`，点名式的 `{type:'function', name:'decide'}` 实测不会被强制执行 |
| 接住结论 | `handleDecideCall()` | 结论以 `decide` 工具调用的形式回来，参数由 API 按 schema 校验 |
| 执行结论 | `applyDecision()` | 要说就再发一次语音响应，要查就走后台通道，后台正忙时把问题排进队列 |
| 文本兜底 | `onSelfCheckText()` | 它没走工具而是回了文字时尽量解析，解析不出来就按不说处理 |
| 后台查证 | `runBackgroundLookup()` / `runIdleResearch()` | 前者查它自己提的问题，后者是定时备料 |
| 中止后台 | `yieldBgToUser()` | 主播开口时取消后台请求，并让后端结束正在跑的子进程 |
| 画面 buffer | `pushFrameBuf()` / `framesAround()` | 每 5 秒存一帧（384px，保留 5 分钟），取用时近处密、远处稀 |
| 传输层 | `liveConnect()` / `handleLiveEvent()` / `handleToolCall()` | WebRTC 连接、音频图、事件分派 |

### 查证部分：`agent/agent_live.py`

| 端点 | 函数 | 问题的来源 | codex 会话 |
|---|---|---|---|
| `/answer` | `answer()` | 题目文件，用在不连 Live 的通路上 | `fg` |
| `/lookup` | `_handle_lookup()` | 主播问出声，或者它自检时自己提的（`background:true`） | `fg` / `bg` |
| `/research` | `_handle_research()` | 没有人提问，codex 从最近十帧画面里自己想一个 | `bg` |
| `/cancel` | `cancel_run()` | 主播开口时结束正在跑的 codex 子进程 | — |
| `/progress` | 路由里内联 | 前端轮询，回显 codex 正在读什么、搜什么 | — |

其他值得知道的位置：`run_codex()` 负责起子进程、解析 `--json` 事件流、续接会话和看门狗
超时；`DEADLINES` 是三条截止线（前台 40s、后台 90s、锚点题 120s）；`get_resource_docs()`
按当前进度决定把哪几篇资料拼进 prompt；三个提示词模板是 `PROMPT_TMPL`、`LOOKUP_TMPL`
和 `RESEARCH_TMPL`。

---

## 二、bench：数据获取、出题、判分

```bash
python3 bench/fetch_videos.py                    # 按清单把视频下到 demo/media/
python3 bench/mine_proactive.py <cid> <en.vtt>   # 挖 proactive 题
python3 bench/build_proactive_index.py           # 刷新 proactive 界面索引
python3 bench/run_query.py <cid>                 # 问答题，每道题冷启动各跑各的
python3 bench/run_stream.py <cid>                # 问答题，顺着视频看、边看边备料
python3 bench/run_proactive.py <cid>             # 离线跑纯 proactive，不用 agent 后端
python3 bench/gen_tts.py                         # 给 query 题生成提问语音
python3 bench/vtt.py <file.vtt> [n]              # 看 VTT 解析结果
```

### 数据获取

`bench/fetch_videos.py` 完全由 container 清单驱动。清单里写着这个 container 用哪个视频
（`video.source_url`）以及该放在哪（`video.src`），所以下载、命名、放置一次做完，
`--check` 只报状态不下载。视频因为体积和版权都不入库，题库和资料入库。
`bench/vtt.py` 把 YouTube 自动字幕转成 `{t, text}` 序列，出题的第一步要用。

### 两种题

| | query 型 | proactive 型 |
|---|---|---|
| 场景 | 主播问出声 | 没有人提问 |
| 考什么 | 答得准不准 | 该不该在这一刻开口 |
| 存放位置 | `data/containers/<id>.json` 的 `tasks[]` | `data/proactive/<id>.json` |
| 锚点 | 一个时刻 `anchor_sec` | 一段窗口 `window_sec` |
| 出题代码 | 没有，目前是人和 agent 一起写进 JSON | `bench/mine_proactive.py` |

query 题的字段包括 `question`、`context_window_sec`（agent 只能看到锚点之前的内容）、
`hint_level`（提示分级）、`scene`（写的必须是这一帧画面上有什么），以及 `grading` 里的
`rubric_points`、`spoiler_blocklist` 和 `must_cite`。出题时有两条硬规则：锚点必须用
`ffmpeg -ss` 截帧核对过，并且要落在证据已经出现的那一刻。

proactive 题由 `bench/mine_proactive.py` 分两段挖出来：

| 阶段 | 函数 | 做什么 |
|---|---|---|
| 一、从转写提候选 | `mine_chunk()` | 按分钟切段，找他确实需要帮助的时刻，把原话抄下来当 `evidence`。这一步看不到画面，所以只写 `look_for`，也就是如果这件事是真的，画面上应该能看到什么 |
| 二、截帧复核 | `verify()` | 在窗口内取八帧，让模型只看画面判断一个听不到声音的人能不能察觉这里不太顺，能察觉才留下 |

刷掉的比留下的多是有意的。只在嘴上抱怨、画面上完全没有痕迹的时刻，对一个只有画面的
agent 来说是无解题。被刷掉的候选写进 `<id>.dropped.json`，方便回头复盘。

### 判分

`bench/judge.py` 对外只有 `judge_run()` 一个入口。它不碰 codex，也不碰 Realtime 会话，
不共享任何上下文，只拿题面和 agent 实际说出的话去问一个纯文本模型。让同一条会话既作答
又给自己打分等于自己验自己，所以这条路必须独立。dashboard 在一道题跑完后自动调一次
（`POST /api/judge`），模型可以用 `HERBENCH_JUDGE_MODEL` 覆盖。

---

## 三、dashboard

| 文件 | 内容 |
|---|---|
| `server.py` | 发静态文件（带 HTTP Range，视频拖动需要），另外提供 `/api/realtime/token`（用 master key 换 ephemeral key，浏览器拿不到真 key）和 `/api/judge` |
| `app/index.html` | 主界面：时间轴、题、判分、后台面板，以及把 agent 接线拉起来的那部分 |
| `app/proactive.html` | 纯 proactive 界面，只给画面，没有声音也没有人提问 |

`app/index.html` 内部按注释分区，搜 `═══` 可以跳转：

| 分区 | 内容 |
|---|---|
| 时间轴绘制 | `draw()`：缩略图带、锚点标记、响应窗口、拖动缩放 |
| 右侧面板 | 任务、资料、判分、后台调用、记录五个 tab，其中 `renderBackendPane()` 展开 agent 每一次调用的输入输出 |
| 任务触发与判分 | `triggerTask()` 在播到锚点时触发，`openGrading()` 在跑完后送去判分 |
| 评分窗口 | `armProactiveWindows()` 和 `noteProactiveHit()` 记录 proactive 窗口有没有被接住，不去催 agent 说话 |
