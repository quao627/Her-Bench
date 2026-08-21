"""顺着视频从头看到尾，边看边攒料，问题来了才答。

    python3 bench/run_stream.py portal-e01 --limit 1300

跟 run_query.py 的差别是唯一重要的那一点：**agent 有没有跟着看**。

run_query.py 每道题各跑各的，agent 手上什么都没有，每次都得现查。这测的是
「冷启动能不能答对」，答案对不对是准的，但延迟系统性偏高——真实场景里它一直在看，
很多东西早就查过了。

这里换成顺着视频走：全程每 5 秒一帧地看着，每隔一段视频时间把最近几帧交给后台
备料，攒下来的笔记一直带着；走到某道题的锚点时，把从开头到此刻的回看条连同笔记
一起摆在面前，先看够不够直接答，够就直接答（快），不够才去查（慢）。

回看条是「它一直在看」的离线等价物：浏览器里每 5 秒一帧全进上下文，到某一刻时它
手上有从开头到现在的全部画面。这边不可能每次都重发几百帧，所以按对数往回退取样，
近处密远处稀，一直取到开头。「我刚拿到的这个装置是干什么用的」这种题，
答案就在几分钟前那一帧里，没有这条就只能靠猜。这样测出来的延迟才是真实的那个数，而且能看出「提前准备」
到底帮了多少。

不按真实时间走，但**记一本视频时间的账**。codex 跑一次要十几二十秒，这段时间在真实
场景里是要流过去的：视频 10:00 发起的备料，实测跑了 18 秒，那它要到 10:18 才可用，
10:10 的题就用不上。所以每次调用都把实测耗时折算成视频时间记下来，锚点处只给已经
"回来了"的笔记。codex 的后台通道一次只能跑一条，上一条没回来这一格就跳过；
主播一开口，正在跑的那条按打断规则作废。

墙上时间只花在真实调用上，中间的空白照样跳过——但跳过的量永远不超过 API 实际
花掉的。这样既不用等视频那么久，"资料来不来得及"这件事又是真的。

前提是 agent 后端在跑：
    python3 agent/agent_live.py --backend codex

    --brief N    每隔多少秒视频时间备一次料（默认 120）
    --limit N    只跑前 N 秒视频
    --no-brief   不备料，退化成 run_query.py 那样，用来做对照
    --no-judge   只跑不判
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
FAST_MODEL = os.environ.get("HERBENCH_FRONT_MODEL", "gpt-5.4")

# 备料带的帧：跟浏览器里那条一致，近处密远处稀
BRIEF_OFFSETS = [0, -5, -10, -20, -45, -90, -180]

# 前台那一端是一直在看的：浏览器里每 5 秒一帧全进上下文，走到某一刻时它手里有
# 从开头到现在的全部画面。离线这边不可能把几百帧每次都重发，所以按对数往回退取样：
# 近处密、远处稀，一直取到视频开头。要答「我刚拿到的这个装置」这种题，靠的就是这条。
LOOKBACK = [0, -10, -25, -50, -90, -150, -240, -360, -540, -800, -1200, -1800, -2600, -3600]
FRAME_STEP = 5           # 一次抽完的帧间隔，秒

FAST_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "enough": {"type": "boolean",
                   "description": "手上这些够不够直接答。不确定具体事实就是不够"},
        "answer": {"type": "string", "description": "够的话直接把话说出来；不够就传空"},
        "lookup": {"type": "string", "description": "不够的话，要去查什么"},
    },
    "required": ["enough", "answer", "lookup"],
}

FAST_SYS = """你是主播的陪玩搭子，正跟着他看直播。他刚问了你一句话。

你手上有：当前这一帧画面，以及你之前跟着看的时候后台替你查过的一些笔记。

先判断一件事：**手上这些够不够直接答**。

够：笔记里正好有这个东西的准确细节，或者这就是从画面上直接看得出来的事。
不够：涉及具体数值、机制细节、剧情设定，而笔记里没有对得上的。
「我大概知道」不算够——你对这类细节的记忆本来就不可靠，不确定就去查。

注意：你是一路看过来的，前面那些画面里发生过的事你都知道。他问「我刚拿到的这个东西」
这种，答案往往就在前面某一帧里，那不算「不确定」，直接答。

