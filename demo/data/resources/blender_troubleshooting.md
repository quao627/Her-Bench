# 崩溃救援 & 「画的颜色说没就没」：社区排查手册

> 来源（视频）：Recover Lost Or Crashed Files - Blender 3 - AutoSave, Grant Abbitt (https://www.youtube.com/watch?v=dpD_ly5deZ4) 、2 Ways to recover LOST work in Blender, BitterButterRender (https://www.youtube.com/watch?v=hadwDHvio18) 、Blender 4.0 - Texture Painting quick start guide, Jamie Dunbar (https://www.youtube.com/watch?v=iwWoXMWzC_c) 、Common Texture Issues and How to Fix Them in Blender, Tosmo (https://www.youtube.com/watch?v=KJ5OgYFqilk) 、Fixing 11 Common Blender 3D Mistakes, Blender Ustad (https://www.youtube.com/watch?v=97xRbo5qjRg)
>
> 来源（社区）：https://blender.stackexchange.com/questions/14413/how-to-setup-auto-save 、https://blender.stackexchange.com/questions/64334/blender-is-saving-as-a-blend1-file-not-blend 、https://blender.stackexchange.com/questions/58027/computer-crashed-entire-scene-replaced-with-default-cube 、https://blenderartists.org/t/recover-unsaved-work-after-crash/1397788 、https://devtalk.blender.org/t/move-autosave-out-of-tmp/10328 、https://blenderartists.org/t/blender-texture-painting-crashes-fixed/1263429 、https://blender.stackexchange.com/questions/7681/why-did-the-texture-i-painted-in-texture-paint-mode-disappear 、https://blender.stackexchange.com/questions/5368/why-are-all-the-textures-in-my-file-pink 、https://blender.stackexchange.com/questions/15301/cant-paint-texture 、https://blender.stackexchange.com/questions/284851/texture-paint-not-working 、https://blender.stackexchange.com/questions/304624/texture-paint-not-painting-properly 、https://blender.stackexchange.com/questions/19459/how-can-vertex-paint-be-rendered 、https://blender.stackexchange.com/questions/25928/how-to-hide-vertex-colors-in-texture-paint 、https://blenderartists.org/t/vertex-paint-not-showing/678600 、https://blenderartists.org/t/i-just-lost-all-my-texture-paint/1184677 、https://blenderartists.org/t/painted-texture-empty/1405098 、https://blenderartists.org/t/painted-textures-dont-stay/642710 、https://blenderartists.org/t/texture-paint-only-paints-black/1556981 、https://blenderartists.org/t/cant-paint-texture/1236396 、https://blenderartists.org/t/paint-over-existing-texture/1628455 、https://blenderartists.org/t/texture-paint-mode-says-missing-textures-although-that-there-are-no-missing-textures/1274721 、https://blenderartists.org/t/painting-on-wrong-textures/1233778 、https://blenderartists.org/t/cant-paint-over-black-squares-on-texture-dont-know-where-they-came-from/1587537 、https://blenderartists.org/t/texture-paint-affecting-incorrect-part-of-model/1547460 、https://blenderartists.org/t/object-disappearing-in-texture-paint-mode-there-in-edit-mode/1493790

官方手册讲「这个功能是什么」，这份讲「我照做了为什么还是出问题」。素材来自教程视频和论坛高赞回答。**下文用 `SE 数字` 指上面的 blender.stackexchange 问题号、`BA 数字` 指 blenderartists 帖子号。社区吵起来的地方照原样列出来，不替它们下结论。**

---

## 一、崩了 / 手滑关了，进度还救得回来吗

### 成因侧的第一件事：Blender 有三套备份，别混成一套

SE 14413 的最高票回答（score 17）第一句就在纠正这个：「The autosave timer and the .blend1, .blend2 files are part of **separate systems**.」

| 机制 | 什么时候产生 | 存在哪 | 怎么打开 |
| --- | --- | --- | --- |
| 自动保存临时文件 | 每隔 N 分钟（默认 2） | 系统临时目录，文件名带随机数字 | File → Recover → Auto Save |
| `quit.blend` | 退出 Blender 时 | 同一个临时目录 | File → Recover → Last Session |
| `.blend1` / `.blend2` … | **每次手动保存时** | 跟 `.blend` 同一个文件夹 | 直接打开（见下） |

新手最容易混的是把 `.blend1` 当「自动保存文件」。论坛里确实有人这么叫（BA 1397788 有回复说「those are your autosave files」），**这个说法是错的**——`.blend1` 只跟手动保存挂钩。

### 排查顺序

1. **先试 File → Recover → Auto Save。** 两个教程视频强调同一点：这个菜单打开的文件浏览器**直接指向正确的临时目录**，还带修改时间，不用自己翻系统文件夹（Grant Abbitt、BitterButterRender 都是按修改时间找最新那个）。
2. **再试 File → Recover → Last Session**（读 `quit.blend`）。
3. **去项目文件夹找 `.blend1`。** 坑在于：**打开文件对话框默认不显示备份文件**，得在显示过滤器里手动打开「backup files」（SE 14413、SE 64334）。另一条通行做法是把 `myfile.blend1` 改名成 `.blend` 再打开。

### 社区反复提到、手册里没写的几条

- **临时目录本身就靠不住。** 开发者论坛整帖在提这事（devtalk 10328），发起人因系统崩溃丢了四小时——Linux 上 `/tmp` 常挂在内存里，**整机崩溃或重启后，自动保存和 `quit.blend` 会一起没**。根治办法是去 Preferences → File Paths → Temporary Files 指一个真实目录。
- **`.blend1` 救回来的常是「大部分」不是「全部」**（SE 58027：崩溃后 `.blend1`「seemed to have most of the scene, though I still had to repair parts of it」）。
- **Texture Paint 本身就是崩溃高发环节。** 论坛有帖子标题直接写着 texture painting crashes（BA 1263429），最后查出的原因不是显卡，而是从旧版本带过来的 startup file 里挂着一个 modifier。单个案例，不能当通用诊断。
- **从没保存过的新文件能不能救？说法不一。** BA 1397788 里楼主开着 1 分钟自动保存却只找到 `quit.blend`，回复说「先存一次盘，autosave 才开始起作用」。**官方文档没有这条限制，两边对不上。** 但「开工先 Ctrl+S 存一次」在社区里是压倒性共识。

---

## 二、手绘的颜色一上贴图 / 一换材质就没了

新手区提问量最大的一类。**同一句「颜色没了」，底下至少六七种完全不同的成因。**

### 症状 A：重开文件就没了，有时模型还变粉紫色

**成因：贴图图片没有单独保存。** 共识度最高的一条。SE 7681 被接受的回答：「You need to save the image texture to an image file … otherwise all changes are lost.」教程视频说得更直白（Jamie Dunbar）：「**Blender doesn't do this by default, not even when you save your scene**.」

**验证**：Image Editor 顶部 Image 菜单旁有个**星号**，就代表改过没存。**修**：Image → Save As，或 File → External Data → **Pack Resources** 打包进 `.blend`（打包这条有人反对，认为有损坏风险，主张存外部文件——BA 642710，个人意见非共识）。

**粉紫色 = 找不到图片文件。** Blender SE 上浏览量最高的问题之一（15 万+，SE 5368）：「Pink means that the texture files are missing … textures are referenced **relative to the blend file**.」修法：External Data → Find Missing Files / Make All Paths Absolute / 打包。**没存过的手绘贴图重开后正好就长这样**，两个症状是连着的。

### 症状 B：Blender 一直开着，中途颜色突然全没了

**这条社区没有定论，三种说法互相打架**（同一帖 BA 1184677）：撤销撤过头了；Blender 把没保存的图当可回收内存扔了（「it keeps it in volatile memory, and eventually, it decides it doesn't need that memory anymore」）；还有人两条都不认，要求提供复现步骤，**帖子最后没结论**。BA 1405098 的说法又是第三种：新建图片时把已有图片的 datablock 覆盖了。**所以遇到这种情况，诚实的答法就是「说不准是哪一条」**；唯一共识在操作层面：离开 Paint 模式前先点一下 Save All Images。

### 症状 C：一加材质 / 一接 Image Texture，之前画的就被盖住了

最贴近「贴图一上到角色身上，之前画好的颜色说没就没」的一类，机制有好几种：

- **顶点色（Vertex Paint）根本没接进材质。** 顶点色不是贴图，存在 Color Attribute 里，材质不去读就等于不存在。标准答案是在着色器里加 Attribute / Color Attribute 节点、填上图层名（老版本默认 `Col`）再接进 Base Color（SE 19459，score 24）。**最贴题的一条**在 BA 678600：楼主的错误是**新建了一个材质，而不是把顶点色接进原来那个皮肤材质**——修法是回原材质加 Attribute 节点 + 一个设成 Multiply 的 MixRGB，把两者**混**起来。
- **shader 里有两张图，你画的是被压在下面那张。** SE 284851 被接受的回答：「the image called SnakeTex02 is over the one called SnakeTex01, so whatever you do on SnakeTex01, you won't see it.」
- **想在已有贴图上加手绘，正确做法是「混」不是「盖」。** 别直接往那张贴图上画，新建一张**透明**图片当图层，用 Color Mix 节点把两张混起来、拿透明图的 **Alpha 输出当混合因子**，画在透明图上（SE 304624，同样的配方在 BA 1628455 又出现一次）。根本原因有人点破了：**Blender 原生没有图层概念**（「blender does not support layers」）。
- **反过来，顶点色图层也可能把贴图压成全黑**（SE 25928）。

### 症状 D：笔刷划过去什么都没发生

- **三样东西缺一不可。** Jamie Dunbar 的视频演示了那行报错原文：「**missing UVs, materials and texture detected**」——UV、材质、图片，缺哪个都画不上。
- **笔刷上挂了一张黑图。** 高票回答（score 21，SE 15301）：默认笔刷是 TexDraw，「If no texture exists, it paints with a plain black square, which leaves no trace **because the default color of the image texture is also black**.」另一帖楼主确认就是这条（BA 1236396）：「It **multiply your brush effect by 0**, nullifying it.」也有人是把要画的目标图误填进了 brush texture 栏（BA 1556981）。
- **新建图片时 alpha 设成 0**（BA 1493790，Blender 3.6 / 4.1）；或 **Texture Slot 指向了一个空槽**（BA 1274721 说切到 Material，BA 1233778 说切到 Single Image，方向相反——**两边都对，关键是别让它指向空的**）。

### 症状 E：画一笔，模型上两个地方同时被涂

**UV 重叠，或者有多套 UV。** BA 1587537 楼主最后自己查出来：**是 Mirror 修改器造成的重叠**——没应用的镜像意味着两侧共用同一片 UV，一笔下去两边都上色（这条跟 Mirror 的关系在 `blender_community_tips.md` 里展开）。BA 1547460 的答案则是物体上有多套 UV set。

另有两条连带坑：Ctrl+J 合并两物体后其中一个贴图消失，是因为两者 UV 图层**名字不一样**（`UVMap` vs `UVMap.001`），合并后成了两个通道、一次只能启用一个，合并前先改成同名即可（Blender Ustad）；Object Mode 里改过的 Scale / Rotation **必须 Ctrl+A 应用掉**，否则 unwrap 出来是歪的，而且「these changes will **not** show up in UV stretching」，连拉伸检查都看不出问题（Tosmo）。

---

## 三、怎么用这份资料下判断

上面每一节都是「可能的成因清单」，不是诊断结论。社区里同一个症状经常有三四种互相打架的解释，连原帖楼主都常常是试到最后才知道是哪条。合适的用法是：**把可能性讲清楚，同时说明凭现有信息定不了是哪一条。** 没有画面证据、当事人也没说明的时候，别替他挑一条当答案——尤其「他最后到底怎么绕过去的」这种，只有他自己知道。
