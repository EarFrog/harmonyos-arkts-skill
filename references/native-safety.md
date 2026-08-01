# Native 安全、并发与生命周期

## 目录

- [Node-API 状态与异常](#node-api-状态与异常)
- [线程所有权](#线程所有权)
- [锁与快照](#锁与快照)
- [资源生命周期](#资源生命周期)
- [异步状态机](#异步状态机)
- [边界与持久化](#边界与持久化)

## Node-API 状态与异常

核心规则不是机械地“每行都写一次 if”，而是：

- 任何后续会使用输出参数或依赖副作用的调用，都必须确认 `napi_ok`。
- 把连续的创建/设置操作集中到返回 status 的 helper，可以减少遗漏。
- 抛异常、记录 last error 或 best-effort 清理本身失败时，不得再递归进入普通成功逻辑。
- 若环境已有 pending exception，不要再 resolve 成成功结果。

必填参数解析失败时 throw/reject；可选字段只有“确实缺失”才用默认值，类型错误仍应失败。

## 线程所有权

| 资源 | 所有权规则 |
| --- | --- |
| `napi_env` / `napi_value` | 只在所属 JS 线程和有效 scope 使用 |
| `napi_ref` | 仍绑定 env；只解决跨 callback 生命周期，不自动解决跨线程 |
| async work `execute` | 只操作复制后的 Native 数据 |
| async work `complete` | 在可操作 JS 的线程创建结果和 settle Promise |
| EGL context / GL object | 由明确的渲染线程或严格验证的 current-thread 协议拥有 |
| ArkUI node/content | 遵守目标 API 的 UI/事件线程和注销顺序 |
| session handle | 由 registry 管理；查找、关闭和重复销毁有明确语义 |

互斥锁只能阻止并发进入，不能把 JS env、ArkUI node 或 EGL context 变成“任意线程可用”。

## 锁与快照

避免一个全局锁串行化输入、渲染、草稿 I/O 和图片编码。

推荐：

1. 短锁内校验 session/page 并复制不可变快照。
2. 解锁后做序列化、文件写入、图片编码或大规模计算。
3. 完成时用 version/epoch 检查结果是否仍可提交。
4. 按 session/page/renderer 拆锁，明确锁顺序。

不要：

- 持锁调用可能回调上层的代码。
- 持锁等待另一个线程 drain。
- 在 GL export、`glReadPixels`、压缩编码或文件系统慢路径期间阻塞触摸输入。

## 资源生命周期

用 RAII 或唯一 owner 管理：

- `napi_async_work`、`napi_ref`、TSFN、cleanup hook。
- ArkUI custom event 注册、NodeContent node、XComponent surface。
- NativeWindow、EGLDisplay/EGLSurface/EGLContext、FBO/texture/buffer/program。
- Native Drawing bitmap/canvas/image/pen/brush/path。
- Image packer、PixelMap、文件描述符和临时文件。

释放函数必须：

- 可重复调用。
- 清空 handle，阻止释放后继续使用。
- 覆盖组件 disappear/recycle、Surface destroy、session destroy、env cleanup 和初始化到一半失败。
- 按依赖反向销毁；例如先停止提交，再释放 surface/context，最后清 registry。

## 异步状态机

Promise 异步接口至少覆盖：

1. 参数复制失败。
2. promise 创建失败。
3. resource name 创建失败。
4. async work 创建失败。
5. queue 失败。
6. execute 失败或取消。
7. complete 构造结果失败。
8. resolve/reject 失败。
9. env 正在关闭。

每条路径保证：

- Promise 只 settle 一次。
- `napi_async_work` 只删除一次。
- context 只释放一次。
- 创建 work 成功但 queue 失败时仍删除 work。
- 业务失败使用 reject 还是结构化结果保持一致；不要有时 throw、有时返回 false 而门面无法区分。

异步 context 中优先保存纯 Native 数据。`complete` 会收到 env，通常无需把 env 缓存到 context。

## 边界与持久化

- `width * height * bytesPerPixel`、`count * stride` 等先做除法式溢出检查，再分配。
- 对页面大小、点数、字符串、数组、递归深度、图片质量和文件大小设置上限。
- 路径只允许业务授权的沙箱位置；不接受未经验证的任意系统路径。
- 二进制草稿包含 magic、version、尺寸、数量和长度上限。
- 保存使用同目录临时文件，成功后原子替换；失败清理临时文件，不破坏最后一份有效数据。
- CPU/矢量数据作为事实源时，GPU cache 是可删除的派生数据；用内容 hash + 尺寸 + schema/version 校验，失配即丢弃重建。
- 读取旧版本时显式迁移；不把“能读出来”视为坐标、宽度和颜色语义仍兼容。
