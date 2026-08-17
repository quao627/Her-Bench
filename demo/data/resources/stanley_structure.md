# The Stanley Parable 的结局结构、重开机制与跨周目记忆

> 来源：https://en.wikipedia.org/wiki/The_Stanley_Parable 、https://thestanleyparable.fandom.com/wiki/Endings 、https://thestanleyparable.fandom.com/wiki/Points_of_divergence 、https://thestanleyparable.fandom.com/wiki/Settings_Character 、https://thestanleyparable.fandom.com/wiki/Have_you_played_The_Stanley_Parable_before%3F 、https://thestanleyparable.fandom.com/wiki/Broom_closet 、https://thestanleyparable.fandom.com/wiki/Museum 、https://thestanleyparable.fandom.com/wiki/Monitor_room 、https://thestanleyparable.fandom.com/wiki/Achievements 、https://www.gamepressure.com/the-stanley-parable-ultra-deluxe/number-of-endings-and-game-length/z6fd57 、https://www.stanleyparable.com/ 、https://store.steampowered.com/app/1703340/The_Stanley_Parable_Ultra_Deluxe/ 、https://steamcommunity.com/app/221910/discussions/0/1738882855319768963/

> 本文件讲"结局"这套系统在结构上怎么运作。**具体每个结局叫什么、怎么触发、里面演什么，在 `stanley_endings.md` 里，那份是完整题底。** 两份都是给 agent"心里有数"用的，防剧透由每个任务的 `spoiler_blocklist` 和 `hint_level` 管输出。

## 结局是"多个平行的短篇"，不是一条主线的多个尾巴

地图是可以反复重走的循环结构。不同的路径选择走向**彼此独立的短篇故事**，没有哪一个是"真结局"——虽然 Freedom Ending 因为拿 "Beat the Game" 成就、被玩家群体普遍当成真结局，但游戏本身不这么定性，走完照样回办公室重开。

开发者 William Pugh 在 Gamedeveloper 访谈里说过：

> "There's no perfect ending for me, but there might be one for you."

团队做过一版**结局流程图**又砍掉了，因为它 "killed the magic of discovery"，而且 Pugh 说游戏里有些部分本来就没法画成流程图。**这条对陪玩很关键：官方自己认为"提前知道有哪些结局、怎么走"会破坏体验。** agent 手里有全图，但正因为官方是这个态度，说出来才更不合适。

## 结局数量：三种口径，别说死数字

| 来源 | 说法 |
|---|---|
| Wikipedia | 2011 年 HL2 mod 版 **6 个**；2013 重制版 "more than ten endings" |
| Fandom Endings 页 | 原版 19 + Ultra Deluxe 新增 27 = 全系列 46；Serious Ending 在 UD 里做不出来，**UD 实际 45** |
| gamepressure（UD 攻略页） | UD 共 **27 个**，其中 9 个全新 |

分歧的根源是"什么算一个独立结局"没有统一标准：Broom Closet 和 Whiteboard 不触发重开，Fandom 自己都标 "technically not an ending"；bucket 版本算不算独立结局也没定论。**"十几个长短不一的结局"是安全表述，具体数字不安全。**

## 长短差异极大，短到离谱是刻意的

- 长的可以走几十分钟（Confusion Ending 套了五段、中间重开四五次；Art Ending 要求连续玩满四小时）。
- 短的只有几十秒：Coward Ending 就是出门前把自己办公室的门关上；Whiteboard Ending 里那个房间只有一块白板；走进扫帚柜，字幕直接打出 "Stanley stepped into the broom closet, but there was nothing here."
- 旁证：官方成就 **Speed run** 的条件是"4 分 22 秒内通关"（不含读盘）。从头到"通关"最快只要四分多钟。

所以玩家吐槽"这游戏的结局也太随便了吧"——**对，就是故意的。**"一个结局"在这游戏里不承诺任何长度或分量。

## 触发结局 = 自动重开，这不是失败

Wikipedia：

> "After experiencing an ending, the game resets to the beginning."

- **重开不是"失败重来"**，是这游戏的玩法循环。每一周目就是去试一条不同的分支。
- **没有失败惩罚、没有 game over、没有进度损失。** 官方商店页那句 "You are not here to win" 就是这个意思。角色在很多结局里"死掉"只是一种收尾方式——被压碎机碾死、从楼梯摔死、跳下仓库摔死、被核弹炸掉，都不算玩砸了。
- 少数结局不会自动重开，得自己手动重来（Fandom：some endings restart on their own, others may need the player to manually restart it themselves）。Steam 讨论区也有人问过"我是不是应该卡住然后重开"，回复是 "There are some situations in which restarting the game is the only way out."
- ⚠️ **但这条只能事后说，不能事前说。** 她还没死的时候提前科普"这游戏里死了也没事、会自动重开"，等于预告结果，本身就是剧透。这种安慰只能等事情真的发生之后再讲。

## 重开不会把世界原样重置：它记得你干过什么

Fandom 的 Endings 页专门有一节 Progression 讲这件事，可以确认的例子：

