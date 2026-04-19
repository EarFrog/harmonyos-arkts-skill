# 常见错误排查

## 目录

1. [编译错误](#编译错误)
2. [运行时错误](#运行时错误)
3. [UI 渲染问题](#ui-渲染问题)
4. [网络请求问题](#网络请求问题)
5. [状态管理问题](#状态管理问题)
6. [性能问题](#性能问题)
7. [调试技巧](#调试技巧)

---

## 编译错误

### ❌ `Cannot find name 'xxx'`

**原因**：变量/函数未定义或未导入

**解决**：
```typescript
// 检查是否导入
import { router } from '@kit.ArkUI'

// 检查变量是否声明
let userName: string = ''  // 不要忘记 let/const
```

### ❌ `Type 'xxx' is not assignable to type 'yyy'`

**原因**：类型不匹配

**解决**：
```typescript
// 检查类型定义
interface IUser {
  id: number
  name: string
}

// 错误：传入类型不对
const user: IUser = { id: '123', name: '张三' }  // id 应该是 number

// 正确
const user: IUser = { id: 123, name: '张三' }
```

### ❌ `Property 'xxx' does not exist on type 'yyy'`

**原因**：访问了对象上不存在的属性

**解决**：
```typescript
// 错误
let data = { name: '张三' }
console.log(data.age)  // age 不存在

// 正确：使用可选链
console.log(data?.age)

// 或定义完整接口
interface IPerson {
  name: string
  age?: number  // 可选属性
}
```

### ❌ `ArkTS:Cannot use 'any' type`

**原因**：ArkTS 禁止使用 `any`

**解决**：
```typescript
// ❌ 禁止
let data: any = {}

// ✅ 使用具体类型
let data: Record<string, string> = {}

// ✅ 使用 unknown + 类型守卫
let data: unknown = {}
if (typeof data === 'object' && data !== null) {
  // ...
}
```

### ❌ `ArkTS:Cannot use 'enum'`

**原因**：ArkTS 禁止使用 `enum`

**解决**：
```typescript
// ❌ 禁止
enum Status { Loading, Success, Error }

// ✅ 使用 const 对象 + union
const Status = {
  Loading: 'loading',
  Success: 'success',
  Error: 'error'
} as const
type Status = typeof Status[keyof typeof Status]
```

### ❌ `ArkTS:Cannot use 'for...in'`

**原因**：ArkTS 禁止 `for...in`

**解决**：
```typescript
// ❌ 禁止
for (let key in obj) { }

// ✅ 使用 Object.entries
for (let [key, value] of Object.entries(obj)) { }
```

---

## 运行时错误

### ❌ `Cannot read property 'xxx' of undefined`

**原因**：访问了 `undefined` 或 `null` 的属性

**解决**：
```typescript
// ❌ 危险
let name = user.profile.name

// ✅ 使用可选链
let name = user?.profile?.name ?? '默认名称'

// ✅ 提前判空
if (user && user.profile) {
  let name = user.profile.name
}
```

### ❌ `JSON.parse error`

**原因**：JSON 字符串格式错误

**解决**：
```typescript
// ❌ 直接解析可能崩溃
let data = JSON.parse(jsonStr)

// ✅ try-catch 包裹
try {
  let data = JSON.parse<IUserData>(jsonStr)
} catch (e) {
  console.error('JSON parse failed:', e)
  // 处理错误
}
```

### ❌ `Network request failed`

**原因**：网络请求失败

**检查项**：
1. 是否在 `module.json5` 中声明 `ohos.permission.INTERNET` 权限
2. URL 是否正确（是否包含协议 `https://`）
3. 设备是否联网
4. 服务器是否可访问

```json
// module.json5
{
  "module": {
    "requestPermissions": [
      { "name": "ohos.permission.INTERNET" }
    ]
  }
}
```

---

## UI 渲染问题

### ❌ 组件不显示

**排查步骤**：
1. 检查父容器是否设置了 `width` / `height`
2. 检查是否被其他组件遮挡（`Stack` 层级）
3. 检查 `visibility` 属性
4. 检查条件渲染 `if` 的条件

```typescript
// 常见问题：没有设置尺寸
Column() {
  Text('内容')
}
// ❌ 没有设置尺寸，可能不可见

// ✅ 设置明确尺寸
Column() {
  Text('内容')
}
.width('100%')
.height('100%')
```

### ❌ 列表不刷新

**原因**：数据变化但 UI 未更新

**解决**：
```typescript
// ❌ 直接修改数组元素不会触发刷新
this.list[0].name = '新名称'

// ✅ 方式1：替换整个数组
this.list = [...this.list]

// ✅ 方式2：使用 @Observed + @ObjectLink
@Observed
class Item {
  name: string = ''
}

@Component
struct ItemComponent {
  @ObjectLink item: Item  // 深层监听
}
```

### ❌ 布局溢出

**原因**：子元素超出父容器

**解决**：
```typescript
// ✅ 使用 clip 裁剪
Image($r('app.media.banner'))
  .width('100%')
  .height(200)
  .clip(true)  // 裁剪超出部分

// ✅ 使用 layoutWeight
Row() {
  Text('标题').layoutWeight(1)  // 占据剩余空间
  Button('操作').width(80)
}
```

### ❌ 键盘弹起遮挡输入框

**解决**：
```typescript
// 使用 expandSafeArea
Column() {
  TextInput()
    .expandSafeArea([SafeAreaType.KEYBOARD])  // 键盘弹起时自动避让
}
```

---

## 网络请求问题

### ❌ HTTP 请求无响应

**检查项**：
1. 是否声明 `INTERNET` 权限
2. 是否忘记调用 `destroy()`
3. 超时时间是否过短

```typescript
// ✅ 正确流程
let httpRequest = http.createHttp()
try {
  const response = await httpRequest.request(url, options)
  // 处理响应
} finally {
  httpRequest.destroy()  // 必须销毁
}
```

### ❌ HTTPS 证书问题

**解决**：
- 生产环境：使用正规 CA 证书
- 测试环境：在 `module.json5` 中配置网络安全策略

### ❌ 请求返回 401

**原因**：未登录或 Token 过期

**解决**：
```typescript
// 在请求拦截器中统一处理
if (response.code === 401) {
  // 清除本地 Token
  await prefUtil.remove('token')
  // 跳转登录页
  router.replaceUrl({ url: 'pages/Login' })
}
```

---

## 状态管理问题

### ❌ @State 不更新

**原因**：
1. 直接修改对象属性（非顶层）
2. 修改数组元素

**解决**：
```typescript
// ❌ 直接修改对象属性
this.user.name = '新名称'  // 不触发刷新

// ✅ 整体替换对象
this.user = { ...this.user, name: '新名称' }

// ❌ 直接修改数组元素
this.list[0].name = '新名称'

// ✅ 替换数组
this.list = [...this.list]

// ✅ 或使用 @Observed + @ObjectLink
```

### ❌ @Link 传参错误

**原因**：忘记使用 `$` 传递引用

**解决**：
```typescript
// ❌ 错误：直接传值
Child({ count: this.count })

// ✅ 正确：使用 $ 传递引用
Child({ count: $count })
```

### ❌ @Provide / @Consume 找不到

**原因**：名称不匹配或不在同一组件树

**解决**：
```typescript
// 确保名称一致
@Provide theme: string = 'dark'  // 提供者
@Consume theme: string           // 消费者

// 使用别名
@Provide('appTheme') theme: string = 'dark'
@Consume('appTheme') currentTheme: string
```

---

## 性能问题

### ❌ 列表滚动卡顿

**原因**：列表项过于复杂或未使用懒加载

**解决**：
```typescript
// ✅ 使用 LazyForEach
List() {
  LazyForEach(this.dataSource, (item: IItem) => {
    ListItem() {
      ItemComponent({ item })
    }
  })
}
.cachedCount(5)  // 缓存屏幕外 item

// ✅ 减少列表项复杂度
// 避免在 ListItem 中使用复杂动画
```

### ❌ 页面加载慢

**原因**：首屏数据过多或同步加载

**解决**：
```typescript
// ✅ 分步加载
aboutToAppear() {
  this.loadEssentialData()  // 先加载必要数据
}

onPageShow() {
  this.loadSecondaryData()  // 页面显示后加载次要数据
}

// ✅ 使用骨架屏
if (this.loading) {
  SkeletonScreen()
} else {
  RealContent()
}
```

### ❌ 内存泄漏

**原因**：未清理定时器、监听器

**解决**：
```typescript
@Component
struct MyComponent {
  private timer: number = -1

  aboutToAppear() {
    this.timer = setInterval(() => { }, 1000)
  }

  aboutToDisappear() {
    // ✅ 必须清理
    if (this.timer !== -1) {
      clearInterval(this.timer)
    }
  }
}
```

---

## 调试技巧

### 1. 日志输出

```typescript
import { hilog } from '@kit.PerformanceAnalysisKit'

const TAG = 'MyApp'

hilog.info(0x0000, TAG, '普通信息')
hilog.debug(0x0000, TAG, '调试信息')
hilog.warn(0x0000, TAG, '警告信息')
hilog.error(0x0000, TAG, '错误信息')
```

### 2. 断点调试

- DevEco Studio 支持断点调试
- 在代码行号处点击添加断点
- Debug 模式运行

### 3. 性能分析

- DevEco Studio → Profiler
- 分析 CPU、内存、网络

### 4. 检查组件树

- DevEco Studio → View Hierarchy
- 查看组件层级和属性

### 5. 网络请求抓包

- DevEco Studio → Network Profiler
- 查看请求详情和响应
