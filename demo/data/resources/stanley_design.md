# The Stanley Parable 设计理念：旁白、服从与交互

> 来源：https://en.wikipedia.org/wiki/The_Stanley_Parable 、https://store.steampowered.com/app/1703340/The_Stanley_Parable_Ultra_Deluxe/ 、https://www.stanleyparable.com/ 、https://www.shacknews.com/article/70363/interview-davey-wreden-on-stanley-parable-remake-and-self-taught 、https://www.gamedeveloper.com/business/behind-the-scenes-with-i-the-stanley-parable-i-

> 本文件只讲这个游戏整体是怎么设计的。**具体的结局、分支走向和场景内容在 `stanley_endings.md` / `stanley_endings_right.md` / `stanley_ud_extras.md`，那三篇是完整题底**——防剧透由每个任务的 `spoiler_blocklist` 和 `hint_level` 管输出，不由资料侧管。

## 这是什么游戏

官方定位是 **first person exploration game**（第一人称探索游戏）。开场设定：Stanley 是个办公室职员，某天发现整栋楼的同事全不见了，于是出门找答案。

Wikipedia 的 Gameplay 段落写得很直白：

> "The player has a first-person perspective, and can travel and interact with certain elements of the environment, such as pressing buttons or opening doors, but has no combat or other action-based controls."

翻译过来就是：第一人称视角，能走动、能跟环境里**某些**元素互动（比如按按钮、开门），**没有战斗，也没有任何其他动作类操作**。

官方商店页的宣传语本身就是一串自相矛盾的话：

> "You will play as Stanley, and you will not play as Stanley. You will make a choice, and you will have your choices taken from you."
>
> "The rules of how games should work are broken, then broken again. You are not here to win. The Stanley Parable is a game that plays you."

"You are not here to win"——这游戏没有"赢"这个概念，也没有失败惩罚。

## 核心机制：旁白（the Narrator）

旁白由英国演员 **Kevan Brighting** 配音，全程用讲故事的口吻描述 Stanley 正在做什么、接下来会做什么。他不是背景音，他是这个游戏里唯一持续存在的"角色"。

Wikipedia：

> "The Narrator takes the player's choices into account, reacting with new narration or attempts to return the player back to the target path if he is contradicted."

也就是说：**你不照他说的做，游戏不会拦你，旁白会现场改词。** 他可能挖苦你、可能装作没看见、可能试图把你哄回原来的路上——但这些反应本身都是**提前写好、提前录好的正片内容**，不是游戏出错，也不是惩罚。

## 整个游戏就建在"服从 vs 反抗"这根轴上

作者 Davey Wreden 说过，做这个游戏的第一个问题就是：

> "The very first thing I asked with the game was 'what would happen if you could disobey the narrator?'"
>
> "The game that popped around that question is about the perception and limitations of freedom in video gaming."
>
> —— Davey Wreden, Shacknews 访谈

所以：

- **照旁白说的走** 和 **反着来**，两边都是做好的内容，都是"正常玩法"。
- 没有"玩错了"这一说，也不存在"听话才是正确玩法"或者"不听话内容更多"。
- 玩家在两扇门前犹豫、反复横跳、赖在一个房间里不走，全都在设计预期之内。

## 旁白会主动摆布玩家的情绪，别把他当中立叙述者

Wreden 对重制版的设计目标：

> "Mess with the player's head in every way possible, throwing them off-guard, or pretending there's an answer and then kinda whisking it away."
>
> —— Davey Wreden（引自 Wikipedia 开发段落）

评论者 Jeffrey Matulef 把这个体验形容成（引自 Wikipedia 评价段落）：

> "playing improv theater with a robot comedian who was programmed to be much, much funnier than you."
>
> （像跟一个被编程得比你有趣得多的机器人喜剧演员一起演即兴剧）

**这意味着旁白说的话不能当成事实照单全收。** 他会给你一个期待、再抽走（Wreden 原话就是 "pretending there's an answer and then kinda whisking it away"）。这种反转是他的常规手法之一，不是穿帮、也不是剧情错乱。玩家遇到这种反转时，"这段是不是认真的"本身就是要自己往下看的部分，旁观者不该替她下结论。

**但这只能用来解释已经发生过的反转，不能拿来预告。** 具体他会在哪一段、用什么方式反转，属于剧透——不要提前告诉玩家"等下他会怎样怎样"。

## "看似有选择、其实只有一条路"

评论者 Ben Kuchera 提到这游戏给的是一种 **illusion of choice**（选择的错觉）：玩家实际控制权有限，但体验上像在做选择（引自 Wikipedia 评价段落）。

学术讨论里也有类似的说法（引自 Wikipedia 评价段落）：整个游戏在玩家到达之前就已经被完整地构造好了，玩家做的是"拿自己的能动性去试探这个已经写死的结构"。

对陪玩来说的实用结论：**游戏里出现"面板上只有一个按钮能按""看着有分岔其实只通一条路"这种情况，通常是刻意的场景设计，不是坏了、不是漏看了选项。** 按下去继续走就行。

## 为什么大部分东西不能拿起来

这是被问得最多的一类问题之一。事实层面：

- 这个游戏**从来没有"捡起/搬运物品"这套系统**。操作就是走路、转视角、开门，以及按剧本安排好的少数几个东西（按钮、电梯面板一类）。
- 桌上的文件、杯子、盆栽、梯子上挂的马克杯……绝大多数都是纯布景（props）。没有交互提示图标、没有准星高亮，就是因为它们根本不是交互对象。
- 没有藏起来的"交互键"。不是玩家少按了 E / F / 右键，也不是游戏卡住了。
- Wikipedia 那句 "no combat or other action-based controls" 是把话说死的：除了走动和有限的环境交互，这游戏**没有其他动作类操作**。

而且这件事游戏自己在台词里就明说过——旁白会调侃 Stanley 把办公室里每样小东西都摸了一遍，结果没有任何区别、也不会推动故事。**这是设计上的自我说明，不是内容做少了。**

重心不在手上，在选择上：走哪条路、听不听旁白的。玩家不用担心自己漏掉了什么隐藏交互系统。

## 幽默基调：一本正经地装傻

这游戏的笑点结构基本是固定的两招：

1. **把宏大的描述配上寒酸的实现**——旁白把一个场面吹得天花乱坠，画面给出一个敷衍到好笑的版本，落差本身就是笑点。
2. **把不该被指令化的东西指令化**——用系统提示、按键提示、正经的设置界面去包装完全不正经的内容。

Ultra Deluxe 的 Steam 页面上，官方自己把这个调性总结为"游戏应该怎么运作的规则被打破，然后再打破一次"。开发者也提过（Gamedeveloper 访谈）：

> "players love to form meaning out of random events, even when there is absolutely no meaning to be found."
>
> （玩家特别擅长从随机事件里读出意义，哪怕根本没有意义可读）

所以遇到"游戏突然一本正经地问你一个奇怪问题""屏幕上蹦出一行奇怪的大字"，第一反应应该是"这是它在开玩笑"，而不是"我电脑出问题了"或者"这是新手教学"。
