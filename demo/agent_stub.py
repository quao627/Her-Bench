#!/usr/bin/env python3
"""Her-Bench agent stub — 演示"后台 agent"接入协议.

查看器在 Agent 模式下播到任务锚点时，会向配置的端点 POST 一个 JSON:

    {
      "task_id": "hff-p1-t03",
      "type": "query" | "proactive",
      "question": "...",              # proactive 型没有
      "anchor_sec": 900,
      "hint_level": "direction_only",
      "frame_jpeg_base64": "...",     # 锚点处的画面截图
      "transcript_excerpt": "..."     # 锚点前的转写片段（若有）
    }

端点返回:

    { "text": "回答内容", "citations": ["..."], "latency_ms": 1234 }

把这个文件换成真正的实现（调 GPT-live / 自家 agent / claude 都行），
协议不变，查看器就能直接测。

Usage:  python3 agent_stub.py [port]     # default 8787
"""
import json
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# 每个 task 一条罐头回答，演示协议用
CANNED = {}


def load_canned():
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "container.json")
    try:
        with open(path) as f:
            data = json.load(f)
        for t in data.get("tasks", []):
            demo = t.get("demo_agent_answer")
            if demo:
                CANNED[t["task_id"]] = demo
    except Exception as e:
        print("could not preload canned answers:", e)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        start = time.time()
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length))
        except Exception:
            payload = {}
        task_id = payload.get("task_id", "?")

        canned = CANNED.get(task_id)
        if canned:
            text = canned.get("text", "")
            citations = canned.get("citations", [])
        else:
            q = payload.get("question") or "(主动型任务，无提问)"
            text = f"[stub] 收到任务 {task_id}：{q} — 这里应接入真正的 agent。"
            citations = []

        time.sleep(0.6)  # 模拟思考延迟
        body = json.dumps({
            "text": text,
            "citations": citations,
            "latency_ms": int((time.time() - start) * 1000),
        }, ensure_ascii=False).encode()

        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[agent] {args[0] if args else ''}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    load_canned()
    print(f"agent stub listening on http://localhost:{port}  ({len(CANNED)} canned answers)")
    try:
        HTTPServer(("127.0.0.1", port), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
