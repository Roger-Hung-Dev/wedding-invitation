# 參考：全域錯誤處理

錯誤分層處理，避免重複顯示：

| 層 | 負責 | 作法 |
| --- | --- | --- |
| 元件層 | 預期內錯誤（驗證失敗、找不到資源） | 讀 store 的 `error` signal → 就地顯示（用哪個元件見 `ui-*` skill） |
| 攔截器層 | 系統性錯誤（網路 / 逾時 / 5xx / 未來 401） | 注入 `NotifyService` 全域提示 + 副作用（401 導回登入） |
| 全域 | 未捕捉的錯誤（含樣板與生命週期） | 自訂 `ErrorHandler` 記錄（未來接監控） |

- **不重複顯示**：攔截器只對「系統性錯誤」全域提示（見 [http-client.md](http-client.md)）；業務錯誤（帶 `ApiError` 的 4xx）交給元件顯示。
- **錯誤怎麼「長在畫面上」是 UI 元件庫的事**：本檔只定分層與職責；用哪個元件顯示、命令式提示怎麼叫，見專案選定的 `ui-*` skill。

## 跳過全域提示

某次請求想自己處理錯誤、不要攔截器插手時，用 `HttpContext` 傳旗標（**不要**用 header —— 那會真的送到後端）：

```ts
// src/app/core/http-context.ts
import { HttpContextToken } from '@angular/common/http'

export const SKIP_GLOBAL_ERROR = new HttpContextToken<boolean>(() => false)
```

```ts
// 呼叫端
this.http.get<Task>(url, { context: new HttpContext().set(SKIP_GLOBAL_ERROR, true) })
```

```ts
// 攔截器內
if (!req.context.get(SKIP_GLOBAL_ERROR) && (error.status === 0 || error.status >= 500)) {
  notify.error('連線異常或系統忙碌，請稍後再試。')
}
```

## 全域 ErrorHandler

```ts
// src/app/core/global-error-handler.ts
import { ErrorHandler, Injectable } from '@angular/core'

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  handleError(error: unknown): void {
    console.error('[Angular error]', error) // 未來改接監控服務
  }
}
```

```ts
// src/app/app.config.ts（節錄）
{ provide: ErrorHandler, useClass: GlobalErrorHandler }
```

> `ErrorHandler` 接的是**未捕捉**的錯誤。已被攔截器 `catchError` 轉成 `ApiError` 並在 store 裡處理掉的，不會走到這裡 —— 這是預期行為，不要為了「集中」而把 HTTP 錯誤也丟給它。
