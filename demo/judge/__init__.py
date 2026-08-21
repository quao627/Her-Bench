"""独立判分：跟被测的 agent 完全分开的一次 LLM 调用。

判分必须是外部视角。让同一条会话既作答又给自己打分等于自己验自己，而且它手里
还留着刚查到的资料，会顺着自己的话往下认。所以这一层不碰 codex、不碰 Realtime
会话、不共享任何上下文——只拿「题面 + agent 到底说了什么」去问一个纯文本模型，
材料之外的东西一概不许用。

对外只有一个入口：

    from judge import judge_run
    code, verdict = judge_run(task, run, frame_jpeg_base64=None, model=None)

细节见 judge/README.md。
"""

from .core import JUDGE_MODEL, JUDGE_TIMEOUT, judge_run     # noqa: F401

__all__ = ["judge_run", "JUDGE_MODEL", "JUDGE_TIMEOUT"]
