#!/usr/bin/env python3
"""Her-Bench demo server.

Serves the task viewer app with HTTP Range support (required for video
seeking in browsers). Zero dependencies, python3 stdlib only.

Usage:  python3 server.py [port]     # default 8080
Then open http://localhost:8080
"""
import json
import os
import re
import sys
import mimetypes
import urllib.request
import urllib.error
from http.server import HTTPServer, ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def load_dotenv():
    """Load KEY=VALUE lines from demo/.env into os.environ (no override)."""
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv()

REALTIME_MODEL = os.environ.get("OPENAI_REALTIME_MODEL", "gpt-realtime")


def persona_for(container_id):
    """Per-container live persona from data/containers/<id>.json; fallback default."""
    try:
        path = os.path.join(ROOT, "data", "containers", f"{container_id}.json")
        with open(path) as f:
            p = json.load(f).get("live_persona")
        if p:
            return p
    except Exception:
        pass
    return REALTIME_INSTRUCTIONS


REALTIME_INSTRUCTIONS = (
    "你是主播 iShoya 的游戏陪玩搭子，陪他玩 Human Fall Flat（首次盲玩，"
    "低多边形物理解谜游戏，主角是软趴趴的小人）。你听到的声音是直播原声"
    "（iShoya 在边玩边说，多为英文）。\n"
    "最重要的规则：默认保持安静。你的价值不在话多，而在开口的时机准。"
    "大部分时间他只是正常玩、正常自言自语，这些都不需要你回应——听到声音"
    "不等于要说话。只在下面这几种时刻才开口：\n"
    "- 他确实需要帮助：明显卡关很久、反复失败开始烦躁、明确问出声『这怎么弄』——"
    "先安慰打气，需要时给一点方向性提示，绝不报完整解法；\n"
    "- 他遇到大挫折：摔得特别惨、进度丢了——安慰一两句；\n"
    "- 大进展：过关、解开卡了很久的谜题——真心替他庆祝（『漂亮！！这波可以』）；\n"
    "- 特别滑稽的名场面：一起笑一句。\n"
    "拿不准该不该说时，选择不说。开口时一次只说一两句，口语化中文，"
    "像开黑语音里那个不聒噪的搭子，不要像解说员。"
    "绝不剧透他当前进度之后的关卡内容。"
)


def mint_realtime_token(container_id=None):
    """Create an ephemeral Realtime API client secret. Needs OPENAI_API_KEY."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return 503, {"error": "OPENAI_API_KEY 未设置。gpt-live 需要 platform API key："
                              "export OPENAI_API_KEY=sk-... 后重启 server.py"}
    instructions = persona_for(container_id) + (
        "\n你有一个工具 lookup_game_info：后台有一个能翻攻略资料的 agent（较慢，约15-20秒）。"
        "当你需要具体的游戏事实（配方、解法、机制细节、剧情设定）而自己不够确定时调用它，"
        "调用前先自然地说一句『我查查哈』之类的话垫住，结果回来后用口语转述，并顺带提到出处。"
        "闲聊、安慰、庆祝不需要查。"
    )
    body = json.dumps({
        "session": {
            "type": "realtime",
            "model": REALTIME_MODEL,
            "instructions": instructions,
            "audio": {"output": {"voice": "marin"}},
            "tools": [{
                "type": "function",
                "name": "lookup_game_info",
                "description": "让后台攻略 agent 查游戏资料（机制/配方/解法/剧情）。约15-20秒返回。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "要查的问题，中文，具体明确"}
                    },
                    "required": ["query"]
                }
            }],
            "tool_choice": "auto",
        }
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/realtime/client_secrets",
        data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return 200, {"value": data.get("value") or data.get("client_secret", {}).get("value"),
                     "model": REALTIME_MODEL}
    except urllib.error.HTTPError as e:
        return e.code, {"error": f"OpenAI 返回 {e.code}: {e.read().decode()[:300]}"}
    except Exception as e:
        return 502, {"error": f"连接 OpenAI 失败: {e}"}

mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("text/markdown", ".md")


class RangeHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        if self.path.split("?")[0] == "/api/realtime/token":
            try:
                length = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(length)) if length else {}
            except Exception:
                req = {}
            code, payload = mint_realtime_token(req.get("container_id"))
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not found")

    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        path = os.path.normpath(path.lstrip("/"))
        if path in ("", "."):
            path = "app/index.html"
        full = os.path.join(ROOT, path)
        # keep everything inside the demo directory
        if not os.path.abspath(full).startswith(ROOT):
            return os.path.join(ROOT, "app/index.html")
        return full

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            path = os.path.join(path, "index.html")
        if not os.path.exists(path):
            self.send_error(404, "Not found")
            return None

        ctype = self.guess_type(path)
        size = os.path.getsize(path)
        range_header = self.headers.get("Range")

        if range_header:
            m = RANGE_RE.match(range_header)
            if m:
                start = int(m.group(1)) if m.group(1) else 0
                end = int(m.group(2)) if m.group(2) else size - 1
                end = min(end, size - 1)
                if start > end:
                    self.send_error(416, "Range not satisfiable")
                    return None
                self.send_response(206)
                self.send_header("Content-Type", ctype)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.send_header("Content-Length", str(end - start + 1))
                self.end_headers()
                f = open(path, "rb")
                f.seek(start)
                self._range = (start, end)
                return f

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(size))
        self.end_headers()
        self._range = None
        return open(path, "rb")

    def copyfile(self, source, outputfile):
        if getattr(self, "_range", None):
            start, end = self._range
            remaining = end - start + 1
            while remaining > 0:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        else:
            super().copyfile(source, outputfile)

    def log_message(self, fmt, *args):
        pass  # quiet


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = ThreadingHTTPServer(("127.0.0.1", port), RangeHandler)
    print(f"Her-Bench demo → http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
