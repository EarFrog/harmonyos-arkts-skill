# Native 渲染架构

## 目录

- [选择事实模型](#选择事实模型)
- [按意图记录命令](#按意图记录命令)
- [使用多时间尺度分层](#使用多时间尺度分层)
- [按脏区和瓦片更新](#按脏区和瓦片更新)
- [只渲染活动增量](#只渲染活动增量)
- [复用 Native Drawing 资源](#复用-native-drawing-资源)
- [统一像素语义](#统一像素语义)
- [管理 GLES 资源与线程](#管理-gles-资源与线程)
- [构建持久画布](#构建持久画布)
- [控制缓存和内存](#控制缓存和内存)
- [验证渲染架构](#验证渲染架构)

## 选择事实模型

不要默认把整张 RGBA 位图或默认 framebuffer 当作唯一数据。根据产品需要选择事实模型：

| 事实模型 | 适合 | 代价 |
| --- | --- | --- |
| 矢量命令/对象 | 可编辑、撤销、缩放、重放 | 重放成本和模型复杂度 |
| 像素瓦片 | 局部修改、固定分辨率 | 版本迁移和缩放受限 |
| 媒体帧/纹理流 | 视频、相机、实时滤镜 | 外部时序和 buffer 所有权 |
| 混合模型 | 高频交互 + 长期可编辑 | 一致性和失效协议更复杂 |

GPU texture、FBO、shader、VBO 和窗口 surface 通常是派生资源。context loss 后应能从事实模型、可信 cache 或上游数据重建。

## 按意图记录命令

撤销/重做优先记录业务意图，不在每次操作复制完整页面。

通用命令示例：

- add/remove/update object。
- erase/clear region。
- transform layer。
- apply filter。
- replace source。

命令保存恢复所需的最小 before/after 数据。为命令历史同时设置：

- 条数或时长预算。
- 实际字节预算。
- 大对象外部存储策略。
- schema/version。

派生像素快照可在内存压力下丢弃并重建；业务对象和不可逆输入不能静默淘汰。

## 使用多时间尺度分层

高频交互画布可拆成：

| 层 | 责任 | 典型更新频率 |
| --- | --- | --- |
| stable/completed | 已烘焙、低变化历史 | 低 |
| recent/foreground | 近期提交对象 | 每操作或小批 |
| presentation/overlay | 已提交但稳定层尚未可见的过渡内容 | 短暂 |
| active/preview | 当前手势、选择、橡皮或临时效果 | 高频 |

overlay 解决模型 commit 与稳定层可见之间的时间窗口。不要在下层尚未呈现前立即清除 overlay；用 sequence、prefix 或 generation 确认对应内容已经接管。

达到经过测量的对象数、点数、字节数或时间阈值后，再把 recent 合并到 stable。阈值必须用目标设备 profile 决定。

## 按脏区和瓦片更新

为可绘制对象维护 bounds，并按笔宽、阴影、滤镜核、纹理旋转等扩大 padding。

局部更新流程：

1. 计算旧 bounds 与新 bounds 的并集。
2. 与 viewport/clip 相交。
3. 映射到受影响瓦片。
4. 只更新这些瓦片。
5. 更新 tile content version。

撤销需要像素快照时，对受影响瓦片使用 copy-on-write：

- 首次写共享瓦片前 clone。
- snapshot 只保留涉及区域。
- 恢复后同步 dirty/version。
- 限制快照总字节，不只限制条数。

tile size 取决于页面规模、更新局部性、笔刷/滤镜核和设备缓存，不存在通用固定值。

## 只渲染活动增量

renderer 保存已消费位置，例如 `consumedItemCount` 或 `renderedPointCount`。

每次更新：

1. 从权威模型获取 `[consumed, produced)`。
2. 为连接连续性按需多取一个前置元素。
3. 只生成新增几何或像素。
4. 更新消费位置。
5. 同一帧合并 draw/swap。

结构变化、resize、撤销或 cache 失配才触发 full render。

任何仅为显示做的降采样都不能修改事实模型。用高速转角、短操作、边缘、透明度突变和结束尾部做视觉差异测试。

## 复用 Native Drawing 资源

对 OH_Drawing handle 使用 RAII wrapper，明确 bitmap、image、shader、path、brush、pen 和 sampling option 的所有权。

复用方向：

- image/bitmap 与其像素内容版本绑定。
- sampling、src/dst rect 和通用绘制状态集中准备。
- 不在 draw callback 内反复创建昂贵对象。
- 纹理着色或滤镜结果设置预算和定向失效。
- callback 内只复制轻量 snapshot，避免长时间持模型锁。

缓存 key 不能只依赖裸内存地址。容器释放并复用地址时会命中旧内容。加入不可回退的 content version、资源 ID 或内容 hash。

## 统一像素语义

CPU、Native Drawing、GLES 和导出路径共享纯函数定义：

- 颜色解析和通道顺序。
- alpha 与 premultiplied/unpremultiplied。
- 透明背景和背景合成。
- 纹理采样与边缘处理。
- 擦除/混合语义。
- 行方向和坐标原点。

长期数据保存 source semantics，派生 render color、bucket、顶点和像素 cache 可重建。

为纯函数建立小尺寸 golden tests，再做整帧视觉 diff。不要在多个 renderer 内维护相似但不完全相同的循环和公式。

## 管理 GLES 资源与线程

renderer 可以持有：

- EGLDisplay/EGLSurface/EGLContext。
- window/native surface identity。
- program、shader、VBO/IBO、texture、FBO。
- viewport、transform 和 active state。
- readback/export buffer。

要求：

- 在固定线程或串行 renderer queue 创建、使用和销毁 context。
- UI/N-API 线程提交不可变命令，不直接抢 context。
- Surface resize/recreate 更新 generation，丢弃旧命令。
- context loss 后清理 GL handle，并把 CPU 资源标记为待上传。
- shader/program/VBO/texture 延迟创建并复用。
- 纹理只在内容版本变化时上传。
- 关键 EGL/GL 调用检查返回值和状态。

registry/global 锁不能覆盖 makeCurrent、draw、swap、readback、编码或 I/O。

## 构建持久画布

默认 framebuffer 在 swap 后不保证保留。请求 preserved swap behavior 时也要检查设备支持和调用结果。

更可控的结构：

```text
业务事实模型
    |
    v
规范化增量
    |
    v
自持有 page texture/FBO
    |
    +--> active/overlay 合成
    |
    v
window surface + swap
```

Surface 丢失只重建展示目标；context 丢失才从事实模型或可信 cache 重建 page texture。

## 控制缓存和内存

每类 cache 都定义：

- key 和 schema。
- 字节预算。
- entry 数量辅助上限。
- 淘汰策略。
- 失效事件。
- rebuild 路径。
- hit/miss/eviction/peak bytes 指标。

重点统计：

- CPU tile/bitmap bytes。
- GPU texture/FBO bytes。
- vertex/index buffer capacity。
- undo snapshot bytes。
- readback/export buffer。
- 多页面或多 renderer 总量。

按“当前页距离”淘汰只能作为启发式，还要结合字节预算、最近使用和系统低内存事件。

## 验证渲染架构

- input-to-pixel p50/p95/p99。
- full render 与 delta render 次数。
- draw/swap 次数和每帧合并率。
- vertex build、upload、draw、swap 分段时间。
- 脏区面积、tile clone/rebuild 数。
- texture upload 次数和字节。
- lock wait/max hold。
- CPU/GPU 内存稳态和峰值。
- Surface/context 重建恢复时间。
- CPU、屏幕和导出结果的像素/视觉一致性。

平均值变好但 p99、首次使用、内存峰值或正确性变差时，不判定优化完成。
