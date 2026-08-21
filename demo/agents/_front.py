"""前台那一半：拿着看过的画面和手上的笔记，判断够不够直接答。

watching 和 prepared 共用。reactive 没有前台判断，被问就直接扔给后台。
"""

import json
import os
import urllib.request

MODEL = os.environ.get("HERBENCH_FRONT_MODEL", "gpt-5.4")

SCHEMA = {"type": "object", "additionalProperties": False,
          "properties": {"enough": {"type": "boolean"}, "answer": {"type": "string"}},
          "required": ["enough", "answer"]}

SYS = """你是主播的陪玩搭子，正跟着他看直播。他刚问了你一句话。

你手上有：一路看过来的画面，以及后台替你查过的一些笔记（可能没有）。

先判断：**手上这些够不够直接答**。
够：笔记里正好有这个东西的准确细节，或者这是从看过的画面里直接知道的事。
不够：涉及具体数值、机制细节、剧情设定，而手上没有对得上的。
「我大概知道」不算够，不确定就去查。

注意你是一路看过来的，前面画面里发生过的事你都知道。他问「我刚拿到的这个东西」
这种，答案往往就在前面某一帧里，那不算不确定。

够的话直接把话说出来：口语，说清楚，别念稿子，不要「首先/其次/建议你」这类
书面词。绝不剧透他还没走到的地方。"""


def ask(question, strip, notes, title):
    """strip 是 [(视频秒, b64), ...]，按时间排好。返回 (够不够, 话)。"""
    ns = "\n".join(f"- Q: {n['question']}\n  A: {n['text']}" for n in notes[-6:]) or "（还没有笔记）"
    stamps = "、".join(f"{s//60}:{s%60:02d}" for s, _ in strip)
    content = [{"type": "text", "text":
                f"你在陪他玩：{title}\n\n"
                f"下面是你一路看过来的画面，时间点分别是 {stamps}，最后一张是此刻。\n\n"
                f"后台替你查过这些：\n{ns}\n\n他刚问：「{question}」"}]
    for _, b in strip:
        content.append({"type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64," + b, "detail": "low"}})
    body = {"model": MODEL,
            "messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": content}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "fast", "strict": True, "schema": SCHEMA}}}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    out = json.loads(d["choices"][0]["message"]["content"])
    return out["enough"], out["answer"].strip()


def backend(path, body, timeout=200):
    url = os.environ.get("HERBENCH_BACKEND", "http://localhost:8787") + path
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)
