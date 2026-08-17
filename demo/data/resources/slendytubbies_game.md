# Slendytubbies（2012）基本机制与操作

> 来源：https://zeoworks.com/games/slendytubbies.html 、https://slendytubbies.fandom.com/wiki/Slendytubbies 、https://slendytubbies.fandom.com/wiki/Updates_(S1) 、https://slendytubbies.fandom.com/wiki/Collect 、https://slendytubbies.fandom.com/wiki/Multiplayer 、https://slendytubbies.fandom.com/wiki/Tubby_Custard 、https://zeoworksslendytubbies.fandom.com/wiki/Slendytubbies 、https://archive.org/details/slendytubbies-v-1-beta 、https://juanarcades.itch.io/slendytubbies-v2-web-player-edition

## 是什么游戏

Slendytubbies 是 ZeoWorks（作者 Sean Toman）用 Unity 做的独立恐怖小游戏，2012 年 12 月 12 日首发。开发者自己在官网上的原话是："Slendytubbies is a re-make of the popular indie game 'Slender', with a massive twist"——就是把《Slender: The Eight Pages》的玩法原样搬过来，换成《天线宝宝》（Teletubbies）的皮。原版收集 8 张纸，这里改成收集 10 碗 Tubby Custard。

它是整个 Slendytubbies 系列的第一作，wiki 上常写作 S1 / ST1。注意别跟续作 **Slendytubbies II**（2014 年 5 月发行的另一款游戏）搞混——第一作自己的大版本更新叫 "V2.0 BETA"，名字很像但完全是两回事。

平台是 Windows / Mac 下载版，**同时官方也提供过浏览器直玩版**：ZeoWorks 官网的 Slendytubbies 页面上，除了 "Download (WinRAR required)" 的 32/64 位和 MAC OS X 链接之外，还单独有一个红字 "PLAY NOW  *No download*" 的入口。后来抢救这个网页版的 itch.io 页面说得很明确——*"This web port is not a recreation or a fangame. This is the **official web version** made by ZeoWorks."*——技术上走的是当年的 **Unity Web Player** 插件，随着这个插件被现代浏览器淘汰、加上托管站点被黑，官方网页版就打不开了（官网上那批 adf.ly 短链现在也全失效）。

也就是说：**"在浏览器里玩的 Slendytubbies" 和下载版是同一个游戏**，机制、操作、内容都一样，不是什么阉割版或者别人做的小游戏。

## 核心目标

官网 Singleplayer 一节的原文：*"The objective is to collect all 10 teletubby custards without being caught by the slendertubby."*

- 地图上散布 **10 个 Tubby Custard**（蓝色小碗装的粉色糊状物），全部捡到就算通关。
- 只有一张地图（Teletubby Land / Main Land），可以选 Day / Dusk / Night 三个时段。**三个时段只有视觉差别，玩法完全一样**，wiki 上给的注解是 Day = Scary、Dusk = Scarier、Night = Scariest。
- 被反派抓到就直接结束，进度不保留，得从头再来。
- 捡到 custard 时会播一段音效（这是 V2.0 BETA 才加的，见下面版本一节）。

> **关于 10 这个数字**：ZeoWorks 官网、两个 fandom wiki、Collect 模式条目全都写 10，游戏内 UI 也是 `N/10`，这条很扎实。网上有二手博客写成"12 个"，那是错的，别跟着写。

## 开局的 intermission

进入任一时段后，玩家先进入一个 **intermission（准备段）**：这时候地图大部分是封锁的，只能在出生点附近很小一块地方转悠，**按 E 才正式开始游戏**，什么时候按由玩家自己决定。这个设计在续作里被砍掉了。

（顺带：官网 V2.0 BETA 更新列表里写的 "In-game Lobby/start game feature" 指的就是这套东西。）

## 操作（照抄 ZeoWorks 官网的 Controls 表）

| 操作 | 按键 |
|---|---|
| 前后左右移动 | W/A/S/D 或方向键 |
| 视角 | 移动鼠标 |
| Sprint（冲刺） | Left Shift |
| Crouch（蹲下） | C |
| **手电筒开关** | **F 或鼠标右键** |
| Jump | Space |
| Map（小地图） | 按住 M |
| Hide/Show Cursor | G / H（官网备注：联机时无效） |
| Toggle chat | T |

fandom wiki 的操作表跟官网一致，另外补了一条 **Open Menu — E**（游戏内菜单，Character Customization 就在菜单左下角）。

两点值得注意：

1. **手电筒不是解锁物，也不是地图上捡的道具**。它从一开始就在，右键（或 F）随时开关。官方和 wiki 的操作表里都是并列的两个键位，没有任何"需要先找到手电筒"的说法。游戏本身没有把这个提示打在屏幕上，所以玩家不看说明页的话确实容易一直不知道有这功能。
2. **按住 M 有小地图**。同样是基础功能，不需要解锁。

