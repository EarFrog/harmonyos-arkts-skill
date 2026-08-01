# ArkTS 与 Native 互操作

## 目录

- [门面边界](#门面边界)
- [类型与数值](#类型与数值)
- [ArrayBuffer 和二进制协议](#arraybuffer-和二进制协议)
- [异步模型选择](#异步模型选择)
- [回调与引用](#回调与引用)
- [高频输入](#高频输入)

## 门面边界

优先让一个 ArkTS bridge 成为原始 `.so` 的唯一导入点：

```typescript
import nativeModule from 'libfoo.so'

interface FooNativeModule {
    createSession(): number
    appendPoints(sessionId: number, packet: ArrayBuffer, count: number): boolean
}

const foo = nativeModule as FooNativeModule
```

门面负责：

- 把 Native 方法转换成业务术语。
- 统一单位、默认值、错误语义和功能探测。
- 隐藏 `.so`、N-API 与 UI 组件之间的耦合。
- 集中维护类型契约，避免业务层到处强制转换。

门面不能替代契约审计；它仍需与 C++ 导出表同步。

## 类型与数值

| ArkTS | Native 处理 |
| --- | --- |
| `number` | 先读 `double`，再校验有限性、整数性和目标范围 |
| `boolean` | 校验 `napi_boolean` 后读取 |
| `string` | 先取 UTF-8 长度，再分配 `length + 1` |
| `Array<T>` | 校验 array、长度上限和每一项 |
| object/interface | 区分必填/可选字段，逐字段校验 |
| `ArrayBuffer` | 校验字节长度、布局、生命周期和所有权 |
| callback | 同步直接调用；跨 callback 用 `napi_ref` |
| `Promise<T>` | 建立唯一 resolve/reject/cleanup 路径 |

注意：

- JS/ArkTS number 只能精确表示安全整数范围内的整数。可能超过该范围的 64 位 ID 使用 BigInt（若目标 API 支持）、字符串或受控 handle 表，不要直接强转 double。
- `Uint8Array`、其他 TypedArray 与 ArrayBuffer 不是可随意互换的契约。按声明接受的类型调用对应检查/读取 API，并处理 byte offset。
- `Object` 和 `Object[]` 会丢失字段约束。跨语言对象应定义明确 interface；高频大对象优先改成稳定二进制协议。

## ArrayBuffer 和二进制协议

协议至少写明：

- magic/schema version。
- 每条记录的 stride 和字段顺序。
- 数值类型、字节序、对齐和浮点约束。
- `count` 与 `byteLength` 的关系。
- 最大记录数、最大总字节数。
- buffer 所有者、消费时机和可否复用。

例如点数据：

```text
version: 1
endianness: little-endian
stride: 32 bytes
record: x:f64, y:f64, pressure:f64, timestamp:f64
requiredBytes = count * stride
```

Native 侧先做溢出安全检查：

```cpp
if (count > kMaxPoints || count > byteLength / kStride) {
    // reject
}
```

用 `memcpy` 读取可能未对齐的数值，不要把任意字节地址直接 `reinterpret_cast<double*>`。

同一 ArrayBuffer 只在以下条件下可立即复用：Native callback 在返回前已经同步消费或复制内容。若工作被排入 async work、render queue 或后台线程，必须复制数据、转移所有权，或持有能保证 backing store 生命周期的正式引用模型。

## 异步模型选择

### ArkTS taskpool 包装同步 Native

适合：

- 单次、粗粒度、无 JS 回调的 CPU/文件任务。
- Native 函数本身可从 taskpool 线程安全调用。
- 输入输出可跨 taskpool 边界传输。

不适合：

- 依赖固定 EGL/GL context 线程的渲染任务。
- 内部依赖 UI 线程状态或 JS value 的任务。

### `napi_create_async_work`

适合在 Native 模块内直接返回 Promise：

1. callback 中把 ArkTS 输入复制成纯 Native context。
2. 创建 promise、resource name 和 async work。
3. `execute` 中只访问 Native 数据，不创建/读取 JS 对象。
4. `complete` 中检查 status，创建 JS 结果，resolve/reject。
5. 无论创建、排队、执行还是完成失败，都只清理一次。

### 专用渲染线程

高频 GL 命令或持久 context 使用专用线程和队列：

- context 在该线程创建、使用和销毁。
- UI/N-API 线程只提交不可变命令或复制后的批数据。
- 用序列号/epoch 丢弃过期 resize、replay 或 export 请求。
- shutdown 先停止入队，再 drain/cancel，最后在线程内销毁图形资源。

## 回调与引用

- 同步 callback：先校验 `napi_function`，在当前 JS 线程调用。
- 跨 callback 保存函数/对象：`napi_create_reference` 与 `napi_delete_reference` 成对。
- Native/设备线程回调 ArkTS：使用线程安全函数或目标 SDK 明确允许的机制。
- TSFN 队列满、closing、abort 和 finalize 都要定义数据释放责任。
- 不把 `napi_env`、`napi_value` 或 scope 内指针塞进普通 C++ 任务后跨线程使用。

## 高频输入

按以下顺序优化：

1. 先确认事件是否提供 coalesced/historical points，避免丢采样。
2. 把单位转换、压力归一化和输入过滤集中在边界。
3. 复用 DataView/ArrayBuffer，避免每点构造 object/array。
4. 真正按批或按帧 flush；仅换成 ArrayBuffer、但每个 Move 立即 flush，通常只减少解析成本，不减少跨语言调用次数。
5. 在 Up、Cancel、组件复用/回收、Surface 销毁和超时边界强制 flush。
6. 同时设置“最大点数”和“最大等待时间”，在吞吐与延迟之间做设备实测。
