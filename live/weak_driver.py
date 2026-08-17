#!/usr/bin/env python3
"""不联网的弱 harness：gpt-5-mini 当玩家，只看画面 + RAM 状态，没有任何工具/联网能力。

用法：
    python3 weak_driver.py --server http://localhost:8765

跟 pokemon-agent 自带的 `play`（hermes CLI + 完整 agent stack）不是一回事——
这里就是纯 vision+text 的单轮请求，没有 function calling，没有搜索，
产出的错误应该是"人味的"（看错菜单、走错路、忘了刚拿到的道具），
而不是 RL agent 那种机械的最优化失败。

设计上参考了几个已知教训（研究 NousResearch/pokemon-agent 源码 + Claude Plays
Pokemon 相关复盘之后定的）：
  - 卡死检测必须是机械的（按 RAM 里的 map_id/x/y 判断），不能让模型自己判断
    "我是不是卡住了"——Claude Plays Pokemon 复盘里就出过模型自己编了个错误
    信念（"死一次能被传送出去"）然后连续昏厥 8 次的真实事故。
  - /screenshot/grid 实际上不画可走性红绿底色（读源码验证过，是这个库的一个
    bug）——真正能用的可走性数据是 state["collision"]["ascii"]，不是画面本身。
  - 库自带的 a_until_dialog_end 有 bug（判断的 key 名不对，永远只循环一次），
    对话框翻页这里改成自己在 driver 里机械地按 A，不占 LLM 的一轮。
  - battle 是完全不同的决策模式（FIGHT/BAG/POKEMON/RUN 菜单），用单独的
    system prompt，不跟 overworld 探索混在一起问。
  - 目标范围按 pcc-labs 的基准分档设的："走出 Pallet Town、抓到最初几只
    Pokémon、往第一个道馆走"大概 200 轮量级——不是要它打完全程。
"""
import argparse
import base64
import collections
import json
import os
import time
import traceback
from datetime import datetime, timezone

import requests
from openai import OpenAI

ACTIONS = [
    "press_a", "press_b", "press_start", "press_select",
    "walk_up", "walk_down", "walk_left", "walk_right",
    "hold_a_30", "wait_60",
]

DEFAULT_GOAL = "走出 Pallet Town，抓到最初的几只 Pokémon，往第一个道馆的方向走"

OVERWORLD_SYSTEM = f"""你在玩 Pokemon Red。你是个新手，没打过这游戏，只能看当前画面和游戏状态判断，
不能查攻略、不能上网、不知道地图全貌、不知道后面剧情。

当前目标（大方向，别死磕）：{{goal}}

每一轮我给你：
- 一张当前画面截图（带 A1..J9 方格坐标，你所在格子在图上有红框标出）
- 一份 RAM 读出来的真实可走性地图（ascii，'.' 能走 '#' 不能走，比看画面猜准）
- 最近几轮你自己的想法和动作，帮你记得刚试过什么，别重复白试
- 如果卡住了，会有一条机械检测出来的提醒（不是我猜的，是位置真的没变）

你选 1-3 个动作执行，动作只能是这些之一：{", ".join(ACTIONS)}

有个常见坑先提醒你：起名字的画面（给自己/给对手 Rival 取名）是个字母格子，
方向键只是移动光标选字母，不是走路——选完想要的字母/名字后，
必须把光标移到字母表右下角的 "END" 上再按 A 才算确认，不是选完字母就结束了。
如果你发现自己好像在一个字母网格里、按了好几次方向和 A 但画面一直没变，
大概率就是还没把光标移到 END。

像真人新手一样玩：不确定往哪走就先探索，卡住了就换个方向试试，
不用装作全知全能。用一两句话说说你现在在想什么（会显示在观察者的 dashboard 上，
让人知道你在纠结什么、发现了什么）。

只输出 JSON，不要多余文字。"""

BATTLE_SYSTEM = f"""你在玩 Pokemon Red，现在处于战斗中。你是新手，没有攻略可查，
只能凭自己对属性/招式名字的直觉判断。

战斗菜单用方向键 + A/B 操作：主菜单是 FIGHT/BAG/POKEMON/RUN 四个选项，
方向键切光标，A 确认，B 返回上一层。选 FIGHT 后是招式列表，同样方向键选、A 确认。

每一轮我给你当前画面截图 + 敌方信息 + 我方队伍血量。
你选 1-3 个动作执行，动作只能是这些之一：{", ".join(ACTIONS)}

新手打法就行：血量低就想想要不要换人/用道具，不确定招式属性克制就凭感觉选，
别装作背熟了克制表。一两句话说说你在想什么。

只输出 JSON，不要多余文字。"""

RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "pokemon_turn",
        "schema": {
            "type": "object",
            "properties": {
                "thought": {"type": "string", "description": "一两句话，你现在在想什么/打算干嘛"},
                "actions": {
                    "type": "array",
                    "items": {"type": "string", "enum": ACTIONS},
                    "minItems": 1,
                    "maxItems": 3,
                },
            },
            "required": ["thought", "actions"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

# 卡死检测：最近 N 轮里出现的不同 (map_id,x,y) 格子数 <= 2 就判定卡住
STUCK_WINDOW = 12
STUCK_UNIQUE_THRESHOLD = 2
# 卡住之后，连续这么多"轮"（不是 LLM 调用次数，是判定周期）还没恢复，
# 就绕过 LLM 直接机械地往一个固定方向硬走几步，强制打破循环
HARD_UNSTUCK_AFTER = 2
DIALOG_CLEAR_MAX_PRESSES = 8


def api_get(server, path, **kw):
    r = requests.get(f"{server}{path}", timeout=15, **kw)
    r.raise_for_status()
    return r


def api_post(server, path, body):
    r = requests.post(f"{server}{path}", json=body, timeout=20)
    r.raise_for_status()
    return r.json()


def get_state(server):
    return api_get(server, "/state").json()


def b64_screenshot_grid(server):
    return base64.b64encode(api_get(server, "/screenshot/grid").content).decode()


def push_event(server, kind, **fields):
    try:
        requests.post(f"{server}/event", json={"type": kind, **fields}, timeout=5)
    except Exception:
        pass  # dashboard 不是关键路径，挂了不该拖垮玩游戏


def position_of(state):
    p = (state.get("player") or {}).get("position") or {}
    map_id = (state.get("map") or {}).get("map_id")
    return (map_id, p.get("x"), p.get("y"))


def is_in_battle(state):
    battle = state.get("battle") or {}
    return bool(battle.get("in_battle"))  # battle 本身永远是个非空 dict，不能用 bool(battle) 判断


def is_dialog_active(state):
    dialog = state.get("dialog") or {}
    return bool(dialog.get("active"))


def is_name_entry_pending(state):
    """踩过的真实事故：mash_a 盲按 A 在正常对话框里是"翻页"，但在起名字的字母格
    画面里 A 在左上角，盲按 A 会变成"选中字母 A 打进名字里"——实测把玩家名字
    刷成了 "AAAAAAE" 这种乱码。名字还是占位符（一串 "?"）说明这段还没走完，
    这时候所有机械 mash/unstuck 都不该碰 press_a，只能让 LLM 自己判断
    （已经在 prompt 里提醒过它"记得把光标移到 END"）。"""
    p = state.get("player") or {}
    name, rival = p.get("name") or "", p.get("rival_name") or ""
    return bool((name and set(name) <= {"?"}) or (rival and set(rival) <= {"?"}))


def mash_a(server, state, max_presses=DIALOG_CLEAR_MAX_PRESSES, stop_when=None):
    """机械地翻对话，不占 LLM 的一轮。

    这里的时序坑比想象中多，测出来至少三种不同的"卡文字"行为，而且同一句台词
    在不同局里表现还不一致（可能是模拟器对连续外部注入按键的处理跟真实手柄
    时序有细微差异）：
      1. 正常对话框——按 A 翻页，但背靠背狂按（不夹 wait）会跟游戏自己的文字
         打印状态机撞车，按的时机正好落在"这行字还在一个字一个字打印"的动画
         窗口里，直接被吃掉；夹一个 wait_60 再按，规律地按，能推过去。
      2. Mom 那句"All boys leave home someday"——手动测试里 press_a（8 帧
         按压）反复卡在同一行不动，换成 hold_a_30（按住 30 帧）才推得动。
         怀疑是这类台词对"按下"事件的判定窗口比普通对话框窄，短按容易被
         夹在两帧动画之间漏判，长按能确保跨过那个窗口。
    没法完美建模每种到底要哪种按法，所以这里用 hold_a_30（长按）作为主力——
    比短按 press_a 更不容易被吃、目前没发现有副作用，只是耗的游戏帧数更多，
    但反正现在是不限速模拟，帧数不等于真实时间。"""
    presses = 0
    while (stop_when is None or not stop_when(state)) and presses < max_presses:
        actions = ["wait_60", "wait_60", "hold_a_30"] if presses % 2 == 0 else ["wait_60", "hold_a_30"]
        state = api_post(server, "/action", {"actions": actions})["state_after"]
        presses += 1
    return state, presses


def clear_dialog(server, state):
    """库自带的 a_until_dialog_end 有 bug（判断 key 名不对，永远只循环一次），
    这里自己机械地按 A 翻页，不占 LLM 的一轮、也不用等模型判断"这是不是对话"。"""
    return mash_a(server, state, stop_when=lambda s: not is_dialog_active(s))


def summarize_state(state, goal):
    p = state.get("player") or {}
    party = state.get("party") or []
    battle = state.get("battle") or {}
    collision = state.get("collision")
    out = {
        "goal": goal,
        "position": p.get("position"),
        "facing": p.get("facing"),
        "map_name": (state.get("map") or {}).get("map_name"),
        "badges": p.get("badges"),
        "party": [{"species": m.get("species"), "level": m.get("level"),
                    "hp": m.get("hp"), "max_hp": m.get("max_hp")} for m in party],
    }
    if collision and collision.get("ascii"):
        out["walkable_map_ascii"] = collision["ascii"]  # RAM 读出来的真值，比截图猜靠谱
    if is_in_battle(state):
        enemy = battle.get("enemy") or {}
        out["enemy"] = {"species": enemy.get("species"), "level": enemy.get("level"),
                          "hp": enemy.get("hp"), "max_hp": enemy.get("max_hp"),
                          "status": enemy.get("status"), "moves": enemy.get("moves")}
    return out


class StuckTracker:
    """卡死检测是机械的（按真实坐标判断），不能让模型自己判断"我是不是卡住了"——
    这类判断很容易被模型自己的叙述带偏（比如编出个"死一次就能传送走"的错误理论
    然后自我强化）。"""

    def __init__(self):
        self.positions = collections.deque(maxlen=STUCK_WINDOW)
        self.stuck_streak = 0  # 连续判定为"卡住"的周期数
        self.hard_unstuck_count = 0  # 连续触发硬破局的次数，用来轮换破局策略

    def update(self, pos):
        self.positions.append(pos)
        if len(self.positions) < STUCK_WINDOW:
            # 窗口还没填满（硬破局后 positions 会被清空，这里也会触发）——
            # 注意 hard_unstuck_count 这里不重置：窗口填满前还不知道刚才那次
            # 破局策略到底有没有用，得等填满了、真判断出"没卡了"才能清零
            self.stuck_streak = 0
            return False
        unique = len(set(self.positions))
        stuck_now = unique <= STUCK_UNIQUE_THRESHOLD
        self.stuck_streak = self.stuck_streak + 1 if stuck_now else 0
        if not stuck_now:
            self.hard_unstuck_count = 0  # 真的挪窝了，破局策略轮换重新从头算
        return stuck_now

    def needs_hard_unstuck(self):
        return self.stuck_streak >= HARD_UNSTUCK_AFTER


def build_prompt_messages(state, goal, history, stuck):
    in_battle = is_in_battle(state)
    system = (BATTLE_SYSTEM if in_battle else OVERWORLD_SYSTEM).format(goal=goal)
    summary = summarize_state(state, goal)

    parts = [f"当前状态：\n{json.dumps(summary, ensure_ascii=False, indent=None)}"]
    if history:
        hist_lines = "\n".join(f"- 想法：{h['thought']} → 动作：{h['actions']}" for h in history)
        parts.append(f"\n你最近几轮做过什么（别重复白试一样的东西）：\n{hist_lines}")
    if stuck:
        parts.append(
            f"\n⚠️ 机械检测：你最近 {STUCK_WINDOW} 轮几乎一直在同一个/两个格子里，"
            "没有实质进展。别再重复同一个方向了，换个完全不同的动作或方向试试。"
        )
    return system, "\n".join(parts)


def one_llm_turn(client, model, server, goal, history, stuck):
    state = get_state(server)

    # 对话框翻页是机械操作，不该占 LLM 的一轮，也不该让模型来判断"这是不是对话"
    if is_dialog_active(state):
        state, n = clear_dialog(server, state)
        if n:
            print(f"[dialog] auto-pressed A x{n}")
        if is_dialog_active(state):
            # 翻页翻满了还没结束，可能是需要选择的菜单式对话，交回给 LLM 判断
            pass
        else:
            return state, None  # 对话清完了，这一轮不用问模型，直接进下一个循环

    img_b64 = b64_screenshot_grid(server)
    system, user_text = build_prompt_messages(state, goal, history, stuck)

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            ]},
        ],
        response_format=RESPONSE_SCHEMA,
        # 故意不传 tools —— 这是个不联网的弱 harness，只能看画面/状态判断
    )
    out = json.loads(resp.choices[0].message.content)
    thought, actions = out.get("thought", ""), out.get("actions", [])
    print(f"[think] {thought}")
    print(f"[act]   {actions}")
    push_event(server, "reasoning", text=thought)

    action_resp = api_post(server, "/action", {"actions": actions})
    return action_resp["state_after"], out


