"""从主播的转写里挖「他确实需要帮助」的时刻，出成纯 proactive 的题。

跟原来那套题的区别：

- 没有人向 agent 提问。评测时原声整条不给，agent 只看得到画面帧，
  什么时候开口、说什么，全由它自己判断。
- 转写只在出题时用，用来找出「他这会儿真的卡住了/真的在纳闷」的时刻，
  并作为 evidence 存进题里。跑评测时 agent 一个字都看不到。
- 每道题对应一段时间窗口，不是一个时间点。窗口内开口才算接住。

因为 agent 只有画面，所以出题时多一条硬要求：这个时刻的困难必须在画面上
也看得出来（人物反复摔在同一处、菜单翻来翻去找不到、同一个界面卡着不动）。
只在嘴上抱怨、画面上完全看不出来的，不出题——那种题无解。

用法：
    python3 mine_proactive.py stanleyparable-e01 \\
        "../videos/stanley_parable/01_First time playing The Stanley Parable! [D2CKwN57S5Y].en.vtt"
"""

import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

import vtt

ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("HERBENCH_MINE_MODEL", "gpt-5.4")
OUT_DIR = os.path.join(ROOT, "data", "proactive")

CHUNK_SEC = 240          # 一次给模型看五分钟转写
OVERLAP_SEC = 60         # 相邻块重叠，免得卡在边界上的事件被切断
MIN_GAP_SEC = 45         # 两道题之间至少隔这么久，不然全挤在一处


# ────────────────────────────── LLM ──────────────────────────────

CAND_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "moments": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "start_sec": {"type": "number", "description": "从哪一秒起，帮他一把是有用的"},
                "end_sec": {"type": "number", "description": "到哪一秒为止；再晚他自己就弄明白了，说了也没用"},
                "kind": {"type": "string",
                         "enum": ["不知道这是什么", "卡住出不去", "找不到在哪", "方法用错了",
                                  "怕/慌了", "刚做成一件事", "误解了规则"]},
                "need": {"type": "string", "description": "一句话说清他这会儿缺什么"},
                "look_for": {"type": "string",
                             "description": "如果这事是真的，画面上应该能找到什么。写成待验证的线索，"
                                            "不要当成已知事实"},
                "evidence": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {"t": {"type": "number"}, "text": {"type": "string"}},
                    "required": ["t", "text"]},
                    "description": "让你判定他需要帮助的原话，原样抄，别改写"},
                "help_points": {"type": "array", "items": {"type": "string"},
                                "description": "一句有用的话应该说到什么，2-4 条，逐条可勾"},
                "must_not_say": {"type": "array", "items": {"type": "string"},
                                 "description": "这一刻不能说的：后面的剧情、完整解法步骤"},
                "hint_level": {"type": "string", "enum": ["direction_only", "full"]},
                "confidence": {"type": "number", "description": "0-1，你有多确信他真的需要帮助"},
            },
            "required": ["start_sec", "end_sec", "kind", "need", "look_for",
                         "evidence", "help_points", "must_not_say", "hint_level", "confidence"]}}
    },
    "required": ["moments"],
}

MINE_SYSTEM = """你在为一个评测挑素材。素材是一段真实录像：有人第一次玩某个游戏、
或者第一次上手某个软件，边玩边自言自语。

评测要考的是一个「陪看 agent」：它全程只看得到画面，听不到任何声音，也没有人向它提问。
它得自己判断什么时候该开口帮一把。

你的活是从转写里找出**他确实需要帮助的时刻**，每个时刻出成一道题。

什么算需要帮助：
- 他明确在纳闷：「这是啥」「这怎么用」「我该干嘛」
- 他卡住了：同一个地方反复试、反复失败、开始烦躁
- 他找不到东西：翻菜单翻半天、来回找某个按钮
- 他理解错了：说出一个明显错误的判断，然后照着这个错的走
- 他吓到了、慌了，需要一句安抚
- 他刚做成一件难事，值得接一句

什么不算：
- 只是在闲聊、念叨剧情、跟观众打招呼
- 他嘴上嘀咕一句但马上自己解决了
- 纯情绪表达，没有任何可以帮上的内容

**最重要的一条**：agent 只看得到画面。所以你挑的时刻，必须是在画面上也看得出来的
——人一直摔在同一个地方、菜单被翻来翻去、同一个界面停着不动、屏幕上有报错。
只在嘴上抱怨而画面上完全没有痕迹的，不要出题，那种题 agent 根本没法答。

你看不到画面，所以 look_for 写的是**待验证的线索**：如果这事是真的，画面上应该能找到什么。
写成「应该能看到 X」这种，别当成已知事实写。后面会有一步真的去截帧核，核不上就丢掉。

窗口怎么定：start_sec 是「从这时候起说了有用」，end_sec 是「再晚说就没意义了」
（他自己解决了，或者已经走开了）。一般 20 到 90 秒。窗口不是越大越好，
定得太宽等于白送分。

help_points 写的是「一句真正有用的话应该说到什么」，要具体、可勾选。
注意提示分级：游戏里的谜题多数是 direction_only，只给方向；软件操作类的
（这个按钮在哪、这个参数干嘛的）可以 full，直接讲清楚。

宁缺毋滥。一段五分钟的转写里，通常只有零到三个真正值得出题的时刻。
confidence 低于 0.6 的就别放进来。"""


