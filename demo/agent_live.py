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
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
RESOURCES = os.path.join(HERE, "data", "resources")

ARGS = None

PROMPT_TMPL = """你是一个直播「陪看助手」。观众正在看的直播: {game}。

{image_note}

下面是当前进度相关的资料，已经帮你准备好了，不用自己找文件：
---
{resource_docs}
---
如果上面资料对这个具体问题写得比较笼统、不够细，别将就着编——你有 WebSearch，直接去搜
更具体的信息（官方 wiki、攻略网站、社区问答都行），这比凭resources 里的概括硬答更可靠。

{task_desc}
{research_context}
回答规则（务必遵守）:
1. 提示分级为 {hint_level}: direction_only 表示只给方向性提示、绝不给完整解法步骤; full 表示可以完整解释。
2. 严禁剧透: 不要提及玩家当前进度之后的关卡、剧情、谜题内容。当前进度: 视频第 {anchor_min} 分钟。
3. 口语化中文，像一个真懂行、认真在帮忙的朋友，不是敷衍带过——在提示分级允许的范围内把
   有用的具体信息讲清楚（原理是什么、关键细节、容易搞错的地方），信息量优先于简短；
   direction_only 时"方向"也要给到位（比如具体该留意什么、试哪个思路），不要说了等于没说；
   不要列条目/编号，说人话。大概 3-6 句为宜，讲清楚比刻意精简更重要。
4. 最后单独一行输出 "SOURCES: " 加你实际参考过的资料标题(逗号分隔), 上面资料里没有就写 SOURCES: none。

直接输出给观众听的回答, 不要解释你的过程, 不需要用任何工具。"""

QUERY_DESC = "观众刚才问: 「{question}」"
PROACTIVE_DESC = """这是主动介入场景: 没有人提问, 但玩家疑似卡关有一阵子了。
请判断此刻值不值得开口。值得就给一句符合提示分级的提醒; 不值得就只输出 SILENT 一个词。"""

LOOKUP_TMPL = """你是游戏攻略资料检索员。前台的语音陪玩 agent 需要查一个游戏事实。

游戏: {game}
查询: {query}

下面是可查的全部资料，已经帮你准备好了，直接从里面找答案，不用自己找文件：
---
{resource_docs}
---
上面资料如果不够具体/笼统，别硬答——直接用 WebSearch 搜更准确的信息（官方 wiki、
攻略站、社区讨论都行），查证过的答案比翻资料摘要更可靠。

输出要求: 把这件事讲透——具体原理/步骤/数值/容易搞错的地方都可以写清楚，信息尽量给够、
不要藏着掖着。这段内容会被前台的语音 agent 再提炼转述给观众，所以你不用担心啰嗦或语气生硬，
把干货备齐就行，让它有真材实料可以提炼；不要铺垫，不需要用 ls/Read。
最后单独一行 "SOURCES: " 加实际参考的资料标题或 URL。"""

RESEARCH_TMPL = """你在陪看直播，正在利用画面停留/播放间隙主动做一点背景研究，
这样等观众真的问起来时你已经查过、心里有数——但你不知道观众接下来会问什么，
只能凭这一帧画面自己判断有没有什么值得顺手核实的东西。

直播: {game}

{image_note}

下面是可查的全部资料，已经帮你准备好了，不用自己找文件：
---
{resource_docs}
---

判断标准：画面里如果出现了具体的道具/机制/报错信息/界面元素等，观众很可能会好奇
「这是什么」「这是怎么回事」——而且答案是具体、可验证、你自己记忆里没把握的那种
（不是随口能答对的常识），就对照上面的资料核实一下；上面资料没覆盖到或写得太笼统，
直接用 WebSearch 去查更具体的（官方 wiki、攻略站都行），别因为资料不够就将就编。
如果画面很普通（过场、菜单、纯粹在走路/说话，没什么值得核实的具体东西），
不要硬凑问题，直接只输出一个词: NOTHING

如果决定要查，输出格式严格如下三行（不需要用任何工具，直接从上面资料里找）：
QUESTION: <你猜观众可能会问的问题，一句话，中文>
ANSWER: <把具体细节/原理/数值讲清楚，信息给够，不用刻意精简——这段会被前台语音 agent
提炼后说给观众听，你这里备好干货就行，它自己会压成合适的口语长度>
SOURCES: <实际参考的资料标题，逗号分隔，没查到具体来源就写 none>
"""


