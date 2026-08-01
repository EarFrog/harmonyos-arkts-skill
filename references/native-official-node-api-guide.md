# 官方资料与版本核对

## 来源优先级

按以下顺序解决 API 行为和版本差异：

1. 工程实际 compileSdk/compatibleSdk、构建日志和生成产物。
2. 该 SDK 安装目录中的头文件与注释。
3. 与目标 API 版本匹配的华为官方指南/API reference。
4. 示例代码和本 skill 的案例提炼。

案例与官方/SDK 冲突时，以匹配版本 SDK 和官方文档为准。不要在 skill 中写死“最新更新时间”或旧版 `-Vxx` URL。

## 本地 SDK 重点头文件

在实际 SDK root 下查找：

- `native/sysroot/usr/include/napi/native_api.h`
- `native/sysroot/usr/include/node_api.h`
- `native/sysroot/usr/include/node_api_types.h`
- `native/sysroot/usr/include/arkui/native_node_napi.h`
- `native/sysroot/usr/include/arkui/native_node.h`
- `native/sysroot/usr/include/native_drawing/`
- `native/sysroot/usr/include/EGL/`
- `native/sysroot/usr/include/GLES3/`

用头文件确认：

- API 起始版本和 deprecated 标记。
- 函数输出参数、返回 status 和允许的 null 参数。
- `NAPI_MODULE` 的真实展开与注册名。
- ArrayBuffer/TypedArray 的目标版本行为。
- ArkUI/XComponent/Native Drawing 对线程和生命周期的约束。

## 官方入口

| 主题 | 官方页面 |
| --- | --- |
| Node-API 交互总入口 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/using-napi-interaction-with-cpp> |
| Node-API 简介 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/napi-introduction> |
| 状态码 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/napi_status_introduction> |
| 数据类型与接口 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/napi-data-types-interfaces> |
| 开发规范 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/napi-guidelines> |
| 交互开发流程 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/use-napi-process> |
| 接口使用 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/napi-use> |
| 典型场景 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/napi-scenarios> |
| NDK 概述 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/ndk-development-overview> |
| 命令行/Hvigor 构建 | <https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/ide-command-line-building-app> |

图形 API 页面名称和版本变化较快。需要 XComponent、NativeWindow、Native Drawing、EGL/GLES 细节时，从当前官方文档中心或本地头文件按具体符号检索，不凭记忆补库名或线程规则。
