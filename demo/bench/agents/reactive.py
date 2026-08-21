"""什么都不做，直到被问：不看画面，不备料，不用后台通道。

harness 每 5 秒推一帧，但这个类根本没有 on_frame，所以那些帧它一眼都没看。
被问到时手上只有锚点那一帧。

这是最底下那一档。跟 watching 比，多出来的是「看视频」；watching 跟 prepared 比，
多出来的才是「后台备料」。少了中间那档，分差说不清是哪一半的功劳。
"""

import json
import urllib.request


class Agent:
    name = "reactive"
    desc = "不看画面，被问到才现查"

    def __init__(self, backend="http://localhost:8787"):
        self.backend = backend

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
