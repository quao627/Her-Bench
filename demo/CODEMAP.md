# 代码地图

三部分，各管各的。锚点用函数名不用行号——行号会漂，名字不会（`grep -n <名字> <文件>`）。

```
demo/
  agent/     被测的那个 agent：说话的一端 + 查证的一端
  bench/     数据获取 + 出题 + 判分：把视频变成题，把回答变成分
  server.py  dashboard 入口（发静态文件 + 两个 API）
  app/       前端：agent.js（agent 的决策逻辑）+ index.html / proactive.html（dashboard）
  data/      素材与题库（三部分共用）
```

一句话分工：**bench 出题 → dashboard 把题喂给 agent 并录下它说了什么 → bench 判分。**
agent 不知道题是怎么出的，判分不知道 agent 是怎么想的。这两条隔离是刻意的。

---

## 一、agent

两个引擎，一次 HTTP 调用衔接。**说话的那端做全部判断，查证的那端只是工具。**

```
浏览器 ──原声/画面帧──► Realtime API ──┬──► 说出来（用户听得到）
                        （常驻，会说话） │
                                        └──► HTTP ──► agent/agent_live.py ──► codex CLI
                                                      （无状态，能读资料/搜网）
```

### 决策在浏览器这端（`app/agent.js`）

单独一个文件，**只有声明、没有任何顶层副作用**——定时器、按钮绑定、初始化都在
`app/index.html` 那边由 dashboard 拉起，所以 agent.js 先加载，两边共享同一个全局作用域。
它向 dashboard 借 `$` / `video` / `C` / `liveLine` / `bcallStart` / `captureFrame` 这些，
都是运行时才解析（文件头的注释里列全了）。

| 环节 | 函数 | 关键点 |
|---|---|---|
| 定期自检 | `selfCheck()` | 每 5 秒一次纯文本响应（用户听不到），`tools:[DECIDE_TOOL]` + `tool_choice:'required'`。**必须 `'required'`**，点名式实测不生效 |
| 接住结论 | `handleDecideCall()` | 结论以 `decide` 工具调用回来，参数由 API 按 schema 校验 |
| 执行结论 | `applyDecision()` | 要说 → 再发一次语音响应；要查 → 走后台通道；后台忙就排队 |
| 文本兜底 | `onSelfCheckText()` | 它没走工具时尽量解析，解析不了按「不说」处理 |
| 后台查证 | `runBackgroundLookup()` / `runIdleResearch()` | 前者是它自己提的问题，后者是定时备料 |
| 让路 | `yieldBgToUser()` | 主播一开口就掐掉后台请求，并让后端 kill 掉子进程 |
| 画面 buffer | `pushFrameBuf()` / `framesAround()` | 每 5 秒存一帧（384px，留 5 分钟），取用时近处密远处稀 |
| 传输层 | `liveConnect()` / `handleLiveEvent()` / `handleToolCall()` | WebRTC、音频图、事件分派 |

### 查证在后端（`agent/agent_live.py`）

| 端点 | 函数 | 问题谁提的 | 会话 |
|---|---|---|---|
| `/answer` | `answer()` | 题目文件（不连 Live 时的通路） | `fg` |
| `/lookup` | `_handle_lookup()` | 主播问出声；或它自检时自己提的（`background:true`） | `fg` / `bg` |
| `/research` | `_handle_research()` | 没人提问，codex 从最近十帧画面里自己想一个 | `bg` |
| `/cancel` | `cancel_run()` | 主播开口时杀掉正在跑的 codex 子进程 | — |
| `/progress` | 路由里内联 | 前端轮询，回显 codex 在读什么搜什么 | — |

其余关键位置：`run_codex()`（起子进程、解析 `--json` 事件流、会话续接、看门狗超时）、
`DEADLINES`（前台 40s / 后台 90s / 锚点题 120s）、`get_resource_docs()`（按进度挑该给哪几篇资料）、
三个提示词模板 `PROMPT_TMPL` / `LOOKUP_TMPL` / `RESEARCH_TMPL`。

`agent/agent_stub.py` 是同协议的罐头实现，秒回，用来验证接线。

---

## 二、bench：数据获取 + 出题 + 判分

