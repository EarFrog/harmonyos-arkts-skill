---
name: harmonyos-arkts
description: >
  Develop, migrate, review, optimize, and debug HarmonyOS NEXT applications across ArkTS,
  ArkUI, and Native/NDK C/C++. Use when users mention HarmonyOS, 鸿蒙, 纯血鸿蒙, ArkTS,
  ArkUI, Android 转鸿蒙, 安卓迁移, or 鸿蒙原生开发; and for components, navigation,
  networking, storage, lib*.so imports, Node-API/N-API bridges, CMake/Hvigor, XComponent,
  NativeWindow, OpenGL ES, Native Drawing, async work, lifecycle and thread safety, native
  persistence and image export, build/load failures, crashes, or performance problems.
---

# HarmonyOS NEXT 开发助手

## 工作原则

1. 先读取目标仓库约束、目标 API/SDK 版本、模块配置、既有代码范式和验证命令。
2. 以目标仓库、匹配版本的本地 SDK 和华为官方文档为事实来源；示例只提供模式，不覆盖项目与官方契约。
3. 先确认活跃调用链，再修改代码。区分正在使用的实现、生成代码、兼容回退、派生缓存、实验路径和失活代码。
4. 按任务类型只加载相关 reference；不要为无状态、无图形或无 Native 的任务引入额外架构。
5. 实施最小但完整的跨层修改，保持 ArkTS、Native、构建配置、资源、声明和调用方一致。
6. 修改后按风险验证；只修复本次变更引入的问题，不借机修改无关代码或本机编译环境。

## 任务路由

### ArkTS 与 ArkUI

当任务主要涉及 `.ets`、声明式 UI、状态管理、Navigation、网络、存储、权限或普通应用排障时：

1. 根据任务读取 ArkTS/ArkUI reference。
2. 遵循目标项目已有的 V1 或 V2 状态管理范式，不主动混用。
3. 修改后运行项目实际提供的 lint、test 和 Hvigor 构建任务。

### HarmonyOS Native 与 NDK

当出现以下任一信号时进入 Native 工作流：

- `src/main/cpp`、`CMakeLists.txt`、`externalNativeOptions`、ABI 或三方 C/C++ 库。
- `lib*.so` import、`napi_init.cpp`、`NAPI_MODULE`、`napi_module_register` 或 `napi_property_descriptor`。
- `types/lib*/index.d.ts`、ArkTS Native facade、ArrayBuffer、TypedArray 或跨语言 callback。
- XComponent、NativeWindow、Native Drawing、EGL、GLES、Surface、renderer 或 Native crash。

先把 `SKILL_ROOT` 解析为当前 `SKILL.md` 所在目录，再运行 bundled 只读静态审计。不要从目标仓库解析脚本路径，也不要执行目标仓库中的同名脚本：

```bash
SKILL_ROOT="/absolute/path/to/harmonyos-arkts"
python3 "$SKILL_ROOT/scripts/audit_harmony_native.py" <project-root>
```

再建立以下调用链：

```text
ArkTS import/facade
  → 类型声明
  → Native 注册与导出
  → CMake SHARED target
  → lib<target>.so 与目标 ABI
```

写出参数、返回值、异常、单位、范围、二进制布局、内存所有权、线程所有权和销毁顺序，然后按场景读取 Native reference。

### Android 到 HarmonyOS 迁移

先读取 [android-migration.md](references/android-migration.md)，按 `Spec → Plan → Execute → Verify → Retrospect` 推进。

- 迁移资源时读取 [android-resource-migration.md](references/android-resource-migration.md)。
- 迁移 Activity、Fragment、XML、RecyclerView、Dialog 或导航时读取 [android-ui-mapping.md](references/android-ui-mapping.md)。
- 遇到 Android NDK/JNI、SurfaceView、TextureView、自定义渲染、二进制协议或 C/C++ 三方库时，同时进入 Native 工作流。
- 迁移结果遵循目标 HarmonyOS 项目现有架构，不逐行翻译 Android 源码，不静默留下空实现。

### 跨层任务

ArkTS 页面调用 Native、XComponent 驱动渲染、Native Promise 回传 UI、Native 持久化或 Android 自绘迁移属于跨层任务。至少核对：

| 层 | 核对项 |
| --- | --- |
| ArkTS/UI | 状态、生命周期、调用频率、错误展示、取消和页面复用 |
| 类型契约 | 导出名、参数、返回、Promise/callback、ArrayBuffer stride/端序/上限 |
| Native | 注册、参数校验、异常、所有权、线程、幂等销毁 |
| 构建 | CMake target、源文件、系统库、三方库、ABI、HAP/HAR/HSP 打包 |
| 图形/数据 | Surface/context、事实源、派生 cache、持久化版本和失效条件 |

## ArkTS 与 ArkUI 核心约束

- 使用完整类型，不使用 `any`，不在 `build()` 中执行网络请求、定时器或其他副作用。
- 按作用域和同步方向选择状态：组件内使用 `@State`，父子单向使用 `@Prop` 或普通参数，双向使用 `@Link`，跨层级使用 `@Provide`/`@Consume`，复杂对象深层观察使用 `@Observed` + `@ObjectLink`。
- 涉及时间戳、耗时、超时和排序时，使用 `systemDateTime.getTime()`，不使用 `Date.now()` 或 `new Date()`。
- 处理 Promise 时建立明确的成功、失败和清理路径；调用方不得静默丢弃 rejection。
- 调用 SDK API 时，先把 options/record 对象声明为对应 SDK interface 类型，再传入 API，避免未类型化对象字面量。
- 优先使用具体源码或官方具体模块入口，不为方便而打开无关聚合入口。
- ArkUI 布局默认使用 vp；Canvas、PixelMap、截图、屏幕物理尺寸和 Native 明确要求时才使用 px。先确认单位，再通过当前 `UIContext` 转换。
- ArkTS/ArkUI 新增或重排的续行使用 4 个空格；修改已有代码时保持最小范围一致。
- 不把耗时工作笼统塞进 UI 线程、taskpool 或 Worker。先确认任务使用的数据和资源是否允许跨线程。

