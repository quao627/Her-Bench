#!/usr/bin/env python3
"""什么都不做，直到被问：不看画面，不备料，被问到才现查。

最底下那一档。跟 watching 比，少的是「一路看着」；跟 prepared 比，还少「后台提前查」。
三个连着看，分差才能归因到具体某一样上。
"""

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _client

BACKEND = os.environ.get("HERBENCH_BACKEND", "http://localhost:8787")


class Agent:
    def on_tick(self, sess, r):
        ev = r.get("event")
        if not ev:
            return None              # 没人问就什么都不干，连画面都不看
        body = {"task_id": "live", "type": "query", "question": ev["text"],
                "anchor_sec": int(r["t"]), "hint_level": "full",
                "game": sess["title"], "container_id": sess["container"],
                "frame_jpeg_base64": r.get("frame")}
        req = urllib.request.Request(f"{BACKEND}/answer", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=200) as resp:
            return json.load(resp).get("text", "")


if __name__ == "__main__":
    _client.loop(Agent())
