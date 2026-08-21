"""被测的 agent 实现。harness 只认这几个方法，别的都是各自的事。

    start(ctx)                        可选，开跑前叫一次
    on_frame(ctx, sec, frame_b64)     每帧叫一次；返回字符串 = 此刻主动开口
    on_question(ctx, sec, q, task)    主播开口了；返回字符串或 {"text": ..., 附加字段}
    finish(ctx)                       可选

ctx 里有：ctx.now() 视频时间、ctx.frames 画面架子、ctx.bg 后台通道、ctx.title。
后台通道一次只能跑一个活，扔进去的东西要等到 now + 实测耗时 才拿得到——想得慢
就是会错过时机，这条由 harness 强制，agent 绕不过去。
"""

from . import prepared, reactive           # noqa: F401

REGISTRY = {
    "reactive": reactive.Agent,            # 只有前台，被问了才现查
    "prepared": prepared.Agent,            # 前台 + 后台备料
}
