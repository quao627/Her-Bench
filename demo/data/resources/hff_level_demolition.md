# Human Fall Flat · Demolition（第 5 关，拆迁工地）

> 来源：
> - https://walkthroughhumanfall.blogspot.com/2018/09/level-5-demolition.html （本关流程的**主干来源**。这是一份逐关文字攻略，正文直接引用 TrueAchievements 的成就解锁率数据，可视为 TA 攻略的镜像；下文简称"TA 系攻略"。TA 本站 curl 与 WebFetch 都被 403/Cloudflare 拦截）
> - https://humanfallflat.fandom.com/wiki/Demolition （fandom wiki，确认为第 5 关、工地主题；页面直连返回 402，走 `api.php?action=parse` 取 wikitext。这一页只有一句话，是个 stub）
> - https://steamcommunity.com/stats/477160/achievements/ （Steam 全球成就页，四条本关成就的官方英文描述）
> - https://gameplay.tips/guides/1583-human-fall-flat.html （100% 成就攻略，Demolition 一节给了 Wrong direction 的两条提示）
> - https://steamcommunity.com/sharedfiles/filedetails/?id=3246543535 （Steam 指南《ALL achievements [151/151]》，作者 isaac_Nagibat0r，420 评分）
> - https://segmentnext.com/human-fall-flat-walkthrough/ （SegmentNext 全流程攻略的 "Construction Level" 一节——**这份资料的关卡命名不可靠**，但 Demolition 这一段本身可以拿来做交叉对照）
> - https://steamcommunity.com/app/477160/discussions/0/807952395548179484/ （Steam 讨论 "Broken lever in demolition"，2025 年 8 月，关于结尾拉杆折断）
> - https://steamcommunity.com/app/477160/discussions/0/3160848559778706213/ （Steam 讨论 "Weird voice line/easter egg?"，本关语音彩蛋）
> - https://steamcommunity.com/sharedfiles/filedetails/?id=1605791801 （Steam 指南 "Hidden Messages"，作者 Frick，给出彩蛋的具体触发条件）

---

## 关卡定位

fandom wiki 对这一关的全部描述只有一句：*"Demolition is the fifth level in Human: Fall Flat. It is a construction site level that uses helpfully destructive mechanics."*（第 5 关，一座工地，用的是"帮得上忙的破坏性机制"。）

和前面几关"搬箱子垫脚、按按钮开门"不同，这一关的核心是**把挡路的墙和玻璃砸开**。会依次出场的破坏工具：徒手拆木板 → 灭火器 → 吊斗（bucket）→ 巨石雪崩（avalanche）→ 拆迁铁球（wrecking ball）→ 叉车（forklift）。

这一关同时挂着几个和"打法分支"绑定的成就，玩法自由度很高——TA 系攻略作者本人在流程里就明确提过 **"during your speedrun you can continue through the other side of this building and skip about half the map"**（速通时可以从这栋楼的另一侧走，直接跳过大约半张图）。

---

## 逐段完整解法（TA 系攻略的主线顺序）

### 1. 撬掉门上的木板

- **场景**：出生房间，前方的门被几块木板钉死。
- **完整解法**：走到门前，**抓住木板往回拽**，一块块把它们拔下来，门洞露出来就能过。TA 系攻略的原文就是一句 "Pry the wood planks off the door in front of you and move on through."
- **方向性提示**（不剧透版）：门上钉的木板是可以直接用手抓住往外拉的障碍物，不是需要钥匙或机关的锁——确认你是抓住木板在持续用力拉，而不是在推门。

### 2. 灭火器砸玻璃

- **场景**：过门后的房间，出口是玻璃；旁边地上放着一具红色灭火器。
- **完整解法**：捡起灭火器，抡向玻璃把它砸碎，从缺口出去。这具灭火器后面还要反复用来砸墙，**别丢**。

### 3. 吊斗（bucket）+ 床垫 →`Wrong direction`

- **场景**：一根控制悬吊铲斗左右摆动的拉杆（lever），旁边地上散着几张床垫，左手边有一栋带玻璃的建筑。
- **完整解法**：
  1. 先扳一下拉杆，**用吊斗把挡在旁边的床垫撞开**；
  2. 然后开始"荡秋千"——**往一侧推杆，等吊斗荡到那一侧的最高点时立刻反向推**，如此反复，摆幅越来越大（TA 系攻略原文："move the bucket one way, and then when the bucket is at the pinnacle of its swing, immediately start moving it in the opposite direction"）；
  3. 用它**砸碎左边那栋建筑的玻璃**；
  4. **⚠️ 注意别把吊斗往右荡太多**——右边那面墙要留着完好，后面 `Primal` 成就要用手持道具砸它；
  5. 玻璃碎了之后，把灭火器抓上、跳下去，**先把灭火器放在右边那面墙旁边**；
  6. 走到刚砸开的窗口下面，**用 swing climb（cheese method）荡上去爬进窗**——进去就解锁 `Wrong direction`。
