# 页面路由与导航

## 目录

1. [Router 路由](#router-路由)
2. [Navigation 导航组件](#navigation-导航组件)
3. [页面间参数传递](#页面间参数传递)
4. [页面转场动画](#页面转场动画)
5. [最佳实践](#最佳实践)
6. [Tab + Navigation 组合模式](#tab--navigation-组合模式)

---

## Router 路由

### 基础用法

```typescript
import { router } from '@kit.ArkUI'

// 跳转（压栈）
router.pushUrl({ url: 'pages/Detail' }).catch(err => {
    console.error(`页面跳转失败: ${err.message}`)
})

// 跳转并传参
router.pushUrl({
    url: 'pages/Detail',
    params: { id: 1001, title: '商品详情' }
}).catch(err => {
    console.error(`页面跳转失败: ${err.message}`)
})

// 替换当前页（不可返回）
router.replaceUrl({ url: 'pages/Login' }).catch(err => {
    console.error(`页面跳转失败: ${err.message}`)
})

// 返回上一页
router.back().catch(err => {
    console.error(`页面返回失败: ${err.message}`)
})

// 返回并传参
router.back({ url: 'pages/Index', params: { result: 'ok' } }).catch(err => {
    console.error(`页面返回失败: ${err.message}`)
})

// 返回到指定页面
router.backToUrl({ url: 'pages/Home' }).catch(err => {
    console.error(`页面返回失败: ${err.message}`)
})

// 清空栈并跳转
router.clear()
router.pushUrl({ url: 'pages/Login' }).catch(err => {
    console.error(`页面跳转失败: ${err.message}`)
})
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
            Button('返回').onClick(() => {
                router.back().catch(err => {
                    console.error(`页面返回失败: ${err.message}`)
                })
            })
        }
    }
}
```

### 跳转模式

```typescript
import { RouterMode } from '@kit.ArkUI'

// Standard：每次跳转都压入新实例
router.pushUrl({ url: 'pages/Detail' }, router.RouterMode.Standard).catch(err => {
    console.error(`页面跳转失败: ${err.message}`)
})

// Single：栈中已有则复用
router.pushUrl({ url: 'pages/Detail' }, router.RouterMode.Single).catch(err => {
    console.error(`页面跳转失败: ${err.message}`)
})
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

---

## Tab + Navigation 组合模式

底部 Tab 与 Navigation 导航是实际项目中最常见的组合。下面给出两种主流实现方式。

### 方式一：自定义 TabBar + Stack 切换

```typescript
// 底部 Tab + Navigation 常见组合
@Entry
@Component
struct MainTab {
    @State currentIndex: number = 0
    @State pathStack: NavPathStack = new NavPathStack()

    // Tab 配置
    private tabs: ITab[] = [
        { title: '首页', icon: $r('app.media.home'), activeIcon: $r('app.media.home_active') },
        { title: '分类', icon: $r('app.media.category'), activeIcon: $r('app.media.category_active') },
        { title: '我的', icon: $r('app.media.profile'), activeIcon: $r('app.media.profile_active') }
    ]

    build() {
        Column() {
            // 内容区域
            Stack() {
                if (this.currentIndex === 0) {
                    HomePage()
                } else if (this.currentIndex === 1) {
                    CategoryPage()
                } else {
                    ProfilePage()
                }
            }
            .layoutWeight(1)

            // 底部 TabBar
            Row() {
                ForEach(this.tabs, (tab: ITab, index?: number) => {
                    Column() {
                        Image(this.currentIndex === index ? tab.activeIcon : tab.icon)
                            .width(24).height(24)
                        Text(tab.title)
                            .fontSize(10)
                            .fontColor(this.currentIndex === index ? '#007DFF' : '#999999')
                    }
                    .layoutWeight(1)
                    .onClick(() => { this.currentIndex = index ?? 0 })
                })
            }
            .width('100%')
            .height(56)
            .backgroundColor('#FFFFFF')
            .border({ width: { top: 0.5 }, color: '#EEEEEE' })
        }
        .width('100%')
        .height('100%')
    }
}
```

### 方式二：Navigation + Tabs 组件

```typescript
@Entry
@Component
struct NavTabsDemo {
    private navStack: NavPathStack = new NavPathStack()
    @State currentIndex: number = 0

    build() {
        Column() {
            Tabs({ index: this.currentIndex }) {
                TabContent() {
                    Navigation(this.navStack) {
                        HomePage()
                    }
                    .title('首页')
                    .navDestination(this.buildNavDestination)
                }.tabBar(this.tabBuilder('首页', 0))

                TabContent() {
                    CategoryPage()
                }.tabBar(this.tabBuilder('分类', 1))

                TabContent() {
                    ProfilePage()
                }.tabBar(this.tabBuilder('我的', 2))
            }
            .onChange((index: number) => { this.currentIndex = index })
        }
    }

    @Builder
    tabBuilder(title: string, index: number) {
        Column() {
            Text(title)
                .fontSize(this.currentIndex === index ? 14 : 12)
                .fontColor(this.currentIndex === index ? '#007DFF' : '#999999')
        }
    }

    @Builder
    buildNavDestination(name: string, param: Object) {
        // 路由目标页
    }
}
```