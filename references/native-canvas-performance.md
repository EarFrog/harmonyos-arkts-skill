# 画布与手写渲染性能

## 目录

- [先定义目标](#先定义目标)
- [选择渲染架构](#选择渲染架构)
- [输入与跨语言边界](#输入与跨语言边界)
- [统一笔迹语义与结束事务](#统一笔迹语义与结束事务)
- [增量绘制与分层](#增量绘制与分层)
- [缓存与内存](#缓存与内存)
- [GLES 线程与 Surface](#gles-线程与-surface)
- [草稿和导出](#草稿和导出)
- [常见伪优化](#常见伪优化)
- [验收表](#验收表)

## 先定义目标

同时定义：

- 输入到可见像素的延迟。
- 帧耗时分位数和掉帧。
- 笔迹视觉正确性。
- 稳态/峰值内存。
- 前后台、resize、undo/redo、Surface 重建的稳定性。
- 草稿和图片导出的完成时间与对交互的影响。

没有基线时先加低开销计数器和分段计时，不先改架构。

## 选择渲染架构

### Native Drawing + ArkUI custom node

适合 2D 图形、ArkUI 布局融合和按脏区重绘。要控制：

- `markDirty` 范围和频率。
- active/completed layer 分离。
- 位图、纹理着色结果和瓦片缓存。
- draw callback 内的锁和分配。

### XComponent/NativeWindow + EGL/GLES

适合高频顶点、纹理笔刷、shader 和 GPU 合成。要控制：

- Surface/context 生命周期。
- GL 线程亲和性。
- 持久 framebuffer。
- 每帧命令、buffer 上传和 swap 次数。

### CPU 模型 + GPU 派生视图

手写/草稿场景通常保留 CPU 矢量笔迹作为事实源，GPU 资源作为可重建派生缓存。这样能支持：

- 草稿保存和版本迁移。
- context loss 后 replay。
- GPU 导出失败时 CPU fallback。
- 用内容签名判断缓存是否可复用。

双路径会增加每次输入的成本，必须测量 CPU 采样与 GPU 提交是否重复做了昂贵工作。

## 输入与跨语言边界

1. 在边界统一 vp/px、颜色、压力、时间戳和 page 坐标。
2. 保存 Down/Move/Up/Cancel 状态机；生命周期打断时 flush 或 cancel。
3. 复用 ArrayBuffer/DataView，使用固定 stride，Native 端设置点数和字节上限。
4. 批处理必须减少调用次数：收集 coalesced points，按一帧、最大点数或最大等待时间 flush。
5. Up/Cancel/Surface destroy/recycle 前强制 flush。
6. buffer 复用前确认 Native 已同步消费；异步队列必须复制或转移所有权。

一个容量为 64 的 buffer 如果每个 Move 都立即 flush，主要收益只是减少 object/array 解析，不能视为已经完成批处理优化。

## 统一笔迹语义与结束事务

CPU 和 GPU 同时参与渲染时，不要让两边分别从原始触点计算平滑、笔锋、宽度和 alpha。选择一个权威采样器，其他 renderer 只消费带完整渲染属性的采样点。

推荐协议：

1. `begin`：创建 active stroke，冻结本笔的 style。
2. `append(raw points)`：权威采样器更新 active stroke。
3. renderer 查询自己的 `consumedPointCount`，只拉取 `[consumed, produced)`。
4. `prepareEnd`：补尾点、结束 Bézier/速度状态，但暂不移走 active stroke。
5. renderer 拉取最后一段并完成可见提交。
6. `commitEnd`：把 active stroke 转入历史命令和稳定层，再清理 active 状态。

把结束拆成 prepare/commit 是为了同时满足：

- GPU 能读取完整的尾部采样。
- CPU 模型只提交一次。
- 失败时能区分采样、renderer 同步和模型提交三个阶段。
- CPU/GPU 不会因为各自补尾而产生形状漂移。

若 renderer 提交失败，必须预先定义策略：保留 active 以便重试、提交 CPU 后触发整页 replay，或明确降级到 CPU 显示。不要留下“CPU 已提交、GPU 少尾点”但没有修复路径的中间态。

## 增量绘制与分层

### Active delta

- 记录 `activeDrawnPointCount`。
- 新增点只构建从上次末点到当前末点的几何；连接处重叠一个点。
- 预分配/复用 vertex vector 或 GPU buffer，避免每点反复申请。
- 同一帧合并多段后一次 draw/swap。

### Completed + overlay + active

- completed layer 保存稳定、成本可摊销的历史内容。
- foreground layer 保存近期已提交 stroke，避免每笔都重建 completed。
- presentation overlay 保证“模型已提交但稳定层尚未完成”的笔迹立刻可见。
- active layer 只展示当前 stroke 或橡皮预览。
- bake 完成后先标记 overlay 的 committed prefix，待对应稳定层确认可见再移除；避免过早清理导致闪烁。
- 按经过测量的 stroke/point/memory 阈值把 foreground/overlay 合并到 completed。

这能避免每次 Move 重放全部历史笔迹。undo/redo 要同时更新事实模型和派生层。

### 脏区与瓦片

- 给 stroke 维护 bounds，并按笔宽/滤镜核扩大 padding。
- 只更新与 bounds 相交的瓦片。
- 绘制时再与 canvas clip/visible viewport 相交。
- undo 可对受影响瓦片做 copy-on-write 快照，并限制保留数量。
- 橡皮 active preview 可在首次触及瓦片时保存快照，Move 只处理新增区间；Cancel 恢复快照，End 再进入正式命令。
- tile size 取决于页面尺寸、笔刷核、缓存局部性和设备，不能把案例值直接当通用最优。

## 缓存与内存

至少为以下缓存定义 key、预算、淘汰和失效：

- 页面 renderer/context。
- completed/foreground/active 瓦片。
- 纹理上传和着色纹理。
- vertex/index buffer。
- 草稿 GPU replay cache。
- 导出 readback buffer。
- undo/redo 快照。

规则：

- key 包含真正影响结果的尺寸、颜色/alpha bucket、纹理版本、scale 和 schema；草稿/GPU 签名还要包含每个会改变像素的点属性。只用裸内存地址容易产生陈旧命中。
- texture/style/size/context 变化时定向失效。
- 页面按当前页距离淘汰只是策略起点；结合字节预算和低内存事件。
- 淘汰 GPU 派生缓存不丢失 CPU 事实数据。
- 大 vector 释放可用 swap/shrink 策略，但不要在热路径频繁归还/重分配。

## GLES 线程与 Surface

- 在固定线程创建和销毁 EGLDisplay/EGLSurface/EGLContext 及 GL object。
- UI/N-API 线程提交不可变命令，不直接抢 context。
- resize/surface recreate 用 epoch 丢弃旧命令并重建 viewport/FBO。
- context loss 后销毁 GL handle，并把仍由 CPU 保留的纹理数据标为待上传；不要只重建 program 而忘记资源恢复。
- 不依赖默认 framebuffer 在 swap 后保留。持久画布使用自有 texture/FBO，最后 blit/composite 到 Surface。
- 检查所有关键 EGL/GL 状态：config、makeCurrent、framebuffer completeness、shader link、context loss。
- 避免每个采样点都 makeCurrent + draw + swap；尽可能按帧合并。
- VBO 更新选择 `glBufferSubData`、orphan 或持久映射前先在目标设备测量；API 可用性随版本/驱动变化。

## 草稿和导出

### 草稿

- 锁内复制 page snapshot，锁外二进制序列化和写盘。
- 文件含 magic/version/尺寸/计数/长度上限。
- 临时文件写完再原子替换。
- dirty page 才保存；并发度有上限，批间让出执行机会。
- GPU cache 带内容 hash、page version、尺寸和格式版本；失配删除并从 CPU replay。
- hash 必须覆盖颜色、模式、宽度、透明度以及实际参与渲染的点坐标、压力、采样宽度、alpha 等字段；签名漏字段会把旧像素误判为可复用。
- 过期 replay 用 sequence/epoch 取消提交。

### 图片导出

- 大图优先 Native 直接构图、编码和落盘，避免 RGBA ArrayBuffer → ArkTS ImageData/PixelMap → 再编码的多次大内存复制。
- GPU 导出用离屏 FBO，保存/恢复 viewport、scroll 和 framebuffer 状态。
- `glReadPixels` 是同步点，放在非交互线程/渲染队列并测量；可用 PBO 等方案时仍需设备验证。
- 复用 readback buffer，检查 `width * height * 4` 溢出和分配失败。
- 行翻转、RGBA/BGRA、alpha 和背景合成必须有像素级测试。
- GPU 失败可回退 CPU，但回退原因要可观测，不能长期静默掩盖 GPU 故障。

## 常见伪优化

- 换成 ArrayBuffer，但仍每点一次跨语言调用。
- 加一把全局 mutex，把所有输入、GL、I/O 和编码串行化。
- GPU 增量绘制仍在每次 Move 重放全部 strokes。
- 每次 stroke/帧重新上传纹理或编译 shader。
- 依赖 `EGL_BUFFER_PRESERVED`，却不检查调用结果和设备支持。
- 每点/每 draw 打日志，测到的瓶颈主要来自日志。
- 固定 cache radius/tile size/batch size，不测设备与页面规模。
- 同时保留 CPU/GPU 两套渲染，却没有事实源、版本和失效协议。
- 在 UI 线程 `glReadPixels`、图片压缩或同步写大文件。
- 只看平均耗时，不看 p95/p99、首次使用和内存峰值。

## 验收表

| 指标 | 改前 | 改后 | 条件 |
| --- | --- | --- | --- |
| touch callback p95/p99 |  |  | 同设备、同笔迹 |
| input-to-pixel p95 |  |  | 高速连续笔迹 |
| frame p95/p99 / dropped |  |  | 页面含固定历史 stroke |
| 跨语言 calls / point |  |  | 同采样源 |
| draw/swap / frame |  |  | 同画笔 |
| texture uploads |  |  | 首次与稳态分开 |
| lock wait / max hold |  |  | 含保存与导出 |
| peak Native/GPU memory |  |  | 多页滚动 |
| draft save/load |  |  | 同内容大小 |
| full/viewport export |  |  | 同分辨率/格式 |
| visual diff / correctness |  |  | 笔锋、橡皮、透明度 |