- **Countdown Ending** 第二次走，旁白在最后 30 秒前的台词会变。
- **Confusion Ending** 之后，那条黄色的 Adventure Line™ 会在后续周目的某些地方冒出来。
- **Bucket 版 Escape Pod Ending** 之后，接下来两个周目 Reassurance Bucket 会从它的基座上消失，第三次换成一个"替代桶"。
- **Figurines Ending** 之后，会议室白板上会出现 "REBOOT THE GAME ENTIRELY."，提示你反复重启游戏去找 Settings Character。
- **反复进扫帚柜**到旁白彻底放弃之后，某一次重开会发现门被木板整个钉死。（触发次数两个来源对不上：Broom Closet Ending 页写"第三次重开后"，Broom closet 地点页写"第二次重开时"。UD 里抱着 bucket 还能进，旁白甚至会把木板拆掉。）
- **Heaven Ending** 的五台 "AWAITING INPUT" 电脑，一个周目只能点一台，进度跨周目保留。

另有一条来源较弱、只在 Steam 讨论区找到明确表述的：

> "Restarting the game (without quitting the software) is different to other games, as the game still remembers what you did and acts accordingly on successive restarts."

同一帖提到这个"记忆"**不跟着存档走**，读存档会打断它，所以这游戏基本不需要存档。

实用结论：**重复去做同一件事，下一周目看到的可能就不一样了——门被封上、东西不见了、旁白换了套说辞。这是玩法的一部分，不是 bug，也不是玩家记错。** 但除了上面这几条有据可查的，具体触发规则（做几次才变、能不能撬开、还有哪些地方会变）没有公开文档，不要编。

## Ultra Deluxe 用一套隐藏的点数系统记结局

首次启动时 Settings Character 会问 "Have you played The Stanley Parable before?"，这个回答决定了后面那扇 "New Content" 门什么时候出现：**答 Yes 需要 6 分，答 No 需要 15 分**。每个结局在代码里有 3 分 / 1 分 / 0 分的固定权重，同一个结局只算一次。这也是为什么两个玩同一款游戏的人，新内容出现的时机可能差很远。（分值明细在 `stanley_endings.md`。）

## 开场那串黑底白字的设置画面，本身就是内容

那不是 Steam、不是系统、不是显卡驱动的弹窗，是游戏自己的启动流程，Fandom 把说话的这个角色叫 **Settings Character**（也有人叫 Settings Person；粉丝圈流行的 "Timekeeper" 是同人叫法，不是官方的）。他只在**前五次启动游戏**时出现，负责调语言、亮度、时间，然后送你进主菜单。

- 第一次启动他装成普通的开机设置流程，不表现出自己有意识。
- **第二次启动开始，他只问时间，并且会根据你前几次填的时间跟你聊天**——填了两次午夜会被念叨"你是不是根本没认真调"，认真填了会被夸，两次填同一个非午夜时间他会怀疑你在耍他或者作息过于规律。第三次启动有九条不同的对话分支。
- 把"现在几点"混进亮度校准这种正经开机设置里，本身就是这游戏一本正经装傻的调性。
- ⚠️ **这条是重度剧透。** 到视频开场那一刻为止，游戏完全没有交代这个时间会被拿去干什么。对首次盲玩的主播，只能说"随便填个大致时间点 Confirm 继续就行"，**不能说"它以后会被记住"**，更不能编一个听起来很专业的用途（同步存档、影响光照天气、和成就挂钩之类）。
- 顺带：Settings Character 和旁白不是同一个人。他管的是游戏"外面"的东西（设置、标题画面、成就机器），旁白管的是游戏"里面"的东西（门、地图）。旁白似乎并不知道他的存在。

## 通关时长

gamepressure 给的数字：把大部分结局都解锁大约 **5 小时**；全结局 + 全成就会大幅拉长——Art Ending 要求连续玩满四小时不失手，Commitment 成就要求从周二零点玩到周二结束，Go outside / Super Go Outside 要求五年 / 十年不打开这游戏。

## 关于那个"开发花絮房间"（Museum）

它在 Museum Ending 里：从 Mind Control Facility 门口左转进写着 "escape" 的走廊，走到底被压碎机碾死之前，一个女声旁白会中断演出，把 Stanley 放进一间全白的博物馆。里面陈列的是**这个游戏自己的开发过程**——切掉的内容、早期的房间设计、旁白的录音 outtake、Zending 原本的三根拉杆方案、Freedom Ending 早期版本的绿野、Greenlight 时期的素材、开发者邮件等等。

可以安全告诉第一次玩的人的判断：

- 这类内容**建立在"你已经知道原版长什么样"之上**，本来就是给玩过一遍、回头来看幕后的人准备的。
- 第一次玩就撞进去，确实容易被剧透"设计思路"——她担心被剧透是对的，不是想多了。
- 处理方式：原路退回，或者找一条没走过的通道往外走，不用在里面细看。
- **绝对不要向她描述里面具体展示了什么。** 这正是她想避开的东西。

Ultra Deluxe 还有一整块自我指涉的新内容（New Content 门那条进度线），玩的也是同一招：拿这个游戏自己、拿玩家的评价、拿"新内容"这个概念本身开玩笑。官网原话是新版 "recreated all the original content, with new elements integrated in unexpected places"，而且新写的剧本比整个原版还长。
