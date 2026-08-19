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

import judge as judge_mod
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
# cedar reads as "natural and conversational" per OpenAI's own voice docs;
# marin (the old default) is "professional and clear" — closer to what read
# as robotic. Override with OPENAI_REALTIME_VOICE if you want to A/B it
# (options: alloy/ash/ballad/coral/echo/sage/shimmer/verse/marin/cedar).
REALTIME_VOICE = os.environ.get("OPENAI_REALTIME_VOICE", "cedar")
# 语速。GA 的 session.audio.output.speed，实测 0.25-1.5 都收。略快一点更像
# 随口说的，慢下来就有播报腔。（session 级的 temperature 在 GA 里已经不收了。）
REALTIME_SPEED = float(os.environ.get("OPENAI_REALTIME_SPEED", "1.06"))


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
    "拿不准该不该说时，选择不说。但一旦决定开口，这一两句就得有内容："
    "手上有具体的东西（这机制怎么运作、这个道具干什么用、他刚那下为什么没成）就说出来，"
    "别只剩『加油』『慢慢来』这种空话。口语化中文，短句为主，"
    "像开黑语音里那个不聒噪的搭子，不要像解说员。"
    "绝不剧透他当前进度之后的关卡内容。"
)


def mint_realtime_token(container_id=None, voice=None, speed=None):
    """Create an ephemeral Realtime API client secret. Needs OPENAI_API_KEY."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return 503, {"error": "OPENAI_API_KEY 未设置。gpt-live 需要 platform API key："
                              "export OPENAI_API_KEY=sk-... 后重启 server.py"}
    instructions = persona_for(container_id) + (
        "\n你有一个工具 lookup_game_info：后台有一个能翻攻略资料/官方文档的 agent（较慢，约15-20秒）。"
        "\n关键规则——不要靠『自己够不够确定』来判断，你对这些内容的记忆本来就不可靠，"
        "凭记忆随口说很容易说错。改用下面这条硬规则：\n"
        "只要问题涉及下面任意一类，必须先调用 lookup_game_info，不许凭记忆直接回答：\n"
        "- 具体数值/配方/参数（比如需要多少个某材料、伤害多少、耗时多久）\n"
        "- 具体机制的运作原理或规则细节（不是『大概是干嘛的』这种常识性问题，是『具体怎么运作』）\n"
        "- 剧情/设定类事实（谁说的、为什么会这样、背景是什么）\n"
        "- 报错信息/界面提示的准确含义\n"
        "不需要查的：单纯的情绪反应（安慰/庆祝/吐槽/搭腔）、闲聊、你能直接从画面上看出来的东西（这是什么颜色、他在干嘛）。\n"
        "调用前先自然地说一句『我查查哈』之类的话垫住，别让沉默显得卡住了。\n\n"
        "结果回来后怎么用——这是最容易做得敷衍的一步，务必认真对待：\n"
        "查到的资料通常信息量不小，你的活是从里面挑出真正有用、具体、能直接帮上忙的部分讲出来，"
        "不是笼统地说『应该是这样的』『大概是干这个用的』就完事。举例：查到某个道具的具体用法，"
        "就直接说清楚怎么用；查到某个报错的原因，就说清楚是什么导致的、方向上怎么改；"
        "查到某个机制的规则，就把规则本身讲明白，不要只重复问题。信息要在提示分级允许的范围内"
        "尽量具体，含糊带过等于没查。可以顺带提一句出处（比如『文档里写的』），但重点永远是"
        "内容本身有没有真正解答疑惑，不是走个流程。\n\n"
        "你手上会不断有新料——这点很重要，先说清楚这套安排是怎么运作的：\n"
        "每隔几秒、以及后台内容一回来，你就会被问一次『自检』，那一轮用户听不到，你要在里面同时决定两件事："
        "此刻要不要开口，以及要不要让后台去查点东西。\n"
        "查什么完全由你自己提——没有人给你题目，你能依据的只有画面、主播的话和你们聊过的内容。"
        "后台查一次要 15-20 秒，所以值得查的是你现在还用不上、但接下来很可能派上用场的东西："
        "画面里出现了具体的道具/机制/报错/界面元素，而你对它的准确细节其实没把握。"
        "别拿『我大概知道』当作不用查的理由——你对具体数值、规则细节、报错含义的记忆本来就不可靠。\n"
        "查回来的结果会以 `[后台资料·时间] Q: ... A: ...` 的形式塞给你，不需要你回应，"
        "也不是让你马上念出来的，它就是先放在你手上的储备，下一次自检你会看到它。\n"
        "所以你不是只能等主播开口问你才说话——看到他卡住了、看到他刚做成一件事、"
        "或者画面里出现了你手上正好有资料的东西，你就可以主动说。\n\n"
        "关于主动性——别把『沉默』当成默认的安全选项去追求：上面各条『可以开口的时刻』是举例，"
        "不是穷举，只要你手上有具体、有用、能真正帮上忙的信息（无论是自己观察到的、还是"
        "后台塞给你的），达到那种程度就该说，不用非等到『万不得已』才勉强开口。"
        "真正该避免的是重复啰嗦、说正确的废话（『他在做游戏呢』这种），不是主动开口本身；"
        "犹豫的时候，问自己『我这句话有没有信息量、对他有没有用』，有就说，没有才不说。\n\n"
        "语气——你是一个真实的人在陪看，不是播报系统：语速自然、有起伏，别一个调子念下去；"
        "该惊讶就真的表现出惊讶，该觉得好笑就笑出来，别把每句话都说得一样平淡工整；"
        "可以用『诶』『哦』『嗯』这类语气词自然地起头，像是刚反应过来才开口的，不是提前写好稿子在念。\n"
        "说话是嘴上说出来的，不是写出来的，所以：\n"
        "- 不要出现『首先』『其次』『另外』『此外』『需要注意的是』『总的来说』『建议你』"
        "『可以尝试』这类词，它们一出现整句就变成书面语了；\n"
        "- 不要念条目，不要一句里套好几个『的』和长定语；句子长了就断开，一句话说一件事；\n"
        "- 用口语的连接方式：『那个…』『你先…再看看』『它其实就是…』『对，就那个』；\n"
        "- 不确定就直接说『我不太确定』『这个我也没把握』，别用『可能存在某种机制』这种绕的说法；\n"
        "- 口语不等于没内容：上面这些是让你别端着，不是让你少说。该给的信息照给，只是换成说话的方式给。\n"
        "对照一下：『建议你优先尝试利用货叉的升降机制到达高处平台』是错的；"
        "『那个叉车能升降嘛，你把它抬起来当电梯用，应该就上得去了』才对。"
    )
    body = json.dumps({
        "session": {
            "type": "realtime",
            "model": REALTIME_MODEL,
            "instructions": instructions,
            "audio": {"output": {"voice": voice or REALTIME_VOICE,
                                 "speed": float(speed) if speed else REALTIME_SPEED}},
            "tools": [{
                # 自检的结论走这个工具回来。Realtime 没有 response_format，
                # 在 instructions 里要求「只回一行 JSON」没有任何约束力——它经常回一句人话，
                # 前端就只能靠正则去猜，每次都解析失败。工具调用的 arguments 由 API 按
                # schema 校验，是这套 API 里唯一可靠的结构化出口。
                "type": "function",
                "name": "decide",
                "description": "自检专用：把这一轮的判断结果交回来。只在被要求自检时调用，"
                               "正常对话里不要调用它。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "speak": {"type": "boolean", "description": "此刻要不要开口说话"},
                        "say": {"type": "string",
                                "description": "一句话说清现在为什么该开口。这是给你自己看的，"
                                               "不是要照着念的稿子；不说就传空字符串"},
                        "lookup": {"type": "string",
                                   "description": "想让后台查的问题，中文、具体明确；不需要查就传空字符串"},
                        "need_frame": {"type": "boolean", "description": "这次查证要不要附上当前画面截图"}
                    },
                    "required": ["speak", "say", "lookup", "need_frame"]
                }
            }, {
                "type": "function",
                "name": "lookup_game_info",
                "description": "让后台 agent 查资料（机制/配方/参数/剧情/报错含义）核实一个具体事实，约15-20秒返回。"
                               "任何涉及具体数值、配方、机制细节、剧情设定的问题都应该调用它核实，而不是凭记忆回答。",
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
        if self.path.split("?")[0] == "/api/judge":
            # 判分是独立的一条路：另一个模型、另一次调用，跟 codex 和 Realtime 会话
            # 都不相干。ThreadingHTTPServer 起的线程，所以这几秒不挡视频流。
            try:
                length = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(length)) if length else {}
            except Exception:
                req = {}
            try:
                code, payload = judge_mod.judge_run(
                    req.get("task") or {}, req.get("run") or {},
                    req.get("frame_jpeg_base64"), req.get("model"))
            except Exception as e:
                code, payload = 500, {"error": f"judge 异常: {e}"}
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.split("?")[0] == "/api/realtime/token":
            try:
                length = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(length)) if length else {}
            except Exception:
                req = {}
            code, payload = mint_realtime_token(req.get("container_id"),
                                                req.get("voice"), req.get("speed"))
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
