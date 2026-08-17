# Blender 核心建模工具

> 来源：https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/transform/basic.html 、https://docs.blender.org/manual/en/latest/modeling/modifiers/index.html 、https://docs.blender.org/manual/en/latest/modeling/modifiers/introduction.html 、https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/mirror.html 、https://docs.blender.org/manual/en/latest/scene_layout/object/editing/transform/control/axis_locking.html 、https://docs.blender.org/manual/en/latest/animation/armatures/posing/tool_settings.html

## 移动 / 旋转 / 缩放：G / R / S

这三个是所有 3D 软件都有的基本变换，Blender 的快捷键是：

- **G（Grab/Move，移动）**：按 G 后拖动鼠标，选中的物体或顶点/边/面就跟着移动。移动过程中按 X、Y 或 Z 能把移动方向锁定在对应坐标轴上，比如按 G 再按 X 就只沿 X 轴移动，很适合精确调整。
- **R（Rotate，旋转）**：按 R 后拖动鼠标进行旋转，同样可以按 X/Y/Z 锁定旋转轴。
- **S（Scale，缩放）**：按 S 后拖动鼠标缩放大小，也支持轴向锁定。

三个操作都支持直接输入数字，比如按 G、X，再打字 "2"，回车，就是精确沿 X 轴移动 2 个单位，不用靠手感拖。这几个键在 Object Mode 和 Edit Mode 下都能用，区别只是操作对象是整个物体还是顶点/边/面。

## 挤出：Extrude（E）

Extrude 是建模里最常用的加体积手段：在 Edit Mode 选中一个面（或边、顶点），按 **E**，拖动鼠标就会从选中的部分“拉”出一段新的几何体，同时自动生成连接原面和新面的侧壁。简单说就是从一个面长出一个新的凸起或凹陷，比如从一个立方体的顶面挤出一根柱子，就是一次 Extrude。挤出默认沿着面的法线方向（垂直于面）移动，也可以按 X/Y/Z 锁定到指定轴。

## 内插面：Inset（I）

Inset 是在选中的面内部再插入一圈缩小（或放大）的新面，效果类似于给这个面往里“镶一圈边框”。在 Edit Mode 选中一个或多个面后按 **I**，拖动鼠标控制内插的距离。Inset 常和 Extrude 搭配使用：先 Inset 出一个小面，再 Extrude 把它往内或往外拉，就能做出窗户、按钮、凹槽这类细节。再按一次 I 可以切换成「Individual」模式，让多个选中面各自独立内插，而不是当成一个整体。

## 环切：Loop Cut（Ctrl+R）

Loop Cut 用来在物体表面切一整圈新的边线，增加局部的分段密度，方便做更细致的形状控制。操作是在 Edit Mode 下按 **Ctrl+R**，把鼠标移到某条边附近，Blender 会实时预览一整圈黄色的切割线，滚动鼠标滚轮可以增加切割的圈数，点击左键确认位置后还能再拖动滑动这圈边的位置，右键或再点一次可以让它保持在中间。环切是给模型加细节、给 Subdivision Surface 之类的修改器保留硬边的常用手段。

## 常见修改器（Modifier）

Modifier 是 Blender 里的“非破坏性”编辑工具：加在物体上之后，原始网格数据不会被直接改动，效果是实时叠加计算出来的，随时可以调整参数或删除，改完之后按需要再「应用（Apply）」把效果固化进网格。三个新手最常用的：

- **Subdivision Surface（细分曲面）**：把网格的每个面自动拆分成更多更小的面，并让整体表面变得圆润平滑，是把「方块感」模型变成有机曲面的最主要手段，常和 Loop Cut 一起用来控制哪些地方保持硬边。
- **Mirror（镜像）**：以物体的某条轴为对称轴，自动生成另一半几何体，做人物、载具这类左右对称的模型时只需要做一半，效率高很多。开启 Clipping 选项后，中线附近的顶点不会越过对称轴，避免中间出现缝隙。
- **Bevel（倒角）**：把物体的尖锐边缘“削”出一个圆润或斜切的过渡面，Amount 控制倒角的宽度，Segments 控制倒角面被细分成几段（段数越多越圆滑）。现实中的物体边缘很少是完全锋利的直角，加一点 Bevel 能让模型看起来更真实。

这几个工具组合起来，就是 Blender 硬表面建模最基本的一套流程：用 G/R/S 摆位置，用 Extrude/Inset/Loop Cut 加细节，最后用 Modifier 做整体的平滑和对称处理。

## Mirror 修改器：好用在哪、坑在哪

先把手册的原始定义摆清楚：Mirror modifier「mirrors a mesh along its **local X, Y and/or Z axes, across the Object Origin**」——注意对称面是过**物体原点**的，不是随便某条线；也可以指定另一个物体（通常是个 empty）当 Mirror Object，改用那个物体的轴。

选轴的行为：「You can select more than one of these axes… With one axis you get a single mirror, with two axes four mirrors, and with all three axes eight mirrors.」勾多了会一下子多出好几份镜像。

手册在 Hints 里点明了它的定位：「Many modeling tasks involve creating objects that are symmetrical. This modifier offers a simple and efficient way to do this, **with real-time update of the mirror as you edit it**.」——你在一侧的每一次编辑都会实时同步到另一侧。这正是它高效的原因，**也正是它的副作用来源**。

### 副作用：不对称的地方它也照镜不误

Mirror 是「整个网格按轴对称」这条规则，它没有「这块除外」的概念。只要这个修改器还挂着、这部分几何还在它的作用范围里，你对一侧做的任何编辑都会原样出现在另一侧。

**典型翻车场景**：角色左手要做一个伸手拿杯子的动作，右手应该垂着——但因为整个身体是靠 Mirror 做出来的，动左手的同时右手被强行做成一模一样的姿势，看起来像两只手同时去够同一个东西。这不是 bug，就是这个修改器的定义在起作用。

### 常规的规避思路

- **Apply（应用）掉再改**：手册对 Apply 的说明是「Makes the modifier "real": converts the object's geometry to match the applied modifier's results, and **deletes the modifier**」。Mirror 页也写了：「Once your modeling is completed you can either click Apply to make a real version of your mesh, or leave it as-is for future editing.」应用之后两侧变成各自独立的真实几何，想单独调哪边都行——代价是从此失去实时对称，改一边另一边不会跟着动了。
- **让不对称的部分不进镜像范围**：把手臂之类需要单独动作的部位拆成独立物体、或者从被镜像的那部分几何里排除出去，就不会被同步。
- 注意 **Clipping** 这个选项本身也会限制编辑：「Vertices on the mirror plane will be unable to move away from the mirror plane as long as Clipping is enabled. You must disable it to be able to move the vertices along the mirror axis again.」中线上的顶点动不了的时候，先看看是不是 Clipping 开着。

### Blender 里「镜像」不止一种，别混为一谈

口语里说「用了镜像工具」，可能指的是下面几个之一，副作用长得很像但机制不同：

- **Mirror modifier**：作用在网格上，上面讲的就是它；
- **X-Axis Mirror**（Sidebar ‣ Tool ‣ Options，Edit Mode 和 **Pose Mode** 都有）：作用在**骨骼**上。手册原话：命名成对（`.L` / `.R` 之类后缀）的骨头，「each time you transform (move, rotate, scale…) a bone, its "other side" counterpart will be transformed accordingly, through a symmetry along the armature local X axis」。摆姿势时两只手同步动，很可能是这个而不是修改器。

**没有画面证据的时候，不要替人断定用的是哪一种**——两者造成的现象几乎一样。
