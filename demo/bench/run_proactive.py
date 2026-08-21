"""一条命令跑完一个纯 proactive container，不用开浏览器。

    python3 bench/run_proactive.py slendytubbies-e01

浏览器那条路是实时的：视频放多久就得等多久。但纯 proactive 这一套根本没有音频，
agent 收到的只是每隔几秒一张画面，没有任何东西必须按真实时间走。所以这里换成离线跑：
一次 ffmpeg 把帧全抽出来，然后按视频时间一格一格问「现在要不要开口」，
问得多快取决于 API 多快，跟视频多长没关系。

跑完输出一份 JSON：它在哪些时刻开了口、命中了哪些窗口、漏了哪些、多说了几次，
以及每次命中的判分结果。

    --tick N     多少秒问一次（默认 8）。越小越细也越贵
    --workers N  并行几段（默认 4）。段之间各自记自己说过的话
    --limit N    只跑前 N 秒，先看看效果
    --no-judge   只跑不判，省钱
    --out PATH   报告写哪
"""

import argparse
import base64
import concurrent.futures as futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge as judge_mod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.environ.get("HERBENCH_AGENT_MODEL", "gpt-5.4")

# 每次问它的时候给几张：现在、上一格、上两格、上四格、上八格。
# 近处密远处稀，跟浏览器那条路给的信息量对齐——「卡住」得跟之前比才看得出来。
STRIP = [0, 1, 2, 4, 8]
COOL_TICKS = 3           # 刚说完之后隔几格不再问，对应浏览器里的 T_cool


DECIDE = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "speak": {"type": "boolean", "description": "此刻要不要开口"},
        "why": {"type": "string", "description": "一句话说清为什么，给你自己看的"},
        "say": {"type": "string", "description": "真要说的话，口语，一两句；不说就传空字符串"},
    },
    "required": ["speak", "why", "say"],
}

SYSTEM = """你在陪一个人。他第一次玩这个游戏 / 第一次用这个软件，正在自己摸索。

硬条件：**你听不到任何声音**，也没有人向你提问。你手上只有几张按时间排的画面。
「他这会儿顺不顺」只能从画面上读，读不出来就是读不出来。

你要做的只有一件事：在他确实需要的时候开口，别的时候闭嘴。

该开口的样子：几帧下来还在同一个地方出不去、同一个界面翻来翻去、同一个动作反复失败、
屏幕上有报错或明显没生效的操作；或者他刚过关、刚解开一个卡了很久的地方。

不该开口的样子：画面在正常推进（场景在换、他在往前走、操作有反馈）；
你只是想描述画面上有什么，他自己看得见；你刚说过差不多的话。

真开口的时候：一两句，口语，像坐他旁边的人。必须有内容——说清这是什么、
大概往哪个方向试、他刚那下为什么没成。只有「加油」「慢慢来」这种等于没说。
不要「首先/其次/建议你/需要注意的是」这类书面词。
绝不剧透他还没走到的地方，也别把完整解法一次报完。

拿不准就不说。大部分时间人都在正常玩，speak=false 是常态。"""


# ───────────────────────────── 抽帧 ─────────────────────────────

def ffmpeg_bin():
    exe = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("找不到 ffmpeg：装一个，或者设 FFMPEG=/path/to/ffmpeg")


def extract(video, tick, limit, width=384):
    """一次过把帧全抽出来。逐帧 seek 要几百次进程启动，整段 fps 过滤只走一遍解码。"""
    d = tempfile.mkdtemp(prefix="herbench_frames_")
    cmd = [ffmpeg_bin(), "-nostdin", "-loglevel", "error"]
    if limit:
        cmd += ["-t", str(limit)]
    cmd += ["-i", video, "-vf", f"fps=1/{tick},scale={width}:-2",
            "-q:v", "6", os.path.join(d, "%06d.jpg")]
    t0 = time.time()
    subprocess.run(cmd, check=True)
    files = sorted(os.listdir(d))
    print(f"抽帧 {len(files)} 张，用了 {time.time()-t0:.0f}s", flush=True)
    # 第 i 张对应视频时间 i*tick（ffmpeg 的 fps 过滤从半格起，差半格不影响判断）
    return d, [(i * tick, os.path.join(d, f)) for i, f in enumerate(files)]


