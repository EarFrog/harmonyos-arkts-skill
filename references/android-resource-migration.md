# Android 资源迁移到 HarmonyOS

## 目录

1. [迁移原则](#迁移原则)
2. [目录映射](#目录映射)
3. [values XML 转 JSON](#values-xml-转-json)
4. [Drawable 与图片](#drawable-与图片)
5. [Adaptive Icon](#adaptive-icon)
6. [Qualifier 映射](#qualifier-映射)
7. [多语言资源](#多语言资源)
8. [资源引用替换](#资源引用替换)
9. [缺失资源处理](#缺失资源处理)
10. [验证清单](#验证清单)

---

## 迁移原则

- 资源迁移应先于页面迁移执行。
- 保留 Android 资源 key 的可读语义，不随意改名。
- 资源名必须符合 HarmonyOS 资源命名要求：小写字母、数字、下划线。
- 同一语义资源在 `base`、`dark`、多语言目录中使用同名 key。
- 不支持的 Android qualifier 不要误转为 `base`，应记录为未映射。
- 缺失资源必须显式登记，不要静默替换为无关占位图。

推荐输出：

```text
spec/baseline/resources/resource-mapping.md
spec/baseline/resources/resource-migration-report.md
```

---

## 目录映射

| Android 目录 | HarmonyOS 目标 | 处理 |
|--------------|----------------|------|
| `res/values/strings.xml` | `resources/base/element/string.json` | XML 转 JSON |
| `res/values/colors.xml` | `resources/base/element/color.json` | XML 转 JSON |
| `res/values/dimens.xml` | `resources/base/element/float.json` | 单位转换 |
| `res/values/integers.xml` | `resources/base/element/integer.json` | XML 转 JSON |
| `res/values/bools.xml` | `resources/base/element/boolean.json` | XML 转 JSON |
| `res/values/arrays.xml` | `resources/base/element/strarray.json` / `intarray.json` | 按数组类型拆分 |
| `res/values/plurals.xml` | `resources/base/element/plural.json` | 复数资源 |
| `res/drawable*/` 图片 | `resources/<qualifier>/media/` | 复制或转换 |
| `res/mipmap*/` 图片 | `resources/<qualifier>/media/` | 图标资源 |
| `res/raw/` | `resources/rawfile/` | 直接复制 |
| `res/font/` | `resources/rawfile/fonts/` | 直接复制 |
| `assets/` | `resources/rawfile/` 或业务 asset 目录 | 按用途放置 |
| `res/xml/` | `resources/base/profile/` | 仅迁移配置类 XML |
| `res/layout/` | 无直接资源等价 | 转 ArkUI 代码 |
| `res/menu/` | 无直接资源等价 | 转 ArkUI 菜单组件 |
| `res/anim/` / `animator/` | 无直接等价 | 转 ArkUI 动画逻辑 |
| `res/values/styles.xml` | 无直接等价 | 提取颜色、字号、间距、主题语义 |

---

## values XML 转 JSON

### string.json

Android：

```xml
<resources>
    <string name="app_name">Demo</string>
    <string name="welcome">Hello\nWorld</string>
</resources>
```

HarmonyOS：

```json
{
    "string": [
        {
            "name": "app_name",
            "value": "Demo"
        },
        {
            "name": "welcome",
            "value": "Hello\\nWorld"
        }
    ]
}
```

处理要求：

- 解码 XML entity：`&amp;`、`&lt;`、`&gt;`、`&quot;`、`&apos;`
- 保留 `\n`、`\t`
- Android 格式化占位符应人工确认，如 `%1$s`、`%d`
- HTML 富文本字符串应记录，需要 ArkUI `Span` 或 Web 渲染方案

### color.json

| Android 值 | HarmonyOS 值 |
|------------|--------------|
| `#RGB` | 展开为 `#ffRRGGBB` |
| `#ARGB` | 展开为 `#AARRGGBB` |
| `#RRGGBB` | 补 alpha 为 `#ffRRGGBB` |
| `#AARRGGBB` | 保持不变 |
| `@color/xxx` | 解析引用链 |

HarmonyOS：

```json
{
    "color": [
        {
            "name": "brand_primary",
            "value": "#ff3366ff"
        }
    ]
}
```

### float.json

| Android 单位 | HarmonyOS 单位 | 说明 |
|--------------|----------------|------|
| `dp` | `vp` | 布局尺寸 |
| `sp` | `fp` | 字体尺寸 |
| `px` | `px` | 仅明确像素场景保留 |
| 无单位数字 | `vp` | 需记录为推断 |

示例：

```json
{
    "float": [
        {
            "name": "page_padding",
            "value": "16vp"
        },
        {
            "name": "title_size",
            "value": "20fp"
        }
    ]
}
```

---

## Drawable 与图片

### 普通图片

| 类型 | 处理 |
|------|------|
| PNG / JPG / WEBP | 复制到 `media/` |
| GIF | 复制到 `media/`，确认 ArkUI 使用场景 |
| SVG | 检查 viewport、fill、stroke、尺寸 |
| 9-patch | 不能直接等价，需转普通图片或 ArkUI 背景样式 |

### VectorDrawable

Android `<vector>` 可转为 SVG。注意：

- `viewportWidth` / `viewportHeight` 转为 SVG `viewBox`
- `pathData` 转为 `<path d="...">`
- `fillColor` / `strokeColor` 转为 SVG 属性
- Android theme attr，如 `?attr/colorControlNormal`，需解析为具体颜色或改为资源引用
- `tint`、`alpha`、group transform 需要单独验证

### Shape Drawable

常见 shape 不建议一律转 SVG。优先用 ArkUI 样式表达：

| Android shape | ArkUI |
|---------------|-------|
| solid | `.backgroundColor()` |
| corners | `.borderRadius()` |
| stroke | `.border()` |
| padding | `.padding()` |
| gradient | `.linearGradient()` 或资源图 |

当 shape 作为图片资源被多个地方引用，才考虑生成 SVG 或封装公共样式。

### Selector / StateList

Android selector 通常对应交互态。迁移时不要只取默认图后丢弃状态。

| Android 状态 | ArkUI 迁移 |
|--------------|------------|
| `state_pressed` | `.stateStyles({ pressed: ... })` 或点击态样式 |
| `state_selected` | 由选中状态变量控制 |
| `state_checked` | Checkbox / Toggle / 自定义状态 |
| `state_enabled=false` | `.enabled(false)` + 禁用样式 |

如果只迁默认态，应在报告中记录被丢弃的状态。

---

## Adaptive Icon

Android adaptive icon：

```xml
<adaptive-icon>
    <background android:drawable="@color/brand_color" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
    <monochrome android:drawable="@drawable/ic_launcher_mono" />
</adaptive-icon>
```

HarmonyOS 通常使用 layered image：

```json
{
    "layered-image": {
        "background": "$media:brand_color_bg",
        "foreground": "$media:ic_launcher_foreground"
    }
}
```

处理要求：

1. `background` 和 `foreground` 转为 `$media:name`
2. `@color/xxx` 不能直接作为 layered image layer，应生成纯色 PNG 或改用可接受的媒体资源
3. `monochrome` 没有直接等价时不要写入 layered image，但其引用的图片仍可作为普通资源迁移
4. 应同步更新 `AppScope/resources/base/media/` 和应用配置中的 icon 引用

---

## Qualifier 映射

### 密度

| Android qualifier | HarmonyOS qualifier |
|-------------------|---------------------|
| `ldpi` | `sdpi` |
| `mdpi` | `mdpi` |
| `hdpi` | `ldpi` |
| `xhdpi` | `xldpi` |
| `xxhdpi` | `xxldpi` |
| `xxxhdpi` | `xxxldpi` |
| `nodpi` | `base` |
| `anydpi` | `base` |

### 语言和地区

| Android | HarmonyOS |
|---------|-----------|
| `values-en` | `en/element/` |
| `values-en-rUS` | `en_US/element/` |
| `values-zh` | `zh/element/` |
| `values-zh-rCN` | `zh_CN/element/` |
| `drawable-ar` | `ar/media/` |

### 深色模式和方向

| Android | HarmonyOS |
|---------|-----------|
| `night` | `dark` |
| `notnight` | `light` |
| `land` | `horizontal` |
| `port` | `vertical` |

### 不建议自动映射的 qualifier

以下目录没有稳定一一映射关系，默认跳过并记录：

- `sw<N>dp`
- `w<N>dp`
- `h<N>dp`
- `small` / `normal` / `large` / `xlarge`
- 特定 API：`v21`、`v26` 等只作为兼容条件，通常剥离

示例：

| Android 目录 | 处理 |
|--------------|------|
| `drawable-xhdpi` | `xldpi/media/` |
| `mipmap-anydpi-v26` | `base/media/`，剥离 `v26` |
| `values-zh-rCN-night` | `zh_CN-dark/element/` |
| `values-sw600dp` | 默认跳过，报告未映射 |

---

## 多语言资源

### 最低要求

迁移字符串资源时，至少保证：

1. `base/element/string.json` 存在
2. 如果 Android 有 `values-en` 或 `values-zh-rCN`，迁移对应语言目录
3. 各语言 `string.json` 的 key 集合保持一致

### key 一致性

若某语言缺 key：

- 优先从 Android 对应语言补值
- 找不到时使用 base 值并在报告中记录待翻译
- 不要让不同语言目录 key 集合发散

报告示例：

```markdown
## Language Resources

| 语言 | key 数 | 状态 |
|------|-------|------|
| base | 120 | PASS |
| en_US | 120 | PASS |
| zh_CN | 120 | PASS |

缺失翻译：
- en_US.settings_backup_summary：使用 base fallback
```

---

## 资源引用替换

| Android | HarmonyOS |
|---------|-----------|
| `@string/app_name` | `$r('app.string.app_name')` |
| `@color/brand_primary` | `$r('app.color.brand_primary')` |
| `@dimen/page_padding` | `$r('app.float.page_padding')` |
| `@drawable/ic_back` | `$r('app.media.ic_back')` |
| `@mipmap/ic_launcher` | `$r('app.media.ic_launcher')` |
| `@raw/intro` | `rawfile` 路径读取 |

ArkTS 中使用资源引用时，注意目标 API 的参数类型。遇到 SDK API options 或 record 对象，不要内联未显式类型的对象字面量。

```typescript
Text($r('app.string.app_name'))
    .fontColor($r('app.color.text_primary'))
    .fontSize($r('app.float.title_size'))

Image($r('app.media.ic_back'))
    .width(24)
    .height(24)
```

---

## 缺失资源处理

缺失资源分三类：

| 类型 | 处理 |
|------|------|
| Android 源码缺失 | 登记为 `missing_source` |
| 三方库资源缺失 | 从 APK merged resources 或依赖库查找 |
| HarmonyOS 不支持 | 登记替代方案 |

不要做：

- 不说明原因地替换为任意系统图标
- 使用空白图片让编译通过
- 把所有缺失资源都合并成一个 `placeholder.png`

建议报告：

```markdown
| Android | 期望 HarmonyOS | 状态 | 处理 |
|---------|----------------|------|------|
| @drawable/ic_vip | app.media.ic_vip | missing_source | 等 Android 资源补齐 |
| @anim/fade_in | ArkUI animateTo | unsupported_direct | 转代码动画 |
```

---

## 验证清单

资源迁移后检查：

- `string.json`、`color.json`、`float.json` JSON 格式合法
- 多语言 key 集合一致
- `$r('app.*.*')` 在编译期可解析
- SVG 在深浅色下可见
- 图标尺寸和 viewport 正确
- app icon / layered image 配置正确
- `dark/` 目录中的资源与 `base/` 同名
- `rawfile` 路径读取代码已处理异常
- 运行项目实际提供的适用 Hvigor/CI 等价构建并通过
- 编译校验只使用项目已有构建环境；禁止为通过编译修改 DevEco/SDK/JDK/Node/ohpm/hvigor、`local.properties`、签名配置、PATH 或本机工具链

---

## 资源映射表模板

```markdown
# Resource Mapping

## Summary

- Android resource root: `<path>`
- HarmonyOS resource root: `entry/src/main/resources`
- Converted: `<count>`
- Missing: `<count>`
- Unsupported: `<count>`

## Mapping

| Android | HarmonyOS | 文件 | 状态 | 备注 |
|---------|-----------|------|------|------|
| @string/app_name | $r('app.string.app_name') | base/element/string.json | converted | |
| @color/brand_primary | $r('app.color.brand_primary') | base/element/color.json | converted | |
| @drawable/ic_back | $r('app.media.ic_back') | base/media/ic_back.svg | converted | vector |
```
