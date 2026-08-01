# HarmonyOS NEXT Development Skill

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

面向纯血鸿蒙（HarmonyOS NEXT）ArkTS、ArkUI 与 Native/NDK 应用开发的 AI Skill。

## 简介

本 Skill 提供统一的 HarmonyOS NEXT 开发入口，覆盖 ArkTS/ArkUI 应用开发、Android 迁移，以及 Node-API、CMake、XComponent、Native Drawing、EGL/GLES 等 Native/NDK 工程场景。

## 功能特性

| 模块 | 内容 |
|------|------|
| **组件开发** | 自定义组件设计模式、装饰器使用指南、性能优化建议 |
| **页面路由** | 路由配置、页面跳转、参数传递、生命周期管理 |
| **网络请求** | 基于 `@kit.NetworkKit` 的 HTTP 客户端封装 |
| **数据存储** | AppStorage、LocalStorage、Preferences 使用方案 |
| **UI 布局** | 声明式 UI 语法、布局技巧、适配方案 |
| **项目规范** | 目录结构、模块划分、代码规范 |
| **问题排查** | 常见错误诊断、调试技巧、解决方案 |
| **API 速查** | 装饰器、工具函数、系统 API 快速参考 |
| **Android 迁移** | Android 项目分析、迁移计划、资源转换、UI 映射、验证流程 |
| **Native/NDK** | Node-API 契约、CMake/ABI、生命周期、线程与内存安全 |
| **Native 渲染** | XComponent、NativeWindow、Native Drawing、EGL/GLES 与画布性能 |
| **静态审计** | 检查 CMake、注册、ArkTS import、类型声明和 Native 高风险路径 |

## 适用对象

- 鸿蒙应用开发者（个人/团队）
- Android 应用迁移到 HarmonyOS NEXT 的开发者
- HarmonyOS Native/NDK、图形和高性能模块开发者
- 学习 ArkTS 与鸿蒙开发的初学者
- 需要快速查阅 API 与最佳实践的开发者

## 安装使用

### 通过 【你的ai】 安装，如codex：

```bash
# 克隆到本地 skills 目录
cd ~/.codex/skills
git clone https://github.com/EarFrog/harmonyos-arkts-skill.git harmonyos-arkts
```

### 直接使用

在与 AI 对话中，AI 将自动引用本 Skill 的文档来回答鸿蒙开发相关问题。

## 文档目录

```
references/
├── arkts-syntax.md       # ArkTS 语法与装饰器速查
├── ui-layout.md          # UI 布局、动画、手势交互
├── navigation-router.md  # 页面路由与导航
├── network-http.md       # HTTP 网络请求、WebSocket
├── storage.md            # 本地存储方案
├── project-structure.md  # 项目结构规范
├── troubleshooting.md    # ArkTS、ArkUI 与应用常见错误排查
├── android-migration.md           # Android 到 HarmonyOS 迁移流程
├── android-ui-mapping.md          # Android UI/XML 到 ArkUI 映射
├── android-resource-migration.md        # Android 资源迁移
├── native-engineering-lessons.md        # Native 工程审查入口
├── native-napi-process.md               # Node-API 注册与契约
├── native-arkts-interop.md              # ArkTS 与 Native 互操作
├── native-safety.md                     # 生命周期、线程与内存安全
├── native-cmake-build.md                # CMake、Hvigor、ABI 与三方库
├── native-debugging.md                  # 编译、加载、崩溃与图形排障
├── native-canvas-performance.md         # 画布和手写性能
├── native-architecture-patterns.md      # Native 状态与资源架构
├── native-rendering-architecture.md     # Native 渲染架构
├── native-persistence-export-scheduling.md # 持久化、导出与任务调度
└── native-official-node-api-guide.md    # 官方资料与版本核对

scripts/
└── audit_harmony_native.py  # 只读 Native 静态审计
```

## Native 静态审计

```bash
python3 scripts/audit_harmony_native.py /path/to/project
python3 scripts/audit_harmony_native.py /path/to/project --module drawing --strict
python3 scripts/audit_harmony_native.py /path/to/project --json
```

脚本只提供静态证据，不能替代项目构建、动态注册检查和目标设备验证。

## 使用示例

### 示例 1：封装 HTTP 客户端

**问题**：如何封装一个带拦截器的 HTTP 客户端？

**解答**：参考 `references/network-http.md`，使用 `HttpClient` 类模板：

```typescript
import { http } from '@kit.NetworkKit'

class HttpClient {
    private interceptors: Interceptor[] = []

    request<T>(config: RequestConfig): Promise<T> {
        // 请求拦截 → 发起请求 → 响应拦截 → 返回结果
    }
}
```

### 示例 2：优化大数据传递

**问题**：`@Prop` 传递大数据对象导致卡顿？

**解答**：`@Prop` 会进行深拷贝，建议改用 `@ObjectLink`：

```typescript
@Observed
class User {
    name: string = ''
    tags: string[] = []
}

@Component
struct Child {
    @ObjectLink user: User  // 共享引用，无拷贝开销
}
```

更多示例详见各文档。

## 核心建议

### 时间计算

涉及时间戳、耗时、超时、排序等时间计算时，使用 `systemDateTime.getTime()` 替代 `Date.now()` / `new Date()`：

```typescript
import { systemDateTime } from '@kit.BasicServicesKit'
const timestamp = systemDateTime.getTime()
```

### 状态管理选择

| 装饰器 | 拷贝行为 | 适用场景 |
|--------|---------|---------|
| `@Prop` | 深拷贝 | 小数据、primitive 类型 |
| `@Link` | 不拷贝 | 需要双向同步 |
| `@ObjectLink` | 不拷贝 | 观察对象内部变化 |

## 贡献指南

欢迎提交 Issue 和 PR！

- **报告问题**：使用 GitHub Issues，描述问题场景和期望行为
- **提交改进**：Fork 后修改，提交 Pull Request
- **补充文档**：发现遗漏的 API 或最佳实践，欢迎补充


## 相关资源

- [鸿蒙开发者官网](https://developer.harmonyos.com/)
- [ArkTS 语言指南](https://developer.harmonyos.com/cn/docs/documentation/doc-guides-V3/arkts-get-started-0000001632697705-V3)
- [ArkUI 声明式开发](https://developer.harmonyos.com/cn/docs/documentation/doc-guides-V3/arkui-overview-0000001632675437-V3)

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 开源。

---

**维护者**: [@EarFrog](https://github.com/EarFrog)
如有问题，欢迎通过 GitHub Issues 交流
