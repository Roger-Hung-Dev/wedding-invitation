---
name: Angular 表單與 i18n
description: Angular 的元件溝通、表單驗證與多國語系規範 —— input()/output() 慣例、Reactive Forms、驗證規則以 Validators 為預設並在跨層共用或複雜時升級為 Zod schema，以及 Transloco 執行期語系切換。建立或修改畫面元件、表單驗證或 i18n 時使用；UI 元件庫的用法（元件、主題、錯誤顯示）見專案選定的 ui-* skill。
---

# Angular 表單與 i18n

> 本 skill 即此主題的權威編碼依據：元件溝通、驗證規則的定義與 i18n 收斂在此，範例見 `references/`。基準：Angular 20+。
> **UI 元件庫的用法不在此**：元件怎麼組、主題怎麼調、錯誤訊息怎麼顯示、命令式回饋怎麼叫 —— 一律見專案選定的 `ui-*` skill。

## UI 元件庫是可插拔的

本工作區把「UI 元件庫」抽成獨立的 `ui-*` skill 家族，Angular 專案可搭配其中任一套：

| ui-* skill | 說明 |
| --- | --- |
| `ui-angular-material` | Angular Material（Angular 專屬） |
| `ui-bootstrap5` | Bootstrap 5（純 CSS，Vue 3 / Angular 通用） |

專案裡通常只會有**一個** `ui-*` skill，由 `engineering-manager` 籌組時選定並複製進來。動手做畫面前先讀它；若專案裡一個都沒有或同時有多個，先向使用者確認要用哪一套，不要自行混用或臆測。

> `ui-element-plus` 是 Vue 3 專屬，**不相容 Angular**。若在 Angular 專案看到它，回報這個矛盾，不要試圖使用。

## 分工線

| 事項 | 歸屬 |
| --- | --- |
| 驗證**規則的定義**（`Validators`、Zod schema、跨層共用型別） | 本 skill |
| 驗證結果**怎麼綁到元件、錯誤怎麼顯示** | `ui-*` skill |
| 應用文案翻譯（Transloco、訊息分檔） | 本 skill |
| **元件庫內建文字**跟著切語言 | `ui-*` skill |
| 元件溝通（`input()` / `output()`） | 本 skill |
| 元件庫的元件怎麼組版面、主題怎麼調 | `ui-*` skill |

## 元件溝通

- 輸入輸出用函式式 API：`input()` / `input.required<T>()` / `output()` / `model()`，**不用** `@Input()` / `@Output()` 裝飾器。
- `shared/` 的展示元件透過 `input()` 接收、`output()` 往上拋事件；**不直接注入狀態層或資料存取層**（詳見 `angular-coding-standards`）。
- 雙向綁定用 `model()`（`[(value)]="..."`），不要自己刻 `valueChange` output。
- 單一元件過大時，抽出子元件或把邏輯移進 service，維持單一職責。

## 表單

- **一律 Reactive Forms**（`ReactiveFormsModule` + `NonNullableFormBuilder`），**不用** Template-driven（`ngModel`）—— 型別安全與可測試性差太多。
- 用 `NonNullableFormBuilder` 而非 `FormBuilder`：控制項不會莫名變成 `T | null`，`reset()` 也會回到初始值而非 null。
- `<form>` 一律加 `novalidate` 關掉瀏覽器原生驗證，錯誤來源只留 Angular 這一套。

## 表單驗證

**預設用 Angular 內建 `Validators`**（`required`、`maxLength`、`email`…）；符合下列情況才升級為 **Zod schema**：

1. 該資料模型需**跨層共用型別**（表單輸入 ≈ API payload / 回應）；
2. 驗證**複雜**（跨欄位、條件式、動態規則）。

用 Zod 時的鐵律：

- **schema 是單一真相來源**，型別一律由 `z.infer` 導出，不要另外手寫一份 `interface`。
- schema 放專案架構指定的位置（見下方落點表）；**不要寫在元件裡**。
- 錯誤訊息文案走 i18n key，不在 schema 裡寫死中文字串。
- 接進 Reactive Forms 時用共用的 `zodValidator` adapter（見 references），不要每個表單各寫一份。

至於「驗證結果怎麼接到表單元件、錯誤怎麼顯示」—— 那是 UI 元件庫的事，見 `ui-*` skill。

### 落點：× 兩架構

表單與 i18n 的寫法兩案完全相同，**差別只在 schema 住哪、以及跟實體驗證的關係**：

| | 精簡分層（`angular-feature-store-architecture`） | Clean（`angular-clean-architecture`） |
| --- | --- | --- |
| Zod schema 位置 | `src/app/schemas/task.schema.ts`（跨層共用） | `features/task/presentation/` 底下（**表單是表現層的事**） |
| 型別的單一真相 | schema（`z.infer`）—— `api/` 也用它 | **Entity**（`domain/`）—— schema 只管表單輸入的形狀 |
| 實體本身的驗證 | 同一份 schema，或 `schemas/` 旁的純函式 | **`Entity.validate()`**（`domain/`），與表單 Validators **並存** |

> **Clean 專案別把 Zod schema 放進 `domain/`** —— 那會讓領域層相依 Zod，違反零框架相依（Zod 不是 Angular，但一樣是外部套件）。`domain/` 的驗證用 `Entity.validate()` 手寫，就那幾行。
>
> **兩層驗證不是重複，都要留**：Validators／Zod 管「使用者打字當下的即時回饋」，`Entity.validate()` 管「這個物件本身合不合法」—— 後者在沒有表單的路徑（匯入、API 回填）也會跑到。

## i18n

- **應用文案** → **Transloco**（執行期切換語言），語言檔放 `src/assets/i18n/{lang}.json`。文案**一律**走 `t('...')` / `transloco` pipe，不寫死字串。
- **元件庫內建文字**（分頁器、日期選擇…）→ 各元件庫做法不同，見 `ui-*` skill；切換語言時要與 Transloco **同步**。

> 為什麼不用官方的 `@angular/localize`：它是**建置期**翻譯，每個語言各出一份 bundle、靠部署路徑分流，**無法在執行期切語言**。本工作區的前端規範（含 Vue 模組的 vue-i18n）都是執行期切換 + 語言切換器，Transloco 才對齊。

## References

- [form-schema.md](references/form-schema.md) — `Validators` 預設、Zod schema 定義、`zodValidator` adapter 與跨層共用。
- [i18n-setup.md](references/i18n-setup.md) — Transloco 設定、loader、樣板與 TS 用法、語言切換。