```bash
python3 bench/fetch_videos.py                    # 按清单把视频下到 demo/media/
python3 bench/mine_proactive.py <cid> <en.vtt>   # 挖 proactive 题
python3 bench/build_proactive_index.py           # 刷新 proactive 界面索引
python3 bench/gen_tts.py                         # 给 query 题生成提问语音
python3 bench/vtt.py <file.vtt> [n]              # 看 VTT 解析结果
```

### 数据获取

`bench/fetch_videos.py` 完全由 container 清单驱动：清单里写着用哪个视频（`video.source_url`）
和该放哪（`video.src`），所以下载、命名、放置一步到位，`--check` 只报状态。
视频不入库（体积 + 版权），题库和资料入库。`bench/vtt.py` 把 YouTube 自动字幕转成
`{t, text}` 序列，出题那一步要用。

### 两种题，两条出题路径

| | query 型 | proactive 型 |
|---|---|---|
| 场景 | 主播问出声 | 没有人提问 |
| 考什么 | 答得准不准 | 该不该在这一刻开口 |
| 题存在 | `data/containers/<id>.json` 的 `tasks[]` | `data/proactive/<id>.json` |
| 锚点 | 一个时刻 `anchor_sec` | 一段窗口 `window_sec` |
| **出题代码** | **没有，是人和 agent 一起写进 JSON 的** | `bench/mine_proactive.py` |

query 题的字段：`question` / `context_window_sec`（只能看到锚点之前）/ `hint_level`
（提示分级）/ `scene`（必须写「这一帧画面上有什么」）/ `grading.rubric_points`、
`spoiler_blocklist`、`must_cite`。两条硬规则：锚点必须 `ffmpeg -ss` 截帧肉眼核对；
锚点要落在**证据已经出现**的那一刻。

proactive 题由 `bench/mine_proactive.py` 两段式挖出来：

| 阶段 | 函数 | 干什么 |
|---|---|---|
| 一、转写提候选 | `mine_chunk()` | 按分钟切段找「他确实需要帮助」的时刻，抄原话当 `evidence`。这一步看不到画面，只写 `look_for`：如果这事是真的，画面上该有什么 |
| 二、截帧复核 | `verify()` | 窗口内取八帧，让模型**只看画面**判断能不能察觉这里不太顺。能才留下 |

刷掉的比留下的多是有意的：只在嘴上抱怨、画面上没痕迹的时刻，对只有画面的 agent
来说是无解题。被刷掉的进 `<id>.dropped.json` 留着复盘。

### 判分

`bench/judge.py`，唯一入口 `judge_run()`。**跟 agent 完全隔离**：不碰 codex、不碰 Realtime
会话、不共享任何上下文，只拿「题面 + agent 到底说了什么」问一个纯文本模型——让同一条
会话既作答又给自己打分等于自己验自己。dashboard 一道题跑完自动调一次
（`POST /api/judge`），模型用 `HERBENCH_JUDGE_MODEL` 覆盖。

---

## 三、dashboard

| 文件 | 是什么 |
|---|---|
| `server.py` | 静态文件（带 HTTP Range，视频拖动要用）+ `/api/realtime/token`（换 ephemeral key，浏览器拿不到真 key）+ `/api/judge` |
| `app/index.html` | 主界面：时间轴 + 题 + 判分 + 后台面板。**只剩 dashboard 的活**，agent 的决策在 `app/agent.js` |
| `app/proactive.html` | 纯 proactive 界面：只给画面，没有声音也没人提问 |

`app/index.html` 里的分区（搜 `═══`）：

| 分区 | 干什么 |
|---|---|
| 时间轴绘制 | `draw()`：缩略图带、锚点标记、响应窗口、拖动缩放 |
| 右侧面板 | 任务 / 资料 / 判分 / 后台调用 / 记录五个 tab；`renderBackendPane()` 是把 agent 每次调用摊开看的那个 |
| 任务触发与判分 | `triggerTask()` 播到锚点时触发，`openGrading()` 跑完自动送判分 |
| 锚点任务与评分窗口 | `sendLiveTask()` 发 query 题；`armProactiveWindows()` / `noteProactiveHit()` 只记录 proactive 窗口有没有被接住，不催它说话 |
