# Human Fall Flat · Mansion（第 1 关，教学关）

> 来源：
> - https://humanfallflat.fandom.com/wiki/Mansion （fandom wiki 的 Mansion 页，本关场景描述的主要依据。网页直连返回 402，实际通过 `https://humanfallflat.fandom.com/api.php?action=parse&page=Mansion&prop=wikitext&format=json` 取到完整原文）
> - https://steamcommunity.com/stats/477160/achievements/ （Steam 全球成就页，成就的官方英文名与描述）
> - https://walkthroughhumanfall.blogspot.com/2018/09/level-1-mansion.html （逐关文字攻略，正文直接引用 TrueAchievements 的成就解锁率数据，可视为 TA 攻略的镜像。TA 本站 curl 与 WebFetch 都被 403/Cloudflare 拦住，取不到）
> - https://gameplay.tips/guides/1583-human-fall-flat.html （单人 100% 成就攻略，Mansion 一节含 Mind the Gap!、Pigeon Simulator 的具体做法）
> - https://steamcommunity.com/sharedfiles/filedetails/?id=1998827316 （Steam 指南 "Mansion and ice walkthrough"，作者 Alaskix）
> - https://steamcommunity.com/sharedfiles/filedetails/?id=1605791801 （Steam 指南 "Hidden Messages"，作者 Frick，184 评分、1.1 万浏览；逐关列出隐藏语音彩蛋）
> - https://www.speedrun.com/api/v1/games/hff/levels （speedrun.com 官方关卡表，确认 Mansion 是第 1 关）

---

## 关卡定位

Mansion 是主线第 1 关（speedrun.com 关卡表和 fandom wiki 都确认），也是**教学关**。fandom wiki 的原文：*"It is served as the tutorial level and is the first level from the base game. In the Mansion level, the player is taught how to use their arms, and how to reach and grab for objects, as the player must press buttons to open the various doors leading to the exit."*

这关不考解谜脑力，只教一件事：**两只手是分开控制的，而且手的高度跟着视角走**。所有门都是"按住按钮"，其中两道要求两只手同时按住两个按钮——这是在为后面几十关的多按钮/多人协作机关铺垫。

**地图分成 4 个区域**（fandom wiki 的划分）：front porch（前廊）、main foyer（主门厅）、side yard（侧院）、garden（花园）。

整体路线：前廊 → 主门厅 →（右侧大楼梯上二楼）红色按钮门 → 侧院 → 竖排双按钮门 → 石桥 → 花园（喷泉+雕像）→ 横排双按钮出口门 → 摔落通关。

---

## 逐段解法

### 1. 前廊（front porch）：熟悉双手

- **场景**：一小块平地连着别墅前廊，白色柱子、护栏，一小段台阶通向一扇朴素的双开门，墙边种着一排尖顶树（wiki 称 spire trees）。
- **地上那个黄色的东西**：**两份来源说法不一致。**
  - fandom wiki 写的是 *"an orange-striped instruction manual, where the Creator will help you on how to progress"*（一本橙色条纹的说明书，"造物主"会通过它指导你）。wiki 的 Trivia 还补了一句 *"The Creator will talk throughout the level after you pass through a door"*（每过一道门造物主都会说话）。
  - TA 系文字攻略写的是 *"You can pick up the yellow walkie talkie for a tutorial"*（可以捡起那个黄色对讲机看教程）。
  - **两者多半指同一件黄/橙色的教学道具，只是叫法不同。** 无论叫什么，它的作用一致：捡起来会有教学提示，不捡也不影响通关。
- **完整解法**：随便抓一抓周围能抓的东西熟悉手感，然后走到双开门前，**用身体直接顶开门**（这扇门不需要按钮，纯物理推开），进入主门厅。
- **方向性提示**（不剧透版）：先别急着往前冲，试试两只手分别抓东西的感觉——它们是独立的两套键。

### 2. 主门厅（main foyer）→ 二楼红色按钮门

- **场景**：一间开阔的大厅，两侧是从头贯到尾的拱门造型。**右侧有一段大楼梯通往二楼。**
- **完整解法**：上右侧大楼梯到二楼，会看到一扇厚重的门（wiki 里叫 *heavy* door），**门左侧墙上有一个红色按钮**。伸手按住这个按钮门就开。
- **方向性提示**：往楼上走，留意二楼门边的墙上有没有能按下去的东西。

### 3.（可选捷径）跳过缺口 —— `Mind the gap!`

