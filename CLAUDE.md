# wedding-invitation

> 由 engineering-manager 籌組的開發專案工作區。

## 專案概述

- **名稱**：wedding-invitation
- **目標**：沉浸式單頁電子喜帖（single-page immersive digital wedding invitation）。純前端視覺展示網站，重視視覺表現與動畫過場。
- **專案性質**：全新專案（greenfield）
- **範圍界線**（很重要，決定了什麼事不該做）：
  - **沒有後端、沒有 API、沒有資料庫。** 喜帖內容（新人姓名、時間、地點、相簿、故事線）一律寫死在前端或放靜態資料檔。
  - **不做 RSVP 後端。** 出席統計走**外部 Google 表單連結** —— 頁面上只放一個連到 Google 表單的按鈕或連結，不自建表單送出、不收使用者資料、不存任何資料。
  - 因此**不要**引入 HTTP 呼叫後端 API、狀態持久化、認證授權、資料庫這幾類東西。真的需要時是另一個決策等級的事，要先確認範圍。

## 怎麼用（本專案納入的能力）

| 能力 | 怎麼叫 | 用途 |
| --- | --- | --- |
| Angular 前端工程（20+） | 直呼 `front-end-angular-engineer` | standalone 元件 ＋ Signals、路由、Reactive Forms、Transloco、Jest |
| 設計稿產線 | `/design-lead <需求>` | 從 Figma 讀取分析、繪製到設計檔、把設計疑問標到畫面上 |
| 程式碼審查 | 直呼 `code-reviewer` | 完成一段程式碼後、或提交前把關 |
| 輪播影片分鏡 | 直呼 `storyboard-artist` | 照片＋配樂 → 規劃表 → 畫進 v2 分鏡稿 .pen 並標註特效 |
| 分鏡稿轉影片 | 直呼 `storyboard-video-renderer` | 指定 .pen → 輸出指定規格 mp4；補實作新特效 |
| 特效實驗室 | 直呼 `fx-lab` | 文字描述 → artifact 預覽 → 使用者裁決 → 寫進 fx-* 特效庫 |
| 3D 角色工作室（一條龍） | `/blender-studio` | 問齊參數 → 建角色 → 做情境 → 發布成果網頁（Claude Artifact） |
| 3D 角色建置 | 直呼 `blender-creator` | VRoid `.vroid`＋真人照片 → 01 身體完成度、02 動作測試、03 照片款服裝；事後改服裝 |
| 3D 角色情境 | 直呼 `blender-scenario-creator` | 情境描述＋角色專案 → 情境影片／圖片 |
| 動作庫擴充 | 直呼 `blender-animation-append` | 動作描述 → 寫進共用動作庫、檢查通過才入庫 |

### 3D 角色產線的分工（三個子代理＋一條 workflow）

```
/blender-studio（主控端問齊參數）──▶ workflow blender-character-studio
    ├─ blender-creator ──────────▶ projects/<名稱>/（.blend、qa/、pictures/、videos/）
    ├─ blender-scenario-creator ─▶ 同一個專案的 videos/scenes、pictures/scenes（每段情境一次）
    └─ 發布成果網頁（blender-report-page）
blender-animation-append ──▶ 共用動作庫（blender-motion-library 的 actions_custom.py ＋ library/actions_catalog.json）
```

- 資料都在 `.claude/docs/data/blender/`：`projects/<名稱>/` 一個角色一個資料夾；`library/` 是預設資料庫（手勢、表情、腳、30 種動作、粉色蓬裙禮服，來自範例專案 `projects/bride`）。資料夾說明見那裡的 `README.md`。
- **臉部模型只收 `.vroid`，但 VRoid MCP 不能匯出 VRM。** 使用者要先在 VRoid Studio 開 .vroid → 按 F8 → 存成 VRM 1.0（放在 .vroid 旁邊同檔名）。沒有 VRM 時 `blender-creator` 會停下來回報，不會硬做。
- **Blender 要開著**（MCP for Blender 外掛啟動）。VRM 匯入只能在 GUI Blender；長時間渲染改用背景 Blender（`blender.exe -b … -P bl_cli.py`），可並行、不受 MCP 120 秒限制。
- 影格 png 放系統暫存 `%TEMP%\blender-work\<名稱>\`，專案裡只放 mp4／jpg 成品。`.blend` 與 `source/`（使用者的原檔與照片）不進版控。

### 輪播影片產線的分工（三個子代理）

```
fx-lab ──（裁決通過）──▶ fx-* 特效技術文件 ◀── 兩邊都照這裡的寫法與演算法
                              │