- **官方成就描述**：*"Use the window on your left instead of smashing the wall in 'Demolition'"*（走左边的窗户而不是砸墙进去）。
- gameplay.tips 给的两条提示简洁到位：*"Basket swings a lot if you alternate between left and right on lever"*（在拉杆上左右交替推，吊斗会荡得很厉害）、*"Mattresses are good to jump on"*（床垫摔上去比较软）。

### 4. 灭火器砸墙 1/4 和 2/4

- 从窗户爬回来，**捡起刚才放在右边那面墙边的灭火器，抡它砸墙**，砸开就是 `Primal` 的第 1 面墙。
- 进入下一区域后，**左前方还有一面墙**，同样用灭火器砸开 —— 第 2 面。

### 5. 传送带平台 + 玻璃房 + 箱子

- **场景**：这一区有**两块传送带平台（一块抬起、一块降下）**、一根拉杆、一间里面装着按钮的玻璃房、一个箱子。
- **完整解法**（TA 系攻略的分步）：
  1. 走到**抬起的那块平台底下，把撑着它的黄色横杆抽出来**，平台降下来；
  2. 爬上台沿，走到降下来那块平台的尽头；
  3. **跳到对面的台沿，扳动玻璃房旁边的拉杆**——这会把另一块平台升起来，让你能走回去；
  4. 跳上台沿**拿到箱子**；
  5. 抱着箱子走回平台这一侧，**用箱子把玻璃砸碎**；
  6. **把箱子放到按钮上**，通往下一区的门打开。

### 6. 黄杆卡住拉杆（保持门开）

- **场景**：下一区有一块**底下撑着两根黄色横杆**的平台，右手边是一根拉杆，**拉杆后面是一堵蓝墙**。
- **完整解法**：
  1. **把两根黄杆都抽掉**，平台降下来；
  2. 拿起其中一根黄杆，**横着塞进拉杆和蓝墙之间**；
  3. 杆会倒下来压在拉杆上，**把拉杆一直压住，门就保持开着**，然后走过去。
- **方向性提示**：抽出来的横杆别随手扔——附近有会自动弹回关闭的门，横杆可以当门挡。

### 7. 摆动平台带箱子过缺口

- **场景**：这一区有一根拉杆、左前方一个按钮、一块吊着的摆动平台、缺口对岸一个箱子。
- **完整解法**：
  1. **先用拉杆把摆动平台调到缺口正中间**，让它来回摆动、两端能分别靠近（或接近）两侧；
  2. 走下去跳上摆动平台，再从平台跳到对岸；
  3. **抓起箱子带回摆动平台边**；
  4. 平台摆近你这侧时**抱着箱子跳上去**；
  5. 平台摆到另一侧时**抱着箱子跳下去，把箱子放到按钮上**；
  6. 再踩着平台回来，进入下一区。

### 8. 抬闸放行滚石雪崩 → `Surprise!`

- **场景**：这一区你右前方有一面墙，但**先别管它——右手边紧挨着的是一座蓝色脚手架**。
- **完整解法**：**顺着蓝色脚手架爬到顶，那里有一道被栅栏挡住的闸门，把栅栏/闸门抬起来**——成堆的巨石会像雪崩一样倾泻下来，解锁 `Surprise! (Avalanche!)`（官方描述："Unleash the boulder gate in 'Demolition'"）。
- **安全提醒**：开闸前先站到侧边，别正对着滚落路径。（这一条是常识性提醒，攻略原文没写，标注为经验建议。）
- isaac 的 151 成就指南把这一步描述成"拿到 Wrong direction 之后继续往前，会遇到一架梯子挡住通往成就的路，把闸门打开就拿到成就"——**他给的先后顺序和 TA 系攻略略有出入**（TA 系把雪崩排在摆动平台之后）。这关本来就非线性，顺序有分歧不奇怪。

### 9. 用滚落的巨石砸墙 3/4 和 4/4 → `Primal`

