# Her-Bench Live：真实环境陪玩

把 `demo/` 那套预录视频的陪看 harness，换成一个真的在实时跑的游戏——
一个刻意"弱"的 agent 在玩 Pokemon Red，companion（gpt-live + codex，复用
`demo/agent_live.py` 那套）在旁边看、能被问问题、能主动帮忙。

## 现状

- `pokemon-agent/`：clone 自 [NousResearch/pokemon-agent](https://github.com/NousResearch/pokemon-agent)，
  headless PyBoy + FastAPI，`/state` `/screenshot` `/action` 等 REST 接口。
  `.venv`（Python 3.12，通过 [uv](https://github.com/astral-sh/uv) 装的，
  没碰系统 Python 3.9.6，也没装 Homebrew）已经装好 `pyboy` + `dashboard` extra。
- `weak_driver.py`：自己写的玩家 driver（跟 `pokemon-agent/` 平级，不在
  clone 里面），**不用**库自带的
  hermes-CLI autopilot。每轮：截图 + RAM 状态 → 喂给 `gpt-5-mini`（纯
  vision+text，没传 `tools`，真联不了网）→ 选 1-3 个动作 → POST `/action`。
- 卡了什么：**还差一个 ROM**——Pokemon Red/Blue/Yellow 的 `.gb`/`.gbc`，
  得是你自己合法转储的那份，这个库不会也不能帮你搞到。FireRed/Emerald
  那条线（PyGBA）README 上写了但实际代码里还没实现，先别指望。

## 跑起来

```bash
cd live
source pokemon-agent/.venv/bin/activate

# 终端 A：起 emulator server
python3 -m pokemon_agent.cli serve --rom /path/to/pokemon_red.gb
# → http://localhost:8765/dashboard 能看实时画面 + agent 的碎碎念

# 终端 B：起弱 agent driver（注意：driver 在 live/ 下，不在 pokemon-agent/ 里面——
# 那是个第三方 clone，自己带了一份 .git，混在一起会让外层仓库的 git 状态很乱）
export OPENAI_API_KEY=sk-...
python3 weak_driver.py --server http://localhost:8765
```

## weak_driver.py 里处理过的几个坑

读了 pokemon-agent 的源码（不只是 README）加上查了 Claude Plays Pokemon 的
复盘之后，这几件事是特意这么做的：

- **卡死检测是机械的，不让模型自判**——按 RAM 里真实的 `(map_id, x, y)`
  坐标滑窗判断，不是让模型自己说"我是不是卡住了"。Claude Plays Pokemon
  真实复盘过一次事故：模型自己编出"死一次能被传送出去"的错误信念，然后
  连续昏厥了 8 次——自我叙述这种东西是会跑偏的，不能当卡死判据。
- 卡够久（连续几个判定周期都没挪窝）**直接绕过 LLM**，机械地往一个方向
  硬走几步破局——这种"物理破局"不需要智能，问模型也问不出新招。
- `/screenshot/grid` 实际上**不画**可走性红绿底色（读源码确认过，是这个
  库的一个 bug，`walkable` 参数在这条路由里根本没传进去）——真正能用的
  可走性数据来自 `state["collision"]["ascii"]`，driver 里用的是这个，
  不是指望模型自己从像素里看出哪能走。
- 库自带的 `a_until_dialog_end` 也有 bug（判断用的 key 名不对，永远只
  循环一次）——对话框翻页改成 driver 自己机械按 A，不占 LLM 的一轮。
- 战斗是单独的 system prompt（FIGHT/BAG/POKEMON/RUN 菜单 vs 探索走路），
  不跟 overworld 的提示混在一起问。
- 目标范围按 pcc-labs 的基准分档设的：走出 Pallet Town、抓到最初几只
  Pokémon、往第一个道馆走，量级大概 200 轮——不是让它打通关，Anthropic
  自己那次全流程跑了 140 小时、3.5 万个动作，明显不是本地 demo 该有的规模。

## 下一步：接进现有的 companion harness

`demo/agent_live.py` 已经有 `/answer` `/lookup` `/research` 三条路径和
gpt-live 的 WebRTC 前端，这套不用重搭。要接的话大概是：

1. 画面源从"每 5 秒读一帧预录视频"换成"每 5 秒打 pokemon-agent 的
   `/screenshot`"（或者直接订阅它的 `/ws` WebSocket 事件流）。
2. `agent_live.py` 里 `get_resource_docs()` 的"资料"这块，对活的游戏来说
   可以换成实时的 `/state`——badge、party、当前地图，这些不用查资料，
   直接是 ground truth，比预录视频时代准。
3. task/rubric 那套 anchor_sec 的设计不完全适用了（没有固定时间轴），
   但"milestone 触发一个 task"是个自然的替代——weak_driver 已经在检测
   拿到徽章/抓到宝可梦这类里程碑并 POST `/event`，可以在这个事件上挂
   proactive 型的判分逻辑，而不是靠预先标好的时间戳。
