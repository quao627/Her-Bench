# Human Fall Flat 核心机制与操作

> 来源：
> - https://store.steampowered.com/app/477160/Human_Fall_Flat/ （官方 Steam 商店页，游戏自述与功能标签，经 store.steampowered.com/api/appdetails 取原文）
> - https://steamcommunity.com/stats/477160/achievements/ （Steam 全球成就页，151 条成就的官方英文名称与描述，是本文里判断"某个行为在游戏里到底算什么"的最高优先级依据）
> - https://humanfallflat.fandom.com/wiki/Mansion 、https://humanfallflat.fandom.com/wiki/Train 、https://humanfallflat.fandom.com/wiki/Commands （fandom 社区 wiki；网页直连被 402 拦，改走 `api.php?action=parse&prop=wikitext` 取原始 wikitext）
> - https://en.wikipedia.org/wiki/Human:_Fall_Flat （开发背景、设计意图）
> - https://gameplay.tips/guides/1583-human-fall-flat.html （单人 100% 成就攻略，含大量具体操作描述）
> - https://walkthroughhumanfall.blogspot.com/2018/09/level-1-mansion.html 等分关页面（一份逐关文字攻略，正文里直接引用 TrueAchievements 的成就解锁率数据，可视为 TA 攻略的镜像；TA 本站 curl/WebFetch 均被 403 拦截）
> - https://www.chaptercheats.com/cheat/pc/362906/human-fall-flat/hint/158865 （玩家 Cinnamon 撰写的 Water 关船只操作详解，本文载具部分主要依据）
> - https://steamcommunity.com/sharedfiles/filedetails/?id=3246543535 （Steam 指南《ALL achievements in Human Fall Flat [151/151]》，作者 isaac_Nagibat0r，420 评分）
> - https://www.youtube.com/watch?v=fliG3qY_K1M （视频 "How To Swing Climb In Human Fall Flat"，频道 intro，3 分钟，专门讲荡墙爬升）
> - https://steamcommunity.com/app/477160/discussions/1/1488866813770653167/ （Steam Bug 区："Flying Glitch/Infinite Jumps Glitch"）

---

## 一、这游戏为什么"操作起来这么怪"

**这是设计，不是手感差。** 官方 Steam 商店页把它定义成 "a hilarious, light-hearted physics platformer set in a world of floating dreamscapes"（一款设定在漂浮梦境里的搞笑轻松物理平台游戏），Wikipedia 归类为 puzzle-platform（解谜平台），引擎是 Unity。角色是一具全物理模拟的软体布娃娃，走路、摆臂、抓握全部交给物理引擎算，没有"按一下键播一段动画"这种事。

有一条开发史很能说明问题（来源：Wikipedia 引 TheGamer 对开发者 Tomas Sakalauskas 的采访）：他本来是想做一个类似 Limbo 或 Portal 那样谜题严丝合缝的游戏，结果拿自己儿子做测试时发现"他想尽一切办法不去解谜"，只顾着玩物理引擎本身。于是他改了方向，故意把谜题做得 "not really watertight"（不那么密不透风），允许乱来、允许绕路、允许用开发者没想到的方式过关。所以**同一个谜题有多种解法是官方明确的设计目标**，玩家瞎试不是走弯路，就是这游戏本来的玩法。

摔倒、抓空、把自己甩飞出去，这些是游戏的卖点而不是失败。IGN 的 Dan Stapleton 在 7.9/10 的评测里干脆说这游戏更适合看别人玩而不是自己玩，理由正是这套滑稽的操作和动画。

## 二、基本操作

PC 默认键位：

- **WASD**：移动
- **Space**：跳跃
- **鼠标移动**：控制视角——**同时也控制两只手伸出的方向和高度**
- **鼠标左键**：左手抓取（按住不放＝一直抓着，松键＝松手）
- **鼠标右键**：右手抓取

手柄上对应 **L2/LT** 抓左手、**R2/RT** 抓右手（多份攻略与教学视频一致这么写；swing climb 教学视频里作者的原话就是 "let go of R2 or L2"）。

**两只手是完全独立的两套输入。** 你可以只抓一只手做精细动作（拉杆、按按钮、拎小东西），也可以双手一起抓来爬墙、搬重物、扶稳自己。很多机关直接把这一点做成了门槛：Mansion 关有两道门需要两只手同时按住两个按钮，松开任意一只门就会重新关上（来源：fandom wiki Mansion 页明确写了出口门 "can only be opened by pressing the buttons that are horizontally placed next to each other"）。

