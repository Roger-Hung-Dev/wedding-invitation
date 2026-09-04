---
name: Angular 編碼規範
description: Angular 前端的跨架構共用編碼鐵律 —— 命名慣例、standalone 元件、架構選型入口與共通相依方向、TypeScript 規則、依賴注入（inject）規則、Signals 心法、新控制流、共通設計模式落點、組合根與環境變數、註解規範（JSDoc 與行內註解該寫什麼、禁止什麼）。撰寫或審查任何 Angular 前端程式碼前先遵循；目錄結構與各層職責見所選架構的 skill。
---

# Angular 編碼規範（鐵律）

> 本 skill 即此主題的權威編碼依據：收斂為**可執行規則**；較長的架構說明與範例程式放在 `references/`。
> **基準：Angular 20+**（standalone、signals、`input()`／`output()`、`@if`／`@for` 新控制流皆已穩定）。

## 1. 命名慣例

| 對象 | 規則 | 範例 |
| --- | --- | --- |
| 元件檔案 | kebab-case + 用途後綴 | `task-list.component.ts` |
| 元件類別 | PascalCase + `Component` | `TaskListComponent` |
| 元件 selector | `app-` + kebab-case | `app-task-list` |
| Service（含 store） | PascalCase + `Service` / `Store` | `TaskApiService`、`TaskStore` |
| 型別 / 介面 | PascalCase，**不加 `I` 前綴** | `interface Task {}` |
| 變數 / 函式 | camelCase | `activeId`、`fetchTasks()` |
| 常數 | UPPER_SNAKE_CASE | `MAX_TITLE_LENGTH` |
| 自訂 CSS class | kebab-case | `.task-card__title` |

## 2. 架構：專案級決策，二選一

本工作區的 Angular 專案支援**兩種互斥架構**。哪一種由 `engineering-manager` 籌組時定案，寫在**專案 CLAUDE.md 的「前端架構」段**，對應的架構 skill 也只會複製那一個進專案：

| 架構 | 架構 skill | 相依鏈 |
| --- | --- | --- |
| 精簡分層（feature store） | `angular-feature-store-architecture` | `component → store → api → core` |
| Clean Architecture | `angular-clean-architecture` | `presentation → domain ← data`（相依指向內層） |

- **動手前先確認專案用哪一套**：以專案 CLAUDE.md 為首選來源，其次看 `.claude/skills/` 底下有哪個架構 skill（正常只會有一個），然後讀它。
- **不臆測、不混用**：一個都沒有、同時有兩個、或 CLAUDE.md 與既有程式碼結構不符時，**停下來回報**，不要自己挑一個。若 CLAUDE.md 與程式碼衝突，**依程式碼實作並回報矛盾**（程式碼是事實，CLAUDE.md 只是當初的宣告）。
- 選項的取捨說明只在 `engineering-manager` 一份，本檔不重複。

**兩案共通的相依鐵律**（架構 skill 只講各自的落點，這幾條一律適用）：

- **上層可相依下層，下層不得相依上層**；同層之間盡量避免互相相依。
- **元件不得直接注入資料存取層**（`api/` 或 `data/`），一律經該架構指定的中介（store 或 facade）。
- **最底層不得相依任何 UI 元件庫**（`core/`、`api/`、`domain/`、`data/`；見第 6 節）。
- **`shared/` 只放無業務邏輯的展示元件 / pipe / directive**，不得相依任何 feature。

SPA 進入點與 `app.config.ts` 組合根兩案共用，見 [references/app-bootstrap.md](references/app-bootstrap.md)。

## 3. 元件

- **一律 standalone**：Angular 19+ 起 `standalone: true` 是預設值，**不要再寫這個旗標**，也不要新增 `NgModule`。
- 相依的元件 / 指令 / pipe 寫進 `imports: [...]`。
- **一律 `changeDetection: ChangeDetectionStrategy.OnPush`**。搭配 signals 時這是正確且高效的預設，沒有例外理由。
- 輸入輸出用函式式 API：`input()` / `input.required<T>()` / `output()` / `model()`，**不用** `@Input()` / `@Output()` 裝飾器。
- 樣板控制流用 `@if` / `@for` / `@switch`，**不用** `*ngIf` / `*ngFor`。`@for` 的 `track` 是必填，填穩定唯一值（通常是 `id`），**不要填 `$index`**（會讓 DOM 重用失效）。
- 單一元件過大時，抽出子元件或把邏輯移進 service，維持單一職責。

