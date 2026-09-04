---
name: Bootstrap 5 UI 元件庫
description: Bootstrap 5 元件庫的使用規範（適用框架：Vue 3、Angular）—— 只用 CSS、不引 Bootstrap JS，SCSS 變數覆寫與按需引入、grid 與 utility 版面、以框架反應式狀態自寫互動元件（modal／dropdown／collapse）、表單錯誤顯示（.is-invalid／.invalid-feedback）、自寫回饋通知，以及瀏覽器截圖 profile。專案的 UI 元件庫選定 Bootstrap 5 時使用。
---

# Bootstrap 5 UI 元件庫

> 本 skill 是 `ui-*` 家族的一員：**只收「UI 元件庫怎麼用」**。框架層的分層、相依方向、schema 驗證與 i18n 機制不在此，見對應的 `vue3-*` / `angular-*` skills。

## 適用框架

| 框架 | 可用 | 說明 |
| --- | --- | --- |
| Vue 3 | ✅ | 互動元件以 `ref` / `computed` 綁 class |
| Angular | ✅ | 互動元件以 signal 綁 class |

Bootstrap 5 是**純 CSS 庫**，這正是它能同時掛在兩個框架下的原因。本 skill 的規則絕大多數兩邊共用，僅「自寫互動元件」與「表單錯誤顯示」需分框架看範例。

一個專案只會有**一個** `ui-*` skill。若你在專案裡同時看到多個或一個都沒有，先向使用者確認要用哪一套，不要自行混用。

## 最重要的鐵律：不引 Bootstrap 的 JS

**只引 Bootstrap 的 CSS，絕不引它的 JS**（不 `import 'bootstrap'`、不用 `data-bs-toggle` / `data-bs-target` 屬性、不 `new bootstrap.Modal()`）。

理由：Bootstrap 的 JS 會**直接操作 DOM**（自行增刪 `show` class、改 inline style、搬移節點到 `body`）。Vue 與 Angular 的反應式渲染同時也在管這些節點，兩者會互相覆寫 —— 症狀是 modal 關不掉、dropdown 狀態錯亂、re-render 後樣式消失。這類 bug 極難查。

**正確作法**：把 Bootstrap 的元件 class 當成「純樣式」，開關狀態一律用框架自己的反應式變數綁上去。`.modal`、`.show`、`.collapse`、`.dropdown-menu` 這些 class 的 CSS 照用，只是**由誰來加**換成框架。

## 自組客製元件時：什麼算「Bootstrap 5 的一部分」

Bootstrap 是純 CSS 庫，**自寫元件本來就是這套的常態**（見上一節鐵律），所以這裡幾乎不會出現「元件架構關不掉」那種分歧。可用的是：

- Bootstrap 的 SCSS 變數、mixin 與 utility class（讓自組元件跟其他畫面同一套間距與色彩尺標）。
- 框架自身的能力（Vue 的 `ref`／`Teleport`；Angular 的 signal／`@angular/cdk` 的 Overlay 與 a11y —— **Angular 專案用 CDK 是合理的**，它是框架生態的一部分，不是另一套元件庫）。
- **不得**引入第三方元件庫，也**不得**引入 Bootstrap 自己的 JS（既有鐵律）。純工具型函式庫（不含 UI 元件與樣式）不算元件庫，但引入前要先回報。

**自組的驗收條件**（a11y 與鍵盤操作、呼叫端零修改、零落差驗證）—— 見 [[common-user-browser]] 的「落差修不掉時：元件選型階梯與停損點」一節，那是框架中立的權威，本檔不複述。

## 引入與主題

- **引入**：在專案的 SCSS 進入點以 `@use` 引入 Bootstrap 的 SCSS 原始碼（**不是**編譯好的 `bootstrap.min.css`），才能覆寫變數與按需挑模組。
- **主題**：覆寫變數必須在 `@use ... with (...)` 一併傳入，或用 `@use ... as *` 前先設好；Bootstrap 5 的 SCSS 變數是 `!default`，晚設無效。**實際色系待設計稿確定**。
- **按需**：只引用得到的模組（`grid`、`buttons`、`forms`…），不要整包吃下來，可省下可觀的 bundle。

## 版面與 utility

- 版面優先用 Bootstrap grid（`.container` / `.row` / `.col-*`）與 flex utility（`.d-flex`、`.justify-content-between`…），不自行刻 grid CSS。
- 間距、字級、色彩優先用 utility class（`.mt-3`、`.fs-5`、`.text-muted`），少寫自訂 CSS。
- 真的需要自訂樣式時，Vue 放 `<style scoped>`、Angular 放元件自己的樣式檔（預設就是元件範圍），避免全域 CSS 污染。

## 互動元件（自寫）

modal、dropdown、collapse、offcanvas、tab 這類需要 JS 的元件，**一律自寫**：用框架的反應式狀態控制 Bootstrap 的 class。範例見 [components-without-js.md](references/components-without-js.md)。

常用對照：