还有一个"瘫倒 / ragdoll"动作：把身体主动放软摔下去。fandom 的 Commands 页记录了控制台里对应的 `y` 键效果是 "Will ragdoll you"；实际游玩中这个动作被用来做特定姿势的入水——Water 关的 "Head First"（头朝下入水通关）成就就是靠站到边缘、看向正下方、然后把身体放软实现的。

## 三、最重要的一条规则：手跟着视角走

**抬头看，手就往高处伸；低头看，手就往低处伸。** 这是整个游戏最核心的一条，几乎所有"我明明抓住了怎么还是上不去"的问题都出在这。

由此派生出全游戏最常用的两个动作：

1. **翻越台沿（低头上拉）**：双手搭上边缘之后，把视角往下压。gameplay.tips 的攻略在讲 Mansion 跳缺口时特意提醒："Don't forget you can pull yourself up by moving the mouse down while grabbing a ledge."（别忘了抓住台沿时把鼠标往下移就能把自己拉上去。）这就是标准的上台阶动作，不是靠跳。
2. **举手够高处**：想抓头顶的东西，先抬视角再按抓取键，而不是先按键再抬头。

划船的时候这条规则会显得"反过来"，但原理一样：桨是杠杆，**低头＝把手压低＝桨叶抬出水面，抬头＝桨叶压进水里**（来源：chaptercheats 的船只操作详解，原文 "to lift the paddle(s) in the air, you must look down, and vice versa to lower them into the water"）。

## 四、攀爬：从慢速换手到 swing climb（"cheese method"）

攀爬是新手第一个大坎，也是全游戏最有用的通用技能。三个层次：

**1. 有台沿的地方——抓住 + 低头上拉。**
双手搭上边缘，视角往下压，身体就被拽上去了。这是基础，别的都建立在它上面。

**2. 交替换手往上爬。**
双手抓稳后先把身体拉起来一点，松开一只手，趁另一只手还挂着迅速把空出来的手抓到更高的落点，然后换边重复。要有节奏——一只手、另一只手。

**3. Swing climb（荡墙爬升），社区通称 "cheese method"。**
这是**面对完全没有落脚点的光墙时唯一的通用解**，也是各路成就攻略里出现频率最高的词。TrueAchievements 系的逐关攻略在 Castle 的敲钟成就、Power Plant 的偷电池成就等好几处直接写 "Use the cheese method to swing and climb your way up this"；isaac_Nagibat0r 的 151 成就指南更是在开篇就说，通关类成就"most often use wall climbing, the essence of which is to swing higher and higher, catching on with your arms"（多半要用爬墙，核心就是一边荡一边往上抓）。

教学视频 "How To Swing Climb In Human Fall Flat" 里的做法：

- 跳起来抓住墙面，**确认双脚离地、而且身边没有贴着墙角或柱子**——作者明确说贴太近就荡不起来；
- 松开一只手，用左摇杆（键盘对应 A/D）**左右来回推**，把身体荡起来积累摆幅；
- 摆幅够大之后，在荡到高点的一瞬间抬手往上抓；
- 一次只能上去一点点，作者原话是 "you'll be able to get a little bit of distance a little at a time so it is pretty time consuming"（一次只能挪一点，确实费时间），但比想象中快；
- 上不去的最常见原因就是**摆幅不够**，不是手法不对。

**4. 跳跃辅助爬升。**
抓着墙的同时按跳，配合左右方向借力。isaac_Nagibat0r 在指南里说自己"在后面的关卡开始用 wall jumping，这是可选的，但对某些关卡的通关有帮助"。快，但容易失手，建议先练熟 swing climb。

> 顺带一提：Steam 的 Bug 区有一个流传很广的**传送带无限跳 glitch**（帖子标题 "Flying Glitch/Infinite Jumps Glitch"，2017 年发帖，到 2018 年 2 月仍未修），玩家反馈"从第一次碰到传送带那关之后，按住空格就能无限跳"，能直接跳过整段关卡。跟帖里有人说重开游戏就恢复正常了。这不是正常机制，只是遇到时不用慌。

## 五、跳跃

跳跃本身就是 Space，但它吃物理：助跑越快跳得越远，手臂的姿势也会影响重心。

几乎所有攻略在讲远距离跳跃时都强调同一套动作：**把双臂举起来 → 助跑 → 贴着平台边缘的最后一刻起跳 → 尽量把手往对面探出去抓边 → 抓住后低头把自己拉上来**。gameplay.tips 讲 Mansion 的 "Mind the gap!" 捷径时写的就是 "Extend both arms, walk forward and jump at the last second!"，并补了一条实测技巧："Hold left *and* forward while slightly angled to get more distance!"（斜着按住左+前能跳得更远。）

