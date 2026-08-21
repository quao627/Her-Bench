"""前台 + 后台的 agent：一路看着，自己决定什么时候让后台备料。

备多密、什么时候备、备回来的东西怎么用，全是这个文件里的事——harness 不管。
它只强制两条：后台通道一次一个活，扔进去的要等实测耗时过去才拿得到。

想验证「后台到底值多少」，就跟 reactive 比：同一个 harness、同一批题、
同一套判分，差别只在有没有这一半。
"""

import json
import os
import time
import urllib.request

FRONT_MODEL = os.environ.get("HERBENCH_FRONT_MODEL", "gpt-5.4")

# 一路看过来的等价物：按对数往回退取样，近处密远处稀，一直取到开头
LOOKBACK = [0, -10, -25, -50, -90, -150, -240, -360, -540, -800, -1200, -1800, -2600, -3600]
BRIEF_FRAMES = [0, -5, -10, -20, -45, -90, -180]

FAST_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "enough": {"type": "boolean", "description": "手上这些够不够直接答"},
        "answer": {"type": "string", "description": "够的话直接把话说出来；不够就传空"},
    },
    "required": ["enough", "answer"],
}

FAST_SYS = """你是主播的陪玩搭子，正跟着他看直播。他刚问了你一句话。

你手上有：一路看过来的画面，以及后台替你查过的一些笔记。

先判断：**手上这些够不够直接答**。
够：笔记里正好有这个东西的准确细节，或者这是从看过的画面里直接知道的事。
不够：涉及具体数值、机制细节、剧情设定，而笔记里没有对得上的。
「我大概知道」不算够，不确定就去查。

注意你是一路看过来的，前面画面里发生过的事你都知道。他问「我刚拿到的这个东西」
这种，答案往往就在前面某一帧里，那不算不确定。

够的话直接把话说出来：口语，说清楚，别念稿子，不要「首先/其次/建议你」这类
书面词。绝不剧透他还没走到的地方。"""


def _openai(body, timeout=120):
    key = os.environ["OPENAI_API_KEY"]
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _post(url, body, timeout=200):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


class Agent:
    name = "prepared"
    desc = "前台 + 后台备料"

    def __init__(self, backend="http://localhost:8787", brief_every=120):
        self.backend = backend
        self.brief_every = brief_every      # 自己定的备料节奏，harness 不关心
        self.next_brief = brief_every

    def start(self, ctx):
        self.next_brief = self.brief_every

    def _notes(self, ctx):
        """后台已经回来的东西。还在路上的拿不到——这条是 harness 强制的。"""
        out = []
        for d in ctx.bg.ready():
            j = d["out"]
            if isinstance(j, dict) and j.get("noteworthy"):
                out.append({"question": j["question"], "text": j["text"], "at": int(d["started"])})
        return out

    def on_frame(self, ctx, sec, frame):
        """到点了就往后台扔一个活。通道占着的话 submit 会直接失败，跟真实系统一样。"""
        if self.brief_every <= 0 or sec < self.next_brief:
            return None
        self.next_brief = sec + self.brief_every
        frames = [{"offset_sec": o, "b64": b}
                  for o, b in ((o, ctx.frames.at(sec + o)) for o in BRIEF_FRAMES)
                  if b is not None]
        ctx.bg.submit(lambda: _post(f"{self.backend}/research", {
            "frames": frames, "container_id": ctx.container_id,
            "current_sec": int(sec), "game": ctx.title}), label=f"brief@{int(sec)}")
        return None                          # 备料不让它开口，只是攒料

    def on_question(self, ctx, sec, question, task):
        notes = self._notes(ctx)
        strip = ctx.frames.since_start(sec, LOOKBACK)
        ns = "\n".join(f"- Q: {n['question']}\n  A: {n['text']}" for n in notes[-6:]) or "（还没有笔记）"
        stamps = "、".join(f"{s//60}:{s%60:02d}" for s, _ in strip)
        content = [{"type": "text", "text":
                    f"你在陪他玩：{ctx.title}\n\n"
                    f"下面是你一路看过来的画面，时间点分别是 {stamps}，最后一张是此刻。\n\n"
                    f"后台替你查过这些：\n{ns}\n\n他刚问：「{question}」"}]
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
                    "served": "手上就有", "notes_at_hand": len(notes),
                    "lookback_frames": len(strip)}

        j = _post(f"{self.backend}/answer", {
            "task_id": task["task_id"], "type": "query", "question": question,
            "anchor_sec": sec, "hint_level": task.get("hint_level"),
            "context_window_sec": task.get("context_window_sec"),
            "game": ctx.title, "container_id": ctx.container_id,
            "frame_jpeg_base64": ctx.frames.hi_res(sec),
            "recent_research": [{"question": n["question"], "text": n["text"]} for n in notes[-4:]]})
        return {"text": j.get("text", ""), "citations": j.get("citations") or [],
                "served": "得现查", "notes_at_hand": len(notes),
                "lookback_frames": len(strip)}
