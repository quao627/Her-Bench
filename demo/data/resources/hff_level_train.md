# Human Fall Flat · Train（第 2 关，火车站）

> 来源：
> - https://humanfallflat.fandom.com/wiki/Train （fandom wiki 的 Train 页，本关场景与房间顺序的主要依据。网页直连返回 402，实际通过 `https://humanfallflat.fandom.com/api.php?action=parse&page=Train&prop=wikitext&format=json` 取到完整原文）
> - https://walkthroughhumanfall.blogspot.com/2018/09/level-2-train.html （逐关文字攻略，正文直接引用 TrueAchievements 的成就解锁率，可视为 TA 攻略镜像；下文简称"TA 系攻略"。TA 本站被 403 拦截）
> - https://steamcommunity.com/stats/477160/achievements/ （Steam 全球成就页）
> - https://gameplay.tips/guides/1583-human-fall-flat.html （100% 成就攻略，Train 一节含三个成就的具体做法）
> - https://steamcommunity.com/app/477160/discussions/0/353915309350352962/ （Steam 讨论 "This bothers me more than it should"，帖子里有玩家给出了暗迷宫捷径最完整的一段文字说明）
> - https://steamcommunity.com/app/477160/discussions/0/3160848559778706213/ （Steam 讨论 "Weird voice line/easter egg?"，各关语音彩蛋）
> - https://steamcommunity.com/sharedfiles/filedetails/?id=1605791801 （Steam 指南 "Hidden Messages"，作者 Frick）
> - https://www.speedrun.com/api/v1/games/hff/levels （speedrun.com 官方关卡表）

---

## ⚠️ 本文件的一处重大更正（先说清楚）

这份资料的早先版本，在"核心机制"一节里写了一整段 **"货运电梯（industrial lift）+ 箱子 + 压力开关连环机关"**，描述玩家要在几个相通房间之间来回搬箱子、把箱子压在开关上开门、坐电梯上下运货。

**这一整段是错的，Train 关里没有电梯、没有箱子压力开关。**

- fandom wiki 的 Train 页把主路线（wiki 称之为 "The Dumpster Path"）从头到尾写了一遍，全程只有：垃圾桶、翻倒的长椅、轨道上的车厢（train carts）、大货箱（train boxes）、红色按钮门、立柱、天花板灯具。**一次都没提到电梯或压力开关。**
- TA 系逐关攻略的 Train 章节同样从头到尾没有电梯和开关。
- **箱子（crate）+ 地面开关（ground switch）+ 紫色升降台是 Carry 关（第 3 关）的机制。** fandom wiki 的 Carry 页原文："This dream introduces crates and ground switches, which will be important in future puzzles… The third room is a bit different as it contains a purple lift."

**错误是怎么来的**：SegmentNext 那份被广泛引用的全流程攻略把关卡名标错了——它标着 "Train Level Walkthrough" 的那一段（"put boxes on the switches to ensure the doors stay open. Get past the first elevator and move the train car…"）写的其实是 **Carry**；它标着 "Canyon Level" 的那段其实是 **Mountain**。照抄那份攻略就会把 Carry 的机制安到 Train 头上。

下面的流程按 fandom wiki + TA 系攻略重写。

---

## 关卡定位

Train 是主线第 2 关。fandom wiki 称它是 *"the second tutorial level"*，教的是**跳跃**和**用物理挪动重物**。

它也是**全游戏第一个有两条路线的关卡**——wiki 原文：*"This level will be the first out of many other levels that has 2 paths, a main path and an optional path."* wiki 把两条路分别命名为：

- **The Dumpster Path**（主路线，从垃圾桶那扇门开始）
- **The Secret Passage Path**（暗道路线，wiki 对它的全部说明只有一句：*"it is a way for the player to get to the exit faster but it is a maze in darkness"* —— 一条能更快到出口的路，但里面是一片漆黑的迷宫）

