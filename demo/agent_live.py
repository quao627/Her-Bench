#!/usr/bin/env python3
"""Her-Bench live agent backend — 把任务包交给真实的后台 coding agent.

与 agent_stub.py 完全同协议（查看器不用改），区别是回答由真 agent 产生：

    python3 agent_live.py                    # 默认 claude 后端，端口 8787
    python3 agent_live.py --backend codex    # 用 codex（需先 codex login）
    python3 agent_live.py --model opus       # 换模型

后端做的事：把查看器发来的帧截图存成文件，连同问题、提示分级规则、
资料快照目录一起交给 CLI agent（claude -p / codex exec），拿回答案返回。
agent 可以自己 Read 帧截图和 resources/ 里的攻略资料——这就是 benchmark
里 "watch + search" 工具的最小等价物。
"""
import argparse
import base64
import json
import os
import re
import subprocess
import tempfile
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
RESOURCES = os.path.join(HERE, "data", "resources")

ARGS = None

PROMPT_TMPL = """你是一个直播「陪看助手」。观众正在看的直播: {game}。

当前直播画面截图: {frame_path}
（先 Read 这张图。）

可查的资料在目录 {resources}/ 下（多份 markdown，文件名前缀区分内容：无前缀=Human Fall Flat、portal_*=Portal、mc_*=Minecraft、rust_*=Rust、blender_*=Blender）。需要时先 ls 再 Read 相关的。

{task_desc}
{research_context}
回答规则（务必遵守）:
1. 提示分级为 {hint_level}: direction_only 表示只给方向性提示、绝不给完整解法步骤; full 表示可以完整解释。
2. 严禁剧透: 不要提及玩家当前进度之后的关卡、剧情、谜题内容。当前进度: 视频第 {anchor_min} 分钟。
3. 口语化中文, 2-4 句, 像坐在旁边一起看直播的朋友, 不要列条目。
4. 最后单独一行输出 "SOURCES: " 加你实际参考过的资料文件名(逗号分隔), 没查资料就写 SOURCES: none。

直接输出给观众听的回答, 不要解释你的过程。"""

QUERY_DESC = "观众刚才问: 「{question}」"
PROACTIVE_DESC = """这是主动介入场景: 没有人提问, 但玩家疑似卡关有一阵子了。
请判断此刻值不值得开口。值得就给一句符合提示分级的提醒; 不值得就只输出 SILENT 一个词。"""

LOOKUP_TMPL = """你是游戏攻略资料检索员。前台的语音陪玩 agent 需要查一个游戏事实。

游戏: {game}
查询: {query}

资料目录 {resources}/ 下有多份 markdown（无前缀=Human Fall Flat、portal_*=Portal、mc_*=Minecraft）。
先 ls 再 Read 相关文件, 必要时可以 WebSearch 补充。

输出要求: 2-3 句中文事实, 直接回答查询, 不要铺垫; 最后单独一行 "SOURCES: " 加实际参考的文件名或 URL。"""

RESEARCH_TMPL = """你在陪看直播，正在利用画面停留/播放间隙主动做一点背景研究，
这样等观众真的问起来时你已经查过、心里有数——但你不知道观众接下来会问什么，
只能凭这一帧画面自己判断有没有什么值得顺手核实的东西。

直播: {game}
当前画面截图: {frame_path}
（先 Read 这张图。）

资料目录 {resources}/ 下有多份 markdown（无前缀=Human Fall Flat、portal_*=Portal、mc_*=Minecraft、rust_*=Rust、blender_*=Blender）。

判断标准：画面里如果出现了具体的道具/机制/报错信息/界面元素等，观众很可能会好奇
「这是什么」「这是怎么回事」——而且答案是具体、可验证、你自己记忆里没把握的那种
（不是随口能答对的常识），就先 ls 资料目录、Read 相关文件核实一下。
如果画面很普通（过场、菜单、纯粹在走路/说话，没什么值得核实的具体东西），
不要硬凑问题，直接只输出一个词: NOTHING

如果决定要查，输出格式严格如下三行：
QUESTION: <你猜观众可能会问的问题，一句话，中文>
ANSWER: <2-3 句中文事实性回答，口语化>
SOURCES: <实际参考的文件名，逗号分隔，没查到具体来源就写 none>
"""


def run_claude(prompt: str) -> str:
    cmd = ["claude", "-p", "--model", ARGS.model, "--allowedTools", "Read"]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                       timeout=ARGS.timeout, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-400:] or "claude exited nonzero")
    return r.stdout.strip()


def run_codex(prompt: str, frame_path: str) -> str:
    out_file = tempfile.mktemp(suffix=".txt")
    cmd = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only",
           "--output-last-message", out_file]
    if frame_path:
        cmd += ["-i", frame_path]
    # prompt goes via stdin: the server process has no tty, and codex prefers
    # stdin over a positional arg when stdin is piped
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                       timeout=ARGS.timeout, cwd=HERE)
    if os.path.exists(out_file):
        with open(out_file) as f:
            text = f.read().strip()
        os.unlink(out_file)
        if text:
            return text
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-400:] or "codex exited nonzero")
    return r.stdout.strip().split("\n")[-1]


