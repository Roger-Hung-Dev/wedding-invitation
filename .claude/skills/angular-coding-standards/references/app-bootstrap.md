# 參考：SPA 進入點與組合根

> 本檔內容**兩種架構共用**（精簡分層／Clean）。目錄結構與各層職責依架構而定，見專案配的架構 skill。

## 應用程式架構（SPA）

- **單頁應用（SPA）**：瀏覽器只載入一個 `index.html`，後續畫面切換由 **Angular Router** 在前端完成，不重新整理整頁。
- **前後端分離**：前端只透過 REST JSON API 與後端溝通，不共享伺服器渲染。
- **進入點**：`src/main.ts` 以 `bootstrapApplication(AppComponent, appConfig)` 啟動，**沒有 NgModule**。
- **組合根**：`src/app/app.config.ts` 是唯一集中註冊 provider 的地方（router、http、i18n、UI 轉接實作）。
- **UI 元件庫**：**可插拔**，由專案配的 `ui-*` skill 決定。引入方式、主題與 `app.config.ts` 要註冊什麼，一律見該 skill；本檔不預設任何元件庫。
- **多國語系**：以 Transloco 管理應用文案，於 `app.config.ts` 註冊。

```ts
// src/main.ts
import { bootstrapApplication } from '@angular/platform-browser'
import { AppComponent } from './app/app.component'
import { appConfig } from './app/app.config'

bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err))
```

```ts
// src/app/app.config.ts —— 組合根
import { ApplicationConfig, provideZonelessChangeDetection } from '@angular/core'
import { provideRouter, withComponentInputBinding } from '@angular/router'
import { provideHttpClient, withInterceptors } from '@angular/common/http'
import { routes } from './app.routes'
import { errorInterceptor } from './core/interceptors/error.interceptor'
import { NotifyService } from './core/notify.service'
// NotifyService 的實作由專案配的 ui-* skill 提供（見該 skill），本檔不預設任何元件庫
import { UiNotifyService } from './shared/ui-notify.service'

export const appConfig: ApplicationConfig = {
  providers: [
    provideZonelessChangeDetection(),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([errorInterceptor])),
    // UI 元件庫轉接：換元件庫時只換這一行綁的實作，攔截器不動
    { provide: NotifyService, useClass: UiNotifyService },
    // 元件庫本身要註冊什麼（動畫、locale、paginator 文案…）也一律在此，見 ui-* skill
  ],
}
```

> `provideZonelessChangeDetection()` 需搭配全面使用 signals 才安全（本規範的狀態一律用 signal，符合條件）。若專案仍有依賴 zone.js 的第三方套件，改用預設的 zone 模式並確保元件都是 `OnPush`。
>
> `withComponentInputBinding()` 讓路由參數自動綁進元件的 `input()`，省掉手動讀 `ActivatedRoute`。

## 組合根與架構的關係

`app.config.ts` 註冊的是**全域**相依（router、http、攔截器、`NotifyService` 實作）。**feature 內部的相依綁定不放這裡**：

- **精簡分層**：store 與 api service 都是 `providedIn: 'root'`，不需要在組合根登記。
- **Clean**：Repository 介面對實作的綁定（`{ provide: TaskRepository, useClass: TaskRepositoryImpl }`）放在該 feature 的 route `providers`，不放組合根 —— 否則每個 feature 的相依都堆到同一個檔案，lazy load 也失去意義。

詳見各架構 skill。

## 檔名後綴

檔名後綴（`.component.ts` / `.service.ts` / `.store.ts` / `.api.ts` / `.facade.ts` / `.entity.ts` / `.dao.ts` / `.mapper.ts` …）是刻意保留的：Angular 專案靠它一眼分辨角色，比單看檔名可靠。各架構實際會用到哪些後綴，見對應的架構 skill。