起跳太早是新手跳不过缺口最常见的原因。

## 六、抓取、搬运与投掷

- **抓 = 按住**，不是点按。松键就是松手。很多摔下去都是因为手抖松了键。
- 小物件单手就能拎；大箱子、重物用双手抱住，倒着走或推着走更稳。
- 想把抓着的东西举高，抓住之后抬视角。
- **扔东西**：抓着物体转身甩起来，在合适的时机松开抓取键，靠动量把它抛出去。
- **重量是真的在算**。Castle 关开局砸门锁那一步，Steam 讨论区有玩家做过对照实测：用撬棍（crowbar）反复砸、甚至撬，都打不开锁；换成场景里的大石头，"didn't even need to swing it left to right, just pulled it along and bam, unlocked"，并给出结论 "First lock breaking depends on the mass of the object swung"（能不能砸开取决于挥出去的物体的质量）。所以砸不开东西时先换个更重的道具，而不是继续加大力度。

**一个贯穿全游戏的高级技巧：站在可移动物体上，去抓固定物，物体会往反方向走。** 这是 Train 关后段推车厢的正解——TrueAchievements 系攻略的原话是 "go on the red box car and grab onto the wall. While you're holding onto the wall, you need to walk to the left, and as you're doing this, you'll notice the box car moving towards the right (physics!)"。同一招在 Water 关的浮船段又用了一次（抓住蓝色管子把没有操控台的小船挪出去）。第一次遇到时基本不可能想到，是很值得提示的方向。

## 七、摆动：荡绳、荡灯笼、荡铁球、荡吊斗

凡是吊着的东西（绳子、灯笼、铁钩、锚链、拆迁铁球、吊斗）都走同一套物理：**别硬拽，靠节奏积累摆幅。**

- 人挂在上面时：`AH, EO, EO, EO, EO, OOOOO!` 这个成就（官方描述 "Use the rope to go above the abyss in the level Mountain"）的标准做法是——"as your Human swings forward, press your 'move forward' button, and as it swings backward, press your 'move backward' button"（往前荡时按前进，往后荡时按后退），来源 gameplay.tips。荡秋千的原理，一模一样。
- 用拉杆控制吊斗时：**到最高点立刻反向推**。Demolition 关的吊斗（bucket）就是这么荡开的，攻略原话是 "move the bucket one way, and then when the bucket is at the pinnacle of its swing, immediately start moving it in the opposite direction"。gameplay.tips 给的提示更简短："Basket swings a lot if you alternate between left and right on lever."
- 松手时机统一在**摆到最高点附近**。早了矮，晚了往回走。

## 八、摔落、溺水与重生

**摔落没有伤害。** fandom wiki 在 Mansion 页的 Trivia 里直接写："Even though it is the safest level in the game, you can still fall off the edge of the map and restart."（就算是全游戏最安全的一关，你照样能从地图边缘掉出去然后重来。）

**掉出地图＝原地重生，没有别的惩罚。** 官方成就 `No escape` 的描述就是 "Fall and respawn once"（摔落并重生一次）。逐关攻略在 Mansion 开局教的第一件事就是：把镜头转向地图边缘（原文戏称 "the great beyond"）走出去，"You'll fall down and fall right back onto the map again"——掉下去，然后直接掉回地图上。另一个成就 `Let it rain` 是 "Respawn 100 times"（重生 100 次），攻略建议的刷法就是把手柄卡住让角色反复往边缘走。

所以画面上如果只剩云层和下坠感，那通常就是掉出关卡边缘了，游戏会把人放回最近的检查点附近，**进度不丢，位置重置**。

**但是水会淹死人。** 这是唯一一个和"摔落无惩罚"不一样的地方：

- 官方成就 `Learn to swim` = "Drown 10 times"（溺水 10 次）；
- 官方成就 `Breathing exercise` = "In 'Water', get out of the water in 100ms to avoid drowning"（在 Water 关于溺死前 100 毫秒内爬出水面）。
- 溺水有倒计时提示：TrueAchievements 系攻略写"头没入水后会开始听到缓慢的气泡/爆裂声，数到 16 就赶紧跳出来，因为数到 18 声就会死"；isaac_Nagibat0r 的指南说是 19 下、建议 17-18 下时出水。**两份来源在具体拍数上不一致（16/18 vs 17-18/19），但都指向"十几声之后会死"这个量级。**
- 死了同样只是回检查点重生。攻略里甚至把"跳水淹死"当成快速传送手段用（Water 关点完灯塔后 "simply jump into the water and you'll drown and respawn by the cable car"）。

