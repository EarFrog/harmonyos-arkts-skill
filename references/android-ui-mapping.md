# Android UI 到 ArkUI 映射

## 目录

1. [迁移输入](#迁移输入)
2. [页面发现](#页面发现)
3. [布局容器映射](#布局容器映射)
4. [控件映射](#控件映射)
5. [属性映射](#属性映射)
6. [列表与 Adapter](#列表与-adapter)
7. [导航与页面栈](#导航与页面栈)
8. [弹窗与浮层](#弹窗与浮层)
9. [交互与手势](#交互与手势)
10. [样式与主题](#样式与主题)
11. [常见陷阱](#常见陷阱)
12. [页面迁移检查清单](#页面迁移检查清单)

---

## 迁移输入

单个页面迁移时，优先收集三类输入：

| 输入 | 用途 |
|------|------|
| 运行时层级 / 截图 | 真实可见状态、点击区、滚动区、弹窗状态 |
| layout XML / menu XML / style XML | 静态结构、资源引用、style、include |
| Activity / Fragment / Adapter 源码 | 动态逻辑、点击事件、导航、数据绑定 |

只有 layout XML 时可以迁移静态 UI，但 confidence 应标为 `medium` 或 `low`。

---

## 页面发现

### 必须识别的 UI 单元

| Android 类型 | ArkUI 目标 |
|--------------|------------|
| Activity | 入口页面或 NavDestination |
| Fragment | NavDestination、Tab 内容或子组件 |
| DialogFragment | CustomDialog / Dialog 组件 |
| BottomSheetDialogFragment | Sheet / 半屏弹窗 |
| PopupWindow / PopupMenu | Popup / Menu / 自定义浮层 |
| RecyclerView item | 列表项组件 |
| ViewHolder | 列表项状态和事件绑定 |
| ViewPager page | Tab 子页或 Swiper 内容 |
| include layout | 公共组件或局部 Builder |

### 二三层页面信号

迁移时特别容易漏掉这些页面：

- `ViewPager` / `ViewPager2` adapter 中返回的 Fragment
- `TabLayout` 绑定的分页 Fragment
- `FragmentTransaction.replace()` / `add()` 动态加载的 Fragment
- `DialogFragment.show()`
- `BottomSheetBehavior`
- `PopupWindow` 引用的 layout
- `RecyclerView.Adapter.onCreateViewHolder()` inflate 的 item layout
- Navigation graph 中的 destination

漏识别这些 UI 单元会导致 P0 页面“看起来迁了”，实际点击后缺子页、缺弹窗、缺列表项。

---

## 布局容器映射

| Android | ArkUI | 备注 |
|---------|-------|------|
| `LinearLayout vertical` | `Column` | `orientation="vertical"` |
| `LinearLayout horizontal` | `Row` | `orientation="horizontal"` |
| `FrameLayout` | `Stack` | 处理层叠和占位容器 |
| `RelativeLayout` | `Stack` + 对齐 / `Column` / `Row` | 不要机械全转 Stack，先判断实际结构 |
| `ConstraintLayout` | `Column` / `Row` / `Stack` 组合 | 优先还原视觉关系，不逐条翻约束 |
| `CoordinatorLayout` | `Stack` + 滚动联动 | AppBar / BottomSheet 需单独处理 |
| `ScrollView` | `Scroll` | 单方向滚动 |
| `NestedScrollView` | `Scroll` | 注意嵌套滚动和吸顶 |
| `HorizontalScrollView` | `Scroll` + `.scrollable(ScrollDirection.Horizontal)` | 横向滚动 |
| `RecyclerView` | `List` / `Grid` / `WaterFlow` | 依据 LayoutManager |
| `ViewPager` / `ViewPager2` | `Tabs` / `Swiper` | 有 tab 时优先 Tabs |
| `DrawerLayout` | 侧栏布局 / Navigation 分栏 | 依据目标设计 |
| `BottomNavigationView` | `Tabs` 或自定义底部栏 | 与 Navigation 组合 |

### layout_weight

Android：

```xml
<TextView
    android:layout_width="0dp"
    android:layout_height="wrap_content"
    android:layout_weight="1" />
```

ArkUI：

```typescript
Text(this.title)
    .layoutWeight(1)
```

### match_parent / wrap_content

| Android | ArkUI |
|---------|-------|
| `match_parent` | `.width('100%')` / `.height('100%')` |
| `wrap_content` | 通常省略尺寸 |
| `0dp + weight` | `.layoutWeight(n)` |
| 固定 `dp` | 固定 `vp`，如 `.width(48)` |

---

## 控件映射

| Android | ArkUI | 备注 |
|---------|-------|------|
| `TextView` | `Text` | 文本、颜色、字号、行数、截断 |
| `EditText` | `TextInput` / `TextArea` | 单行用 TextInput，多行用 TextArea |
| `Button` | `Button` | 复杂按钮可用 Row + Text + Image |
| `ImageView` | `Image` | 资源、网络图、objectFit |
| `CheckBox` | `Checkbox` | checked 状态绑定 |
| `RadioButton` | `Radio` | 组状态需自管 |
| `Switch` | `Toggle` / `Switch` | 按项目组件库选择 |
| `ProgressBar` | `Progress` / `LoadingProgress` | 不确定进度用 LoadingProgress |
| `SeekBar` | `Slider` | 音视频进度常用 |
| `RatingBar` | 自定义组件 | Row + Symbol / Image |
| `Toolbar` | 自定义标题栏 / Navigation title | 优先复用项目标题栏 |
| `SearchView` | `Search` | 绑定输入和提交事件 |
| `WebView` | `Web` | 需要 controller 和权限 |
| `SurfaceView` / `TextureView` | `XComponent` | 视频、相机、自绘场景；同时进入 Native 生命周期与渲染工作流 |

---

## 属性映射

### 文本

| Android | ArkUI |
|---------|-------|
| `android:text` | `Text(value)` |
| `android:textColor` | `.fontColor()` |
| `android:textSize="14sp"` | `.fontSize(14)` 或 `$r('app.float.xxx')` |
| `android:textStyle="bold"` | `.fontWeight(FontWeight.Bold)` |
| `android:gravity="center"` | `.textAlign(TextAlign.Center)` + 容器对齐 |
| `android:maxLines` | `.maxLines()` |
| `android:ellipsize="end"` | `.textOverflow({ overflow: TextOverflow.Ellipsis })` |

### 图片

| Android | ArkUI |
|---------|-------|
| `android:src` | `Image($r('app.media.xxx'))` |
| `android:scaleType="centerCrop"` | `.objectFit(ImageFit.Cover)` |
| `android:scaleType="fitCenter"` | `.objectFit(ImageFit.Contain)` |
| `android:tint` | `.fillColor()` 或使用 SVG / Symbol |
| `contentDescription` | 无障碍文本 |

### 间距

| Android | ArkUI |
|---------|-------|
| `padding` | `.padding()` |
| `layout_margin` | `.margin()` |
| `layout_gravity` | 父容器 `.alignItems()` / 子组件对齐 |
| `gravity` | 容器内容布局或 Text 对齐 |

尺寸单位默认 `dp → vp`、`sp → fp`。从截图 bounds 得到的是 px，必须先确认设备密度或用当前 UIContext 转换，不要把 px 直接当 vp。

---

## 列表与 Adapter

### RecyclerView 迁移决策

| Android LayoutManager | ArkUI |
|-----------------------|-------|
| `LinearLayoutManager vertical` | `List` |
| `LinearLayoutManager horizontal` | 横向 `List` 或 `Scroll + Row` |
| `GridLayoutManager` | `Grid` |
| `StaggeredGridLayoutManager` | `WaterFlow` |

### Adapter 拆解

Android Adapter 至少拆成：

1. 数据模型
2. 列表项组件
3. item key
4. 点击 / 长按事件
5. 空态 / 加载态 / 错误态
6. 分页或刷新逻辑

ArkUI 示例：

```typescript
interface IFeedItem {
    id: string
    title: string
    cover: Resource
}

@Component
struct FeedItemCard {
    item: IFeedItem
    onItemClick: (id: string) => void = () => {}

    build() {
        Row({ space: 12 }) {
            Image(this.item.cover)
                .width(64)
                .height(64)
                .borderRadius(8)
            Text(this.item.title)
                .fontSize(16)
                .layoutWeight(1)
                .maxLines(2)
                .textOverflow({ overflow: TextOverflow.Ellipsis })
        }
        .width('100%')
        .padding(12)
        .onClick(() => {
            this.onItemClick(this.item.id)
        })
    }
}
```

注意：列表项不要在 `build()` 中发起网络请求；分页、刷新、缓存应放到页面状态或 ViewModel。

---

## 导航与页面栈

| Android | ArkUI |
|---------|-------|
| `startActivity()` | `router.pushUrl()` 或 `NavPathStack.pushPathByName()` |
| `finish()` | `router.back()` 或 `pathStack.pop()` |
| `Intent extra` | 路由 params |
| `startActivityForResult()` | 回调 / 全局状态 / 事件机制 |
| `FragmentTransaction` | `Navigation` / 条件渲染 / Tabs |
| Navigation Component | `Navigation` + `NavDestination` |
| Deep Link | `Want` / router 参数 / 应用路由表 |

新项目优先使用 [navigation-router.md](navigation-router.md) 中的 `Navigation` 方案；如果目标项目已使用 `router.pushUrl()`，遵循现有项目约定。

迁移时要保留：

- 入口页
- 返回行为
- 参数名和默认值
- 登录拦截
- 外部 Intent / scheme 跳转
- Tab 和 Drawer 的互斥关系

---

## 弹窗与浮层

| Android | ArkUI |
|---------|-------|
| `AlertDialog` | `AlertDialog` / `CustomDialog` |
| `DialogFragment` | `CustomDialog` 或独立组件 |
| `BottomSheetDialogFragment` | 半屏弹窗 / Sheet 组件 |
| `PopupWindow` | `Popup` / `bindPopup` / 自定义 Stack 浮层 |
| `Toast` | `promptAction.showToast()` |
| `Snackbar` | 自定义底部提示条 |
| `DatePickerDialog` | `DatePicker` + Dialog |

弹窗迁移时必须记录：

- 触发入口
- 标题、正文、按钮
- 确认 / 取消回调
- 点击外部是否关闭
- 返回键行为
- 键盘避让
- 安全区避让

---

## 交互与手势

| Android | ArkUI |
|---------|-------|
| `setOnClickListener` | `.onClick()` |
| `setOnLongClickListener` | `LongPressGesture()` |
| `OnTouchListener` | `.onTouch()` 或手势组合 |
| `GestureDetector` | `TapGesture` / `PanGesture` / `PinchGesture` |
| `SwipeRefreshLayout` | `Refresh` |
| `ItemTouchHelper` | 手势 + 列表状态 |
| `TextWatcher` | `TextInput.onChange()` |
| `OnCheckedChangeListener` | checked 状态回调 |

不要把所有 `onClick` 都留空。若业务尚未迁移，应登记接线 owner 和 resolve 条件。

---

## 样式与主题

### Style 解析

Android style 迁移时，先提取语义：

| style 字段 | HarmonyOS |
|------------|-----------|
| `colorPrimary` | 品牌色资源 |
| `textColorPrimary` | 文本色资源 |
| `windowLightStatusBar` | 状态栏前景色 |
| `fontFamily` | 字体资源或系统字体 |
| `buttonStyle` | 公共按钮组件 |

不要把 `styles.xml` 原样搬进 HarmonyOS。应沉淀成：

- `color.json`
- `float.json`
- 公共组件
- `DesignTokens.ets` 或项目已有 token 文件

### 深色模式

Android `values-night` 迁移到 HarmonyOS `dark/element`。同一资源在 `base` 和 `dark` 中保持同名。

### 安全区

Android 依赖系统 decor fitting 的页面，迁移到 ArkUI 后要显式处理：

- 背景是否延伸到系统栏
- 前景内容是否避开状态栏 / 导航条 / 键盘
- 横屏和折叠屏下是否遮挡

---

## 常见陷阱

### 1. 只迁 Activity，漏 Fragment

现象：首屏能打开，点击 Tab、列表项或按钮后页面缺失。

处理：扫描 ViewPager、FragmentTransaction、Navigation graph、DialogFragment。

### 2. RecyclerView 只迁容器，漏 item layout

现象：列表空白或所有行长得一样。

处理：读取 Adapter 的 `onCreateViewHolder()`，迁移每种 viewType 的 item layout。

### 3. 只按截图 bounds 生成固定尺寸

现象：换设备后错位、挤压。

处理：优先还原布局关系，固定尺寸只用于图标、头像、按钮等明确元素。

### 4. Android selector 丢状态

现象：点击态、选中态、禁用态消失。

处理：用 ArkUI 状态变量、`.enabled()`、`.stateStyles()` 或条件样式恢复。

### 5. `sp` 误当 `vp`

现象：字体缩放、大字体模式下文本截断。

处理：文本尺寸用 fp 语义，容器尺寸用 vp，必要时设置 `maxLines` 和自适应布局。

### 6. 资源引用未转换

现象：编译报 unknown resource，或运行时图片不显示。

处理：先迁资源并维护 `resource-mapping.md`。

### 7. WebView / SurfaceView 机械替换

现象：页面白屏、视频无画面、JS 回调不通。

处理：WebView 需要 controller、权限和 JSBridge；SurfaceView / TextureView 需要 XComponent 和 Surface 生命周期，并读取 [native-canvas-performance.md](native-canvas-performance.md) 与 [native-safety.md](native-safety.md)。

### 8. 空态、错误态、加载态被漏掉

现象：正常数据能显示，断网、空列表、接口错误时体验异常。

处理：从 Android 代码中的 `onError`、`catch`、`emptyView`、`ProgressBar` 显隐逻辑提取状态。

---

## 页面迁移检查清单

每个页面完成后检查：

- Android 页面、layout、style、menu、adapter 来源都已记录
- 资源引用已映射到 `$r('app.*.*')`
- 页面标题、返回、右侧操作、Tab / Drawer 状态正确
- 列表 item、空态、加载态、错误态齐全
- 弹窗、Toast、Popup、BottomSheet 已迁移或登记阻塞
- 点击、长按、刷新、搜索、筛选、排序行为已接线
- 导航参数、返回行为、登录拦截正确
- Promise 调用已 catch
- 没有 `any`、空 `catch`、假 TODO
- 修改后已运行项目实际提供的适用 Hvigor/CI 等价构建
- 编译校验只使用项目已有构建环境，不为通过编译修改 DevEco/SDK/JDK/Node/ohpm/hvigor、`local.properties`、签名配置、PATH 或本机工具链

页面报告模板：

```markdown
# Page Migration Report

## Source

- Android: `MainActivity`
- Layout: `res/layout/activity_main.xml`
- Adapter: `FeedAdapter`
- Menu: `res/menu/main.xml`

## Target

- ArkTS: `entry/src/main/ets/pages/MainPage.ets`
- Components:
  - `FeedItemCard.ets`

## Coverage

| 项 | 状态 | 备注 |
|----|------|------|
| 静态布局 | PASS | |
| 资源 | PASS | |
| 列表项 | PASS | 2 viewTypes |
| 导航 | PASS | |
| 弹窗 | BLOCKED | 等支付 SDK |

## Build

- Command: `<project-build-command>`
- Result: PASS
```