_CACHE = {}


def b64(path):
    if path not in _CACHE:
        _CACHE[path] = base64.b64encode(open(path, "rb").read()).decode()
    return _CACHE[path]


# ───────────────────────────── 跑一段 ─────────────────────────────

def post(body, key, timeout=120):
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def ask(frames, said_before, title, tick, key):
    """给它一串画面，问现在要不要开口。"""
    content = [{"type": "text", "text":
                f"你在看的是：{title}\n"
                f"下面 {len(frames)} 张按时间排，最后一张是此刻，往前每张隔 {tick} 秒往上。\n"
                + (f"\n你刚才说过（别重复）：\n"
                   + "\n".join(f"- {s}" for s in said_before[-3:]) if said_before else "\n你还没说过话。")}]
    for _, p in frames:
        content.append({"type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64," + b64(p), "detail": "low"}})
    try:
        d = post({"model": MODEL,
                  "messages": [{"role": "system", "content": SYSTEM},
                               {"role": "user", "content": content}],
                  "response_format": {"type": "json_schema", "json_schema": {
                      "name": "decide", "strict": True, "schema": DECIDE}}}, key)
        return json.loads(d["choices"][0]["message"]["content"])
    except urllib.error.HTTPError as e:
        return {"speak": False, "why": f"[HTTP {e.code}] {e.read().decode()[:120]}", "say": ""}
    except Exception as e:
        return {"speak": False, "why": f"[错误] {str(e)[:120]}", "say": ""}


def run_chunk(idx, frames, lo, hi, title, tick, key, quiet, verbose=False):
    """跑 [lo, hi) 这一格区间。段之间互不知道对方说过什么，换来能并行。"""
    said, out, cool = [], [], 0
    for i in range(lo, hi):
        if cool > 0:
            cool -= 1
            continue
        strip = [frames[i - o] for o in reversed(STRIP) if i - o >= 0]
        r = ask(strip, said, title, tick, key)
        if verbose:
            t = frames[i][0]
            print(f"  [{t//60}:{t%60:02d}] {'说' if r.get('speak') else '不说'} · {r.get('why','')[:70]}",
                  flush=True)
        if r.get("speak") and (r.get("say") or "").strip():
            t = frames[i][0]
            line = r["say"].strip()
            out.append({"t": t, "text": line, "why": r.get("why", "")})
            said.append(line)
            cool = COOL_TICKS
            if not quiet:
                print(f"  [{t//60}:{t%60:02d}] 开口：{line[:56]}", flush=True)
    return idx, out


# ───────────────────────────── 算分 ─────────────────────────────

def score(container, said):
    tasks = []
    for t in container["tasks"]:
        a, b = t["window_sec"]
        hit = next((u for u in said if a <= u["t"] <= b), None)
        tasks.append({**t, "hit": bool(hit), "said": hit,
                      "delay_sec": (hit["t"] - a) if hit else None})
    covered = {id(u) for t in tasks if t["said"] for u in [t["said"]]}
    extra = [u for u in said if id(u) not in covered]
    return tasks, extra


def judge_all(tasks, workers, key):
    todo = [t for t in tasks if t["said"]]
    if not todo:
        return
    def one(t):
        shim = {"task_id": t["task_id"], "type": "proactive",
                "anchor_sec": t["window_sec"][0], "hint_level": t["hint_level"],
                "scene": t.get("scene", ""), "response_window_sec": t["window_sec"],
                "grading": {"rubric_points": t["grading"]["help_points"],
                            "spoiler_blocklist": t["grading"]["must_not_say"],
                            "must_cite": False}}
        code, v = judge_mod.judge_run(shim, {"answer": t["said"]["text"],
                                             "spoke_at_sec": t["said"]["t"]})
        t["judge"] = v if code == 200 else {"error": str(v)[:200]}
    with futures.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, todo))


