# CMake、Hvigor、ABI 与三方库

## 目录

- [构建链](#构建链)
- [目标级 CMake](#目标级-cmake)
- [系统 Native 库](#系统-native-库)
- [预编译三方库](#预编译三方库)
- [失败策略](#失败策略)
- [排查顺序](#排查顺序)

## 构建链

先确认模块级 `build-profile.json5`：

```json5
{
  "buildOption": {
    "externalNativeOptions": {
      "path": "./src/main/cpp/CMakeLists.txt",
      "arguments": "",
      "cppFlags": "",
      "abiFilters": ["arm64-v8a"]
    }
  }
}
```

核对：

- path 相对模块目录是否正确。
- `abiFilters` 是否覆盖发布设备。
- compileSdk/compatibleSdk 与使用的 Native API 是否匹配。
- 构建产物是否实际打进目标 HAP/HAR/HSP。
- 仓库使用的 Hvigor/DevEco 版本和任务名；不要从别的项目复制 wrapper 命令。

## 目标级 CMake

优先写成目标级配置：

```cmake
cmake_minimum_required(VERSION 3.5.0)
project(foo LANGUAGES CXX)

add_library(foo SHARED
    napi_init.cpp
    core/engine.cpp
)

target_compile_features(foo PRIVATE cxx_std_20)
set_target_properties(foo PROPERTIES
    CXX_EXTENSIONS OFF
)

target_include_directories(foo PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
)

target_compile_definitions(foo PRIVATE FOO_SCHEMA_VERSION=3)
target_link_libraries(foo PRIVATE
    libace_napi.z.so
)
```

避免重复设置全局标准、全局 include 和无关 flags。新增源文件时验证它确实进入 target，而不是只存在于目录中。

## 系统 Native 库

以匹配版本 SDK 头文件和官方参考为准。真实画布模块可能需要：

| 能力 | 常见链接库 |
| --- | --- |
| Node-API | `libace_napi.z.so` |
| ArkUI Native Node/NodeContent | `libace_ndk.z.so` |
| hilog | `libhilog_ndk.z.so` |
| Native Drawing | `libnative_drawing.so` |
| NativeWindow | `libnative_window.so` |
| EGL/OpenGL ES | `libEGL.so`、`libGLESv3.so` |
| Image packer/PixelMap | `libimage_packer.so`、`libpixelmap.so` |

不要仅凭头文件能找到就认为链接完整；最终以 undefined symbol、SDK API reference 和目标产物依赖为准。

## 预编译三方库

接入静态库的基本形态：

```cmake
add_library(vendor STATIC IMPORTED)
set_target_properties(vendor PROPERTIES
    IMPORTED_LOCATION "${VENDOR_ROOT}/lib/libvendor.a"
    INTERFACE_INCLUDE_DIRECTORIES "${VENDOR_ROOT}/include"
)

target_compile_definitions(foo PRIVATE VENDOR_STATIC)
target_link_libraries(foo PRIVATE vendor z m pthread dl)
```

逐项验证：

- archive 的 CPU 架构与 `abiFilters` 一致。
- 使用 HarmonyOS 目标 triple、兼容 API level 和兼容 libc++ 构建。
- 静态库链接进 `.so` 时使用 PIC。
- exceptions、RTTI、C++ 标准、visibility 和宏与调用方一致。
- 传递依赖、库顺序和循环静态依赖正确。
- 许可证和必须随包分发的资源完整。
- `.pc`/导出 CMake 文件里没有构建机绝对路径；优先使用项目内可重定位路径。

对多个 archive 组成的栈，先列完整依赖图，再决定链接顺序。不要用“不断追加库直到能链接”代替依赖分析。

## 失败策略

如果三方能力是产品必需功能，缺 archive/header 时使用配置期失败：

```cmake
if(NOT EXISTS "${VENDOR_LIB}")
    message(FATAL_ERROR "required vendor library is missing: ${VENDOR_LIB}")
endif()
```

只有确实存在可测试的降级功能时，才用 compile definition 切换实现。降级版本必须：

- 对 ArkTS 暴露明确 capability。
- 不生成表面成功、运行时才失败的接口。
- 在 CI 同时覆盖 enabled/disabled 构建。

## 排查顺序

1. **配置未进入 CMake**：检查 `externalNativeOptions.path` 和构建变体。
2. **找不到头文件**：检查 target include、大小写、生成顺序和 API level。
3. **编译错误**：检查目标 triple、C++ 标准、宏、exceptions/RTTI。
4. **undefined symbol**：检查源文件、函数签名、C linkage、archive 架构、依赖和顺序。
5. **运行时找不到 `.so`**：检查 target 名、import 名、注册名、ABI 和打包产物。
6. **dlopen 失败**：检查动态依赖、符号版本、libc++/系统 API 兼容。
7. **仅某 ABI 失败**：逐 ABI 检查 archive 和 `abiFilters`，不要拿 arm64 成功推断其他 ABI。
