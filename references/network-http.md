# HTTP 网络请求

## 目录

1. [基础请求](#基础请求)
2. [封装 HttpUtil](#封装-httputil)
3. [拦截器模式](#拦截器模式)
4. [上传下载](#上传下载)
5. [WebSocket](#websocket)

---

## 基础请求

> **提示**：回调风格需要手动处理错误，推荐使用 Promise + try-catch 方式（见下方 Promise 封装）

```typescript
import { http } from '@kit.NetworkKit'

// GET
let request = http.createHttp()
request.request(
  'https://api.example.com/users',
  {
    method: http.RequestMethod.GET,
    header: { 'Content-Type': 'application/json' },
    extraData: null
  },
  (err, data) => {
    if (!err) {
      if (data.responseCode === 200) {
        let result = JSON.parse(data.result as string) as IResponse
      }
    } else {
      // 错误处理：打印或上报错误
      console.error(`请求失败: ${err.message}`)
    }
  }
)

// POST
let request = http.createHttp()
request.request(
  'https://api.example.com/login',
  {
    method: http.RequestMethod.POST,
    header: { 'Content-Type': 'application/json' },
    extraData: JSON.stringify({ username: 'test', password: '123456' })
  },
  (err, data) => {
    if (!err && data.responseCode === 200) {
      let result = JSON.parse(data.result as string)
    } else {
      // 错误处理：打印或上报错误
      console.error(`请求失败: ${err.message}`)
    }
  }
)

// 记得销毁
request.destroy()
```

### Promise 封装基础版

```typescript
import { http } from '@kit.NetworkKit'

function request(url: string, options?: HttpRequestOptions): Promise<string> {
  return new Promise((resolve, reject) => {
    const httpRequest = http.createHttp()
    const defaultOptions: HttpRequestOptions = {
      method: http.RequestMethod.GET,
      header: { 'Content-Type': 'application/json' },
      readTimeout: 15000,
      connectTimeout: 15000,
      ...options
    }
    httpRequest.request(url, defaultOptions, (err, data) => {
      httpRequest.destroy()
      if (err) {
        reject(err)
        return
      }
      if (data.responseCode >= 200 && data.responseCode < 300) {
        resolve(data.result as string)
      } else {
        reject(new Error(`HTTP ${data.responseCode}: ${data.result}`))
      }
    })
  })
}
```

---

## 封装 HttpUtil

### 完整封装（推荐）

```typescript
// utils/HttpUtil.ets
import { http } from '@kit.NetworkKit'
import { AppStorage } from '@kit.ArkUI'

interface IHttpConfig {
  baseUrl: string
  timeout: number
}

interface IRequestOptions {
  url: string
  method?: http.RequestMethod
  data?: Object | string
  header?: Record<string, string>
  extraHeader?: Record<string, string>
}

interface IApiResponse<T> {
  code: number
  message: string
  data: T
}

class HttpUtil {
  private static instance: HttpUtil
  private config: IHttpConfig = {
    baseUrl: 'https://api.example.com',
    timeout: 15000
  }

  private constructor() {}

  static getInstance(): HttpUtil {
    if (!HttpUtil.instance) {
      HttpUtil.instance = new HttpUtil()
    }
    return HttpUtil.instance
  }

  setBaseUrl(baseUrl: string): void {
    this.config.baseUrl = baseUrl
  }

  // 获取 Token
  private getToken(): string {
    return AppStorage.get<string>('token') || ''
  }

  // 构建请求头
  private buildHeader(extra?: Record<string, string>): Record<string, string> {
    const header: Record<string, string> = {
      'Content-Type': 'application/json',
      ...extra
    }
    const token = this.getToken()
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }
    return header
  }

  // 核心请求方法
  private async request<T>(options: IRequestOptions): Promise<T> {
    return new Promise((resolve, reject) => {
      const httpRequest = http.createHttp()
      const fullUrl = options.url.startsWith('http')
        ? options.url
        : `${this.config.baseUrl}${options.url}`

      const body = typeof options.data === 'object'
        ? JSON.stringify(options.data)
        : (options.data || '')

      httpRequest.request(fullUrl, {
        method: options.method || http.RequestMethod.GET,
        header: this.buildHeader(options.extraHeader),
        extraData: body,
        readTimeout: this.config.timeout,
        connectTimeout: this.config.timeout
      }, (err, data) => {
        httpRequest.destroy()
        if (err) {
          reject(new Error(`Network Error: ${err.message}`))
          return
        }
        try {
          const result: IApiResponse<T> = JSON.parse(data.result as string) as IApiResponse<T>
          if (result.code === 0 || result.code === 200) {
            resolve(result.data)
          } else {
            reject(new Error(result.message))
          }
        } catch (e) {
          reject(new Error(`Parse Error: ${data.result}`))
        }
      })
    })
  }

  // GET
  async get<T>(url: string, params?: Record<string, string>): Promise<T> {
    let fullUrl = url
    if (params) {
      const query = Object.entries(params)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
        .join('&')
      fullUrl = `${url}?${query}`
    }
    return this.request<T>({ url: fullUrl, method: http.RequestMethod.GET })
  }

  // POST
  async post<T>(url: string, data?: Object): Promise<T> {
    return this.request<T>({ url, method: http.RequestMethod.POST, data })
  }

  // PUT
  async put<T>(url: string, data?: Object): Promise<T> {
    return this.request<T>({ url, method: http.RequestMethod.PUT, data })
  }

  // DELETE
  async delete<T>(url: string): Promise<T> {
    return this.request<T>({ url, method: http.RequestMethod.DELETE })
  }
}

// 导出单例
export const httpUtil = HttpUtil.getInstance()
```

### 使用示例

```typescript
import { httpUtil } from '../utils/HttpUtil'

interface IUserData {
  id: number
  name: string
  avatar: string
}

@Entry
@Component
struct UserPage {
  @State user: IUserData | null = null
  @State loading: boolean = false
  @State errorMsg: string = ''

  aboutToAppear() {
    this.loadUser()
  }

  async loadUser() {
    this.loading = true
    this.errorMsg = ''
    try {
      this.user = await httpUtil.get<IUserData>('/user/profile')
    } catch (e) {
      this.errorMsg = e instanceof Error ? e.message : '请求失败'
    } finally {
      this.loading = false
    }
  }

  build() {
    Column() {
      if (this.loading) {
        LoadingProgress().width(40).height(40)
      } else if (this.errorMsg) {
        Text(this.errorMsg).fontColor('#FF0000')
      } else if (this.user) {
        Text(this.user.name).fontSize(20)
        Image(this.user.avatar).width(60).height(60).borderRadius(30)
      }
    }
  }
}
```

---

## 拦截器模式

```typescript
// 简易请求拦截器
class HttpInterceptor {
  private static requestInterceptors: Array<(config: IRequestOptions) => IRequestOptions> = []
  private static responseInterceptors: Array<(response: string) => string> = []

  static addRequestInterceptor(fn: (config: IRequestOptions) => IRequestOptions): void {
    HttpInterceptor.requestInterceptors.push(fn)
  }

  static addResponseInterceptor(fn: (response: string) => string): void {
    HttpInterceptor.responseInterceptors.push(fn)
  }

  static async runRequestInterceptors(config: IRequestOptions): Promise<IRequestOptions> {
    let result = config
    for (const interceptor of HttpInterceptor.requestInterceptors) {
      result = interceptor(result)
    }
    return result
  }

  static async runResponseInterceptors(response: string): Promise<string> {
    let result = response
    for (const interceptor of HttpInterceptor.responseInterceptors) {
      result = interceptor(result)
    }
    return result
  }
}

// 使用：添加 Token 拦截器
HttpInterceptor.addRequestInterceptor((config) => {
  const token = AppStorage.get<string>('token')
  if (token) {
    config.extraHeader = { ...config.extraHeader, 'Authorization': `Bearer ${token}` }
  }
  return config
})

// 使用：401 自动跳转登录
HttpInterceptor.addResponseInterceptor((response) => {
  try {
    const result = JSON.parse(response)
    if (result.code === 401) {
      router.replaceUrl({ url: 'pages/Login' })
    }
  } catch (_) { }
  return response
})
```

---

## 上传下载

### 文件上传

```typescript
import { http } from '@kit.NetworkKit'
import { picker } from '@kit.CoreFileKit'

async function uploadFile(filePath: string) {
  const httpRequest = http.createHttp()
  try {
    const response = await new Promise<string>((resolve, reject) => {
      httpRequest.request(
        'https://api.example.com/upload',
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'multipart/form-data'
          },
          extraData: {
            file: filePath,
            type: 'jpg'
          },
          multiFormDataList: [
            { name: 'file', filePath: filePath, filename: 'photo.jpg' }
          ]
        },
        (err, data) => {
          if (err) { reject(err); return }
          resolve(data.result as string)
        }
      )
    })
    return JSON.parse(response)
  } catch (err) {
    // 错误处理：打印或上报错误
    console.error(`上传失败: ${err instanceof Error ? err.message : '未知错误'}`)
    throw err
  } finally {
    httpRequest.destroy()
  }
}
```

### 文件下载

```typescript
import { http } from '@kit.NetworkKit'
import { fileIo } from '@kit.CoreFileKit'

async function downloadFile(url: string, savePath: string): Promise<void> {
  const httpRequest = http.createHttp()
  try {
    await new Promise<void>((resolve, reject) => {
      httpRequest.downloadFile(
        url,
        { filePath: savePath },
        (err, data) => {
          if (err) { reject(err); return }
          resolve()
        }
      )
    })
  } catch (err) {
    // 错误处理：打印或上报错误
    console.error(`下载失败: ${err instanceof Error ? err.message : '未知错误'}`)
    throw err
  } finally {
    httpRequest.destroy()
  }
}
```

---

## WebSocket

```typescript
import { webSocket } from '@kit.NetworkKit'

const ws = webSocket.createWebSocket()

// 连接需要 catch
ws.connect('wss://api.example.com/ws').catch(err => {
  console.error(`WebSocket 连接失败: ${err.message}`)
})

ws.on('open', () => {
  console.info('WebSocket connected')
  ws.send('Hello Server').catch(err => {
    console.error(`WebSocket 发送失败: ${err.message}`)
  })
})

ws.on('message', (err, data) => {
  if (!err) {
    console.info(`Received: ${data}`)
  }
})

ws.on('close', (err, code, reason) => {
  console.info(`WebSocket closed: ${code} ${reason}`)
})

ws.on('error', (err) => {
  console.error(`WebSocket error: ${err.message}`)
})

// 关闭需要 catch
ws.close({ code: 1000, reason: 'Normal closure' }).catch(err => {
  console.error(`WebSocket 关闭失败: ${err.message}`)
})
```

---

## 网络权限

在 `module.json5` 中声明权限：

```json
{
  "module": {
    "requestPermissions": [
      { "name": "ohos.permission.INTERNET" }
    ]
  }
}
```
