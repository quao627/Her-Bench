# Human: Fall Flat 游戏背景

> 来源：
> - https://store.steampowered.com/app/477160/Human_Fall_Flat/ （官方 Steam 商店页；正文经 store.steampowered.com/api/appdetails?appids=477160 取原始英文）
> - https://store.steampowered.com/appreviews/477160?json=1 （Steam 官方评测统计接口，数据为本次核实时的实时快照）
> - https://steamcommunity.com/stats/477160/achievements/ （Steam 全球成就页，151 条成就）
> - https://en.wikipedia.org/wiki/Human:_Fall_Flat （开发史、销量、媒体评分、续作）
> - https://humanfallflat.fandom.com/wiki/Human:_Fall_Flat 、/Human_Fall_Flat_2 、/No_Brakes_Games 、/Curve_Games 、/Devolver_Digital 、/Soundtrack 、/Skins （fandom wiki，走 api.php 取 wikitext）
> - https://www.speedrun.com/api/v1/games/hff （speedrun.com 官方 API：关卡表、分类、子分类）
> - https://www.speedrun.com/api/v1/games/hffce （speedrun.com Category Extensions 板块）

---

## 开发商与发行

开发者是 **Tomas Sakalauskas**，立陶宛人，2012 年从 IT 行业转行做游戏。他最初做手游，中途钱烧完了，加上自己对当时手游普遍的 freemium 模式有伦理上的顾虑，于是转向 PC。他把 Human: Fall Flat 称作自己 "last shot at gaming"（在游戏行业的最后一搏）。他一个人担了制作人、导演、编剧三个身份，连原声音乐也是他自己作曲的（原声带 2017 年 5 月 8 日发行）。工作室名叫 **No Brakes Games**，引擎是 Unity。

**发行商**：Curve。要注意这家公司改过名——Wikipedia 记的是发行时的 **Curve Digital**，而 fandom wiki 和现在的 Steam 商店页写的都是 **Curve Games**（2021 年更名后的名字）。两个名字指同一家公司。手机版是另一套班底：由 Codeglue 移植、505 Games 发行。

游戏有两个有意思的起源细节（来源：Wikipedia 引 GamesIndustry.biz 和开发者访谈）：

- 它最早是给 Intel 的 RealSense 体感摄像头做的原型，后来 Sakalauskas 发现用传统手柄/键鼠反而更好玩，就把体感那套扔了。
- 他本来想做一个像 Limbo 或 Portal 那样谜题严丝合缝的游戏，结果拿自己儿子当测试员时发现"他想尽办法不去解谜"，只顾着玩物理引擎。这件事直接改变了设计方向——他把谜题刻意做成 **"not really watertight"（不那么密不透风）**，允许玩家用开发者没设计过的方式过关。**"每个谜题有多种解法"是官方明确的设计目标，不是玩家的错觉。**
- 游戏先以原型形式放在 itch.io 上，一批主播开始玩之后才有了九个月后的 Steam 版。

## 发行平台与时间线

| 平台 | 日期 |
|---|---|
| Windows / macOS / Linux | 2016-07-22 |
| PlayStation 4 | 2017-05-09 |
| Xbox One | 2017-05-12 |
| Nintendo Switch | 2017-12-07 |
| iOS / Android | 2019-06-26 |
| Google Stadia | 2020-10-01 |
| Xbox Series X/S | 2021-05-28 |
| PlayStation 5 | 2021-06-24 |
| Nintendo Switch 2 | 2026-03-19 |

## 玩法定位

官方 Steam 一句话简介：*"Human Fall Flat is a hilarious, light-hearted platformer set in floating dreamscapes that can be played solo or with up to 8 players online. Free new levels keep its vibrant community rewarded."*（一款设定在漂浮梦境里的搞笑轻松平台游戏，可单人也可最多 8 人联机；持续免费更新的新关卡回馈社区。）

- Wikipedia 的类型标注是 puzzle-platform（解谜平台）。
- 玩家操控一具全物理模拟的软体人偶（社区通称 Bob），两只手可以**分别独立**抓取和攀爬，走路摇摇晃晃，所有动作交给物理引擎。
- 关卡是一个个梦境：别墅、火车站、工地、城堡、水岸峡湾、发电厂、阿兹特克神庙、雪山、暗夜……
- 官方商店页的原话就把"多解法"写进了卖点："Multiple routes through each level, and perfectly playful puzzles ensure exploration and ingenuity are rewarded."
- **联机**：2017 年 10 月的更新加入了最多 8 人在线（也支持 LAN），Sakalauskas 一开始认为全物理引擎做联机不可能，后来靠 Nvidia 的技术方案解决了。Steam 上还标着 Shared/Split Screen Co-op（本地分屏）和 Remote Play Together。
- **成就**：Steam 上一共 **151 个**。
- **创意工坊**：Steam 商店页现在写的是 "explore more than 5,000 unofficial levels from our community creators"（5000 张以上玩家自制关卡），工坊配合 Unity 使用，玩家可以自己做关卡、大厅和皮肤。
- **皮肤**：fandom wiki 列了 Doctor DF、Flight Attendant、Fortune Teller、Jester、Judge、Painter、Professor、Rockstar、Tailor、Wrestler 等。

## 为何以"滑稽失败"闻名

