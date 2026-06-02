# ArkUI 布局最佳实践

## 目录

1. [布局容器概览](#布局容器概览)
2. [Column / Row](#column--row)
3. [List](#list)
4. [Grid](#grid)
5. [Scroll / Tabs](#scroll--tabs)
6. [弹窗与浮层](#弹窗与浮层)
7. [尺寸与间距规范](#尺寸与间距规范)
8. [动画系统](#动画系统)
9. [手势交互](#手势交互)
10. [性能优化](#性能优化)

---

## 布局容器概览

| 容器 | 适用场景 | 核心属性 |
|------|---------|---------|
| `Column` | 垂直排列 | `.space()`, `.justifyContent()`, `.alignItems()` |
| `Row` | 水平排列 | 同上 |
| `Stack` | 层叠定位 | `.alignContent()` |
| `Flex` | 弹性布局 | `.direction()`, `.wrap()`, `.justifyContent()` |
| `List` | 滚动列表 | `.lazyForEach()`, `.cachedCount()` |
| `Grid` | 网格布局 | `.columnsTemplate()`, `.rowsTemplate()` |
| `Scroll` | 可滚动区域 | `.scrollable()`, `.scrollBar()` |
| `Tabs` | 标签页 | `.tabBar()`, `.scrollable()` |
| `Swiper` | 轮播 | `.autoPlay()`, `.interval()` |
| `WaterFlow` | 瀑布流 | `.columnsTemplate()`, `.layoutDirection()` |

---

## Column / Row

### Column 垂直布局

```typescript
Column() {
    Text('标题').fontSize(20).fontWeight(FontWeight.Bold)
    Text('描述内容').fontSize(14).fontColor('#666666')
    Button('操作')
}
.width('100%')
.padding(16)
.backgroundColor('#FFFFFF')
.borderRadius(12)
```

### Row 水平布局

```typescript
Row() {
    Image($r('app.media.icon')).width(40).height(40).borderRadius(20)
    Column({ space: 4 }) {
        Text('用户名').fontSize(16).fontWeight(FontWeight.Medium)
        Text('一句话简介').fontSize(12).fontColor('#999999')
    }
    .alignItems(HorizontalAlign.Start)
    .layoutWeight(1)  // 占据剩余空间
    Blank()
    Image($r('app.media.arrow_right')).width(16).height(16)
}
.width('100%')
.padding(12)
.backgroundColor('#FFFFFF')
.borderRadius(8)
```

### 等分布局

```typescript
Row({ space: 12 }) {
    Text('左').layoutWeight(1).textAlign(TextAlign.Center).backgroundColor('#F0F0F0')
    Text('中').layoutWeight(1).textAlign(TextAlign.Center).backgroundColor('#F0F0F0')
    Text('右').layoutWeight(1).textAlign(TextAlign.Center).backgroundColor('#F0F0F0')
}
.width('100%')
.padding(16)

// 或者用 justifyContent
Row() {
    Text('左').width('30%')
    Text('中').width('30%')
    Text('右').width('30%')
}
.width('100%')
.justifyContent(FlexAlign.SpaceEvenly)
```

### space 间距

```typescript
// Column 内子元素间距
Column({ space: 8 }) {
    Text('A')
    Text('B')
    Text('C')
}

// Row 内子元素间距
Row({ space: 12 }) {
    Text('X')
    Text('Y')
    Text('Z')
}
```

---

## List

### 基础列表

```typescript
@State dataList: string[] = ['项目A', '项目B', '项目C', '项目D']

build() {
    List({ space: 10 }) {
        ForEach(this.dataList, (item: string, index?: number) => {
            ListItem() {
                Text(item).width('100%').padding(16).backgroundColor('#FFFFFF')
            }
            .borderRadius(8)
        }, (item: string, index?: number) => `${item}_${index}`)
    }
    .width('100%')
    .layoutWeight(1)
    .padding({ left: 16, right: 16 })
    .divider({ strokeWidth: 0.5, color: '#EEEEEE' })
}
```

### 分组列表

```typescript
interface IGroup {
    title: string
    items: string[]
}

@State groups: IGroup[] = [
    { title: '分组一', items: ['A1', 'A2'] },
    { title: '分组二', items: ['B1', 'B2', 'B3'] }
]

build() {
    List() {
        ForEach(this.groups, (group: IGroup) => {
            ListItemGroup({ header: this.groupHeader(group.title) }) {
                ForEach(group.items, (item: string) => {
                    ListItem() {
                        Text(item).width('100%').padding(16).backgroundColor('#FFFFFF')
                    }
                }, (item: string) => item)
            }
        }, (group: IGroup) => group.title)
    }

    @Builder
    groupHeader(title: string) {
        Text(title).fontSize(14).fontColor('#666666').padding({ left: 16, top: 12, bottom: 4 })
    }
}
```

### 懒加载（大数据量）

```typescript
import { LazyForEach } from '@kit.ArkUI'

class MyDataSource implements IDataSource {
    private dataArray: string[] = []
    private listeners: DataChangeListener[] = []

    constructor(data: string[]) {
        this.dataArray = data
    }

    totalCount(): number {
        return this.dataArray.length
    }

    getData(index: number): string {
        return this.dataArray[index]
    }

    registerDataChangeListener(listener: DataChangeListener): void {
        this.listeners.push(listener)
    }

    unregisterDataChangeListener(listener: DataChangeListener): void {
        const pos = this.listeners.indexOf(listener)
        if (pos >= 0) {
            this.listeners.splice(pos, 1)
        }
    }
}

@Entry
@Component
struct LazyListDemo {
    private dataSource: MyDataSource = new MyDataSource(Array.from({ length: 1000 }, (_, i) => `Item ${i}`))

    build() {
        List() {
            LazyForEach(this.dataSource, (item: string) => {
                ListItem() {
                    Text(item).width('100%').height(60).textAlign(TextAlign.Center)
                }
            }, (item: string) => item)
        }
        .cachedCount(5)  // 缓存屏幕外 5 个 item
    }
}
```

### 下拉刷新 / 上拉加载

```typescript
@Entry
@Component
struct RefreshList {
    @State dataList: string[] = ['A', 'B', 'C']
    @State refreshing: boolean = false

    build() {
        Refresh({ refreshing: $$this.refreshing }) {
            List({ space: 10 }) {
                ForEach(this.dataList, (item: string) => {
                    ListItem() {
                        Text(item).width('100%').padding(16).backgroundColor('#FFFFFF').borderRadius(8)
                    }
                }, (item: string) => item)
            }
            .width('100%')
            .layoutWeight(1)
            .onReachEnd(() => {
                // 上拉加载更多
                this.dataList.push(...['D', 'E', 'F'])
            })
        }
        .onRefreshing(() => {
            // 下拉刷新逻辑
            setTimeout(() => {
                this.dataList = ['A', 'B', 'C']
                this.refreshing = false  // 停止刷新
            }, 1000)
        })
        .refreshColor('#007DFF')
    }
}
```

---

## Grid

### 基础网格

```typescript
Grid() {
    ForEach(this.items, (item: string) => {
        GridItem() {
            Text(item).width('100%').height(60).textAlign(TextAlign.Center)
                .backgroundColor('#FFFFFF').borderRadius(8)
        }
    })
}
.columnsTemplate('1fr 1fr 1fr')  // 三列等宽
.rowsGap(10)
.columnsGap(10)
.width('100%')
.padding(16)
```

### 自适应列数

```typescript
Grid() {
    ForEach(this.items, (item: string) => {
        GridItem() {
            Text(item).width('100%').height(100).backgroundColor('#F5F5F5')
        }
    })
}
.columnsGap(10)
.rowsGap(10)
.maxCount(3)    // 最大 3 列
.minCount(2)    // 最小 2 列
.layoutDirection(GridDirection.Row)
```

---

## Scroll / Tabs

### Scroll

```typescript
Scroll() {
    Column() {
        Text('长内容区域').width('100%').height(800).backgroundColor('#F0F0F0')
    }
}
.scrollable(ScrollDirection.Vertical)  // 垂直滚动
.scrollBar(BarState.Auto)              // 滚动条自动显隐
.edgeEffect(EdgeEffect.Spring)         // iOS 风格回弹
```

### Tabs

```typescript
@Entry
@Component
struct TabsDemo {
    @State currentIndex: number = 0

    build() {
        Tabs({ barPosition: BarPosition.Start, index: this.currentIndex }) {
            TabContent() { Text('首页内容') }.tabBar(this.tabBuilder('首页', 0))
            TabContent() { Text('分类内容') }.tabBar(this.tabBuilder('分类', 1))
            TabContent() { Text('我的内容') }.tabBar(this.tabBuilder('我的', 2))
        }
        .onChange((index: number) => { this.currentIndex = index })
    }

    @Builder
    tabBuilder(title: string, index: number) {
        Column() {
            Text(title)
                .fontSize(this.currentIndex === index ? 16 : 14)
                .fontWeight(this.currentIndex === index ? FontWeight.Bold : FontWeight.Normal)
                .fontColor(this.currentIndex === index ? '#007DFF' : '#999999')
        }
        .width('100%')
        .padding({ top: 8, bottom: 8 })
        .alignItems(HorizontalAlign.Center)
    }
}
```

---

## 弹窗与浮层

### CustomDialog

```typescript
@CustomDialog
struct ConfirmDialog {
    controller: CustomDialogController
    title: string = '提示'
    message: string = ''
    onConfirm?: () => void

    build() {
        Column({ space: 12 }) {
            Text(this.title).fontSize(18).fontWeight(FontWeight.Bold)
            Text(this.message).fontSize(14).fontColor('#666666')
            Row({ space: 12 }) {
                Button('取消').onClick(() => this.controller.close())
                    .backgroundColor('#F5F5F5').fontColor('#333333')
                Button('确定').onClick(() => {
                    this.onConfirm?.()
                    this.controller.close()
                })
            }
        }
        .padding(24)
        .backgroundColor('#FFFFFF')
        .borderRadius(16)
    }
}

// 使用
let dialog = new CustomDialogController({
    builder: ConfirmDialog({ title: '删除确认', message: '确定删除该项？', onConfirm: () => {} })
})
dialog.open()
```

### 半屏模态

```typescript
@Entry
@Component
struct SheetDemo {
    @State showSheet: boolean = false

    build() {
        Button('打开半屏').onClick(() => { this.showSheet = true })
            .bindSheet($$this.showSheet, this.sheetBuilder(), {
                height: SheetSize.MEDIUM,
                showClose: true,
                dragBar: true,
                backgroundColor: '#FFFFFF'
            })
    }

    @Builder
    sheetBuilder() {
        Column({ space: 16 }) {
            Text('选择操作').fontSize(18).fontWeight(FontWeight.Bold)
            // ...内容
        }
        .padding(24)
    }
}
```

---

## 尺寸与间距规范

### 推荐间距

| 场景 | 间距 |
|------|------|
| 页面内边距 | 16vp |
| 卡片内边距 | 16vp |
| 列表项间距 | 8-12vp |
| 元素内部间距 | 4-8vp |
| 按钮最小高度 | 44vp |
| 点击热区最小 | 44x44vp |
| 圆角 - 卡片 | 12vp |
| 圆角 - 按钮 | 8vp |
| 圆角 - 头像 | 半径 |
| 圆角 - 输入框 | 8vp |

### 响应式尺寸

```typescript
// 使用 vp（虚拟像素，自动适配不同屏幕密度）
.width('100%')
.height(44)
.padding(16)
.fontSize(14)

// 获取屏幕尺寸
import { display } from '@kit.ArkUI'
let displayClass = display.getDefaultDisplaySync()
let screenWidth = displayClass.width  // px
let screenHeight = displayClass.height

// vp 转 px
let pxValue = 16  // vp
// 1vp = displayClass.densityPixels * 1 px
```

### px / vp 转换规则

- ArkUI 组件的数值型 `width`、`height`、`padding`、`fontSize`、`scrollTo` 等布局参数默认按 vp 理解；同一条布局计算链路内应保持 vp，不要中途转 px 后再转回。
- 只有 Canvas 绘制缓冲、PixelMap、截图导出、屏幕物理尺寸、原生接口或明确标注为 px 的 SDK 参数才使用 px。
- px/vp 转换优先绑定当前 UI 实例，使用当前组件或当前窗口的 `UIContext`，例如 `this.getUIContext().px2vp(px)`、`this.getUIContext().vp2px(vp)`。不要在多窗口、分屏、卡片、弹窗或跨 UIAbility 场景中依赖脱离 UI 实例的全局转换。
- `onAreaChange`、窗口信息、屏幕信息、第三方 SDK 回调等返回的长度不要假设单位；先判断 `number`、`'12vp'`、`'12px'` 或 `Resource`，确认后再进入布局公式。
- 需要同时对齐两层 UI 时，先确定共同坐标系。字帖、列表、滚动偏移等视觉布局保持 vp；Canvas、图片导出等像素输出在最终边界再 `vp2px`，并只在像素尺寸处取整。
- 不要提前 `Math.floor()` / `Math.ceil()` 布局中的行高、单元格高度、滚动距离等小数 vp；提前取整会随行数累积误差。只在整数像素、数组索引、页码、行列数等离散边界取整。
- 对长画布或滚动 SDK 参数要区分“内容总高度”和“可滚动高度”。如果 SDK 参数表达可滚动范围，应以 `max(0, contentHeightVp - viewportHeightVp)` 为基准，不要直接传内容总高度；若 SDK 明确不接受 0，再在调用边界按文档要求夹到最小正值。

```typescript
private parseLengthAsVp(value: Length): number {
    if (typeof value === 'number') {
        return Number.isFinite(value) ? value : 0
    }
    if (typeof value !== 'string') {
        return 0
    }
    const text = value.trim()
    const parsed = parseFloat(text)
    if (!Number.isFinite(parsed)) {
        return 0
    }
    if (text.endsWith('px')) {
        return this.getUIContext().px2vp(parsed)
    }
    return parsed
}

private getScrollableHeightVp(contentHeightVp: number, viewportHeightVp: number): number {
    return Math.max(0, contentHeightVp - viewportHeightVp)
}
```

---

## 动画系统

### 显式动画 animateTo

```typescript
@State scale: number = 1
@State opacity: number = 1

// 修改状态时自动触发动画
Button('点击放大')
    .scale({ x: this.scale, y: this.scale })
    .opacity(this.opacity)
    .onClick(() => {
        animateTo({ duration: 300, curve: Curve.EaseInOut }, () => {
            this.scale = this.scale === 1 ? 1.5 : 1
            this.opacity = this.opacity === 1 ? 0.5 : 1
        })
    })
```

### 属性动画 animation

```typescript
@State width: number = 100

// 状态变化时自动动画过渡
Column()
    .width(this.width)
    .height(100)
    .backgroundColor('#007DFF')
    .animation({ duration: 300, curve: Curve.EaseInOut })

Button('变宽').onClick(() => { this.width = 200 })
Button('恢复').onClick(() => { this.width = 100 })
```

### 组件转场 transition

```typescript
@State show: boolean = false

if (this.show) {
    Text('出现/消失动画')
        .transition({
            type: TransitionType.Insert,
            opacity: 0,
            translate: { y: -20 }
        })
        .transition({
            type: TransitionType.Delete,
            opacity: 0,
            translate: { y: -20 }
        })
}

Button('切换').onClick(() => {
    animateTo({ duration: 300 }, () => {
        this.show = !this.show
    })
})
```

### 常用动画曲线

| 曲线 | 效果 |
|------|------|
| `Curve.Linear` | 匀速 |
| `Curve.EaseIn` | 先慢后快 |
| `Curve.EaseOut` | 先快后慢 |
| `Curve.EaseInOut` | 慢→快→慢 |
| `Curve.FastOutSlowIn` | 快出慢入（Material） |
| `Curve.Spring` | 弹簧效果 |
| `Curve.Smooth` | 平滑 |

---

## 手势交互

### 点击手势 TapGesture

```typescript
Text('双击点赞')
    .gesture(
        TapGesture({ count: 2 })
            .onAction(() => { console.info('双击') })
    )
```

### 长按手势 LongPressGesture

```typescript
Image($r('app.media.photo'))
    .gesture(
        LongPressGesture({ repeat: true })
            .onAction((event: GestureEvent) => {
                console.info(`长按中: ${event.timestamp}`)
            })
            .onActionEnd(() => { console.info('长按结束') })
    )
```

### 拖动手势 PanGesture

```typescript
@State offsetX: number = 0
@State offsetY: number = 0

Image($r('app.media.icon'))
    .width(60).height(60)
    .translate({ x: this.offsetX, y: this.offsetY })
    .gesture(
        PanGesture()
            .onActionStart(() => { console.info('开始拖动') })
            .onActionUpdate((event: GestureEvent) => {
                this.offsetX = event.offsetX
                this.offsetY = event.offsetY
            })
            .onActionEnd(() => { console.info('结束拖动') })
    )
```

### 捏合手势 PinchGesture

```typescript
@State scale: number = 1

Image($r('app.media.photo'))
    .scale({ x: this.scale, y: this.scale })
    .gesture(
        PinchGesture()
            .onActionUpdate((event: GestureEvent) => {
                this.scale = event.scale
            })
    )
```

### 旋转手势 RotationGesture

```typescript
@State angle: number = 0

Image($r('app.media.photo'))
    .rotate({ angle: this.angle })
    .gesture(
        RotationGesture()
            .onActionUpdate((event: GestureEvent) => {
                this.angle = event.angle
            })
    )
```

### 滑动手势 SwipeGesture

```typescript
Text('左滑删除')
    .gesture(
        SwipeGesture({ direction: SwipeDirection.Horizontal })
            .onAction(() => { console.info('左滑') })
    )
```

### 手势组合

```typescript
// 串行：按顺序识别
.gesture(
    GestureGroup(GestureMode.Sequence,
        TapGesture({ count: 2 }),
        LongPressGesture()
    )
)

// 并行：同时识别
.gesture(
    GestureGroup(GestureMode.Parallel,
        PinchGesture(),
        RotationGesture()
    )
)
```

---

## 性能优化

1. **使用 `LazyForEach` 替代 `ForEach`**：列表超过 100 项时
2. **设置 `cachedCount`**：`List` 和 `Grid` 缓存屏幕外 3-5 项
3. **避免 `build()` 中复杂计算**：提前计算好数据再赋值
4. **减少 `@State` 嵌套层级**：扁平化状态，避免深层对象频繁变更触发大量重绘
5. **使用 `if` 替代 `visibility`**：不需要显示时用 `if` 完全移除组件
6. **图片懒加载**：`Image().interpolation(ImageInterpolation.Low).syncLoad(false)`
7. **长列表避免动画**：`ListItem` 内避免 `transition` 和 `animateTo`