详细规则读取 [arkts-syntax.md](references/arkts-syntax.md)。

## Native 核心约束

- 必填参数同时校验 `napi_get_cb_info` 状态、实收数量、类型、有限数值、范围和业务不变量；解析失败时 throw/reject。
- 只有 Node-API 调用返回 `napi_ok` 后才使用输出参数，不让 helper 吞掉 status、参数或 pending exception。
- `napi_env`、`napi_value` 和 JS object 只在所属 JS 线程和有效 scope 使用。async `execute` 只处理拥有明确所有权的 Native 数据，在 `complete` 中创建 JS 值并 settle Promise。
- 为 EGL/GL、ArkUI node、Surface 和设备资源定义固定 owner thread 或官方允许的线程协议。mutex 只能互斥，不能改变线程亲和性。
- 为 ArrayBuffer/TypedArray 定义 stride、端序、长度上限和所有权。只有 Native 在 callback 返回前同步消费或复制数据时，ArkTS 才能立即复用 buffer。
- 把业务事实源与 GPU、索引、缩略图等派生 cache 分离；cache 必须可失效、可校验、可重建。
- 让 Surface、session、renderer、async work、reference、文件和图形资源的关闭幂等，并覆盖销毁、复用、取消、异常和环境退出。
- 性能修改必须有基线、瓶颈证据和目标设备复测；不把 ArrayBuffer、GPU、缓存或多线程本身当作收益证明。

## Reference 索引

### ArkTS、ArkUI 与应用能力

| 场景 | Reference |
| --- | --- |
| ArkTS 语法、类型、装饰器、生命周期、Promise、编码和性能规范 | [arkts-syntax.md](references/arkts-syntax.md) |
| UI 布局、动画、手势和尺寸单位 | [ui-layout.md](references/ui-layout.md) |
| Router、Navigation 和 Tab 组合 | [navigation-router.md](references/navigation-router.md) |
| HTTP、上传下载和 WebSocket | [network-http.md](references/network-http.md) |
| Preferences、RelationalStore 和文件存储 | [storage.md](references/storage.md) |
| 模块、包、资源和源码结构 | [project-structure.md](references/project-structure.md) |
| ArkTS/UI 编译、运行、权限和真机排障 | [troubleshooting.md](references/troubleshooting.md) |

### Android 迁移

| 场景 | Reference |
| --- | --- |
| 项目盘点、Spec、Plan、增量迁移和验证 | [android-migration.md](references/android-migration.md) |
| Activity、Fragment、XML、RecyclerView、Dialog 和导航映射 | [android-ui-mapping.md](references/android-ui-mapping.md) |
| values、drawable、mipmap、raw、font、多语言和 qualifier | [android-resource-migration.md](references/android-resource-migration.md) |

### Native 契约、构建与安全

| 场景 | Reference |
| --- | --- |
| 现有 Native 工程审查和高频风险入口 | [native-engineering-lessons.md](references/native-engineering-lessons.md) |
| Node-API 注册、参数、导出和声明同步 | [native-napi-process.md](references/native-napi-process.md) |
| ArkTS facade、类型、二进制协议和异步选择 | [native-arkts-interop.md](references/native-arkts-interop.md) |
| 生命周期、线程、内存、锁和错误处理 | [native-safety.md](references/native-safety.md) |
| CMake、Hvigor、ABI、系统库和三方库 | [native-cmake-build.md](references/native-cmake-build.md) |
| 编译、加载、黑屏、花屏、崩溃和性能排障 | [native-debugging.md](references/native-debugging.md) |
| API 行为、版本差异和官方资料入口 | [native-official-node-api-guide.md](references/native-official-node-api-guide.md) |

### Native 状态、渲染与持久化

| 场景 | Reference |
| --- | --- |
| XComponent、Native Drawing、GLES、手写和画布性能 | [native-canvas-performance.md](references/native-canvas-performance.md) |
| handle、事实源、高频事件协议和多后端状态 | [native-architecture-patterns.md](references/native-architecture-patterns.md) |
| 增量渲染、瓦片、GLES、资源复用和持久画布 | [native-rendering-architecture.md](references/native-rendering-architecture.md) |
| 二进制持久化、派生缓存、图片导出和任务调度 | [native-persistence-export-scheduling.md](references/native-persistence-export-scheduling.md) |

只加载与当前任务相关的文件。需要审查复杂现有 Native 工程时，先读 `native-engineering-lessons.md`，再沿命中的风险加载详细 reference。

## 验证

按风险逐级执行：

1. 运行静态检查，确认 ArkTS、声明、注册、CMake 和 `.so` 调用链一致。
2. 运行仓库已有 lint、test、Native 模块构建和 CI 等价命令。
3. 查询当前项目实际提供的 Hvigor 任务，再运行适用的应用构建；不要假定一定存在 `./hvigorw assembleHap`。
4. 不为通过验证而修改 DevEco、SDK、JDK、Node、ohpm、Hvigor、PATH、`local.properties`、签名或本机缓存。
5. 在目标 ABI 真机验证权限、页面生命周期、前后台、组件复用、Surface 重建、取消和异常路径。
6. 图形或性能变更比较改动前后的输入延迟、帧耗时分位数、主线程阻塞、锁等待、内存峰值、缓存行为和导出耗时。

若环境、依赖安装、签名、设备或本机路径阻塞验证，停止修改环境并明确报告已完成和未完成的验证层级。
