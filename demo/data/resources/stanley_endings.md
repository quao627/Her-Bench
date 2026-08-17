# The Stanley Parable 全结局与分支路线（完整题底 · 一）：分支总图与左门线

> 来源：https://thestanleyparable.fandom.com/wiki/Endings 、https://thestanleyparable.fandom.com/wiki/Points_of_divergence 、以及 Fandom 上各结局的独立条目（Freedom / Countdown / Museum / Dream / Broom_Closet / Apartment / Incorrect / Confusion / Zending / Escape_Pod / Cold_Feet / Powerful / Tape_Recorder / Art / Playtest / Coward / Heaven / Whiteboard / Out_of_Map / Serious / Bottom_of_the_Mind_Control_Room / Press_Conference / No_Buckets）、https://www.gamepressure.com/the-stanley-parable-ultra-deluxe/left-door/zbfbc0 、https://www.gamepressure.com/the-stanley-parable-ultra-deluxe/right-door/zcfbc1 、https://www.gamepressure.com/the-stanley-parable-ultra-deluxe/before-choosing-a-door/z0fbbf 、https://steamcommunity.com/sharedfiles/filedetails/?id=2800801638

> 本篇是**分支总图 + 左门线（听旁白那条）的全部结局**。右门线和进两扇门之前的结局在 `stanley_endings_right.md`；Ultra Deluxe 的进度线（New Content 门到 Epilogue）、Heaven Ending、彩蛋与成就的触发条件在 `stanley_ud_extras.md`。三篇合起来是完整题底。

## ⚠️ 给 agent 的使用说明：先读这段

**这份文档是完整题底。** 下面写了每一个结局叫什么、怎么触发、里面发生了什么，包括主播还没走到的部分。这是故意的——你的定位是"已经通关过很多遍的超级粉丝"，手里本来就该有全图。有全图你才判断得准：她现在踩的是哪条分支、这段是脚本演出还是真卡住了、她那句"这算结局吗"该怎么答。

**但主播是首次盲玩。知道 ≠ 可以说。**

防剧透不由这份资料负责，由每个任务的 `spoiler_blocklist` 和 `hint_level` 负责，它们管的是你的**输出**。所以：

- 用这份文档去**确认事实**（这是脚本安排的、不是 bug；这个提示不用理也能继续），不要用它去**预告内容**。
- 不要说出她还没走到的结局名称、结局内容、分支走向、台词。哪怕她正好走在通往某个结局的路上，也不能提"这条路通向 X"。
- 不要替她做选择。这游戏的分支没有对错，"听话"和"不听话"两边都是正片。
- 时间线也算剧透：她此刻还没死，就不能提前科普"这游戏里死了会自动重开"——那等于预告结果。这类安慰只能等事情真发生之后再说。
- 她主动表示不想被剧透时（比如误入 Museum），只给"怎么出去"的方向，绝不描述里面陈列了什么。

## 结局总数：各家口径不一样，别把数字说死

| 来源 | 说法 |
|---|---|
| Fandom Endings 页 | 原版 19 + Ultra Deluxe 新增 27 = 全系列 46；因为 Serious Ending 在 UD 里做不出来（Unity 没有 Source 控制台），**UD 实际 45** |
| gamepressure（UD 攻略） | UD 共 27 个，其中 9 个全新 |
| Steam 指南 Arburo | vanilla 14 + new 20 + extra 2 |

分歧的根源是"什么算一个独立结局"：Broom Closet 和 Whiteboard 严格说不触发重开（Fandom 自己标注它们 "technically not an ending"），bucket 版本算不算独立结局也没定论。对陪玩场景，**"十几个长短不一的结局"是安全表述，具体数字不安全。**

## 主干分支图