**场景设定**：一座废弃破败的老火车站。一列蒸汽机车像是从站台冲破墙壁、坠落到站外街道上。站体是半圆筒形屋顶、开顶、矩形基座，护栏被撞断。整栋建筑长满苔藓和树根，暗示荒废已久。机车是黑色红边，有驾驶室，**烟囱上挂着一条链子吊着一盏灯笼**（这盏灯笼就是暗道路线的关键道具）。你脚下那条街是断裂的，往下就是白色虚空（the White Void）。

---

## 主路线：逐段完整解法

### 1. 出生点（街上）：黄色垃圾桶挡门

- **场景**：出生在车站外的街上，机车撞出来的坑和碎片散了一地。**附近有两张长椅**（一张在你落点旁边，一张靠墙），墙边有一个**黄色、黑盖的垃圾桶（dumpster）顶着一扇朴素的双开门**。
- **完整解法**：抓住垃圾桶把它从门口拖开，然后直接推门走进去（不需要按钮）。
- **顺手的两个成就**（做法来自 gameplay.tips 和 TA 系攻略，两处一致）：
  - **`Public service`**（官方描述 "Place 5 pieces of debris in a dumpster"）：先把垃圾桶**拖到碎片堆旁边**方便搬；**从后面爬上去抓住盖子往下拽，把盖子打开**（TA 系攻略强调"从后端开最容易"）；然后捡 5 块碎片扔进去。
    - gameplay.tips 特别加了一条：**"Pink debris is the only kind that works for this achievement for some reason."**（不知为何只有粉色碎片算数。）**这是社区攻略的说法，官方成就描述只写了 "5 pieces of debris"，没有提颜色。** 两份攻略都建议挑最小的碎片，好搬也占地方小。
  - **`Convertible ride`**（官方描述 "Ride 50m in a dumpster"）：**先把桶清空**（里面有东西会更难滑），人爬进桶里，**双手抓住桶壁，按住跳跃键，同时往各个方向推**，靠这种方式把桶开出 50 米。TA 系攻略的具体做法是"到桶的前端或后端，双手抓住，然后跳——这样是在推桶而不是把自己跳出去"，来回开就行，成就进度可以在游戏里查。
    - isaac 的 151 成就指南补了一条信息：**Train 和 Demolition 两关都有垃圾桶**，这个成就在哪关刷都行。
- **要走暗道路线的话**：先去机车前部把**灯笼**取下来带上（见下面第 6 节）。

### 2. 第二个房间：翻倒的长椅 + 交叉轨道上的两节车厢

- **场景**：过了垃圾桶那扇门是一个小房间。**进门右手边有一张翻倒的长椅**（wiki 的原话带着调侃："There is also an overturned bench on a raised pavement that you can flip back up again. (if you have OCD issues, but no-one is judging you)"）。房间里还有**两节红色车厢停在轨道上，把通往下一道门的路挡死了**。
  - **轨道形状两份来源写法不同**：fandom wiki 写 *"on rail tracks in a criss-cross pattern"*（十字交叉）；TA 系攻略写 *"you'll see some red train cars in an L shape"*（L 形）。**说的是同一处两条轨道相交的布局，只是形容角度不同。**
- **完整解法（车厢）**：TA 系攻略的具体描述是——**先把和长椅平行的那节车厢往它的黄色轴承方向拉开**，腾出空间；然后**把和你要过的那道门平行的那节车厢推到它的黄色轴承上、让开门口**。顺序反了两节车厢会在交叉口互相顶死，得退回来重来。车厢在轨道上滑动比较省力，顺着轨道方向推拉即可。
- **`Perfectionist` 成就**（官方描述 "Align a flipped bench with a wall"）：把那张翻倒的长椅**从正面推一下翻回正面朝上**，然后让它**贴齐墙面**。TA 系攻略说了一个关键手法：**长椅从正面是推不动到位的，要走到一端把它往墙的方向拉到底，再走到另一端重复，一点点蹭齐**。gameplay.tips 说翻正通常就够了，不行再对齐墙。

### 3. 第三个房间：一高一低两节车厢

- **场景**：又是两节红色车厢，**一节在地面，一节在抬高的平台上**，高处那节挡着门。
- **完整解法**（fandom wiki 和 TA 系攻略一致）：**先跳上地面那节车厢，再从它跳上高处那节**，然后走到左边**把高处那节车厢推下平台**，被它挡住的门就露出来了。

