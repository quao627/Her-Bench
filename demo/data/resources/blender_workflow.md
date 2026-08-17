# Blender 新手常见困惑排查

> 来源：https://docs.blender.org/manual/en/latest/interface/window_system/tabs_panels.html 、https://docs.blender.org/manual/en/latest/interface/undo_redo.html 、https://docs.blender.org/manual/en/latest/render/materials/introduction.html 、https://docs.blender.org/manual/en/latest/troubleshooting/crash.html

## 找不到某个面板/按钮怎么办

Blender 界面里大部分面板是可以被隐藏或者滚动到看不见的地方的，遇到「教程里有但我这没有」的情况，先按这几个方向排查：

- **侧边栏（Sidebar）不见了**：按 **N** 键就能在 3D 视口右侧呼出/收起侧边栏，里面有物体的位置、旋转、缩放数值等信息，这是最容易被误关的一块。
- **Properties 编辑器的某个选项卡（比如 Modifier 的扳手图标）找不到**：右侧属性面板是竖排的图标当选项卡，如果窗口太窄，部分选项卡可能被挤到看不见，把鼠标放在选项卡区域滚动，或者拖宽面板区域即可。
- **界面布局整体乱了**：顶部有 Layout、Modeling、Sculpting 等工作区（Workspace）标签页，先确认自己是不是切到了别的工作区；实在理不清，可以通过 File → Defaults → Load Factory Settings 恢复到默认界面布局（注意这会重置所有偏好设置，不是撤销单个操作）。
- 拖动面板边界能调整大小，面板边缘的小三角/双箭头图标是折叠展开的开关，很多“消失”的功能其实只是被折叠了。

## 不小心删除物体怎么撤销

Blender 的撤销机制很直接：

- **Ctrl+Z**：撤销上一步操作（手册：Edit ‣ Undo），可以连续按，一路撤回到之前很多步。
- **Shift+Ctrl+Z**：重做（Redo，手册：Edit ‣ Redo），如果撤销多了想恢复回来就用这个。
- **Edit → Undo History**：一份最近操作的列表，点某一项就跳回那个状态，不用一步步按 Ctrl+Z。手册原话：「Rolling back actions using the Undo History feature will take you back to the action you choose.」注意 3.6 / 4.2 / 5.x 的手册在这一项下**都只写了菜单位置，没有列快捷键**（Undo 和 Redo 则明确列了 Ctrl-Z 和 Shift-Ctrl-Z）。网上常见的 Ctrl+Alt+Z 说法未在官方手册中出现，也可能随键位方案不同而不同，别当成定论。
- **F9**（Adjust Last Operation）：改上一步操作的参数而不是撤销它，比如刚挤出完想改挤出距离。

误删物体、误操作变形，第一反应都是 Ctrl+Z，比在场景里手动重建要快得多。需要注意的是撤销步数有上限（Preferences ‣ System ‣ Memory & Limits ‣ Undo Steps 可调；手册在讲崩溃排查时还建议内存不够就把这个值调小），而且手册明说「Once you do make a new change, the Undo History is truncated at that point」——一旦在中途做了新改动，那条时间线后面的记录就没了。所以重要节点还是要手动保存（Ctrl+S）。

## 崩溃、进度丢失、贴图颜色消失

这三类是最常见的翻车场景，因为涉及的官方文档比较多，单独拆了两篇：

- **崩溃后怎么找回进度**（Auto Save 存在哪、`.blend1` 备份怎么来的、File → Recover 那两项各自能救什么）：见 `blender_recovery.md`。手册在 Troubleshooting → Crashes 里给的第一条建议就是「you may be able to recover your work with Auto Save」。
- **Texture Paint 里画好的颜色为什么会消失**（图片没保存、顶点色和贴图不是一回事、Base Color 被贴图顶掉、画错 slot、UV 重叠等）：见 `blender_texture_paint.md`。

## 材质与渲染的基本关系

新手常把「材质」和「渲染」搞混，其实两者是分工关系：

- **材质（Material）**定义的是物体表面「长什么样」——颜色、粗糙度、金属感、透明度等等，本质上是靠一套叫 Shader（着色器）的运算规则来描述光线打到表面上会发生什么。Blender 里最常用的是 Principled BSDF 这个万能着色器，调它的参数就能做出塑料、金属、玻璃、皮肤等各种材质效果。
- **渲染（Render）**是渲染引擎（比如 Eevee 或 Cycles）根据场景里的材质、灯光、摄像机角度，实际计算出一张最终图像的过程。同一个材质，在不同渲染引擎、不同灯光条件下渲染出来的效果可能差别不小。
- 简单理解：材质是「食材和调料」，渲染引擎是「怎么做菜」，最后渲染出的图像才是「成品」。物体如果没有指定材质，渲染时会显示为默认的灰色。

新手卡住的时候，先分清楚问题出在「材质没调对」还是「渲染设置不对」，排查方向能少走很多弯路。
