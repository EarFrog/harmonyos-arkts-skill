# 页面路由与导航

## 目录

1. [Router 路由](#router-路由)
2. [Navigation 导航组件](#navigation-导航组件)
3. [页面间参数传递](#页面间参数传递)
4. [页面转场动画](#页面转场动画)
5. [最佳实践](#最佳实践)

---

## Router 路由

### 基础用法

```typescript
import { router } from '@kit.ArkUI'

// 跳转（压栈）
router.pushUrl({ url: 'pages/Detail' })

// 跳转并传参
router.pushUrl({
  url: 'pages/Detail',
  params: { id: 1001, title: '商品详情' }
})

// 替换当前页（不可返回）
router.replaceUrl({ url: 'pages/Login' })

// 返回上一页
router.back()

// 返回并传参
router.back({ url: 'pages/Index', params: { result: 'ok' } })

// 返回到指定页面
router.backToUrl({ url: 'pages/Home' })

// 清空栈并跳转
router.clear()
router.pushUrl({ url: 'pages/Login' })
```

### 接收参数

```typescript
import { router } from '@kit.ArkUI'

@Entry
@Component
struct Detail {
  @State id: number = 0
  @State title: string = ''

  aboutToAppear() {
    const params = router.getParams() as Record<string, string | number>
    if (params) {
      this.id = params.id as number
      this.title = params.title as string
    }
  }

  build() {
    Column() {
      Text(`ID: ${this.id}`)
      Text(this.title)
      Button('返回').onClick(() => router.back())
    }
  }
}
```

### 跳转模式

```typescript
import { RouterMode } from '@kit.ArkUI'

// Standard：每次跳转都压入新实例
router.pushUrl({ url: 'pages/Detail' }, router.RouterMode.Standard)

// Single：栈中已有则复用
router.pushUrl({ url: 'pages/Detail' }, router.RouterMode.Single)
```

### 路由拦截

```typescript
// 在 EntryAbility 中设置
import { UIAbility } from '@kit.AbilityKit'

export default class EntryAbility extends UIAbility {
  onWindowStageCreate(windowStage: window.WindowStage) {
    windowStage.loadContent('pages/Index', (err) => {
      if (err.code) {
        return
      }
    })
  }
}
```

### 路由配置

在 `main_pages.json` 中配置所有页面：

```json
{
  "src": [
    "pages/Index",
    "pages/Detail",
    "pages/Login",
    "pages/Profile",
    "pages/Settings"
  ]
}
```

---

## Navigation 导航组件

Navigation 是推荐的路由方案，替代传统 Router。

### 基础用法

```typescript
@Entry
@Component
struct NavigationDemo {
  @State pathStack: NavPathStack = new NavPathStack()

  build() {
    Navigation(this.pathStack) {
      // 首页内容
      Column() {
        Button('跳转详情').onClick(() => {
          this.pathStack.pushPath({ name: 'Detail', param: 'Hello' })
        })
      }
    }
    .title('首页')
    .navDestination(this.navDestinationBuilder)
  }

  @Builder
  navDestinationBuilder(name: string, param: Object) {
    if (name === 'Detail') {
      DetailPage({ pathStack: this.pathStack, content: param as string })
    } else if (name === 'Settings') {
      SettingsPage({ pathStack: this.pathStack })
    }
  }
}
```

### 目标页面

```typescript
@Component
struct DetailPage {
  @State pathStack: NavPathStack = new NavPathStack()
  content: string = ''

  build() {
    NavDestination() {
      Column() {
        Text(this.content).fontSize(20)
        Button('返回').onClick(() => { this.pathStack.pop() })
      }
    }
    .title('详情页')
    .hideBackButton(false)
  }
}
```

### NavPathStack 常用方法

```typescript
let stack: NavPathStack = new NavPathStack()

// 入栈
stack.pushPath({ name: 'Detail', param: { id: 1 } })
stack.pushPathByName('Detail', { id: 1 })  // 按名称

// 替换
stack.replacePath({ name: 'Login', param: null })
stack.replacePathByName('Login', null)

// 出栈
stack.pop()          // 弹出栈顶
stack.popToName('Home')  // 弹出到指定页
stack.popToIndex(0)      // 弹出到指定位置
stack.clear()            // 清空栈

// 查询
stack.size()          // 栈大小
stack.getParam(0)     // 获取指定位置参数
stack.getAllPathName()  // 所有路径名
```

### Navigation 样式

```typescript
Navigation(this.pathStack) {
  // 内容
}
.title('我的应用')
.titleMode(NavigationTitleMode.Mini)     // Mini / Full
.hideNavBar(false)                       // 隐藏导航栏
.hideToolBar(false)                      // 隐藏工具栏
.navBarWidth('100%')
.navBarHeight(56)
.mode(NavigationMode.Stack)              // Stack（导航栈）/ Split（分栏）
```