### 4. 第四个房间（小公园）：站在货箱上抓墙 —— 本关最关键的一招

- **场景**（fandom wiki 描述）：这个房间比前面几间大，长满杂草，树根缠着一根高柱子、爬满墙壁。你进门时站在一处高台上，**右手边有一段楼梯下到一个小公园**，里面有一只空的喷泉池和一张长椅，你身后还有另一张翻倒的长椅。**房间左侧有一节红色大货箱（train box）**，得靠它才能到左前角那块高台。
- **完整解法**：这一步是全关最容易卡住、也最不可能自己想到的地方。TA 系攻略的原文是：

  > *"go on the red box car and grab onto the wall. While you're holding onto the wall, you need to walk to the left, and as you're doing this, you'll notice the box car moving towards the right (physics!)"*

  也就是：**站到货箱上面，伸手抓住旁边的墙，然后人往一个方向走——因为你抓着不动的墙，货箱会往相反方向滑。** 重复这个动作、随时调整站位别掉下去，直到货箱挪到能让你跳上有门那块平台的位置，**按红色按钮开门**。
- **方向性提示**（不剧透版）：那节货箱推是推不动的，但你站在它上面的时候，身体和它之间的作用力是双向的——试试抓住旁边固定不动的东西再走。

### 5. 两段过渡走廊

- 第五个房间是建筑背后的一条过渡走廊，角落长着树根，尽头又是一道厚重门，**按红色按钮**通过。
- 第六个是另一条向建筑左侧拐的走廊，有一段楼梯通向车站内部。
- fandom wiki 在这里留了一句耐人寻味的话：*"Oddly enough, there is a strange window that you pass by once you go through here."*（奇怪的是，你经过这里时会路过一扇奇怪的窗户。）**这扇"奇怪的窗户"极可能就是暗道捷径的出口——从主路线这一侧看过去，它显得莫名其妙。**

### 6. 车站内部：抓立柱推货箱 → 阳台出口

- **场景**：车站内部散落着好几节红色大货箱，墙上有机车撞出来的大洞。
- **完整解法**（TA 系攻略的分步）：
  1. 从左边那段楼梯上去，跳到其中一节货箱上；
  2. **抓住立柱、人往右走，货箱就往左移**——和第 4 点是同一招，只是把"墙"换成了"柱子"。一根柱子推到尽头就换下一根重复；
  3. 一路把货箱挪到能跳上"两侧带木板的那节货箱"的位置；
  4. 从那里跳到长的那节货箱上，走过去；
  5. 上楼梯，**按红色按钮开门**；
  6. 门后是建筑背面的外部阳台（护栏同样爬满苔藓和树根），**从边缘一跃而下**即通关，解锁 `Choo Choo!`（官方描述 "Complete 'Train'"），进入下一关 Carry。
- fandom wiki 的版本在这一段补充说，中途还可以**踩天花板灯具**当过渡落脚点（原文 "Hop across more boxes and ceiling lights until you reach the final box"）。

---

## 可选路线：暗迷宫捷径（The Secret Passage Path）

fandom wiki 确认这条路存在，但页面本身还是个 stub，只写了一句"能更快到出口，但里面是黑暗迷宫"。**目前能找到的最完整描述来自 Steam 讨论区一位玩家的回帖**（帖子 "This bothers me more than it should"），原文：

> *"On the first level (not the tutorial), you'll immediately notice a train that's crashed over a balcony, leaving a mess. Behind the train, there's a door that a lot of people ignore. This door actually lets you skip half the level. The problem is that, once you enter the door, it's pitch black inside, and a maze. The trick here is to take the lantern off the front of the train, clear the rubble in front of the door, and then use the lantern to guide your way through the maze inside. You'll know you've reached the end when you find a room with a box and a vent. Pull the vent down and hop out to find yourself at the staircase leading up to the second level. There's nothing really of interest inside the maze itself."*

翻成中文的流程：

