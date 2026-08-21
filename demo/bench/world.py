"""评测这一侧：手里攥着视频和时钟，等 agent 连进来。

agent 是另一个进程，跟这边只有 HTTP。它拿不到题、拿不到判分标准、拿不到这个文件里
的任何东西——能看到的只有画面和主播说的话。

## 时钟

时钟归这一侧管。每次 /tick，视频时间前进：

    max(帧间隔, agent 上次拿到响应到这次发请求之间的墙钟时间)

/say 也一样结账，只是不保底一帧——不然「主播问完到它答上用了多久」永远是 0，
它花在想和查上的那十几秒等于白送。

想得快就每次前进一帧，看到每一帧，整场跑完远快于视频本身。想得慢就按它自己的耗时
前进，**中间的帧直接错过**，主播的问题也要等它回来才拿得到。「想得慢会错过时机」
是协议自带的，不用特意去模拟；agent 在自己那边开几条线程做后台是它的自由，
但那些时间一样会在下一次 /tick 上体现出来。

## 协议

    GET  /session   → 这一场是什么：容器、标题、时长、帧间隔
    POST /tick      → {t, frame, event, done}
                      event 为 null 表示这一刻没人说话；
                      {"type":"question","text":...} 表示主播开口了，等你回话
    POST /say       → {"text": "..."}  在当前视频时间说一句
    GET  /result    → 整场跑完之后取原始记录（判分由评测那一侧另做）

agent 那边的循环就是：

    while True:
        r = POST /tick
        if r["done"]: break
        if r["event"]: POST /say {...}          # 主播问了，得回
        elif 你自己觉得该说: POST /say {...}     # 主动开口
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class World:
    """一场评测的全部状态。除了 frames 和 tasks，agent 什么都碰不到。"""

    def __init__(self, container, frames, tasks, frame_step=5, log=None):
        self.C = container
        self.frames = frames
        self.frame_step = frame_step
        self.log = log or (lambda *a: None)

        self.dur = len(frames) * frame_step
        self.by_anchor = {}
        for t in tasks:
            self.by_anchor.setdefault(int(t["anchor_sec"]), []).append(t)
        self.anchors = sorted(self.by_anchor)

        self.t = 0.0                 # 视频时间，只有这一侧能推
        self.last_served = None      # 上一次 /tick 响应发出去的墙钟时刻
        self.pending = None          # 已经递出去、还没等到回话的题
        self.says = []               # agent 说过的每一句
        self.answers = []            # 对着题的回答
        self.done = False
        self.started = time.time()
        self.ticks = 0
        self.missed_frames = 0
        self.lock = threading.Lock()

    # ── 时钟 ──
    def _charge(self, min_step=0.0):
        """把 agent 从上次拿到响应到这次发请求之间的墙钟，记到视频时间上。

        每个请求都结账，不只是 /tick。不然「主播问完到它答上用了多久」永远是 0：
        它花在想和查上的那十几秒不记，就等于白送。
        """
        now = time.time()
        think = 0.0 if self.last_served is None else now - self.last_served
        self.t += max(min_step, think)
        self.last_served = now
        return think

    def tick(self):
        with self.lock:
            if self.done:
                return {"done": True, "t": round(self.t, 1)}
            # 上一道题还没回话就再来 tick：视为放弃作答
            if self.pending is not None:
                self._charge()
                self._record_answer(self.pending, "", gave_up=True)
                self.pending = None

            think = self._charge(min_step=self.frame_step)
            if think > self.frame_step:
                self.missed_frames += int(think // self.frame_step) - 1
            if self.t >= self.dur:
                self.done = True
                return {"done": True, "t": round(self.t, 1)}

            # 这一格跨过去的锚点：主播在这段时间里开过口
            due = [a for a in self.anchors
                   if a <= self.t and not self.by_anchor[a][0].get("_served")]
            event = None
            if due:
                a = due[0]
                task = self.by_anchor[a][0]
                task["_served"] = True
                self.pending = task
                event = {"type": "question", "text": task.get("question") or "",
                         "at": a, "late_sec": round(self.t - a, 1)}
                self.log("ask", self.t, f"{task['task_id']} {event['text'][:40]}"
                         + (f"（晚了 {event['late_sec']:.0f}s 才递到）" if event["late_sec"] > 1 else ""))

            self.ticks += 1
            return {"done": False, "t": round(self.t, 1),
                    "frame": self.frames.at(self.t), "event": event,
                    "video_sec": self.dur}

    def say(self, text):
        with self.lock:
            self._charge()               # 想了多久、查了多久，都算进去
            text = (text or "").strip()
            if not text:
                return {"ok": False, "why": "空话不算"}
            entry = {"t": round(self.t, 1), "text": text}
            if self.pending is not None:
                self._record_answer(self.pending, text)
                self.pending = None
                entry["answering"] = True
            else:
                entry["answering"] = False
                self.log("say", self.t, text[:60])
            self.says.append(entry)
            return {"ok": True, "t": entry["t"]}

    def _record_answer(self, task, text, gave_up=False):
        a = int(task["anchor_sec"])
        self.answers.append({**{k: v for k, v in task.items() if not k.startswith("_")},
                             "answer": text,
                             "answered_at": round(self.t, 1),
                             "latency_sec": round(self.t - a, 1),
                             "gave_up": gave_up})
        self.log("answer", self.t,
                 f"{task['task_id']} 用了 {self.t - a:.1f}s 视频时间 · "
                 + ("放弃作答" if gave_up else text[:46]))

    def result(self):
        return {"container": self.C["container_id"], "title": self.C["title"],
                "video_sec": self.dur, "video_sec_used": round(self.t, 1),
                "wall_sec": round(time.time() - self.started, 1),
                "ticks": self.ticks, "missed_frames": self.missed_frames,
                "says": self.says, "answers": self.answers}


def serve(world, port=0):
    """起服务，返回 (httpd, 端口)。调用方自己 shutdown。"""

    class H(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _send(self, obj, code=200):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read(self):
            n = int(self.headers.get("Content-Length", 0))
            try:
                return json.loads(self.rfile.read(n)) if n else {}
            except Exception:
                return {}

        def do_GET(self):
            p = self.path.split("?")[0]
            if p == "/session":
                self._send({"container": world.C["container_id"], "title": world.C["title"],
                            "video_sec": world.dur, "frame_step": world.frame_step})
            elif p == "/result":
                self._send(world.result())
            else:
                self._send({"error": "no such path"}, 404)

        def do_POST(self):
            p = self.path.split("?")[0]
            body = self._read()
            if p == "/tick":
                self._send(world.tick())
            elif p == "/say":
                self._send(world.say(body.get("text")))
            else:
                self._send({"error": "no such path"}, 404)

        def log_message(self, *a):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]