# 硬破局的动作库——注意方向键在"起名字"这类菜单里只是移动光标，不会改变
# 玩家的 RAM 坐标，所以纯方向键破局对菜单卡死没用。按触发次数轮换策略，
# 不要每次都只试方向键。
#
# 踩过的坑：这里最早还放过 press_b（"取消/返回上一层"），实测在 Mom 那段长
# 对话上按 B 会让台词倒退回更早的一行——B 在对话框语境里更像是"跳过/中断"
# 而不是"继续"，跟方向键硬走一样对文字卡死没用，但方向键最多是无效，
# press_b 是真的会把已经推进的进度吃掉，所以从这个轮换列表里拿掉了，不留着。
UNSTUCK_STRATEGIES = [
    ["walk_up", "walk_down", "walk_left", "walk_right"],  # 方向键刷一圈，overworld 卡墙角最常见
    ["press_start"] * 4,       # 很多菜单/命名画面的"确认"或"跳出"
    ["hold_a_30"] * 4,         # 万一其实还在对话里，长按 A 是目前唯一稳定见效的
    ["wait_60"] * 6,           # 纯等——某种对话类型反而是"按了当卡住"，纯等才推得完
]


def hard_unstuck(server, tracker):
    """卡够久了，别再问模型了——直接绕过 LLM，机械地硬闯几步。
    便宜、快，而且这类"物理破局"本来就不需要智能，模型反复给同类建议也没用。
    按连续触发次数轮换策略——纯方向键在起名字这类菜单里是无效的（光标移动不算
    玩家坐标变化），所以不能死磕一种破局方式。"""
    strategy = UNSTUCK_STRATEGIES[tracker.hard_unstuck_count % len(UNSTUCK_STRATEGIES)]
    print(f"[unstuck] stuck_streak={tracker.stuck_streak}, attempt #{tracker.hard_unstuck_count}, "
          f"trying {strategy} without asking the model")
    push_event(server, "alert", text=f"卡住太久了，强制试一遍 {strategy} 破局（第 {tracker.hard_unstuck_count+1} 次尝试）")
    state = None
    for a in strategy:
        resp = api_post(server, "/action", {"actions": [a]})
        state = resp["state_after"]
    tracker.stuck_streak = 0
    tracker.hard_unstuck_count += 1
    tracker.positions.clear()
    return state


