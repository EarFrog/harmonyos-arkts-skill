# 本地存储

## 目录

1. [Preferences 轻量存储](#preferences-轻量存储)
2. [RelationalStore 关系型数据库](#relationalstore-关系型数据库)
3. [文件存储](#文件存储)
4. [最佳实践](#最佳实践)

---

## Preferences 轻量存储

适用场景：用户偏好设置、小型配置数据（< 100KB）。

### 基础用法

```typescript
import { preferences } from '@kit.ArkData'

// 获取 Preferences 实例
let dataPreferences: preferences.Preferences | null = null

async function getPreferences(context: Context): Promise<void> {
    try {
        dataPreferences = await preferences.getPreferences(context, 'my_store')
    } catch (err) {
        console.error(`getPreferences failed: ${err.message}`)
    }
}

// 存入数据
async function putString(key: string, value: string): Promise<void> {
    if (dataPreferences) {
        try {
            await dataPreferences.put(key, value)
            await dataPreferences.flush()  // 持久化到磁盘
        } catch (err) {
            console.error(`putString failed: ${(err as Error).message}`)
        }
    }
}

// 读取数据
async function getString(key: string, defaultValue: string = ''): Promise<string> {
    if (dataPreferences) {
        try {
            return await dataPreferences.get(key, defaultValue) as string
        } catch (err) {
            console.error(`getString failed: ${(err as Error).message}`)
        }
    }
    return defaultValue
}

// 删除数据
async function remove(key: string): Promise<void> {
    if (dataPreferences) {
        try {
            await dataPreferences.delete(key)
            await dataPreferences.flush()
        } catch (err) {
            console.error(`remove failed: ${(err as Error).message}`)
        }
    }
}

// 清空所有
async function clearAll(): Promise<void> {
    if (dataPreferences) {
        try {
            await dataPreferences.clear()
            await dataPreferences.flush()
        } catch (err) {
            console.error(`clearAll failed: ${(err as Error).message}`)
        }
    }
}
```

### 支持的数据类型

```typescript
// 字符串
await dataPreferences.put('name', '张三')

// 数字
await dataPreferences.put('age', 25)
await dataPreferences.put('score', 98.5)

// 布尔
await dataPreferences.put('isVip', true)

// 数组（存为 JSON 字符串）
await dataPreferences.put('tags', JSON.stringify(['tag1', 'tag2']))
const tags: string[] = JSON.parse(await dataPreferences.get('tags', '[]') as string)

// 对象（存为 JSON 字符串）
interface IConfig {
    theme: string
    fontSize: number
}
await dataPreferences.put('config', JSON.stringify({ theme: 'dark', fontSize: 14 }))
const config: IConfig = JSON.parse(await dataPreferences.get('config', '{}') as string)
```

### 封装 Preferences 工具类

```typescript
// utils/PreferencesUtil.ets
import { preferences } from '@kit.ArkData'

class PreferencesUtil {
    private static instance: PreferencesUtil
    private store: preferences.Preferences | null = null
    private readonly STORE_NAME = 'app_preferences'

    private constructor() {}

    static getInstance(): PreferencesUtil {
        if (!PreferencesUtil.instance) {
            PreferencesUtil.instance = new PreferencesUtil()
        }
        return PreferencesUtil.instance
    }

    async init(context: Context): Promise<void> {
        try {
            this.store = await preferences.getPreferences(context, this.STORE_NAME)
        } catch (err) {
            console.error(`PreferencesUtil init failed: ${(err as Error).message}`)
        }
    }

    async put<T>(key: string, value: T): Promise<void> {
        if (!this.store) return
        try {
            const serialized = typeof value === 'object' ? JSON.stringify(value) : value
            await this.store.put(key, serialized as preferences.ValueType)
            await this.store.flush()
        } catch (err) {
            console.error(`PreferencesUtil put failed: ${(err as Error).message}`)
        }
    }

    async get<T>(key: string, defaultValue: T): Promise<T> {
        if (!this.store) return defaultValue
        try {
            const raw = await this.store.get(key, defaultValue)
            if (typeof defaultValue === 'object' && typeof raw === 'string') {
                return JSON.parse(raw) as T
            }
            return raw as T
        } catch (err) {
            console.error(`PreferencesUtil get failed: ${(err as Error).message}`)
            return defaultValue
        }
    }

    async remove(key: string): Promise<void> {
        if (!this.store) return
        try {
            await this.store.delete(key)
            await this.store.flush()
        } catch (err) {
            console.error(`PreferencesUtil remove failed: ${(err as Error).message}`)
        }
    }

    async clear(): Promise<void> {
        if (!this.store) return
        try {
            await this.store.clear()
            await this.store.flush()
        } catch (err) {
            console.error(`PreferencesUtil clear failed: ${(err as Error).message}`)
        }
    }

    async has(key: string): Promise<boolean> {
        if (!this.store) return false
        try {
            return await this.store.has(key)
        } catch (err) {
            console.error(`PreferencesUtil has failed: ${(err as Error).message}`)
            return false
        }
    }
}

export const prefUtil = PreferencesUtil.getInstance()
```

### 在 EntryAbility 中初始化

```typescript
// entryability/EntryAbility.ets
import { AbilityConstant, UIAbility, Want } from '@kit.AbilityKit'
import { window } from '@kit.ArkUI'
import { prefUtil } from '../utils/PreferencesUtil'

export default class EntryAbility extends UIAbility {
    async onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): Promise<void> {
        // 初始化 Preferences
        try {
            await prefUtil.init(this.context)
        } catch (err) {
            console.error(`Preferences 初始化失败: ${(err as Error).message}`)
        }
    }
}
```

---

## RelationalStore 关系型数据库

适用场景：结构化数据、复杂查询、数据量较大。

### 创建数据库和表

```typescript
import { relationalStore } from '@kit.ArkData'

let rdbStore: relationalStore.RdbStore | null = null

const STORE_CONFIG: relationalStore.StoreConfig = {
    name: 'MyDatabase.db',
    securityLevel: relationalStore.SecurityLevel.S1
}

const SQL_CREATE_TABLE = `
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        email TEXT,
        created_at INTEGER
    )
`

async function initRdb(context: Context): Promise<void> {
    try {
        rdbStore = await relationalStore.getRdbStore(context, STORE_CONFIG)
        await rdbStore.executeSql(SQL_CREATE_TABLE)
    } catch (err) {
        console.error(`initRdb failed: ${err.message}`)
    }
}
```

### 插入数据

```typescript
interface IUser {
    name: string
    age: number
    email: string
}

import { relationalStore } from '@kit.ArkData'
import { systemDateTime } from '@kit.BasicServicesKit'

async function insertUser(user: IUser): Promise<number> {
    if (!rdbStore) return -1

    const valueBucket: relationalStore.ValuesBucket = {
        name: user.name,
        age: user.age,
        email: user.email,
        created_at: systemDateTime.getTime()
    }

    try {
        const rowId = await rdbStore.insert('user', valueBucket)
        return rowId
    } catch (err) {
        console.error(`insertUser failed: ${(err as Error).message}`)
        return -1
    }
}
```

### 查询数据

```typescript
async function queryUsers(): Promise<IUser[]> {
    if (!rdbStore) return []

    const predicates = new relationalStore.RdbPredicates('user')
    predicates.equalTo('age', 25).orderByDesc('created_at')

    try {
        const resultSet = await rdbStore.querySql(predicates)
        const users: IUser[] = []

        while (resultSet.goToNextRow()) {
            users.push({
                name: resultSet.getString(resultSet.getColumnIndex('name')),
                age: resultSet.getLong(resultSet.getColumnIndex('age')),
                email: resultSet.getString(resultSet.getColumnIndex('email'))
            })
        }

        resultSet.close()
        return users
    } catch (err) {
        console.error(`queryUsers failed: ${(err as Error).message}`)
        return []
    }
}

// 原生 SQL 查询
async function queryBySql(sql: string): Promise<IUser[]> {
    if (!rdbStore) return []

    try {
        const resultSet = await rdbStore.querySql(sql)
        const users: IUser[] = []

        while (resultSet.goToNextRow()) {
            users.push({
                name: resultSet.getString(resultSet.getColumnIndex('name')),
                age: resultSet.getLong(resultSet.getColumnIndex('age')),
                email: resultSet.getString(resultSet.getColumnIndex('email'))
            })
        }

        resultSet.close()
        return users
    } catch (err) {
        console.error(`queryBySql failed: ${(err as Error).message}`)
        return []
    }
}
```

### 更新数据

```typescript
async function updateUser(id: number, user: Partial<IUser>): Promise<number> {
    if (!rdbStore) return 0

    const valueBucket: relationalStore.ValuesBucket = {}
    if (user.name) valueBucket.name = user.name
    if (user.age !== undefined) valueBucket.age = user.age
    if (user.email) valueBucket.email = user.email

    const predicates = new relationalStore.RdbPredicates('user')
    predicates.equalTo('id', id)

    try {
        const changedRows = await rdbStore.update(valueBucket, predicates)
        return changedRows
    } catch (err) {
        console.error(`updateUser failed: ${(err as Error).message}`)
        return 0
    }
}
```

### 删除数据

```typescript
async function deleteUser(id: number): Promise<number> {
    if (!rdbStore) return 0

    const predicates = new relationalStore.RdbPredicates('user')
    predicates.equalTo('id', id)

    try {
        const deletedRows = await rdbStore.delete(predicates)
        return deletedRows
    } catch (err) {
        console.error(`deleteUser failed: ${(err as Error).message}`)
        return 0
    }
}
```

### 查询条件构建

```typescript
const predicates = new relationalStore.RdbPredicates('user')

// 等于
predicates.equalTo('name', '张三')

// 不等于
predicates.notEqualTo('age', 25)

// 范围
predicates.between('age', 20, 30)

// 大于 / 小于
predicates.greaterThan('age', 18)
predicates.lessThan('age', 60)

// IN
predicates.in('id', [1, 2, 3])

// LIKE 模糊
predicates.like('name', '%张%')

// IS NULL / IS NOT NULL
predicates.isNull('email')
predicates.isNotNull('email')

// 排序
predicates.orderByAsc('age')
predicates.orderByDesc('created_at')

// 限制
predicates.limitAs(10)
predicates.offsetAs(0)
```

---

## 文件存储

### 应用私有目录

```typescript
import { fileIo } from '@kit.CoreFileKit'
import { common } from '@kit.AbilityKit'

// 获取应用私有目录
let context = getContext(this) as common.UIAbilityContext
let filesDir = context.filesDir           // /data/.../files/
let cacheDir = context.cacheDir           // /data/.../cache/
let tempDir = context.tempDir             // /data/.../temp/
let preferencesDir = context.preferencesDir

// 写入文件
async function writeTextFile(fileName: string, content: string): Promise<void> {
    const filePath = `${context.filesDir}/${fileName}`
    const file = await fileIo.open(filePath, fileIo.OpenMode.CREATE | fileIo.OpenMode.WRITE_ONLY)
    await fileIo.write(file.fd, content)
    await fileIo.close(file.fd)
}

// 读取文件
async function readTextFile(fileName: string): Promise<string> {
    const filePath = `${context.filesDir}/${fileName}`
    const file = await fileIo.open(filePath, fileIo.OpenMode.READ_ONLY)
    const stat = await fileIo.stat(filePath)
    const buffer = new ArrayBuffer(stat.size)
    await fileIo.read(file.fd, buffer)
    await fileIo.close(file.fd)
    return String.fromCharCode(...new Uint8Array(buffer))
}

// 删除文件
async function deleteFile(fileName: string): Promise<void> {
    const filePath = `${context.filesDir}/${fileName}`
    await fileIo.unlink(filePath)
}

// 检查文件是否存在
async function fileExists(fileName: string): Promise<boolean> {
    const filePath = `${context.filesDir}/${fileName}`
    try {
        await fileIo.access(filePath)
        return true
    } catch {
        return false
    }
}
```

---

## 最佳实践

1. **Preferences vs RelationalStore 选择**
   - 数据量 < 100KB、简单 KV → Preferences
   - 结构化数据、复杂查询 → RelationalStore

2. **敏感数据加密**
   - 不要明文存储密码、Token
   - 使用 `@ohos.security.cryptoFramework` 加密后再存储

3. **数据版本管理**
   - RelationalStore 表结构变更时，在 `onCreate` / `onUpgrade` 中处理迁移

4. **异步操作**
   - 所有存储操作都是异步的，必须使用 `await` 或回调

5. **初始化时机**
   - Preferences 在 `EntryAbility.onCreate` 中初始化
   - RelationalStore 在首次使用时按需初始化

6. **数据清理**
   - `cacheDir` 和 `tempDir` 可被系统清理，不要存重要数据
   - 定期清理过期缓存

7. **所有存储操作必须 try-catch**
   - Preferences 的 `get`、`put`、`delete`、`flush`、`has` 等方法均可能抛出异常
   - RelationalStore 的 `insert`、`update`、`delete`、`querySql` 等方法均可能抛出异常
   - 每个 await 调用都应包裹在 try-catch 中，防止单个操作失败导致整个应用崩溃

8. **时间计算使用 systemDateTime.getTime() 而非 Date.now() / new Date()**
   - 涉及时间戳、耗时、超时、排序等计算时，不使用 `Date.now()` / `new Date()`
   - 推荐使用 `@kit.BasicServicesKit` 中的 `systemDateTime.getTime()` 获取毫秒级时间戳
   - 示例：`import { systemDateTime } from '@kit.BasicServicesKit'; const timestamp = systemDateTime.getTime()`