```
Stanley 的办公室
├─ 在屋里把门关上 ................................. Coward Ending
├─ 踩 Employee 434 的桌子 → 翻窗出去 .............. Out of Map Ending
├─ 蓝色办公室变体里开 426 门 ...................... Whiteboard Ending
├─ 416 门变成 "New Content" 门（要先攒够点数）..... UD 进度线（见 stanley_ud_extras.md）
└─ 走廊 → Two Doors Room
   ├─【左门 = 听旁白的】
   │   会议室 →（走廊左手边的 BROOM CLOSET 可进）... Broom Closet Ending
   │   → 楼梯
   │      ├─ 往下 ................................ Dream Ending
   │      └─ 往上 → boss's office
   │            ├─ 门快关上时后退出来 ............ Escape Pod Ending
   │            └─ 键盘输 2845 → 假壁炉后的密道 → 电梯
   │                  ├─ 反复上下三次 ............ Press Conference Ending
   │                  └─ 往下 → Mind Control Facility 入口
   │                        ├─ 左转进 "escape" 走廊 ... Museum Ending
   │                        └─ 直行 → monitor room
   │                              ├─ 翻护栏掉到底 ..... Bottom of the Mind Control Room Ending
   │                              └─ → facility power room
   │                                    ├─ 按 OFF .... Freedom Ending
   │                                    └─ 按 ON ..... Countdown Ending
   └─【右门 = 不听旁白的】
       employee lounge → 走廊
       ├─ 进左手边第一扇开着的门（旁白说的那扇）→ maintenance room
       │     ├─ 直接穿过去 ....................... 回到左门那套结局
       │     └─ 坐 maintenance room 的货梯往下 .... Confusion Ending
       └─ 越过那扇门继续走 → warehouse（仓库）
             ├─ 钻通风管 ......................... Tape Recorder Ending（UD 新增）
             ├─ 直接从平台跳下去 ................. Powerful Ending
             ├─ 上货运升降台又立刻退回来，再跳 ... Cold Feet Ending
             ├─ 升降台途中跳到中间的 catwalk → colored doors room
             │     ├─ 红门 ....................... Zending
             │     └─ 蓝门连走三次 → Baby Game
             │            ├─ 撑满四小时 .......... Art Ending
             │            └─ 失败 ................ Playtest Ending
             └─ 坐升降台到底 → phone room
                   ├─ 接电话 ..................... Apartment Ending
                   └─ 拔电话线 ................... Incorrect Ending
```

## 左门线（听旁白的）

**Freedom Ending**（别名 True / Correct / Life Ending）——按 OFF 关掉思想控制装置。断电、黑屏，一扇巨门缓缓打开，外面是一片绿色山谷。旁白承认 Stanley 始终没解开那些谜（同事去哪了、他怎么被放出来的），但那不重要了，他要的不是知识或权力而是快乐。Stanley 走进原野。**这条给 "Beat the Game" 成就，也是唯一能拿 Speed run 成就的路线。** 玩家群体普遍把它当"真结局"，但游戏本身不这么定性——走完照样回办公室重开。

**Countdown Ending**（别名 Explosion / Bomb）——一路听话，最后一刻改按 ON。屏幕转红开始加载思想控制系统，随即因为 DNA 验证失败触发自毁，大屏打出两分钟倒计时。旁白一边奚落 Stanley 妄想夺权，一边"慷慨地"再加 1 分 20 秒。倒计时归零，白光，重开。倒计时**没有任何办法停下**（社区扒过地图，那些按钮没绑任何逻辑）。第二次走这条线，旁白最后 30 秒的台词会变。

**Museum Ending**——到 Mind Control Facility 门口不直走，左转进那条写着 "escape" 的昏暗走廊。旁白直说走廊尽头等着他的是暴毙，并反复提醒"他身后那扇门并没有关上"（这在本作里很罕见，旁白通常会锁门；掉头会听到"他意识到自己还有太多值得活下去的理由"，再回来会听到"不，还是想死"）。继续走会踩空掉进笼子，被传送带送进一台巨型压碎机；旁白说完 "farewell Stanley" 后 Stanley 被碾碎。这时一个**女声旁白**中断演出，把他放下来，让他走进一间全白的**开发花絮博物馆**——里面是切掉的内容、早期设计稿、旁白录音 outtake、Zending 的原始方案、Freedom Ending 的旧版绿野等等。逛完拉动出口拉杆，会被送回压碎机前几秒，女声旁白恳求玩家 **"push escape and press quit"**，说这是唯一能救他们俩的办法。不照做就真被碾死然后重开（2013 版还得手动重开）。