# 纯"翻文字"类动作——如果模型连续几轮只选这些、且下面 fingerprint() 定义的
# 关键状态完全没变，大概率是撞上了某种脚本化文字序列，而 RAM 里 dialog.active
# 这个字段不是每种文字序列都会置位（实测踩过至少两种：正常对话框、以及改名字
# 之后那段"参观对方房间"的固定台词——两种画面上明明有文字框，RAM 读出来的
# dialog.active 却一直是 False）。这种时候别再花钱问模型了，直接机械地
# mash_a 一轮，比等模型自己反复念叨"再按 A 试试"划算。
TEXT_ADVANCE_ACTIONS = {"press_a", "press_b", "press_start", "wait_60", "hold_a_30"}
TEXT_STALL_AFTER = 2


def has_text_advance_action(actions):
    """用"至少含一个"而不是"全部都是"——实测踩过的真实案例里，卡住的那几轮
    模型经常是 press_a 和 walk_down 混着选（先翻页再想顺手走一步），如果
    要求"这轮全部动作都是翻页类"才算数，会漏掉这种混合轮次，导致文字卡死
    检测迟迟不触发，一路掉到更重的、对文字卡死没用的坐标破局逻辑上去。"""
    return bool(actions) and any(a in TEXT_ADVANCE_ACTIONS for a in actions)


