# ArkTS 语法速查

## 目录

1. [装饰器](#装饰器)
2. [类型系统](#类型系统)
3. [UI 描述](#ui-描述)
4. [生命周期](#生命周期)
5. [状态管理最佳实践](#状态管理最佳实践)
6. [常用工具函数](#常用工具函数)
7. [Promise 使用规范](#promise-使用规范)
8. [@Watch 监听状态变化](#watch-监听状态变化)
9. [@Builder 详细用法](#builder-详细用法)
10. [@Extend 详细用法](#extend-详细用法)
11. [@Styles 详细用法](#styles-详细用法)
12. [自定义组件事件回调](#自定义组件事件回调)
13. [编程规范](#编程规范)

---

## 装饰器

### @Component

标记自定义组件，必须配合 `struct` 使用。

```typescript
@Component
struct MyComponent {
  build() {
    // UI 描述
  }
}
```

### @Entry

标记组件为页面入口，每个页面有且仅有一个 `@Entry`。

```typescript
@Entry
@Component
struct Index {
  build() { }
}
```

### @State

组件内部状态，改变时触发 UI 刷新。

```typescript
@Component
struct Counter {
  @State count: number = 0

  build() {
    Button(`Count: ${this.count}`)
      .onClick(() => this.count++)
  }
}
```

**限制**：不支持 Object、Array 的深层监听；复杂对象用 `@Observed` + `@ObjectLink`。

### @Prop

父 → 子单向数据同步，值拷贝。

```typescript
// 父组件
@Entry @Component
struct Parent {
  @State title: string = 'Hello'

  build() {
    Child({ title: this.title })
  }
}

// 子组件
@Component
struct Child {
  @Prop title: string  // 单向同步

  build() {
    Text(this.title)
  }
}
```

// ⚠️ 性能警告：@Prop 会进行深拷贝
// 对于大数据对象，建议使用 @ObjectLink 或拆分属性

### @Prop 性能问题

**⚠️ 不推荐场景**：传递大数据对象给子组件

```typescript
// ❌ 性能差：@Prop 会深拷贝整个对象
@Component
struct Child {
  @Prop user: IUser  // 深拷贝，大数据对象开销大
}

// ✅ 方案1：只传递需要的字段（primitive 类型）
@Component
struct Child {
  @Prop userName: string
  @Prop userAvatar: string
}

// ✅ 方案2：使用 @ObjectLink（不拷贝，共享引用）
@Observed
class User {
  name: string = ''
  avatar: string = ''
}

@Component
struct Child {
  @ObjectLink user: User  // 共享引用，无拷贝开销
}

// ✅ 方案3：使用 @Link（双向同步，无拷贝）
@Component
struct Child {
  @Link user: User
}
// 父组件传递：Child({ user: $user })
```

**选择指南**：
| 装饰器 | 拷贝行为 | 适用场景 |
|--------|---------|---------|
| `@Prop` | 深拷贝 | 小数据、primitive 类型 |
| `@Link` | 不拷贝 | 需要双向同步 |
| `@ObjectLink` | 不拷贝 | 观察对象内部变化 |
```

### @Link

父子双向同步，必须通过 `$` 传递引用。

```typescript
// 父组件
@Entry @Component
struct Parent {
  @State count: number = 0

  build() {
    Child({ count: $count })  // $ 传递引用
  }
}

// 子组件
@Component
struct Child {
  @Link count: number  // 双向同步

  build() {
    Button(`+1`).onClick(() => this.count++)
  }
}
```

### @Provide / @Consume

跨层级双向同步，替代层层传递 `@Link`。

```typescript
@Entry @Component
struct GrandParent {
  @Provide theme: string = 'dark'

  build() {
    Parent()
  }
}

@Component
struct Parent {
  build() {
    Child()  // 无需传递 theme
  }
}

@Component
struct Child {
  @Consume theme: string  // 自动匹配 @Provide

  build() {
    Text(this.theme)
  }
}
```

### @Watch

监听状态变化，执行回调。

```typescript
@State @Watch('onCountChange') count: number = 0

onCountChange() {
  console.info(`count changed to ${this.count}`)
}
```

### @Observed / @ObjectLink

深层响应式对象（Class 实例）。

```typescript
@Observed
class TodoItem {
  title: string = ''
  done: boolean = false
}

@Component
struct TodoItemComponent {
  @ObjectLink item: TodoItem  // 深层监听

  build() {
    Row() {
      Text(this.item.title)
      Checkbox().select(this.item.done)
        .onChange((checked) => { this.item.done = checked })
    }
  }
}
```

### @Builder

轻量 UI 复用函数，内部可引用组件状态。详见 [@Builder 详细用法](#builder-详细用法)。

```typescript
@Component
struct MyComponent {
  @State label: string = 'Click'

  // 全局 Builder
  @Builder
  buildHeader(title: string) {
    Text(title).fontSize(20).fontWeight(FontWeight.Bold)
  }

  build() {
    Column() {
      this.buildHeader(this.label)
    }
  }
}
```

### @BuilderParam

允许父组件传入自定义 Builder。

```typescript
@Component
struct Container {
  @BuilderParam content: () => void

  build() {
    Column() {
      this.content()
    }
  }
}

// 使用
Container() {
  Text('Custom content')
}
```

### @Extend

扩展原生组件样式，只支持全局定义。详见 [@Extend 详细用法](#extend-详细用法)。

```typescript
@Extend(Text)
function priceText() {
  .fontSize(18)
  .fontColor('#FF0000')
  .fontWeight(FontWeight.Bold)
}

// 使用
Text('¥99.9').priceText()
```

### @Styles

抽取通用样式，支持全局和组件内。详见 [@Styles 详细用法](#styles-详细用法)。

```typescript
// 组件内
@Component
struct MyComponent {
  @Styles
  cardStyle() {
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
    .padding(16)
    .shadow({ radius: 4, color: '#00000020' })
  }

  build() {
    Column() { }
      .cardStyle()
  }
}

// 全局（组件外）
@Styles
function globalCard() {
  .backgroundColor('#FFFFFF')
  .borderRadius(8)
  .padding(12)
}
```

---

## 类型系统

### ArkTS vs TypeScript 差异

| 特性 | TypeScript | ArkTS |
|------|-----------|-------|
| `any` | ✅ | ❌ 禁止 |
| `enum` | ✅ | ❌ 禁止（用 `const` 对象或 union） |
| `prototype` | ✅ | ❌ 禁止 |
| `arguments` | ✅ | ❌ 禁止 |
| `for...in` | ✅ | ❌ 禁止 |
| 动态属性 `obj[key]` | ✅ | ⚠️ 有限支持 |
| `Object.keys()` | ✅ | ❌ 用 `Object.entries()` |
| `as` 类型断言 | ✅ | ⚠️ 仅允许 `as string` 等 |
| `!=` / `==` | ✅ | ❌ 必须用 `!==` / `===` |

### 常用类型

```typescript
// 基础
let num: number = 0
let str: string = ''
let flag: boolean = false

// 联合类型
type Status = 'loading' | 'success' | 'error'

// 接口
interface IUserData {
  id: number
  name: string
  avatar?: string  // 可选
}

// 数组
let list: IUserData[] = []

// Record
let cache: Record<string, string> = {}

// Promise
async function fetchData(): Promise<IUserData> {
  const res = await http.request(...)
  return res.result as IUserData
}

// 回调类型
type OnChange = (value: string) => void
```

### 对象字面量类型限制

ArkTS 不允许对象字面量作为类型声明。需要描述对象结构时，必须显式声明 `interface` 或 `class`。

```typescript
// ❌ 禁止：对象字面量作为类型声明
let badUser: { id: number; name: string } = { id: 1, name: 'Tom' }

function updateUserBad(user: { id: number; name: string }): void {
  // ...
}

// ✅ 推荐：使用 interface
interface IUser {
  id: number
  name: string
}

let user: IUser = { id: 1, name: 'Tom' }

function updateUser(user: IUser): void {
  // ...
}
```

### SDK options 对象必须显式类型化

ArkTSCheck 对 SDK API 的对象字面量也很严格。遇到 `Object literal must correspond to some explicitly declared class or interface (arkts-no-untyped-obj-literals)` 时，不要把 options/record 直接内联传给 SDK 方法；先用 SDK 暴露的 interface 显式声明变量，再传参。

```typescript
import image from '@ohos.multimedia.image'
import photoAccessHelper from '@ohos.file.photoAccessHelper'
import { systemShare } from '@kit.ShareKit'

// ❌ 容易触发 arkts-no-untyped-obj-literals
await packer.packToData(pixelMap, {
  format: 'image/jpeg',
  quality: 100
})

await photoHelper.createAsset(photoAccessHelper.PhotoType.IMAGE, 'jpg', {
  title: imageTitle
})

const data = new systemShare.SharedData({
  utd: utdTypeId,
  uri: fileUri,
  title: '分享我的作品'
})

// ✅ 推荐：先声明为 SDK interface 类型
const packingOption: image.PackingOption = {
  format: 'image/jpeg',
  quality: 100
}
await packer.packToData(pixelMap, packingOption)

const createOptions: photoAccessHelper.CreateOptions = {
  title: imageTitle
}
await photoHelper.createAsset(photoAccessHelper.PhotoType.IMAGE, 'jpg', createOptions)

const shareRecord: systemShare.SharedRecord = {
  utd: utdTypeId,
  uri: fileUri,
  title: '分享我的作品'
}
const shareData = new systemShare.SharedData(shareRecord)

const shareOptions: systemShare.ShareControllerOptions = {
  selectionMode: systemShare.SelectionMode.SINGLE,
  previewMode: systemShare.SharePreviewMode.DETAIL
}
await controller.show(context, shareOptions)
```

常见需要显式类型化的对象：

- `image.PackingOption`：`ImagePacker.packToData()` / `packToFile()`。
- `photoAccessHelper.CreateOptions`：`photoAccessHelper.createAsset()`。
- `systemShare.SharedRecord`：`new systemShare.SharedData(record)`。
- `systemShare.ShareControllerOptions`：`ShareController.show(context, options)`。

### 枚举替代方案

```typescript
// ❌ 禁止
// enum Direction { Up, Down, Left, Right }

// ✅ 推荐
const Direction = {
  UP: 'Up',
  DOWN: 'Down',
  LEFT: 'Left',
  RIGHT: 'Right'
} as const
type Direction = typeof Direction[keyof typeof Direction]
```

---

## UI 描述

### 条件渲染

```typescript
build() {
  Column() {
    if (this.isLoading) {
      LoadingProgress()
    } else if (this.dataList.length > 0) {
      List() { /* ... */ }
    } else {
      Text('暂无数据')
    }
  }
}
```

### 循环渲染

```typescript
@State items: string[] = ['A', 'B', 'C']

build() {
  List() {
    ForEach(this.items, (item: string, index?: number) => {
      ListItem() {
        Text(`${index}: ${item}`)
      }
    }, (item: string) => item)  // keyGenerator
  }
}
```

### 转场动画

```typescript
if (this.showDetail) {
  // 进入：从右侧滑入
  // 退出：向右侧滑出
  Text('Detail').transition(TransitionEffect.translate({ x: 1000 }))
}

// 调用
this.showDetail = true
animateTo({ duration: 300 }, () => {
  this.showDetail = true
})
```

---

## 生命周期

### 组件生命周期

| 方法 | 说明 |
|------|------|
| `aboutToAppear()` | 组件即将出现，可做初始化 |
| `aboutToDisappear()` | 组件即将销毁，清理资源 |
| `onPageShow()` | 页面显示时（仅 `@Entry`） |
| `onPageHide()` | 页面隐藏时（仅 `@Entry`） |
| `onBackPress()` | 返回键按下（仅 `@Entry`） |

### 页面生命周期详细说明

```typescript
// 页面生命周期（@Entry 组件）
@Entry
@Component
struct MyPage {
  // 组件创建时触发（每次进入页面）
  aboutToAppear(): void {
    // 初始化数据、发起请求
  }

  // 组件销毁时触发
  aboutToDisappear(): void {
    // 清理定时器、取消订阅
  }

  // 页面每次显示时触发（从其他页面返回也会触发）
  onPageShow(): void {
    // 刷新数据
  }

  // 页面隐藏时触发
  onPageHide(): void {
    // 暂停操作
  }

  // 返回按钮按下时触发，返回 true 表示自己处理返回逻辑
  onBackPress(): boolean {
    // 弹出确认框
    return true  // 返回 true 阻止默认返回
  }

  build() { }
}
```

### 生命周期触发时序

```
首次进入: aboutToAppear → build → onPageShow
切换离开: onPageHide → aboutToDisappear
返回页面: aboutToAppear → build → onPageShow
按返回键: onBackPress → (返回 true 则不退出, false 则默认退出)
```

### 简要示例

```typescript
@Entry
@Component
struct Index {
  aboutToAppear() {
    console.info('Index aboutToAppear')
  }

  aboutToDisappear() {
    console.info('Index aboutToDisappear')
  }

  onPageShow(): void {
    console.info('Page show')
  }

  onPageHide(): void {
    console.info('Page hide')
  }

  onBackPress(): boolean {
    console.info('Back pressed')
    return false  // false = 默认行为，true = 拦截返回
  }

  build() { }
}
```

---

## 状态管理最佳实践

### 选择决策树

```
需要跨组件共享？
├── 是 → 跨多少层？
│   ├── 1 层（父子）→ @Link（双向）或 @Prop（单向）
│   └── 多层（祖孙）→ @Provide + @Consume
└── 否 → 仅组件内 → @State
```

### 复杂对象

```
对象需要深层响应？
├── 是 → @Observed class + @ObjectLink
└── 否 → @State + 整体替换
```

### 全局状态

```typescript
// AppStorage（应用级）
AppStorage.setOrCreate('token', '')
AppStorage.get<string>('token')
// 组件内使用
@StorageLink('token') token: string
@StorageProp('token') token: string  // 只读

// LocalStorage（页面级）
let storage = new LocalStorage()
storage.setOrCreate('count', 0)
// 组件内使用
@LocalStorageLink('count') count: number
@LocalStorageProp('count') count: number  // 只读
```

---

## 常用工具函数

```typescript
import { promptAction } from '@kit.ArkUI'

// Toast
promptAction.showToast({ message: '操作成功', duration: 2000 })

// AlertDialog
promptAction.showDialog({
  title: '提示',
  message: '确定删除？',
  buttons: [{ text: '取消', color: '#999999' }, { text: '确定', color: '#FF0000' }]
})

// 格式化日期
import { intl } from '@kit.LocalizationKit'
let dateTimeFmt = new intl.DateTimeFormat('zh-CN', {
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit'
})
dateTimeFmt.format(new Date())

// 时间计算 - 使用 systemDateTime（推荐）
import { systemDateTime } from '@kit.BasicServicesKit'

// 获取系统时间（毫秒时间戳）- 不受用户修改系统时间影响
const startTime = systemDateTime.getTime()
// ... 执行操作
const endTime = systemDateTime.getTime()
const diff = endTime - startTime  // 准确的时间差

// ❌ 不推荐：Date.now() / new Date()
// 用户修改系统时间会导致计算错误
const wrongStart = Date.now()
// 用户把系统时间往前调了
const wrongEnd = Date.now()  // 可能比 start 还小！

// 延迟执行
setTimeout(() => { }, 1000)

// JSON 操作
let parsed = JSON.parse<IUserData>(jsonStr)
let jsonStr = JSON.stringify(obj)
```

---

## Promise 使用规范

### 强制规则

**⚠️ 调用返回 Promise 的函数，必须 catch 错误**

未处理的 Promise rejection 在鸿蒙中会导致应用崩溃，没有任何容错余地。

### try...catch vs .catch 选择指南

| 场景 | 推荐 | 原因 |
|------|------|------|
| `async` 函数内 `await` 多个异步操作 | `try...catch` | 一个 catch 包住多个 await，代码简洁 |
| 链式调用 `.then().then()` | `.catch()` | 放在链尾统一捕获整条链的错误 |
| 单个异步调用，需要不同错误处理 | `.catch()` | 每个调用独立处理 |
| 需要在 finally 中做清理（隐藏 loading 等） | `try...catch...finally` | finally 无论成功失败都执行 |
| 并发异步 `Promise.all()` | `try...catch` | 任一失败都需统一处理 |

### try...catch 使用场景

```typescript
// ✅ 场景1：多个 await 需要统一错误处理
async function loadPage() {
  try {
    const userInfo = await fetchUser()
    const config = await fetchConfig()
    const dataList = await fetchData(userInfo.id)
    // 全部成功才到这
  } catch (err) {
    // 任意一个失败都走这
    console.error(`页面加载失败: ${(err as Error).message}`)
    promptAction.showToast({ message: '加载失败' })
  }
}

// ✅ 场景2：需要 finally 做清理
async function submitForm() {
  this.loading = true
  try {
    const res = await httpRequest.submit(formData)
    promptAction.showToast({ message: '提交成功' })
  } catch (err) {
    promptAction.showToast({ message: '提交失败' })
  } finally {
    this.loading = false  // 无论成败都要关闭 loading
  }
}

// ✅ 场景3：Promise.all 并发请求
async function loadDashboard() {
  try {
    const [user, stats, notifications] = await Promise.all([
      fetchUser(),
      fetchStats(),
      fetchNotifications()
    ])
    // 三个请求全部成功
  } catch (err) {
    // 任一请求失败
    console.error(`仪表盘加载失败: ${(err as Error).message}`)
  }
}

// ✅ 场景4：需要不同粒度的错误处理
async function saveData() {
  try {
    await saveToLocal()   // 本地保存
    try {
      await syncToCloud() // 云端同步（失败不影响本地）
    } catch (cloudErr) {
      console.warn(`云端同步失败，数据已保存本地: ${(cloudErr as Error).message}`)
    }
  } catch (localErr) {
    // 本地保存也失败了
    promptAction.showToast({ message: '保存失败' })
  }
}
```

### .catch() 使用场景

```typescript
// ✅ 场景1：链式调用
http.request(url)
  .then(res => res.result as string)
  .then(jsonStr => JSON.parse<IUserData>(jsonStr))
  .then(data => this.userInfo = data)
  .catch(err => {
    // 捕获整条链中任一环节的错误
    console.error(`请求/解析失败: ${(err as Error).message}`)
  })

// ✅ 场景2：单个异步调用，独立处理
router.pushUrl({ url: 'pages/DetailPage' })
  .catch(err => {
    console.error(`页面跳转失败: ${(err as Error).message}`)
    promptAction.showToast({ message: '跳转失败' })
  })

// ✅ 场景3：需要错误恢复（返回默认值）
preferences.get('theme', 'light')
  .then(theme => this.applyTheme(theme as string))
  .catch(() => this.applyTheme('light'))  // 读取失败用默认值

// ✅ 场景4：不依赖上下文的简单操作
promptAction.showDialog({
  title: '提示',
  message: '确定删除？'
}).catch(() => { /* 弹窗失败静默处理 */ })
```

### 常见错误写法

```typescript
// ❌ 只 then 不 catch — rejection 未处理
http.request(url).then(res => { /* ... */ })

// ❌ async/await 不 try-catch — 等同于未 catch
async function load() {
  const res = await http.request(url)  // 网络异常直接崩溃
}

// ❌ try-catch 范围太大 — 成功逻辑也被包进去了
async function load() {
  try {
    const res = await http.request(url)
    this.updateUI(res)        // UI 更新出错也会被 catch 吞掉
    this.saveToCache(res)     // 缓存出错也被吞掉
  } catch (err) {
    // 分不清是网络错误还是 UI 错误
  }
}

// ✅ 缩小 try-catch 范围
async function load() {
  let res: HttpResponse
  try {
    res = await http.request(url)
  } catch (err) {
    promptAction.showToast({ message: '网络请求失败' })
    return  // 网络失败直接返回
  }
  // 以下逻辑不在 try 中，错误可以独立排查
  this.updateUI(res)
  this.saveToCache(res)
}
```

### 统一封装模板

```typescript
// 通用安全请求封装
async function safeRequest<T>(
  fn: () => Promise<T>,
  options?: {
    fallback?: T
    errorMsg?: string
    silent?: boolean
  }
): Promise<T | undefined> {
  try {
    return await fn()
  } catch (err) {
    const msg = options?.errorMsg ?? '操作失败'
    console.error(`${msg}: ${(err as Error).message}`)
    if (!options?.silent) {
      promptAction.showToast({ message: msg })
    }
    return options?.fallback
  }
}

// 使用
const data = await safeRequest(
  () => http.request(url),
  { fallback: defaultData, errorMsg: '加载失败' }
)
```

### 常见需要 catch 的 API

| API | 场景 |
|-----|------|
| `http.request()` | 网络请求 |
| `router.pushUrl()` | 页面跳转 |
| `preferences.get()` | 本地存储读取 |
| `systemDateTime.getTime()` | 系统时间获取 |
| `promptAction.showDialog()` | 弹窗交互 |
| `geoLocationManager.getCurrentLocation()` | 定位获取 |
| `batteryInfo.getBatteryLevel()` | 电池信息 |
| `wifiManager.getLinkedInfo()` | WiFi 信息 |

---

## @Watch 监听状态变化

### 基本用法

```typescript
// @Watch 监听状态变化
@Component
struct SearchPage {
  @State keyword: string = ''
  @Watch('keyword')
  onKeywordChange(newValue: string): void {
    // keyword 变化时自动触发
    this.search(newValue)
  }

  private search(keyword: string): void {
    // 搜索逻辑
  }

  build() {
    TextInput({ text: this.keyword })
      .onChange((value: string) => { this.keyword = value })
  }
}
```

### 监听 @Prop 变化

```typescript
// @Watch 也可以监听 @Prop
@Component
struct Child {
  @Prop @Watch('onCountChange') count: number = 0

  onCountChange(newValue: number): void {
    console.info(`count 变为 ${newValue}`)
  }
}
```

---

## @Builder 详细用法

### 无参与有参 Builder

```typescript
// @Builder 轻量复用 UI 片段
@Component
struct MyComponent {
  @State count: number = 0

  // 无参 Builder
  @Builder
  titleBar() {
    Row() {
      Text('标题').fontSize(18).fontWeight(FontWeight.Bold)
    }
    .width('100%')
    .padding(16)
  }

  // 有参 Builder
  @Builder
  itemCard(title: string, value: string) {
    Row() {
      Text(title).fontSize(14).fontColor('#666666')
      Blank()
      Text(value).fontSize(14).fontWeight(FontWeight.Medium)
    }
    .width('100%')
    .padding(16)
    .backgroundColor('#FFFFFF')
    .borderRadius(8)
  }

  build() {
    Column({ space: 12 }) {
      this.titleBar()
      this.itemCard('姓名', '张三')
      this.itemCard('年龄', '25')
    }
  }
}
```

---

## @Extend 详细用法

### 扩展原生组件样式

```typescript
// @Extend 扩展原生组件样式（只支持全局定义）
@Extend(Text)
function highlightText() {
  .fontSize(16)
  .fontColor('#FF0000')
  .fontWeight(FontWeight.Bold)
}

// 带参数的 @Extend
@Extend(Text)
function styledText(size: number, color: string) {
  .fontSize(size)
  .fontColor(color)
}

// 使用
Text('重要').highlightText()
Text('普通').styledText(14, '#333333')
```

---

## @Styles 详细用法

### 组件内与全局样式

```typescript
// @Styles 提取通用样式（组件内或全局）
// 组件内
@Component
struct MyComponent {
  @Styles
  cardStyle() {
    .width('100%')
    .padding(16)
    .backgroundColor('#FFFFFF')
    .borderRadius(12)
  }

  build() {
    Column() {
      Text('卡片1').cardStyle()
      Text('卡片2').cardStyle()
    }
  }
}

// 全局（不支持参数）
@Styles
function globalCardStyle() {
  .width('100%')
  .padding(16)
  .backgroundColor('#FFFFFF')
  .borderRadius(12)
}
```

---

## 自定义组件事件回调

### 子组件向父组件传递事件

```typescript
// 子组件向父组件传递事件
@Component
struct Child {
  @State inputValue: string = ''
  // 回调函数属性
  onSearch?: (keyword: string) => void
  onClose?: () => void

  build() {
    Row() {
      TextInput({ text: this.inputValue })
        .onChange((value: string) => { this.inputValue = value })
      Button('搜索').onClick(() => {
        this.onSearch?.(this.inputValue)
      })
      Button('关闭').onClick(() => {
        this.onClose?.()
      })
    }
  }
}

// 父组件使用
@Entry
@Component
struct Parent {
  @State searchResult: string = ''

  build() {
    Column() {
      Child({
        onSearch: (keyword: string) => {
          this.searchResult = `搜索: ${keyword}`
        },
        onClose: () => {
          console.info('关闭搜索')
        }
      })
      Text(this.searchResult)
    }
  }
}
```

---
## 编程规范

### 目录

1. [编译和 icon 使用规则](#1-编译和-icon-使用规则)
2. [声明式语法规范](#2-声明式语法规范)
3. [组件封装与复用](#3-组件封装与复用)
4. [布局与弹窗](#4-布局与弹窗)
5. [动画与转场](#5-动画与转场)
6. [手势与导航](#6-手势与导航)
7. [主题与样式](#7-主题与样式)
8. [ArkTS Lint 规则](#8-arkts-lint-规则)
9. [最佳实践总结](#9-最佳实践总结)
10. [开发工具](#10-开发工具)
11. [总结](#11-总结)

---

### 1. 编译和 icon 使用规则

1. 每次 agent 修改完鸿蒙代码，先读取仓库 CI、脚本和当前 Hvigor 任务列表，再执行项目实际提供的 lint、test 和应用构建任务；不要假定一定存在 `hvigorw assembleHap`。如果有编译错误，只修复本次代码变更引入的问题，直到通过或明确说明阻塞原因。
2. 修改鸿蒙代码后的编译校验禁止修改编译环境：不要为了通过编译而修改 DevEco/SDK/JDK/Node/ohpm/hvigor、`local.properties`、签名配置、PATH 或本机工具链；若失败原因属于环境、依赖安装、签名或本机路径问题，停止修改并报告用户处理。
3. 如果需要图标，优先使用 `symbolname.cursorrules` 文件中的 icon。

### 2. 声明式语法规范

#### 核心原则

- **UI 是状态的函数**: 确保 UI 显示与应用状态始终一致，状态变更可预测。
- **性能优先**: 优化 UI 刷新机制，避免不必要的组件渲染，提升应用性能。
- **状态与 UI 解耦**: 将状态管理逻辑从 UI 组件中分离，提高组件复用性和代码可维护性。
- **单向数据流**: 遵循明确的数据流向，简化状态管理复杂度。

#### 推荐做法

##### 代码结构

- **集中共享状态**: 对于多组件共享的状态，推荐使用`StateStore`进行全局管理，将数据集中存储，实现状态与 UI 的解耦。
- **观测数据定义**: 所有需要被`StateStore`管理且能触发 UI 更新的业务数据，必须使用`@Observed`或`@ObservedV2`装饰器修饰。
- **纯函数 Reducer**: 将所有的状态更新逻辑封装在独立的纯函数（Reducer）中，确保状态变更的单一职责和可预测性。

##### 最佳实践

- **理解刷新机制**: 深入理解`@State`, `@Prop`, `@Link`等装饰器的工作原理，明确它们如何触发 UI 刷新。
- **审慎使用`@Link`**: `Link`实现双向绑定。若仅需单向传递数据，优先考虑`@Prop`或普通参数，以减少不必要的子组件刷新范围。
- **按需使用状态变量**: 仅当变量的改变需要触发 UI 更新时，才使用相应的状态装饰器对其进行标记。
- **事件驱动状态更新**: 状态的改变应发生在用户交互（如`onClick`）、生命周期回调（如`onAppear`）、数据请求回调等明确的事件中。

#### 禁止做法

- **`build`方法副作用**: 绝对避免在组件的`build`方法或其直接调用的计算属性/函数中修改非状态变量或执行其他副作用操作。
- **冗余状态变量**: 禁止将未关联任何 UI 组件、或仅被读取但从未被修改的变量定义为状态变量（例如，未在`build`方法中使用的`@State`变量）。
- **不必要的`@Link`**: 避免在仅需单向数据流的场景下使用`@Link`，这会增加不必要的双向依赖和刷新风险。

#### 代码示例

##### 推荐写法

```arkts
@Component
struct MyCounter {
  @State count: number = 0; // 状态变量，UI依赖

  build() {
    Column() {
      Text(`当前计数: ${this.count}`)
        .fontSize(24)
      Button('增加')
        .onClick(() => {
          this.count++; // 状态在事件回调中修改，触发UI刷新
        })
    }
  }
}
```

##### 避免写法

```arkts
// 避免写法1: 在build方法直接调用的函数中引入副作用
@Component
struct BadImageEffect {
  private currentOpacity: number = 0; // 非状态变量

  // 该函数在每次build时都会被调用，意外修改非状态变量
  private calculateOpacity(): number {
    this.currentOpacity = (this.currentOpacity + 0.1) % 1;
    return this.currentOpacity;
  }

  build() {
    Image('icon.png')
      .opacity(this.calculateOpacity()) // 每次UI刷新都累加opacity
  }
}

// 避免写法2: 冗余状态变量
@Entry
@Component
struct BadComponent {
  // 变量未关联任何UI组件，或仅被读取但未修改，不应定义为状态变量
  @State unusedData: string = 'some data';
  @State readonlyMessage: string = 'Hello';

  build() {
    Column() {
      // 仅读取readonlyMessage，未修改
      Text(this.readonlyMessage)
    }
  }
}
```

#### 注意事项

- **利用开发工具**: 使用 HarmonyOS 提供的诊断工具（如`hidumper`）来分析应用运行时状态变量的变化和 UI 组件的刷新情况，定位冗余刷新问题。
- **代码静态检查**: 定期使用`Code Linter`工具进行代码检查，重点关注性能优化规则（如`@performance/hp-arkui-remove-redundant-state-var`），并根据扫描结果进行优化。

---

### 3. 组件封装与复用

#### 核心原则

- **高效复用，减少开销：** 通过组件缓存和生命周期管理，避免频繁创建和销毁UI对象，提升渲染效率。
- **统一封装，提升维护：** 采用标准化的封装模式，如`attributeModifier`，统一组件API风格，简化调用和维护。
- **数据优化，避免冗余：** 选择高效的数据传递方式，减少不必要的深拷贝和重复更新。
- **按需加载，动态渲染：** 利用动态UI能力实现组件的预创建和按需加载，优化页面响应速度。

#### 推荐做法

- **组件复用声明与生命周期：**
  - 使用`@Reusable`装饰器修饰自定义组件，使其具备复用能力。
  - 在`aboutToReuse()`生命周期回调中，根据新数据刷新组件UI，而非在构造函数中执行所有初始化逻辑。
  - 通过`reuseId`属性对不同结构或用途的可复用组件进行精细化分组，提高缓存匹配效率。
- **数据传递与状态更新：**
  - 对于复杂对象或数组，优先使用`@Link`或`@ObjectLink`装饰器传递引用，避免深拷贝带来的性能开销。
  - 避免在`aboutToReuse()`中对会自动更新的状态变量（如`@Link`、`@ObjectLink`、`@Prop`）进行重复赋值。
- **公用组件封装：**
  - 利用ArkTS提供的`attributeModifier`属性方法，对系统组件进行封装，实现链式调用风格，统一API。
  - 提供方可暴露`AttributeModifier`接口实现类，供调用方通过`.attributeModifier()`方法传入。
- **弹窗组件封装：**
  - 使用`UIContext`中获取的`PromptAction`对象来管理自定义弹窗的显示与隐藏，确保生命周期正确。
- **动态UI与性能优化：**
  - 对于需要频繁动态增删改查组件、或组件树深度和复杂度较高的场景，优先使用`FrameNode`配合`NodeController`进行组件的创建、管理和局部渲染，以获得更好的性能。
  - 利用`onIdle()`生命周期回调或其他空闲时间进行组件预创建和缓存，减少用户感知到的加载延迟。

#### 禁止做法

- **函数作为入参：** 避免将函数方法直接作为复用组件的入参，这可能导致组件无法有效复用或引起不必要的渲染更新。
- **`@Prop`深拷贝复杂数据：** 避免使用`@Prop`传递大型或复杂的对象/数组，这会导致不必要的深拷贝，影响性能。
- **传统冗余封装：** 避免采用导致自定义组件入参列表过长、使用方式与系统组件不一致的传统封装方式。
- **过度依赖声明式`diff`：** 在需要频繁动态增删改查组件、或组件树深度和复杂度较高时，仅依赖声明式范式可能导致`diff`算法开销过大，影响性能。
- **整体重绘操作局部：** 避免为了操作或移动局部子组件树而重新渲染整个父组件，导致不必要的性能浪费。

#### 代码示例

##### 推荐写法

```arkts
// 推荐：@Reusable 组件及 aboutToReuse 生命周期
@Reusable
@Component
struct ReusableListItem {
  private itemData: string = ''; // 初始化，但数据更新在aboutToReuse
  aboutToReuse(params: { data: string }) {
    this.itemData = params.data; // 从缓存取出时，更新数据
  }
  build() {
    Text(this.itemData)
      .fontSize(16)
      .fontColor(Color.Black);
  }
}

// 推荐：使用 attributeModifier 封装公用组件样式
class CommonButtonModifier implements AttributeModifier<ButtonAttribute> {
  applyNormalAttribute(instance: ButtonAttribute): void {
    instance.fontSize(18).fontColor(Color.White).backgroundColor(Color.Blue);
  }
}
// 使用方式
Button('提交').attributeModifier(new CommonButtonModifier());
```

##### 避免写法

```arkts
// 避免：传统组件封装导致入参过多且非链式调用
@Component
struct MyLegacyButton {
  @Prop text: string = '';
  @Prop fontSize: number = 14;
  @Prop textColor: Color = Color.Black;
  @Prop bgColor: Color = Color.Gray;
  // ... 如果要支持所有Button属性，此处将非常冗长
  build() {
    Button(this.text)
      .fontSize(this.fontSize)
      .fontColor(this.textColor)
      .backgroundColor(this.bgColor);
  }
}
// 调用方式: <MyLegacyButton text="确认" fontSize={16} textColor={Color.Red} bgColor={Color.Green}/>
```

#### 注意事项

- **性能监控：** 在开发和测试阶段，务必关注应用的帧率、内存占用和CPU使用情况，尤其是在列表滑动、页面切换和复杂动画场景。
- **`FrameNode`适用性：** `FrameNode`虽性能优越，但其使用场景相对特定，主要用于对性能有极高要求且需要直接操作UI树的动态布局，并非所有动态UI都需要采用。
- **调试：** 利用HarmonyOS提供的DevEco Studio调试工具，特别是UI调试器，分析组件树结构和渲染性能。

---

### 4. 布局与弹窗

#### 核心原则

- **性能优先，流畅体验**：精简UI节点，优化布局计算，确保动画和滚动平滑。
- **用户为中心**：提供直观、自然、可预期的交互手势和反馈。
- **组件化与复用**：封装可复用组件，利用数据驱动UI，提升开发效率和可维护性。
- **适配多样性**：考虑不同设备形态（如折叠屏、软键盘）的布局与交互适配。

#### 推荐做法

##### 代码结构

- 将复杂或可复用的UI模块（如瀑布流、评论弹窗、图片预览器）封装为独立的自定义组件。
- 通过数据驱动UI渲染，根据数据类型动态选择和渲染列表项（`ListItem`、`GridItem`）或弹窗内容。

##### 最佳实践

- **布局与性能优化**：
  - **精简UI节点**：避免不必要的布局嵌套，优先使用扁平化布局。
  - **设置布局边界**：为父级容器明确设置固定宽高（如`width('100%').height(xxx)`），减少局部UI更新时的全局重计算。
  - **长列表优化**：对于大量数据，务必使用`LazyForEach`替代`ForEach`实现懒加载和组件复用。当`List`嵌套在`Scroll`内时，为`List`明确设置固定宽高。
  - **条件渲染**：根据组件是否需要存在于组件树中，合理选择`if/else`（减少节点）或`visibility`（保留占位）。
- **交互与动画**：
  - **图片跟手效果**：利用`matrix4`实现缩放跟手，`translate`实现平移跟手，确保精确数学计算。
  - **列表交互**：结合`Refresh`组件实现下拉刷新，利用`List.onReachEnd()`实现上滑加载更多，并提供清晰的状态反馈。
  - **拖拽交换**：`Grid`组件开启`editMode(true)`和`supportAnimation(true)`，并为`GridItem`绑定`LongPressGesture`和`PanGesture`。
  - **自定义指示器**：`Swiper`组件禁用自带`indicator(false)`，并自定义进度条指示器，与`Swiper`页面切换联动。
  - **文本展开折叠**：使用`measureTextSize()`精确测量文本高度，计算截断点，实现"...展开/收起"功能。
- **弹窗管理**：
  - **弹窗选型**：对于评论回复等复杂交互场景，优先选择`Navigation Dialog`或统一的`DialogHub`方案，而非`CustomDialog`。
  - **交互控制**：精细控制弹窗的关闭行为（如是否允许侧滑、点击外部关闭），并自定义进出场动画。
  - **键盘适配**：确保弹窗能自动避让软键盘，避免内容遮挡；在软键盘和表情面板切换时平滑过渡。
  - **多弹窗管理**：利用`DialogHub`管理多弹窗层级，确保显示优先级。

#### 禁止做法

- **长列表一次性渲染**：避免对大量数据直接使用`ForEach`，导致性能瓶颈和内存占用过高。
- **不当的弹窗选型**：避免将`CustomDialog`用于需要复杂软键盘避让和动画控制的场景（如评论回复弹窗），因为它存在不可配置的局限性。
- **依赖默认指示器**：当需要自定义进度条或复杂动画时，不应直接依赖`Swiper`组件自带的`indicator`。
- **过度嵌套布局**：避免不必要的组件嵌套，增加UI节点数量和布局计算开销。
- **重要弹窗随意关闭**：对于关键提示或需用户确认的弹窗，禁止允许侧滑或点击外部区域关闭。

#### 代码示例

##### 推荐写法

```arkts
// 推荐：长列表懒加载与Swiper自定义指示器
Swiper() {
  LazyForEach(this.imageData, (item: ImageItem) => {
    Image(item.src)
  }, (item: ImageItem) => item.id)
}
.autoPlay(true)
.indicator(false) // 关闭默认指示器
// ... 自定义进度条指示器逻辑 (通常是一个独立的组件或布局)

// 推荐：List与下拉刷新、上滑加载
List() {
  // ... ListItem内容
}
.onScrollIndex((first, last) => {
  // 仅渲染可见区域，此处可监听加载更多
  if (last >= this.data.length - 5 && !this.isLoading) {
    this.loadMoreData();
  }
})
.width('100%')
.height(this.listHeight) // List在Scroll内时需固定宽高
```

##### 避免写法

```arkts
// 避免：长列表一次性渲染或过多嵌套
Column() { // 避免不必要的Column/Row包裹
  Row() { // 避免多层嵌套
    Text('Title')
  }
  ForEach(this.largeData, (item: DataItem) => { // 避免直接ForEach大量数据
    Column() {
      // ... 复杂UI
    }
  })
}
```

#### 注意事项

- **充分测试**：在不同设备形态、屏幕尺寸和输入法环境下测试UI的布局、交互和性能。
- **异常处理**：在数据加载、刷新等异步操作中，务必处理网络异常、数据为空等情况，并提供清晰的用户反馈。
- **计算精确性**：涉及复杂动画（如图片跟手）或文本处理（如展开折叠）时，确保数学计算的精确性，避免视觉抖动或错误。
- **状态管理**：封装可复用组件时，明确其内部状态管理机制，确保在不同场景下状态的独立性或可控性。

---

### 5. 动画与转场

#### 核心原则

- **用户体验至上**: 动画旨在提升交互流畅感，引导用户，而非纯粹的视觉炫技。
- **性能优先**: 确保动画运行流畅，不造成卡顿或资源浪费。
- **系统能力优先**: 优先使用 HarmonyOS 提供的原生动画 API 和高级模板。
- **设计意图匹配**: 深入理解 UX 设计，选择最符合场景的动效类型和实现方式。

#### 推荐做法

##### 代码结构

- **声明式动画与状态驱动**: 优先使用 HarmonyOS 的声明式 UI 和 `@State` 驱动动画，通过改变状态变量触发动画。
- **组件化封装**: 将复杂的动画逻辑封装到自定义组件中，提高复用性和可维护性。

##### 最佳实践

- **动效选择与场景匹配**:
  - **页面路由转场**: 大部分页面切换推荐使用**左右位移遮罩动效**。
  - **共享元素转场**: 图片展开、图标（搜索框、头像）展开，推荐使用**一镜到底动效**或`geometryTransition`接口。将关键元素作为持续存在的共享元素。
  - **共享容器转场**: 卡片/视频展开、列表项展开，推荐使用`Navigation`自定义动画或`geometryTransition`结合显示动画。
  - **通用动画**: 元素显隐、状态变化等，使用属性动画（`animateTo`）或显式动画。
- **动画运行流畅度优化**:
  - **优先使用系统动画 API**: 系统提供的 API 经过底层优化，性能更佳。
  - **动画属性选择**: 优先改变不影响布局的图形变换属性，如 `transform` (位移、旋转、缩放) 和 `opacity` (不透明度)。这些属性通常在 GPU 上合成，性能最高。
  - **`animateTo` 复用**: 多个动画参数相同时，尽量在同一个 `animateTo` 块中更新状态，减少开销。
  - **`renderGroup` 应用**: 对于包含复杂子组件的动画，将其设置为 `renderGroup(true)`，减少渲染批次。
- **用户手势反馈**: 对于点击、滑动等手势，提供即时且连贯的动画反馈。

#### 禁止做法

- **频繁修改布局属性**: 严禁在动画过程中频繁改变组件的 `width`、`height`、`padding`、`margin` 等布局属性，这会导致 UI 树重绘，严重影响性能。
- **滥用动画**: 避免不必要的、过于复杂的动画，以免分散用户注意力或增加视觉负担。
- **缺乏用户反馈**: 禁止用户操作后界面无任何视觉反馈，特别是在点击、加载等关键交互点。

#### 代码示例

##### 推荐写法

```arkts
// 推荐：通过状态变化驱动动画，并优先改变图形变换属性
@Entry
@Component
struct GoodAnimationExample {
  @State isScaled: boolean = false;

  build() {
    Column() {
      Button('缩放')
        .width(100).height(100)
        .backgroundColor(Color.Blue)
        .scale(this.isScaled ? 1.5 : 1.0) // 改变scale属性
        .opacity(this.isScaled ? 0.5 : 1.0) // 改变opacity属性
        .onClick(() => {
          // 使用animateTo进行动画过渡
          animateTo({ duration: 300, curve: Curve.EaseOut }, () => {
            this.isScaled = !this.isScaled;
          });
        })
    }
    .width('100%').height('100%')
    .justifyContent(FlexAlign.Center)
  }
}

// 推荐：使用共享元素转场
// PageA.ets
@Entry
@Component
struct PageA {
  build() {
    Column() {
      Image('placeholder.png')
        .width(100).height(100)
        .sharedTransition('heroImage') // 定义共享元素ID
        .onClick(() => {
          Router.pushUrl({ url: 'pages/PageB' });
        })
    }
  }
}

// PageB.ets
@Entry
@Component
struct PageB {
  build() {
    Column() {
      Image('placeholder.png')
        .width(300).height(300)
        .sharedTransition('heroImage') // 相同ID，自动匹配
    }
  }
}
```

##### 避免写法

```arkts
// 避免：在动画中直接修改布局属性
@Entry
@Component
struct BadAnimationExample {
  @State currentWidth: number = 100;
  @State currentHeight: number = 100;

  build() {
    Column() {
      Button('改变大小')
        .width(this.currentWidth) // 避免在动画中直接改变width/height
        .height(this.currentHeight) // 避免在动画中直接改变width/height
        .backgroundColor(Color.Red)
        .onClick(() => {
          // 这种方式会导致UI树的重新布局和重绘，性能较差
          animateTo({ duration: 300 }, () => {
            this.currentWidth = 200;
            this.currentHeight = 200;
          });
        })
    }
    .width('100%').height('100%')
    .justifyContent(FlexAlign.Center)
  }
}
```

#### 注意事项

- **转场曲线**: 页面转场曲线优先使用**弹簧曲线 (Curve.Spring)**，以提供更自然的动效。
- **内存管理**: 注意及时释放不再需要的动画资源，防止内存泄漏。
- **跨应用转场**: 对于跨应用转场，应遵循系统规范，确保体验一致性。
- **调试**: 利用 DevEco Studio 的性能分析工具（如 CPU Profiler, UI Latency）对动画进行性能监控和调试。

---

### 6. 手势与导航

#### 核心原则

- 理解HarmonyOS触摸事件的分发机制和事件响应链的构建过程，是解决手势冲突的基础。
- 优先使用HarmonyOS提供的标准UI组件（如`Tabs`）构建导航，确保一致、高效的用户体验。
- 利用HMRouter简化页面路由管理，提升开发效率和代码可维护性，避免手动管理页面栈。

#### 推荐做法

##### 代码结构

- 使用`@Builder`装饰器封装可复用的UI模块，例如自定义底部页签的图标和文字组合 (`TabItemBuilder`)。
- 通过`@HMRouter`注解为目标页面注册唯一的`pageUrl`，实现声明式路由配置。

##### 最佳实践

- **手势事件冲突解决**：
  - 通过`hitTestBehavior`属性精确控制组件的触摸测试行为：
    - `HitTestMode.Transparent`: 组件自身响应，但允许事件继续向下或向上透传。
    - `HitTestMode.Block`: 组件命中后独占事件，阻塞事件向兄弟节点和父组件传递。
  - 在触摸或手势回调函数中，适时调用`event.stopPropagation()`，立即停止事件向上冒泡。
- **底部页签导航**：
  - 使用`Tabs`组件作为底部导航容器，并设置`barPosition: BarPosition.End`。
  - 为每个`TabContent`组件通过`tabBar`属性定义其对应的页签外观（包括选中和未选中状态的图标及文字）。
  - 对于固定数量的页签，设置`Tabs`的`barMode: Fixed`以平均分配页签宽度。
- **页面跳转与返回**：
  - 使用`HMRouterMgr.push()`或`HMRouterMgr.replace()`方法进行页面跳转，并可通过`param`参数传递数据。
  - 在目标页面（被跳转页）的`aboutToAppear`生命周期中，通过`HMRouterMgr.getCurrentParam()`获取跳转参数。
  - 在`push/replace`方法的`onResult`回调中接收从其他页面返回的数据，并通过`popInfo.srcPageInfo.name`判断返回源页面。

#### 禁止做法

- **过度阻塞手势事件**：未经深思熟虑地滥用`HitTestMode.Block`或`event.stopPropagation()`，可能导致用户交互失效或应用行为异常。
- **手动管理页面栈**：避免直接操作底层的`Navigation`能力进行页面跳转和栈管理，应优先使用HMRouter提供的统一接口。

#### 代码示例

##### 推荐写法

```arkts
// 手势冲突处理: 独占区域手势，不向上冒泡
Column() {
  Text('点击我，事件在此终止')
}
.width('100%').height(100)
.backgroundColor(Color.Blue)
.hitTestBehavior(HitTestMode.Block) // 独占所有触摸事件
.onClick(() => {
  console.log('Column clicked, event stopped here.');
})

// 底部页签导航 (简化示例)
Tabs({ barPosition: BarPosition.End }) {
  TabContent() { Text('消息页面').fontSize(24) }
    .tabBar(this.TabItemBuilder('消息', $r('app.media.message_icon'))) // 自定义页签样式
  TabContent() { Text('我的页面').fontSize(24) }
    .tabBar(this.TabItemBuilder('我的', $r('app.media.profile_icon')))
}

@Builder TabItemBuilder(text: string, icon: Resource) {
  Column() {
    Image(icon).width(24).height(24)
    Text(text).fontSize(12)
  }
}

// 页面跳转与参数传递，并接收返回结果
HMRouterMgr.push({
  pageUrl: 'pages/DetailPage', // 目标页面路由
  param: { id: 123, name: 'Product A' }, // 传递参数
  onResult: (popInfo) => { // 接收返回结果
    if (popInfo.srcPageInfo.name === 'pages/DetailPage') {
      console.log('Returned from DetailPage with result:', popInfo.result);
    }
  }
});
```

#### 注意事项

- 在使用`hitTestBehavior`和`event.stopPropagation()`时，务必充分测试，确保用户交互的连贯性和预期性。
- 在应用中存在多个`HMNavigation`组件（如多窗口、多页面栈）时，务必为`HMRouterMgr.push/replace`方法明确指定正确的`navigationId`，以确保页面跳转到正确的导航栈。
- 为底部导航的页签提供清晰的图标（区分选中和未选中态）和简洁的文字标签，以提升用户识别度和整体用户体验。

---

### 7. 主题与样式

#### 核心原则

- **响应用户/系统偏好**: UI应自动适配深浅色模式及用户自定义亮度。
- **保持视觉一致性**: 在不同模式和页面间，保持UI元素的统一性和协调性。
- **优化资源与性能**: 合理管理资源，避免不必要的电量消耗和性能开销。
- **提供流畅用户体验**: 确保用户在不同场景下（如视频播放、付款码）获得无缝且舒适的体验。

#### 推荐做法

##### 代码结构

- **资源目录管理**: 利用HarmonyOS的资源目录机制 (`src/main/resources/base` 用于浅色模式，`src/main/resources/dark` 用于深色模式) 管理深浅色资源。
- **同名资源定义**: 在 `base` 和 `dark` 目录下，为同一种UI元素（如颜色、图片）定义**同名**的资源文件和资源项，实现自动切换。

##### 最佳实践

- **深浅色模式适配**:
  - **颜色资源**: 自定义颜色应定义在 `base/element/color.json` 和 `dark/element/color.json` 中，并通过 `$('app.color.your_color_name')` 引用。优先使用系统级颜色资源。
  - **媒体资源**:
    - SVG 图标: 利用 `fillColor()` 属性，使其颜色跟随当前主题变化。
    - 非SVG图片: 在 `base/media` 和 `dark/media` 目录下放置同名图片资源。
  - **状态栏**: 确保状态栏背景和内容字体颜色与应用深浅模式保持一致。
  - **Web页面**: 配合前端开发，使应用内嵌Web内容支持深色模式（利用CSS媒体查询 `prefers-color-scheme`）。
  - **模式切换**: 提供应用跟随系统模式切换 (`applicationContext.setColorMode(ColorMode.COLOR_MODE_NOT_SET)`) 或用户手动切换的选项。
- **页面亮度与常亮控制**:
  - **页面级亮度**: 使用 `window.setWindowBrightness()` 实现页面专属亮度。利用 `uiObserver.on('navDestinationUpdate')` 监听页面跳转，并在页面进入时应用亮度，离开时恢复系统默认或前一页面的亮度。
  - **屏幕常亮**: 在沉浸式场景（如视频播放）中，通过 `window.setWindowKeepScreenOn(true)` 保持屏幕常亮。务必将其与组件生命周期绑定（如 `onStart` 开启，`onPause`/`onDestroy` 关闭）。
  - **用户UI**: 为需要用户调节亮度的场景（如视频播放器）提供 `Slider` 等UI组件，方便用户调节。

#### 禁止做法

- **硬编码颜色值**: 避免直接在代码中写入十六进制或RGB颜色值，应统一通过资源引用。
- **不及时关闭屏幕常亮**: 在不需要常亮时（如视频暂停、页面退出）不调用 `setWindowKeepScreenOn(false)`，导致不必要的电量消耗和设备发热。
- **深浅色资源命名不一致**: 在 `base` 和 `dark` 目录下为同一元素定义不同的资源名称，导致深浅色模式切换失败。

#### 代码示例

##### 推荐写法

```arkts
// 1. 深浅色模式下引用颜色资源
Text('Hello HarmonyOS')
  .fontColor($r('app.color.text_primary')) // text_primary 在base和dark下定义不同颜色

// 2. 页面亮度动态设置与屏幕常亮
// 假设在视频播放页面的某个组件内
@State currentBrightness: number = 0.5; // 当前页面亮度

aboutToAppear() {
  // 进入页面时设置亮度，并保持屏幕常亮
  window.setWindowBrightness(this.currentBrightness);
  window.setWindowKeepScreenOn(true);
}

aboutToDisappear() {
  // 离开页面时恢复系统亮度，并关闭屏幕常亮
  window.setWindowBrightness(-1); // -1 表示恢复系统默认亮度
  window.setWindowKeepScreenOn(false);
}

// 用户通过Slider调节亮度
Slider({ value: this.currentBrightness, min: 0.01, max: 1.0, step: 0.01 })
  .onChange((value: number) => {
    this.currentBrightness = value;
    window.setWindowBrightness(value);
  })
```

##### 避免写法

```arkts
// 1. 硬编码颜色值
Text('Avoid this')
  .fontColor('#FF0000') // 硬编码红色，在深色模式下可能不协调

// 2. 随意开启屏幕常亮，不及时关闭
// 假设某个地方开启了常亮，但没有对应的关闭逻辑
window.setWindowKeepScreenOn(true); // 容易造成电量浪费
```

#### 注意事项

- **资源自动切换**: HarmonyOS会自动根据系统颜色模式加载对应资源目录下的同名资源，无需额外代码判断。
- **页面亮度作用域**: `window.setWindowBrightness()` 仅在当前应用内生效，退出应用后系统亮度会自动恢复。
- **Web组件适配**: Web内容的深色模式适配通常需要前端开发人员配合完成，确保Web内容自身支持 `prefers-color-scheme`。
- **权限**: 某些亮度或窗口操作可能需要特定权限，请查阅官方文档。

---

### 8. ArkTS Lint 规则

#### 概述

ArkTS（TypeScript 的子集）的 Lint 规则，用于确保代码符合 HarmonyOS 开发规范。

- **总规则数量**: 67
- **严重程度**: error
- **适用范围**: ArkTS/TypeScript 代码

#### 核心限制规则

以下是 ArkTS 中最常见和重要的限制规则：

##### 类型系统

- ❌ 不支持 `any` 和 `unknown` 类型 - 必须显式指定类型
- ❌ 不支持交叉类型 - 使用继承作为替代方案
- ❌ 不支持条件类型 - 使用带约束的新类型或 Object 重写逻辑
- ❌ 不支持映射类型 - 使用常规类和接口
- ❌ 不支持字面量类型和 `as const` 断言

##### 对象和类

- ❌ 不支持对象字面量作为类型 - 必须显式声明类和接口
- ❌ 不支持索引签名 - 改用数组
- ❌ 不支持通过索引访问对象字段 `obj["field"]` - 使用 `obj.field`
- ❌ 不支持解构赋值和解构声明 - 使用临时变量
- ❌ 不支持 `delete` 运算符 - 使用可空类型并赋值为 null
- ❌ 不支持展开运算符（除了数组展开到 rest 参数或数组字面量）
- ❌ 不支持动态修改对象布局

##### 函数

- ❌ 不支持函数表达式 - 改用箭头函数
- ❌ 不支持嵌套函数 - 改用箭头函数
- ❌ 不支持 `Function.apply`、`Function.call`、`Function.bind`
- ❌ 不支持在函数上声明属性
- ❌ 不支持生成器函数 - 使用 async/await
- ❌ 不支持在独立函数中使用 `this`（仅限实例方法）

##### 模块和导入

- ❌ 不支持 `require` - 使用 ES6 `import`
- ❌ 不支持 `export =` 语法 - 使用普通的 export
- ❌ 不支持环境模块声明
- ❌ 不支持 UMD 模块
- ❌ 所有 import 语句必须在文件顶部

##### 高级特性

- ❌ 不支持命名空间作为对象
- ❌ 不支持声明合并
- ❌ 不支持 JSX
- ❌ 不支持 `Symbol()` API（除了 `Symbol.iterator`）
- ❌ 不支持 `with` 语句
- ❌ 不支持 `for...in` 循环（对于数组使用常规 for 循环）
- ❌ 不支持 `in` 运算符 - 使用 `instanceof`
- ❌ 不支持 `typeof` 进行类型标注
- ❌ 不支持 `new.target`
- ❌ 不支持 `globalThis`

##### 变量和类型断言

- ❌ 不支持 `var` - 使用 `let`
- ❌ 不支持确定性赋值断言 `let v!: T` - 使用带初始化的声明
- ❌ 不支持 `is` 运算符 - 使用 `instanceof`

##### 类和接口

- ❌ 不支持在构造函数中声明类字段
- ❌ 不支持接口中的调用签名和构造签名
- ❌ 不支持类字面量
- ❌ 不支持将类用作对象
- ❌ 不支持重新分配对象方法
- ❌ 不支持原型赋值
- ❌ 不支持私有标识符 `#` - 使用 `private` 关键字

##### 实用类型

ArkTS 仅支持以下 TypeScript 实用类型：
- ✅ `Partial<T>`
- ✅ `Required<T>`
- ✅ `Readonly<T>`
- ✅ `Record<K, V>`（注意：`rec[index]` 的类型为 `V | undefined`）
- ❌ 其他实用类型不支持

#### 迁移建议

当从 TypeScript 迁移到 ArkTS 时：

1. **类型系统**: 为所有变量、函数参数和返回值显式添加类型注解
2. **对象操作**: 使用类和接口替代对象字面量类型
3. **函数**: 使用箭头函数替代函数表达式和嵌套函数
4. **模块**: 使用标准 ES6 import/export 语法
5. **数据访问**: 使用点表示法而非索引访问
6. **解构**: 手动创建临时变量替代解构语法
7. **继承**: 使用类继承替代交叉类型

#### 使用说明

这些规则会在 DevEco Studio 中自动检查。当违反规则时：

1. IDE 会显示错误提示
2. 编译会失败
3. 按照建议进行修改

#### 参考资源

- [HarmonyOS ArkTS 开发指南](https://developer.huawei.com/consumer/en/doc/harmonyos-guides-V14/typescript-to-arkts-migration-guide-V14)
- [ArkTS 规范文档](https://gitee.com/openharmony/docs/blob/master/zh-cn/application-dev/quick-start/arkts-get-started.md)

---

### 9. 最佳实践总结

#### 性能优化关键点

1. **UI 渲染**: 使用 `LazyForEach`、避免深层嵌套、使用 `renderGroup`
2. **动画**: 优先改变 `transform` 和 `opacity`，避免修改布局属性
3. **组件复用**: 使用 `@Reusable` 和 `aboutToReuse`
4. **状态管理**: 避免冗余状态变量，使用 `StateStore` 集中管理

#### 代码质量关键点

1. **类型安全**: 严格遵循 ArkTS 类型规范，显式声明类型
2. **组件封装**: 使用 `attributeModifier` 统一组件 API
3. **资源管理**: 使用资源目录实现主题切换，避免硬编码
4. **路由管理**: 使用 HMRouter 简化页面导航

#### 用户体验关键点

1. **交互反馈**: 为所有用户操作提供即时视觉反馈
2. **主题适配**: 完整支持深浅色模式自动切换
3. **性能流畅**: 确保动画 60fps，列表滚动流畅
4. **手势冲突**: 正确使用 `hitTestBehavior` 和 `stopPropagation`

---

### 10. 开发工具

#### 推荐使用的工具

1. **DevEco Studio**: HarmonyOS 官方 IDE
2. **性能分析工具**:
   - CPU Profiler
   - UI Latency 分析器
   - Memory Profiler
3. **调试工具**:
   - UI 调试器
   - `hidumper` 状态分析
   - Code Linter

#### 代码检查

定期运行以下检查：

1. ArkTS Lint 规则检查
2. 性能规则扫描（如 `@performance/hp-arkui-remove-redundant-state-var`）
3. 代码复杂度分析
4. 内存泄漏检测

---

### 11. 总结

遵循本规范可以确保：

- ✅ 代码符合 HarmonyOS 官方规范
- ✅ 应用性能达到最优
- ✅ 用户体验流畅自然
- ✅ 代码易于维护和扩展
- ✅ 团队协作高效统一

在开发过程中，请始终参考本规范，并结合项目实际情况灵活应用。
