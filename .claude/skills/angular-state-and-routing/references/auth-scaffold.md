# 參考：認證預留骨架

**目前尚未有後端認證契約**。以下是預留接點，一律標 TODO、不做假實作。契約確定後三處一起補。

## 1. auth store 骨架

```ts
// src/app/core/auth.store.ts
import { Injectable, computed, signal } from '@angular/core'

@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly _token = signal<string | null>(null)

  readonly token = this._token.asReadonly()
  readonly isAuthenticated = computed(() => this._token() !== null)

  // TODO(未來 auth)：接後端登入端點，token 存放策略待定
  //   （記憶體 / sessionStorage / httpOnly cookie —— 依後端契約決定，不要自行假設）
  setToken(token: string | null): void {
    this._token.set(token)
  }

  clear(): void {
    this._token.set(null)
  }
}
```

## 2. 路由守衛骨架

```ts
// src/app/core/guards/auth.guard.ts
import type { CanActivateFn } from '@angular/router'

// TODO(未來 auth)：後端契約確定前一律放行，避免擋住開發。
// 契約確定後改為下方註解的實作（屆時才注入 AuthStore / Router，
// 現在先不注入，免得留下用不到的變數）：
//
//   export const authGuard: CanActivateFn = (_route, state) => {
//     const auth = inject(AuthStore)
//     const router = inject(Router)
//     if (auth.isAuthenticated()) return true
//     return router.createUrlTree(['/login'], { queryParams: { redirect: state.url } })
//   }
export const authGuard: CanActivateFn = () => true
```

> 回傳 `UrlTree` 而非 `false` + 手動 `navigate` —— 前者是 Angular 建議的導向寫法，能正確取消原本的導航。

## 3. 攔截器的 401 分支

已在 `angular-api-integration` 的 `references/http-client.md` 預留：

```ts
if (error.status === 401) {
  // TODO(未來 auth)：清除登入狀態並導回登入頁
}
```

## 待辦（契約確定後一起補）

- [ ] token 存放策略（記憶體 / sessionStorage / httpOnly cookie）—— **由後端契約決定**。
- [ ] auth 攔截器：夾帶 `Authorization` header，排在 error 攔截器**之前**。
- [ ] `authGuard` 改為真正檢查並導回登入頁。
- [ ] refresh token 流程（若後端有）。

**不要**在契約未定前自行設計 token 格式或 refresh 流程 —— 猜錯要全部重做。
