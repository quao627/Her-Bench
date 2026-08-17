# Texture Paint 与「画好的颜色说没就没」

> 来源：https://docs.blender.org/manual/en/latest/sculpt_paint/texture_paint/introduction.html 、https://docs.blender.org/manual/en/latest/sculpt_paint/texture_paint/tool_settings/texture_slots.html 、https://docs.blender.org/manual/en/latest/sculpt_paint/vertex_paint/introduction.html 、https://docs.blender.org/manual/en/latest/editors/3dview/display/shading.html 、https://docs.blender.org/manual/en/latest/editors/preferences/save_load.html 、https://docs.blender.org/manual/en/latest/files/blend/packed_data.html 、https://docs.blender.org/manual/en/latest/interface/controls/nodes/parts.html 、https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html 、https://docs.blender.org/manual/en/latest/interface/controls/templates/color_ramp.html 、https://docs.blender.org/manual/en/latest/modeling/meshes/uv/unwrapping/introduction.html

## Texture Paint 到底在画什么

手册开宗明义：UV texture 就是一张图片（image / sequence / movie），「that is used to color the surface of a mesh. The UV texture is mapped to the mesh through one or more UV maps.」

Texture Paint 模式是让你在 3D 视口里**直接往模型上涂**，Blender 通过当前的 UV map 把笔触投射到那张图片上：「In the 3D Viewport in Texture Paint Mode, you paint directly on the mesh by projecting onto the UVs.」在 Image Editor 里画的是摊平的那张画布，两边实时互通。

**硬前提是先展 UV**：「The object to be painted on must first be unwrapped.」没有 UV 层的话，「When no UV layers can be detected, Blender will display a warning message.」应急可以用 Texture Paint 模式里的 **Add Simple UVs**（手册说它就是一次简单的 cube unwrap 加一次 pack，「It's still recommended to make a custom unwrap.」）。

## 官方文档记在案的几类「画不上 / 看不见 / 丢了」

新手把这几种情况都笼统说成「颜色没了」，但成因完全不同。

### 1. 图片改了没保存 —— 最典型的「真的丢了」

手册在 Texture Paint 页明写：「However, the modified texture **will not be saved automatically**; you must explicitly do so with Save Image.」判断方法也写了：**Image Editor 顶上 Image 菜单旁边有个星号，就代表改过但没存。**

配套的偏好设置是 Preferences → Save & Load → **Save Modified Images**，三个选项 Ask Every Time / Always Save / Never Save，手册在这里挂了一条警告：「Failing to manually save modified images will result in the changes being lost.」

另一条保命路是 File → External Data → **Pack Resources**（或 Automatically Pack Resources），把外部图片打包进 `.blend` 里；Texture Paint 页也提到「If Packing is enabled… saving your images to a separate file is not necessary.」

> 再叠一层：Blender 的 Auto Save **明写不保存 Texture Paint 模式下的改动**（见 blender_recovery.md）。所以「画贴图的时候崩了」这个组合，是文档层面确实存在风险的组合。

### 2. Vertex Paint 的颜色和 Texture Paint 的贴图，不是一回事

Vertex Paint 是「painting color onto an object, **by directly manipulating the color of vertices, rather than textures**」，颜色存成 **Color Attribute**（顶点色），根本不进贴图。

顶点色能不能被看见，取决于两件事：

- 视口里：Solid Shading → Color 选 **Attribute**，手册说这会「Display the active Color Attribute of an object」；
- 渲染/材质里：得在材质节点树里接一个 Color Attribute 节点（「Color Attributes can be used in a material node tree using the Color Attribute Node.」）。

**所以很常见的一幕是**：在 Vertex Paint 里涂得好好的，一旦切到 Material Preview / Rendered，或者给物体配上一个走贴图的材质，那些颜色就「不见了」。它们没被删掉，只是没有任何东西在用它们。同一个下拉里 Solid → Color 选 **Texture** 则是另一套：「Show the texture from the active image texture node using the active UV map coordinates」。

### 3. 材质里一接贴图，原来手调的颜色就被顶掉

Principled BSDF 的 **Base Color** 是「Overall color of the material used for diffuse, subsurface, metal and transmission」，也就是整体颜色从哪来。

节点手册对插槽的说明是：「Each input socket, except for the green shader input, **when disconnected**, has a default value which can be edited via a color, numeric, or vector interface input.」反过来讲——插槽一旦被连上，那个手调的颜色控件就不再决定结果，数据从连线来。

**结果**：给 Base Color 接上一张 Image Texture 之后，之前调好的整片颜色就被那张图整体取代。要是那张图还是新建出来的空白 / 默认底色，视觉上就正好是「颜色一上贴图就全没了」。

### 4. 画到了错的那个 Texture Slot 上

手册：Texture Slots 的 **Material** 模式下，「For the Cycles renderer, all textures (Image Texture node) in the material's node tree are added in the slots tab.」哪一个生效由 **Active Paint Texture Index** 决定，还得配一个 **UV Map** 下拉选用哪层 UV。

材质里有多张贴图的时候，很容易画在了当前没显示的那一张上，看起来就是「笔刷划过去什么都没发生」。

### 5. 手册专门列的三条 Known Limitations

- **UV Overlap**：「In general overlapping UVs are not supported (as with texture baking).」不过手册补了一句，只有当一笔同时刷到多个共用同一张贴图的面时才真出问题。
- **透视视图下部分在视野外的面画不上**：「When painting onto a face which is partially behind the view (in perspective mode), the face cannot be painted on.」解决办法手册也给了：拉远，或者切到正交视口。
- **透视 + 低模，法线背对视角时可能画不上**：手册建议关掉笔刷 stroke 设置里的 **Normal Falloff**，并点名这是 Blender bug #34665，典型场景就是画立方体的侧面。

## 「改用渐变色反而成功了」这件事

**先声明：下面是把文档事实摆在一起，不是官方给出的因果解释。** 手册没有把「换成渐变」列为上面任何一条的官方解法。

Blender 里做渐变至少有两条不经过「逐笔画在 UV 贴图上」的路：

- 材质节点里用 **Color Ramp**——手册：「Color Ramps specify a color gradient based on color stops. Each stop has a position and a color.」颜色是算出来的，不存在需要手动 Save Image 的图片；
- 直接拿一张现成的渐变图当贴图接上去。

这两条的共同点是：不依赖笔刷落点、不依赖 UV 铺得多好、也不存在「改完忘了保存图片」这一步，所以上面第 1、4、5 类坑都自动绕开了。

至于某次具体的失败到底卡在哪一条——UV 没铺好、画错了 slot、还是图片没保存——**没有画面证据就无法确定，不要替当事人下诊断**。能确认的只是「反复手绘失败，换个做法绕过去了」这个结果。
