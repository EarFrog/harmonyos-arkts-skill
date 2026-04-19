# HarmonyOS ArkTS Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

面向纯血鸿蒙（HarmonyOS NEXT）应用开发的 OpenClaw AI Skill。

## 简介

本 Skill 为 ArkTS + ArkUI 开发者提供一站式开发辅助，涵盖组件设计、网络请求、状态管理、性能优化等核心场景的最佳实践与代码模板。

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

## 适用对象

- 鸿蒙应用开发者（个人/团队）
- 学习 ArkTS 与鸿蒙开发的初学者
- 需要快速查阅 API 与最佳实践的开发者

## 安装使用

### 通过 OpenClaw 安装

```bash
# 克隆到本地 skills 目录
cd ~/.qclaw/skills
git clone https://github.com/EarFrog/harmonyos-arkts-skill.git harmonyos-arkts
```

### 直接使用

在 OpenClaw 对话中，AI 将自动引用本 Skill 的文档来回答鸿蒙开发相关问题。

## 文档目录

```
references/
├── arkts-syntax.md       # ArkTS 语法与装饰器速查
├── component-patterns.md # 组件设计模式
├── http-client.md        # HTTP 请求封装
├── navigation.md         # 页面路由指南
├── storage-guide.md      # 本地存储方案
└── project-structure.md  # 项目结构规范
```

## 使用示例

### 示例 1：封装 HTTP 客户端

**问题**：如何封装一个带拦截器的 HTTP 客户端？

**解答**：参考 `references/http-client.md`，使用 `HttpClient` 类模板：

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
  data: Object[] = []
}

@Component
struct Child {
  @ObjectLink user: User  // 共享引用，无拷贝开销
}
```

更多示例详见各文档。

## 核心建议

### 时间计算

使用 `systemDateTime.getTime()` 替代 `Date.now()`，避免用户修改系统时间导致计算错误：

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

## 更新日志

| 日期 | 更新内容 |
|------|---------|
| 2025-04-19 | 添加时间计算最佳实践（`systemDateTime.getTime()`） |
| 2025-04-19 | 添加 `@Prop` 性能警告与替代方案 |
| 2025-04-18 | 初始版本，覆盖核心开发场景 |

## 相关资源

- [鸿蒙开发者官网](https://developer.harmonyos.com/)
- [ArkTS 语言指南](https://developer.harmonyos.com/cn/docs/documentation/doc-guides-V3/arkts-get-started-0000001632697705-V3)
- [ArkUI 声明式开发](https://developer.harmonyos.com/cn/docs/documentation/doc-guides-V3/arkui-overview-0000001632675437-V3)

## 许可证

[MIT](LICENSE)

---

**维护者**: [@EarFrog](https://github.com/EarFrog)  
如有问题，欢迎通过 GitHub Issues 交流
