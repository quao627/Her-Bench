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

这个后端不做任何感知判断：查什么、什么时候查，全部由前台那个常驻的 agent 决定
（它在自检 tick 里自己提问题）。以前这里还有一个 /research 端点，由查看器每 15 秒
定时驱动 codex 自己看画面造问题——那等于 harness 替 agent 行使自主性，节拍是我们
定的不是它定的，已经去掉。
"""
import argparse
import base64
import json
import os
import re
import subprocess
import tempfile
import threading
import time
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
RESOURCES = os.path.join(HERE, "data", "resources")

ARGS = None

# 说话对象是主播本人，不是观众。这里原本写的是「陪看助手 / 观众正在看的直播」，
# 跟 container 里 live_persona 的设定（"你是主播 XXX 的游戏陪玩搭子，陪他玩…"）是两套人称，
# gpt-live 那条路以为自己在跟主播说话、codex 这条路以为自己在跟观众说话。
# 任务里的问题也是主播第一人称问出来的（"我现在抱着的这个大铁球是干嘛用的？"），
# 所以这里统一成：你在跟主播本人对话，回答直接称呼"你"。
PROMPT_TMPL = """你是主播的游戏陪玩搭子，正陪他玩/看: {game}。
你说的每一句话都是**直接说给主播本人听的**——称呼他用"你"，不要用"他/她"，
也不要说成是在向别人转述他的情况。

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
   例外：如果这一刻是纯情绪反应（庆祝通关/安慰失败/一起笑名场面），一两句真诚的话就够，
   不适用上面的长度要求——这种时候硬凑成 3-6 句、或者顺势讲攻略，反而是错的。
4. 最后单独一行输出 "SOURCES: " 加你实际参考过的资料标题(逗号分隔), 上面资料里没有就写 SOURCES: none。

直接输出说给主播听的回答, 不要解释你的过程, 不需要用任何工具。"""

QUERY_DESC = "主播刚才问你: 「{question}」"
# 注意: 这里不能预设"玩家疑似卡关"。proactive 锚点实际覆盖四类时刻，卡关只占一半——
# 另一半是通关庆祝 / 挂掉安慰 / 名场面吐槽。之前的版本把卡关写死成前提，导致模型要么
# 看画面发现"根本没卡关"直接输出 SILENT(该庆祝的时刻沉默了)，要么硬把庆祝时刻脑补成
# 卡关、顺势灌一段攻略(该说"恭喜"的时候给了五句教学)。现在改成让它自己从画面判断属于
# 哪一类，并明确情绪类时刻不要借机讲攻略。
PROACTIVE_DESC = """这是主动介入场景: 没有人提问，要不要开口、开口说什么由你自己判断。
上面那组按时间先后排好的截图就是你的判断依据 —— 先对比着看清楚这段时间到底发生了什么，
再决定属于下面哪一种:
- 卡关求助: 几张图场景几乎没变、一直在同一处打转 —— 先安慰一句，再按提示分级给方向性提示，绝不给完整解法;
- 大挫折: 摔惨了/进度丢了/被判定失败/角色死亡/画面回到菜单或重生点 —— 安慰一两句就够;
- 大进展: 明显推进到了新场景、解开了卡很久的东西、做出成果、拿到成就 —— 真心替他高兴，一两句;
- 名场面: 操作或口误特别滑稽 —— 跟着笑一句。
如果对比下来只是在正常推进、没什么特别的，就只输出 SILENT 一个词。

落点是**他此刻的处境**：正卡着出不去、刚被判失败、刚做成一件事、还是刚到一个新地方。
前面几张图是用来看清「怎么走到此刻」的（有没有变化、变的是什么），这种跨图对比出来的变化
本身就可能是此刻的处境（比如几张图还在原来的场景、最后一张已经换了地方，说明他刚推进过来）。
但如果中间某一帧闪过的是个跟此刻处境无关的孤立事件（捡到了什么、数字跳了一下、提示闪过），
那件事已经翻篇了，别转头去说它 —— 要回应的始终是此刻。

重要: 后三类是纯情绪反应，一两句真诚的话就够，此时不要给攻略提示、不要分析操作、
不要长篇大论 —— 把一个该庆祝或该安慰的时刻当成卡关来"帮忙"是明确的错误。
只有第一类(确实卡住了)才需要给信息量。"""

LOOKUP_TMPL = """你是游戏攻略资料检索员。前台的语音陪玩 agent 需要查一个游戏事实。
问题是它自己提的（主播问到了、或者它自检时觉得这东西接下来可能用得上），你只管查准。

游戏: {game}
查询: {query}
{image_note}
下面是可查的全部资料，已经帮你准备好了，直接从里面找答案，不用自己找文件：
---
{resource_docs}
---
上面资料如果不够具体/笼统，别硬答——直接用 WebSearch 搜更准确的信息（官方 wiki、
攻略站、社区讨论都行），查证过的答案比翻资料摘要更可靠。

