"""一路看着，但没有后台：被问到时手上有从开头到现在的画面，没有任何提前查好的资料。

夹在 reactive 和 prepared 中间，用来把两件事拆开：
    reactive → watching   多的是「看视频」
    watching → prepared   多的是「后台备料」
少了这一档，两者的分差说不清是哪一半的功劳。
"""

import json
import os
import urllib.request

from .prepared import FAST_SCHEMA, FAST_SYS, LOOKBACK, _openai, _post, FRONT_MODEL


class Agent:
    name = "watching"
    desc = "一路看着，但没有后台备料"

    def __init__(self, backend="http://localhost:8787"):
        self.backend = backend

    def on_frame(self, ctx, sec, frame):
        return None          # 看着，但什么都不做——回看条是从 ctx.frames 现取的

    def on_question(self, ctx, sec, question, task):
        strip = ctx.frames.since_start(sec, LOOKBACK)
        stamps = "、".join(f"{s//60}:{s%60:02d}" for s, _ in strip)
        content = [{"type": "text", "text":
                    f"你在陪他玩：{ctx.title}\n\n"
                    f"下面是你一路看过来的画面，时间点分别是 {stamps}，最后一张是此刻。\n\n"
                    f"后台替你查过这些：（还没有笔记）\n\n他刚问：「{question}」"}]
        for _, b in strip:
            content.append({"type": "image_url",
                            "image_url": {"url": "data:image/jpeg;base64," + b, "detail": "low"}})
        d = _openai({"model": FRONT_MODEL,
                     "messages": [{"role": "system", "content": FAST_SYS},
                                  {"role": "user", "content": content}],
                     "response_format": {"type": "json_schema", "json_schema": {
                         "name": "fast", "strict": True, "schema": FAST_SCHEMA}}})
        fast = json.loads(d["choices"][0]["message"]["content"])
        if fast["enough"] and fast["answer"].strip():
            return {"text": fast["answer"].strip(), "citations": [],
                    "served": "看到过", "notes_at_hand": 0, "lookback_frames": len(strip)}

        j = _post(f"{self.backend}/answer", {
            "task_id": task["task_id"], "type": "query", "question": question,
            "anchor_sec": sec, "hint_level": task.get("hint_level"),
            "context_window_sec": task.get("context_window_sec"),
            "game": ctx.title, "container_id": ctx.container_id,
            "frame_jpeg_base64": ctx.frames.hi_res(sec)})
        return {"text": j.get("text", ""), "citations": j.get("citations") or [],
                "served": "得现查", "notes_at_hand": 0, "lookback_frames": len(strip)}
