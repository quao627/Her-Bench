"""跟评测那一侧说话的最小客户端。三个 agent 共用。

这个文件里没有任何评测的知识——它不知道有题、不知道判分标准，只知道怎么发 HTTP。
"""

import json
import os
import urllib.request

WORLD = os.environ.get("HERBENCH_WORLD", "http://127.0.0.1:8899")


def _call(path, body=None, timeout=300):
    data = json.dumps(body or {}).encode() if body is not None else None
    req = urllib.request.Request(WORLD + path, data=data,
                                 method="POST" if data is not None else "GET",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def session():
    return _call("/session")


def tick():
    return _call("/tick", {})


def say(text):
    return _call("/say", {"text": text})


def loop(agent):
    """通用主循环。agent 只要实现 on_tick(sess, r) 返回要说的话或 None。"""
    sess = session()
    if hasattr(agent, "start"):
        agent.start(sess)
    while True:
        r = tick()
        if r.get("done"):
            break
        out = agent.on_tick(sess, r)
        if out:
            say(out)
    if hasattr(agent, "finish"):
        agent.finish(sess)
