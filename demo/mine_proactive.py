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



# ───────────────────── 直接扫画面出候选 ─────────────────────
#
# 只靠转写有个天花板：他不吭声的时候就没有候选，而且他嘴上说的困难有一半在画面上
# 根本看不出来（复核阶段刷掉的大多是这一类）。反过来从画面扫，出来的候选天生就是
# 可见的，不用再赌一次。
#
# 分工：**画面决定这算不算一道题、窗口在哪**（公平，因为 agent 也只有画面），
# **转写决定「什么才叫帮到了」**（他自己说出来的困惑，是最准的 help_points 依据）。

SWEEP_WIN = 120          # 一次看这么长一段
SWEEP_STRIDE = 80        # 往前挪这么多，留点重叠

SWEEP_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "worth": {"type": "boolean",
                  "description": "这一段值不值得让旁边的人开口。正常推进就是 false"},
        "kind": {"type": "string",
                 "enum": ["不知道这是什么", "卡住出不去", "找不到在哪", "方法用错了",
                          "怕/慌了", "刚做成一件事", "误解了规则", "无"]},
        "start_sec": {"type": "number", "description": "从哪一秒起说了有用，落在给你的时间范围内"},
        "end_sec": {"type": "number", "description": "到哪一秒为止；再晚说就没意义了"},
        "visible": {"type": "string", "description": "你从这串帧上看到了什么才这么判断。只写画面上真有的"},
        "scene": {"type": "string", "description": "这一段画面上有什么，写实"},
        "confidence": {"type": "number"},
    },
    "required": ["worth", "kind", "start_sec", "end_sec", "visible", "scene", "confidence"],
}

SWEEP_PROMPT = """你在看一段录像的连续截帧：有人第一次玩这个游戏 / 第一次用这个软件。

**先回答一个具体问题：从第一帧到最后一帧，这段时间里他推进了吗？**

推进了的样子：换了房间/区域/场景，界面从一个切到另一个，HUD 上的数字变了，
物体做出来了、门开了、任务提示更新了。只要看得出「现在的位置比刚才靠后」，就算推进。

没推进的样子：几帧下来还在同一片地方转，视角在变但位置没变；同一个菜单/面板一直开着；
同一个东西被反复对准或反复操作，屏幕上没有任何反馈；进度数字从头到尾没动；
同一个动作循环出现（掉下去、爬上来、又掉下去）。

**没推进，就是这一局要找的东西**——他大概率卡住了、迷路了、或者在反复试错。
这时 worth=true。

另外两种也算 worth=true：
- 屏幕上有明确的报错、警告、失败提示
- 明显刚完成一件事（一直打不开的门开了、做了半天的东西成了），值得接一句

worth=false 只有一种情况：他在正常推进，画面一路往前走。

注意别把「画面暗」「场景重复」「你看不懂在干嘛」当成没推进。判断依据是**位置和状态有没有往前**，
不是你看得清不清楚。真拿不准就 false。

worth=true 的时候，start_sec / end_sec 定在给你的时间范围里：从哪一秒起搭话有用，
到哪一秒为止再说就晚了。visible 写你到底看到了什么（比如「6:01 和 6:57 两帧都是同一片
树林空地，中间几帧只是视角在转，HUD 的收集数一直是 3/10」），别写「他看起来困惑」这种。"""


def sweep_window(video, t0, t1, key, n=8):
    """看一段画面，判断这一段值不值得开口。"""
    secs = [round(t0 + (t1 - t0) * i / (n - 1), 1) for i in range(n)]
    frames = [(s_, grab(video, s_)) for s_ in secs]
    frames = [(s_, f) for s_, f in frames if f]
    if len(frames) < 4:
        return None
    content = [{"type": "text", "text":
                f"这是同一段录像里按时间排的 {len(frames)} 帧，时间点分别是 "
                + "、".join(vtt.fmt(s_) for s_, _ in frames)
                + f"（秒数：{', '.join(str(int(s_)) for s_, _ in frames)}）。\n"
                + f"start_sec / end_sec 用秒数，落在 {int(t0)} 到 {int(t1)} 之间。\n\n"
                + SWEEP_PROMPT}]
    for s_, f in frames:
        content.append({"type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64," + f, "detail": "low"}})
    try:
        d = _post("https://api.openai.com/v1/chat/completions", {
            "model": MODEL,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "sweep", "strict": True, "schema": SWEEP_SCHEMA}},
        }, key)
        return json.loads(d["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"    [扫描失败] {str(e)[:100]}", flush=True)
        return None


FILLIN_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "need": {"type": "string", "description": "一句话说清他这会儿缺什么"},
        "help_points": {"type": "array", "items": {"type": "string"},
                        "description": "一句有用的话该说到什么，2-4 条，逐条可勾"},
        "must_not_say": {"type": "array", "items": {"type": "string"}},
        "hint_level": {"type": "string", "enum": ["direction_only", "full"]},
    },
    "required": ["need", "help_points", "must_not_say", "hint_level"],
}


