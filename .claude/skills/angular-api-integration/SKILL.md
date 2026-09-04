---
name: Angular API 串接
description: Angular 串接後端 API 的規範 —— 以 HttpClient + functional interceptors 建立資料存取層、× 兩架構的落點（api service 或 DAO）、ApiError 正規化、錯誤分層處理、NotifyService 轉接，以及 Observable 與 signal 的橋接。建立或修改 api service／DAO、攔截器或處理 API 錯誤時使用。
---

# Angular API 串接

> 本 skill 即此主題的權威編碼依據；範例見 `references/`。基準：Angular 20+。

## 核心規則（兩案共通）

- HTTP 一律用 `HttpClient`（在 `app.config.ts` 以 `provideHttpClient(withInterceptors([...]))` 註冊），**不用** `fetch` 或 axios。
- **資料存取層只做一件事**：定義端點、回傳 `Observable`。不碰狀態、不碰 UI、不做提示。
- **元件不得直接注入資料存取層**，一律經該架構指定的中介（store／facade）。
- 錯誤先在攔截器**正規化**成一致的 `ApiError`（保留 `code`，便於 i18n 在地化）。
- 攔截器一律用 **functional interceptor**（`HttpInterceptorFn`），不用 class-based 的 `HTTP_INTERCEPTORS`。
- 攔截器**兩案都住在 `core/interceptors/`**，寫法完全相同。

## 落點：× 兩架構

「怎麼包 `HttpClient`」兩案相同，**差別在包出來的東西住哪、回傳什麼**：

| | 精簡分層（`angular-feature-store-architecture`） | Clean（`angular-clean-architecture`） |
| --- | --- | --- |
| 端點定義檔 | `api/task.api.ts`（`TaskApiService`） | `features/task/data/daos/task-api.dao.ts`（`TaskApiDao`） |
| 回傳型別 | **領域型別** `Observable<Task>` | **DTO** `Observable<TaskDTO>`，由 Repository 實作轉成 Entity |
| 格式轉換（`user_name` → `name`） | 沒有專責落點；契約不對盤就在此就地轉，或前端跟著後端命名 | **一律 Mapper**，DAO 不轉 |
| provider | `providedIn: 'root'` | `@Injectable()`，跟著 feature 的 route／page providers |
| 誰呼叫它 | feature store | Repository 實作（**只有它**） |
| 攔截器 | `core/interceptors/` | `core/interceptors/`（相同） |
| `ApiError` 型別 | `core/` | `core/`（相同） |

**先確認專案用哪一套**（見 `angular-coding-standards` 第 2 節），再決定寫哪一種。**不要在 Clean 專案裡建 `api/` 目錄**，也不要在精簡分層專案裡憑空生出 DTO 與 Mapper。

## Observable 與 signal 的分工

- **HTTP 這類一次性非同步仍走 Observable** —— `HttpClient` 回傳 Observable，這是正確的邊界。
- **狀態一律是 signal** —— 在 store／facade 裡訂閱 Observable、把結果 `set()` 進 signal。
- 需要把 Observable 直接當 signal 讀時，用 `@angular/core/rxjs-interop` 的 `toSignal()`。
- **不要**把 `HttpClient` 的 Observable 存進 signal 再到樣板用 `async` pipe —— 那是兩套非同步機制疊在一起。

## 錯誤處理分層（重點）

| 層 | 負責 | 作法 |
| --- | --- | --- |
| 元件層 | 預期內錯誤（驗證失敗、找不到資源） | 讀 store／facade 的 `error` signal → 就地顯示（用哪個元件見 `ui-*` skill） |
| 攔截器層 | 系統性錯誤（網路 / 逾時 / 5xx / 未來 401） | 注入 `NotifyService` 全域提示 + 副作用（401 導回登入） |
| 全域 | 未捕捉的錯誤 | `ErrorHandler` 自訂實作記錄（未來接監控） |

**不重複顯示**：攔截器只對系統性錯誤全域提示；業務錯誤（帶 `ApiError` 的 4xx）交給元件顯示。

**這張表兩案相同**，只有「誰持有 `error` signal」不同：精簡分層是 store，Clean 是 Facade。Clean 另有一層 —— `ApiError` 到「給人看的訊息」的轉換在 **Facade**，不要洩漏到 Page。

**底層不得相依 UI 元件庫**（`core/`、`api/`、`data/`、`domain/`）：攔截器要提示時注入 `NotifyService`（abstract class 當 token，宣告在 `core/`），實作由專案的 `ui-*` skill 提供並在 `app.config.ts` 綁定 —— 換元件庫時攔截器不用動。

## References

- [http-client.md](references/http-client.md) — `provideHttpClient`、`ApiError` 型別、錯誤攔截器與 `NotifyService` token。
- [api-service.md](references/api-service.md) — 端點寫法與型別（以精簡分層的 `api/` 為例；Clean 的 DAO 寫法相同，只是回傳 DTO，見 `angular-clean-architecture` 的 `references/structure.md`）。
- [error-handling.md](references/error-handling.md) — 分層策略、跳過全域提示、全域 `ErrorHandler`。
