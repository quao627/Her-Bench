#!/usr/bin/env python3
"""一键把 container 需要的视频拉到位。

视频不入库（体积大、版权不属于我们），但每个 container 清单里都写着它是哪个视频
（`video.source_url`）和该放在哪（`video.src`），所以这件事可以完全自动化：

    python3 fetch_videos.py               # 把缺的都下下来
    python3 fetch_videos.py --check       # 只报状态，不下载
    python3 fetch_videos.py hff-p1 mc-e01 # 只下指定的几个

下载格式刻意挑 H.264 + AAC 的 mp4：浏览器 <video> 能直接播，省掉一次转码。
拿不到这个组合时才退回「下最好的再转码」，那条路需要 ffmpeg。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # demo/bench
DEMO = os.path.dirname(HERE)
CONTAINERS = os.path.join(DEMO, "data", "containers")
MEDIA = os.path.join(DEMO, "media")

# 浏览器兼容优先：720p 以内的 avc1 视频 + mp4a 音频，合成 mp4。
# 拿不到就退到 best，再由 ffmpeg 转码（--remux 不够，源可能是 vp9/opus）。
FORMAT = "bv*[vcodec^=avc1][height<=720]+ba[acodec^=mp4a]/b[ext=mp4][height<=720]/b"


def manifests(only=None):
    out = []
    for fn in sorted(os.listdir(CONTAINERS)):
        if not fn.endswith(".json") or fn == "index.json":
            continue
        with open(os.path.join(CONTAINERS, fn)) as f:
            m = json.load(f)
        cid = m.get("container_id") or fn[:-5]
        if only and cid not in only:
            continue
        video = m.get("video") or {}
        if not video.get("src") or not video.get("source_url"):
            print(f"  {cid}: 清单里没写 src 或 source_url，跳过")
            continue
        out.append({"id": cid, "title": m.get("title", ""),
                    "path": os.path.join(MEDIA, os.path.basename(video["src"])),
                    "url": video["source_url"],
                    "duration": video.get("duration")})
    return out


def probe_duration(path):
    """有 ffprobe 就用它核一下时长，没有就算了——这只是个校验，不是必需品。"""
    if not shutil.which("ffprobe"):
        return None
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", path],
                           capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except Exception:
        return None


def status(v):
    if not os.path.exists(v["path"]):
        return "缺失", None
    size_mb = os.path.getsize(v["path"]) / 1e6
    got = probe_duration(v["path"])
    want = v["duration"]
    if got and want and abs(got - want) > max(30, want * 0.05):
        return f"时长对不上（清单 {want:.0f}s，文件 {got:.0f}s）", size_mb
    return "就位", size_mb


def download(v):
    os.makedirs(MEDIA, exist_ok=True)
    cmd = ["yt-dlp", "-f", FORMAT, "--merge-output-format", "mp4",
           "-o", v["path"], "--no-playlist", v["url"]]
    print(f"  $ {' '.join(cmd[:5])} … {v['url']}", flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        return False, "yt-dlp 失败（视频可能已下架或需要登录）"
    if not os.path.exists(v["path"]):
        return False, "yt-dlp 说成功了，但文件不在预期位置"
    return True, None


def main():
    ap = argparse.ArgumentParser(description="按 container 清单下载视频到 demo/media/")
    ap.add_argument("containers", nargs="*", help="只处理这几个 container_id，默认全部")
    ap.add_argument("--check", action="store_true", help="只报状态，不下载")
    args = ap.parse_args()

    vids = manifests(set(args.containers) or None)
    if not vids:
        print("没有匹配的 container。可用的："
              + ", ".join(v["id"] for v in manifests()))
        return 1

    print(f"{len(vids)} 个 container，媒体目录 {MEDIA}\n")
    todo = []
    for v in vids:
        st, size = status(v)
        size_s = f"{size:.0f}MB" if size else "—"
        print(f"  {v['id']:22} {st:34} {size_s}")
        if st != "就位":
            todo.append(v)

    if args.check:
        print(f"\n{len(vids) - len(todo)} 个就位，{len(todo)} 个待下载")
        return 0
    if not todo:
        print("\n全部就位，没什么要做的。")
        return 0

    if not shutil.which("yt-dlp"):
        print("\n需要 yt-dlp（没找到）：")
        print("  brew install yt-dlp        # 或 pipx install yt-dlp / pip install -U yt-dlp")
        print("合成 mp4 还需要 ffmpeg：brew install ffmpeg")
        return 1
    if not shutil.which("ffmpeg"):
        print("\n提醒：没有 ffmpeg，yt-dlp 无法把分离的音视频流合成 mp4。")
        print("  brew install ffmpeg")
        return 1

    print(f"\n开始下载 {len(todo)} 个：")
    failed = []
    for v in todo:
        print(f"\n[{v['id']}] {v['title']}")
        ok, err = download(v)
        if not ok:
            failed.append((v["id"], err))
            print(f"  ✗ {err}")
            continue
        st, size = status(v)
        print(f"  ✓ {st}，{size:.0f}MB")
        if st != "就位":
            print("    （时长对不上通常说明源视频被重传或剪过，题里的锚点可能对不上画面）")

    print(f"\n完成：成功 {len(todo) - len(failed)}，失败 {len(failed)}")
    for cid, err in failed:
        print(f"  {cid}: {err}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
