# HarmonyOS ArkTS Skill

面向纯血鸿蒙（HarmonyOS NEXT）应用开发的 AI 助手技能包。

## 作用

这个 Skill 帮助开发者高效进行 **ArkTS + ArkUI** 鸿蒙应用开发，提供：

| 能力 | 说明 |
|------|------|
| **组件代码生成** | 根据需求生成符合鸿蒙规范的 ArkTS 组件代码 |
| **页面路由** | 路由配置、跳转逻辑、参数传递的最佳实践 |
| **HTTP 请求封装** | 基于 `@kit.NetworkKit` 的网络请求封装模板 |
| **本地存储** | AppStorage、LocalStorage、Preferences 的使用指南 |
| **UI 布局** | ArkUI 声明式语法、布局技巧、性能优化 |
| **模块结构** | 项目目录组织、模块划分、代码规范 |
| **错误排查** | 常见错误诊断与解决方案 |
| **API 速查** | 常用 API、装饰器、工具函数的快速参考 |

## 适用场景

- 🚀 个人鸿蒙 App 项目开发
- 📚 学习 ArkTS 语法和鸿蒙开发规范
- 🔧 快速查找 API 用法和最佳实践
- 🐛 解决开发中遇到的具体问题

## 核心特性

- **纯血鸿蒙**：针对 HarmonyOS NEXT（API 12+）设计
- **性能优先**：内置性能优化建议（如避免 `@Prop` 深拷贝）
- **最佳实践**：基于官方文档和实际项目经验整理
- **即查即用**：速查文档 + 代码模板，提升开发效率

## 文档结构

```
references/
├── arkts-syntax.md      # ArkTS 语法速查
├── component-patterns.md # 组件设计模式
├── http-client.md       # HTTP 请求封装
├── navigation.md        # 页面路由指南
├── storage-guide.md     # 本地存储方案
└── project-structure.md # 项目结构规范
```

## 使用示例

**问**：如何封装一个带拦截器的 HTTP 客户端？

**答**：参考 `references/http-client.md` 中的 `HttpClient` 类模板，包含：
- 请求/响应拦截器
- 统一错误处理
- Token 自动注入

**问**：`@Prop` 传递大数据对象卡顿怎么办？

**答**：`@Prop` 会深拷贝，建议改用 `@ObjectLink` 或拆分字段传递。详见 `references/arkts-syntax.md` → @Prop 性能问题。

## 更新日志

- **2025-04-19**: 添加鸿蒙时间计算最佳实践（`systemDateTime.getTime()`）
- **2025-04-19**: 添加 `@Prop` 性能警告和替代方案
- **2025-04-18**: 初始版本，覆盖核心开发场景

## 相关链接

- [鸿蒙开发者官网](https://developer.harmonyos.com/)
- [ArkTS 语言指南](https://developer.harmonyos.com/cn/docs/documentation/doc-guides-V3/arkts-get-started-0000001632697705-V3)
- [ArkUI 声明式开发](https://developer.harmonyos.com/cn/docs/documentation/doc-guides-V3/arkui-overview-0000001632675437-V3)

---

**维护者**: @EarFrog  
**许可证**: MIT