## 4. 依賴注入

- **一律用 `inject()`**，不用 constructor 參數注入 —— 可用於欄位初始化、繼承時不必轉傳、型別推導更好。
- 注入的相依宣告為 `private readonly`：`private readonly http = inject(HttpClient)`。
- 全域單例用 `@Injectable({ providedIn: 'root' })`；只服務單一元件子樹的，才寫進該元件的 `providers`。
- 需要抽換實作時（如 UI 轉接層）用 **abstract class 當 DI token**，在 `app.config.ts` 綁實作，不要讓上游 import 具體類別。

## 5. Signals

- **狀態一律用 signal**，不用 `BehaviorSubject` 當狀態容器。
- 對外**只暴露唯讀**：內部 `private readonly _items = signal<Task[]>([])`，對外 `readonly items = this._items.asReadonly()`。
- 衍生值用 `computed()`，**不要**用 `effect()` 去寫另一個 signal（那是把宣告式改成命令式，會產生難查的連鎖更新）。
- `effect()` 只用於**副作用**（記 log、寫 localStorage、呼叫命令式 API），不用於同步狀態。
- RxJS 與 signal 的橋接用 `@angular/core/rxjs-interop` 的 `toSignal()` / `toObservable()`。HTTP 這類一次性非同步仍走 Observable，在邊界轉成 signal。

## 6. UI 元件庫可插拔

UI 元件庫**不綁在本 skill**，由專案配的 `ui-*` skill 決定（`ui-angular-material`、`ui-bootstrap5`…）：

- 做畫面前先確認專案用哪個 `ui-*`（正常只會有一個），**沒有或有多個就問，不要臆測**。
- **`core/` 與 `api/` 不得 import 任何 UI 元件庫**。需要全域提示時注入 `NotifyService`（abstract class 當 token，宣告在 `core/`），實作由 `ui-*` skill 提供並在 `app.config.ts` 綁定 —— 換元件庫時攔截器不用動。

## 7. TypeScript

- `tsconfig` 開啟 `strict`（含 `strictTemplates`）；**不使用 `any`**，必要時用 `unknown` 並收斂型別。
- 對外匯出的函式標註回傳型別；跨層共用型別放 `types/` 或 `schemas/`。
- API 回傳資料一律先定義型別，再於 service 中使用。

## 8. 設計模式落點

兩案共通的模式落點：

| 模式 | 落點 | 用途 |
| --- | --- | --- |
| Singleton | `providedIn: 'root'` service | 全站共用單一實例 |
| Adapter | `core/notify.service.ts`（abstract token） | 隔離 UI 元件庫的命令式提示，讓底層不相依元件庫 |
| Interceptor | `core/interceptors/` | 集中處理錯誤正規化、未來夾帶 token |

> **Store Pattern／Facade／Repository／Mapper** 這些與分層直接相關的模式，落點依專案架構而定 —— 見專案配的架構 skill（第 2 節），本檔不預設。

## 9. 開發流程

- 提交前由 **husky + lint-staged** 對 staged 檔自動跑 ESLint（`--fix`）+ Prettier，未過即擋下提交。
- 型別檢查與完整 build 交由 CI 或 `build` 指令，不入 pre-commit。
- 環境變數、多環境與建置指令詳見 [references/env-config.md](references/env-config.md)。

## 10. 註解（鐵律）

> **總判準：註解寫「為什麼」，不寫「做什麼」。** 程式碼本身已經說了做什麼，複述一次不會增加資訊，卻會在下次改程式時變成謊言 —— **過期的註解比沒有註解更糟**，因為讀的人會相信它。
> **一律使用繁體中文、純文字**（識別名稱與專有名詞保留原樣）。

