# ArkTS 语法速查

## 目录

1. [装饰器](#装饰器)
2. [类型系统](#类型系统)
3. [UI 描述](#ui-描述)
4. [生命周期](#生命周期)
5. [状态管理最佳实践](#状态管理最佳实践)
6. [常用工具函数](#常用工具函数)
7. [Promise 使用规范](#promise-使用规范)

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

轻量 UI 复用函数，内部可引用组件状态。

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

扩展原生组件样式，不支持传参（无参）。

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

抽取通用样式，支持全局和组件内。

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