- **完整解法**：**从雪崩下来的石堆里搬一块石头**，砸开**脚手架旁边**那面墙 —— 第 3 面。
- 进入下一区，**左边有一节红色货箱，右边有一面墙**，用同一块石头砸开 —— 第 4 面，解锁 `Primal`。
- **官方成就描述**：*"Break 4 walls without using any gadgets in 'Demolition'"*（不用任何机械装置砸开 4 面墙）。
- **⚠️ TA 系攻略的关键警告**：*"If you broke a wall using the bucket, the wrecking ball, or the box car, you'll have to start the level over."*（如果你用吊斗、拆迁铁球或者货箱破过墙，就得重开这一关。）
- gameplay.tips 补充说，能算数的手持道具包括灭火器和石头。

> 附带信息：这条警告本身也说明了一件事——**吊斗、拆迁铁球、货箱都是能砸开墙的**，只是用了就不算 Primal。

### 10. 拆迁铁球（wrecking ball）

- **场景**：往前走会遇到一块**黄色平台**，走过它的时候对面的玻璃会碎。上楼梯之后，**前方是一个按钮，前方偏右的平台上吊着拆迁铁球**。
- **完整解法（TA 系攻略的写法）**：
  1. 跳到吊着铁球的那块平台上，爬上去；
  2. **把铁球从台沿推下去**——TA 系攻略明说这一步不好做："It's a bit tough so try different maneuvers to get it moving."（有点难推，多换几个姿势试）；
  3. **铁球一掉下去，刚才那块黄色平台就会被抬到和你同高**（配重/跷跷板原理）；
  4. 走过旁边的通道进入建筑，开门拿到里面的箱子；
  5. **抱着箱子走过升起来的黄色平台，放到按钮上**，下一道门打开。

> **来源冲突（重要）**：SegmentNext 那份攻略对铁球的写法完全不同——*"use the wrecking ball to go to the other side. Use the same ball to break the wall on the right side of the crane."*（抓着铁球荡到对岸，再用同一颗球砸开吊车右侧的那面墙。）
>
> 加上第 9 点里 TA 系攻略自己的警告（用铁球破墙会让 Primal 作废），可以确定的是：**这颗铁球既能当配重把平台压起来、也能抓着荡、也能砸墙**。这关允许多种走法，不同攻略走的路不一样很正常。任务场景里"趴在横梁上抱住红色缆绳吊着的黑色铁球"两种走法都对得上——**它挂在缆绳上，能荡、能砸、也能被推下去当配重。**

### 11. 梯子上的箱子

- **场景**：这一区左边有一块摆动平台、中间一个**黄色发电机模样的大件**、一个按钮——那么箱子在哪？
- **完整解法**：
  1. 往右走，跳过两块平台，**跳到那个黄色大件上面**；
  2. 站在上面**转身面对你刚进来的那扇门**，会看到**一架梯子，顶上放着一个箱子**；
  3. **举起双臂朝梯子跳过去**——抓住梯子会把它拽倒，箱子随之掉下来；
  4. 把箱子扛上楼梯，放在楼梯顶端；
  5. 下去操作拉杆，**把摆动平台移到放着箱子那一侧、尽量靠近**；
  6. 把箱子放到摆动平台上；
  7. 回到拉杆，**把平台连箱子一起移过缺口，送到另一侧那块带楼梯的平台**；
  8. 自己跳过缺口，上楼梯把箱子拿下来放到按钮上，最后一道门打开。

### 12. 出口区：叉车 + 红色木板 + 脚手架 + 黑色秋千 → `Brute Force`

这是本关最后、也是最容易在门口反复折腾的一段。

- **场景**：一台叉车（forklift 类的机械）和地上一块**红色木板**。
- **完整解法**（TA 系攻略的分步）：
  1. **把红色木板抬起来，尽量往里（往后）放到叉车的货叉上**；
  2. **用拉杆把货叉升起来**；
  3. **跳起抓住木板把自己拉上去**，再从木板跳到脚手架上；
  4. **顺着脚手架一路爬到顶**，那里有一根**黄色横杆**；
  5. **把黄杆抽出来——一个黑色的秋千（swing）会随之垂下来**；
  6. **拿着那根黄杆，往秋千掉下来的位置跳下去**，落地时会把下面的玻璃砸碎；
  7. 在下面这个坑里**扳动拉杆，出口闸门打开**；
  8. **爬出坑，面向出口门，跳起来抓住那个黑色秋千**；
  9. **前后荡起来积累摆幅，觉得够了就松手，把自己甩出出口** —— 下落中解锁 `Brute Force`（官方描述："Complete 'Demolition'"），进入下一关 Castle。

