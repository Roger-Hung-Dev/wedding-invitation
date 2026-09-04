# 參考：測試策略

## 分層優先序

| 對象 | 優先序 | 理由 |
| --- | --- | --- |
| `core/validators/`（`zodValidator`）、pipe、純函式 | **必測** | 純函式，輸入輸出明確，CP 值最高 |
| `schemas/`（Zod schema） | **必測** | 驗證規則是業務規則，錯了整個表單都錯 |
| `api/`（`*.api.ts`） | **必測** | 用 `HttpTestingController`，測 URL、method、payload、參數編碼 |
| `features/*/*.store.ts` | **必測** | 用假 api service，測三態流轉（loading / error / 資料） |
| `core/interceptors/` | **必測** | 錯誤正規化與提示分支是全站共用邏輯 |
| 互動型元件（表單、有分支邏輯的） | **選測** | 只測有分支邏輯、關鍵互動者 |
| 純展示型元件、UI 元件庫本身 | **不測** | 無邏輯或第三方已測，效益低 |

## 掛載注意事項

- 元件測試用 `TestBed.configureTestingModule({ imports: [XxxComponent], providers: [...] })` —— standalone 元件放 `imports` 而非 `declarations`。
- 需要 HTTP 時用 `provideHttpClient()` + `provideHttpClientTesting()`，**不要**用已移除的 `HttpClientTestingModule`。
- 需要路由時用 `provideRouter([])`，需要 `routerLink` 就把 `RouterLink` 加進元件的 imports（元件本來就該有）。
- **i18n**：用 Transloco 的測試模組（或提供假的 `TranslocoService`），否則 `t()` 會回傳 key 而非文案 —— 若斷言的是畫面文字就會失敗。實務上**斷言 key 比斷言翻譯後的文案穩定**，優先用假實作讓 `t()` 回傳 key。
- **UI 元件庫**：是否需要註冊、怎麼註冊見該 `ui-*` skill（`ui-angular-material` 的元件需 import 對應 module；`ui-bootstrap5` 是純 CSS，不需要）。
- `NotifyService` 一律用假實作（`useValue: { error: jest.fn(), success: jest.fn() }`），不必真的渲染提示。

## 常見陷阱

- **signal 不需要 `tick()`**：它是同步讀取的。要 `fakeAsync` 的是 RxJS 的非同步流與 `setTimeout`。
- **`OnPush` 元件**：改了 input 後要 `fixture.componentRef.setInput('id', 'x')` 再 `detectChanges()`，直接改 `component.id` 不會觸發變更偵測。
- **`httpMock.verify()`** 放在 `afterEach`，能抓出「測完還有沒被消化的請求」這種漏網之魚。
