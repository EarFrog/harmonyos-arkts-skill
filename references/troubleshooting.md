# 常见错误排查

## 目录

1. [编译错误](#编译错误)
2. [运行时错误](#运行时错误)
3. [UI 渲染问题](#ui-渲染问题)
4. [网络请求问题](#网络请求问题)
5. [状态管理问题](#状态管理问题)
6. [权限管理](#权限管理)
7. [性能问题](#性能问题)
8. [调试技巧](#调试技巧)
9. [真机调试问题](#真机调试问题)

---

## 编译错误

### 编译环境保护约束

修改鸿蒙业务代码、页面代码、资源或配置后，可以运行项目已有的编译命令做校验，但禁止为了让编译通过而修改编译环境。

禁止自动修改：

- DevEco Studio、SDK、JDK、Node、ohpm、hvigor 等工具链
- `local.properties`、PATH、shell profile、本机环境变量
- 签名证书、Profile、自动签名配置
- ohpm 全局缓存、SDK 安装目录、本机工具目录

如果编译失败指向环境、依赖安装、签名或本机路径问题，应停止修改并报告阻塞项；只有编译器明确指向本次代码变更产生的 ArkTS、资源、权限或项目源码问题时，才继续修代码。

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

// ✅ 已知结构时声明 interface
interface IUserData {
    id: number
    name: string
}
let userData: IUserData = { id: 1, name: 'Tom' }
```

### ❌ `ArkTS:Cannot use 'enum'`

**原因**：ArkTS 禁止使用 `enum`

**解决**：
```typescript
// ❌ 禁止
enum Status { Loading, Success, Error }

// ✅ 使用常量类，避免 enum、字面量类型和 as const
class Status {
    static readonly Loading: string = 'loading'
    static readonly Success: string = 'success'
    static readonly Error: string = 'error'
}
```

### ❌ `ArkTS:Cannot use 'for...in'`

**原因**：ArkTS 禁止 `for...in`

**解决**：
```typescript
// ❌ 禁止
for (let key in obj) { }

// ✅ 将动态对象改为数组化键值结构，再用常规 for 循环
interface IKeyValue {
    key: string
    value: string
}

let items: IKeyValue[] = [
    { key: 'name', value: 'Tom' },
    { key: 'city', value: 'Shenzhen' }
]

for (let i = 0; i < items.length; i++) {
    let item = items[i]
    console.info(`${item.key}: ${item.value}`)
}
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

// ✅ 整体替换对象，显式拷贝字段
const newUser: IUser = {
    id: this.user.id,
    name: '新名称',
    avatar: this.user.avatar
}
this.user = newUser

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

## 权限管理

### ❌ 权限未声明

**现象**：调用 API 报错 `Permission denied`

**解决**：
```json
// module.json5 中声明权限
{
    "module": {
        "requestPermissions": [
            { "name": "ohos.permission.INTERNET" },
            { "name": "ohos.permission.GET_WIFI_INFO" },
            { "name": "ohos.permission.APPROXIMATELY_LOCATION" },
            { "name": "ohos.permission.LOCATION" }
        ]
    }
}
```

### ❌ 动态授权被拒绝

**原因**：敏感权限需要运行时弹窗授权

**解决**：
```typescript
import { abilityAccessCtrl, bundleManager, Permissions } from '@kit.AbilityKit'

async function requestPermission(context: Context, permission: Permissions): Promise<boolean> {
    const atManager = abilityAccessCtrl.createAtManager()
    try {
        const result = await atManager.requestPermissionsFromUser(context, [permission])
        return result.authResults[0] === 0  // 0 = 授权成功
    } catch (err) {
        console.error(`请求权限失败: ${(err as Error).message}`)
        return false
    }
}

// 使用
const granted = await requestPermission(this.context, 'ohos.permission.LOCATION')
if (granted) {
    // 执行需要权限的操作
} else {
    promptAction.showToast({ message: '需要位置权限才能使用此功能' })
}
```

### 常用权限分级

| 权限 | 类型 | 说明 |
|------|------|------|
| `ohos.permission.INTERNET` | normal | 网络访问（声明即可） |
| `ohos.permission.GET_WIFI_INFO` | normal | WiFi 信息（声明即可） |
| `ohos.permission.APPROXIMATELY_LOCATION` | user_grant | 大概位置（需动态授权） |
| `ohos.permission.LOCATION` | user_grant | 精确位置（需动态授权） |
| `ohos.permission.CAMERA` | user_grant | 相机（需动态授权） |
| `ohos.permission.READ_MEDIA` | user_grant | 读取媒体文件（需动态授权） |
| `ohos.permission.WRITE_MEDIA` | user_grant | 写入媒体文件（需动态授权） |
| `ohos.permission.NOTIFICATION_CONTROLLER` | system_core | 通知（系统应用才有） |

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

---

## 真机调试问题

### ❌ 设备连接不上

**排查步骤**：
1. USB 线是否支持数据传输（非仅充电线）
2. 手机是否开启开发者模式和 USB 调试
3. DevEco Studio 是否识别到设备
4. 执行 `hdc list targets` 检查设备列表

```bash
# hdc 是鸿蒙的设备调试工具（类似 adb）
hdc list targets              # 列出已连接设备
hdc install xxx.hap           # 安装应用
hdc shell                     # 进入设备 shell
hdc log -x                    # 查看日志
```

### ❌ 签名配置错误

**现象**：安装 HAP 时报签名错误

**解决**：
1. 在 AGC（AppGallery Connect）创建项目和应用
2. 生成调试签名证书和 Profile
3. 在 DevEco Studio → File → Project Structure → Signing Configs 中配置
4. 勾选「Automatically generate signature」

### ❌ 真机运行白屏

**排查步骤**：
1. 检查 EntryAbility 中 `loadContent` 路径是否正确
2. 检查 `main_pages.json` 中是否注册了页面
3. 查看 log 日志是否有崩溃信息
4. 检查是否缺少权限导致功能异常