def fill_in(cand, title, evidence, key):
    """画面定了「这是一道题」之后，再写「什么才算帮到了」。

    有转写就把这一段的原话给它——他自己说出来的困惑，比对着画面猜准得多。
    没转写也能写，只是依据只有画面。
    """
    ev = "\n".join(f"[{int(e['t'])}s] {e['text']}" for e in evidence) or "（这一段他没说话）"
    user = (f"素材：{title}\n"
            f"这一段（{vtt.fmt(cand['start_sec'])}–{vtt.fmt(cand['end_sec'])}）从画面上看是「{cand['kind']}」。\n"
            f"画面上看到的：{cand['visible']}\n"
            f"画面里有什么：{cand['scene']}\n\n"
            f"他这段时间自己说的话（只给你写判分标准用，被测的 agent 看不到）：\n{ev}\n\n"
            f"写清楚：他这会儿缺什么，以及一句真正帮到他的话应该说到什么。\n"
            f"help_points 要具体、可勾选，别写「给予鼓励」这种没法判的。\n"
            f"must_not_say 写这一刻不能说的：后面的剧情、完整解法步骤。\n"
            f"提示分级：游戏里的谜题多数 direction_only 只给方向；软件操作类的"
            f"（这个按钮在哪、这个参数干嘛）可以 full 直接讲清楚。")
    try:
        d = _post("https://api.openai.com/v1/chat/completions", {
            "model": MODEL,
            "messages": [{"role": "user", "content": user}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "fillin", "strict": True, "schema": FILLIN_SCHEMA}},
        }, key)
        return json.loads(d["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"    [补写失败] {str(e)[:100]}", flush=True)
        return None


def sweep_video(video, dur, title, lines, key):
    """从头到尾扫一遍画面，直接出题。"""
    out, t = [], 0
    while t < dur - 20:
        t1 = min(dur, t + SWEEP_WIN)
        r = sweep_window(video, t, t1, key)
        if r and r["worth"] and r["confidence"] >= 0.55 and r["kind"] != "无":
            a = max(t, min(r["start_sec"], t1 - 20))
            b = min(t1, max(r["end_sec"], a + 20))
            ev = [{"t": l["t"], "text": l["text"]} for l in lines if a - 10 <= l["t"] <= b + 5][:4]
            fi = fill_in({**r, "start_sec": a, "end_sec": b}, title, ev, key)
            if fi:
                out.append({"start_sec": a, "end_sec": b, "kind": r["kind"],
                            "visible": r["visible"], "scene": r["scene"],
                            "confidence": r["confidence"], "evidence": ev,
                            "from": "frames", **fi})
                print(f"  ✓ [{vtt.fmt(a)}–{vtt.fmt(b)}] {r['kind']} · {fi['need'][:40]}"
                      + (f"  依据 {len(ev)} 句" if ev else "  （他没说话）"), flush=True)
        elif r:
            print(f"    {vtt.fmt(t)}–{vtt.fmt(t1)} 正常", flush=True)
        t += SWEEP_STRIDE
    return out


# ────────────────────────────── main ──────────────────────────────

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    cid = args[0]
    vtt_path = args[1] if len(args) > 1 else None
    source = "both"
    for f in flags:
        if f.startswith("--from="):
            source = f.split("=", 1)[1]
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY 没设")

    src = json.load(open(os.path.join(ROOT, "data", "containers", f"{cid}.json"), encoding="utf-8"))
    video = os.path.join(ROOT, src["video"]["src"].lstrip("/"))
    if not os.path.exists(video):
        sys.exit(f"找不到视频 {video}")
    dur = src["video"]["duration"]

    lines = vtt.utterances(vtt_path) if vtt_path and os.path.exists(vtt_path) else []
    if not lines and source in ("transcript", "both"):
        if source == "transcript":
            sys.exit("没有转写，--from=transcript 跑不了")
        print("没有转写，只走画面这一路", flush=True)
        source = "frames"
    print(f"{cid}: 转写 {len(lines)} 句，视频 {vtt.fmt(dur)}，出题来源 {source}", flush=True)

    tasks, dropped = [], []

    # ── A) 从画面扫。出来的候选天生可见，不用再复核一遍
    frame_cands = []
    if source in ("frames", "both"):
        print("\n【一】扫画面", flush=True)
        frame_cands = sweep_video(video, dur, src["title"], lines, key)
        print(f"画面这一路 {len(frame_cands)} 个", flush=True)

    # ── B) 从转写挖。能捞到画面上不显眼但他自己说破了的时刻，要过一遍截帧复核
    tr_cands = []
    if source in ("transcript", "both") and lines:
        print("\n【二】挖转写", flush=True)
        t = 0
        while t < dur:
            seg = [l for l in lines if t <= l["t"] < t + CHUNK_SEC]
            if len(seg) >= 4:
                got = mine_chunk(seg, src["title"], key, t, min(dur, t + CHUNK_SEC))
                got = [c for c in got if c["confidence"] >= 0.55
                       and c["end_sec"] - c["start_sec"] >= 20]
                tr_cands.extend(got)
            t += CHUNK_SEC - OVERLAP_SEC
        # 跟画面那一路撞车的先扔掉，省下复核的钱
        tr_cands = [c for c in tr_cands
                    if all(abs(c["start_sec"] - f["start_sec"]) >= MIN_GAP_SEC for f in frame_cands)]
        tr_cands.sort(key=lambda c: (-c["confidence"], c["start_sec"]))
        uniq = []
        for c in tr_cands:
            if all(abs(c["start_sec"] - k["start_sec"]) >= MIN_GAP_SEC for k in uniq):
                uniq.append(c)
        print(f"转写这一路 {len(uniq)} 个候选，逐个截帧复核…", flush=True)
        for c in uniq:
            v = verify(c, video, key)
            print(f"  {'✓' if v['visible_ok'] else '✗'} [{vtt.fmt(c['start_sec'])}–"
                  f"{vtt.fmt(c['end_sec'])}] {c['kind']} · {c['need'][:36]}", flush=True)
            if v["visible_ok"]:
                frame_cands.append({**c, "visible": v["visible"], "scene": v["scene"],
                                    "from": "transcript"})
            else:
                dropped.append({**c, "drop_reason": v["note"]})

    # ── 合并、去重、编号
    frame_cands.sort(key=lambda c: c["start_sec"])
    merged = []
    for c in frame_cands:
        if merged and c["start_sec"] - merged[-1]["start_sec"] < MIN_GAP_SEC:
            # 挨太近的留置信度高的那个
            if c.get("confidence", 0) > merged[-1].get("confidence", 0):
                merged[-1] = c
            continue
        merged.append(c)

    for c in merged:
        tasks.append({
            "task_id": f"{cid}-p{len(tasks)+1:02d}",
            "type": "proactive",
            "window_sec": [round(c["start_sec"]), round(c["end_sec"])],
            "context_window_sec": [0, round(c["end_sec"])],
            "kind": c["kind"],
            "need": c["need"],
            "visible": c["visible"],
            "scene": c["scene"],
            "hint_level": c["hint_level"],
            "found_by": c.get("from", "frames"),
            "evidence": c.get("evidence", []),
            "grading": {
                "help_points": c["help_points"],
                "must_not_say": c["must_not_say"],
            },
        })

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
    by_frame = sum(1 for t in tasks if t["found_by"] == "frames")
    with_ev = sum(1 for t in tasks if t["evidence"])
    print(f"\n写出 {path}：{len(tasks)} 题"
          f"（画面挖到 {by_frame}，转写挖到 {len(tasks)-by_frame}；"
          f"{with_ev} 题有主播原话作依据），复核刷掉 {len(dropped)}", flush=True)


if __name__ == "__main__":
    main()