# ───────────────────────────── main ─────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container")
    ap.add_argument("--tick", type=int, default=8)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 秒")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--verbose", action="store_true", help="每一格都打印它的判断，用来看它为什么不说")
    a = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY 没设")

    path = os.path.join(ROOT, "data", "proactive", f"{a.container}.json")
    if not os.path.exists(path):
        sys.exit(f"没有这个 container：{path}")
    C = json.load(open(path, encoding="utf-8"))
    video = os.path.join(ROOT, C["video"]["src"].lstrip("/"))
    if not os.path.exists(video):
        sys.exit(f"找不到视频 {video}")
    dur = min(C["video"]["duration"], a.limit) if a.limit else C["video"]["duration"]

    live = [t for t in C["tasks"] if t["window_sec"][0] < dur]
    print(f"{a.container}：{C['title']}")
    print(f"视频 {dur//60} 分 {dur%60} 秒，窗口 {len(live)} 个，每 {a.tick} 秒问一次，"
          f"{a.workers} 段并行\n", flush=True)

    t_all = time.time()
    d, frames = extract(video, a.tick, a.limit)
    try:
        n = len(frames)
        bounds = [(i * n // a.workers, (i + 1) * n // a.workers) for i in range(a.workers)]
        bounds = [(lo, hi) for lo, hi in bounds if hi > lo]
        print(f"开始跑，共 {n} 格\n", flush=True)
        t_run = time.time()
        said = []
        with futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
            jobs = [ex.submit(run_chunk, i, frames, lo, hi, C["title"], a.tick, key,
                              a.quiet, a.verbose)
                    for i, (lo, hi) in enumerate(bounds)]
            for f in futures.as_completed(jobs):
                said.extend(f.result()[1])
        said.sort(key=lambda u: u["t"])
        run_sec = time.time() - t_run
    finally:
        shutil.rmtree(d, ignore_errors=True)

    tasks, extra = score({**C, "tasks": live}, said)
    if not a.no_judge:
        print("\n判分…", flush=True)
        judge_all(tasks, a.workers, key)

    hit = sum(1 for t in tasks if t["hit"])
    useful = sum(1 for t in tasks if t.get("judge") and not t["judge"].get("error")
                 and any(x["hit"] for x in t["judge"].get("rubric", [])))
    total = time.time() - t_all

    print(f"\n{'═'*54}")
    print(f"窗口     {hit}/{len(tasks)} 接住" + (f"，其中 {useful} 条说到了点上" if not a.no_judge else ""))
    print(f"多余发言 {len(extra)} 次")
    print(f"总开口   {len(said)} 次")
    print(f"耗时     {total/60:.1f} 分钟（问 agent {run_sec/60:.1f} 分，视频本身 {dur/60:.0f} 分）")
    print(f"          比实时快 {dur/max(1,run_sec):.1f} 倍")
    print(f"{'═'*54}\n")
    for t in tasks:
        w = t["window_sec"]
        mark = "✓" if t["hit"] else "·"
        line = f"{mark} [{w[0]//60}:{w[0]%60:02d}–{w[1]//60}:{w[1]%60:02d}] {t['kind']:<8}"
        if t["hit"]:
            j = t.get("judge") or {}
            rb = j.get("rubric") or []
            line += f" 晚{t['delay_sec']:>3}s  {sum(1 for x in rb if x['hit'])}/{len(rb)}  {t['said']['text'][:44]}"
        print(line)

    out = a.out or os.path.join(ROOT, "data", "runs", f"{a.container}-{int(t_all)}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"container": a.container, "model": MODEL, "tick": a.tick,
               "duration_sec": dur, "wall_sec": round(total),
               "window_hit": hit, "window_total": len(tasks),
               "useful": useful, "over_trigger": len(extra),
               "said": said, "tasks": tasks},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n报告写到 {out}")


if __name__ == "__main__":
    main()
