# Her-Bench

评一个**实时陪看 agent**：一个人在做他不熟的事——盲玩一款游戏、第一次打开
Blender——agent 在旁边看着，在他需要的时候给恰好够用的帮助。

难点不在知识，在分寸。同一份正确答案，说早了毁掉探索，说晚了他已经自己弄明白了，
说多了变成替他玩。所以这套 benchmark 把两件事分开评：**说得对不对**（要点命中、
引用真实、不剧透），和**该不该在这一刻说**（开口时机、多余发言）。

- 📄 **设计草案**：<https://quao627.github.io/Her-Bench/design-v0.4.html>
- 🎬 **可跑的 demo**：见 [`demo/README.md`](demo/README.md)

## 现在有什么

| | 说明 |
|---|---|
| **8 个 container** | 每个 = 一个视频 + 转写 + 资料快照 + 挂在时间轴上的题。游戏盲玩、直播编程、软件首次上手、恐怖/叙事游戏各占一档 |
| **两套题** | *query* 型（主播问出声，考答得准不准）和 *proactive* 型（没有人提问，考该不该开口） |
| **一个查看器** | 像剪辑软件一样摊开时间轴、锚点、判分配置，以及 agent 每一次调用的输入输出 |
| **一个参考 agent** | Realtime API 负责说话 + codex CLI 负责查证，两个引擎经一次 HTTP 调用衔接 |
| **独立判分** | 判分是另一个模型的另一次调用，不碰陪看 agent 的任何上下文 |

## 快速开始

```bash
cd demo
python3 bench/fetch_videos.py                  # 把视频下到位（首次；需要 yt-dlp + ffmpeg）
python3 server.py                              # dashboard → http://localhost:8080
python3 agent/agent_live.py                    # agent 后端（另开一个终端，需先 codex login）
```

要用语音陪看，把 platform key 写进 `demo/.env`（`OPENAI_API_KEY=sk-...`）后重启
`server.py`，再点界面右上角 🎙 Live。完整说明在 [`demo/README.md`](demo/README.md)。

## 仓库结构

```
demo/
  agent/       ① 被测的 agent：说话的一端（Realtime）+ 查证的一端（codex）
  bench/       ② 数据获取 + 出题 + 判分：把视频变成题，把回答变成分
  server.py    ③ dashboard 入口
  app/         ③ dashboard 前端（主界面 + 纯 proactive 界面）
  data/        素材与题库（三部分共用）
docs/          设计草案（v0.1 → v0.4）和两张机制图，GitHub Pages 从这里发布
live/          一个旁支实验：让弱 agent 直接玩 Pokemon，用来对照「看着别人玩」和「自己玩」
```

谁在哪、哪个函数干什么：[`demo/CODEMAP.md`](demo/CODEMAP.md)

## 视频不在仓库里

`demo/media/`（浏览器兼容版视频）和 `videos/`（原片）都被 `.gitignore` 排除了——
体积太大，而且版权不属于我们。clone 下来的仓库里题库、资料、缩略图、转写都在，
视频用一条命令补齐（清单里记着每个视频的来源和该放哪）：

```bash
cd demo && python3 bench/fetch_videos.py        # --check 只报状态，也可以只下某几个
```

需要 `yt-dlp` 和 `ffmpeg`（`brew install yt-dlp ffmpeg`）。

`demo/.env` 同样不入库，里面是 OpenAI 的 key。

## 状态

设计还在改，接口也还在动。当前 demo 与正式 harness 的差距列在
[`demo/README.md` 的「已知简化」](demo/README.md#已知简化demo--正式-harness)。