**检查点**：关卡内有多个检查点，重生回最近一个。Steam 讨论区里有玩家把"读检查点"当成卡关的标准解法——Castle 那把砸不开的锁，跟帖给的建议就是 "you can just get the next checkpoint and have her respawn there"。

## 九、载具与操纵机构

这游戏后半段大量出现载具和机械，操作方式基本都遵循"**用手抓住实体控制器**"，没有专门的驾驶按键。

**划艇（rowboat，Water 关）** — 来源 chaptercheats + TrueAchievements 系攻略：
- 左手抓左桨、右手抓右桨。
- 前进：抓住两支桨 → 低头（桨抬出水面）→ 人往船尾走 → 抬头（桨压入水中）→ 人往船头走 → 重复。
- 后退：同样的循环反过来。
- 转向：只操作一侧的桨，或者干脆停下来转镜头（TA 攻略的建议是"要调方向就停止划桨，把镜头转向想去的方向"）。
- 关键是两手**同步**、动作走直上直下，不同步就会原地乱转。

**快艇（speedboat，Water 关）**：操纵手柄在船尾（黄黑配色的舵柄）。抓住往前推就走。**转向是反的**——"turning it right or left will turn it in the opposite direction"（往右扳船往左转）。

**货轮 / 油轮（cargo ship / tanker，Water 关）** — 驾驶室里两根操纵杆，**分别控制左右两侧推进器**，是标准的差速转向：
- 两杆同时前推 → 直行
- 两杆同时后拉 → 后退
- 两杆都回中 → 停
- 左杆推前 + 右杆拉后 → 向右转
- 右杆推前 + 左杆拉后 → 向左转
- 一杆推前、另一杆回中 → 原地画圈（左推右中＝顺时针，右推左中＝逆时针）

因为要同时操作两根杆，这里正好是"两只手独立抓取"这个核心机制第一次被强制用上的地方。

**叉车（forklift，Demolition / Power Plant）**：方向盘转向；**右边的操纵杆前推＝前进、后拉＝后退**；**方向盘左边另有一根杆控制货叉升降**。TA 系攻略提醒 "It's super tough to maneuver"（非常难开）。经典用法是把货叉插到闸门底下抬起来，然后拿别的东西垫住缝隙保持门开。

**翻斗卡车（dump truck，Power Plant）**：驾驶室里是**方向盘 + 右手边一根档杆**。有两档前进和两档后退——"one for a light tilt and one for a full tilt"（杆推一点是慢档，推到底是快档）。攻略作者自己都选慢档开，理由是怕冲出山路。车斗的升降开关不在车上，而是**车身左侧地面高度的一根拉杆**，扳一下车斗抬起倒货。

> 通用判断：**这游戏里凡是能坐进去、有方向盘或操纵杆的载具，基本都是给玩家开的**。官方成就 `Hitchhiker`（"Ride one of the vehicles for 10 seconds"）和 `Petrolhead`（"Use any of the ground vehicles to travel 1km"）都用的是复数 "vehicles"，说明可驾驶载具本来就是一类设计好的内容。

## 十、常见误区速查

- **误区：狂点抓取键。** 抓取是按住，不是点。
- **误区：忽视视角。** 手不听使唤九成是视角没摆对——手永远跟着视线走。
- **误区：用蛮力。** 荡的东西靠节奏不靠力气；砸不开的东西靠换更重的道具不靠多砸几下。
- **误区：光墙就放弃。** 没有落脚点的墙不代表上不去，swing climb 就是为这个准备的。
- **误区：怕摔。** 摔落零惩罚，大胆试错是这游戏预期的玩法——唯一要留意的是水。
- **误区：以为只有一条路。** 开发者明说了谜题是故意做得"不密封"的，几乎每关都有捷径、绕路和取巧解法，官方成就里甚至专门为"用非常规方式过关"设了好几个（`Wrong direction`、`Mind the gap!`、`Improvised Ammo`、`Walk the Plank`……）。
- **技巧：先练慢爬再练快爬。** 交替换手是一切进阶动作的基础。
- **技巧：站在活动物体上抓固定物。** 车厢、小船这类"推不动"的重物，往往就靠这一招挪。
