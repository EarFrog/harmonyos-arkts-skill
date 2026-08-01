# Native 状态与资源架构

## 目录

- [先判断模块类型](#先判断模块类型)
- [使用不透明 handle](#使用不透明-handle)
- [区分事实源与派生状态](#区分事实源与派生状态)
- [收敛 ArkTS 门面](#收敛-arkts-门面)
- [设计高频事件协议](#设计高频事件协议)
- [保持单一语义权威](#保持单一语义权威)
- [拆分 prepare、consume 与 commit](#拆分-prepareconsume-与-commit)
- [覆盖完整生命周期](#覆盖完整生命周期)
- [限制锁的职责](#限制锁的职责)
- [采用模式前分级](#采用模式前分级)
- [审查清单](#审查清单)

## 先判断模块类型

不要把同一种 session/registry 架构套到所有 Native 模块。先分类：

| 类型 | 典型特征 | 推荐形态 |
| --- | --- | --- |
| 无状态计算 | 输入完整、调用后不保留资源 | 普通同步函数或 async work |
| 短任务状态 | 有进度、取消、一次性结果 | task handle + 明确结束 |
| 长生命周期对象 | decoder、数据库、模型、renderer | opaque handle + registry/owner |
| UI/Surface 绑定 | 生命周期受组件和窗口驱动 | component identity + generation |
| 多实体会话 | 文档/页面、项目/资源、会话/流 | session handle + entity key |

只在确实需要跨调用保存状态时引入 registry。无状态能力若被包装成全局 session，会增加锁、泄漏和环境退出复杂度。

## 使用不透明 handle

ArkTS 只持有身份，不持有 C++ 裸指针。Native 通过 handle 查找对象和资源。

要求：

- handle 无法被调用方解引用或伪造为有效指针。
- create/destroy 明确，destroy 幂等。
- lookup 区分不存在、已关闭和 generation 过期。
- 不用简单位移拼接多个无限范围整数。
- 对外暴露的数值 handle 必须落在 JS 安全整数范围；否则使用 BigInt、字符串或拆分字段。
- async context 同时保存 handle 和 generation，完成时重新校验。

如果调用频繁，可用结构化 key：

```text
ResourceKey {
  session_id
  entity_id
  generation
}
```

generation 用于阻止旧任务把结果提交到已经复用的新对象。

## 区分事实源与派生状态

为每类状态标注角色：

| 角色 | 示例 | 丢失后处理 |
| --- | --- | --- |
| 事实源 | 业务模型、命令、原始数据、配置 | 不可静默丢失 |
| 派生状态 | 索引、GPU 资源、解码缓存、缩略结果 | 从事实源重建 |
| 运行时状态 | active operation、临时 buffer、事务阶段 | cancel/finish/reset |
| 外部资源 | fd、NativeWindow、EGLSurface、线程 | 明确 owner 释放 |

新增缓存前回答：

1. 事实源在哪里？
2. cache key/version 包含哪些影响结果的字段？
3. 谁触发失效？
4. 丢失或损坏后如何重建？
5. 重建发生在哪个线程，会不会阻塞首帧或调用线程？

不要把派生缓存当作唯一持久化数据。

## 收敛 ArkTS 门面

每个 `.so` 选择一个稳定 ArkTS facade，业务代码不要到处直接 import Native 模块。

门面负责：

- 统一类型、单位、枚举和错误语义。
- 将 vp、px、时间戳、颜色和编码转换限制在边界。
- 隔离兼容 API 和版本探测。
- 封装 handle 生命周期。
- 把同步、Promise、callback 的选择暴露为一致接口。

`.d.ts` 或 ArkTS Native interface 选一个主契约源，另一个通过生成或静态审计保持一致。不要维护两份无人检查的手写契约。

## 设计高频事件协议

触点、音频帧、传感器数据、图像块等高频数据适合固定二进制协议。

协议必须定义：

- schema/version。
- 字段顺序和 stride。
- 数值位宽和端序。
- count、byteLength 和累计大小上限。
- 单位、范围和有限值要求。
- buffer 所有权和有效期。

复用 ArrayBuffer 只有在 Native callback 返回前完成同步消费或复制时才安全。若数据进入异步队列，立即复制、转移所有权或使用带生命周期的共享内存。

“用了二进制 buffer”不等于“已经批处理”。用 `calls / item`、`items / call`、等待时间和端到端延迟证明跨语言调用次数确实下降。

## 保持单一语义权威

多个后端处理同一业务对象时，选择一个权威层生成规范化结果。例如：

- 一个采样器生成平滑后的点、宽度和 alpha。
- 一个 parser 生成 AST，多个执行/展示后端消费 AST。
- 一个 decoder 生成规范化帧描述，CPU/GPU 后端消费同一描述。
- 一个布局模型生成几何，多个 renderer 只负责呈现。

不要让每个后端从原始输入各自推导业务语义。否则保存、预览、导出和屏幕显示可能逐步漂移。

权威层输出应包含后端所需的完整字段，并具有版本。后端只记录自己的消费进度和派生资源。

## 拆分 prepare、consume 与 commit

当结束操作同时影响事实模型和多个消费者时，使用小事务：

1. `prepare`：补齐尾部/校验/冻结结果，但保留消费者仍需读取的活动数据。
2. `consume`：各后端消费剩余增量或生成最终结果。
3. `commit`：更新事实模型、命令历史和版本，再清理活动状态。

适用场景：

- 流式解析结束。
- 录音/编码 flush。
- 绘制笔迹结束。
- 数据库批次提交。
- 多后端导出。

预先定义失败语义：

- prepare 失败是否保持原状态。
- 某个消费者失败是否允许降级。
- commit 失败后如何使派生后端恢复一致。
- 重试是否幂等。

简单、单后端、无活动状态的调用不需要机械拆成三阶段。

## 覆盖完整生命周期

为每种资源填写生命周期矩阵：

| 事件 | 活动任务 | handle | Surface/context | buffer/cache |
| --- | --- | --- | --- | --- |
| 正常完成 | finish | 保留或销毁 | 保留 | 按策略复用 |
| cancel | 停止并回滚/提交部分结果 | 保留 | 保留 | 清临时状态 |
| 组件复用 | flush/cancel | 更新 generation | 解绑旧资源 | 定向失效 |
| Surface destroy | 阻止新渲染 | 保留模型 | 释放 | 保留可重建数据 |
| 前后台 | 暂停/恢复 | 保留 | 按平台规则重建 | 控制内存 |
| env cleanup | 停止并等待 | 全部失效 | 全部释放 | 全部释放 |

组件回调可能重复或乱序。bind 前比较期望身份与已绑定身份；变更时先 release 旧资源，再 bind 新资源。

## 限制锁的职责

registry 锁只保护：

- map 查找和插入/删除。
- 短小状态转换。
- 获取强引用或复制不可变 snapshot。

不要持有 registry/global 锁执行：

- 文件 I/O。
- 网络或 IPC。
- 图片编码、模型推理、整页计算。
- EGL makeCurrent、draw、swap、readback。
- Node-API callback 或 Promise resolve。

对象内部可以有自己的锁或串行队列。线程亲和资源需要固定 owner thread；mutex 只能互斥，不能改变 API 的线程约束。

## 采用模式前分级

审阅现有实现时给结论分级：

| 分级 | 含义 |
| --- | --- |
| 契约事实 | 由 SDK、头文件或活跃调用链证明 |
| 通用模式 | 可跨项目采用，但仍需适配 |
| 经验参数 | 批量、阈值、cache size、并发度，需要重新测量 |
| 风险实现 | 当前可运行但存在未证明假设 |
| 非活跃路径 | feature flag 关闭、无调用者或仅诊断代码 |

不要把“生产仓库里存在”当作“通用最佳实践”。

## 审查清单

- 模块是否真的需要 session/registry？
- handle 是否不透明、可校验且不会复用串线？
- 事实源、派生状态和运行时状态是否明确？
- ArkTS 是否通过单一 facade 访问 Native？
- 高频协议是否定义 stride、端序、上限和所有权？
- 多后端是否消费同一规范化语义？
- 结束事务是否会过早清理消费者仍需的数据？
- destroy、cancel、reuse、Surface destroy 和 env cleanup 是否幂等？
- 全局锁内是否存在长任务、回调或图形操作？
- 案例常量和非活跃代码是否被误写成规范？
