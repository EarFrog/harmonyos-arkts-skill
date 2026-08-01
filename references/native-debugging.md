# Native 调试、图形故障与性能验证

## 目录

- [先分层](#先分层)
- [构建与加载](#构建与加载)
- [崩溃和并发](#崩溃和并发)
- [画布故障](#画布故障)
- [性能诊断](#性能诊断)
- [验证矩阵](#验证矩阵)

## 先分层

按最早失败层排查：

1. Hvigor 是否进入 CMake。
2. CMake 是否生成正确 ABI 的 `.so`。
3. `.so` 是否打包且依赖可加载。
4. 模块是否注册、导出是否存在。
5. ArkTS 参数是否符合 Native 契约。
6. session/surface/context 是否处于可用生命周期。
7. 渲染结果是否正确。
8. 性能是否满足目标。

不要在 import 失败时先调 shader，也不要在黑屏时先改笔刷算法。

## 构建与加载

### import `lib*.so` 失败

- CMake target 与最终库名。
- `NAPI_MODULE`/`nm_modname`。
- types package 或 ArkTS 门面。
- 目标 ABI 产物是否在包内。
- `readelf`/平台工具显示的动态依赖是否都可满足。

### undefined symbol

- 新 `.cpp` 是否加入 target。
- 声明/定义和 namespace 是否一致。
- C API 是否需要 `extern "C"`。
- 预编译 archive 架构和链接顺序。
- 静态库是否缺传递依赖或 PIC。

### 构建命令

优先使用仓库 CI、脚本或 DevEco 当前项目的任务列表。若本机缺匹配 SDK/签名/设备，明确区分：

- 已做静态验证。
- 已做 CMake/模块编译。
- 已做 HAP 构建。
- 已做真机运行。

## 崩溃和并发

LLDB/Native crash 栈重点看：

- callback 参数解析后的空指针/越界。
- session 或 renderer 已释放。
- `napi_env` owner 不匹配或 env 已销毁。
- async complete 与 shutdown 竞态。
- EGL context 在错误线程 current。
- NativeWindow/Surface 销毁后继续 swap。
- buffer 大小乘法溢出或分配失败。

若看到 `param env not equal to its owner`、`owner env has been destroyed`、`current tsfn was created by dead env` 等日志，回查缓存 env/value/ref、TSFN 关闭顺序和环境清理。

## 画布故障

### 黑屏

- Surface ID/NativeWindow 是否有效且已绑定当前 page/session。
- width/height 是否已从 vp 转为 px，是否为 0。
- `eglInitialize`、config、context、window surface、`eglMakeCurrent` 是否成功。
- framebuffer 是否 complete，shader compile/link 是否成功。
- viewport、scroll、坐标系和裁剪是否把内容移出可见区。
- context loss 或 Surface recreate 后是否重建 GL object/纹理。

### 闪烁、旧内容丢失、笔迹断裂

- 不要假定 swap 后默认 framebuffer 仍保留全部像素。
- 检查设置 `EGL_BUFFER_PRESERVED` 是否真的成功并被目标设备支持。
- 持久增量画布优先把内容保存在自有 FBO/texture，再按帧组合到 Surface。
- 增量线段必须从上次末点重叠一个点，避免连接缝隙。
- resize、undo、clear、context loss 后应触发全量重建，而不是继续追加 delta。

### 上下颠倒、颜色/透明度异常

- GL 原点与 UI/图片原点转换。
- RGBA/BGRA 通道顺序。
- premultiplied/unpremultiplied alpha。
- 透明背景转 JPEG 前必须先与目标背景色合成。
- `glReadPixels` 行翻转与 stride。

### 橡皮错误

- blend mode 是否为目标语义，例如 destination-out。
- active preview 与 committed layer 的快照/恢复顺序。
- undo 是否保存受影响区域，而不是复制整页或什么都不保存。

## 性能诊断

先测：

- touch callback、跨语言调用、采样、vertex build、draw、swap 的分段耗时。
- frame time 的 p50/p95/p99 和掉帧数。
- 锁等待和最长持锁时间。
- 每帧点数、顶点数、draw call、纹理上传次数。
- CPU/GPU 内存峰值、页面/瓦片/cache 数量。
- 草稿快照、写入、GPU replay、图片 readback/编码耗时。

日志策略：

- 热路径只累积计数和最大值；结束或采样窗口后汇总。
- 慢调用按阈值记录，并做时间限流。
- 日志不包含笔迹原始内容、完整路径、账号或其他隐私。
- 诊断开关与发布构建隔离。

做 A/B 时一次只改变一个主要变量，并在同设备、同笔迹、同页面尺寸、同构建类型下比较。GPU 使用率上升不等于体验更好；以输入延迟、帧稳定性、功耗和正确性共同判断。

## 验证矩阵

- 冷启动/首次落笔/连续长笔迹/快速短笔迹。
- 手指、手写笔、压力为 0/缺失/异常。
- Up、Cancel、多指拒绝、组件 recycle/reuse/disappear。
- 多页滚动、远页缓存淘汰、返回旧页。
- undo/redo/clear/橡皮。
- 前后台、Surface 重建、窗口尺寸变化。
- 草稿保存中继续绘制、取消、损坏文件、旧 schema。
- GPU cache 命中/失配/删除后的 CPU replay。
- 透明/白色背景、PNG/JPEG、全页/viewport 导出。
- 低内存、超大页面、超长笔迹和异常输入上限。