输出要求: 把这件事讲透——具体原理/步骤/数值/容易搞错的地方都可以写清楚，信息尽量给够、
不要藏着掖着。这段内容会被前台的语音 agent 再提炼转述给主播，所以你不用担心啰嗦或语气生硬，
把干货备齐就行，让它有真材实料可以提炼；不要铺垫，不需要用 ls/Read。
最后单独一行 "SOURCES: " 加实际参考的资料标题或 URL。"""

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


STRIP_READING_GUIDE = (
    "对比这几张能看出他这段时间实际在干什么：\n"
    "- 几张图场景/位置几乎没变 → 大概率卡在同一个地方出不去；\n"
    "- 明显推进到了新场景、或多了之前没有的东西 → 刚有进展；\n"
    "- 从游戏画面变成菜单/结算/重生画面 → 刚结束一局、通关或者失败了。\n"
    "只凭最后那一张静态图是分辨不出这些的，务必对比着看。"
)


def image_note(frame_paths, frame_labels):
    """codex gets frames natively attached via `-i` (no tool call needed);
    claude has no such CLI flag here, so it still has to Read the files.

    Multiple frames arrive for proactive tasks: a single anchor frame is
    genuinely insufficient there, because every signal that makes a moment
    worth speaking up about is temporal (how long they've been stuck, what
    they just finished). Verified concretely — the frame at the exact second
    Human Fall Flat's Water level is beaten shows the character falling
    through clouds, pixel-for-pixel the same kind of shot as falling off the
    map; and the Stanley Parable 'Beat the Game' achievement popup isn't even
    on screen yet at its own anchor. Handing the model one frame and asking
    'is this worth reacting to?' was asking it to guess."""
    if not frame_paths:
        return "（本轮没有画面截图，仅凭文字判断）"
    if len(frame_paths) == 1:
        if ARGS.backend == "codex":
            return "当前直播画面已经作为图片附件发给你了，直接看，不用 Read。"
        return f"当前直播画面截图: {frame_paths[0]}\n（先 Read 这张图。）"
    seq = " → ".join(frame_labels)
    if ARGS.backend == "codex":
        return (
            f"已经给你附上了 {len(frame_paths)} 张按时间先后排好的画面截图：{seq}。\n"
            "最后一张是此刻，前面几张是它之前的画面。直接看图，不用 Read。\n"
            + STRIP_READING_GUIDE
        )
    listing = "\n".join(f"- {lab}: {p}" for lab, p in zip(frame_labels, frame_paths))
    return (
        "按时间先后排好的画面截图（先把这几张都 Read 一遍）：\n" + listing + "\n"
        + STRIP_READING_GUIDE
    )


def run_claude(prompt: str) -> str:
    cmd = ["claude", "-p", "--model", ARGS.model, "--allowedTools", "Read"]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                       timeout=ARGS.timeout, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-400:] or "claude exited nonzero")
    return r.stdout.strip()


# Every codex call used to be `codex exec`, i.e. a brand new process with no
# memory of anything asked before. Two lookups about the same puzzle five minutes
# apart would each start cold and re-search the web from scratch, which is most of
# why the front end kept saying "我查查哈" and then coming back with nothing.
#
# `codex exec resume <thread_id>` continues an existing thread, so we keep one
# thread per container and reuse it. Two threads actually, split by how latency
# sensitive the caller is:
#
#   fg  /answer + /lookup            — someone is waiting on this
#   bg  /lookup {background: true}   — the live agent asked for it ahead of time
#
# They are kept apart on purpose. A single shared thread would need a single lock,
# and a foreground lookup would then queue behind a 20s background research call,
# undoing the reason this server is threaded in the first place. Each thread still
# needs its own lock, because concurrent `resume` on one thread means two codex
# processes writing the same session file.
_THREADS = {}            # key -> {"id": str|None, "lock": threading.Lock}
_THREADS_GUARD = threading.Lock()


def _thread_slot(container_id, kind):
    key = f"{container_id or '_'}::{kind}"
    with _THREADS_GUARD:
        if key not in _THREADS:
            _THREADS[key] = {"id": None, "lock": threading.Lock()}
        return _THREADS[key]


def _parse_thread_id(stdout: str):
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "thread.started" and ev.get("thread_id"):
            return ev["thread_id"]
    return None


def run_codex(prompt: str, frame_paths, container_id=None, kind="fg") -> str:
    slot = _thread_slot(container_id, kind)
    if isinstance(frame_paths, str):          # back-compat: single path
        frame_paths = [frame_paths] if frame_paths else []

    with slot["lock"]:
        out_file = tempfile.mktemp(suffix=".txt")
        base = ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only"]
        if slot["id"]:
            # resume takes the thread id as a subcommand arg; flags for `exec`
            # itself have to come before the subcommand or the parser rejects them
            cmd = base + ["resume", slot["id"], "--output-last-message", out_file]
        else:
            # --json so the first call can report its thread id back to us
            cmd = base + ["--json", "--output-last-message", out_file]
        for p in frame_paths:                 # -i is repeatable (`--image <FILE>...`)
            cmd += ["-i", p]
        # prompt goes via stdin: the server process has no tty, and codex prefers
        # stdin over a positional arg when stdin is piped
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                           timeout=ARGS.timeout, cwd=HERE)
        if not slot["id"]:
            tid = _parse_thread_id(r.stdout)
            if tid:
                slot["id"] = tid
                print(f"[codex] thread started {container_id}/{kind} = {tid}", flush=True)
    if os.path.exists(out_file):
        with open(out_file) as f:
            text = f.read().strip()
        os.unlink(out_file)
        if text:
            return text
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-400:] or "codex exited nonzero")
    # fallback: --json runs emit JSONL on stdout, so pick the last agent_message
    # out of the event stream rather than blindly taking the final line
    for line in reversed(r.stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            item = ev.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text"):
                return item["text"].strip()
    return r.stdout.strip().split("\n")[-1]


def _write_temp_jpeg(b64: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".jpg")
    with os.fdopen(fd, "wb") as f:
        f.write(base64.b64decode(b64))
    return path


def answer(payload: dict) -> dict:
    # chronological: oldest context frame first, "now" last
    frame_paths, frame_labels = [], []
    for cf in (payload.get("context_frames") or []):
        cb64 = cf.get("b64")
        if not cb64:
            continue
        frame_paths.append(_write_temp_jpeg(cb64))
        frame_labels.append(f"{abs(int(cf.get('offset_sec', 0)))} 秒前")

    frame_path = ""
    b64 = payload.get("frame_jpeg_base64")
    if b64:
        frame_path = _write_temp_jpeg(b64)
        frame_paths.append(frame_path)
        frame_labels.append("此刻")

    if payload.get("type") == "proactive":
        task_desc = PROACTIVE_DESC
    else:
        task_desc = QUERY_DESC.format(question=payload.get("question", ""))

    notes = payload.get("recent_research") or []
    research_context = ""
    if notes:
        lines = "\n".join(f"- Q: {n.get('question','')} / A: {n.get('text','')}" for n in notes)
        research_context = (
            "\n你之前自己要求后台查过下面这些东西（不一定跟这题有关，自己判断能不能用，"
            f"不相关就忽略，别硬套）：\n{lines}\n"
        )

    prompt = PROMPT_TMPL.format(
        game=payload.get("game", "Human Fall Flat"),
        image_note=image_note(frame_paths, frame_labels),
        resource_docs=get_resource_docs(payload.get("container_id"), payload.get("anchor_sec")),
        task_desc=task_desc,
        research_context=research_context,
        hint_level=payload.get("hint_level", "direction_only"),
        anchor_min=round(payload.get("anchor_sec", 0) / 60),
    )

    try:
        if ARGS.backend == "codex":
            raw = run_codex(prompt, frame_paths,
                            container_id=payload.get("container_id"), kind="fg")
        else:
            raw = run_claude(prompt)
    finally:
        for p in frame_paths:
            if p and os.path.exists(p):
                os.unlink(p)

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
        """前台 agent 的查证请求都落到这里，两种来路只差一个 background 标志：

        - 主播问到了 → lookup_game_info 工具调用 → 有人等 → fg thread
        - 它自己在自检 tick 里提的 → background: true → 没人等 → bg thread

        问题始终是前台 agent 提的。这个后端不做任何感知判断，只管把问题查准。
        """
        query = payload.get("query", "")
        game = payload.get("game", "")
        background = bool(payload.get("background"))
        kind = "bg" if background else "fg"
        # 只有它明说这次要看图时才带帧（need_frame），多传图会让 codex 明显变慢
        frame_paths, frame_labels = [], []
        for fr in (payload.get("frames") or []):
            b64 = fr.get("b64")
            if not b64:
                continue
            frame_paths.append(_write_temp_jpeg(b64))
            off = int(fr.get("offset_sec", 0))
            frame_labels.append("此刻" if off == 0 else f"{abs(off)} 秒前")
        print(f"[{ARGS.backend}] lookup ({kind}): {query}", flush=True)
        prompt = LOOKUP_TMPL.format(game=game or "见资料目录", query=query,
                                    image_note=("\n" + image_note(frame_paths, frame_labels) + "\n") if frame_paths else "",
                                    resource_docs=get_resource_docs(payload.get("container_id"), payload.get("current_sec")))
        try:
            if ARGS.backend == "codex":
                raw = run_codex(prompt, frame_paths,
                                container_id=payload.get("container_id"), kind=kind)
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
        finally:
            for fp in frame_paths:
                if fp and os.path.exists(fp):
                    os.unlink(fp)
        result["latency_ms"] = int((time.time() - t0) * 1000)
        print(f"[{ARGS.backend}] lookup done in {result['latency_ms']}ms", flush=True)
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