| 元件 | 開啟時要加的 class | 額外注意 |
| --- | --- | --- |
| modal | `.modal` 加 `.show` + inline `display: block` | 需自行渲染 `.modal-backdrop.show`，並在開啟時給 `body` 加 `.modal-open` |
| dropdown | `.dropdown-menu` 加 `.show` | 需自行處理「點外面關閉」 |
| collapse | `.collapse` 加 `.show` | 高度轉場需自行處理，或直接不做動畫 |

## 回饋通知

Bootstrap **沒有**命令式的 toast API（不像 Element Plus 的 `ElMessage`）。專案需自行提供一個薄薄的回饋服務，內部維護一個訊息陣列，樣式套 `.toast` / `.alert`：

- Vue 3 → 一個 `useToast()` composable（模組層級單例 state）。
- Angular → 一個 `providedIn: 'root'` 的 `ToastService`（signal 持有訊息陣列）。

於 App 根元件放一個 `.toast-container` 渲染該陣列。不要每個頁面各自刻一份。

### notify 轉接層（基礎設施層要用提示時走這裡）

`api/client.ts`（Vue）／`core/interceptors/`（Angular）這類**基礎設施層不得直接相依 UI**。框架 skill 各自約定了一個轉接介面，由本 skill 提供實作。

**Vue 3** —— 模組層級的薄轉接函式：

```ts
// src/utils/notify.ts —— ui-bootstrap5 的實作
import { useToast } from '@/composables/useToast'

export function notifyError(message: string): void {
  useToast().push({ message, variant: 'danger' })
}

export function notifySuccess(message: string): void {
  useToast().push({ message, variant: 'success' })
}
```

**Angular** —— 實作 `core/notify.service.ts` 宣告的 abstract class（它同時是型別與 DI token）：

```ts
// src/app/shared/bootstrap-notify.service.ts
import { Injectable, inject } from '@angular/core'
import { NotifyService } from '../core/notify.service'
import { ToastService } from './toast.service'

@Injectable({ providedIn: 'root' })
export class BootstrapNotifyService extends NotifyService {
  private readonly toast = inject(ToastService)

  error(message: string): void {
    this.toast.push({ message, variant: 'danger' })
  }

  success(message: string): void {
    this.toast.push({ message, variant: 'success' })
  }
}
```

於 `app.config.ts` 綁定：`{ provide: NotifyService, useClass: BootstrapNotifyService }`。

> Angular 有 DI，但**攔截器仍不該直接注入本 skill 的 `ToastService`** —— 那樣 `core/` 就 import 了 UI 元件庫的具體類別，換元件庫要改攔截器。注入 `NotifyService` 這個 token，實作在組合根綁定，才是真正可插拔。

元件層要提示時直接用 `useToast()` / `ToastService`，不必繞這層；轉接層存在的目的只是隔離**不該相依 UI 的層**。

## 表單錯誤顯示

- 欄位錯誤時給 `<input>` 加 `.is-invalid`，錯誤訊息放緊鄰的 `<div class="invalid-feedback">`（`.invalid-feedback` 只有在前一個兄弟元素有 `.is-invalid` 時才會顯示，順序不能錯）。
- **不要用** Bootstrap 的 `.was-validated` + 瀏覽器原生驗證：它繞過框架的驗證狀態，兩套錯誤來源會打架。錯誤一律由框架的驗證結果驅動。
- 驗證**規則怎麼定義**不在本 skill（見 `vue3-forms-and-i18n` / `angular-forms-and-i18n`），本 skill 只管**驗證結果怎麼顯示**。

範例見 [forms-validation.md](references/forms-validation.md)（Vue 3 與 Angular 各一份）。

## 與框架 skill 的分工

| 事項 | 歸屬 |
| --- | --- |
| 驗證**規則的定義**（schema、跨層共用型別） | 框架 skill |
| 驗證結果**怎麼綁到元件、錯誤怎麼顯示** | 本 skill |
| 應用文案翻譯（`t('...')` / i18n 機制） | 框架 skill |
| 元件溝通（props / emits / input / output）、相依方向 | 框架 skill |
| Bootstrap class 怎麼用、互動元件怎麼自寫 | 本 skill |

> Bootstrap 沒有「元件庫內建文字」需要跟著切語言（純 CSS，不含任何文案），所以**沒有** Element Plus 那種 locale 同步問題 —— i18n 全部交給框架 skill。

## 瀏覽器截圖 profile

同資料夾的 `profiles/bootstrap5.profile.yaml` 是給 `common-user-browser` skill 用的慣例預設 profile。做 UI 截圖驗證時直接取用它；若專案客製過版面，複製它覆寫對應欄位即可。

## References

- [setup-and-theme.md](references/setup-and-theme.md) — SCSS 按需引入與變數覆寫。
- [components-without-js.md](references/components-without-js.md) — 自寫 modal / dropdown（Vue 3 與 Angular）。
- [forms-validation.md](references/forms-validation.md) — `.is-invalid` / `.invalid-feedback` 錯誤顯示（Vue 3 與 Angular）。
- [profiles/bootstrap5.profile.yaml](profiles/bootstrap5.profile.yaml) — `common-user-browser` 的慣例 profile。
