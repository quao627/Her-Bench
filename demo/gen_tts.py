#!/usr/bin/env python3
"""为 container 里的 query 型任务生成提问语音（「合成语音」评测条件用）。

「合成语音」档要的是干净、可控、时间对齐的音频输入：主播原声对模型静音，
只在锚点播放这段合成提问，模型靠语音活动检测听完自己作答。所以这里合成的是
**观众提问的那句话**，不是回答。

用法:
    python3 gen_tts.py                          # 补齐所有缺失的
    python3 gen_tts.py blender-e02              # 只做某个 container
    python3 gen_tts.py --force blender-e02      # 覆盖已存在的

已存在的文件默认跳过（这东西要花钱，别重复生成）。
"""
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CONTAINERS = os.path.join(HERE, "data", "containers")
TTS_DIR = os.path.join(HERE, "data", "tts")
MODEL = "gpt-4o-mini-tts"
VOICE = "nova"          # 观众提问的声音，跟陪玩 agent 的 cedar 区分开
FFMPEG = "/Users/bytedance/bin/ffmpeg"

# 提问是「观众随口问出来的一句话」，不是播报稿——念得太字正腔圆反而不像真人发问
INSTRUCTIONS = (
    "用轻松随意的日常语气说这句话，像看直播时随口问身边朋友一样，"
    "带一点好奇和困惑，不要念稿子的腔调，语速自然偏快一点。"
)


def load_key():
    env = os.path.join(HERE, ".env")
    if os.path.exists(env):
        for line in open(env):
            line = line.strip()
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("OPENAI_API_KEY", "")


def synth(text, key):
    """gpt-4o-mini-tts 不直接吐 m4a，用 mp3 再转成跟现有文件一致的 aac/24k/mono。"""
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=json.dumps({
            "model": MODEL, "voice": VOICE, "input": text,
            "instructions": INSTRUCTIONS, "response_format": "mp3",
        }).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        mp3 = r.read()
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(mp3)
        mp3_path = f.name
    m4a_path = mp3_path.replace(".mp3", ".m4a")
    subprocess.run(
        [FFMPEG, "-y", "-i", mp3_path, "-c:a", "aac", "-b:a", "86k",
         "-ar", "24000", "-ac", "1", m4a_path, "-loglevel", "error"],
        check=True,
    )
    data = open(m4a_path, "rb").read()
    os.unlink(mp3_path)
    os.unlink(m4a_path)
    return data


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    force = "--force" in sys.argv
    key = load_key()
    if not key:
        sys.exit("no OPENAI_API_KEY (demo/.env 或环境变量)")

    os.makedirs(TTS_DIR, exist_ok=True)
    names = args or [
        f[:-5] for f in sorted(os.listdir(CONTAINERS))
        if f.endswith(".json") and f != "index.json"
    ]

    made = skipped = 0
    for cid in names:
        path = os.path.join(CONTAINERS, cid + ".json")
        manifest = json.load(open(path))
        changed = False
        for task in manifest["tasks"]:
            if task.get("type") != "query" or not task.get("question"):
                continue
            rel = f"/data/tts/{task['task_id']}.m4a"
            dest = os.path.join(TTS_DIR, task["task_id"] + ".m4a")
            if os.path.exists(dest) and not force:
                if task.get("tts") != rel:
                    task["tts"] = rel
                    changed = True
                skipped += 1
                continue
            print(f"  synth {task['task_id']}: {task['question'][:34]}…", flush=True)
            open(dest, "wb").write(synth(task["question"], key))
            task["tts"] = rel
            changed = True
            made += 1
        if changed:
            with open(path, "w") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"{cid}: manifest updated")
    print(f"\ndone. generated {made}, skipped {skipped} (already existed)")


if __name__ == "__main__":
    main()
