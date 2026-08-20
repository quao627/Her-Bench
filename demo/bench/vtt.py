"""把 YouTube 自动字幕的 VTT 变成干净的 {t, text} 序列。

自动字幕是滚动式的：同一句话会在连续好几个 cue 里重复出现，每次只多冒出一两个词，
还夹着 <00:00:01.079><c>词</c> 这种逐词时间戳。直接按 cue 读会得到一堆重复。

这里的做法是把所有 cue 拼成一条词流（词 + 它自己的时间戳），去掉相邻重复，
再按停顿切成一句一句。切句用停顿而不是标点，因为自动字幕根本没有标点。
"""

import re
import sys

TS = re.compile(r"(\d\d):(\d\d):(\d\d)\.(\d\d\d)")
WORD_TS = re.compile(r"<(\d\d:\d\d:\d\d\.\d\d\d)>")
TAG = re.compile(r"</?c[^>]*>")


def _sec(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def _parse_ts(text):
    m = TS.match(text)
    return _sec(*m.groups()) if m else None


def words(path):
    """VTT → [(秒, 词)]，逐词时间戳，已去掉滚动重复。

    自动字幕每个 cue 一般是两行：第一行是上一句的完整文本（结转，没有逐词时间戳），
    第二行才是这一轮新冒出来的词，带 <hh:mm:ss.mmm> 逐词时间戳。只收带逐词时间戳
    的那一行，结转行整行丢掉，重复就没了。
    """
    raw = open(path, encoding="utf-8", errors="replace").read()
    blocks = raw.split("\n\n")
    timed_any = any(WORD_TS.search(b) for b in blocks)
    out, seen_end = [], -1.0

    for block in blocks:
        lines = [l for l in block.strip().split("\n") if l.strip() and l != "WEBVTT"]
        if not lines:
            continue
        head = next((l for l in lines if "-->" in l), None)
        if not head:
            continue
        start = _parse_ts(head.split("-->")[0].strip())
        if start is None:
            continue
        body_lines = [l for l in lines if "-->" not in l]
        if timed_any:
            # 只要带逐词时间戳的那一行；一个 cue 里最多一行是新内容
            body_lines = [l for l in body_lines if WORD_TS.search(l)]
        if not body_lines:
            continue

        for line in body_lines:
            parts = WORD_TS.split(TAG.sub("", line))
            cur = start
            chunks = [(start, parts[0])]
            for i in range(1, len(parts) - 1, 2):
                cur = _parse_ts(parts[i]) or cur
                chunks.append((cur, parts[i + 1]))
            for t, seg in chunks:
                for w in seg.split():
                    if t < seen_end - 0.05:      # 时间倒流 = 又抄了一遍，丢掉
                        continue
                    out.append((round(t, 2), w))
                    seen_end = t
    return out


def utterances(path, gap=1.6, max_sec=14):
    """按停顿切句 → [{'t': 起始秒, 'end': 结束秒, 'text': 一句话}]"""
    ws = words(path)
    if not ws:
        return []
    lines, cur, t0, prev = [], [], ws[0][0], ws[0][0]
    for t, w in ws:
        if cur and (t - prev > gap or t - t0 > max_sec):
            lines.append({"t": round(t0, 1), "end": round(prev, 1), "text": " ".join(cur)})
            cur, t0 = [], t
        cur.append(w)
        prev = t
    if cur:
        lines.append({"t": round(t0, 1), "end": round(prev, 1), "text": " ".join(cur)})
    return lines


def fmt(sec):
    sec = int(sec)
    return f"{sec // 3600:d}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 \
        else f"{sec // 60:d}:{sec % 60:02d}"


if __name__ == "__main__":
    u = utterances(sys.argv[1])
    print(f"{len(u)} 句，覆盖到 {fmt(u[-1]['end'])}")
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    for x in u[:n]:
        print(f"  [{fmt(x['t'])}] {x['text']}")