def _post(url, body, key, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def mine_chunk(lines, title, key, t_from, t_to):
    body = "\n".join(f"[{vtt.fmt(l['t'])} = {int(l['t'])}s] {l['text']}" for l in lines)
    user = (f"素材：{title}\n"
            f"这一段是视频的 {vtt.fmt(t_from)} 到 {vtt.fmt(t_to)}。\n"
            f"时间戳给的是秒数，start_sec / end_sec / evidence 里的 t 都用这个秒数，别自己换算。\n\n"
            f"转写：\n{body}")
    try:
        d = _post("https://api.openai.com/v1/chat/completions", {
            "model": MODEL,
            "messages": [{"role": "system", "content": MINE_SYSTEM},
                         {"role": "user", "content": user}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "moments", "strict": True, "schema": CAND_SCHEMA}},
        }, key)
        return json.loads(d["choices"][0]["message"]["content"])["moments"]
    except urllib.error.HTTPError as e:
        print(f"    [提取失败 {e.code}] {e.read().decode()[:160]}", flush=True)
        return []
    except Exception as e:
        print(f"    [提取失败] {e}", flush=True)
        return []


# ─────────────────────── 截帧 + 视觉复核 ───────────────────────

VERIFY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "visible_ok": {"type": "boolean",
                       "description": "只看这串画面，能不能察觉这一段不太顺（或者确实发生了值得接一句的事）"},
        "visible": {"type": "string",
                    "description": "看得出来的话，写清楚从这串帧上看到了什么才这么判断。"
                                   "只写画面上真有的，写成一句人话"},
        "scene": {"type": "string", "description": "这一段画面上有什么，写实，别推测心理"},
        "note": {"type": "string", "description": "看不出来的话说清为什么"},
    },
    "required": ["visible_ok", "visible", "scene", "note"],
}


def _ffmpeg():
    """系统里不一定装了 ffmpeg，但 imageio-ffmpeg 自带一份，用它兜底。"""
    import shutil
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
        FFMPEG = _ffmpeg()
    out = tempfile.mktemp(suffix=".jpg")
    subprocess.run([FFMPEG, "-nostdin", "-loglevel", "error", "-ss", str(max(0, sec)),
                    "-i", video, "-frames:v", "1", "-vf", f"scale={width}:-1",
                    "-q:v", "5", "-y", out], check=False)
    if not os.path.exists(out) or os.path.getsize(out) < 500:
        return None
    b = base64.b64encode(open(out, "rb").read()).decode()
    os.unlink(out)
    return b


def verify(cand, video, key, n=8):
    """截一串帧，让模型自己看这一段画面上能不能看出不对劲。

    候选是纯靠转写提的，提的人看不到画面，所以 look_for 只是线索。这一步才是
    定生死的：只看画面能不能察觉这里不太顺，能的话 visible 由这一步写，
    保证写进题里的都是画面上真有的东西。
    """
    a, b = cand["start_sec"], cand["end_sec"]
    # 铺垫只取两帧，剩下的全给窗口本身。之前按 [start-30, end] 均匀取，碰上十几秒的
    # 窗口会有七八成的帧落在铺垫里，判出来的是铺垫不是窗口。
    lead = [round(max(0, a - 30), 1), round(max(0, a - 12), 1)]
    inner = [round(a + (b - a) * i / max(1, n - 3), 1) for i in range(n - 2)]
    secs = sorted(set(lead + inner))
    frames = [(s_, grab(video, s_)) for s_ in secs]
    frames = [(s_, f) for s_, f in frames if f]
    if len(frames) < 3:
        return {"visible_ok": False, "visible": "", "scene": "", "note": "截帧失败"}
    content = [{"type": "text", "text":
                f"下面是同一段录像里按时间顺序排的 {len(frames)} 帧，时间点分别是 "
                + "、".join(vtt.fmt(s_) for s_, _ in frames) + "。\n"
                f"头两帧是铺垫（窗口之前），从 {vtt.fmt(a)} 起才是要判的那一段，一直到 {vtt.fmt(b)}。\n"
                f"visible 只写要判的那一段，铺垫帧只是给你做对比用的。\n\n"
                f"背景：这是有人第一次玩/第一次用这个东西的录像。有人根据他的自言自语判断，"
                f"这一段他大概{cand['kind']}：{cand['need']}\n"
                f"提出的人看不到画面，他猜画面上可能能找到：{cand['look_for']}\n\n"
                f"你的活：**只看这串帧**，判断一个听不到声音、只看得到画面的人，"
                f"能不能察觉这一段不太顺——比如几帧下来还在同一个地方、同一个界面翻来翻去、"
                f"同一段路来回走、进度条/场景一直没变、屏幕上有报错或提示。"
                f"如果这一段是「刚做成一件事」，那就判断画面上有没有可辨认的完成迹象。\n"
                f"能察觉就 visible_ok=true，并在 visible 里写清楚你从这串帧上看到了什么。"
                f"只写画面上真有的，别把上面那段背景抄进去。\n"
                f"察觉不到就 false：画面一直在正常推进、或者这几帧看不出任何异常，都算 false。"}]
    for s_, f in frames:
        content.append({"type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64," + f, "detail": "low"}})
    try:
        d = _post("https://api.openai.com/v1/chat/completions", {
            "model": MODEL,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "verify", "strict": True, "schema": VERIFY_SCHEMA}},
        }, key)
        return json.loads(d["choices"][0]["message"]["content"])
    except Exception as e:
        return {"visible_ok": False, "visible": "", "scene": "", "note": f"复核调用失败: {e}"}


