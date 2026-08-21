#!/usr/bin/env python3
"""一路看着，但没有后台备料：被问时手上有从开头到现在的画面，没有提前查好的资料。

夹在 reactive 和 prepared 中间。reactive → watching 多的是「看视频」，
watching → prepared 多的才是「后台提前查」。少了这一档，分差说不清是哪一半的功劳。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _client
import _front

# 一路看过来的等价物：按对数往回退取样，近处密远处稀，一直取到开头
LOOKBACK = [0, -10, -25, -50, -90, -150, -240, -360, -540, -800, -1200, -1800, -2600, -3600]


class Agent:
    def start(self, sess):
        self.seen = {}          # 视频秒 → 帧。它一路看着，自己攒下来

    def _strip(self, now):
        out, seen = [], set()
        for off in LOOKBACK:
            s = now + off
            if s < 0:
                continue
            k = min(self.seen, key=lambda x: abs(x - s)) if self.seen else None
            if k is None or abs(k - s) > 30 or k in seen:
                continue
            seen.add(k)
            out.append((int(k), self.seen[k]))
        return sorted(out)

    def on_tick(self, sess, r):
        t = int(r["t"])
        if r.get("frame"):
            self.seen[t] = r["frame"]
        ev = r.get("event")
        if not ev:
            return None
        enough, text = _front.ask(ev["text"], self._strip(t), [], sess["title"])
        if enough and text:
            return text
        j = _front.backend("/answer", {
            "task_id": "live", "type": "query", "question": ev["text"],
            "anchor_sec": t, "hint_level": "full",
            "game": sess["title"], "container_id": sess["container"],
            "frame_jpeg_base64": r.get("frame")})
        return j.get("text", "")


if __name__ == "__main__":
    _client.loop(Agent())
