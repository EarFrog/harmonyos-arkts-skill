# 项目结构规范

## 目录

1. [标准项目结构](#标准项目结构)
2. [模块划分](#模块划分)
3. [命名规范](#命名规范)
4. [资源管理](#资源管理)
5. [最佳实践](#最佳实践)

---

## 标准项目结构

```
MyApp/
├── AppScope/
│   ├── app.json5                    # 应用全局配置
│   └── resources/
│       └── base/
│           ├── element/
│           │   ├── color.json       # 全局颜色
│           │   └── string.json      # 全局字符串
│           └── media/
│               └── app_icon.png     # 应用图标
│
├── entry/                           # 主模块（入口模块）
│   ├── src/
│   │   └── main/
│   │       ├── ets/                 # ArkTS 源码
│   │       │   ├── entryability/
│   │       │   │   └── EntryAbility.ets
│   │       │   ├── pages/           # 页面
│   │       │   │   ├── Index.ets
│   │       │   │   ├── Home.ets
│   │       │   │   └── Profile.ets
│   │       │   ├── components/      # 通用组件
│   │       │   │   ├── common/
│   │       │   │   │   ├── Header.ets
│   │       │   │   │   └── Loading.ets
│   │       │   │   └── business/    # 业务组件
│   │       │   │       ├── UserCard.ets
│   │       │   │       └── NewsItem.ets
│   │       │   ├── viewmodels/      # 视图模型
│   │       │   │   ├── HomeViewModel.ets
│   │       │   │   └── ProfileViewModel.ets
│   │       │   ├── models/          # 数据模型
│   │       │   │   ├── IUser.ets
│   │       │   │   └── INews.ets
│   │       │   ├── services/        # 服务层
│   │       │   │   ├── api/
│   │       │   │   │   ├── Api.ets
│   │       │   │   │   ├── UserApi.ets
│   │       │   │   │   └── NewsApi.ets
│   │       │   │   └── storage/
│   │       │   │       ├── PreferencesUtil.ets
│   │       │   │       └── DbUtil.ets
│   │       │   ├── utils/           # 工具类
│   │       │   │   ├── HttpUtil.ets
│   │       │   │   ├── DateUtil.ets
│   │       │   │   └── LogUtil.ets
│   │       │   ├── constants/       # 常量
│   │       │   │   ├── AppConstants.ets
│   │       │   │   └── ApiConstants.ets
│   │       │   └── common/          # 公共定义
│   │       │       ├── enums.ets
│   │       │       └── types.ets
│   │       ├── resources/           # 模块资源
│   │       │   └── base/
│   │       │       ├── element/
│   │       │       │   ├── color.json
│   │       │       │   ├── string.json
│   │       │       │   └── float.json
│   │       │       ├── media/
│   │       │       │   └── images/
│   │       │       └── profile/
│   │       │           └── main_pages.json
│   │       └── module.json5         # 模块配置
│   ├── build-profile.json5
│   ├── hvigorfile.ts
│   └── oh-package.json5
│
├── feature_user/                    # Feature 模块（用户模块）
│   └── src/main/ets/
│       ├── pages/
│       │   ├── Login.ets
│       │   └── Register.ets
│       ├── components/
│       └── viewmodels/
│
├── feature_news/                    # Feature 模块（新闻模块）
│   └── ...
│
├── common/                          # 公共共享模块
│   └── src/main/ets/
│       ├── components/              # 共享组件
│       ├── utils/                   # 共享工具
│       └── constants/               # 共享常量
│
├── build-profile.json5              # 构建配置
├── hvigorfile.ts                    # 构建脚本
├── oh-package.json5                 # 依赖配置
└── oh_modules/                      # 依赖包
```

---

## 模块划分

### 模块类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `entry` | 入口模块，应用启动页 | 主页、Tab 导航 |
| `feature_*` | 功能模块，按业务划分 | `feature_user`、`feature_news` |
| `common` | 公共共享模块 | 通用组件、工具类 |

### 模块依赖关系

```
entry → feature_user → common
      → feature_news → common
      → feature_cart → common
```

**原则**：
- `entry` 依赖所有 `feature_*` 和 `common`
- `feature_*` 只依赖 `common`，不相互依赖
- `common` 不依赖任何业务模块

### HAR 共享包

```typescript
// common 模块的 oh-package.json5
{
  "name": "common",
  "version": "1.0.0",
  "description": "公共共享模块",
  "main": "index.ets",
  "author": "",
  "license": "ISC"
}

// common/index.ets - 导出公共接口
export * from './src/main/ets/components'
export * from './src/main/ets/utils'
export * from './src/main/ets/constants'

// 在 feature 模块中使用
import { Header, formatDate, ApiConstants } from 'common'
```

---

## 命名规范

### 文件命名

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 页面 | PascalCase.ets | `Index.ets`、`UserProfile.ets` |
| 组件 | PascalCase.ets | `UserCard.ets`、`LoadingSpinner.ets` |
| 工具类 | PascalCase + Util.ets | `HttpUtil.ets`、`DateUtil.ets` |
| 接口/模型 | I + PascalCase.ets | `IUser.ets`、`INews.ets` |
| 常量 | PascalCase + Constants.ets | `AppConstants.ets` |
| 服务 | PascalCase + Service.ets | `UserService.ets` |

### 代码命名

```typescript
// 组件名：PascalCase
@Component
struct UserCard { }

// 变量/函数：camelCase
let userName: string = ''
function fetchUserData() { }

// 常量：UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3
const API_BASE_URL = 'https://api.example.com'

// 接口：I 前缀
interface IUserData {
  id: number
  name: string
}

// 类型别名：PascalCase
type UserStatus = 'active' | 'inactive'

// 枚举替代：const 对象
const UserStatus = {
  ACTIVE: 'active',
  INACTIVE: 'inactive'
} as const

// 私有成员：_ 前缀（可选）
private _cache: Map<string, string> = new Map()
```

---

## 资源管理

### 资源目录结构

```
resources/
└── base/
    ├── element/
    │   ├── color.json          # 颜色
    │   ├── string.json         # 字符串
    │   ├── float.json          # 尺寸
    │   ├── integer.json        # 整数
    │   └── boolean.json        # 布尔
    ├── media/
    │   ├── icon.png
    │   ├── logo.png
    │   └── images/
    │       ├── banner.png
    │       └── avatar.png
    ├── profile/
    │   └── main_pages.json     # 页面路由配置
    └── rawfile/                # 原始文件
        └── config.json
```

### 资源定义

```json
// element/color.json
{
  "color": [
    { "name": "primary", "value": "#007DFF" },
    { "name": "secondary", "value": "#666666" },
    { "name": "error", "value": "#FF0000" },
    { "name": "background", "value": "#F5F5F5" },
    { "name": "card_bg", "value": "#FFFFFF" }
  ]
}

// element/string.json
{
  "string": [
    { "name": "app_name", "value": "我的应用" },
    { "name": "login", "value": "登录" },
    { "name": "logout", "value": "退出登录" }
  ]
}

// element/float.json
{
  "float": [
    { "name": "font_size_small", "value": "12vp" },
    { "name": "font_size_normal", "value": "14vp" },
    { "name": "font_size_large", "value": "18vp" },
    { "name": "padding_normal", "value": "16vp" },
    { "name": "border_radius", "value": "8vp" }
  ]
}
```

### 资源引用

```typescript
// 引用颜色
.fontColor($r('app.color.primary'))
.backgroundColor($r('app.color.card_bg'))

// 引用字符串
.text($r('app.string.login'))

// 引用尺寸
.fontSize($r('app.float.font_size_normal'))
.padding($r('app.float.padding_normal'))

// 引用图片
Image($r('app.media.icon')).width(24).height(24)

// 引用 rawfile
Image($rawfile('images/banner.png'))

// 国际化：自动根据系统语言切换
// resources/en/element/string.json
// resources/zh/element/string.json
```

---

## 最佳实践

### 1. 目录层级控制

- 源码目录深度不超过 5 层
- 单个文件不超过 500 行，超过则拆分

### 2. 导入导出规范

```typescript
// 推荐：按类型分组导入
import { router } from '@kit.ArkUI'
import { http } from '@kit.NetworkKit'

import { UserCard } from '../components/UserCard'
import { formatDate } from '../utils/DateUtil'
import { IUser } from '../models/IUser'

// 导出：统一从 index.ets 导出
// components/index.ets
export { Header } from './Header'
export { Footer } from './Footer'
export { UserCard } from './business/UserCard'

// 使用时
import { Header, Footer, UserCard } from '../components'
```

### 3. 页面路由配置

```json
// main_pages.json
{
  "src": [
    "pages/Index",
    "pages/Home",
    "pages/Profile",
    "pages/Settings",
    "pages/Login"
  ]
}
```

### 4. 模块化建议

- 小型项目：单 `entry` 模块即可
- 中型项目：`entry` + `common`
- 大型项目：`entry` + 多个 `feature_*` + `common`

### 5. 注释规范

```typescript
/**
 * 用户卡片组件
 * @param user - 用户数据
 * @param onAvatarClick - 头像点击回调
 */
@Component
export struct UserCard {
  @Prop user: IUser
  onAvatarClick?: () => void

  build() {
    // ...
  }
}
```
