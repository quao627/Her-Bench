"""一条命令跑完一个 container 的问答题，不用开浏览器。

    python3 bench/run_query.py portal-e01

问答题不需要实时：每道题就是「在锚点这一刻，主播问了这么一句，你怎么答」，
跟视频播到哪儿没关系。所以这里直接按题跑：截锚点那一帧，连同题包一起发给
agent 后端，拿回答案再送去判分。

前提是 agent 后端在跑：
    python3 agent/agent_live.py --backend codex

跑完输出一份 JSON：每道题它答了什么、引用了什么、判分结果，以及汇总。

    --tasks a,b,c   只跑这几道（写 task_id 或序号）
    --limit N       只跑前 N 道
    --workers N     并行几道（默认 1）。codex 那边按 container 串行，调大意义不大
    --no-judge      只跑不判，省钱
    --agent URL     agent 后端地址，默认 http://localhost:8787/answer
    --out PATH      报告写哪
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

# 主动型题要靠一段时间线才判得出来，问答题只需要锚点那一帧加几张铺垫
CONTEXT_OFFSETS = [-240, -180, -120, -60, -20]


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


def grab(video, sec, width):
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


def ask_agent(url, payload, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def run_one(t, C, video, url, quiet):
    """截帧 + 打一次 /answer。返回 (task, 回答)。"""
    t0 = time.time()
    frame = grab(video, t["anchor_sec"], 640)
    ctx = []
    if t["type"] == "proactive":
        for off in CONTEXT_OFFSETS:
            s = t["anchor_sec"] + off
            if s < 0:
                continue
            b = grab(video, s, 448)
            if b:
                ctx.append({"offset_sec": off, "b64": b})
    payload = {
        "task_id": t["task_id"], "type": t["type"], "question": t.get("question"),
        "anchor_sec": t["anchor_sec"], "hint_level": t.get("hint_level"),
        "context_window_sec": t.get("context_window_sec"),
        "game": C["title"], "container_id": C["container_id"],
        "frame_jpeg_base64": frame,
    }
    if ctx:
        payload["context_frames"] = ctx
    try:
        j = ask_agent(url, payload)
    except urllib.error.URLError as e:
        return t, {"text": "", "citations": [], "error": f"连不上 agent 后端：{e.reason}"}
    except Exception as e:
        return t, {"text": "", "citations": [], "error": str(e)[:200]}
    j.setdefault("latency_ms", int((time.time() - t0) * 1000))
    if not quiet:
        print(f"  {t['task_id']}  {j['latency_ms']/1000:.0f}s  {(j.get('text') or '')[:56]}", flush=True)
    return t, j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container")
    ap.add_argument("--tasks", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--agent", default="http://localhost:8787/answer")
    ap.add_argument("--out", default=None)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not a.no_judge and not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY 没设（判分要用；只想跑不判就加 --no-judge）")

    path = os.path.join(ROOT, "data", "containers", f"{a.container}.json")
    if not os.path.exists(path):
        sys.exit(f"没有这个 container：{path}")
    C = json.load(open(path, encoding="utf-8"))
    video = os.path.join(ROOT, C["video"]["src"].lstrip("/"))
    if not os.path.exists(video):
        sys.exit(f"找不到视频 {video}")

    tasks = [t for t in C["tasks"] if t["type"] == "query"]
    if a.tasks:
        want = {x.strip() for x in a.tasks.split(",")}
        tasks = [t for i, t in enumerate(tasks) if t["task_id"] in want or str(i + 1) in want]
    if a.limit:
        tasks = tasks[:a.limit]
    if not tasks:
        sys.exit("没有要跑的题")

    print(f"{a.container}：{C['title']}")
    print(f"问答题 {len(tasks)} 道，agent 后端 {a.agent}\n", flush=True)

    t_all = time.time()
    results = []
    if a.workers > 1:
        with futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
            results = list(ex.map(lambda t: run_one(t, C, video, a.agent, a.quiet), tasks))
    else:
        for t in tasks:
            results.append(run_one(t, C, video, a.agent, a.quiet))
    run_sec = time.time() - t_all

    dead = [t for t, j in results if j.get("error")]
    if len(dead) == len(results):
        print(f"\n全都失败了：{results[0][1]['error']}")
        print("agent 后端起来了吗？  python3 agent/agent_live.py --backend codex")
        sys.exit(1)

    rows = [{**t, "answer": j.get("text", ""), "citations": j.get("citations") or [],
             "latency_ms": j.get("latency_ms"), "error": j.get("error")}
            for t, j in results]

    if not a.no_judge:
        print("\n判分…", flush=True)
        def one(r):
            if r["error"]:
                return
            code, v = judge_mod.judge_run(r, {"answer": r["answer"], "citations": r["citations"]})
            r["judge"] = v if code == 200 else {"error": str(v)[:200]}
        with futures.ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(one, rows))

    ok = [r for r in rows if not r["error"]]
    def jv(r, k, d=None):
        return (r.get("judge") or {}).get(k, d)
    hit = sum(len([x for x in (jv(r, "rubric") or []) if x["hit"]]) for r in ok)
    total = sum(len(jv(r, "rubric") or []) for r in ok)
    spoil = sum(len([x for x in (jv(r, "spoiler") or []) if x["violated"]]) + (1 if jv(r, "leaked_future") else 0)
                for r in ok)
    lvl = sum(1 for r in ok if jv(r, "hint_level_ok") is False)
    cite_need = [r for r in ok if (r.get("grading") or {}).get("must_cite")]
    cite_ok = sum(1 for r in cite_need if jv(r, "citation") == "ok")
    spoken = sum(1 for r in ok if jv(r, "spoken_ok") is True)
    lat = sorted(r["latency_ms"] for r in ok if r["latency_ms"])

    print(f"\n{'═'*58}")
    print(f"答对    rubric {hit}/{total}" + (f"（{hit/total*100:.0f}%）" if total else ""))
    print(f"剧透    {spoil} 处；提示分级越级 {lvl} 道")
    print(f"引用    需要引用 {len(cite_need)} 道，给对来源 {cite_ok} 道")
    print(f"口语    {spoken}/{len(ok)} 道判为像说出来的")
    if lat:
        print(f"延迟    中位 {lat[len(lat)//2]/1000:.0f}s，最慢 {max(lat)/1000:.0f}s")
    print(f"耗时    {run_sec/60:.1f} 分钟跑完 {len(ok)} 道" + (f"，{len(dead)} 道失败" if dead else ""))
    print(f"{'═'*58}\n")
    for r in rows:
        j = r.get("judge") or {}
        rb = j.get("rubric") or []
        s = len([x for x in (j.get("spoiler") or []) if x["violated"]]) + (1 if j.get("leaked_future") else 0)
        mark = "✗" if r["error"] else ("!" if s else "✓")
        n = f"{len([x for x in rb if x['hit']])}/{len(rb)}" if rb else "—"
        print(f"{mark} {r['task_id']:<16} {n:>5}  " +
              (f"剧透{s} " if s else "     ") +
              (r["error"] or r["answer"])[:60])

    out = a.out or os.path.join(ROOT, "data", "runs", f"{a.container}-query-{int(t_all)}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"container": a.container, "kind": "query", "agent": a.agent,
               "judge_model": judge_mod.JUDGE_MODEL,
               "wall_sec": round(run_sec), "n": len(rows),
               "rubric_hit": hit, "rubric_total": total,
               "spoiler": spoil, "hint_level_bad": lvl,
               "cite_needed": len(cite_need), "cite_ok": cite_ok,
               "tasks": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n报告写到 {out}")


if __name__ == "__main__":
    main()
