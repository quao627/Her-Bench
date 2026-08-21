# Her-Bench

评测实时陪看 agent 的一套题库、运行环境和参考实现。场景是有人在盲玩游戏或者第一次用
某个软件，agent 看着同一块屏幕，在他需要时给帮助。评测分两条轴：说得对不对（要点命中、
引用真实、不剧透、提示不越级），以及该不该在这一刻说（开口时机落没落进窗口、有多少多余
发言）。这两条分开算，不合成单一总分。

设计草案：<https://quao627.github.io/Her-Bench/design-v0.4.html>

## 现在有什么

题库覆盖 8 个视频，共 19.3 小时：

| container | 时长 | query 题 | 锚点 proactive | 内容 |
|---|---|---|---|---|
| `hff-p1` | 4.1h | 12 | 6 | Human Fall Flat 首次盲玩 |
| `portal-e01` | 2.7h | 11 | 4 | Portal 首次盲玩全流程 |
| `mc-e01` | 2.4h | 11 | 4 | Minecraft 不看 wiki 盲玩 |
| `rust-e01` | 3.8h | 10 | 4 | Rust 直播编程 |
| `blender-e01` | 5.0h | 11 | 4 | Blender 首次上手 |
| `blender-e02` | 0.2h | 6 | 3 | Blender 一周自学复盘 |
| `slendytubbies-e01` | 0.3h | 8 | 3 | 恐怖游戏首次盲玩 |
| `stanleyparable-e01` | 0.8h | 15 | 7 | 叙事游戏首次盲玩，剧透红线最严 |

- **84 道 query 题**：主播问出声，题里写着问题原文、可见范围（`context_window_sec`）、
  提示分级、要点清单、剧透黑名单、是否必须引用。
- **35 道锚点型 proactive 题** 加 **16 道纯 proactive 题**：没有人提问，考它自己判断
  什么时候开口。纯 proactive 那批由脚本从转写挖出候选、再截帧复核，另有 10 条候选因为
  画面上看不出异常被刷掉。
- **配套素材**：39 篇资料快照（wiki 和攻略，每篇标真实来源 URL）、234 张时间轴缩略图、
  84 条提问 TTS 音频。视频本身不入库，用脚本按清单下载。

## 参考 agent 实现了什么

agent 分两端。Realtime API 常驻浏览器，听声音、每 5 秒看一帧画面、负责说话；codex CLI
在本地起 HTTP 服务，能读资料和搜网。判断全在说话那一端，codex 只执行交给它的问题。

- **自检**：Realtime 不会自发说话，所以每 5 秒发一个纯文本响应（用户听不到），强制它调用
  `decide` 工具交回四个字段：说不说、说什么要点、要不要查、查证是否需要看画面。判断不说
  的时候是真的安静，因为那一轮的 modality 就是纯文本。
- **三条查证通道**：题目文件触发的 `/answer`、主播问出声时它自己调工具的 `/lookup`、
  以及没人提问时 codex 从最近十帧画面自己想问题的 `/research`。前两条走前台会话，
  后两条走后台会话，`codex exec resume` 让同一 container 的多次查证能接上。
- **主播问话优先**：语音检测一响就取消后台请求并结束 codex 子进程，实测 0.8 秒返回。
- **截止线**：前台 40 秒、后台 90 秒、锚点题 120 秒，超时返回一句 agent 能直接用的话。
- **独立判分**：`bench/judge.py` 单独一个模型、单独一次调用，不共享 agent 的任何上下文，
  一道题跑完自动打一次分。

## 怎么用

```bash
cd demo
python3 bench/fetch_videos.py                  # 按清单下载视频（首次；需要 yt-dlp + ffmpeg）
python3 server.py                              # dashboard → http://localhost:8080
python3 agent/agent_live.py                    # agent 后端 → :8787（另开终端，需先 codex login）
```

打开 dashboard，左上角切 container，时间轴上的 ◆/◇ 是题的锚点。播到锚点会触发一道题，
右侧面板能看到 agent 每一次调用的完整输入输出，包括它实际收到的 prompt。要用语音陪看，
把 platform key 写进 `demo/.env`（`OPENAI_API_KEY=sk-...`，跟 codex 用的 ChatGPT 登录不是
一套账号），重启 `server.py`，点右上角 🎙 Live。不连 Live 也能跑完整流程，回答改由浏览器
TTS 念出来。

出题和判分的命令、端点签名、所有可调参数的默认值，见 [`demo/README.md`](demo/README.md)。
哪个文件负责什么、关键函数在哪，见 [`demo/CODEMAP.md`](demo/CODEMAP.md)。

## 仓库结构

```
demo/
  agent/       被测的 agent 后端（717 行），决策部分在 app/agent.js（641 行）
  bench/       下载视频、解析转写、挖 proactive 题、生成 TTS、判分
  server.py    dashboard 入口，发静态文件并提供 token 和判分两个 API
  app/         dashboard 前端：主界面和纯 proactive 界面
  data/        题库、资料快照、缩略图、TTS 音频
docs/          设计草案 v0.1 到 v0.4，GitHub Pages 从这里发布
live/          旁支实验：让弱 agent 直接玩 Pokemon，对照「看着别人玩」和「自己玩」
```

## 视频不在仓库里

`demo/media/` 和 `videos/` 都在 `.gitignore` 里，体积太大，版权也不属于我们。clone 之后
题库、资料、缩略图、转写都是全的，视频用一条命令补齐，每个 container 的清单里记着它用
哪个视频、该放在哪：

```bash
cd demo && python3 bench/fetch_videos.py        # --check 只报状态，也可以只下某几个
```

`demo/.env` 同样不入库，里面是 OpenAI 的 key。

## 还没做的

- 规则类指标（`window_hit`、`time_diff`、`over_trigger`）还没做成离线脚本，现在只在
  界面里记录。
- query 题目前是人和 agent 一起写进 JSON 的，没有出题脚本；proactive 有
  `bench/mine_proactive.py`。
- 不连 Live 的 HTTP 模式里，主动型任务仍在响应窗口起点直接触发，真正由 agent 自己决定
  时机只在 Live 那条路上生效。
- `transcript_excerpt` 暂时为空，跑完 ASR 后接入。