### 10.0 先決定用哪一種：看位置，不看長度

| 註解寫在哪 | 用哪一種 |
| --- | --- |
| 函式、類別、service 方法、store 或 facade 成員、型別成員的**宣告上方** | **`/** */` JSDoc 區塊註解**（§10.1） |
| 函式**內部**、程式碼敘述之間或行尾 | **`//` 行內註解**（§10.2） |

- **禁止在宣告上方堆疊 `//`**。說明一個匯出項目是 JSDoc 的工作，不是行內註解的。堆一疊 `// xxx` 的代價是**全部工具都讀不到**：編輯器的 hover tooltip 不顯示、TypeScript 不會把它帶到呼叫端、文件產生器抓不到，而且視覺上像被註解掉的程式碼。
- **這條與長度無關。** 宣告上方就算只有一句也用 `/** */`；函式內部就算要寫兩句也用 `//`。§10.2 的「1～2 行為原則」約束的是**函式內部**的行內註解，**不是**「超過兩行就升級成 JSDoc」。
- **樣板／template 內**要說明時用該框架的樣板註解，不要把 JSDoc 塞進樣板。

```ts
// ✗ 錯：用行內註解說明宣告
// 品項 Id。
// 依 kind 分別對映 ProductSku.Id 或 ProductCombo.Id，兩路值域重疊。
id: number

// ✓ 對：宣告上方一律用 JSDoc
/**
 * 品項 Id。
 * 依 kind 分別對映 ProductSku.Id 或 ProductCombo.Id，兩路值域重疊。
 */
id: number
```

### 10.1 JSDoc 區塊註解 `/** */`

| 情況 | 規則 |
| --- | --- |
| **必寫** | 跨檔案會被別人用到的匯出項目：service／store／facade 的公開方法（尤其**副作用**與**何時觸發請求**）、UseCase、Repository 介面、Mapper、共用 util、`CanActivateFn` 守衛的放行條件 |
| **必寫** | 元件的 `input()`／`output()` 中**語意無法從名稱與型別看出**的項目（單位、代碼意義、允許值、與其他 input 的關係） |
| **不必寫** | 檔案內部的私有方法；名稱已完整表達的自明方法；一般的 `input()` 項目 |
| **禁止** | **重複 TypeScript 已表達的資訊** —— 不寫 `@param {string} id`、不寫 `@returns {Observable<User>}`。型別由 TS 負責，JSDoc 只補型別說不出的語意 |
| **禁止** | 留空的標籤、只是把方法名翻成中文。寫不出比名稱更多的資訊，就不要寫 |

**排版：一句一行**

- **一個完整的句子結束就換行。** 一行放兩句以上會擠成一段密文，編輯器的 hover tooltip 也會糊成一塊。句號、驚嘆號、問號算句子結束；**逗號、頓號不算**（「依 kind 分別對映 A 或 B，兩路值域重疊。」是一句，不要從逗號拆開）。

**排版：多行標籤的續行要縮排一層**

一個標籤的說明跨多行時，**續行相對於標籤行縮排一層**（依專案 `.editorconfig`，本工作區為空白，**不要打 Tab 字元**）。續行與標籤齊平時，看不出哪裡是新標籤、哪裡還是上一個標籤的內容 —— 尤其說明裡含 `{@link}`／`{@linkcode}` 這類子標記時，主層與子層會糊成一片。

- **縮排代表的是層級，不是換行。** 一句話太長而必須折行時，續行與該句首行同層、不再多縮一層；真的每次都得折，代表這句該拆成兩句。

```ts
// ✗ 錯：續行與標籤齊平，看不出還屬於同一個 @param
/**
 * @param kind 品項路別。必須與 {@link id} 成對使用：兩路值域重疊、
 * 服務層依此決定查哪張表。
 * @param id 品項識別碼
 */

// ✓ 對：續行縮排一層，一句一行
/**
 * @param kind
 *     品項路別（sku／combo，大小寫不敏感）。
 *     必須與 {@link id} 成對使用：兩路值域重疊，服務層依此決定查哪張表。
 * @param id 品項識別碼
 */
```