# ────────────────────────────── main ──────────────────────────────

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cid, vtt_path = sys.argv[1], sys.argv[2]
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY 没设")

    src = json.load(open(os.path.join(ROOT, "data", "containers", f"{cid}.json"), encoding="utf-8"))
    video = os.path.join(ROOT, src["video"]["src"].lstrip("/"))
    if not os.path.exists(video):
        sys.exit(f"找不到视频 {video}")
    dur = src["video"]["duration"]

    lines = vtt.utterances(vtt_path)
    print(f"{cid}: {len(lines)} 句转写，视频 {vtt.fmt(dur)}", flush=True)

    # 1) 分块提候选
    cands, t = [], 0
    while t < dur:
        seg = [l for l in lines if t <= l["t"] < t + CHUNK_SEC]
        if len(seg) >= 4:
            got = mine_chunk(seg, src["title"], key, t, min(dur, t + CHUNK_SEC))
            got = [c for c in got if c["confidence"] >= 0.55]
            print(f"  {vtt.fmt(t)}–{vtt.fmt(min(dur, t+CHUNK_SEC))}  候选 {len(got)}", flush=True)
            cands.extend(got)
        t += CHUNK_SEC - OVERLAP_SEC

    # 2) 窗口太短的丢掉：十几秒对一个几秒才看一帧的 agent 不公平
    before = len(cands)
    cands = [c for c in cands if c["end_sec"] - c["start_sec"] >= 20]
    if before != len(cands):
        print(f"窗口短于 20 秒的丢掉 {before - len(cands)} 个", flush=True)

    # 3) 去掉挨太近的，按置信度留强的
    cands.sort(key=lambda c: (-c["confidence"], c["start_sec"]))
    kept = []
    for c in cands:
        if all(abs(c["start_sec"] - k["start_sec"]) >= MIN_GAP_SEC for k in kept):
            kept.append(c)
    kept.sort(key=lambda c: c["start_sec"])
    print(f"去重后 {len(kept)} 个候选，开始截帧复核…", flush=True)

    # 4) 逐个截帧复核
    tasks, dropped = [], []
    for i, c in enumerate(kept):
        v = verify(c, video, key)
        mark = "✓" if v["visible_ok"] else "✗"
        print(f"  {mark} [{vtt.fmt(c['start_sec'])}–{vtt.fmt(c['end_sec'])}] {c['kind']} · {c['need'][:38]}",
              flush=True)
        if not v["visible_ok"]:
            dropped.append({**c, "drop_reason": v["note"]})
            continue
        tasks.append({
            "task_id": f"{cid}-p{len(tasks)+1:02d}",
            "type": "proactive",
            "window_sec": [round(c["start_sec"]), round(c["end_sec"])],
            "context_window_sec": [0, round(c["end_sec"])],
            "kind": c["kind"],
            "need": c["need"],
            "visible": v["visible"],
            "scene": v["scene"],
            "hint_level": c["hint_level"],
            "evidence": c["evidence"],
            "grading": {
                "help_points": c["help_points"],
                "must_not_say": c["must_not_say"],
            },
        })
        time.sleep(0.2)

    os.makedirs(OUT_DIR, exist_ok=True)
    out = {
        "container_id": cid,
        "title": src["title"],
        "video": src["video"],
        "thumbs": src.get("thumbs"),
        "chapters": src.get("chapters", []),
        "mode": "proactive_only",
        "note": "评测时不给原声、不给转写、不给题目，agent 只看画面帧自己决定什么时候开口。"
                "evidence 是出题依据，判分时给判分员看，不给被测的 agent。",
        "tasks": tasks,
    }
    path = os.path.join(OUT_DIR, f"{cid}.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if dropped:
        json.dump(dropped, open(os.path.join(OUT_DIR, f"{cid}.dropped.json"), "w",
                                encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写出 {path}：{len(tasks)} 题，复核刷掉 {len(dropped)} 个", flush=True)


if __name__ == "__main__":
    main()