- **官方成就描述**：*"Take a big shortcut in the level 'Mansion'"*（在 Mansion 里抄一条大近道）。注意官方只说"抄近道"，没说具体位置；不过两份独立攻略描述的是同一个地方。
- **场景**：从二楼楼梯上来之后附近有一段比较宽的缺口。正常路线要绕远走完侧院那道双按钮门才能到对面。
- **完整解法**（gameplay.tips 的分步）：
  1. 出生后径直穿过大门；
  2. 上楼梯，然后停下；
  3. 把自己和缺口对齐；
  4. **张开双臂、往前走、在最后一刻起跳**（原文 "Extend both arms, walk forward and jump at the last second!"）；
  5. 多试几次；
  6. 抓住对面台沿后，**把鼠标往下移就能把自己拉上去**（原文 "Don't forget you can pull yourself up by moving the mouse down while grabbing a ledge."）。
  - 加分技巧：*"Hold left **and** forward while slightly angled to get more distance!"*（稍微侧一点角度、同时按住左和前，能跳得更远。）
- Alaskix 的 Steam 指南把这段浓缩成一句："First, go into the door. Go to the left and jump. What a big shortcut!"
- **对首次盲玩的新手不建议强求**，走正常路线更稳，这条只是速通/成就党的捷径。

### 4. 侧院（side yard）→ 竖排双按钮门

- **场景**（fandom wiki 的描述）：进侧院要先走下一小段台阶。这里有**两层地面**。上层是一条水泥走道，走道分成两个方向：**右边通往下层，左边通向另一道厚重门**。石柱上架着木头顶梁，wiki 说这可能是在暗示侧院"还没盖完"。下层没什么装饰，只有两棵尖顶树和一处能望进虚空（the Void）的视角。这里还能找到第二本说明书。走道左侧尽头是一小段台阶，通向一处高台，门就在那儿。
- **按钮排列**：wiki 原文 *"Two red buttons are placed vertically from each other."* —— **两个红色按钮是上下竖排的**（不是左右并排）。
- **完整解法**：走到高台前，**一只手按住上面那个按钮，另一只手按住下面那个**，两个必须同时保持按住门才会持续开着，松开任意一个都可能导致门重新关上。门开到位后赶紧走过去。
- **方向性提示**：这道门跟刚才那道不一样，得两只手一起用。

### 5. 石桥 → 花园（garden）→ 雕像

- **场景**：过了竖排按钮门要走过**一座窄石桥**，跨越一道把花园和别墅其余部分隔开的大缺口。花园是本关最后一个区域，标志性物件是**喷泉台上那尊"Human"雕像**。
  - **雕像长什么样，两份来源的形容差别很大**：fandom wiki 写的是 *"hunched forward with its hands on its stomach"*（弯腰弓背、双手捂着肚子）；Steam 的彩蛋指南则直接称它为 *"the statue of the urinating Bob"*（撒尿的 Bob 雕像）。同一尊雕像，玩家和 wiki 编辑的解读不同。
  - 雕像两侧各有一组台阶通向后面的高处，花园里还有更多尖顶树和石柱。
- **完整解法**：小步通过石桥（别快跑或大幅甩手，惯性容易把你带下去）。到花园后走雕像任意一侧的台阶上去，**绕到雕像正后方，爬上它背后的围栏/护栏，从围栏上举起双臂朝雕像头顶跳过去，再把自己拉上来**，站到头顶即解锁 `Pigeon Simulator`。
  - **官方成就描述是 "Stand on the head of the statue in the intro"**。gameplay.tips 特意警告：这指的是 Mansion 里的雕像，**联机大厅里那尊雕像不算数**。

### 6. 出口门（横排双按钮）→ 通关

- **场景**：花园尽头是带绿色 EXIT 标志的出口门。
- **按钮排列**：wiki 原文 *"It can only be opened by pressing the buttons that are horizontally placed next to each other."* —— **两个按钮是左右横排的**，和第 4 点那道竖排的方向不同。
- **完整解法**：站在两个按钮正中间，张开双臂，左右手分别按住左右两个按钮，保持同时按住直到门完全打开，然后走过去。**穿过出口门后角色会直接摔下去，这一摔就是通关**，解锁 `Leap of Fail`（官方描述："Complete 'Mansion'"），接着进入下一关 Train。

---

## 本关能拿到的成就

