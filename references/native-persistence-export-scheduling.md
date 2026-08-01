# Native 持久化、导出与任务调度

## 目录

- [区分主数据与派生文件](#区分主数据与派生文件)
- [锁内快照、锁外工作](#锁内快照锁外工作)
- [设计安全的二进制格式](#设计安全的二进制格式)
- [迁移源语义](#迁移源语义)
- [构建完整缓存签名](#构建完整缓存签名)
- [丢弃过期异步结果](#丢弃过期异步结果)
- [限制并发和背压](#限制并发和背压)
- [淘汰可重建缓存](#淘汰可重建缓存)
- [降低图片导出复制](#降低图片导出复制)
- [遵守 async work 线程边界](#遵守-async-work-线程边界)
- [让观测收敛到低成本指标](#让观测收敛到低成本指标)
- [验收清单](#验收清单)

## 区分主数据与派生文件

持久化前先分类：

| 数据 | 示例 | 策略 |
| --- | --- | --- |
| 主数据 | 业务对象、命令、用户输入、源配置 | 可迁移、校验、原子保存 |
| 派生 cache | GPU replay、索引、缩略图、中间编译结果 | 可删除、签名校验、自动重建 |
| 临时输出 | 导出中间文件、上传分片 | 有 owner、超时和清理 |

不要让 cache 成为唯一恢复来源。不要把 Native handle、指针、FBO、驱动对象或进程地址写入长期格式。

## 锁内快照、锁外工作

长任务使用：

1. 锁内查找对象并校验 generation。
2. 复制不可变 snapshot 和开始版本。
3. 释放锁。
4. 序列化、压缩、编码、计算或写盘。
5. 完成时重新校验 generation/version。
6. 只有结果仍新鲜时提交状态或标记 clean。

不要持锁执行文件 I/O、图片编码、整页计算或 JS callback。

保存期间源对象可能继续变化。`markClean` 必须 compare-and-set：仅当当前版本等于 snapshot 版本时清 dirty。

## 设计安全的二进制格式

文件头至少包含：

- magic。
- schema version。
- flags/encoding。
- header/body length。
- 必要的业务尺寸或数量。
- checksum 或完整性字段（按风险选择）。

每个变长字段在分配前检查：

- 单项长度。
- 总文件长度。
- count。
- 累计 count/bytes。
- 乘法与加法溢出。
- 剩余可读字节。

数值检查有限值和业务范围。字符串定义编码。写入临时文件，flush/close 成功后再原子替换目标。

不要因为文件来自应用沙箱就跳过校验；崩溃、版本 bug、部分写入和磁盘损坏同样会产生异常输入。

## 迁移源语义

长期格式优先保存业务源语义，而不是某个 renderer 或算法版本的派生结果。

迁移规则：

- 每个旧版本使用独立迁移函数。
- 缺失字段使用有业务依据的默认值。
- 迁移后统一做范围、有限值和计数归一化。
- 记录影响结果的算法/schema 版本。
- 非等比 resize 明确坐标、尺寸和宽度的缩放规则。
- 用旧版本 golden files 做回归。

派生颜色、采样点、顶点、索引和 GPU cache 可以在加载后重建。

## 构建完整缓存签名

派生 cache 签名包含：

- cache schema。
- 事实模型 version。
- 尺寸、scale、format。
- 所有影响结果的配置字段。
- 所有影响结果的数据字段。
- 依赖资源 version。
- 算法/renderer version。

签名字段遗漏会把旧结果误判为可复用。仅使用条目数、修改时间或内存地址通常不够。

加载 cache：

1. 先读固定大小 header。
2. 比较 schema、version、尺寸和内容签名。
3. 校验长度/完整性。
4. 匹配才加载。
5. 失配或损坏则删除/忽略，从主数据重建。

## 丢弃过期异步结果

为每个实体维护 sequence/epoch。排队时保存：

- session/entity handle。
- generation。
- expected version。
- task sequence。
- cancel/closing state。

提交前逐项比较。任一变化就丢弃结果，不覆盖新状态。

异步任务只引用不可变 snapshot 或拥有的 Native 数据，不能引用随后会修改的 ArkTS array、裸指针或已释放对象。

## 限制并发和背压

批量保存、预热、导出、重建 cache 时设置：

- 最大并发。
- 最大排队数/字节。
- 单任务大小上限。
- 优先级。
- 取消和超时。
- 前台交互的资源保留。

并发度由设备 CPU、存储、内存、worker 数和 renderer queue 决定，不复制其他项目的常量。

只 `yield` 不能让同步重任务自动变轻。确认真正的计算发生在 worker 或专用队列，UI/complete 阶段只做轻量提交。

## 淘汰可重建缓存

按组合预算淘汰：

- 当前可见/即将可见优先级。
- CPU bytes。
- GPU bytes。
- 最近使用时间。
- 重建成本。
- 系统低内存信号。

活动任务、尚未持久化的唯一数据和无法重建资源不得被普通 cache 策略淘汰。

淘汰后更新 dirty/ready 状态。重新进入视口或调用时从事实源恢复；对高重建成本资源做可取消预热。

## 降低图片导出复制

若 Native 已拥有事实模型或 renderer，优先在 Native 内构图、编码并写入临时文件，只向 ArkTS 返回 path、尺寸、错误和必要 metadata。

避免无必要的链路：

```text
Native RGBA
  -> ArrayBuffer
  -> ArkTS ImageData
  -> PixelMap
  -> encoder
```

GPU 离屏导出：

1. 在 renderer 所属线程执行。
2. 创建/复用 texture + FBO。
3. 检查 framebuffer completeness。
4. 保存 viewport、绑定和变换状态。
5. render。
6. readback 到有上限的复用 buffer。
7. 统一处理行方向、通道和背景。
8. 编码并原子写文件。
9. 恢复状态。

`glReadPixels` 是同步点。不要在 UI 线程执行，也不要持 registry/global 锁跨越 readback、编码和 I/O。

GPU 失败可以回退 CPU，但记录失败阶段和 fallback 次数。长期静默 fallback 会掩盖 GPU 故障。

## 遵守 async work 线程边界

Node-API async work：

- `execute` 只使用 Native 数据。
- `execute` 不访问 `napi_env`、`napi_value` 或 JS object。
- `complete` 创建 JS 值并 resolve/reject。
- context 持有复制后的字符串、buffer、handle generation 和 Native result。
- create/queue/complete/delete 每个阶段检查 status。
- env cleanup/cancel 定义任务与资源释放顺序。

worker thread 也不自动拥有 EGL context、UI object 或其他线程亲和资源。需要通过 owner queue 执行。

## 让观测收敛到低成本指标

开发阶段可以使用细粒度探针，但稳定后收敛为：

- count、bytes 和直方图。
- p50/p95/p99 或 max。
- 慢路径阈值日志，并限流。
- cache hit/miss/eviction。
- lock wait/max hold。
- queue depth/backpressure。
- fallback、context loss、cancel 和 stale result 数。
- 持久化/导出的阶段错误码。

默认关闭：

- 每个事件、点、帧或 draw 的日志。
- 大数组、坐标和像素 dump。
- 会触发 readback 的诊断。
- release 构建的全量状态扫描。

诊断能力使用 build/runtime gate，并设定清理条件。

## 验收清单

- 保存期间源对象变化不会被误标为 clean。
- 截断、损坏、超大 count 和旧版本文件安全失败或迁移。
- cache 签名覆盖所有影响结果的字段。
- generation/version/sequence 变化后旧任务不会提交。
- 并发、队列和 snapshot 内存有上限。
- cache 淘汰不丢事实数据，恢复成本可接受。
- 导出不在 UI 线程，不持全局锁执行 readback/编码/I/O。
- CPU/GPU 导出的颜色、alpha、方向和背景一致。
- fallback 和慢阶段可观测，但热路径没有日志洪泛。