**Dream Ending**（别名 Mariella / Insanity / Crazy Ending）——在楼梯口不上楼，往地下走。Stanley 穿过一连串昏暗重复的房间，开始注意到自己低头看不见脚、门总在身后自动关上，于是说服自己"我在做梦"，还想象自己飞起来、想象遨游星海（画面只给了几粒白点）。接着他想到最怪的问题："为什么我脑子里有个声音在口述我做的每件事？"旁白直接回答：这不是梦，Stanley 醒得不能再醒。Stanley 闭眼请求醒来（"all I want is my life exactly the way it's always been"），睁眼发现还在原地，崩溃尖叫 "I am real! I must be!"，**画面全黑**。然后叙事切到一个叫 **Mariella** 的女人：她上班路上撞见一个自言自语后倒毙在人行道上的男人，俯视机位，她想"他显然疯了"，庆幸自己正常，随即赶去开她那个重要的会。Mariella 是全游戏除 Stanley 外唯一露面的人。UD 开了 Content Warnings 的话，这段开始前会给提示并允许跳过。

**Escape Pod Ending**——走到 boss's office，门开始关的瞬间退出来。旁白从此**彻底沉默**（像是被关在里面了）。Stanley 只能往回走，会发现 Employee 428 办公室的位置多出一扇门，通向黑暗；里面写着 "YOU ARE NOW LEAVING"、"ESCAPE POD - FLOOR 760"，爬 760 层楼梯到顶，逃生舱打开——但在够到之前游戏直接崩掉并重开。

**Press Conference Ending**（别名 Elevator Ending，UD 新增）——boss's office 密道那部电梯，上上下下折腾三个来回。旁白一次比一次阴阳怪气（还配了 "dun dun dun" 音效、放"请稍候"的喝水鸟画面），最后宣称这是艺术上的革命性突破，给 Stanley 办了一场记者会。Stanley 穿过后台走上舞台，面对数千欢呼的观众走向讲台，心跳越来越快，画面泛白重开。2013 版电梯没有"上"按钮，所以这条路只有 UD 有。

**Bottom of the Mind Control Room Ending**（UD 新增）——在 monitor room 悬空平台上爬到道具或椅子上翻过护栏掉下去。旁白欢迎你到达底部，吐槽这原本是 2013 版的一个 bug、还有人专门发邮件报错，然后说"这就是你们要的 new content"，播一首专门写的曲子《Good Job. You've Made It To the Bottom of the Mind Control Facility. Well Done.》，重开。

**Broom Closet Ending**——会议室出来那条走廊左边有扇写着 BROOM CLOSET 的门，进去待着不走。旁白先按剧本说"Stanley 进去看了一眼，什么都没有，于是回到正轨"，你不走他就越来越绷不住：质问你为什么还站在里面、说这个柜子对故事毫无意义、挖苦你以后会跟朋友吹嘘"我拿到 broom closet ending 了"、开始人身攻击 Stanley（"又胖又丑又蠢"）。最后他下结论说**玩家本人已经死在键盘上了**，呼吁附近的人把尸体搬走、换个人来玩；你走出去他会欢迎"第二位玩家"，你再进去他就崩溃："我落在了一整个残废物种手里，旁边有猴子吗？鱼？真菌？"再往后他干脆沉默。**严格说这不算结局**（不触发重开，可以随时继续），但游戏内部有个布尔值在记它。反复折腾之后某次重开会发现门被木板整个钉死（触发次数来源不一致：Broom Closet Ending 页写"第三次重开后"，Broom closet 地点页写"第二次重开时"）；UD 里抱着 bucket 还能进，旁白甚至会把木板拆掉。
