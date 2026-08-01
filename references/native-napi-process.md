# Node-API 模块与契约

## 目录

- [先识别真实形态](#先识别真实形态)
- [模块命名链](#模块命名链)
- [注册方式](#注册方式)
- [参数解析](#参数解析)
- [导出与声明](#导出与声明)
- [审计清单](#审计清单)

## 先识别真实形态

常见模板把声明放在 `src/main/cpp/types/lib<target>/index.d.ts`，但这不是唯一结构。真实工程可能：

- 使用名为 `lib<target>.so` 的 types package。
- 在唯一 ArkTS bridge 中导入 `.so`，再用本地 interface 描述 Native 模块。
- 由生成器产生注册表或声明。
- 由 HAR/HSP 门面对外隐藏原始 `.so`。

先沿 `.so` import 找到调用者，再反向确认 CMake target、注册入口和声明来源。不要仅凭目录名判断契约完整。

## 模块命名链

分别核对以下名字，不要粗暴要求字符串全部相同：

1. CMake target `foo` 通常生成 `libfoo.so`。
2. ArkTS import 使用完整库名，例如 `libfoo.so`。
3. `NAPI_MODULE(foo, Init)` 的 token 会变成注册名 `foo`。
4. 显式 `napi_module` 使用 `.nm_modname = "foo"`。
5. `types/libfoo/oh-package.json5` 若存在，通常声明 `"name": "libfoo.so"`。

若工程的 loader、别名或打包规则改变了默认关系，以构建产物和匹配版本官方规则为准，并把差异写进契约矩阵。

## 注册方式

一个模块只保留一种注册入口。

### 宏注册

```cpp
namespace {
napi_value Init(napi_env env, napi_value exports)
{
    napi_property_descriptor properties[] = {
        {"ping", nullptr, Ping, nullptr, nullptr, nullptr, napi_default, nullptr},
    };
    if (napi_define_properties(
            env, exports, sizeof(properties) / sizeof(properties[0]), properties) != napi_ok) {
        napi_throw_error(env, nullptr, "failed to register native exports");
        return nullptr;
    }
    return exports;
}
}

NAPI_MODULE(foo, Init)
```

### 显式注册

```cpp
static napi_module module = {
    .nm_version = 1,
    .nm_flags = 0,
    .nm_filename = nullptr,
    .nm_register_func = Init,
    .nm_modname = "foo",
    .nm_priv = nullptr,
    .reserved = {0},
};

extern "C" __attribute__((constructor)) void RegisterFoo()
{
    napi_module_register(&module);
}
```

`NAPI_MODULE` 已经展开为模块结构、constructor 和 `napi_module_register`；不要再为同一库重复写显式注册。

## 参数解析

固定参数接口使用固定容量数组：

```cpp
bool ReadTwoNumbers(
    napi_env env,
    napi_callback_info info,
    double& left,
    double& right)
{
    size_t argc = 2;
    napi_value argv[2] = {nullptr, nullptr};
    if (napi_get_cb_info(env, info, &argc, argv, nullptr, nullptr) != napi_ok) {
        napi_throw_error(env, nullptr, "failed to read arguments");
        return false;
    }
    if (argc < 2) {
        napi_throw_type_error(env, nullptr, "two numbers are required");
        return false;
    }

    napi_valuetype leftType = napi_undefined;
    napi_valuetype rightType = napi_undefined;
    if (napi_typeof(env, argv[0], &leftType) != napi_ok ||
        napi_typeof(env, argv[1], &rightType) != napi_ok ||
        leftType != napi_number || rightType != napi_number) {
        napi_throw_type_error(env, nullptr, "arguments must be numbers");
        return false;
    }
    if (napi_get_value_double(env, argv[0], &left) != napi_ok ||
        napi_get_value_double(env, argv[1], &right) != napi_ok ||
        !std::isfinite(left) || !std::isfinite(right)) {
        napi_throw_range_error(env, nullptr, "arguments must be finite");
        return false;
    }
    return true;
}
```

规则：

- `argc` 表示 `argv` 容量，必须初始化；数组容量不得小于它。
- 对固定 arity，不需要为“获取真实数量”做多余的两次调用。
- 对可变 arity，只有在目标 SDK 头文件或官方文档明确支持相应两阶段用法时才采用，并给数组设置硬上限。
- 必填参数不得用“转换失败就回退 0/空串”掩盖类型错误。
- 对 number 同时校验 `NaN`/Infinity、整数性、范围和向目标整数类型转换是否安全。
- 对 object 先校验 object/null，再区分必填和可选属性；属性缺失与属性类型错误不能混为一谈。
- 抛出异常后立即停止业务逻辑，不继续读取失败调用的输出。

## 导出与声明

以下三处必须逐项一致：

1. `napi_property_descriptor` 的导出名。
2. ArkTS 声明或本地 `NativeModule` interface。
3. 实际门面调用的方法名、参数顺序和返回/异常语义。

声明形式可以是具名导出、默认 namespace 或 ArkTS 门面。选择工程既有风格，但避免以下漂移：

- C++ 返回 Promise，声明仍是同步值。
- C++ 可能 throw/reject，门面把失败静默转成正常值。
- `number` 承载超过 JS 安全整数范围的 64 位 ID。
- C++ 接受 ArrayBuffer，声明写成任意 Object。
- C++ object 字段可选性与 ArkTS interface 不一致。

Native 导出多时，优先维护一份可机器审计的契约源；至少用静态脚本比较导出名。不要在 `.d.ts` 和 ArkTS 私有 interface 中长期复制两份手写签名。

## 审计清单

- CMake target 能生成预期 `lib*.so`。
- 模块只有一个注册入口，注册名与加载规则一致。
- `Init` 只注册导出和做轻量初始化。
- `napi_define_properties` 失败不会返回一个看似成功的模块。
- 每个 callback 校验状态、数量、类型、范围和业务约束。
- 所有输出值只在创建成功后使用。
- 抛异常或 reject 后不再走成功路径。
- 描述符、声明和门面没有缺失、多余或签名漂移。
- session/handle 不用不安全的浮点整数表示。
- 变更后验证真实 import，而不只验证 C++ 能编译。
