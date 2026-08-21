#!/usr/bin/env python3
"""一路看着 + 后台提前查：自己定备料节奏，攒下的笔记一直带着。

备多密、什么时候备、备回来的怎么用，全是这个文件里的事，评测那一侧不管。
但代价它自己扛：备料这十几秒里视频照样往前走，中间的帧就错过了。想备得密，
就得接受看漏更多——这不是规则罚它，是真实场景本来就这样。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _client
import _front
from watching import LOOKBACK

BRIEF_EVERY = int(os.environ.get("HERBENCH_BRIEF_EVERY", "120"))   # 视频秒
BRIEF_FRAMES = [0, -5, -10, -20, -45, -90, -180]


class Agent:
    def start(self, sess):
        self.seen = {}
        self.notes = []
        self.next_brief = BRIEF_EVERY

    def _strip(self, now, offsets=LOOKBACK):
        out, seen = [], set()
        for off in offsets:
            s = now + off
            if s < 0:
                continue
            k = min(self.seen, key=lambda x: abs(x - s)) if self.seen else None
            if k is None or abs(k - s) > 30 or k in seen:
                continue
            seen.add(k)
            out.append((int(k), self.seen[k]))
        return sorted(out)

    def _brief(self, sess, t):
        """往后台扔一次备料。同步等着——这段时间视频会往前走，帧会漏，认了。"""
        frames = [{"offset_sec": s - t, "b64": b} for s, b in self._strip(t, BRIEF_FRAMES)]
        if not frames:
            return
        try:
            j = _front.backend("/research", {
                "frames": frames, "container_id": sess["container"],
                "current_sec": t, "game": sess["title"]})
        except Exception:
            return
        if j.get("noteworthy"):
            self.notes.append({"question": j["question"], "text": j["text"], "at": t})

    def on_tick(self, sess, r):
        t = int(r["t"])
        if r.get("frame"):
            self.seen[t] = r["frame"]

        ev = r.get("event")
        if ev:
            enough, text = _front.ask(ev["text"], self._strip(t), self.notes, sess["title"])
            if enough and text:
                return text
            j = _front.backend("/answer", {
                "task_id": "live", "type": "query", "question": ev["text"],
                "anchor_sec": t, "hint_level": "full",
                "game": sess["title"], "container_id": sess["container"],
                "frame_jpeg_base64": r.get("frame"),
                "recent_research": [{"question": n["question"], "text": n["text"]}
                                    for n in self.notes[-4:]]})
            return j.get("text", "")

        if t >= self.next_brief:
            self.next_brief = t + BRIEF_EVERY
            self._brief(sess, t)
        return None


if __name__ == "__main__":
    _client.loop(Agent())
