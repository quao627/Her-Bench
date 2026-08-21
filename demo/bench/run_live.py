"""跑一遍评测，agent 可换。

    python3 bench/run_live.py portal-e01 --agent prepared --limit 1300
    python3 bench/run_live.py portal-e01 --agent reactive --limit 1300

harness 只驱动世界：按视频时间推画面、到锚点递问题、记下 agent 说了什么、判分。
agent 有没有后台、备不备料、备多密，是 agent 自己的事，这个文件不知道也不需要知道。

唯一强制的是时间：agent 花掉的墙钟时间折算成视频时间，后台通道一次一个活，
扔进去的东西要等实测耗时过去才拿得到。想得慢的 agent 在真实场景里就是会错过时机，
这条绕不过去。

    --agent NAME       reactive（只有前台）或 prepared（前台+后台备料）
    --brief N          只对 prepared 有意义：它自己的备料节奏，秒
    --limit N          只跑前 N 秒视频
    --no-judge         只跑不判
"""

import argparse
import concurrent.futures as futures
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import harness
import judge as judge_mod
from agents import REGISTRY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME_STEP = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container")
    ap.add_argument("--agent", default="prepared", choices=sorted(REGISTRY))
    ap.add_argument("--brief", type=int, default=120)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--backend", default="http://localhost:8787")
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

    kwargs = {"backend": a.backend}
    if a.agent == "prepared":
        kwargs["brief_every"] = a.brief
    agent = REGISTRY[a.agent](**kwargs)

    print(f"{a.container}：{C['title']}")
    print(f"agent = {agent.name}（{agent.desc}）")
    print(f"看前 {dur//60} 分钟，问答题 {len(tasks)} 道\n", flush=True)

    t_all = time.time()
    frames = harness.Frames(video, step=FRAME_STEP, limit=dur)
    print(f"抽帧 {len(frames)} 张，用了 {frames.extract_sec:.0f}s\n", flush=True)

    def log(kind, sec, msg):
        print(f"  [{int(sec)//60}:{int(sec)%60:02d}] {msg}", flush=True)

    try:
        r = harness.run(agent, C, frames, tasks, frame_step=FRAME_STEP, on_event=log)
    finally:
        frames.close()
    rows = r["answers"]
    run_sec = time.time() - t_all

    if not a.no_judge:
        print("\n判分…", flush=True)
        def one(x):
            code, v = judge_mod.judge_run(x, {"answer": x["answer"],
                                              "citations": x.get("citations") or []})
            x["judge"] = v if code == 200 else {"error": str(v)[:200]}
        with futures.ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(one, rows))

    jv = lambda x, k, d=None: (x.get("judge") or {}).get(k, d)
    hit = sum(len([y for y in (jv(x, "rubric") or []) if y["hit"]]) for x in rows)
    tot = sum(len(jv(x, "rubric") or []) for x in rows)
    spoil = sum(len([y for y in (jv(x, "spoiler") or []) if y["violated"]])
                + (1 if jv(x, "leaked_future") else 0) for x in rows)
    fast = [x for x in rows if x.get("served") == "手上就有"]
    lat = sorted(x["latency_ms"] for x in rows if x.get("latency_ms"))
    med = lambda xs: sorted(xs)[len(xs)//2] if xs else 0
    ln = r["lane"]

    print(f"\n{'═'*60}")
    print(f"agent     {agent.name}")
    print(f"后台      扔了 {ln['submitted']} 个活"
          + (f"，通道占着扔不进去 {ln['busy_rejected']} 次" if ln["busy_rejected"] else "")
          + (f"，被主播开口掐掉 {ln['cancelled']} 次" if ln["cancelled"] else "")
          + (f"；每个占 {min(ln['durations']):.0f} 到 {max(ln['durations']):.0f} 秒视频时间"
             if ln["durations"] else ""))
    print(f"答对      rubric {hit}/{tot}" + (f"（{hit/tot*100:.0f}%）" if tot else ""))
    print(f"剧透      {spoil} 处")
    print(f"延迟      中位 {med(lat)/1000:.1f}s；其中手上就有 {len(fast)}/{len(rows)} 道")
    print(f"跑完      {run_sec/60:.1f} 分钟（视频 {dur/60:.0f} 分，快 {dur/max(1,run_sec):.1f} 倍）")
    print(f"{'═'*60}\n")
    for x in rows:
        rb = jv(x, "rubric") or []
        n = f"{len([y for y in rb if y['hit']])}/{len(rb)}" if rb else "—"
        print(f"{x['task_id']:<16} {x.get('served','—'):<6} {x['latency_ms']/1000:>5.1f}s "
              f"{n:>5}  {x['answer'][:46]}")

    out = a.out or os.path.join(ROOT, "data", "runs",
                                f"{a.container}-{agent.name}-{int(t_all)}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"container": a.container, "agent": agent.name, "brief_every": kwargs.get("brief_every"),
               "limit_sec": dur, "wall_sec": round(run_sec),
               "rubric_hit": hit, "rubric_total": tot, "spoiler": spoil,
               "latency_median_ms": med(lat), "served_fast": len(fast),
               "lane": ln, "tasks": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n报告写到 {out}")


if __name__ == "__main__":
    main()