够的话就直接把话说出来：口语，一两句到三四句，说清楚，别念稿子，
不要「首先/其次/建议你」这类书面词。绝不剧透他还没走到的地方。"""


def ffmpeg_bin():
    exe = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit("找不到 ffmpeg：装一个，或者设 FFMPEG=/path/to/ffmpeg")


FFMPEG = None


def grab(video, sec, width=448):
    global FFMPEG
    if FFMPEG is None:
        FFMPEG = ffmpeg_bin()
    out = tempfile.mktemp(suffix=".jpg")
    subprocess.run([FFMPEG, "-nostdin", "-loglevel", "error", "-ss", str(max(0, sec)),
                    "-i", video, "-frames:v", "1", "-vf", f"scale={width}:-2",
                    "-q:v", "5", "-y", out], check=False)
    if not os.path.exists(out) or os.path.getsize(out) < 500:
        return None
    b = base64.b64encode(open(out, "rb").read()).decode()
    os.unlink(out)
    return b


def extract_all(video, step, limit):
    """一次 ffmpeg 抽完整段。逐帧 seek 要几百次进程启动，整段 fps 过滤只走一遍解码。"""
    global FFMPEG
    if FFMPEG is None:
        FFMPEG = ffmpeg_bin()
    d = tempfile.mkdtemp(prefix="herbench_stream_")
    cmd = [FFMPEG, "-nostdin", "-loglevel", "error"]
    if limit:
        cmd += ["-t", str(limit + step)]
    cmd += ["-i", video, "-vf", f"fps=1/{step},scale=384:-2", "-q:v", "6",
            os.path.join(d, "%06d.jpg")]
    t0 = time.time()
    subprocess.run(cmd, check=True)
    files = sorted(os.listdir(d))
    print(f"抽帧 {len(files)} 张（每 {step}s 一张），用了 {time.time()-t0:.0f}s\n", flush=True)
    return d, [os.path.join(d, f) for f in files]


def at(shelf, sec, step):
    """取视频第 sec 秒那一格。取不到就返回 None。"""
    i = int(round(sec / step))
    if i < 0 or i >= len(shelf):
        return None
    try:
        return base64.b64encode(open(shelf[i], "rb").read()).decode()
    except Exception:
        return None


def lookback(shelf, now, step):
    """从开头到此刻的回看条：近处密、远处稀。这是「它一直在看」这件事的离线等价物。"""
    out = []
    for off in LOOKBACK:
        s = now + off
        if s < 0:
            continue
        b = at(shelf, s, step)
        if b:
            out.append((int(s), b))
    seen, uniq = set(), []
    for s, b in sorted(out):
        if s in seen:
            continue
        seen.add(s); uniq.append((s, b))
    return uniq


def post(url, payload, timeout=200):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def openai(body, timeout=120):
    key = os.environ["OPENAI_API_KEY"]
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def try_fast(question, strip, notes, game, now):
    """前台那一端：手上的料够不够直接答。够就在这儿把话说了，不用惊动后台。

    strip 是从视频开头到此刻的回看条。它一直在看，所以「刚才发生过什么」是它本来
    就有的东西，不是查来的——很多题的答案就藏在几分钟前那一帧里。
    """
    ns = "\n".join(f"- Q: {n['question']}\n  A: {n['text']}" for n in notes[-6:]) or "（还没有笔记）"
    stamps = "、".join(f"{s//60}:{s%60:02d}" for s, _ in strip)
    content = [{"type": "text", "text":
                f"你在陪他玩：{game}\n\n"
                f"下面是你一路看过来的画面，时间点分别是 {stamps}，最后一张是此刻。\n\n"
                f"你跟着看的时候后台替你查过这些：\n{ns}\n\n"
                f"他刚问：「{question}」"}]
    for _, b in strip:
        content.append({"type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64," + b, "detail": "low"}})
    t0 = time.time()
    d = openai({"model": FAST_MODEL,
                "messages": [{"role": "system", "content": FAST_SYS},
                             {"role": "user", "content": content}],
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "fast", "strict": True, "schema": FAST_SCHEMA}}})
    return json.loads(d["choices"][0]["message"]["content"]), int((time.time() - t0) * 1000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container")
    ap.add_argument("--brief", type=int, default=120, help="每隔多少秒视频时间备一次料")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-brief", action="store_true")
    ap.add_argument("--no-clock", action="store_true",
                    help="不记视频时间的账：备料一回来就当可用。对照用，会高估命中率")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--agent", default="http://localhost:8787")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY 没设")

    path = os.path.join(ROOT, "data", "containers", f"{a.container}.json")
    if not os.path.exists(path):
        sys.exit(f"没有这个 container：{path}")
    C = json.load(open(path, encoding="utf-8"))
    video = os.path.join(ROOT, C["video"]["src"].lstrip("/"))
    dur = min(C["video"]["duration"], a.limit) if a.limit else C["video"]["duration"]
    tasks = [t for t in C["tasks"] if t["type"] == "query" and t["anchor_sec"] <= dur]
    if not tasks:
        sys.exit("这段里没有问答题")

    print(f"{a.container}：{C['title']}")
    print(f"顺着看前 {dur//60} 分钟，问答题 {len(tasks)} 道，"
          + ("不备料（对照组）" if a.no_brief else f"每 {a.brief}s 视频时间备一次料") + "\n", flush=True)

    t_all = time.time()
    shelf_dir, shelf = extract_all(video, FRAME_STEP, dur)
    notes, rows, briefs, skipped, killed = [], [], 0, 0, 0
    bg_free_at = 0.0          # 后台通道空出来的视频时刻
    # 把备料点和题的锚点按视频时间排到一条线上，顺着走
    events = [] if a.no_brief else [("brief", s) for s in range(a.brief, dur, a.brief)]
    events += [("task", t["anchor_sec"]) for t in tasks]
    events.sort(key=lambda e: e[1])
    by_anchor = {t["anchor_sec"]: t for t in tasks}

    for kind, sec in events:
        if kind == "brief":
            if not a.no_clock and bg_free_at > sec:
                skipped += 1
                print(f"  [{sec//60}:{sec%60:02d}] 备料跳过 · 上一条到 "
                      f"{int(bg_free_at)//60}:{int(bg_free_at)%60:02d} 才回来", flush=True)
                continue
            frames = []
            for off in BRIEF_OFFSETS:
                s2 = sec + off
                if s2 < 0:
                    continue
                b = at(shelf, s2, FRAME_STEP)
                if b:
                    frames.append({"offset_sec": off, "b64": b})
            t0 = time.time()
            try:
                j = post(f"{a.agent}/research", {
                    "frames": frames, "container_id": C["container_id"],
                    "current_sec": sec, "game": C["title"]})
            except Exception as e:
                print(f"  [{sec//60}:{sec%60:02d}] 备料失败 {str(e)[:60]}", flush=True)
                continue
            briefs += 1
            took = time.time() - t0                    # 真实耗时，直接当视频秒数记账
            ready = sec + took
            bg_free_at = ready
            if j.get("noteworthy"):
                notes.append({"question": j["question"], "text": j["text"],
                              "at": sec, "ready_at": ready, "took_sec": round(took, 1)})
                print(f"  [{sec//60}:{sec%60:02d}] 备料 {took:.0f}s → "
                      f"{int(ready)//60}:{int(ready)%60:02d} 可用 · {j['question'][:40]}", flush=True)
            else:
                print(f"  [{sec//60}:{sec%60:02d}] 备料 {took:.0f}s → 没什么值得查的", flush=True)
            continue

        t = by_anchor[sec]
        # 主播开口：正在跑的那条后台立刻让路，它的产出作废
        if not a.no_clock and bg_free_at > sec:
            if notes and notes[-1]["ready_at"] > sec:
                notes.pop()
                killed += 1
                print(f"  [{sec//60}:{sec%60:02d}] 主播开口 → 掐掉正在跑的那条备料", flush=True)
            bg_free_at = sec
        ready_notes = notes if a.no_clock else [n for n in notes if n["ready_at"] <= sec]

        strip = lookback(shelf, sec, FRAME_STEP)
        frame = grab(video, sec, 640)          # 后台查证仍然只给锚点这一帧，跟浏览器那条一致
        fast, fast_ms = try_fast(t.get("question", ""), strip, ready_notes, C["title"], sec)
        if fast["enough"] and fast["answer"].strip():
            rows.append({**t, "answer": fast["answer"].strip(), "citations": [],
                         "latency_ms": fast_ms, "served": "手上就有",
                         "notes_at_hand": len(ready_notes), "notes_total": len(notes),
                         "lookback_frames": len(strip)})
            print(f"  [{sec//60}:{sec%60:02d}] {t['task_id']} 手上就有 · {fast_ms/1000:.1f}s"
                  f"（{len(ready_notes)}/{len(notes)} 条笔记来得及）", flush=True)
        else:
            t0 = time.time()
            try:
                j = post(f"{a.agent}/answer", {
                    "task_id": t["task_id"], "type": "query", "question": t.get("question"),
                    "anchor_sec": sec, "hint_level": t.get("hint_level"),
                    "context_window_sec": t.get("context_window_sec"),
                    "game": C["title"], "container_id": C["container_id"],
                    "frame_jpeg_base64": frame,
                    "recent_research": [{"question": n["question"], "text": n["text"]}
                                        for n in ready_notes[-4:]]})
            except Exception as e:
                rows.append({**t, "answer": "", "citations": [], "latency_ms": None,
                             "served": "失败", "error": str(e)[:150],
                             "notes_at_hand": len(ready_notes), "lookback_frames": len(strip)})
                print(f"  [{sec//60}:{sec%60:02d}] {t['task_id']} 失败 {str(e)[:50]}", flush=True)
                continue
            took = time.time() - t0
            ms = fast_ms + int(took * 1000)
            bg_free_at = max(bg_free_at, sec + fast_ms / 1000 + took)   # 前台占着的这段时间后台也别插队
            rows.append({**t, "answer": j.get("text", ""), "citations": j.get("citations") or [],
                         "latency_ms": ms, "served": "得现查",
                         "notes_at_hand": len(ready_notes), "notes_total": len(notes),
                         "lookback_frames": len(strip)})
            print(f"  [{sec//60}:{sec%60:02d}] {t['task_id']} 得现查 · {ms/1000:.1f}s"
                  f"（判断 {fast_ms/1000:.1f}s + 查证 {took:.1f}s）", flush=True)

    shutil.rmtree(shelf_dir, ignore_errors=True)
    run_sec = time.time() - t_all

    if not a.no_judge:
        print("\n判分…", flush=True)
        def one(r):
            if r.get("error"):
                return
            code, v = judge_mod.judge_run(r, {"answer": r["answer"], "citations": r["citations"]})
            r["judge"] = v if code == 200 else {"error": str(v)[:200]}
        with futures.ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(one, rows))

    ok = [r for r in rows if not r.get("error")]
    def jv(r, k, d=None):
        return (r.get("judge") or {}).get(k, d)
    hit = sum(len([x for x in (jv(r, "rubric") or []) if x["hit"]]) for r in ok)
    tot = sum(len(jv(r, "rubric") or []) for r in ok)
    spoil = sum(len([x for x in (jv(r, "spoiler") or []) if x["violated"]])
                + (1 if jv(r, "leaked_future") else 0) for r in ok)
    fastn = [r for r in ok if r["served"] == "手上就有"]
    slown = [r for r in ok if r["served"] == "得现查"]
    med = lambda xs: sorted(xs)[len(xs)//2] if xs else None

    print(f"\n{'═'*60}")
    lb = [r.get("lookback_frames", 0) for r in ok]
    print(f"看视频    每 {FRAME_STEP}s 一帧，答题时回看 {max(lb) if lb else 0} 帧（覆盖到开头）")
    print(f"备料      跑了 {briefs} 次，攒下 {len(notes)} 条"
          + (f"；因为上一条还没回来跳过 {skipped} 次" if skipped else "")
          + (f"；被主播开口掐掉 {killed} 次" if killed else ""))
    if notes:
        tk = [n["took_sec"] for n in notes]
        print(f"          每次占用 {min(tk):.0f} 到 {max(tk):.0f} 秒视频时间"
              + ("（没记账，全都当立刻可用）" if a.no_clock else "，这段时间里它是不可用的"))
    print(f"答对      rubric {hit}/{tot}" + (f"（{hit/tot*100:.0f}%）" if tot else ""))
    print(f"剧透      {spoil} 处")
    print(f"手上就有  {len(fastn)}/{len(ok)} 道，延迟中位 "
          + (f"{med([r['latency_ms'] for r in fastn])/1000:.1f}s" if fastn else "—"))
    print(f"得现查    {len(slown)}/{len(ok)} 道，延迟中位 "
          + (f"{med([r['latency_ms'] for r in slown])/1000:.1f}s" if slown else "—"))
    print(f"跑完      {run_sec/60:.1f} 分钟（视频本身 {dur/60:.0f} 分，快 {dur/max(1,run_sec):.1f} 倍）")
    print(f"{'═'*60}\n")
    for r in rows:
        rb = jv(r, "rubric") or []
        n = f"{len([x for x in rb if x['hit']])}/{len(rb)}" if rb else "—"
        lat = f"{r['latency_ms']/1000:>5.1f}s" if r["latency_ms"] else "    —"
        print(f"{r['task_id']:<16} {r['served']:<6} {lat} {n:>5}  {(r.get('error') or r['answer'])[:48]}")

    out = a.out or os.path.join(ROOT, "data", "runs", f"{a.container}-stream-{int(t_all)}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"container": a.container, "kind": "stream", "brief_sec": None if a.no_brief else a.brief,
               "limit_sec": dur, "briefs": briefs, "notes": notes,
               "wall_sec": round(run_sec), "rubric_hit": hit, "rubric_total": tot,
               "spoiler": spoil, "served_fast": len(fastn), "served_lookup": len(slown),
               "tasks": rows}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n报告写到 {out}")


if __name__ == "__main__":
    main()
