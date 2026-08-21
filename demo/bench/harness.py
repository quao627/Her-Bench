"""评测框架：只驱动世界、只观察输出，不碰 agent 怎么实现。

评的是一套有时间属性的系统：有人在直播里做他不熟的事，旁边一个 agent 跟着看。
所以 harness 只做三件事：

1. 按视频时间把画面推给 agent
2. 主播开口时把问题递过去
3. 记下 agent 什么时候说了什么，再判分

**它不知道 agent 有没有后台、备不备料、备多密、用不用 codex。** 换一个只有前台
没有后台的 agent，或者一个每秒备一次料的，这个文件一行都不用改。

唯一被强制的是时间。agent 花掉的墙钟时间要折算成视频时间：视频 10:00 发起、
真跑了 18 秒的活，产出要到 10:18 才存在。这不是实现细节，是这套系统的定义——
一个想得慢的 agent 在真实场景里就是会错过时机。所以后台通道由 harness 提供，
agent 只管往里扔活、按时来取。
"""

import base64
import os
import shutil
import subprocess
import tempfile
import threading
import time


# ────────────────────────── 时间 ──────────────────────────

class Clock:
    """视频时间。agent 只能读，不能自己往前拨。"""

    def __init__(self):
        self._v = 0.0

    def now(self):
        return self._v

    def _set(self, v):
        self._v = max(self._v, float(v))

    def _charge(self, wall_sec):
        """把一段真实耗时折算成视频时间。"""
        self._v += float(wall_sec)


class Lane:
    """后台通道：一次只能跑一个活，跑多久按真实耗时折算成视频时间。

    agent 想什么时候扔活、扔多少，harness 不管。管的只有两件事：
    通道占着的时候扔不进来，以及扔进去的东西要等到 now + 实测耗时 才拿得到。
    """

    def __init__(self, clock, name="bg"):
        self.clock, self.name = clock, name
        self.free_at = 0.0
        self._done = []
        self._inflight = None
        self.stats = {"submitted": 0, "busy_rejected": 0, "cancelled": 0,
                      "wall_sec": 0.0, "durations": []}

    def busy(self):
        return self.clock.now() < self.free_at

    def submit(self, fn, label=""):
        """扔一个活进去。通道占着就返回 False，跟真实系统一样。"""
        if self.busy():
            self.stats["busy_rejected"] += 1
            return False
        started = self.clock.now()
        t0 = time.time()
        try:
            out = fn()
        except Exception as e:
            out = {"error": str(e)[:200]}
        took = time.time() - t0
        self.free_at = started + took
        self._inflight = {"label": label, "started": started,
                          "ready_at": started + took, "took": took, "out": out}
        self._done.append(self._inflight)
        self.stats["submitted"] += 1
        self.stats["wall_sec"] += took
        self.stats["durations"].append(round(took, 1))
        return True

    def ready(self):
        """已经回来了的产出。还在路上的取不到。"""
        now = self.clock.now()
        return [d for d in self._done if d["ready_at"] <= now and not d.get("killed")]

    def preempt(self):
        """主播开口了：正在跑的那条让路，产出作废。"""
        if self._inflight and self._inflight["ready_at"] > self.clock.now():
            self._inflight["killed"] = True
            self.stats["cancelled"] += 1
            self.free_at = self.clock.now()
            self._inflight = None
            return True
        return False


# ────────────────────────── 画面 ──────────────────────────

def _ffmpeg():
    exe = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


