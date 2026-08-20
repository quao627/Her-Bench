# Her-Bench

Her-Bench 用来评测实时陪看 agent。场景是一个人在做他不熟的事，比如盲玩一款游戏、
第一次打开 Blender，agent 在旁边看着，在他需要的时候给恰好够用的帮助。

难的地方不是知识，是分寸。同一份正确答案，说早了会毁掉他自己探索的过程，说晚了他
已经弄明白了，说太多就变成替他玩。所以评测把两件事分开算：说得对不对（要点有没有
命中、引用是否真实、有没有剧透），以及该不该在这一刻说（开口时机、有多少多余发言）。

- 设计草案：<https://quao627.github.io/Her-Bench/design-v0.4.html>
- 可以跑的 demo：见 [`demo/README.md`](demo/README.md)

## 现在有什么

| | 说明 |
|---|---|
| 8 个 container | 每个 container 是一个视频，加上转写、资料快照和挂在时间轴上的题。覆盖游戏盲玩、直播编程、软件首次上手、恐怖和叙事游戏 |
| 两种题 | query 型是主播问出声，考答得准不准；proactive 型没有人提问，考该不该开口 |
| 一个 dashboard | 展开时间轴、锚点、判分配置，以及 agent 每一次调用的输入和输出 |
| 一个参考 agent | Realtime API 负责说话，codex CLI 负责查证，中间用一次 HTTP 调用衔接 |
| 独立判分 | 判分是另一个模型的另一次调用，不共享陪看 agent 的任何上下文 |

## 快速开始

```bash
cd demo
python3 bench/fetch_videos.py                  # 把视频下到位（首次；需要 yt-dlp + ffmpeg）
python3 server.py                              # dashboard → http://localhost:8080
python3 agent/agent_live.py                    # agent 后端（另开一个终端，需先 codex login）
```

要用语音陪看，把 platform key 写进 `demo/.env`（`OPENAI_API_KEY=sk-...`）后重启
`server.py`，再点界面右上角的 🎙 Live。完整说明在 [`demo/README.md`](demo/README.md)。

## 仓库结构

```
demo/
  agent/       被测的 agent：说话的一端（Realtime）和查证的一端（codex）
  bench/       数据获取、出题、判分：把视频变成题，把回答变成分
  server.py    dashboard 入口
  app/         dashboard 前端，以及 agent 在浏览器这端的决策逻辑
  data/        素材与题库
docs/          设计草案（v0.1 到 v0.4）和两张机制图，GitHub Pages 从这里发布
live/          一个旁支实验：让弱 agent 直接玩 Pokemon，用来对照「看着别人玩」和「自己玩」
```

哪个文件负责什么、关键函数在哪，见 [`demo/CODEMAP.md`](demo/CODEMAP.md)。

## 视频不在仓库里

`demo/media/`（浏览器兼容版视频）和 `videos/`（原片）都在 `.gitignore` 里，一是体积太大，
二是版权不属于我们。clone 下来之后题库、资料、缩略图、转写都是全的，视频用一条命令补齐，
每个 container 的清单里记着它用哪个视频、该放在哪：

```bash
cd demo && python3 bench/fetch_videos.py        # --check 只报状态，也可以只下某几个
```

需要 `yt-dlp` 和 `ffmpeg`（`brew install yt-dlp ffmpeg`）。`demo/.env` 同样不入库，
里面是 OpenAI 的 key。

## 状态

设计和接口都还在改。当前 demo 与正式 harness 的差距列在
[`demo/README.md` 的「已知简化」](demo/README.md#已知简化demo--正式-harness)。
