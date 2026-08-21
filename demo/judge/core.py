"""调用与兜底。判分本身是一次无状态的纯文本请求，没有会话、没有重试历史。"""

import json
import os
import time
import urllib.error
import urllib.request

# 判分用的模型跟陪看用的完全无关，单独一个环境变量，方便换了模型重跑一遍对比
JUDGE_MODEL = os.environ.get("HERBENCH_JUDGE_MODEL", "gpt-5.4")
JUDGE_TIMEOUT = int(os.environ.get("HERBENCH_JUDGE_TIMEOUT", "90"))

from .prompt import SYSTEM, build_prompt


def _schema():
    item = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "hit": {"type": "boolean"},
            "why": {"type": "string", "description": "一句话依据，引用 agent 原话里的关键词"},
        },
        "required": ["hit", "why"],
    }
    spoil = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "violated": {"type": "boolean"},
            "why": {"type": "string"},
        },
        "required": ["violated", "why"],
    }
    return {
        "type": "object", "additionalProperties": False,
        "properties": {
            "rubric": {"type": "array", "items": item,
                       "description": "跟 rubric_points 一一对应，顺序和条数必须一致"},
            "spoiler": {"type": "array", "items": spoil,
                        "description": "跟 spoiler_blocklist 一一对应"},
            "leaked_future": {"type": "boolean",
                              "description": "blocklist 之外，是否说了锚点之后才会发生的事"},
            "leaked_future_why": {"type": "string"},
            "hint_level_ok": {"type": "boolean"},
            "hint_level_why": {"type": "string"},
            "grounding": {"type": "string", "enum": ["ok", "wrong", "na"],
                          "description": "指认画面里的东西对不对；没给画面或没指认就 na"},
            "grounding_why": {"type": "string"},
            "citation": {"type": "string", "enum": ["ok", "missing", "irrelevant", "na"],
                         "description": "must_cite 为假时一律 na"},
            "citation_why": {"type": "string"},
            "spoken_ok": {"type": "boolean",
                          "description": "像说出来的而不是念稿子，同时不是没信息量的空话"},
            "spoken_why": {"type": "string"},
            "silence_ok": {"type": "string", "enum": ["good", "missed", "na"],
                           "description": "proactive 且没开口时用：good=这一刻确实不该说，"
                                          "missed=该说没说；开口了或非 proactive 就 na"},
            "verdict": {"type": "string", "description": "一两句总评，说清扣在哪"},
        },
        "required": ["rubric", "spoiler", "leaked_future", "leaked_future_why",
                     "hint_level_ok", "hint_level_why", "grounding", "grounding_why",
                     "citation", "citation_why", "spoken_ok", "spoken_why",
                     "silence_ok", "verdict"],
    }



def judge_run(task, run, frame_jpeg_base64=None, model=None):
    """跑一次判分。返回 (http_code, dict)。"""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return 503, {"error": "OPENAI_API_KEY 未设置，judge 跑不了"}

    mdl = model or JUDGE_MODEL
    content = [{"type": "text", "text": build_prompt(task, run)}]
    if frame_jpeg_base64:
        content.append({"type": "image_url", "image_url": {
            "url": "data:image/jpeg;base64," + frame_jpeg_base64,
            "detail": "low"}})

    body = json.dumps({
        "model": mdl,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": content}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "herbench_verdict", "strict": True, "schema": _schema()}},
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=JUDGE_TIMEOUT) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        return e.code, {"error": f"judge 调用失败 {e.code}: {detail}"}
    except Exception as e:
        return 502, {"error": f"judge 调用失败: {e}"}

    try:
        verdict = json.loads(data["choices"][0]["message"]["content"])
    except Exception as e:
        return 502, {"error": f"judge 返回的不是预期的 JSON: {e}"}

    # 条数对不上的话前端按 index 渲染会错位，这里补齐/截断，宁可少判也不错位
    for field, ref in (("rubric", (task.get("grading") or {}).get("rubric_points") or []),
                       ("spoiler", (task.get("grading") or {}).get("spoiler_blocklist") or [])):
        got = verdict.get(field) or []
        if len(got) != len(ref):
            filler = {"hit": False, "why": "(判分没返回这一条)"} if field == "rubric" \
                else {"violated": False, "why": "(判分没返回这一条)"}
            verdict[field] = (got + [filler] * len(ref))[:len(ref)]

    usage = data.get("usage") or {}
    verdict["_meta"] = {
        "model": mdl,
        "latency_ms": int((time.time() - t0) * 1000),
        "tokens_in": usage.get("prompt_tokens"),
        "tokens_out": usage.get("completion_tokens"),
        "saw_frame": bool(frame_jpeg_base64),
    }
    return 200, verdict
