# agents — 被测的 agent

跟评测那一侧只有 HTTP，别的什么都不共享。它们跑在**另一个进程**里，拿不到题、
拿不到判分标准、拿不到 `bench/` 和 `judge/` 里的任何东西——能看到的只有画面和
主播说的话。

协议见 [PROTOCOL.md](PROTOCOL.md)。用任何语言写都行，能发 HTTP 就够了。

## 现有的三个

| | 看画面 | 后台备料 | 用来说明 |
|---|---|---|---|
| `reactive.py` | ✗ | ✗ | 最底下那一档：不问就什么都不干 |
| `watching.py` | ✓ | ✗ | 比 reactive 多的是「一路看着」 |
| `prepared.py` | ✓ | ✓ | 比 watching 多的是「后台提前查」 |

三个连着看是一条消融线，每档只多一样东西，所以分差能归因。

## 跑

```bash
python3 bench/run_eval.py portal-e01 --agent agents/prepared.py --limit 1300
```

`run_eval.py` 会起评测服务、把地址通过 `HERBENCH_WORLD` 传给 agent 进程、
等它跑完、再判分。agent 崩了或者卡住不算评测的问题，会照实报出来。

## 自己写一个

```python
import os, urllib.request, json
W = os.environ["HERBENCH_WORLD"]

def call(path, body=None):
    req = urllib.request.Request(W + path, method="POST" if body is not None else "GET",
                                 data=json.dumps(body or {}).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)

while True:
    r = call("/tick", {})
    if r["done"]:
        break
    if r["event"]:                       # 主播开口了，得回话
        call("/say", {"text": my_answer(r["event"]["text"], r["frame"])})
    elif i_should_speak(r["frame"]):     # 或者你自己觉得该说
        call("/say", {"text": "..."})
```

**时间是要算的。** 你从拿到响应到下一次 `/tick` 之间花掉的墙钟时间，会被记进视频
时间：花得少就每次前进一帧、看到每一帧；花得多就按你的耗时前进，中间的帧直接错过，
主播的问题也要等你回来才拿得到。后台线程随便开，但那些时间同样会在下一次 `/tick`
上体现。