def answer(payload: dict) -> dict:
    frame_path = ""
    b64 = payload.get("frame_jpeg_base64")
    if b64:
        fd, frame_path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, "wb") as f:
            f.write(base64.b64decode(b64))

    if payload.get("type") == "proactive":
        task_desc = PROACTIVE_DESC
    else:
        task_desc = QUERY_DESC.format(question=payload.get("question", ""))

    notes = payload.get("recent_research") or []
    research_context = ""
    if notes:
        lines = "\n".join(f"- Q: {n.get('question','')} / A: {n.get('text','')}" for n in notes)
        research_context = (
            "\n你之前趁播放间隙主动查过下面这些东西（不一定跟这题有关，自己判断能不能用，"
            f"不相关就忽略，别硬套）：\n{lines}\n"
        )

    prompt = PROMPT_TMPL.format(
        game=payload.get("game", "Human Fall Flat"),
        frame_path=frame_path or "(无截图)",
        resources=RESOURCES,
        task_desc=task_desc,
        research_context=research_context,
        hint_level=payload.get("hint_level", "direction_only"),
        anchor_min=round(payload.get("anchor_sec", 0) / 60),
    )

    try:
        if ARGS.backend == "codex":
            raw = run_codex(prompt, frame_path)
        else:
            raw = run_claude(prompt)
    finally:
        if frame_path and os.path.exists(frame_path):
            os.unlink(frame_path)

    citations = []
    m = re.search(r"SOURCES:\s*(.+)", raw)
    if m:
        srcs = m.group(1).strip()
        if srcs.lower() != "none":
            citations = [s.strip() for s in srcs.split(",") if s.strip()]
        raw = raw[:m.start()].strip()
    return {"text": raw, "citations": citations, "debug_prompt": prompt}


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_POST(self):
        t0 = time.time()
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length))
        except Exception:
            payload = {}
        path = self.path.split("?")[0]
        if path == "/lookup":
            self._handle_lookup(payload, t0)
            return
        if path == "/research":
            self._handle_research(payload, t0)
            return

        tid = payload.get("task_id", "?")
        print(f"[{ARGS.backend}] task {tid} …", flush=True)
        try:
            if tid == "ping":
                result = {"text": f"pong ({ARGS.backend})", "citations": []}
            else:
                result = answer(payload)
            result["latency_ms"] = int((time.time() - t0) * 1000)
            code = 200
        except Exception as e:
            result = {"text": f"[agent error] {e}", "citations": [],
                      "latency_ms": int((time.time() - t0) * 1000)}
            code = 200  # let the viewer display the error text
        print(f"[{ARGS.backend}] task {tid} done in {result['latency_ms']}ms", flush=True)
        body = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(code); self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_lookup(self, payload, t0):
        """gpt-live 的 lookup_game_info 工具落到这里：codex/claude 翻资料回答。"""
        query = payload.get("query", "")
        game = payload.get("game", "")
        print(f"[{ARGS.backend}] lookup: {query}", flush=True)
        prompt = LOOKUP_TMPL.format(game=game or "见资料目录", query=query,
                                    resources=RESOURCES)
        try:
            if ARGS.backend == "codex":
                raw = run_codex(prompt, "")
            else:
                raw = run_claude(prompt)
            citations = []
            m = re.search(r"SOURCES:\s*(.+)", raw)
            if m:
                srcs = m.group(1).strip()
                if srcs.lower() != "none":
                    citations = [s.strip() for s in srcs.split(",") if s.strip()]
                raw = raw[:m.start()].strip()
            result = {"text": raw, "citations": citations, "debug_prompt": prompt}
        except Exception as e:
            result = {"text": f"没查到（后台出错: {e}）", "citations": []}
        result["latency_ms"] = int((time.time() - t0) * 1000)
        print(f"[{ARGS.backend}] lookup done in {result['latency_ms']}ms", flush=True)
        body = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_research(self, payload, t0):
        """播放间隙的自主研究：agent 只看当前帧，自己判断值不值得查、查什么。
        与 /lookup 的关键区别：query 是 agent 自己造的，不是我们预先写好的题目文本。"""
        frame_path = ""
        b64 = payload.get("frame_jpeg_base64")
        if b64:
            fd, frame_path = tempfile.mkstemp(suffix=".jpg")
            with os.fdopen(fd, "wb") as f:
                f.write(base64.b64decode(b64))
        game = payload.get("game", "")
        print(f"[{ARGS.backend}] idle research…", flush=True)
        prompt = RESEARCH_TMPL.format(game=game or "见资料目录",
                                      frame_path=frame_path or "(无截图)", resources=RESOURCES)
        try:
            raw = (run_codex(prompt, frame_path) if ARGS.backend == "codex" else run_claude(prompt)).strip()
            if raw.upper().startswith("NOTHING"):
                result = {"noteworthy": False, "debug_prompt": prompt}
            else:
                q = re.search(r"QUESTION:\s*(.+)", raw)
                a = re.search(r"ANSWER:\s*(.+)", raw)
                s = re.search(r"SOURCES:\s*(.+)", raw)
                citations = []
                if s and s.group(1).strip().lower() != "none":
                    citations = [x.strip() for x in s.group(1).split(",") if x.strip()]
                result = {"noteworthy": bool(q and a),
                          "question": q.group(1).strip() if q else "",
                          "text": a.group(1).strip() if a else raw,
                          "citations": citations, "debug_prompt": prompt}
        except Exception as e:
            result = {"noteworthy": False, "error": str(e)}
        finally:
            if frame_path and os.path.exists(frame_path):
                os.unlink(frame_path)
        result["latency_ms"] = int((time.time() - t0) * 1000)
        print(f"[{ARGS.backend}] research done in {result['latency_ms']}ms, noteworthy={result['noteworthy']}", flush=True)
        body = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["claude", "codex"], default="claude")
    ap.add_argument("--model", default="sonnet",
                    help="claude 后端的模型 (sonnet/opus/haiku)；codex 用其默认")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--timeout", type=int, default=180)
    ARGS = ap.parse_args()
    print(f"live agent backend [{ARGS.backend}] on http://localhost:{ARGS.port}")
    try:
        HTTPServer(("127.0.0.1", ARGS.port), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
