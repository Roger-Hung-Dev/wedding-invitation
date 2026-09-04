# 參考：HttpClient 設定、ApiError 與錯誤攔截器

## ApiError 型別

```ts
// src/app/core/types/api.ts
export interface ApiError {
  code: string
  message: string
}
```

## NotifyService（UI 元件庫的轉接 token）

`core/` 不得 import 任何 UI 元件庫，所以這裡只宣告**介面**，實作由專案的 `ui-*` skill 提供。用 abstract class 而非 `InjectionToken`：它同時是型別又是 token，注入端不必寫泛型。

```ts
// src/app/core/notify.service.ts
export abstract class NotifyService {
  abstract error(message: string): void
  abstract success(message: string): void
}
```

於 `app.config.ts` 綁定實作（見 `angular-coding-standards` 的 `references/app-bootstrap.md`）：

```ts
{ provide: NotifyService, useClass: MaterialNotifyService }  // 實作見 ui-* skill
```

## 錯誤攔截器（functional）

```ts
// src/app/core/interceptors/error.interceptor.ts
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http'
import { inject } from '@angular/core'
import { catchError, throwError } from 'rxjs'
import { NotifyService } from '../notify.service'
import type { ApiError } from '../types/api'

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  // functional interceptor 可以直接 inject —— 它跑在注入脈絡中
  const notify = inject(NotifyService)

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        // TODO(未來 auth)：清除登入狀態並導回登入頁
      } else if (error.status === 0 || error.status >= 500) {
        // status 0 = 網路中斷 / CORS 失敗 / 逾時
        notify.error('連線異常或系統忙碌，請稍後再試。')
      }

      const apiError: ApiError = {
        code: error.error?.code ?? 'UNKNOWN_ERROR',
        message: error.error?.message ?? '發生非預期的錯誤，請稍後再試。',
      }
      return throwError(() => apiError)
    }),
  )
}
```

## 註冊

```ts
// src/app/app.config.ts（節錄）
provideHttpClient(withInterceptors([errorInterceptor]))
```

> 攔截器的執行順序就是陣列順序。之後加 auth 攔截器時，**auth 要排在 error 之前**（先夾帶 token，再由 error 處理回應）。

## 基底 URL

```ts
// src/app/api/task.api.ts（節錄）
private readonly baseUrl = `${env.apiBaseUrl}/tasks`
```

各 api service 自行組 URL（`env` 見 `angular-coding-standards` 的 `references/env-config.md`）。若之後端點變多，再抽一個 `withBaseUrl` 攔截器統一加前綴，不要在每支 service 硬拼絕對網址。

> 後端回應信封格式（flat `{ code, message }` vs `{ rtnCode, message, validateErrors, data }`）尚待確認，據以調整此攔截器的 `error.error?.*` 取值。