| 成就 | 官方英文描述 | 说明 |
|---|---|---|
| `Leap of Fail` | Complete "Mansion" | 通关即得 |
| `Mind the gap!` | Take a big shortcut in the level "Mansion" | 跳过二楼那道缺口 |
| `Pigeon Simulator` | Stand on the head of the statue in the intro | 站上花园雕像头顶 |
| `No escape` | Fall and respawn once | **描述是通用的**——任何地方摔落并重生一次都算，只是攻略习惯在 Mansion 开局刷 |
| `Let it rain` | Respawn 100 times | **同样是通用成就**，累计重生 100 次。TA 系攻略建议的刷法是把镜头朝向地图边缘，用皮筋卡住手柄让角色反复走出去 |

> **更正**：早先版本把 `No escape` 写成"故意在出生点走出地图边缘触发"、把 `Let it rain` 写成"在出生点反复摔死刷 100 次"，暗示它们是 Mansion 专属成就。查 Steam 官方成就页，两条的描述都不带关卡限定，是全局累计型成就。Mansion 只是最方便刷的地方。

另外 Steam 成就列表里有一条 `Wrecking Crew`，描述是 "Destroy the statue"（毁掉那尊雕像）。**官方描述没有指明是哪一关的哪尊雕像**，本次也没找到可靠来源确认它就是 Mansion 花园里这尊，所以这里只记录它的存在，不做归属判断。

---

## 隐藏语音彩蛋

Steam 指南《Hidden Messages》（作者 Frick）给出的 Mansion 触发方式：

> 走到关卡末尾的雕像那里，**抓住雕像的胯部区域大约 20-30 秒**，就会听到一句隐藏语音。

- **台词**：该指南记的原文是 **"I'm only doing this because I love you"**。
- **更正**：这份资料早先版本写的是 "I'm only **saying** this because I love you"，与目前能查到的唯一一份逐关彩蛋指南的记载不符，已按来源改成 "doing"。**这句台词只有社区指南这一个来源，没有官方文本可对照，措辞可能有出入。**
- Alaskix 的 Steam 指南也提到同一件事，只是说得更简略："you will earn an achievement by standing on the statue and the secret message by grabbing it."（站上雕像拿成就，抓住它拿隐藏语音。）

顺带一提：同一份指南记录了另外几关的彩蛋台词（Train "It was dark, I couldn't see anything"、Carry "It was this one night when i found myself alone in the bush"、Mountain "What were you thinking buddy?"、Demolition "It was an accident!"、Castle "I'm a good driver"、Water "Bigger, better, and more powerful"、Power Plant "I'm not dead, I know i'm not dead!"）。Steam 讨论区里有玩家总结说 **"i managed to find one of those in all maps but mansion, train and aztec"** —— 也就是有一部分老玩家认为 Mansion 没有彩蛋语音，和上面这份指南的说法冲突。**记录这个分歧，不下结论。**

---

## 新手常见卡点

- **不知道左右手是分开控制的**。习惯了"一个交互键"的玩家会两只手乱抓或只用一只，导致按钮按不稳、抓握经常落空。
- **不知道双按钮门要同时按住不放**。典型错误是先按一个、看到门开条缝就松手跑去按另一个，结果第一个一松门又关上，来回徒劳。
- **分不清按钮是竖排还是横排**。侧院那道是上下竖排，花园出口那道是左右横排，站位方式不一样。
- **走位/甩手导致意外掉落**。布娃娃物理下跑动加挥手很容易带偏重心，过石桥、爬雕像围栏、走侧院上层走道时尤其容易踩空。
- **不小心走出地图边缘**。前廊边缘、侧院分岔口边缘都很空旷。**掉下去不算失败**——fandom wiki 在 Trivia 里明确写着 *"Even though it is the safest level in the game, you can still fall off the edge of the map and restart."*（就算是全游戏最安全的一关，你照样能从地图边缘掉出去然后重来。）
- **想找"解谜"却找不到"解谜"**。这是教学关，机制直白到只有按按钮开门，有些新手会下意识去找更复杂的机关而卡壳。

---

## 冷知识

- fandom wiki 的 Trivia 三条：这是游戏第一关；每过一道门"造物主"都会说话；就算它是全游戏最安全的一关，你依然能掉出地图然后重来。
- 侧院下层的地面除了两棵树什么都没有，wiki 说它的作用就是"给你一个能望进虚空（the Void）的视角"——这关的地图是漂在虚空里的一块。
- 这一关虽然是教学关，却挂着好几个跟"胡闹"有关的成就（Mind the gap!、Pigeon Simulator，加上顺手能刷的 No escape 和 Let it rain），密度并不低。
