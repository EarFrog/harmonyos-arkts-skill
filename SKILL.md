---
name: harmonyos-arkts
description: |
  HarmonyOS NEXT (纯血鸿蒙) ArkTS + ArkUI 开发助手。
  当用户提到以下任何关键词时触发：鸿蒙、HarmonyOS、HarmonyOS NEXT、纯血鸿蒙、
  ArkTS、ArkUI、@Component、@State、@Link、@Prop、@Provide、@Consume、
  @Watch、@Builder、@Extend、@Styles、@Observed、@ObjectLink、
  AppStorage、LocalStorage、router、Navigation、ohos.net.http、
  Preferences、RelationalStore、systemDateTime、animateTo、transition、
  TapGesture、PanGesture、PinchGesture、Refresh、鸿蒙开发、鸿蒙App、鸿蒙组件。
  覆盖场景：生成 ArkTS 组件代码、页面路由、HTTP 请求封装、本地存储、
  UI 布局、项目结构规范、常见错误排查、API 速查。
metadata:
  openclaw:
    emoji: "🦋"
---

# HarmonyOS ArkTS 开发助手

## 目标平台

HarmonyOS NEXT (API 12+)，纯血鸿蒙，ArkTS + ArkUI 声明式开发范式。

## 核心约定

- 语言：ArkTS（TypeScript 的超集，有额外的编译期检查和装饰器）
- UI：ArkUI 声明式（`@Component` + `build()`）
- 代码风格：遵循 [ArkTS 编码规范](references/arkts-syntax.md)
- 状态管理：优先使用 `@State` / `@Link` / `@Provide` / `@Consume`
- 时间获取：使用 `systemDateTime.getTime()`（`@kit.BasicServicesKit`），不使用 `Date.now()`
- 错误处理：所有 Promise 调用必须 catch，详见 [arkts-syntax.md → Promise 使用规范](references/arkts-syntax.md)
- 性能优先：避免 `@Prop` 传递大数据对象，优先 `@ObjectLink`

## 参考文档索引

根据任务类型加载对应参考文档：

| 任务类型 | 参考文档 |
|---------|---------|
| ArkTS 语法、装饰器、类型系统、生命周期、Promise | [arkts-syntax.md](references/arkts-syntax.md) |
| UI 布局、动画、手势交互 | [ui-layout.md](references/ui-layout.md) |
| 页面路由跳转、Navigation、Tab 组合 | [navigation-router.md](references/navigation-router.md) |
| HTTP 网络请求、WebSocket | [network-http.md](references/network-http.md) |
| 本地存储（Preferences/RelationalStore） | [storage.md](references/storage.md) |
| 项目/模块/包结构规范 | [project-structure.md](references/project-structure.md) |
| 常见错误排查、权限管理、真机调试 | [troubleshooting.md](references/troubleshooting.md) |

## 代码生成规范

### 组件生成

生成 `@Component` 时必须包含：
1. 装饰器（`@Component`、`@Entry`（如为入口页面）、`@State` / `@Link` 等）
2. `build()` 方法，内部使用 ArkUI 声明式语法
3. 必要的生命周期方法（`aboutToAppear`、`aboutToDisappear`）
4. 类型注解完整，不使用 `any`

### 示例：基础组件模板

```typescript
@Component
export struct MyComponent {
  @State message: string = 'Hello'
  private timer: number = -1

  aboutToAppear(): void {
    // 初始化逻辑
  }

  aboutToDisappear(): void {
    if (this.timer !== -1) {
      clearInterval(this.timer)
    }
  }

  build() {
    Column() {
      Text(this.message)
        .fontSize(16)
        .fontColor('#333333')
    }
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
  }
}
```

### 命名规范

- 组件名：PascalCase（`UserCard`、`NewsList`）
- 变量/函数：camelCase（`userName`、`fetchData`）
- 常量：UPPER_SNAKE_CASE（`MAX_COUNT`）
- 文件名：与组件名一致（`UserCard.ets`）
- 接口前缀：`I`（`IUserData`）

### 禁止事项

- 禁止使用 `any` 类型
- 禁止在 `build()` 中执行副作用（网络请求、定时器等）
- 禁止直接操作 DOM（ArkUI 无 DOM）
- 禁止使用 `eval()`
- 禁止在 UI 线程执行耗时操作，使用 `@ohos.taskpool` 或 Worker
- 禁止使用 `Date.now()` / `new Date()` 获取时间戳，必须使用 `systemDateTime.getTime()`
- 禁止不 catch Promise 返回值，所有返回 Promise 的函数调用必须 try-catch 或 .catch()
- 禁止使用 `@Prop` 传递大数据对象（深拷贝性能差），改用 `@ObjectLink` 或拆分字段
- 禁止使用 `enum`，使用 `const` 对象 + union type 替代
- 禁止使用 `for...in`，使用 `Object.entries` 替代