def fingerprint(state):
    """比 position_of() 更宽的"有没有实质进展"判据——除了坐标，也看队伍/徽章，
    这样战斗里合理的、位置不变的操作不会被这个判据冤枉（战斗有自己的处理，
    这个判据只用来配合 TEXT_ADVANCE_ACTIONS 抓"卡在文字上"这一类）。"""
    p = (state.get("player") or {}).get("position") or {}
    return (
        (state.get("map") or {}).get("map_id"), p.get("x"), p.get("y"),
        len(state.get("party") or []),
        len((state.get("player") or {}).get("badges") or []),
    )


def check_milestones(server, prev_state, state):
    if prev_state is None:
        return
    prev_badges = len((prev_state.get("player") or {}).get("badges") or [])
    badges = len((state.get("player") or {}).get("badges") or [])
    if badges > prev_badges:
        push_event(server, "key_moment", description="拿到了新徽章！", category="badge")

    prev_n = len(prev_state.get("party") or [])
    n = len(state.get("party") or [])
    if n > prev_n:
        newest = (state.get("party") or [])[-1]
        push_event(server, "key_moment",
                   description=f"抓到/收到了新宝可梦：{newest.get('species')}", category="catch")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://localhost:8765")
    ap.add_argument("--model", default="gpt-5-mini")
    ap.add_argument("--goal", default=DEFAULT_GOAL)
    ap.add_argument("--interval", type=float, default=1.5, help="每轮之间等几秒（模拟真人节奏，也控成本）")
    ap.add_argument("--turns", type=int, default=0, help="0 = 一直跑")
    ap.add_argument("--history", type=int, default=8, help="喂给模型的最近几轮想法/动作记忆窗口")
    ap.add_argument("--log", default="", help="把每轮记录写成 jsonl，留空则不写")
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("没有 OPENAI_API_KEY，先 export 一下")
    client = OpenAI(api_key=api_key)

    log_f = open(args.log, "a") if args.log else None
    history = collections.deque(maxlen=args.history)
    tracker = StuckTracker()
    prev_state = None
    last_fingerprint = None
    text_stall_streak = 0

    print(f"weak_driver: model={args.model} server={args.server} interval={args.interval}s goal={args.goal!r}")
    n = 0
    while True:
        try:
            stuck = tracker.stuck_streak > 0  # 用上一轮算出来的卡死状态提示这一轮
            name_pending = is_name_entry_pending(prev_state or {})
            # text-stall 检查放在 hard_unstuck 前面：mash_a 便宜且对着"真是文字
            # 卡死"以外的情况基本无害（顶多白按几下 A），但 hard_unstuck 的方向键
            # 硬走对文字卡死完全没用——按走投无路的顺序试，不要反过来。
            # 起名字画面例外：那两条机械 fallback 都可能按到 press_a，在正常对话框
            # 里是翻页，在起名字的字母格里却是"选中字母打进名字"——这时候宁可让
            # LLM 自己（已经在 prompt 里提醒过要找 END）慢慢试，也不要机械乱按。
            if name_pending:
                state, out = one_llm_turn(client, args.model, args.server, args.goal, history, stuck)
            elif text_stall_streak >= TEXT_STALL_AFTER and not is_in_battle(prev_state or {}):
                state, n_presses = mash_a(args.server, get_state(args.server), max_presses=30)
                print(f"[text-stall] fingerprint frozen for {text_stall_streak} turns with a text-advance "
                      f"action mixed in — force mash_a x{n_presses} (RAM dialog flag likely stale here)")
                text_stall_streak = 0
                out = None
            elif tracker.needs_hard_unstuck():
                state = hard_unstuck(args.server, tracker)
                out = None
            else:
                state, out = one_llm_turn(client, args.model, args.server, args.goal, history, stuck)

            pos = position_of(state)
            tracker.update(pos)
            check_milestones(args.server, prev_state, state)

            fp = fingerprint(state)
            if out is not None and has_text_advance_action(out.get("actions")) and fp == last_fingerprint \
                    and not is_in_battle(state):
                text_stall_streak += 1
            else:
                text_stall_streak = 0
            last_fingerprint = fp

            if out is not None:
                history.append(out)
            if log_f:
                log_f.write(json.dumps({
                    "t": datetime.now(timezone.utc).isoformat(),
                    "position": pos, "stuck": stuck, "turn": out,
                }, ensure_ascii=False) + "\n")
                log_f.flush()

            prev_state = state
        except requests.exceptions.RequestException as e:
            print(f"[error] server unreachable: {e}")
            time.sleep(5)
            continue
        except Exception as e:
            print(f"[error] {e}")
            traceback.print_exc()
            time.sleep(3)
            continue

        n += 1
        if args.turns and n >= args.turns:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
