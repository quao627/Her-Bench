# judge — 判分

一次无状态的 LLM 调用，把「agent 说的这段话」变成一组可勾选的判断。

```python
from judge import judge_run
code, verdict = judge_run(task, run)          # code=200 时 verdict 是结果
```

## 为什么单独一层

**判分必须是外部视角。** 让同一条会话既作答又给自己打分等于自己验自己；而且它手里
还留着刚查到的资料、刚看过的画面，会顺着自己的话往下认——「我说白墙才能开门，
那当然对」。

所以这一层：

- 不 import agent 那边的任何东西，不碰 codex，不碰 Realtime 会话
- 不接收 agent 的上下文、笔记、查证记录
- 只拿**题面**和**agent 到底说出口的那段话**
- 用一个单独的模型（`HERBENCH_JUDGE_MODEL`，默认 `gpt-5.4`），跟被测的那个无关

提示词里那条最重要的规矩是：**只根据给你的材料判**。判分员很可能自己就知道这游戏
怎么通关，但那不作数——依据只能是题面写的 rubric、防剧透清单和 agent 的原话。

## 判什么

一次调用返回八项，每项都带一句依据（要引 agent 的原话或题面的原话）：

| 字段 | 判什么 | 取值 |
|---|---|---|
| `rubric[]` | 跟 `rubric_points` 一一对应，逐条判有没有说到这条的意思 | `hit` + `why` |
| `spoiler[]` | 跟 `spoiler_blocklist` 一一对应，点名的内容有没有被提到 | `violated` + `why` |
| `leaked_future` | 清单之外，有没有说锚点之后才会发生的事 | bool + `why` |
| `hint_level_ok` | `direction_only` 的题有没有给出照着做就能过的完整步骤 | bool + `why` |
| `grounding` | 指认画面里的东西对不对 | `ok` / `wrong` / `na` |
| `citation` | `must_cite` 为真时，有没有给来源、来源对不对得上 | `ok` / `missing` / `irrelevant` / `na` |
| `spoken_ok` | 像说出来的还是念稿子；口语但没信息量也算不合格 | bool + `why` |
| `silence_ok` | proactive 且没开口时：这一刻该不该沉默 | `good` / `missed` / `na` |
| `verdict` | 一两句总评，说清扣在哪 | string |

判断标准看意思不看字面：同义换句算命中；说到了但说错了不算；只是重复问题、
或者含糊到听完还是不知道怎么办，不算。

结果里另有 `_meta`：用了哪个模型、耗时、token 数、有没有看到画面。

## 输入长什么样

```python
task = {
  "task_id": "portal-e01-t01",
  "type": "query",                      # 或 proactive
  "anchor_sec": 630,                    # 锚点之后的一律算它不该知道
  "hint_level": "full",                 # 或 direction_only
  "question": "我刚拿到的这个装置是干什么用的？",
  "scene": "...",                       # 可选，锚点那一帧上有什么
  "response_window_sec": [a, b],        # 可选，proactive 才有
  "grading": {
    "rubric_points": [...],
    "spoiler_blocklist": [...],
    "must_cite": True,
  },
}
run = {"answer": "...", "citations": [...], "spoke_at_sec": 640}
```

纯 proactive 那套题的字段名不一样（`help_points` / `must_not_say`），调用方负责
映射成上面这个形状，见 `bench/run_proactive.py` 里的 `shim`。

可以再传一张 `frame_jpeg_base64`，判 `grounding` 时用；不传就返回 `na`。

## 谁在调

| 调用方 | 什么时候 |
|---|---|
| `server.py` 的 `POST /api/judge` | dashboard 上一道题跑完自动判，或者点「⚖ 重判」 |
| `bench/run_live.py` | 离线跑完一遍之后批量判 |
| `bench/run_query.py` / `run_stream.py` / `run_proactive.py` | 同上 |

判分是并发安全的：没有会话、没有共享状态，几条一起跑就行。dashboard 那条走
`ThreadingHTTPServer` 的线程，判分那几秒不挡视频流。

## 文件

```
judge/
  __init__.py   对外只有 judge_run / JUDGE_MODEL
  core.py       输出 schema、调用、兜底。条数跟 rubric 对不上会补齐，防止前端错位
  prompt.py     判分员是谁、给他什么材料、要他逐条判什么
```

`prompt.py` 是最常改的一个。**改判分标准会让历史分数不可比**，所以动它的时候
最好一并换掉 `HERBENCH_JUDGE_MODEL` 或者留个版本记号，别让新旧结果混在一起。

## 环境变量

| | 默认 | |
|---|---|---|
| `OPENAI_API_KEY` | 必须 | 没有就返回 503 |
| `HERBENCH_JUDGE_MODEL` | `gpt-5.4` | 换模型重跑一遍能看判分本身稳不稳 |
| `HERBENCH_JUDGE_TIMEOUT` | `90` | 秒 |
