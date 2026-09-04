---
name: Angular 測試
description: Angular 測試規範 —— Jest + TestBed 的分層測試優先序、× 兩架構的測試對象（store／facade、Entity／Mapper）、MVP 範圍界線、以 mock provider 測狀態層、以 HttpTestingController 測 api service／DAO、signal 斷言與測試替身寫法。撰寫或規劃前端測試時使用。
---

# Angular 測試

> 本 skill 即此主題的權威編碼依據；範例見 `references/`。基準：Angular 20+。

## 工具與範圍

- **工具**：Jest（單元 / 元件測試）+ `TestBed` + jsdom 環境。**不用 Karma + Jasmine**（已進入 deprecation，且需要真實瀏覽器、慢）。
- 測試優先序依分層而定，**兩種架構的層不同**，見下表。

## 測試對象：× 兩架構

| 測什麼 | 精簡分層 | Clean | 怎麼測 |
| --- | --- | --- | --- |
| 業務規則 | `schemas/` 的純函式（如 `canEdit()`）**必測** | **Entity 必測**（`canEdit()`／`complete()`／`validate()`） | 純函式／純 class，**不進 `TestBed`**，直接 `new` 了就斷言 |
| 格式轉換 | （無此層） | **Mapper 必測**（DTO ↔ Entity 雙向、狀態碼對照、邊界值） | 純函式，不進 `TestBed` |
| 流程編排 | store 的動作方法 | **UseCase 必測**（驗證失敗會 `throwError`、多 Repository 協調） | 假 Repository（`{ provide: TaskRepository, useValue: {...} }`） |
| 狀態流轉 | **store 必測** | **Facade 必測** | 精簡分層用假 api service；Clean 用假 UseCase |
| HTTP | **api service 必測** | **DAO 必測** | `HttpTestingController` |
| 資料層協調 | （無此層） | Repository 實作 **選測** | 假 DAO；只驗有沒有正確串 Mapper |
| 互動型元件 | **選測** | **選測** | 精簡分層用假 store；Clean 用假 facade |
| 純展示元件、UI 元件庫本身 | **不測** | **不測** | — |

> **Clean 的測試紅利就在前兩列**：Entity 與 Mapper 零框架相依，不必進 `TestBed`、不必 mock 任何東西，是整個專案最快最穩的測試。做了 Clean 卻沒測它們，等於付了架構的成本沒領好處。

## 測試替身

- **api service／DAO** 用 `HttpTestingController` 測，**不打真實網路**；每個測試結尾 `httpMock.verify()` 確認沒有漏掉的請求。
- **store** 用假的 api service（`provide: TaskApiService, useValue: {...}`）測狀態流轉，不碰 HTTP。
- **Facade** 用假的 UseCase（`provide: SaveTaskUseCase, useValue: { execute: jest.fn() }`）測狀態流轉，不碰 Repository、不碰 HTTP。
- **UseCase** 用假的 Repository（`provide: TaskRepository, useValue: {...}`）—— Repository 是 abstract class，直接拿來當 token 用。
- **元件** 用假的 store／facade 測互動，不碰資料存取層。
- **Entity 與 Mapper 不需要替身** —— 它們沒有相依，直接測。
- `NotifyService` 是 UI 元件庫的轉接層，測試中一律用假實作（`useValue: { error: jest.fn(), success: jest.fn() }`）。

## signal 斷言

signal 是同步讀取的，直接呼叫即可斷言，不需要 `fakeAsync` / `tick()`：

```ts
// 精簡分層
expect(store.tasks()).toHaveLength(1)
expect(store.isLoading()).toBe(false)

// Clean —— 一模一樣，只是換成 facade
expect(facade.tasks()).toHaveLength(1)
expect(facade.isLoading()).toBe(false)
```

元件樣板要看到更新，才需要 `fixture.detectChanges()`。

## 範圍界線（MVP）

- **覆蓋率**：MVP 階段**先不設覆蓋率門檻**，避免為湊數字寫低價值測試；待核心穩定後再視需要加入。
- **不測**：Angular 框架本身、UI 元件庫本身、純轉發的 getter。
- **不寫 e2e**：MVP 階段先不導入 Playwright / Cypress；瀏覽器層的驗證由前端代理用 `common-user-browser` 實測（見 agent 的「瀏覽器自我驗證」）。

## References

- [testing-strategy.md](references/testing-strategy.md) — 分層優先序表與掛載注意事項。
- [test-examples.md](references/test-examples.md) — api service（`HttpTestingController`）、store、元件的完整範例。Clean 專案的 Facade／UseCase 測法比照 store（換掉替身即可）；Entity／Mapper 是純 TypeScript，直接 `new` 了斷言，不需範例。
