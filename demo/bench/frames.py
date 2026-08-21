"""视频帧的架子：整段一次抽完，之后按视频时间取。

agent 是一路看过来的，走到某一刻手上有从开头到现在的全部画面。这里把帧存下来，
world.py 按视频时间发给它，回看多深是 agent 自己的事。
"""

import base64
import os
import shutil
import subprocess
import tempfile
import time


def _ffmpeg():
    exe = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


class Frames:
    """整段视频一次抽完，之后按视频时间取。

    真实场景里 agent 是一路看过来的，走到某一刻手上有从开头到现在的全部画面。
    这里把这些帧存在架子上，agent 想回看多深是它自己的事。
    """

    def __init__(self, video, step=5, limit=0, width=384):
        self.step = step
        self.dir = tempfile.mkdtemp(prefix="herbench_frames_")
        cmd = [_ffmpeg(), "-nostdin", "-loglevel", "error"]
        if limit:
            cmd += ["-t", str(limit + step)]
        cmd += ["-i", video, "-vf", f"fps=1/{step},scale={width}:-2", "-q:v", "6",
                os.path.join(self.dir, "%06d.jpg")]
        t0 = time.time()
        subprocess.run(cmd, check=True)
        self.files = sorted(os.path.join(self.dir, f) for f in os.listdir(self.dir))
        self.extract_sec = time.time() - t0
        self._video = video

    def __len__(self):
        return len(self.files)

    def at(self, sec):
        i = int(round(sec / self.step))
        if i < 0 or i >= len(self.files):
            return None
        try:
            return base64.b64encode(open(self.files[i], "rb").read()).decode()
        except Exception:
            return None

    def since_start(self, now, offsets):
        """按给定偏移往回取，越界的丢掉，去重后按时间排好。"""
        out, seen = [], set()
        for off in offsets:
            s = now + off
            if s < 0:
                continue
            k = int(round(s / self.step))
            if k in seen:
                continue
            b = self.at(s)
            if b:
                seen.add(k)
                out.append((int(k * self.step), b))
        return sorted(out)

    def hi_res(self, sec, width=640):
        """要一张清楚的：单独截，不走架子。"""
        out = tempfile.mktemp(suffix=".jpg")
        subprocess.run([_ffmpeg(), "-nostdin", "-loglevel", "error", "-ss", str(max(0, sec)),
                        "-i", self._video, "-frames:v", "1", "-vf", f"scale={width}:-2",
                        "-q:v", "5", "-y", out], check=False)
        if not os.path.exists(out) or os.path.getsize(out) < 500:
            return None
        b = base64.b64encode(open(out, "rb").read()).decode()
        os.unlink(out)
        return b

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)