1. **先把机车前部（车鼻位置）那盏灯笼取下来拿在手上**——wiki 确认灯笼是用一条链子挂在烟囱的钩子上的。
2. **机车后方有一扇很多人会忽略的门，被瓦砾堵着，先把瓦砾清开。**
3. 钻进去，里面**伸手不见五指**，是一个迷宫。靠灯笼的光摸索。
4. 走到尽头会找到**一个放着木箱的小房间，墙上有一个通风格栅（vent）**。
5. **把格栅拉下来钻出去**，落点就在通往关卡后段的楼梯那里。
6. 迷宫里面本身没有任何值得拿的东西。

**同一个帖子里另外两位玩家的补充**：

- *"I found a wall vent thing on the last bit of train that you can jump into and there is a box in the room and its a super dark maze and you can find your way to 2 doors that cant be opened at the end."* —— 迷宫深处**有两扇打不开的门**（死路），而且这条通道**从主路线那一侧的通风口反向钻进去也可以**。
- 还有玩家表示自己在 Switch 上"反向走完了这个迷宫"。

> **更正**：早先版本把出口写成"爬上箱子从**窗户**翻出去"。按 Steam 帖子的原文，出口是**墙上的通风格栅（vent）**，做法是把它拉下来钻出去。木箱确实在那个房间里。

---

## 隐藏语音彩蛋

**"It was dark, I couldn't see anything"**（当时太黑了，我什么都没看见）。

- **触发条件**：**不带灯笼**摸黑走完暗迷宫。
- Steam 指南《Hidden Messages》给的操作建议很实用：**把画质调到最低或关掉阴影**，这样即使不拿灯笼也能勉强看清路，走完就能听到这句台词。
- 来源交叉：这句台词在 Steam 讨论区的帖子里（"the voice over said 'It was dark, i could not see anything'"）和《Hidden Messages》指南里各自独立出现过，措辞略有出入（could not / couldn't），**指同一句**。
- 有意思的争议：另一个 Steam 帖子里，有玩家总结说自己"在除了 mansion、train 和 aztec 之外的所有地图都找到了彩蛋语音"，也就是**这部分老玩家认为 Train 根本没有彩蛋语音**。这和上面两处记载冲突，**记录分歧，不下结论**。

---

## 本关能拿到的成就

| 成就 | 官方英文描述 |
|---|---|
| `Choo Choo!` | Complete "Train" |
| `Public service` | Place 5 pieces of debris in a dumpster |
| `Convertible ride` | Ride 50m in a dumpster |
| `Perfectionist` | Align a flipped bench with a wall |

注意后三条的官方描述都**没有写死在 Train**——垃圾桶 Demolition 也有一个，长椅这关有两张。

---

## 新手常见卡点

- **不知道垃圾桶能被拖走**。开局第一个障碍就在这里，容易对着它乱撞、以为要找别的机关。
- **交叉轨道上的两节车厢乱推卡死**。顺序没想清楚就推，两节会在交叉口互相顶死，得退回来重排。这是玩家第一次遇到"轨道类"物理机关。
- **小公园那节大货箱推不动**。这是本关真正的坎——不知道"站在货箱上抓住固定的墙/柱子，人往一边走货箱往另一边滑"这一招，就只会在车厢附近反复打转。同一招在车站内部还要再用一次（换成抓立柱），后面 Water 关推那条没有操控台的小船时又要用第三次。
- **暗迷宫摸黑迷路**。没带灯笼就钻进去会彻底失去方向，还可能走进那两扇打不开的死路门空耗时间。
- **最后货箱之间的跳跃踩空**。布娃娃物理在不规则高度的货箱之间跳很容易失手，摔回地面就得重爬。

---

## 冷知识

- fandom wiki 的 Trivia：*"A very eerie sound of a steam engine and its horn can be heard in the background, indicating a dark past for this dreamscape."*（背景里能听到蒸汽机车和汽笛的诡异声响，暗示这片梦境有段黑暗的过去。）
- Train 是全游戏**第一个采用"主路线 + 可选路线"双路径设计**的关卡（Mansion 是纯线性的），后面很多关卡都延续了这种设计。
- 你脚下那条街是断裂的，断口之外就是白色虚空——这一关的地图和 Mansion 一样漂在虚空里。