class Frames:
    """整段视频一次抽完，之后按视频时间取。

    真实场景里 agent 是一路看过来的，走到某一刻手上有从开头到现在的全部画面。
    这里把这些帧存在架子上，agent 想回看多深是它自己的事。
    """

    def __init__(self, video, step=5, limit=0, width=384):
        self.step = step
        self.dir = tempfile.mkdtemp(prefix="herbench_frames_")
        cmd = [_ffmpeg(), "-nostdin", "-loglevel", "error"]
        if limit:
            cmd += ["-t", str(limit + step)]
        cmd += ["-i", video, "-vf", f"fps=1/{step},scale={width}:-2", "-q:v", "6",
                os.path.join(self.dir, "%06d.jpg")]
        t0 = time.time()
        subprocess.run(cmd, check=True)
        self.files = sorted(os.path.join(self.dir, f) for f in os.listdir(self.dir))
        self.extract_sec = time.time() - t0
        self._video = video

    def __len__(self):
        return len(self.files)

    def at(self, sec):
        i = int(round(sec / self.step))
        if i < 0 or i >= len(self.files):
            return None
        try:
            return base64.b64encode(open(self.files[i], "rb").read()).decode()
        except Exception:
            return None

    def since_start(self, now, offsets):
        """按给定偏移往回取，越界的丢掉，去重后按时间排好。"""
        out, seen = [], set()
        for off in offsets:
            s = now + off
            if s < 0:
                continue
            k = int(round(s / self.step))
            if k in seen:
                continue
            b = self.at(s)
            if b:
                seen.add(k)
                out.append((int(k * self.step), b))
        return sorted(out)

    def hi_res(self, sec, width=640):
        """要一张清楚的：单独截，不走架子。"""
        out = tempfile.mktemp(suffix=".jpg")
        subprocess.run([_ffmpeg(), "-nostdin", "-loglevel", "error", "-ss", str(max(0, sec)),
                        "-i", self._video, "-frames:v", "1", "-vf", f"scale={width}:-2",
                        "-q:v", "5", "-y", out], check=False)
        if not os.path.exists(out) or os.path.getsize(out) < 500:
            return None
        b = base64.b64encode(open(out, "rb").read()).decode()
        os.unlink(out)
        return b

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


# ────────────────────────── agent 那一侧看到的世界 ──────────────────────────

class Context:
    """递给 agent 的东西。它能看到画面、能用后台通道、能读视频时间，别的没有。"""

    def __init__(self, clock, frames, lane, title, container_id):
        self.clock = clock
        self.frames = frames
        self.bg = lane
        self.title = title
        self.container_id = container_id

    def now(self):
        return self.clock.now()


# ────────────────────────── 主循环 ──────────────────────────

def run(agent, container, frames, tasks, frame_step=5, on_event=None):
    """走一遍视频。返回 agent 的每次发言，以及各项计数。

    事件只有两种：到点了推一帧，和主播开口。agent 在这两个回调里干什么、
    有没有往后台扔活，harness 一概不问，只把它花掉的墙钟时间记到视频时间上。
    """
    clock = Clock()
    lane = Lane(clock)
    ctx = Context(clock, frames, lane, container["title"], container["container_id"])
    log = on_event or (lambda *_: None)

    dur = len(frames) * frame_step
    by_anchor = {}
    for t in tasks:
        by_anchor.setdefault(t["anchor_sec"], []).append(t)

    events = [("frame", s) for s in range(0, dur, frame_step)]
    events += [("ask", s) for s in sorted(by_anchor)]
    events.sort(key=lambda e: (e[1], e[0] != "frame"))   # 同一刻先喂帧再提问

    says, answers = [], []
    if hasattr(agent, "start"):
        agent.start(ctx)

    for kind, sec in events:
        clock._set(sec)
        if kind == "frame":
            if not hasattr(agent, "on_frame"):
                continue
            t0 = time.time()
            out = agent.on_frame(ctx, sec, frames.at(sec))
            clock._charge(time.time() - t0)
            if out:                                   # agent 自己决定要说话
                says.append({"t": int(sec), "text": str(out), "kind": "spontaneous"})
                log("say", sec, str(out))
            continue

        # 主播开口。真实系统里这一刻后台要让路
        lane.preempt()
        for t in by_anchor[sec]:
            t0 = time.time()
            reply = agent.on_question(ctx, sec, t.get("question") or "", t)
            took = time.time() - t0
            clock._charge(took)
            text = reply if isinstance(reply, str) else (reply or {}).get("text", "")
            meta = {} if isinstance(reply, str) else dict(reply or {})
            meta.pop("text", None)
            answers.append({**t, "answer": text or "", "latency_ms": int(took * 1000), **meta})
            log("answer", sec, f"{t['task_id']} {took:.1f}s {text[:50]}")

    if hasattr(agent, "finish"):
        agent.finish(ctx)

    return {"says": says, "answers": answers,
            "video_sec_used": clock.now(), "video_sec_total": dur,
            "lane": lane.stats}
