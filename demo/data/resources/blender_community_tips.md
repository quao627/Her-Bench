# Mirror、参考图与版本差异：社区经验补遗

> 来源（视频）：Mirror Modifier for Complete Beginners, Ryan King Art (https://www.youtube.com/watch?v=_YEyik7UQZ8) 、How to Fix Broken Blender Mirror Modifier, Michael Bullo (https://www.youtube.com/watch?v=l6KarXMvA-A) 、2 Ways to Import Character Front, Side, Back Reference Images, Chris' Tutorials (https://www.youtube.com/watch?v=bd0MmTqVuIw) 、How to Use Reference Images in Blender, MrWonderHow (https://www.youtube.com/watch?v=wkTAJS233_c) 、Blender 4.0 - Texture Painting quick start guide, Jamie Dunbar (https://www.youtube.com/watch?v=iwWoXMWzC_c) 、Common Texture Issues and How to Fix Them in Blender, Tosmo (https://www.youtube.com/watch?v=KJ5OgYFqilk)
>
> 来源（社区）：https://blenderartists.org/t/modifier-mirror-help/1599908 、https://blenderartists.org/t/3-3-lts-both-sides-are-one-vertex-group-vertex-weights-mirror-modifier-applied-only-one-group/1491923 、https://blenderartists.org/t/mirror-modifier-is-applied-but-works-as-if-it-is-still-on/1395221 、https://blenderartists.org/t/problem-with-x-mirror-in-pose-mode/651917 、https://blenderartists.org/t/paste-x-flipped-pose-option-seems-to-not-work/1597134 、https://blenderartists.org/t/trying-to-make-asset-symmetrical-causes-clipping-on-one-side/1513118 、https://blenderartists.org/t/how-to-deactivate-mirror-in-text-paint-2-81/1214040 、https://blenderartists.org/t/mirrored-mesh-move-in-opposition-direction-when-tweaking/661849 、https://steamcommunity.com/app/365670/discussions/0/3267935171629636800 、https://steamcommunity.com/app/365670/discussions/0/143388132205062810 、https://steamcommunity.com/app/365670/discussions/0/3192489172314245628 、https://steamcommunity.com/app/365670/discussions/0/3032599335586325234 、https://steamcommunity.com/app/365670/discussions/0/3267935171645768428 、https://steamcommunity.com/app/365670/discussions/0/3051736373897730988 、https://blender.stackexchange.com/questions/124773/blender-2-8-reference-image-disappeared 、https://blender.stackexchange.com/questions/201708/background-image-vs-reference-image-what-are-the-pros-and-cons-of-these-method 、https://blender.stackexchange.com/questions/29259/is-there-colour-picker-in-texture-paint-mode 、https://blenderartists.org/t/reference-image-problem/1520905 、https://projects.blender.org/blender/blender/issues/125583 、https://www.katsbits.com/codex/vertex-painting/ 、https://github.com/Pullusb/reference_to_image_plane

配合 `blender_troubleshooting.md`。**`BA 数字` 指 blenderartists 帖子号，`SE 数字` 指 blender.stackexchange 问题号，`Steam 数字` 指上面那几条 Steam 讨论。**

---

## 一、Mirror 与「两只手一起动」

### Blender 里的「镜像」有五个，成因和解法都不同

| 名字 | 在哪 | 干什么 |
| --- | --- | --- |
| **Mirror 修改器** | Properties → 扳手 → Generate | 实时**生成**另一半几何 |
| **Mesh Symmetry X/Y/Z** | Edit Mode 顶栏（蝴蝶图标） | 编辑网格时左右同步 |
| Sculpt 对称 | Sculpt Mode 顶栏 | 雕刻时左右同步 |
| **Pose Mode X-Axis Mirror** | Armature 属性 | 摆姿势时左右骨骼同步，**依赖骨骼名** |
| Copy / Paste Flipped Pose | Ctrl+C / Ctrl+Shift+V | 一次性镜像粘贴，不是持续同步 |

### 新手真正卡住的地方：它是「生成」另一半，不是「连着」两半

社区里反复出现同一个误解。BA 1599908 楼主的原话最典型：「i turned it off but **the entire other half of my model disappeared???**」关掉修改器另一半就没了，是因为那半边本来就不存在——它是算出来的。同样的困惑在 Steam 上至少还独立出现过两次。

两个教程视频都把同一件事当头号排查点：**它绕的是物体的 origin，不是世界中心**（Michael Bullo：「this orange dot is the origin, and it's the point about which the mirroring occurs」；origin 恰好在物体正中间时镜像完全重叠，看着像「什么都没发生」）。另外，**在 Object Mode 转过/缩放过，镜像轴就不是你以为的那根**，因为修改器用局部轴，修法是 Ctrl+A 把 Rotation Apply 掉（Ryan King Art）。

### 要不要 Apply？社区分两派，而且两派回答的其实是不同的问题

**「先 Apply 再做不对称」是多数派。** 应用方式：修改器右上角下拉 → Apply，或**鼠标悬停在修改器面板上按 Ctrl+A**（Ryan King Art）。Blender 自己也会弹一句警告：「Mirror modifier not applied first results may be unexpected」。

**但少数派拿出了能跑的方案。** Steam 3192489172314245628 里 Stretchyf：「you can leave Mirror Modifier in the stack as well! **All you need is to create empty vertex groups for the other side**（bone.l / bone.r 这样命名）… everything works」，楼主确认可用。BA 1491923（Blender 3.3 LTS）结论一致：「So long as the symmetrical bones have all been added with suffix .r or .l … **The mesh is possible to pose asymmetrically with the mirror modifier still active.**」

**两派其实不矛盾。** 同一个 Stretchyf 在另一帖（Steam 3032599335586325234）划了界线：「You cannot draw different weights on mirrored side when you use Mirror modifier. **Like at all.**」也就是说：**留着 Mirror 不挡「骨骼驱动的不对称摆姿势」（前提是骨名和顶点组配好），但会死死挡住「逐侧编辑」网格、权重和 UV。** 多数派在回答「怎么单独改一侧网格」，提问的人往往在问「怎么只让一只手抬起来」——问题不一样，答案自然打架。

**常被忽略的一条：修改器顺序。** BA 1599908 和 Steam 143388132205062810 都指出 **Mirror 必须排在 Armature 修改器之前**。

### Apply 之后 / 关掉之后的连带问题

- **中缝会留重复顶点。** BA 1513118 楼主的修复记录：中线顶点在 X 轴缩放到 0 对齐 → 应用修改器 → 「removed doubles (**there were 10**)」。Ryan King Art 强调建模时就该开着 **Clipping**（顶点滑到中线自动焊住，拖不开）。
- **应用了却还在镜像？多半是另一个开关。** BA 1395221 就是这一幕：修改器列表已经空了，动一个顶点对侧还跟着动，回复一句点破：**Mesh Symmetry 那个蝴蝶图标 + X/Y/Z 还开着**。楼主回「Don't remember turning it on, and yet」——这开关存在网格上，各绘制/雕刻模式共用。
- **Apply 之后再靠 Edit Mode 的 X Mirror 维持对称只能小修小补**（BA 661849）：「it's only good for tweaking. **The moment you start to cut or add edges to the mesh in anyway, the whole mirror setup will be ruined.**」
- **P → Separate 会把修改器一起复制过去**，新物体上还挂着 Mirror，得手动删掉（Steam 3267935171629636800，楼主自陈「i forgot to apply my mirror mod when i decide to separate it」）。

### 跟贴图 / UV 的冲突（和 troubleshooting 那份的症状 E 是同一件事）

Steam 3267935171645768428：「When you use the mirror modifier, **the UV islands are naturally also mirrored i.e. sitting on top of each other.** If you were to apply the Mirror and then unwrap again, each side would get it's own island so you could have asymetric details.」**但他紧接着提醒**：已经画过贴图再重新 unwrap，「you would eventually mess stuff up」，所以结论是「don't texture paint with mirror modifier because of the UV issues」（Steam 3051736373897730988 的 Pte Jack 说法一致）。同帖 henryfleischer01 给了另一条路并自陈代价：应用后**复制一份材质和贴图**让两半各用一个，「at the expense of not being able to have your changes mirrored」。另有个绕开办法（BA 1214040，未结帖）：直接在 UV 编辑器窗口里画，「it bypasses all the mirror options」。

### 骨骼命名：Pose Mode 镜像失效基本都栽在这

**必须以 `.L` / `.R` 结尾，前半截完全一致，大小写也一致**（BA 651917：「They should be Arm.L and Arm.R. **The first part of the name needs to be identical.**」；BA 1597134：「**Even capital letters must be exactly the same.**」）。从 Mixamo 导入的 `mixamorig:LeftArm` 就是栽在这。**改完骨名还有个坑**：顶点组名字不跟着改，网格就不再跟随骨架了。

> **写给回答问题的人**：以上是「可以怎么做」的清单。**具体某一次是靠 Apply、靠删掉镜像、还是干脆放弃那个动作绕过去，只有当事人自己知道**——没有画面证据就别替他认定。另外值得知道的是：社区自己也拿不出一篇从「对称建模」一路讲到「不对称成品姿势」的完整教程，相关建议散在摆姿势、刷权重、做贴图几个子问题里，这也是各家说法看起来互相矛盾的原因之一。

---

## 二、参考图：`blender_reference_image.md` 之外的几条

- **加之前先切视图。** MrWonderHow 的教程（Blender 5）单拎出这条：先按小键盘 **1** 进正视图，**再** Shift+A → Image → Reference，原话是「**Blender places reference images based on the view you're currently in**」——透视视角下随手加，图就是歪的。没有小键盘就走 View → Viewpoint → Front，或按反引号（`）调出视图饼菜单。
- **「图突然不见了」最反直觉的一条：叠加层被关了。** image empty 属于视口 overlay，SE 124773 被接受的回答（score 9）：「Image empties are part of the viewport's overlays, and you disabled your overlays' display」，还得确认 overlay 菜单里的 **Extras** 也开着。同帖另提两种可能：误入 **Local View**（按 `/` 回去）；Opacity 调成了 0 或 Depth 设得不对。
- **Reference 和 Background 差在哪**（官方手册没解释）——SE 201708 被接受的回答：**两者是同一种物体，只是默认设置不同**，「by default **Background will only be seen in orthographic view and it is set to have its back transparent**」；另一条回答概括为「just two **presets** for an image object」。两组设置随时可以互相改。
- **三视图的具体摆法**（Chris' Tutorials）：每张图 Location / Rotation 全归零，然后 **R X 90** 立起来面向正前方；侧视图再 **R Z 90**，背视图 **R Z 180**。切视图用小键盘 **1** / **3** / **Ctrl+1**。默认从背面也能看见正视图那张，把 Object Data 里的 **Side** 设成 Front 就各管各了。

---

## 三、版本差异速查：菜单和快捷键搬过家

引用某个具体操作前先确认版本，下面几条是有据可查的变动：

| 项目 | 变化 | 出处 |
| --- | --- | --- |
| Texture Paint 取色快捷键 | **3.6 及更早是 `S`，4.0 起是 `Shift+X`** | Jamie Dunbar 视频；SE 29259 高票老答案说 S，后来的回答注明它已过时 |
| 参考图机制 | 2.79 是贴在视口上的「背景图」；**2.8 起变成场景里真实存在的 empty 对象** | BA 1520905 |
| Import Images as Planes | **4.2 起并入本体**，Add → Image → Mesh Plane，不必再启用插件 | github.com/Pullusb/reference_to_image_plane |
| 4.2 已知问题 | 正交视图里拖进来的 image plane，「Display image in perspective view」**默认是关的**，切到透视就看不见 | projects.blender.org #125583 |
| 顶点色数据块名 | **3.0 之前默认叫 `Col`**，之后叫 `Attribute`；面板名也从 Vertex Colors 变成 Color Attributes | katsbits |
| UV Stretching 显示开关 | 位置在各版本间一直挪；2.83 时在 Edit Mode → UV Editor → View → Overlays → Stretching | Tosmo 视频（「has had a tendency to move around between different versions」） |

---

## 四、哪些是共识，哪些只是某个人的习惯

**高共识（多个独立来源）**：贴图必须单独 Save 或 Pack；粉紫＝找不到图片文件；顶点色必须接进着色器才看得见；Mirror 绕 origin 镜像；Pose Mode 镜像依赖 `.L`/`.R` 命名；参考图要正交视图 + 两张 90 度交叉。

**有分歧，别当定论**：Mirror 到底要不要 Apply；Texture Slot 选 Material 还是 Single Image；打包贴图是稳妥还是有风险；「没保存过的文件 autosave 生不生效」。

**只是个人习惯，别写成通用做法**：参考图 Opacity 调到多少（Chris 用 0.5）；Ryan King Art 说自己几乎从没用过 Mirror 的 **Bisect** 和 **Merge**、只用 Clipping（「I really don't use the bicect that often. I've really never used it for any projects」）——这是他的取舍，不代表这两个选项没用；某个 up 主偏好 PNG 还是 JPEG。

**引用时的分寸**：教程视频的自动字幕里大量「点这里」「按这个键」脱离画面对不上，本文只摘了不依赖画面也成立的部分（快捷键、菜单路径、原理、报错原文）。论坛答案要看是否被采纳、楼主有没有回来确认——凡标了「楼主确认」的都核对过。
