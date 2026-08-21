"""判分员看到的东西：他是谁、给他什么材料、要他逐条判什么。

这一层单独拆出来是因为它最常改：判分标准一动，历史分数就不可比了，
所以改这里要有意识——最好换个 HERBENCH_JUDGE_MODEL 或者留个版本记号，
别让新旧结果混在一起。
"""

SYSTEM = """你是 Her-Bench 的判分员。

场景：有人在直播里第一次玩某个游戏、或者第一次上手某个软件，旁边有一个 AI 陪看
agent。你要判断这个 agent 这一次说的话好不好。

最重要的一条：**只根据下面给你的材料判**。你可能自己就知道这个游戏怎么通关，
但那不作数——判断依据只能是题面写的 rubric、防剧透清单和 agent 实际说出口的话。
材料里没写的，就当你不知道。

判的时候把「说得对不对」和「该不该这么说」分开：一段话可以事实全对但因为剧透
或者越级给解法而不合格，反过来也一样。"""




def _fmt(sec):
    sec = int(sec or 0)
    return f"{sec // 60}:{sec % 60:02d}"


def build_prompt(task, run):
    g = task.get("grading") or {}
    rubric = g.get("rubric_points") or []
    block = g.get("spoiler_blocklist") or []
    must_cite = bool(g.get("must_cite"))
    is_q = task.get("type") == "query"
    answer = (run.get("answer") or "").strip()
    cites = run.get("citations") or []

    L = []
    L.append("【题面】")
    L.append(f"类型：{'query（主播开口问了）' if is_q else 'proactive（没人问，agent 自己决定要不要开口）'}")
    L.append(f"锚点：视频 {_fmt(task.get('anchor_sec'))}。agent 只看得到锚点之前的内容，"
             f"锚点之后的一律算它不该知道。")
    hint = task.get("hint_level") or "direction_only"
    L.append(f"提示分级 {hint}："
             + ("只能给方向，指出该往哪想、该留意什么，不能给出照着做就能过的完整步骤。"
                if hint == "direction_only" else
                "可以把原理、步骤、容易搞错的地方讲透，讲清楚比含糊带过好。"))
    if task.get("scene"):
        L.append(f"锚点那一帧画面上有什么：{task['scene']}")
    if is_q and task.get("question"):
        L.append(f"主播问的：「{task['question']}」")
    if not is_q and task.get("response_window_sec"):
        w = task["response_window_sec"]
        L.append(f"标注的响应窗口：{_fmt(w[0])} – {_fmt(w[1])}")

    L.append("")
    L.append("【rubric 要点】（逐条判，顺序和条数原样返回）")
    if rubric:
        L.extend(f"{i + 1}. {p}" for i, p in enumerate(rubric))
    else:
        L.append("（这道题没写要点，rubric 返回空数组）")

    L.append("")
    L.append("【防剧透清单】（提到即违规，逐条判）")
    if block:
        L.extend(f"{i + 1}. {p}" for i, p in enumerate(block))
    else:
        L.append("（没有点名的条目，spoiler 返回空数组；但仍要判 leaked_future）")

    L.append("")
    L.append(f"【must_cite】{'是，这题必须给出来源' if must_cite else '否，citation 一律返回 na'}")

    L.append("")
    L.append("【agent 这一次说的】")
    if answer:
        L.append(answer)
    else:
        L.append("（它选择了不开口，一个字都没说）")
    if cites:
        L.append("")
        L.append("它给的来源：" + " / ".join(str(c) for c in cites))

    if run.get("spoke_at_sec") is not None:
        L.append("")
        L.append(f"它开口的时刻：视频 {_fmt(run['spoke_at_sec'])}")

    L.append("")
    L.append("""【怎么判】
1. rubric 逐条独立判：这段话里有没有说到这一条的意思。看意思不看字面，同义换句算命中；
   说到了但说错了不算命中；只是把问题重复一遍、或者含糊到听完还是不知道怎么办，不算命中。
2. spoiler 逐条判清单里的内容有没有被提到。清单之外，如果它说了锚点之后才会发生的事
   （后面的关卡、后面的剧情、还没出现的机制），leaked_future 记 true。
3. hint_level：direction_only 的题给出了照着做就能过关的完整步骤，就是越级，hint_level_ok=false。
   full 的题该讲透没讲透，也记 false。
4. grounding：它指认画面里的东西时说对了没有。给了截图就对着截图判，没给或者它压根没指认，返回 na。
5. citation：must_cite 为真时才判。给了来源且跟答案对得上 = ok；没给 = missing；
   给了但跟这段话没关系 = irrelevant。
6. spoken_ok：这段话是要念出来给主播听的。出现「首先/其次/另外/需要注意的是/建议你/可以尝试」
   这类书面词、念条目、长句套长句，记 false。反过来，口语但通篇没信息量（只有「加油」
   「慢慢来」这种），也记 false。
7. proactive 且它没开口时判 silence_ok：这一刻按题面看确实没什么值得说的，记 good；
   题面标了响应窗口说明这是该出声的时刻，它却沉默，记 missed。开口了或者是 query 题，返回 na。

why 字段都要短，一句话，尽量引 agent 的原话或者题面的原话，不要空泛地夸或者骂。""")
    return "\n".join(L)


