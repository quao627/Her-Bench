"""起评测服务、把 agent 拉起来、等它跑完、判分。

    python3 bench/run_eval.py portal-e01 --agent agents/prepared.py --limit 1300

agent 跑在另一个进程里，跟这边只有 HTTP（见 agents/PROTOCOL.md）。它拿不到题、
拿不到判分标准、拿不到这个仓库里除协议之外的任何东西。用别的语言写也行，
`--agent` 后面跟能跑起来的命令就够。

agent 崩了、卡住、或者一句话都不说，都不算评测的问题——照实记下来，该零分零分。

    --agent CMD    agent 的启动命令，默认 agents/prepared.py
    --limit N      只跑前 N 秒视频
    --timeout N    agent 多久没动静就算它挂了（秒），默认 600
    --no-judge     只跑不判
"""

import argparse
import concurrent.futures as futures
import json
import os
import shlex
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import frames as frames_mod
import world as world_mod
import judge as judge_mod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAME_STEP = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container")
    ap.add_argument("--agent", default="agents/prepared.py")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    path = os.path.join(ROOT, "data", "containers", f"{a.container}.json")
    if not os.path.exists(path):
        sys.exit(f"没有这个 container：{path}")
    C = json.load(open(path, encoding="utf-8"))
    video = os.path.join(ROOT, C["video"]["src"].lstrip("/"))
    dur = min(C["video"]["duration"], a.limit) if a.limit else C["video"]["duration"]
    tasks = [t for t in C["tasks"] if t["type"] == "query" and t["anchor_sec"] <= dur]
    if not tasks:
        sys.exit("这段里没有问答题")

    agent_cmd = shlex.split(a.agent)
    if len(agent_cmd) == 1 and agent_cmd[0].endswith(".py"):
        agent_cmd = [sys.executable, agent_cmd[0]]

    print(f"{a.container}：{C['title']}")
    print(f"看前 {dur//60} 分钟，问答题 {len(tasks)} 道")
    print(f"agent = {' '.join(agent_cmd)}（另一个进程，只走 HTTP）\n", flush=True)

    t_all = time.time()
    frames = frames_mod.Frames(video, step=FRAME_STEP, limit=dur)
    print(f"抽帧 {len(frames)} 张，用了 {frames.extract_sec:.0f}s\n", flush=True)

    def log(kind, t, msg):
        print(f"  [{int(t)//60}:{int(t)%60:02d}] {msg}", flush=True)

    W = world_mod.World(C, frames, tasks, frame_step=FRAME_STEP, log=log)
    httpd, port = world_mod.serve(W)
    env = {**os.environ, "HERBENCH_WORLD": f"http://127.0.0.1:{port}"}

    proc, agent_err = None, None
    try:
        proc = subprocess.Popen(agent_cmd, cwd=ROOT, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        deadline = time.time() + a.timeout
        while proc.poll() is None and time.time() < deadline and not W.done:
            time.sleep(0.3)
        if proc.poll() is None:
            reason = "跑完了但没退出" if W.done else f"超过 {a.timeout}s 没跑完"
            proc.kill()
            agent_err = reason
        elif proc.returncode != 0 and not W.done:
            agent_err = f"agent 进程退出码 {proc.returncode}"
        out = (proc.stdout.read() or "").strip() if proc.stdout else ""
        if agent_err and out:
            agent_err += "\n" + out[-800:]
    finally:
        httpd.shutdown()
        frames.close()

    r = W.result()
    rows = r["answers"]
    if agent_err:
        print(f"\n⚠ agent 那边出问题了：{agent_err}\n", flush=True)

    if rows and not a.no_judge:
        print("\n判分…", flush=True)
        def one(x):
            if not x["answer"]:
                x["judge"] = {"error": "一个字都没说"}
                return
            code, v = judge_mod.judge_run(x, {"answer": x["answer"], "citations": []})
            x["judge"] = v if code == 200 else {"error": str(v)[:200]}
        with futures.ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(one, rows))

    jv = lambda x, k, d=None: (x.get("judge") or {}).get(k, d)
    hit = sum(len([y for y in (jv(x, "rubric") or []) if y["hit"]]) for x in rows)
    tot = sum(len(jv(x, "rubric") or []) for x in rows)
    spoil = sum(len([y for y in (jv(x, "spoiler") or []) if y["violated"]])
                + (1 if jv(x, "leaked_future") else 0) for x in rows)
    gave_up = [x for x in rows if x["gave_up"]]
    lat = sorted(x["latency_sec"] for x in rows if not x["gave_up"])
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
    wall = time.time() - t_all

    print(f"\n{'═'*62}")
    print(f"agent     {' '.join(agent_cmd)}")
    print(f"看了      {r['ticks']} 格" +
          (f"，因为想得慢错过 {r['missed_frames']} 帧" if r["missed_frames"] else "，一帧没漏"))
    print(f"回话      {len(rows) - len(gave_up)}/{len(tasks)} 道"
          + (f"，放弃 {len(gave_up)} 道" if gave_up else "")
          + f"；主动开口 {len([s for s in r['says'] if not s['answering']])} 次")
    print(f"答对      rubric {hit}/{tot}" + (f"（{hit/tot*100:.0f}%）" if tot else ""))
    print(f"剧透      {spoil} 处")
    print(f"延迟      中位 {med(lat):.1f}s 视频时间（从主播问出口到它答上）")
    print(f"跑完      {wall/60:.1f} 分钟，视频 {dur/60:.0f} 分，快 {dur/max(1,wall):.1f} 倍")
    print(f"{'═'*62}\n")
    for x in rows:
        rb = jv(x, "rubric") or []
        n = f"{len([y for y in rb if y['hit']])}/{len(rb)}" if rb else "—"
        print(f"{x['task_id']:<16} {x['latency_sec']:>5.1f}s {n:>5}  "
              f"{'（放弃作答）' if x['gave_up'] else x['answer'][:46]}")

    name = os.path.basename(agent_cmd[-1]).replace(".py", "")
    out = a.out or os.path.join(ROOT, "data", "runs", f"{a.container}-{name}-{int(t_all)}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"container": a.container, "agent": " ".join(agent_cmd),
               "agent_error": agent_err, "limit_sec": dur, "wall_sec": round(wall),
               "rubric_hit": hit, "rubric_total": tot, "spoiler": spoil,
               "gave_up": len(gave_up), "latency_median_sec": med(lat),
               **{k: r[k] for k in ("ticks", "missed_frames", "video_sec_used", "says")},
               "tasks": rows}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n报告写到 {out}")
    if agent_err:
        sys.exit(2)


if __name__ == "__main__":
    main()
