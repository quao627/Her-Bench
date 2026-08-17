# 参考图（reference image）：导进来、对齐、垫着建模

> 来源：https://docs.blender.org/manual/en/latest/modeling/empties.html 、https://docs.blender.org/manual/en/latest/scene_layout/object/types.html 、https://docs.blender.org/manual/en/latest/editors/3dview/navigate/viewpoint.html 、https://docs.blender.org/manual/en/latest/editors/3dview/navigate/projections.html 、https://docs.blender.org/manual/en/latest/editors/preferences/navigation.html 、https://docs.blender.org/manual/en/latest/editors/outliner/interface.html 、https://docs.blender.org/api/current/bpy.ops.object.html

把手绘稿或照片丢进 Blender 当「描图纸」垫着建模，是官方文档直接背书的正规用法。Empties 那一页原话：「Empties can display images. This can be used to create **reference images, including blueprints or character sheets to model from**.」

## 两种把图放进场景的做法

**① Empty Image（Add → Image → Reference / Background）**

Object Types 页的说明：「**Image** — Empty objects that display images in the 3D Viewport. These images can be used to aid artists in modeling or animating.」

关键性质：**empty 是渲染不出来的**——「Because an empty has no volume and surface, it cannot be rendered.」也就是说这类参考图天然不会混进最终画面，不用额外操心。

> 说法边界：Add → Image 菜单下的 **Reference** 和 **Background** 两项，底层调的是同一个 operator（`bpy.ops.object.empty_image_add`，只差一个 `background` 参数），但**手册正文没有专门解释两者的区别**，这里不下结论。

**② Image Plane（Add → Image → Mesh Plane）**

同一页：「**Image Plane** — Adds a mesh plane with materials and texture from an image file. The dimensions of the plane are calculated to match the aspect of the image file.」

这个是**真的网格 + 材质**，长宽会自动按图片比例算好。代价是它会参与渲染，不想让它出现在成品里就得自己在大纲栏里关掉 Disable in Renders。视口里看上去，两种做法都是一张竖着的「白板子」，光看画面分不出是哪种。

## Empty Image 的关键设置（Properties → Object Data → Empty）

- **Offset X, Y**：图片原点的位置。`0.5 / 0.5` 是图片中心，`0.0 / 0.0` 是左下角，`1.0 / 1.0` 是右上角。
- **Depth**：Default / **Front**（永远盖在其他物体前面）/ Back（永远在后面）。手册的 Tip 直接给了建模的推荐组合：「When using the image as a reference for modeling, it can be useful to **set the depth to Front, with a low Opacity**.」
- **Side**：Both / Front / Back。手册 Tip：如果正面和背面各有一张照片，可以让两张图各自只在对应方向看得见。
- **Show in**：Orthographic / Perspective 两个开关，外加 **Only Axis Aligned**（「Only displays the image contents when the view is aligned with the object's local axis」——转开视角图就自动隐掉，就是这个开关）。手册 Hint：「It's often useful to disable this so reference images don't get in the way when viewing a model.」
- **Opacity**：把图片混进背景的不透明度，调低了就是半透明描图纸的效果。

## 为什么要正视图 + 侧视图两张，还得 90 度交叉着摆

一张正视图能定的只有左右（X）和高低（Z）；**前后这个深度方向（Y）完全没有参照**——鼻子突出多少、身体多厚，正面图一点信息都不提供。侧视图补的正是这个方向。

两张成 90 度立着，好处是切到 Front（正对第一张）和 Right（正对第二张）时，各自都能一比一贴着轮廓描，模型从正面和侧面两个方向看外形才都对得上。

> 标注：这一段是几何上的常规做法。**Blender 手册只写了 Empty Image 可以当 blueprints / character sheets 用，没有专门一节讲「必须两张 90 度交叉」**，所以这属于通行工作流，不是官方原文。

## 对齐：必须用正交（orthographic）视图

**切视角**（View → Viewpoint，或直接用小键盘）：

| 方向 | 快捷键 | 反方向 |
| --- | --- | --- |
| Top（顶） | Numpad 7 | Bottom：Ctrl-Numpad 7 |
| Front（前） | Numpad 1 | Back：Ctrl-Numpad 1 |
| Right（右） | Numpad 3 | Left：Ctrl-Numpad 3 |

手册补充：这些键对齐的是**全局（世界）轴**；额外按住 Shift 则对齐到选中物体的**局部轴**，「you can for example view any mesh face head-on, no matter how it's oriented」。

**切投影方式**：**Numpad 5** = View → Perspective/Orthographic。手册解释了为什么建模要用正交：透视是「distant objects appear smaller」，正交则「objects stay the same size regardless of their distance… it provides a more 'technical' insight into the scene, **making it easier to model and judge proportions**」。透视视图下描参考图会有近大远小的畸变，正交没有。

**很多人其实自动就进正交了**：Preferences → Navigation 里的 **Auto Perspective** 开着时，「the view switches to Perspective when orbiting the view, and to **Orthographic when aligning to an axis** (Top, Side, Front, Back, etc.)」——按 Numpad 1 的同时投影方式已经切好了。

另外手册也提了一句：改视口投影**不影响渲染**，「Rendering is in perspective by default」，要渲正交图得去相机的 Lens 面板把 Type 设成 Orthographic。

## 别让参考图碍事：锁住、隐藏、收进一个 collection

大纲栏（Outliner）右侧那排 **Restriction Toggles** 对物体和 collection 都生效（默认只显示几个，其余的在 Filter 弹出面板里打开）：

- **Disable Selection**——手册举的例子恰好就是参考图：「Toggles whether the object or collection can be selected in the 3D Viewport. This can be useful for, say, **reference images that you only want to display and never select/move**.」建模时手一滑把参考图拖走，就是靠这个开关根治的。
- **Hide in Viewports**（等价于在视口里按 H，Alt-H 取消）：只影响 3D 视口，「The render is not affected.」
- **Disable in Viewports**：更彻底的长期隐藏，Alt-H 也不会把它放出来。
- **Disable in Renders**：只影响渲染，视口不受影响。用 Image Plane 当参考图时要靠它把图排除在成品之外。

手册还提到：按住 Shift 点某个图标，会把这个开关一次性应用到它下面所有子项。

**所以常见的组织方式**是：把参考图统一放进一个单独的 collection（比如叫 `reference`），然后对整个 collection 一次性锁选择、按需隐藏。**注意 Blender 并没有内置一个叫 reference 的 collection，这个名字纯粹是个人命名习惯**，大纲里看到它只能说明作者手动建了个分组。

## 一句话总结

参考图是垫在底下的描图纸：正面 + 侧面各一张、90 度交叉卡在模型位置上，Depth 设 Front、Opacity 调低，切到正交的 Front / Right 视图一比一描轮廓；建完之后它不参与最终画面（Empty 根本渲不出来，Image Plane 则要手动关掉 Disable in Renders）。