## 冲刺有没有耐力限制

**未证实。** 官网的 Controls 只写了 "Sprint - Left shift"，两个 wiki 的机制说明里都没有出现过耐力条 / stamina / 体力这类字眼，S1 的更新日志里也从没提过耐力相关的改动。也就是说"能一直按着 Shift 跑"跟现有资料不冲突，但没有任何来源明说过"冲刺无限"，别当成官方设定讲。

## 有没有血量 / 伤害

来源里**完全没有**任何血量、受伤、掉血、减速状态的记载。S1 的失败条件只有一条：被 Tinky Winky 弄死（判定细节见 `slendytubbies_enemy.md`）。地图上的倒树、尸体、Noo-Noo 之类都属于纯氛围/惊吓要素，没有伤害数值。

## 版本演进（Updates (S1)）

| 版本 | 日期 | 关键改动 |
|---|---|---|
| V1.0 | 2012-12-12 | 首发 |
| V1.1 "Fix" | 2012-12-20 | 改进光照；**加入山脉（Mountains）**；**Tinky Winky 开始"每捡一个 custard 就变快一点"**；修复烟雾显示 |
| V2.0 BETA | 2013-01-02 | 降低追击速度；降低尖叫音量；加入捡 custard 音效；加入"反派靠近"音效；CO-OP 改成 Competitive；加入 Character customization；加入游戏内文字聊天；加入 Lobby / start game；修 Versus 跳跃 bug；**加入 Interactive objects（可交互物件）**；增加植被树木；一名玩家死亡不再直接结束整局（除非死的是房主）；加入隐藏光标；加入彩蛋 |
| V2.0 BETA "Fix" | — | 修正版（fandom 记为该作最终标称版本）。trivia 里提到这次修掉了"Tinky Winky 爬不上/飞不上山和树"的问题 |
| V2.5 | 2013-05-03 | 加入同步动画；**移除 VERSUS 模式**。这是最后一版，因为只传了 Game Jolt 没传 MediaFire，被 wiki 归为 lost media |

上面这张表同时来自 fandom 的 Updates (S1) 页和 ZeoWorks 官网首屏的 "So what are you to expect in this Beta?" 列表，两边逐条一致，可信度较高。

**"Interactive objects in-game" 这一条很关键**——地图上会自己倒下来的树就是这次加的，详见 `slendytubbies_map.md`。

## 联机模式

S1 的联机**必须靠 Hamachi 这类虚拟局域网工具或者端口转发**才能连上，官网专门给了两篇教程链接。菜单里只能建房或加入房间，可选 Competitive / Versus 两种模式，外加三个时段之一。

- **Competitive（竞速）**：官网原文 *"Play against your friends and try to collect all the custards before they do! Be warned though, Each player has a slenytubby chasing them."* 也就是各玩各的，谁先集齐 10 个谁赢，**每个玩家头上都挂一只独立的 Tinky Winky**。fandom 的 Multiplayer 页写的是 **up to 4 players**（该页同时指出这个模式经常被误当成合作模式）。V2.0 BETA 之前这个模式叫 CO-OP。
- **Versus（对抗）**：房主扮演 Tinky Winky 去抓人，其他人照常收集 10 个 custard。反派视野被红光点亮，跳跃比玩家高。房主中途退出会随机挑一个玩家接手当怪。**注意：官网页面底部有一条大写警告——"VERSUS MODE SELF-DESTROYED ITSELF WHEN I RENDERED THE GAME, IT WILL NOT WORK! SORRY EVERYONE, FOR NOW; STICK TO COMPETITIVE MODE."** 也就是 V2 BETA 发布时 Versus 是坏的。V2.5 干脆把它删了。

> **人数说法不一**：fandom 的 Multiplayer 页明确写 Competitive "up to 4 players"，但同一个 wiki 的 Slendytubbies 主条目只笼统说 "two or more players"，官网一个数字都没给。**"最多两人"这个说法在任何来源里都找不到依据**，别用。

## 屏幕上的进度播报

游戏里那行第三人称的进度公告（形如 `A Player has collected N/10 custards`）**在所有找到的来源里都没有被记录过**——官网说明页没写，两个 fandom wiki 的机制、UI、模式条目里也都没有这条。

能确认的只有旁证：wiki 的 Slendytubbies 条目提到联机时"有玩家加入会在屏幕左上角弹出一行 *a helpless victim has joined the game*"，说明这游戏确实有一套第三人称口吻的文字播报系统；而 V2.0 BETA 又是把联机、聊天一起加进来的版本。所以"单人模式下沿用了联机的播报措辞"是一个合理推测，**但它是推测，不是有出处的设定**。至于这行字**在什么条件下会重复播报**，来源里同样没有任何说明，不要编触发条件。
