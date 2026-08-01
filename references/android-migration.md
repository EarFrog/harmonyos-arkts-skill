# Android 到 HarmonyOS 迁移指南

## 目录

1. [适用范围](#适用范围)
2. [核心原则](#核心原则)
3. [迁移流水线](#迁移流水线)
4. [Android 项目盘点](#android-项目盘点)
5. [Spec 生成](#spec-生成)
6. [Plan 拆分](#plan-拆分)
7. [执行迁移](#执行迁移)
8. [验证与回归](#验证与回归)
9. [增量迁移](#增量迁移)
10. [产物目录建议](#产物目录建议)

---

## 适用范围

当任务涉及 Android 项目迁移到 HarmonyOS NEXT / ArkTS / ArkUI 时，优先加载本文档，并按需联动：

| 任务 | 参考文档 |
|------|---------|
| Android XML / Activity / Fragment UI 迁移 | [android-ui-mapping.md](android-ui-mapping.md) |
| Android 资源转换 | [android-resource-migration.md](android-resource-migration.md) |
| ArkUI 布局实现 | [ui-layout.md](ui-layout.md) |
| 页面路由与 Navigation | [navigation-router.md](navigation-router.md) |
| HTTP / WebSocket / 数据请求 | [network-http.md](network-http.md) |
| Preferences / RDB / 文件存储 | [storage.md](storage.md) |
| 编译错误与调试 | [troubleshooting.md](troubleshooting.md) |
| Android NDK / JNI、C/C++ 三方库 | [native-cmake-build.md](native-cmake-build.md)、[native-napi-process.md](native-napi-process.md) |
| SurfaceView / TextureView / 自定义渲染 | [native-canvas-performance.md](native-canvas-performance.md)、[native-safety.md](native-safety.md) |

本文覆盖：

- Android `Activity`、`Fragment`、`DialogFragment`、`BottomSheetDialogFragment` 页面迁移
- XML layout、menu、drawable、values 资源迁移
- Retrofit / OkHttp / WebSocket 等接口盘点
- SharedPreferences / SQLite / Room 数据层迁移
- RecyclerView、ViewPager、TabLayout、DrawerLayout、Toolbar 等常见 UI 模式迁移
- 编译、静态检查、页面覆盖率、功能验收和视觉对齐验证

本文不展开、需要转入对应专项工作流：

- Android 原生业务逻辑逐行翻译
- NDK / JNI / 自定义渲染引擎迁移；按顶层 `SKILL.md` 的 Native 工作流处理
- 三方闭源 SDK 的鸿蒙版本获取
- 已废弃或运行时不可达的 Android 死代码迁移

---

## 核心原则

### 1. 先建模，再写代码

迁移不是把 Java/Kotlin/XML 逐行改成 ArkTS。应先建立可追踪的事实模型：

1. Android 页面清单
2. 资源清单
3. 导航关系
4. 接口与数据模型清单
5. 功能验收标准
6. HarmonyOS 目标文件清单

没有清单就直接写页面，最容易漏掉二层 Fragment、Dialog、RecyclerView item、动态菜单和资源引用。

### 2. 行为同步优先于源码差集

Android 和 ArkUI 范式不同，同一个用户行为在两端的类名、文件名、组件树通常完全不同。

- UI / 业务层：同步用户可感知行为，如入口、交互、状态变化、错误提示、结果展示。
- 资源层：可以使用名称差集，如 `string` key、图片名、接口路径、权限名。
- 代码层：只把差集当线索，不把类名或 id 是否存在当作唯一结论。

### 3. 资源先行

页面迁移前先迁移资源。否则 `$r('app.media.xxx')`、`$r('app.string.xxx')`、`$r('app.color.xxx')` 缺失会导致编译失败或 UI 失真。

推荐顺序：

```text
资源扫描 → 资源转换 → 资源映射表 → 页面迁移 → 编译校验
```

### 4. 目标项目范式优先

迁移输出必须遵循目标 HarmonyOS 项目的既有风格。

- 现有项目使用 `@Component` / `@State` / `@Prop` 时，继续使用该范式。
- 现有项目使用 `@ComponentV2` / `@Local` / `@Param` 时，按 V2 范式生成。
- 不为了迁移而混用两套状态模型。
- 本 skill 当前示例默认沿用主文档中的 `@Component` / `@State` 风格；若项目已有 V2 约定，以项目为准。

### 5. 不静默留空实现

迁移代码中不要用空回调、空 `catch`、伪 `TODO` 或固定假数据伪装完成。

确实受限于三方 SDK、接口未定或资源缺失时，应在迁移报告中登记：

| 字段 | 说明 |
|------|------|
| `owner` | 谁负责补齐 |
| `location` | 文件和方法 |
| `blocked_by` | 缺少 SDK、接口、资源、账号、设备等 |
| `resolve_condition` | 什么条件满足后可清理 |
| `impact` | 对功能、编译或验证的影响 |

### 6. 每批迁移后编译

修改 HarmonyOS 应用代码后，先读取仓库 CI、脚本和当前 Hvigor 任务列表，再执行项目实际提供的 lint、test 和应用构建任务。例如项目确实提供该任务时，可以执行：

```bash
./hvigorw assembleHap
```

不要假定所有仓库都存在 `assembleHap`。编译校验只使用项目已有构建环境。禁止为了通过编译而修改 DevEco Studio、SDK、JDK、Node、ohpm、hvigor、`local.properties`、签名配置、PATH 或本机工具链。若项目没有 wrapper 或构建失败指向环境、依赖安装、签名、本机路径问题，停止修改并报告阻塞项；不要把环境问题伪装成代码修复。

编译失败时，只修复本批代码变更引入的问题，再继续下一批。

---

## 迁移流水线

推荐使用五阶段流水线：

```text
Spec → Plan → Execute → Verify → Retrospect
```

| 阶段 | 目标 | 主要产物 |
|------|------|----------|
| Spec | 盘点 Android 事实，定义迁移目标 | `ui-manifest.md`、`feature-index.md`、页面/功能 spec |
| Plan | 把目标拆成可执行批次 | `ui-plan.md`、`feature-plan.md` |
| Execute | 分批写 ArkTS / 资源 / 配置 | ArkTS 源码、资源文件、迁移报告 |
| Verify | 编译、覆盖率、功能和视觉验证 | `verify-report.md` |
| Retrospect | 沉淀错误模式和迁移决策 | `retrospect-report.md` |

### 阶段入口判断

| 当前状态 | 下一步 |
|----------|--------|
| 没有 Android 清单和 spec | 执行 Spec |
| 有 spec 但无计划 | 执行 Plan |
| 有计划但代码未落地 | 执行 Execute |
| 已落地但未验证 | 执行 Verify |
| 验证后仍有重复问题 | 执行 Retrospect |

---

## Android 项目盘点

### 必扫文件

```bash
find <android-root> -name AndroidManifest.xml | sort
find <android-root> -name build.gradle -o -name build.gradle.kts | sort
find <android-root> -path "*/res/layout*" -name "*.xml" | sort
find <android-root> -path "*/res/menu*" -name "*.xml" | sort
find <android-root> -path "*/res/values*" -name "*.xml" | sort
find <android-root> -path "*/res/drawable*" -o -path "*/res/mipmap*"
```

### 页面识别信号

必须同时识别一层和二三层 UI：

| 信号 | 常见位置 | 迁移目标 |
|------|----------|----------|
| Manifest 中的 `<activity>` | `AndroidManifest.xml` | 页面入口、Ability / NavDestination |
| `Activity` / `Fragment` 继承链 | `.java` / `.kt` | ArkUI 页面或子组件 |
| `setContentView()` / `inflate()` | Activity / Fragment | layout 源 |
| `ViewPager` / `ViewPager2` adapter | 代码和 XML | Tab 子页 |
| `FragmentTransaction.add/replace` | 代码 | 嵌套页面 |
| `DialogFragment` / `BottomSheetDialogFragment` | 代码 | 弹窗或 Sheet |
| `PopupWindow` / `PopupMenu` | 代码 | Popup / Menu |
| `RecyclerView.Adapter` item layout | Adapter | 列表项组件 |
| Navigation graph / `navigate()` | `res/navigation` 和代码 | 路由边 |

### 接口与外部通信盘点

按以下顺序扫描：

1. Retrofit service：`@GET`、`@POST`、`@Multipart`、`@Streaming`
2. OkHttp 裸请求：`OkHttpClient`、`Request.Builder`、`newCall`
3. WebSocket：`newWebSocket`、`wss://`
4. SSE / GraphQL / gRPC：按依赖和关键字识别
5. 三方 SDK：从 Gradle 依赖和调用点识别能力边界
6. 硬编码 URL 和 baseUrl 常量

输出建议：

```text
spec/baseline/api-inventory.json
spec/baseline/api-inventory.md
```

### 数据层盘点

| Android 来源 | HarmonyOS 迁移方向 |
|--------------|-------------------|
| SharedPreferences | Preferences |
| SQLiteOpenHelper | RelationalStore |
| Room Entity / DAO | RelationalStore + DAO 封装 |
| DataStore | Preferences 或文件封装 |
| 文件缓存 | 沙箱路径 + fileIo |
| LiveData / Flow | ViewModel 状态 + Promise / 事件机制 |

---

## Spec 生成

### 输出结构

建议在目标 HarmonyOS 项目根目录下建立：

```text
spec/
└── baseline/
    ├── ui-manifest.md
    ├── feature-index.md
    ├── feature-base.md
    ├── ui/
    │   ├── page_0001_MainActivity.md
    │   └── page_0002_SettingsFragment.md
    ├── features/
    │   ├── F-001-login.md
    │   └── F-002-feed-list.md
    └── resources/
        └── resource-mapping.md
```

### UI Manifest

`ui-manifest.md` 至少包含：

| 字段 | 说明 |
|------|------|
| Page ID | `page_0001_MainActivity` |
| Android 源 | Activity / Fragment / Dialog 类名 |
| layout | `res/layout/*.xml` |
| HarmonyOS 目标 | `entry/src/main/ets/pages/*.ets` |
| 优先级 | P0 / P1 / P2 |
| confidence | high / medium / low |
| 状态 | pending / converted / verified |
| 依赖 | 资源、数据、导航、子组件 |

### Confidence 评级

| 等级 | 判定 |
|------|------|
| high | 有真实截图或 UIAutomator dump，layout 和源码能互相印证 |
| medium | 无真实运行快照，但 layout、menu、style 和源码完整 |
| low | layout 缺失、动态生成 UI 多、关键业务代码不可读或三方闭源 |

### 功能 Spec

每个功能 spec 建议包含：

```markdown
# F-001 功能名

## 用户行为

## Android 证据

## HarmonyOS 目标

## 数据与接口

## 页面与组件

## 验收标准

## 阻塞项
```

验收标准必须可检查，避免“体验一致”“功能正常”这类不可执行描述。

---

## Plan 拆分

### 双计划

推荐拆成两份计划：

| 计划 | 内容 |
|------|------|
| `ui-plan.md` | 按页面优先级和依赖分批迁移 UI |
| `feature-plan.md` | 按功能依赖拓扑迁移数据层、状态、接口、页面接线 |

### UI 批次

按 P0 → P1 → P2 排序，同一优先级内 high confidence 先做。每批建议不超过 5 个页面；复杂页面单独成批。

每批完成后必须：

1. 编译
2. 更新页面状态
3. 记录缺失资源和未完成接线

### Feature Slice

每个功能切片建议拆 5 步：

1. UI 补充：页面与子组件
2. 状态管理：ViewModel / 本地状态 / 全局状态
3. 数据层接入：接口、Repository、Preferences / RDB
4. 页面接线：事件、导航、参数、错误提示
5. 切片验证：编译 + 功能验收

### 计划标注

每个任务都应标注推荐 reference：

| 任务 | 推荐 reference |
|------|----------------|
| Android XML 页面 | `android-ui-mapping.md`、`ui-layout.md` |
| 资源转换 | `android-resource-migration.md` |
| 路由 | `navigation-router.md` |
| HTTP / API | `network-http.md` |
| Preferences / RDB | `storage.md` |
| 编译错误 | `troubleshooting.md` |

---

## 执行迁移

### Stage 0: 资源前置

先扫描全部 spec 中的资源引用：

- `@string/name`
- `@color/name`
- `@dimen/name`
- `@drawable/name`
- `@mipmap/name`
- `raw/`、`font/`、`assets/`

转换后生成资源映射：

```markdown
| Android | HarmonyOS | 状态 |
|---------|-----------|------|
| @string/app_name | $r('app.string.app_name') | converted |
| @drawable/ic_back | $r('app.media.ic_back') | converted |
| @dimen/page_padding | $r('app.float.page_padding') | converted |
```

缺失资源不要静默替换为随意图标，应显式登记。

### Stage 1: UI 页面

转换页面时使用三源交叉验证：

| 来源 | 用途 |
|------|------|
| `view.xml` / 运行截图 | 真实层级、可见状态、点击区 |
| layout XML | 静态结构、style、include、资源引用 |
| Activity / Fragment 源码 | 动态显隐、点击事件、导航、Adapter |

没有运行快照时可以从 layout XML 推断，但 confidence 应降级。

### Stage 2: Base 层

先建立跨功能公共能力：

- Model / DTO
- API client / Repository
- Preferences / RDB 封装
- Event / 状态共享
- 公共组件
- 路由表
- 资源与设计 token

### Stage 3: 功能切片

按功能依赖顺序接入真实数据和交互。不要只生成页面外壳后把业务逻辑留给“后续补齐”。

### 迁移报告

每批写入：

```text
spec/migration-report.md
```

包含：

- 已迁移页面和功能
- 修改文件
- 编译状态
- 缺失资源
- 阻塞项
- 验收结果

---

## 验证与回归

### 验证清单

| 检查 | 必做项 |
|------|--------|
| 编译 | 项目实际提供的适用 Hvigor/CI 等价构建通过 |
| 静态检查 | 无 `any`、无未 catch Promise、无错误导入 |
| 页面覆盖 | P0 页面都有 ArkTS 文件和入口 |
| 资源覆盖 | `$r(...)` 都能解析 |
| 功能验收 | V1 / P0 功能验收标准通过 |
| 导航 | 页面跳转、返回、参数传递正确 |
| 数据 | 本地存储、接口错误、空态、加载态正确 |
| 视觉 | 关键页面布局、间距、颜色、文字截断可接受 |

### 页面覆盖率

对账三层：

1. Android Screen：Activity / Fragment / Dialog / Popup
2. Spec Page：`spec/baseline/ui/page_*.md`
3. ArkTS Page：`entry/src/main/ets/**/*.ets`

若 Android 有二层 Fragment 或 Dialog，而 spec 没有对应条目，应先补 spec，再补代码。

### 编译错误处理

只修复编译器报告的错误和本批引入的问题，不做无关重构，不修改编译环境。常见问题见 [troubleshooting.md](troubleshooting.md)。

---

## 增量迁移

当 Android 端新增功能或修 bug 后，不要直接比对类名差集。推荐流程：

1. 确定 Android final state：分支、commit 或本地目录
2. 提取用户可感知行为变化
3. 在 HarmonyOS 端找等价行为路径
4. 只把缺少等价路径的行为列入差异清单
5. 让用户确认差异清单
6. 为确认项生成增量 spec、plan、execute、verify

### 死代码过滤

以下 Android 代码不进入迁移清单：

- 注释代码
- `@Deprecated` 且无运行入口
- `if (false)` / 永不进入的分支
- 关闭的 feature flag
- `TODO()` / `NotImplementedError`
- 测试、demo、debug-only 页面，除非用户明确要求

### 差异清单模板

```markdown
## 增量迁移差异清单

| ID | Android 行为变化 | HarmonyOS 现状 | 结论 | 证据 |
|----|------------------|----------------|------|------|
| D-001 | 设置页新增深色模式开关 | 无等价入口 | 待迁移 | SettingsFragment + SettingsPage |
| D-002 | 列表新增空态插图 | 已实现 | 无需迁移 | EmptyView.ets |
```

---

## 产物目录建议

```text
spec/
├── baseline/
│   ├── ui-manifest.md
│   ├── feature-index.md
│   ├── feature-base.md
│   ├── api-inventory.md
│   ├── ui/
│   ├── features/
│   ├── plans/
│   │   ├── ui-plan.md
│   │   └── feature-plan.md
│   └── resources/
│       └── resource-mapping.md
├── migration-report.md
├── verify-report.md
└── retrospect-report.md
```

不要求所有项目都完整使用该目录。小项目可以只保留 `ui-manifest.md`、`feature-index.md`、`migration-report.md` 和 `verify-report.md`。