> **更正**：早先版本把这一段写成"借助货叉上搭着的红色木板作为斜坡爬到最高平台 → 在平台上拿黄杆朝脚下的玻璃地板砸下去 → 走到最后的拉杆前扳动，闸门被顶起，从门下钻过去出关"。按 TA 系攻略，正确顺序里**黄杆的作用是放下秋千**（人是抱着杆一起跳下去顺带砸碎玻璃的），而**出口是靠荡那个黑色秋千把自己甩出去的，不是从门底下钻过去**。
>
> 这一段和"卡在出口门前折腾两分钟"的情况高度对应——**卡住的人通常是没注意到脚手架顶上那根黄杆、也没注意到抽掉它之后头顶多了一个可以荡的秋千。** 给方向提示时往"出口门上方/横梁方向"指，是对的。

> **关于"最后那根拉杆会断"**：Steam 讨论区 2025 年 8 月的帖子 "Broken lever in demolition"，楼主说自己砸碎玻璃地板后去扳拉杆，**杆直接崩断了，门也没开**，最后是**翻过那道还关着的门**才通关的。跟帖里的说法：
> - "yeah the levers supposed to snap but i forgot what happens"
> - "the lever is design to snap off"（拉杆本来就设计成会断的）
> - "i think the door not opening is a bug though"（不过门不开我觉得是 bug）
>
> **更正**：早先版本写的是"拉杆断掉的同时闸门已经被顶到了足够钻过的缝隙，直接从下方钻/爬过去正常出关即可"。**这个说法在帖子里找不到依据**——楼主的实际遭遇是门根本没开。**能确认的只有"拉杆断掉是设计好的"；"断了门就一定开"是没有来源的推断。** 真遇到门没开，翻过去是社区实际用过的办法。

---

## 本关能拿到的成就

| 成就 | 官方英文描述 |
|---|---|
| `Brute Force` | Complete "Demolition" |
| `Wrong direction` | Use the window on your left instead of smashing the wall in "Demolition" |
| `Surprise! (Avalanche!)` | Unleash the boulder gate in "Demolition" |
| `Primal` | Break 4 walls without using any gadgets in "Demolition" |

另外 `Convertible ride`（在垃圾桶里开出 50 米）在这关也能刷——isaac 的指南指出 **Train 和 Demolition 两关都有垃圾桶**。

---

## 隐藏语音彩蛋

**"It was an accident!"**（这是个意外！）

Steam 指南《Hidden Messages》给的触发条件：

> 走到关卡里的某栋建筑，进去；**建筑内部的阳台上有一个板条箱（crate）**，拿起它，**用它把这栋建筑里所有的玻璃全部砸碎**，砸完就会听到这句台词。

Steam 讨论区里另一位玩家的独立描述可以互相印证："i managed to find one where i had to smash all the window's in a room in the Demolition level and i would hear a guy say ''it was an accident!''"。还有一位西班牙语玩家的说法（经翻译）是"在火车旁边那栋房子里打碎所有的水晶（玻璃），他会说一句话"。**三处描述都指向"砸光某栋建筑里的全部玻璃"这一个条件。**

---

## 新手常见卡点

- **不知道门上的木板能徒手拆**。开局第一个障碍，容易被误认为是需要钥匙的锁。
- **吊斗荡不起来**。只往一个方向推杆，摆幅很快衰减；不知道"到最高点立刻反推"这个节奏，就永远够不到左边那扇窗。
- **不小心用错工具破墙毁掉 Primal**。用吊斗、铁球或货箱砸过墙就得重开关卡。
- **抽出来的黄杆被随手扔掉**。第 6 点那根杆是用来压住拉杆保持门开的，扔了门就重新关上，得回头再抽一根。
- **铁球推不动**。TA 系攻略自己都说这一步"有点难"，要换姿势试。
- **摆动平台没停稳就跳**，容易连人带箱子掉进缺口。
- **梯子上的箱子没发现**。第 11 点那个箱子在梯子顶上，必须站到黄色大件上回头看才能看到。
- **出口那段卡最久**。叉车、红木板、脚手架、黄杆、秋千是一条五步链，中间任何一环没想到都会在出口门前反复打转。**最容易漏的是"脚手架顶那根黄杆抽掉后会放下一个秋千"这一步。**
- **误把拉杆折断当成卡关**。杆断是正常的；门没开的话翻过去。

---

## 冷知识

- **这关允许明显的"抢跑"（sequence break）**：TA 系攻略作者自己在 `Wrong direction` 那一步写道，速通时可以从那栋楼的另一侧直接走出去，跳过大约半张图的内容。
- 官方成就里专门为"不按设计走"设了两条（`Wrong direction` 走窗户、`Primal` 不用机械），说明绕路和取巧是被官方认可的玩法。
- 结尾那根"扳一下就断"的拉杆在社区里被讨论过很多年，普遍认为是刻意做出来的效果而不是 bug——但**"断了之后门开没开"这件事，玩家的实际体验并不一致**。
