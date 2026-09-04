---
name: Angular 精簡分層架構
description: Angular 前端的精簡分層（feature store）架構規範 —— core／api／features（store + component）／shared 四個目錄的職責、component → store → api → core 的單向相依、目錄結構與各層落點。當專案架構選定為精簡分層時，撰寫或審查程式碼前先遵循；Clean Architecture 請改用 angular-clean-architecture。
---

# Angular 精簡分層架構（feature store）

> 本 skill 是**架構**的權威依據：目錄、各層職責、相依方向與落點。
> 跨架構的編碼鐵律（命名、standalone、`inject()`、Signals、TS）見 `angular-coding-standards`；SPA 進入點與組合根見其 `references/app-bootstrap.md`。
> **基準：Angular 20+。**

## 這個架構是什麼

資料由下往上流動，四層各一個目錄：

```
core/  →  api/  →  features/*/*.store.ts  →  features/*/*.component.ts
基礎設施   資料存取        狀態                      表現
```

辨識特徵：**feature store 直接呼叫 `api/`**。沒有 Entity、UseCase、Repository 介面、DTO、Mapper —— `api/` 回傳的型別就是元件用的型別。一個 feature 大約 3–4 個檔案。

**適合**：CRUD 為主、後端契約穩定且命名對盤、領域邏輯單純（欄位搬運多於業務規則）、團隊規模小、要快。

**不適合**：領域規則多且需獨立測試、後端格式常變或命名不對盤（蛇形 vs 駝峰）、要抽換資料來源 —— 那些是 `angular-clean-architecture` 的場景。

## 各層職責

| 層 | 目錄 | 職責 | 可相依 |
| --- | --- | --- | --- |
| 基礎設施 | `core/` | 攔截器、guards、環境設定、`NotifyService` token、全域單例 | 無（最底層） |
| 資料存取 | `api/` | 端點定義，包 `HttpClient`，回傳 `Observable<T>` | `core/` |
| 狀態 | `features/*/*.store.ts` | 以 signal 持有狀態，呼叫 `api/`，對外暴露唯讀 signal 與動作 | `core/`、`api/` |
| 表現 | `features/*/*.component.ts`、`shared/` | 渲染與使用者互動，注入 store service | 以上皆可 |

## 鐵律

- **元件不得直接注入 `api/` 的 service**，一律經 feature store。
- **store 是 feature 對元件的唯一入口**（它同時扮演 Facade）：對元件隱藏 API 細節，只暴露唯讀 signal 與動作方法。
- **`core/` 與 `api/` 不得 import 任何 UI 元件庫**（要提示就注入 `NotifyService`）。
- **`shared/` 只放無業務邏輯的展示元件 / pipe / directive**，不得相依任何 feature。
- **store 一律 `providedIn: 'root'`**，不需要在組合根或 route providers 登記。
- **三態（`isLoading` / `error` / 資料）由 store 持有並暴露**，元件只讀。

## 業務邏輯放哪

這個架構**沒有 domain 層**，所以要講清楚落點，否則邏輯會散掉：

| 邏輯種類 | 落點 |
| --- | --- |
| 表單驗證規則 | `schemas/*.schema.ts`（Zod；見 `angular-forms-and-i18n`） |
| 衍生／篩選／彙總 | store 的 `computed()` |
| 流程編排（存檔後重載、錯誤轉換） | store 的動作方法 |
| 單一實體的判斷（如「停用中不可編輯」） | `schemas/` 旁的純函式，如 `canEdit(task: Task): boolean` |

> **純函式，不要寫成 class 方法** —— 這個架構的型別是 `interface`／Zod 推導出來的資料形狀，不是有行為的物件。想要 `task.canEdit()` 那種寫法，代表你要的是 Clean 的 Entity，該考慮換架構了。

## 目錄結構（示意）

> 體現分層的**代表性結構**，非既有檔案清單；實作時依需求新增。

```
（前端專案根目錄）
├── angular.json
├── tsconfig.json
├── package.json
└── src/
    ├── main.ts                    # 進入點：bootstrapApplication
    ├── styles.scss                # UI 元件庫主題（做法見 ui-* skill）+ 全域樣式
    ├── environments/              # 多環境設定（見 angular-coding-standards 的 env-config.md）
    │   ├── environment.ts
    │   └── environment.prod.ts
    ├── assets/
    │   └── i18n/                  # Transloco 語言檔（zh-TW.json、en.json）
    └── app/
        ├── app.config.ts          # 組合根：集中註冊所有 provider
        ├── app.routes.ts          # 路由表（lazy loadComponent）
        ├── app.component.ts       # 根元件
        ├── core/                  # ── 基礎設施層
        │   ├── interceptors/
        │   │   └── error.interceptor.ts
        │   ├── guards/
        │   │   └── auth.guard.ts
        │   ├── notify.service.ts  # abstract token；實作由 ui-* 提供
        │   └── config/
        │       └── env.ts
        ├── api/                   # ── 資料存取層：回傳 Observable
        │   └── task.api.ts
        ├── schemas/               # 跨層共用 schema、型別與純函式規則
        │   └── task.schema.ts
        ├── features/              # ── 功能：store（狀態）+ 元件（表現）
        │   └── task/
        │       ├── task.store.ts
        │       ├── task-list.component.ts
        │       └── task-form.component.ts
        └── shared/                # ── 共用展示元件 / pipe / directive
            └── ...
```

## 其他 skill 在本架構下的落點

| 主題 | skill | 本架構落點 |
| --- | --- | --- |
| API 串接 | `angular-api-integration` | `api/*.api.ts` |
| 狀態 | `angular-state-and-routing` | `features/*/*.store.ts` |
| 表單驗證規則 | `angular-forms-and-i18n` | `schemas/*.schema.ts` |
| 測試 | `angular-testing` | api service（`HttpTestingController`）、store（假 api）必測 |

## References

- [structure.md](references/structure.md) — 各層完整範例：`api/`、`schemas/`、store、元件的相依串接。