### 10.2 行內註解 `//`

**只在讀的人會困惑的地方寫。** 以下五種情況**必須**寫：

1. **非顯而易見的畫面規則** —— 用一句話說明它為什麼長這樣。例如「暫存不檢核必填，只有正式送出才檢核」。
2. **刻意不做的事、反直覺的寫法** —— 沒寫的話，下一個人（或下一個代理）會「順手改回正常寫法」而破壞行為。
3. **對抗框架或 UI 元件庫預設行為的 workaround** —— `::ng-deep`、`!important`、覆寫元件庫內部 class、`ViewEncapsulation.None`。**寫清楚為什麼非這樣不可、以及影響到哪些畫面**；這是前端最常見「看不出為什麼、於是被下一個人刪掉」的地方，**動全域樣式時尤其必要**。
4. **變更偵測與時序陷阱** —— `OnPush` 下需要手動 `markForCheck()` 的原因、`effect()` 的觸發時機與相依、`untracked()` 的必要性、`toSignal`／`toObservable` 的橋接取捨、手動清理的訂閱與計時器。
5. **暫時性妥協** —— `// TODO:`／`// HACK:` 一律附**原因**與**解除條件**，不得只留一個裸 `TODO`。

**格式：純文字、簡短**

- **只用純文字。** 不要表情符號或圖示（⚠ 🔒 ⛔ ✅ 🚨 等）—— 它們沒有一致的定義，讀的人得自己猜「這個鎖頭是什麼意思」，而且無法搜尋。要強調就把話講清楚。
- **不要引用規格章節或編號**（`VR-003`、`IR-002`、`§三`、需求單號）—— 規格會改版、編號會位移，引用很快就指向錯的地方；而且讀的人還是得跳出去翻文件才知道你在講什麼，等於沒說。**要講的重點直接寫成一句話。**
- **行內註解以 1～2 行為原則。** 需要三行以上，通常代表這件事屬於規格文件、或這段程式碼該重構 —— 不是該寫更長的註解。

**禁止**：

- **複述程式碼** —— `// 取得使用者` 寫在 `getUser()` 上面。
- **被註解掉的程式碼／template 區塊** —— 一律刪除，歷史留在 git。
- 分隔線橫幅（`// ===== 以下為表單 =====`）—— 需要分區代表該拆元件或拆 service 了。
- **過期註解** —— 改程式碼時同步改註解；改不動就刪掉，不要留著。
- **template 註解裡寫任何敏感或內部資訊** —— Angular 的 `<!-- -->` 會保留成 DOM 的 comment node，使用者按檢視原始碼就看得到。

### 10.3 樣式中的寫死數值

對稿時若不得不寫死數值（而非用設計 token），**用一句純文字說明它從哪來**，例如 `// 設計稿數值`。沒有說明的 magic number 無法判斷是刻意還是隨手填的，下一個人不敢動也不敢刪。**優先仍是用 token 修，寫死是例外。**

### 10.4 紅線：註解不是規格

畫面規則（欄位檢核、連動、API 對應）**以 `fe`／`api` 規格為單一真相，不要搬進註解**。註解只交代「這段程式碼為什麼這樣寫」；**一句話講不完的，就是規格文件的內容，不是註解的內容**。

### 10.5 既有檔案

**不強制回頭補齊或清理**既有檔案的註解。動到的方法順手補、順手把圖示與章節引用改成純文字；沒動到的不碰 —— 為補註解而產生的大量無關 diff，會讓真正的變更淹沒在裡面。

## References

- [app-bootstrap.md](references/app-bootstrap.md) — SPA 進入點、`app.config.ts` 組合根（兩案共用）。
- [env-config.md](references/env-config.md) — 環境變數、多環境設定與建置指令。

> 目錄結構與各層職責**不在本 skill** —— 依專案架構而定，見 `angular-feature-store-architecture` 或 `angular-clean-architecture`。
