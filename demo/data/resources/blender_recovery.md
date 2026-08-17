# Blender 崩溃救援：自动保存、备份文件与恢复

> 来源：https://docs.blender.org/manual/en/latest/files/blend/open_save.html 、https://docs.blender.org/manual/en/latest/editors/preferences/save_load.html 、https://docs.blender.org/manual/en/latest/editors/preferences/file_paths.html 、https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html 、https://docs.blender.org/manual/en/latest/troubleshooting/crash.html 、https://docs.blender.org/api/current/bpy.types.PreferencesFilePaths.html

Blender 崩溃是新手阶段极其常见的事。官方手册专门有一页讲崩溃（Troubleshooting → Crashes），开篇列的三大常见原因是：内存耗尽、显卡或驱动的问题、Blender 自身的 bug。同一页紧接着的第一句建议就是「Firstly, you may be able to recover your work with Auto Save.」——先去试自动保存。

Blender 里能救回进度的机制有三套，互相独立，出事时值得挨个试。

## 一、File → Recover → Auto Save（自动保存）

**它是什么**：Blender 会按固定间隔把当前文件的一份临时备份写到系统临时目录（Temporary Directory）。开关在 Preferences → Save & Load → Blend Files → **Auto Save**，下面的 **Timer (Minutes)** 是间隔分钟数。

**默认值**：Python API 文档写得最明确——`use_auto_save_temporary_files` 默认为开（True），`auto_save_time` 默认 **2 分钟**，可调范围 1–60。（Blender 4.2 手册正文也写「The default value of the Blender installation is 2 minutes. The minimum is 1, and the Maximum is 60」；最新版手册把这句具体数字删掉了，只说「Specifies the interval, in minutes, between automatic saves」。两边不矛盾，只是新版没写死。）

**怎么恢复**：菜单 File → Recover → Auto Save。手册原话：选这一项会打开一个**指向系统临时目录的文件浏览器**；自动保存的文件名「typically have a name such as `<filename>_autosave.blend` or a random identifier」，扩展名还是 `.blend`。API 那边补了一句这类文件「uses process ID」，也就是名字里可能带进程号。

**三条必须知道的限制**（手册 4.5 LTS / 5.0 / 5.2 都写了这段，4.2 及更早的手册没有这段文字）：

- **Auto Save 不保存 Sculpt、Texture Paint、Edit Mode 里的改动。** 手册原话：「Auto save has some limitations, notably it will not save changes in Sculpt, Texture Paint, and Edit mode.」Python API 对同一个属性的说明是「Warning: Sculpt and edit mode data won't be saved」（这条只点了 Sculpt 和 Edit，没点 Texture Paint，两处措辞不完全一致，以手册正文为准更保险）。
- **每个项目只留一份自动保存**：「Only one auto-saved file is kept per project… Older auto saves are not retained.」不存在「回退到二十分钟前那一版」这种操作。
- **恢复回来的是上次自动保存那一刻的状态**，之后的改动一律丢失。

> 对「做贴图做到一半崩了」这种场景，这条限制值得注意：Texture Paint 模式恰好在 Auto Save 明写的盲区里。但手册只说「不保存该模式下的改动」，没说这种情况下自动保存文件就完全没用或者不生成——**不能据此断定某次崩溃一定救不回来**。

## 二、File → Recover → Last Session（上次会话）

手册原话：这会载入 Blender **退出前**自动写的 `quit.blend` 文件，「This option enables you to recover your last work session if, for example, you closed Blender by accident.」

手册举的例子是「不小心关掉了 Blender」。**至于程序真的崩溃（进程被强杀）时 `quit.blend` 会不会被写出来，官方文档没有交代**——按机制推断多半写不出来，但这属于推断，不是文档结论。所以崩溃场景下主力还是 Auto Save，Last Session 更适合「手滑点了退出」。

## 三、`.blend1` / `.blend2` 备份文件

**它是什么**：Preferences → Save & Load → Blend Files → **Save Versions**。手册原话：「This option keeps saved versions of your file in the same directory, using extensions: `.blend1`, `.blend2`, etc., with the number increasing to the number of versions you specify. Older files will be named with a higher number.」也就是说，`myfile.blend` 是最新的，`myfile.blend1` 是上一次保存的，`myfile.blend2` 是上上次，跟主文件放在同一个文件夹里。

**跟自动保存是两套东西**：API 文档对 `save_version` 的说明是「The number of old versions to maintain in the current directory, **when manually saving**」——`.blend1` 只在你**手动按 Ctrl+S 保存**的时候产生，不是自动保存产生的，也不在临时目录里。

**默认值这里有分歧，注意**：Python API 明写 `save_version`「(in [0, 32], **default 1**)」；但手册正文举例时说「with the **default setting of 2**, you will have three versions of your file」。两个官方来源对默认值说法不一致。按 API 的说法，默认只会多出一个 `.blend1`；按手册举例的说法会有 `.blend1` 和 `.blend2`。**用之前自己去 Preferences 里看一眼实际数值最稳妥。**

**怎么用它恢复**：手册只写了这些文件怎么产生，**没有写恢复步骤**。社区通行的做法是直接打开 `.blend1`，或者先把它改名成 `.blend` 再打开——这属于经验做法，不是官方文档里的说明。

## 临时目录（Temporary Directory）到底在哪

自动保存文件和崩溃日志都写在这里。手册给的是一个**优先级顺序**，不是一个固定路径：

1. Preferences → File Paths → Data → **Temporary Files** 里设的路径（「The path must reference an existing directory or it will be ignored」，留空则用系统临时目录）；
2. 环境变量：Windows 上是 `TEMP`，其他平台是 `TMP` 和 `TMP_DIR`；
3. 都没有的话，用 `/tmp/`。

手册没有直接给出「Windows 是 C:\Users\你\AppData\Local\Temp」这类具体路径。最省事的办法是不用自己找——**直接走 File → Recover → Auto Save，那个文件浏览器打开时就已经指向正确的目录了。**

## 崩溃日志

手册：Blender 崩溃时会写一个文本文件，「Usually, this file is written in the Temporary Directory」，里面记着崩溃前用过的工具和调试信息，报 bug 时很有用。

- Windows：按当前文件名生成，`test.blend` 对应 `test.crash.txt`；
- macOS：系统的 Crash Reporter 会弹窗，`.crash` 文件也可能在 `~/Library/Logs/DiagnosticReports/` 下。

## 日常习惯上的一句话总结

Auto Save 是兜底不是保险：它有间隔、只留一份、而且在 Sculpt / Texture Paint / Edit Mode 下明写不保存改动。真正可靠的还是自己 Ctrl+S（顺便产生 `.blend1` 备份），关键节点用 File → Save Incremental（Ctrl+Alt+S，手册：「Save the current Blender file with a numerically incremented name that does not overwrite any existing files」）另存一版。
