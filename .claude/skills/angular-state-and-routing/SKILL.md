---
name: Angular 狀態與路由
description: Angular 狀態管理與路由規範 —— 以 Signals + Service 持有狀態（不引 NgRx）、× 兩架構的落點（store 或 facade）、唯讀暴露與 computed 衍生、provideRouter 與 lazy loadComponent、CanActivateFn 函式式守衛，以及未來認證的預留骨架。建立或修改 store／facade、路由或 auth 接點時使用。
---

# Angular 狀態與路由

> 本 skill 即此主題的權威編碼依據；範例見 `references/`。基準：Angular 20+。

## 狀態管理：Signals + Service（兩案共通）

本工作區的 Angular 專案**不引 NgRx**（Store／Effects／SignalStore 皆不用），**兩種架構都一樣**。狀態一律是「service + signals」：

- 這與 Vue 模組的 Pinia setup store 是同一個心智模型（一包狀態 + 一包動作），跨框架看得懂。
- 少一層相依與樣板碼；signals 本身已具備細粒度反應性與 `computed` 衍生。
- 真的長到需要 Redux 那套的規模時再談 —— 屆時是一次明確的架構決策，不是預設。

### 鐵律（兩案皆適用）

- **對外只暴露唯讀**：內部 `private readonly _items = signal<Task[]>([])`，對外 `readonly items = this._items.asReadonly()`。元件只能透過方法改狀態，不能直接 `set()`。
- **衍生值用 `computed()`**，不要用 `effect()` 去寫另一個 signal（宣告式改命令式，會產生難查的連鎖更新）。
- **`effect()` 只用於副作用**（記 log、寫 localStorage、呼叫命令式 API），不用於同步狀態。
- 三態（`isLoading` / `error` / 資料）由持有者暴露，元件只讀。
- **元件不得直接碰資料存取層**。

### 落點：× 兩架構

「signals + service」的寫法兩案完全相同，**差別在這個 service 叫什麼、注入什麼、活多久**：

| | 精簡分層 | Clean |
| --- | --- | --- |
| 持有狀態的東西 | `features/task/task.store.ts`（`TaskStore`） | `features/task/presentation/task.facade.ts`（`TaskFacade`） |
| 它注入什麼 | **api service**（直接呼叫） | **UseCase**（不得直接注入 Repository） |
| 它持有什麼型別 | 領域型別 `Task`（`api/` 回傳的） | `TaskEntity`（Entity 有業務方法） |
| provider 範圍 | `providedIn: 'root'`（全域單例） | `@Injectable()` + Page／route `providers`（跟著畫面生滅） |
| 元件注入什麼 | store | facade |
| 衍生值 | `computed(() => tasks().filter(t => t.status !== 'done'))` | `computed(() => tasks().filter(t => t.canEdit()))`（判斷來自 Entity） |

> **生命週期差異別搞錯**：精簡分層的 store 是 `'root'` 單例，離開畫面狀態還在（要清就自己寫 `reset()`）。Clean 的 Facade 跟著 route providers 走，離開畫面就釋放 —— 想跨畫面共用才提升到 `'root'`，那是一次明確的決定。

## 路由

- 路由表放 `app.routes.ts`，於 `app.config.ts` 以 `provideRouter(routes, withComponentInputBinding())` 註冊。
- **一律 lazy load**：用 `loadComponent: () => import('...').then(m => m.XxxComponent)`，不要靜態 import 頁面元件。
- **命名路由參數綁進 `input()`**：有 `withComponentInputBinding()` 時，路由參數／query 會自動綁到同名的 `input()`，不必注入 `ActivatedRoute` 手動讀。
- 守衛一律用 **functional guard**（`CanActivateFn`），不用 class-based 的 `CanActivate` 介面。
- 導頁用 `Router.navigate(['/tasks', id])` 或樣板的 `routerLink`；路徑集中在路由表，不要散落在各元件寫死字串。

**路由規則兩案相同**，只有路由表的擺法不同：

| | 精簡分層 | Clean |
| --- | --- | --- |
| 路由表 | 集中在 `app.routes.ts` | 根路由 `app.routes.ts` 以 `loadChildren` 指向各 feature 的 `*.routes.ts` |
| feature 的 `providers` | 不需要（store 是 `'root'`） | **必要** —— Repository 介面綁實作那一行住這裡（見 `angular-clean-architecture`） |

## 認證預留

目前**尚未有後端認證**，先預留接點，不做假實作：

- `core/guards/auth.guard.ts` —— `CanActivateFn` 骨架，目前一律放行並標 TODO。
- `core/auth.store.ts` —— 持有 `isAuthenticated` signal 的骨架。
- 攔截器的 401 分支已預留（見 `angular-api-integration`）。

後端 auth 契約確定後，這三處一起補實作；**不要**在契約未定前自行設計 token 格式。

## References

- [signal-store.md](references/signal-store.md) — Signals + Service 完整範例（三態、唯讀暴露、computed）。以精簡分層的 store 為例；Clean 的 Facade 寫法相同，只是注入 UseCase、持有 Entity，見 `angular-clean-architecture` 的 `references/structure.md`。
- [router.md](references/router.md) — 路由表、lazy load、`withComponentInputBinding()` 與守衛。
- [auth-scaffold.md](references/auth-scaffold.md) — 認證預留骨架與待辦。