storyboard-artist ──畫──▶ v2 分鏡稿 .pen ──讀──▶ storyboard-video-renderer ──▶ mp4
```

- **格式契約**是 `storyboard-pen-format`：分鏡稿怎麼命名、每個欄位怎麼寫。畫稿與讀稿兩邊都以它為準。
- 產生器程式在 `.claude/skills/storyboard-video-render/scripts/`。它已用第 2 版成片逐格驗證：1,569 個時間點像素完全相同。
- 子代理不能問使用者問題。需要裁決時（例如 fx-lab 的預覽），子代理會停下來回報；主控端轉問使用者後，再把結果帶回去。
- 現有的 `wedding-photo-slideshow.pen` 是 **v1 格式**，產生器不能直接讀。v1 缺版型欄與特效參數。要用新產線重產，先請 `storyboard-artist` 以 `upgrade` 模式升級成 v2。

### 設計稿產線的三個前提（不照做會出事）

1. **設計檔須由你自己在 Pencil Desktop 手動建立並開啟。** 代理不自建、不自開、不自存 —— 這條防的是已發生過的事故：以 shell 產生的 0-byte 空檔會被 Pencil 當成可拋棄的暫時檔，換文件時連帶把其他已開啟的設計檔丟進回收桶。
2. **繪製完成後要手動 Save All，內容才會真的寫到磁碟。**
3. **逐題結案設計疑問請直接呼叫 `design-question-curator`，不要走 `/design-lead`。** 那是需要你逐題裁決的互動迴圈，不經 workflow 編排。

要讓下游看得到設計稿視覺，請組長跑 `pen-export-png`（設計檔 → png ＋ `_index.md` ＋ `_layout-spec.md` 版面數值）。這是獨立呼叫，不是 step。

## 指派團隊（agents）

- `front-end-angular-engineer`：Angular 20+ 前端實作，以 `angular-*` skills 為權威依據，預載 `angular-coding-standards`。
  - 對應 skills：`angular-coding-standards`、`angular-feature-store-architecture`、`angular-api-integration`、`angular-state-and-routing`、`angular-forms-and-i18n`、`angular-testing`、`ui-bootstrap5`、`common-user-browser`、`git-commit-convention`
- `code-reviewer`：程式碼審查、提交前把關。
- `figma-reader`：設計稿產線 worker（step `read`）—— 用 Figma Bridge MCP 讀設計稿，產出中介分析檔。不碰設計檔。
  - 對應 skills：`design-handoff-contract`、`figma-bridge-reading`
- `pen-drawer`：設計稿產線 worker（step `draw-flow`／`draw-screen`／`draw-scenario`）—— 依分析檔用 Pencil MCP 繪製。不讀 Figma。
  - 對應 skills：`design-handoff-contract`、`pen-authoring`、`pen-flow-diagram`、`pen-screen-drawing`、`pen-scenario-sequence`、`pen-shared-component-library`
- `design-question-curator`：設計稿產線 worker（step `annotate`）＋ 直呼的逐題結案迴圈（`resolve`）。
  - 對應 skills：`design-handoff-contract`、`pen-authoring`、`pen-screen-drawing`
- `storyboard-artist`：輪播影片分鏡師（plan／draw／revise／upgrade）。
  - 對應 skills：`storyboard-pen-format`、`storyboard-planning`、`pen-authoring`、`fx-camera-motion`、`fx-transition`、`fx-title-opening`、`fx-title-ending`
- `storyboard-video-renderer`：分鏡稿 → 影片。對 .pen 只能唯讀（frontmatter 掛了 `pen-readonly-guard` hook）。
  - 對應 skills：`storyboard-video-render`、`storyboard-pen-format`、`fx-*` 四份
- `fx-lab`：特效發想與預覽，裁決通過後擴充 `fx-*` 特效庫。
  - 對應 skills：`fx-lab-preview`、`fx-*` 四份
- `blender-creator`：3D 角色建置（.vroid＋照片 → 01 身體、02 動作測試、03 服裝；改服裝）。工具含整個 `mcp__blender`。
  - 對應 skills：`blender-character-build`、`blender-motion-library`、`blender-report-page`
- `blender-scenario-creator`：3D 角色情境（情境描述＋專案 → 影片／圖片）。
  - 對應 skills：`blender-scenario`、`blender-motion-library`、`blender-report-page`
- `blender-animation-append`：擴充共用動作庫（檢查通過才入庫）。
  - 對應 skills：`blender-motion-library`

> **`blender-studio` 也是 skill（slash command `/blender-studio`），不是 agent**：它在主控端問齊參數後呼叫 workflow `blender-character-studio`。

> **組長 `design-lead` 是 skill ＋ slash command，不是 agent。** 別去 `.claude/agents/` 找它，那裡沒有這個檔。派工能力只存在於主控端，因為子代理不能再派發子代理。

## UI 元件庫

- 本專案選定：`ui-bootstrap5`（Bootstrap 5）。
- **用法是純 CSS，不引 Bootstrap 的 JS** —— 互動元件（modal、collapse、dropdown、carousel）一律用 Angular 的反應式狀態自寫。做畫面前先讀該 skill。
- 框架層的分層、驗證規則定義與 i18n 見 `angular-*` skills。
- 專案只配這一套，不要混用其他元件庫。

### 「不混用元件庫」≠「一律用現成元件湊」

這兩件事是分開的，不要混為一談：

- **禁止的是引入第三方元件庫**（Angular Material、PrimeNG、Ng-Zorro、Vuetify、Ant Design 等）。這條沒有例外。
- **Bootstrap 5 本來就是純 CSS 庫，自寫互動元件是常態、不是例外。** Angular 專案要做 overlay／focus trap／a11y 這類底層行為時，用 `@angular/cdk` 是合理的（見 `ui-bootstrap5` skill）。
- 設計稿要求的**結構或行為模型**與某顆元件的規範架構衝突時（不是色值／尺寸差異），**自組客製元件是預期作法，不是例外**。硬用 CSS 去凹一個架構上做不到的樣子，只會浪費輪次並留下半套結果。
- **這個專案尤其如此** —— 沉浸式喜帖的視覺一定是全客製，會有大量捲動觸發動畫、全螢幕過場、自訂相簿之類的東西，那些本來就沒有現成元件可用。
- 選型階梯、停損點（同一落差試過 2 種 CSS 解法仍無法對齊即停止嘗試）與自組的驗收條件見 `common-user-browser` skill 的「落差修不掉時：元件選型階梯與停損點」一節。

## 前端架構

- **架構**：精簡分層（feature store）—— 分層、各層職責與相依方向見 `angular-feature-store-architecture` skill。
  - 結構為 `core/`／`api/`／`features/*/*.store.ts`／`shared/`，相依鏈 `component → store → api → core`。
  - 選它的理由：這個專案沒有後端契約要對映、沒有前端專屬業務規則、也沒有資料來源要抽換。Clean Architecture 的十幾個檔案在這裡只會是純成本。
  - ⚠️ 本專案沒有後端，所以 `api/` 這一層多半是空的或只放靜態資料載入。**不要為了「架構完整」而生出一個假的 API 層。**
- **狀態管理**：Signals ＋ service，**不引 NgRx**（這是跨專案的硬性規定，不是本專案的選擇）。
- 跨架構的編碼鐵律（命名、standalone、`inject()`、Signals、新控制流、TS、註解規範）見 `angular-coding-standards`。
- 以上為**專案級決策、一次定案**，本專案不混用兩種架構。要改屬獨立的重構任務，需先確認範圍。

## 目錄結構

```
D:\SideProject\wedding-invitation\
├── CLAUDE.md                  # 本檔
├── .mcp.json                  # 專案級 MCP servers（chrome-devtools、figma-bridge）
├── .env.example               # MCP 變數鍵名樣板（只登記鍵名，不放真值）
├── .gitignore                 # 只忽略密鑰與個人設定
├── .gitattributes             # 釘 .claude/workflows/*.js 為 LF
└── .claude\
    ├── settings.json          # hooks 接線（進版控）
    ├── settings.local.json    # MCP 免提示核准＋密鑰真值（不進版控）
    ├── agents\                # 11 個：front-end-angular-engineer、code-reviewer、
    │                          #        figma-reader、pen-drawer、design-question-curator、
    │                          #        storyboard-artist、storyboard-video-renderer、fx-lab、
    │                          #        blender-creator、blender-scenario-creator、blender-animation-append
    ├── skills\                # 30 個（angular-* 6、ui-bootstrap5、common-user-browser、
    │                          #        git-commit-convention、design-* 與 pen-* 8、
    │                          #        storyboard-* 3、fx-* 5、blender-* 5）
    ├── commands\
    │   └── design-lead.md     # 設計稿產線組長入口 /design-lead
    ├── workflows\
    │   ├── figma-pen-team.js  # 產線編排（read／draw-flow／draw-screen／draw-scenario／annotate）
    │   ├── pen-export-png.js  # 下游交付：設計檔 → png ＋ _index.md ＋ _layout-spec.md
    │   └── blender-character-studio.js  # 3D 角色：建角色 → 情境 → 發布成果網頁
    ├── docs\data\blender\     # 3D 角色專案（projects/）與預設資料庫（library/）
    └── hooks\                 # 6 個守門 script（見下）
```

實際的 Angular 專案原始碼之後放在本目錄底下（`src/`、`angular.json` 等），與 `.claude/` 並列。

## 守門 hooks（本專案已接線）

| hook | 事件 | 擋什麼 |
| --- | --- | --- |
| `block-pen-file-ops.ps1` | PreToolUse `Bash\|PowerShell` | 以 shell 建立／開啟／文字寫入／刪除設計檔 |
| `require-analysis-before-draw.ps1` | PreToolUse `mcp__pencil-server__execute` | 跳過 `read` 就動筆（唯讀查詢會放行） |
| `figma-pen-prompt-reminder.ps1` | UserPromptSubmit | 不擋，只在提到 Figma 卻沒給設計檔路徑時提醒 |
| `enforce-commit-convention.ps1` | PreToolUse `Bash\|PowerShell` | commit 訊息不符 Conventional Commits |
| `check-comment-standards.ps1` | PostToolUse `Edit\|Write\|MultiEdit` | `.ts` 寫入後掃註解違規並要求當場修正（不擋寫入，只回饋） |
| `pen-readonly-guard.ps1` | PreToolUse `mcp__pencil-server__execute`（**只掛在 `storyboard-video-renderer` 的 frontmatter**，不在 settings.json） | 該子代理對 .pen 執行任何寫入函式 |

⚠️ hook 的 `.ps1` 要存成**帶 BOM 的 UTF-8**。Windows PowerShell 5.1 讀到沒有 BOM 的中文腳本會解析失敗；hook 因此安靜地不生效，也不會報錯。

⚠️ **hooks 是 session 啟動時載入快照的。** 這些是籌組當下寫進 `settings.json` 的，第一次在本專案開 Claude Code 就會生效；但日後若手動改了 `settings.json`，**要重啟 Claude Code 才算數**，而且沒生效時完全沒有錯誤訊息，只是安靜地不觸發。

⚠️ **`block-pen-file-ops` 會誤擋文件寫作。** 它比對的是指令字面，所以用 Bash heredoc 寫一份「內文提到設計檔」的 markdown 也會被擋（籌組本檔時就發生過）。遇到時改用 Write／Edit 工具即可 —— 那不是繞路，因為被禁止的是「用 shell 動設計檔」，寫 markdown 本來就該用專用工具。

## 專案級 MCP

- server 走 npx 釘版執行期（不裝 `node_modules`）；密鑰用 `${VAR}` 展開，**真值放 `.claude/settings.local.json` 的 `"env"` 區（不是 `.env`）**，改完要重啟 Claude Code。
  - ⚠️ **Claude Code 不會自動載入 `.env`。** 真值放 `.env` 的話，server 會收到字面的 `${VAR}`，而錯誤訊息看起來像「值填錯」。**辨識特徵：錯誤訊息裡出現 `${...}` 字面，就是展開沒生效，不是設定寫錯。**
  - 本專案目前兩個 server 都**不需要**任何密鑰，`.env.example` 是空樣板。
- 已納入：
  - `chrome-devtools`（`chrome-devtools-mcp@1.5.0`）—— 供 `common-user-browser` 驅動系統 Chrome 做 UI 檢視與截圖對稿。
  - `figma-bridge`（`@gethopp/figma-mcp-bridge`）—— 供 `figma-reader` 讀 Figma 設計稿。⚠️ 未釘版（抓最新），與「server 應釘版」的規範不一致；要團隊重現時改成 `@gethopp/figma-mcp-bridge@<版本>`。
  - `blender`（`mcp-for-blender@2.1.3`，走 `uvx`，已設 `DISABLE_TELEMETRY`）—— 讓 Claude 操作 Blender 做 3D 角色動畫與算圖。**本機要先裝 Blender（5.2）與 uv**，並在 Blender 的 Add-ons 啟用「Interface: MCP for Blender」。**使用時 Blender 要開著**：外掛預設「Auto-Start Server」，開啟 Blender 就會在 port 9876 等連線；沒連上時在 3D 視窗按 N →「MCP for Blender」分頁手動按啟動。⚠️ 這個 server 能在 Blender 裡執行任意 Python。
    - ⚠️ **剛裝完 uv 時 MCP 會連線失敗（CONNECTION_CLOSED）**：終端機若在安裝前就開著，Claude Code 繼承的 PATH 裡沒有 `uvx`。整個終端機重開即可；或用 `claude mcp add --scope local blender -e DISABLE_TELEMETRY=true -- "<uvx.exe 完整路徑>" mcp-for-blender@2.1.3` 加一條只在本機生效的覆寫（不進版控）。
- **地端 MCP（不在 `.mcp.json`）**：`pencil-server` —— 由 **Pencil Desktop app** 隨附，登錄在使用者層級（`~/.claude.json`），跨專案可用。**本機必須先安裝 Pencil Desktop**（`C:\Users\<user>\AppData\Local\Programs\Pencil\`）這個 MCP 才會出現，`pen-drawer` 與 `design-question-curator` 沒有它就完全動不了。
- 核准：`.claude/settings.local.json` 的 `enableAllProjectMcpServers: true`（不進版控）。

## 版控

- **`.claude/` 底下的骨架（agents／skills／commands／hooks／workflows／settings.json）都進版控。** clone 下來就是完整的工作區，不必再跑一次籌組腳本。`git status` 會多出幾十個檔，那是預期的，不是複製出錯。
- **只有兩類東西不進版控**：`.env*` 與 `.claude/settings.local.json`（後者裝的是 MCP 密鑰真值）。
- **骨架有兩條更新路徑，會打架**：重跑母工作區的 `scaffold-project.ps1`（以母版覆寫，`-Force` 時 `agents/`／`skills/` 整個清掉重建）vs 直接改本專案的檔案再 commit。**要在本專案客製骨架，就不要再重跑腳本**，否則客製會被無聲蓋掉。
- `.gitattributes` 把 `.claude/workflows/*.js` 釘成 LF。**不要拿掉** —— Windows 的 `core.autocrlf` 換成 CRLF 後，Workflow 工具會以 `script contains control characters` 拒絕執行那些 script。

## 語言規則

- 與使用者互動時全程使用繁體中文。
- 例外：程式碼識別名稱、專有名詞（API、CLI、JSON 等）、終端機指令與路徑、引用原文可保留原樣。

## 工作規範

1. **動手前先理解**：修改既有內容前，先閱讀相關檔案，確認脈絡再動作。
2. **小步前進**：偏好小而清晰的變更，方便檢視與回復。
3. **不臆測**：資訊不足時，先提問釐清，不要自行假設。
4. **忠實回報**：如實說明結果；測試失敗或步驟跳過都要明講。
5. **暫存檔案**：臨時檔案請放在系統暫存目錄，不要污染專案。
