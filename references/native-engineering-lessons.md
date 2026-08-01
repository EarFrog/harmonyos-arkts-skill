# HarmonyOS Native 工程经验与避坑

## 目录

- [使用方式](#使用方式)
- [先证明活跃调用链](#先证明活跃调用链)
- [不要信任宽松的 Node-API helper](#不要信任宽松的-node-api-helper)
- [不要把二进制 buffer 当成批处理完成](#不要把二进制-buffer-当成批处理完成)
- [不要跨线程携带 JS 值](#不要跨线程携带-js-值)
- [handle 必须防止旧任务串线](#handle-必须防止旧任务串线)
- [mutex 不能解决线程亲和性](#mutex-不能解决线程亲和性)
- [不要在全局锁内做长任务](#不要在全局锁内做长任务)
- [GPU 不天然更快](#gpu-不天然更快)
- [不要依赖默认 framebuffer 持久化](#不要依赖默认-framebuffer-持久化)
- [缓存 key 必须表达内容身份](#缓存-key-必须表达内容身份)
- [主数据与派生 cache 必须分离](#主数据与派生-cache-必须分离)
- [二进制格式必须限制分配](#二进制格式必须限制分配)
- [异步结果必须检查新鲜度](#异步结果必须检查新鲜度)
- [减少跨语言大对象往返](#减少跨语言大对象往返)
- [热路径日志会制造假瓶颈](#热路径日志会制造假瓶颈)
- [缺少必要依赖时不要静默降级](#缺少必要依赖时不要静默降级)
- [经验参数不能直接迁移](#经验参数不能直接迁移)
- [交付前的反向检查](#交付前的反向检查)

## 使用方式

把本文件当作问题清单，不当作架构模板。

对每条经验执行：

1. 在目标仓库寻找触发信号。
2. 沿活跃调用链确认问题是否真实存在。
3. 只采用与当前约束匹配的修复。
4. 用构建、真机、性能或故障注入验证。

如果目标模块无状态、无图形或无持久化，跳过对应条目。不要为了应用经验而引入不需要的 session、cache、worker 或 renderer。

## 先证明活跃调用链

### 常见误判

- 看到大型 C++ 文件就认为是当前实现。
- 看到 feature flag 后面的代码就认为线上启用。
- 看到函数导出就认为 ArkTS 正在调用。
- 看到性能计数器就认为优化路径已经验证。

### 检查

- CMake 是否编译该源文件。
- 注册表是否导出该函数。
- ArkTS facade 和业务入口是否调用。
- feature flag、运行条件和设备分支是否可达。
- git 历史是在继续维护、兼容保留还是等待删除。

### 经验

只从活跃路径提炼通用经验。非活跃代码最多作为风险提示，不能描述成已经证明的方案。

## 不要信任宽松的 Node-API helper

### 常见误判

封装了 `GetNumber`、`GetString`、`CreateObject` 就认为边界安全。

### 风险

- 必填参数解析失败后静默变成 0、空串或默认值。
- `napi_get_cb_info` 实收参数不足仍继续执行。
- 创建对象/property/Promise/async work 的 status 被忽略。
- throw 后继续返回看似正常的结果。
- JS `number` 承载超出安全整数的 ID。

### 检查

- 固定参数接口同时校验 status、argc、类型、有限值、范围和业务不变量。
- 只有 `napi_ok` 后才读取输出参数。
- 错误路径只产生一种可识别结果：throw、reject 或明确错误对象。
- 大整数使用 BigInt、字符串或拆分字段。

### 经验

helper 只能减少重复代码，不能隐藏失败语义。边界越方便，越要检查它是否把错误吞掉。

## 不要把二进制 buffer 当成批处理完成

### 常见误判

把 object array 换成 ArrayBuffer 后，就宣称跨语言性能已经优化。

### 风险

如果每个事件仍立即 flush，调用次数没有下降，只减少了对象构造和解析。

### 检查

- `calls / item`。
- `items / call`。
- buffer 分配次数。
- 最大等待时间。
- input-to-result p95/p99。

### 经验

真正批处理需要同时控制最大条数和最大等待时间，并在 end/cancel/recycle/关闭前强制 flush。批量过大也会增加交互延迟。

## 不要跨线程携带 JS 值

### 风险

`napi_env`、`napi_value`、JS object 和普通 reference 都受线程与作用域约束。async `execute` 使用它们可能产生随机崩溃或 GC 相关问题。

### 检查

- execute context 是否只含复制后的 Native 数据。
- JS 值是否只在 complete/JS 线程创建。
- async work、deferred、reference 是否在每条失败路径释放。
- env cleanup 是否取消或等待任务。

### 经验

先把输入转换成拥有明确所有权的 C++ 数据，再排队。worker 完成后只回传 Native result，由 complete 构造 JS 结果。

## handle 必须防止旧任务串线

### 风险

对象销毁后 ID 被复用，旧异步任务可能把结果提交给新对象。

### 检查

- handle 是否包含或关联 generation。
- 任务排队时是否保存 generation/version。
- 完成时是否重新 lookup 并比较。
- destroy 是否先阻止新任务，再取消/等待旧任务。

### 经验

只有互不复用的 ID 还不够；重启、溢出、测试替身和 registry 重建都可能破坏假设。显式 generation 更可靠。

## mutex 不能解决线程亲和性

### 常见误判

“所有 GL 调用都加锁了，所以可以从任意 worker 调用。”

### 风险

EGL context、UI object、部分媒体/设备 API 需要固定线程。互斥只能阻止同时访问，不能迁移线程所有权。

### 检查

- 资源在哪个线程创建、使用和销毁。
- 是否有固定 renderer/owner queue。
- worker 是否绕过队列直接访问资源。
- context loss 和 shutdown 是否仍在 owner thread 处理。

### 经验

把线程亲和资源封装进串行 owner，让其他线程提交不可变命令。

## 不要在全局锁内做长任务

### 高风险操作

- 文件 I/O。
- 图片编码、压缩和大块复制。
- 整页重放或模型推理。
- GL draw/swap/readback。
- JS callback、Promise resolve。

### 经验

全局锁只保护 registry 和短状态转换。锁内获取强引用或复制 snapshot，锁外完成重任务，提交时用 generation/version 验证新鲜度。

同时记录 lock wait 和 max hold；只看函数总耗时无法定位锁竞争。

## GPU 不天然更快

### 常见误判

- 使用 GLES 就认为 CPU 压力已经降低。
- 每个事件都 makeCurrent、上传、draw、swap。
- GPU 和 CPU 各自重复采样或布局。
- 导出在 GPU 后立即同步 readback。

### 检查

- CPU sampling/geometry 时间。
- upload bytes 和次数。
- draw/swap 次数。
- `glReadPixels` 等同步点。
- 首次 shader/texture 创建。
- 目标设备的 p95/p99 和功耗。

### 经验

GPU 优化的核心是减少重复工作、批量提交和资源复用。若数据准备、同步和 readback 成本更高，CPU 路径可能更合适。

## 不要依赖默认 framebuffer 持久化

### 风险

swap 后默认 framebuffer 内容不保证保留。仅请求 preserved behavior 而不检查支持/返回值，可能在部分设备出现黑屏、残缺或随机丢内容。

### 经验

需要持久增量画布时，优先自持有 texture/FBO，再合成到窗口 Surface。若使用 preserved behavior，必须验证设备支持并准备 full redraw fallback。

## 缓存 key 必须表达内容身份

### 常见误判

- key 只使用裸指针、地址、长度或条目数。
- 内容变了但地址未变。
- 地址复用后命中旧结果。
- 签名漏掉 alpha、压力、scale、算法版本等影响输出的字段。

### 经验

key 包含所有影响结果的输入、资源 version、尺寸/format 和算法/schema version。缓存还要定义字节预算、失效事件和重建路径。

## 主数据与派生 cache 必须分离

### 风险

把 GPU cache、缩略图、索引或中间结果当作唯一恢复数据，会让驱动变化、版本升级和 cache 损坏变成数据丢失。

### 经验

长期保存业务源语义；派生 cache 可随时删除并从主数据重建。加载先校验签名，失配后重建，不让 cache 反向覆盖主数据。

## 二进制格式必须限制分配

### 常见误判

文件有 magic/version 就认为读取安全。

### 风险

损坏的 count 或 length 可能导致超大 vector/string 分配、整数溢出或越界读取。

### 检查

- 总文件大小。
- 单项和累计 count。
- 单项和累计 bytes。
- 乘法/加法溢出。
- 剩余字节。
- 数值有限值和范围。

### 经验

所有长度在分配前校验。保存使用临时文件和原子替换；加载旧版本通过独立迁移函数恢复源语义。

## 异步结果必须检查新鲜度

### 风险

延迟 replay、预热、加载或导出完成时，目标对象可能已经 resize、切页、关闭或加载了新版本。

### 经验

任务携带 handle generation、entity version 和 sequence。提交前全部比较，过期结果直接丢弃。取消只能作为优化，版本检查才是最终防线。

## 减少跨语言大对象往返

### 常见误判

把 Native RGBA 返回 ArkTS，再构造 ImageData/PixelMap、再编码，认为层次清晰。

### 风险

多次大内存复制、峰值内存和 GC 压力可能远大于编码本身。

### 经验

若 Native 已拥有模型或 renderer，让 Native 直接编码到临时文件，ArkTS 只处理 path、权限、相册或分享。保留对外 API 语义，不必保留内部数据搬运方式。

## 热路径日志会制造假瓶颈

### 风险

逐事件、逐点、逐帧或逐 draw 日志会改变调度和耗时，使 profile 主要测到日志。

### 经验

调试阶段使用探针，稳定后收敛为计数器、直方图、慢路径阈值和时间限流。大数组、像素 dump、readback 诊断默认关闭。

## 缺少必要依赖时不要静默降级

### 风险

三方 archive/header 缺失时仍生成可加载 `.so`，功能调用后才失败，CI 可能误判构建成功。

### 经验

产品必需能力在 CMake 配置期失败。可选能力暴露可测试 capability，并覆盖启用/禁用两种构建。记录 ABI、编译选项、传递依赖和许可证。

## 经验参数不能直接迁移

以下数值都属于目标设备和业务数据分布：

- batch size 和最大等待时间。
- tile size。
- cache entries/bytes。
- page/preload radius。
- worker concurrency。
- slow log threshold。
- undo snapshot 数量。

### 经验

迁移的是决策变量、约束和测量方法，不是原项目的数值。

## 交付前的反向检查

- 是否把一个案例结构写成所有项目必须遵守的架构？
- 是否引用了项目名、类名、commit 或业务常量？
- 是否把非活跃路径描述成有效优化？
- 是否把 ArrayBuffer、GPU、cache 或 async 当作天然收益？
- 是否遗漏错误、取消、复用、Surface destroy 和 env cleanup？
- 是否只看平均值，没有 p95/p99、首次使用和内存峰值？
- 是否只修 C++，没有同步注册、声明、facade、CMake 和 ABI？
- 是否在缺乏官方契约时凭记忆使用 API？
- 是否给出了目标仓库可执行的验证命令和结果？
