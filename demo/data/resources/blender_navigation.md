# Blender 视口导航与选择基础

> 来源：https://docs.blender.org/manual/en/latest/editors/3dview/navigate/navigation.html 、https://docs.blender.org/manual/en/latest/editors/3dview/navigate/viewpoint.html 、https://docs.blender.org/manual/en/latest/editors/3dview/navigate/projections.html 、https://docs.blender.org/manual/en/latest/editors/3dview/display/gizmo.html 、https://docs.blender.org/manual/en/latest/editors/3dview/display/overlays.html 、https://docs.blender.org/manual/en/latest/scene_layout/object/editing/transform/control/axis_locking.html

## 视口（Viewport）导航三件套

Blender 默认用鼠标中键（MMB）来控制视角，三个动作都围着中键转：

- **旋转视角（Orbit）**：按住中键拖动，视角就绕着场景转。这是最常用的操作，看模型的正面、侧面、背面全靠它。
- **缩放（Zoom）**：滚动鼠标滚轮就能缩放，或者按住 Ctrl 再拖中键。数字键盘的 `+` / `-` 也能缩放。
- **平移（Pan）**：按住 Shift 再拖中键，视角整体平移，不改变朝向，适合把模型挪到视口中间。

没有鼠标中键（比如触控板）的话，也可以在 View 菜单里找到对应操作，或者在偏好设置里换成 Emulate 3 Button Mouse。

## 数字键盘切换正视图

键盘右侧的数字键盘（Numpad）是切固定视角的快捷方式：

- **Numpad 1**：正前视图（Front）
- **Numpad 3**：右侧视图（Side）
- **Numpad 7**：顶视图（Top）
- 同一个键位配合 Ctrl 会切到反方向（比如背面、左侧、底部）
- **Numpad 5**：在透视（Perspective）和正交（Orthographic）之间切换——建模找角度、量尺寸时正交视图更准

笔记本没有独立数字键盘的话，可以在偏好设置里开启「Emulate Numpad」，用主键盘数字键代替。

## Object Mode 与 Edit Mode

Blender 里最基础的两个模式：

- **Object Mode（物体模式）**：把整个物体当一个整体来操作，比如移动、复制、删除一整个模型。刚打开 Blender、选中一个物体时默认就在这个模式。
- **Edit Mode（编辑模式）**：进到物体内部，直接操作顶点（Vertex）、边（Edge）、面（Face），是真正“建模”的地方，比如加线、挤出、切面都在这个模式下做。

两个模式之间用 **Tab 键**来回切换——选中物体后按一次 Tab 进编辑模式，再按一次 Tab 回到物体模式。如果按 Ctrl+Tab，会弹出一个模式选择的圆盘菜单，方便切到更多模式（比如雕刻模式）。

## 选择物体的基本方式

- **左键单击**：选中点到的物体（Blender 2.8 之后默认左键选择，不是右键）。
- **Shift + 左键单击**：在已有选择基础上加选或减选多个物体。
- **A 键**：全选场景里所有物体。
- **Alt + A**：取消所有选择。
- 框选（按住鼠标左键拖出一个框）也能一次选中多个物体，这个习惯在 Edit Mode 里选顶点、边、面时同样好用。

先练熟这几个手感，后面学具体建模工具会顺很多。

## 怎么分清自己在哪根轴上：X 红、Y 绿、Z 蓝

新手最常犯晕的就是「我到底是在 X 轴还是 Y 轴」。Blender 用一套**固定的颜色**来标轴向，认颜色比认字母快得多。

手册在讲 Object Gizmos 时写得很直白：「A gizmo always has three **color-coded axes: X (red), Y (green), and Z (blue)**.」这套配色是全局统一的——地面网格里那两条穿过原点的高亮线（Overlays 面板里的 **Axes** 开关控制「Show the X, Y and/or Z axis lines」）、右上角那个导航球、变换 gizmo 上的三根杆，用的都是同一套红绿蓝。

**看到一条黄绿色的线亮着，就是 Y 轴；红的是 X，蓝的是 Z。**

## 锁轴：G / S / R 之后再按 X / Y / Z

手册的 Axis Locking 页：「The axis of movement can be changed at any time during transformation by typing X, Y, Z.」在 Object Mode 和 Edit Mode 下，移动、缩放、旋转、挤出都能这么锁。

几条实用细节，都是手册原文：

- **锁住的那根轴会画得更亮**：「A locked axis will display in a brighter color than an unlocked axis.」
- **左上角会直接写出当前锁在哪根轴上**：「The current mode will be displayed in the left-hand side of the 3D Viewport header.」——比如 `Scale: 9.54833 along global Y axis` 这行，就是在告诉你「现在沿全局 Y 轴缩放，倍数 9.54833」。分不清方向的时候，看这行字比看画面靠谱。
- **同一个键按多次会换参考系**：第一次按锁到当前 Transform Orientation 的对应轴，第二次按切到 **Global** 轴（如果本来就是 Global，则切到 Local），第三次按取消所有约束。
- **Shift + X/Y/Z 是「平面锁」**：锁住两根轴、放开一根，等于让物体只在某个平面内自由移动或缩放。手册注明平面锁只对移动和缩放有意义。
- 锁轴之后照样可以直接打数字，键盘输入的精确值不受影响。

## 正交 vs 透视：Numpad 5

手册解释了这两种投影的差别：透视是我们眼睛习惯的「distant objects appear smaller」；正交则是「objects stay the same size regardless of their distance… making it easier to model and judge proportions」——量比例、对参考图的时候必须用正交。

另外 Preferences → Navigation 里有个 **Auto Perspective**，开着的时候按 Numpad 1/3/7 对齐到某个轴会**自动切成正交**，转动视角又自动回到透视。所以有时候你并没有主动按 Numpad 5，视图却已经是正交的了。