这套故意做得不听使唤的操作是笑点的来源：小人经常抓空、摔下高台、把队友拽下悬崖。**失败本身比成功更好笑**——摔落在这个游戏里几乎没有惩罚（唯一的例外是水会淹死人），所以玩家可以毫无心理负担地一直摔。

IGN 的 Dan Stapleton 给了 7.9/10，Wikipedia 对他评测的概括是：**他推荐"看"这个游戏而不是"玩"它**，理由正是这套滑稽的操作、幽默的动画和角色自定义。这句评价某种程度上预言了它后来的命运——官方商店页现在直接写着："Streamers and YouTubers flock to Human Fall Flat for its unique, hilarious gameplay. Fans have watched these videos more than 3 Billion times!"（主播和 YouTuber 蜂拥而至，相关视频的观看量超过 30 亿次。）

## 口碑与销量

**媒体评价是分化的，玩家口碑很好。**

- Metacritic：PC 70/100，PS4 67/100，Xbox One 73/100，Switch 65/100，整体判定为 "mixed or average"（褒贬不一）。
- OpenCritic：只有 **39%** 的评论者推荐。
- 具体评分：IGN 7.9/10、Destructoid 8/10（称赞谜题可重复游玩、每个谜题都有多种解法）、Hardcore Gamer 3.5/5、Nintendo Life 7/10、Nintendo World Report 8/10、Pocket Gamer 3.5/5、Push Square 6/10。

**Steam 评测（本次核实时的实时数据）**：

- 全语言：**226,404 条评测，214,240 条好评（约 94.6%），总评标签是 "Very Positive"（特别好评）**。
- 只筛英文：**44,601 条评测，42,412 条好评（约 95.1%），标签是 "Overwhelmingly Positive"（好评如潮）**。
- 注意这两个不要混：**"好评如潮" 是英文筛选下的标签，全站总评是"特别好评"。** 评测总数也是二十多万条量级，不是几万条。

**销量（Wikipedia 汇总的历年公开数字）**：

| 时间 | 累计销量 |
|---|---|
| 2018-02 | 200 万 |
| 2018-06 | 400 万 |
| 2021-02 | 2500 万 |
| 2023-03 | 4000 万 |
| 2025-01 | 5500 万 |
| 2025-12 | **5800 万** |

Wikipedia 的表述是 "making it one of the best selling video games of all-time"（使它成为史上最畅销的游戏之一）。2020 年在中国的走红（经 XD 和 505 Games 发行，叠加疫情期间的联机需求）是 2021 年那波增长的主要推手之一。

> **一个容易搞混的数字**：官方 Steam 商店页现在写的是 "Join 60 million **players** across all formats"（全平台 6000 万**玩家**），这是玩家数不是销量。销量的口径是 5800 万份（2025 年 12 月）。两个数字不要互相替换。

## 十周年

官方商店页现在挂着 10 周年纪念关卡（"10TH ANNIVERSARY"），内容是把 Mansion、Mountain、Demolition、Castle、Water、Powerplant、Aztec 这些经典关卡的名场面重做一遍，里面还藏了开发历程的采访视频。speedrun.com 的关卡表里也已经收录了 "10th Anniversary" 这张图。

## 续作

**Human: Fall Flat 2** 于 2023 年 6 月在 Devolver Direct 上公布，仍由 No Brakes Games 开发，但**发行商换成了 Devolver Digital**（不再是 Curve）。计划登陆 Windows 和 Nintendo Switch 2。官方简介："Team up and let your creativity run wild in Human Fall Flat 2, the outrageous new sequel to the much-loved capers of everyone's favourite physics-based human friends."

## 速通社区

speedrun.com 的 Human Fall Flat 板块（`speedrun.com/hff`）目前收录 **34 张关卡**。分类结构：

- **全流程分类**：Any%、Checkpoint%、Aztec%、Dark%、Steam%，以及 Checkpoint Aztec% / Checkpoint Dark% / Checkpoint Steam%、Aztec% Team Fling，还有按旧版本单独计的 Any% 1.0 / 0.3.1 / 0.3.0。
- **单关分类**：按平台分成 PC / Console / Mobile 三档。
- **子分类**：Any% 下面按人数和限制细分成 Solo、Coop 2p、Coop 3p+，每一档还再分 Glitchless（禁用 bug）、Pinch、No Extended Climb（禁用"延长攀爬"技巧）等变体。榜单还要求登记游戏版本号和 Water 关的出生点版本（New / Old）。
- **Category Extensions 板块**（`speedrun.com/hffce`）收录整活向分类：**Achievement%、Jumpless%（全程不跳）、One Arm%（只用一只手）、Voiceline%（收集语音彩蛋）、No Checkpoint%、To The Top%、Checkpoint% Reversed**。

因为全物理引擎会产生大量甩飞、越点、爬墙抄近道的技巧，这个游戏的速通观赏性很强；反过来说，榜单专门设了 Glitchless 和 No Extended Climb 这类子分类，也说明"用物理漏洞抄近路"在这个游戏里普遍到需要单独隔离出来。

> **未证实**：早先版本写的关注者人数、提交成绩的玩家数、全流程/单关记录条数（约 1100 / 800 / 2100 / 3000）本次没能通过 speedrun.com 的公开 API 核对到，已从正文删掉。上面列出的关卡数和分类结构都是从 API 直接取的。
