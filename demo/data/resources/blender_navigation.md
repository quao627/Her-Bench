# Blender 视口导航与选择基础

> 来源：https://docs.blender.org/manual/en/latest/editors/3dview/navigate/navigation.html 、https://docs.blender.org/manual/en/latest/editors/3dview/modes.html

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
