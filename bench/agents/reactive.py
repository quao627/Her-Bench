"""只有前台的 agent：不备料，不用后台通道，被问到才去查。

存在的意义是对照组。它跟 prepared 跑同一个 harness、同一批题、同一套判分，
差别只在它没有后台这一半——所以两者的分差就是「后台到底值多少」。
"""

import json
import os
import urllib.request


class Agent:
    name = "reactive"
    desc = "只有前台，不备料，被问到才现查"

    def __init__(self, backend="http://localhost:8787", lookback=None):
        self.backend = backend
        # 它是一路看过来的，所以回看能力仍然有——那是「看视频」不是「备料」
        self.lookback = lookback or [0, -10, -25, -50, -90, -150, -240, -360, -540, -800]

    def on_question(self, ctx, sec, question, task):
        body = {
            "task_id": task["task_id"], "type": "query", "question": question,
            "anchor_sec": sec, "hint_level": task.get("hint_level"),
            "context_window_sec": task.get("context_window_sec"),
            "game": ctx.title, "container_id": ctx.container_id,
            "frame_jpeg_base64": ctx.frames.hi_res(sec),
        }
        req = urllib.request.Request(f"{self.backend}/answer",
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=200) as r:
            j = json.load(r)
        return {"text": j.get("text", ""), "citations": j.get("citations") or [],
                "served": "现查", "notes_at_hand": 0}