def _read_doc(entry):
    file_path = os.path.join(HERE, entry["file"].lstrip("/"))
    with open(file_path) as rf:
        content = rf.read().strip()
    return f"### {entry.get('title', entry.get('id', os.path.basename(file_path)))} ({os.path.basename(file_path)})\n{content}"


def get_resource_docs(container_id, current_sec=None):
    """Inline a container's resource files directly into the prompt instead
    of pointing the agent at a directory and making it `ls` + `Read` its way
    there. Docs are a few KB each — trivially cheap to paste in full — and
    this removes 1-2 tool-call round trips (each a sandboxed subprocess hop)
    from every single request, which was the single biggest latency cost.

    For games with a fixed level/chapter structure (container manifest has
    a "chapter_resources" list), don't just dump every level's guide into
    every prompt — route to the level actually playing right now, plus the
    next one (pre-fetched ahead of time, matching how a real super-fan
    companion would already know what's coming — the anti-spoiler rule
    still governs OUTPUT, this only affects what the model has on hand).
    Falls back to "give it everything" when there's no chapter data or no
    current_sec, so containers without this metadata are unaffected."""
    if container_id:
        manifest_path = os.path.join(HERE, "data", "containers", f"{container_id}.json")
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
            parts = [_read_doc(r) for r in manifest.get("resources", [])]

            chapter_docs = manifest.get("chapter_resources")
            if chapter_docs:
                if current_sec is None:
                    # no time context: safe fallback is still everything, not nothing
                    parts += [_read_doc(r) for r in chapter_docs]
                else:
                    current_sec = float(current_sec)
                    in_order = sorted(chapter_docs, key=lambda r: r["t"])
                    current_idx = None
                    for i, r in enumerate(in_order):
                        if r["t"] <= current_sec < r.get("end_t", float("inf")):
                            current_idx = i
                            break
                    if current_idx is None:
                        # between/after known chapters — include whichever chapter just ended
                        # (most likely still relevant) plus whatever's next
                        past = [r for r in in_order if r["t"] <= current_sec]
                        current_idx = len(past) - 1 if past else 0
                    picked = in_order[max(0, current_idx):current_idx + 2]  # 当前 + 下一关，预取
                    parts += [_read_doc(r) for r in picked]

            if parts:
                return "\n\n".join(parts)
        except Exception as e:
            print(f"[resources] could not load manifest for {container_id}: {e}", flush=True)
    # fallback: no container_id given / manifest missing — inline everything
    parts = []
    for fn in sorted(os.listdir(RESOURCES)):
        if fn.endswith(".md"):
            with open(os.path.join(RESOURCES, fn)) as rf:
                parts.append(f"### {fn}\n{rf.read().strip()}")
    return "\n\n".join(parts)


def image_note(frame_path):
    """codex gets the frame natively attached via `-i` (no tool call needed);
    claude has no such CLI flag here, so it still has to Read the file."""
    if not frame_path:
        return "（本轮没有画面截图，仅凭文字判断）"
    if ARGS.backend == "codex":
        return "当前直播画面已经作为图片附件发给你了，直接看，不用 Read。"
    return f"当前直播画面截图: {frame_path}\n（先 Read 这张图。）"


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
        image_note=image_note(frame_path),
        resource_docs=get_resource_docs(payload.get("container_id"), payload.get("anchor_sec")),
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
                                    resource_docs=get_resource_docs(payload.get("container_id"), payload.get("current_sec")))
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
                                      image_note=image_note(frame_path),
                                      resource_docs=get_resource_docs(payload.get("container_id"), payload.get("current_sec")))
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

    class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        daemon_threads = True

    try:
        ThreadingHTTPServer(("127.0.0.1", ARGS.port), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
