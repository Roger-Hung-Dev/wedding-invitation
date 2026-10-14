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
| 影片劇本發想 | 直呼 `film-director` | 描述／參考影片連結／參考網站 → 研究參考 → 2～4 個劇本提案 → 選擇題用 ask-panel 外掛送回主對話讓你選 → 修訂後存成劇本檔（`.claude/docs/storyboard/<片名>-script.md`） |
| ZEPETO 開場片・導演（一條龍） | `/zepeto-film-director-workflow <片名>`（新片：`新片：<描述／參考連結>`） | 劇本（film-director）→ 整支片設定面板（片子規格 film.json＋字卡與轉場 edit.json）→ 選角（zepeto-picker）→ 分鏡展開（workflow `zepeto-shot-breakdown`，每鏡一個子代理）→ 補素材（通知場景、服裝）→ 逐鏡發「動畫開工」給 zepeto-animation → 整支片審看 → 完整渲染 → 配樂與對拍 → 剪接輸出（`render_edit.py`）。看檔案與狀態紀錄判斷做到哪、從那步接著做；工具 `scripts/director.py`（status／lint／record／program） |
| 輪播影片分鏡 | 直呼 `storyboard-artist` | 照片＋配樂 → 規劃表 → 畫進 v2 分鏡稿 .pen 並標註特效 |
| 分鏡稿轉影片 | 直呼 `storyboard-video-renderer` | 指定 .pen → 輸出指定規格 mp4；補實作新特效 |
| 特效實驗室 | 直呼 `fx-lab` | 文字描述 → artifact 預覽 → 使用者裁決 → 寫進 fx-* 特效庫 |
| 3D 角色工作室（一條龍） | `/blender-studio` | 問齊參數 → 建角色 → 做情境 → 發布成果網頁（Claude Artifact） |
| 3D 角色建置 | 直呼 `blender-creator` | VRoid `.vroid`＋真人照片 → 01 身體完成度、02 動作測試、03 照片款服裝；事後改服裝 |
| 3D 角色情境 | 直呼 `blender-scenario-creator` | 情境描述＋角色專案 → 情境影片／圖片 |
| 動作庫擴充 | 直呼 `blender-animation-append` | 動作描述 → 寫進共用動作庫、檢查通過才入庫 |
| 整支片批次審看 | 主控端呼叫 workflow `film-scene-review` | 多幕 3D 情境一起渲出快速預覽 → 彙整成審看網頁 → 使用者一次給逐幕回饋 → 照回饋修 → 確認的幕才做完整品質 |
| 修某一幕的動作 | `/fix-animation <幕＋動作＋問題>` | 只拍那個部位的多角度近照＋客觀檢查數字 → 近照確認頁（Claude Artifact）→ 使用者指出哪裡不對就修、更新同一頁 → 說「可以」才渲整幕 |
| ZEPETO 挑選器（身體／大頭） | `/zepeto-bodies`、`/zepeto-heads`（都可加 `demo`、`multi`）；代理用工具 `mcp__zepeto-picker__pick_body`（`multi`、`released_only`）、`mcp__zepeto-picker__pick_head`（`multi`、`ready_only`） | 自製面板列出所有身體或大頭（資料來自 `list_bodies.py`、`list_heads.py`），選項不限 4 個、可複選，按 `y` 送出「我選 … 身體／頭：路徑」；服裝工作流選身體、身體工作流選頭時用它。專案外掛，見「專案外掛（mod）」 |
| ZEPETO 身體（一條龍） | `/zepeto-body-generation-workflow` | 選頭（挑選器面板，可複選）→ 比對頭有沒有更新 → 關閘門 → 依頭自動量尺寸長出照 ZEPETO 官方比例的 4.5 頭身身體（骨架＋前臂扭轉骨、手腳固定模板、頭身接口環、權重清理、膚色、UV、交接尺寸）→ 16 項出廠檢查＋近照自我審查 → 審看網頁 → 照回饋修 → 出廠（RELEASE.json＋產線狀態紀錄；黏土風版本換新版要先問導演）→ 通知衣服、動畫。2026-10-14 起黏土風做法已移除（封存 `D:/render-work/archive/zepeto-body-clay-route-20261014/`）；四肢技術見該 skill 的 `references/limbs.md` |
| ZEPETO 動畫製作 | `/zepeto-animation-generation-workflow <鏡號>`（或「改 B1：…」、或測試情境描述；導演端發「動畫開工：B2」時也走這條） | 一次做一鏡：讀分鏡展開檔（沒有就問齊自己寫一份）→ 比對上游 → 先上網查真人姿勢 → Mixamo 原樣套上 → 貼地鎖腳 → 道具、一開始就穿衣服 → 手指碰到就停 → 皮膚與衣服逐格量＋自我審查 → 改動作後先自我檢驗（腳／身體數字＋固定機位小片段，過了才交）→ 近照確認頁（附短片，同一頁逐版更新）→ 說可以才定案（狀態紀錄、樣張、通知導演端）。共用程式在該 skill 的 `scripts/`（zanim*），每一鏡的程式與定案參數在 `.claude/docs/data/blender/zepeto/anim/<片名>/<鏡>/` |
| ZEPETO 穿戴物品 | `/zepeto-clothing-generation-workflow <描述>`（可 Alt+V 貼參考照片或 @圖片檔） | 開身體選單面板勾要穿在誰身上（可複選、只列已出廠的；面板沒載入時退回內建選單，不用自己找檔）→ 分析參考 → 用共用配方寫成 `outfit.py` → 背景 Blender 從身體長出衣服、鞋子、配件並綁骨架 → 近照＋Mixamo 動作穿模檢查 → 審看網頁 → 照回饋修；素材庫在 `library/outfits-zepeto/`。2026-10-14 起照參考照刻細節＋寫實布料（取代黏土風；配方 `garment_detail.py`，會垂的布用布料模擬在站姿垂一次定形）；大蓬裙的手交給動畫端（提裙、手搭裙側），交接資料寫在 `outfit.json` 的 `anim_handoff` |
| ZEPETO 黏土風場景與道具 | `/zepeto-scenes-generation-workflow <情境描述>`（可 Alt+V 貼參考照片或 @圖片檔） | 拆出要的景與道具 → 先用素材庫現有的，缺的照來源清單 `sources.md` 上網找免費素材（下載前先問）或用 Blender 自建 → 加進素材庫 `library/props-zepeto/`、組場景示意、更新展示頁；新查到的素材網站一律記進 `sources.md` |
| ZEPETO 大頭（一條龍） | `/zepeto-character-face-generation-workflow`（Alt+V 貼照片或 @照片檔；沒有照片的配角可以只給文字設定） | 真人大頭照（或文字設定）→ ZEPETO 風 3D 頭模型（OBJ；V 字臉、杏仁眼、光滑亮澤）→ 後處理成一打開就能看的 .blend＋四角度驗收圖 → 可動臉（AI 頭本身當成品：ARKit 52 表情＋臉部控制骨架＋脖子修細到頭寬 38%＋長髮避開身體＋自動檢查報告，含「ZEPETO 比例」量測）。**改了大頭產線程式要跑回歸測試** `zepeto-face-rig/scripts/regress/regress.py`（快速約 1 分鐘、`--full` 約 15 分鐘；測試組與加頭規則見該 skill 的 SKILL.md） |
| ZEPETO 大頭生成 | 直呼 `zepeto-analyze-photo-3d-model` | 照片 → 五官分析 → Hyper3D Rodin 文字生成（不上傳照片）→ 三角度檢查 → OBJ＋貼圖 |
| ZEPETO 大頭後處理 | 直呼 `zepeto-avatar-crafter` | OBJ → 置中、焊接頂點、平滑、亮澤材質、三點燈光 → .blend＋驗收圖 |
| ZEPETO 可動臉（ARKit 52） | 直呼 `zepeto-face-rigger`（或 skill `zepeto-face-rig` 的 `scripts/run_face_rig.py`） | 上一步的 .blend → AI 網格路線：模板只當籠子算 52 表情再轉移到 AI 頭、照唇線切嘴縫＋自建口腔袋、材質眼睛、控制骨架、整理成身體端的交接格式、照這顆頭試接一副身體來調長髮 → `head_rig.blend`＋自動檢查報告＋預覽圖，約 5 分鐘 |

### ZEPETO 大頭產線的分工（三個子代理＋一條 workflow）

```
/zepeto-character-face-generation-workflow（主控端找照片路徑、問名稱）──▶ workflow zepeto-character-face-generation
    ├─ zepeto-analyze-photo-3d-model ─▶ zepeto/<名稱>/stylized_face_generated.obj＋貼圖、analysis.md（在開著的 Blender 另開 ZEPETO_WORK 場景，做完刪掉）
    ├─ zepeto-avatar-crafter ─────────▶ zepeto/<名稱>/stylized_face_zepeto.blend、qa/（只用背景 Blender）
    └─ zepeto-face-rigger ────────────▶ zepeto/<名稱>/rig/head_rig.blend、rig/preview/（只用背景 Blender）
```

- 資料在 `.claude/docs/data/blender/zepeto/<名稱>/`；腳本與交接格式在 skill `zepeto-character-face-generation-workflow` 的 `scripts/`、`references/handoff.md`。
- **Alt+V 貼上的圖子代理看不到**：主控端要先換成檔案路徑（Claude Code 存在本 session 暫存資料夾的 `images\N.png`）。
- 生成用 Hyper3D Rodin 的**免費試用額度**（每跑一次 1～3 次），**只送文字描述、不上傳照片**。生成時不要給 `bbox_condition`、描述不寫否定句（兩次馬尾的教訓）。
- 材質預設值是亮澤（2026-10-14 起；使用者 2026-10-13 看比較圖選亮澤）：透光權重 0.15、半徑 (1.0, 0.2, 0.1)、縮放 0.05、粗糙度 0.5，不加 Coat（整張臉會泛白）。舊的霧面黏土值（0.3／0.75）已停用。
- 新郎第一次手動做的頭（2026-10-11，產線建好前的版本，原本放在專案根目錄 `stylized_face_*`）2026-10-14 使用者決定不用了，整包搬到 `D:/render-work/archive/groom-head-legacy-20261014/`（含 `stylized_face_rig/head_rig.blend`，sha `065b90ee7f39…` 沒變）。新郎之後用新流程重做。
- **要能眨眼張嘴、做 ARKit 52 表情**：AI 生成的頭五官是畫在表面的，推拉網格做不出來（那次測試 `stylized_face_expressions/` 也在上面的封存裡）。走 skill `zepeto-face-rig`（一條龍第三段，`stages` 預設 `['generate','craft','rig']`）。
  - **2026-10-14 起是 AI 網格路線**：AI 頭本身當成品（外型、貼圖原封不動），通用模板頭（LucaDrech，CC BY 4.0，**對外分享要標註**，見 `templates/cartoon-head-lucadrech/ATTRIBUTION.md`）只當「籠子」算出 52 個表情再轉移過去；牙齒、舌頭來自模板。說明與坑在該 skill 的 `references/ai-mesh-route.md`。
  - 舊路線（模板當成品、AI 的樣子轉印上去 → 包子臉、眼線對不上）已刪，程式封存在 `D:/render-work/archive/zepeto-face-rig-old-route-20261014/`。新郎（產線建好前手動做的，已封存，見上）、新娘 v4、攝影師 v1 是舊路線做的，成品沒動。
  - 驗證過新娘、攝影師兩張臉；第三種臉型第一次跑，自動檢查報告（`rig/check/report.html`）和預覽圖要逐張看。
- **頭和身體的接縫：標準脖子接口環**（2026-10-14 起）：頭端 `neck_ring.py` 在脖子做出一圈 48 點寫進 Head（點屬性 `neck_ring` 1～48＋Head 物件的自訂屬性 `neck_ring_ver`、`neck_ring_n`、`neck_ring_z`、`neck_ring_yc`、`neck_chin_bottom`，Head 本地座標；環的高度是先找下巴底、再往下找脖子），身體端 `body_build.py` 用 `neck_chin_bottom` 當下巴放頭（V 字長下巴自己量會量到下巴前緣、頭被放低放大）、照抄環的座標接上，兩邊點對點重合、看不出接縫；Head 有 `neck_ring_ver` 才走新路，舊頭照舊。環的高度、點數、順序是兩邊的合約，**改了要通知對方一起改**；合約與坑見 skill `zepeto-face-rig` 的 `references/ai-mesh-route.md`「頭身接縫」。

### 3D 角色產線的分工（三個子代理＋一條 workflow）

```
/blender-studio（主控端問齊參數）──▶ workflow blender-character-studio
    ├─ blender-creator ──────────▶ projects/<名稱>/（.blend、qa/、pictures/、videos/）
    ├─ blender-scenario-creator ─▶ 同一個專案的 videos/scenes、pictures/scenes（每段情境一次）
    └─ 發布成果網頁（blender-report-page）
blender-animation-append ──▶ 共用動作庫（blender-motion-library 的 actions_custom.py ＋ library/actions_catalog.json）
```

- 資料都在 `.claude/docs/data/blender/`：`projects/<名稱>/` 一個角色一個資料夾；`library/` 是預設資料庫（手勢、表情、腳、30 種動作、粉色蓬裙禮服，來自範例專案 `projects/bride`）。資料夾說明見那裡的 `README.md`。
- **穿戴物品素材庫**：`library/outfits-zepeto/`（每套服裝一個資料夾：`outfit.py`＋`outfit.json`＋`refs/`＋`previews/`）。配方與產生器在 skill `zepeto-clothing-generation-workflow` 的 `scripts/`（`garment_detail.py`＝照參考照刻細節＋寫實布料，新衣服用；`garment_lib.py`＝基本動作與舊黏土風配方；`outfit_build.py`、`outfit_page.py`）。衣服每次都從身體重新長出來，身體出廠新版本後重跑即可；`.blend` 與檢查圖在 `D:/render-work/zepeto-costume/<服裝>/<身體>/`。身體只用已出廠的（身體出廠閘門 hook `require-body-release.ps1` 會擋），Blender 直接開 body.blend、另存 outfit.blend，絕不存回原檔。
- **場景與道具素材庫**：`library/props-zepeto/`（ZEPETO 黏土風，45 樣＋8 個場景示意）。情境要道具時先查 `catalog.json`，用 `use_props.py` 的 `place_prop()` 載入；要新增道具或場景走 `/zepeto-scenes-generation-workflow`（自建的寫 `build_props.py` 的 `@item`、下載的寫 `external_items.py` 的 `ext_item`、場景寫 `scenes/<key>.py`）。素材網站清單與查詢紀錄在 `sources.md`、CC BY 標註在 `ATTRIBUTION.md`。`.blend`、下載原檔、參考照片不進版控，clone 後先跑一次 `build_props.py`（約 1 分鐘）。
- **臉部模型只收 `.vroid`，但 VRoid MCP 不能匯出 VRM。** 使用者要先在 VRoid Studio 開 .vroid → 按 F8 → 存成 VRM 1.0（放在 .vroid 旁邊同檔名）。沒有 VRM 時 `blender-creator` 會停下來回報，不會硬做。
- **Blender 要開著**（MCP for Blender 外掛啟動）。VRM 匯入只能在 GUI Blender；長時間渲染改用背景 Blender（`blender.exe -b … -P bl_cli.py`），可並行、不受 MCP 120 秒限制。
- **調整動作或情境時走快速迭代**：調整中只交低解析、無物理、只渲改到片段的快速預覽＋多角度檢查圖，一次收齊問題再修；使用者確認後才做完整渲染。規範在 `blender-motion-library` 的 `references/fast-iteration.md`，三個 Blender 子代理的定義都已寫入。
- **一支片有好幾幕要一起看時**（例：開場影片各幕），由主控端呼叫 workflow `film-scene-review`：每幕一個情境子代理並行出快速預覽，彙整成一個審看網頁，使用者一次給「第 N 幕：…」的回饋，再照回饋跑下一輪。規範在 `fast-iteration.md` §5。
- **動作來源與兩關審看（2026-10-10 起）**：角色動作一律用 Mixamo 現成動畫原樣套上（不用 CMU；劇情不改、挑最接近的、套用後可微調但不破壞動作結構）。多幕影片分三關，每一關每一幕都確認了才進下一關，最後才完整渲染：
  1. 骨骼動作：Mixamo 原樣，只選段、接段、站位（3D 骨架播放器，workflow `stage: 'skeleton'`）。
  2. 正式版骨骼動作：為了劇情要求的骨骼微調，例如餵食、新郎比 YA，灰線對照 Mixamo 原樣（`stage: 'final'`）。
  3. 低畫質預覽（`stage: 'preview'`）。

  三關的審看網頁都要有逐幕回覆框＋Ctrl+V 貼圖，回饋存在網頁的 db，主控端直接讀。規範在 `fast-iteration.md` §0、§0.5。
- 影格 png 放 `D:\render-work\blender-work\<名稱>\`（C 槽容易滿，`blender_env.py` 預設就指這裡；環境變數 `BLENDER_WORK_ROOT` 可覆寫），專案裡只放 mp4／jpg 成品。`.blend` 與 `source/`（使用者的原檔與照片）不進版控。

### 輪播影片產線的分工（三個子代理）

```
fx-lab ──（裁決通過）──▶ fx-* 特效技術文件 ◀── 兩邊都照這裡的寫法與演算法
                              │
storyboard-artist ──畫──▶ v2 分鏡稿 .pen ──讀──▶ storyboard-video-renderer ──▶ mp4
```

- **格式契約**是 `storyboard-pen-format`：分鏡稿怎麼命名、每個欄位怎麼寫。畫稿與讀稿兩邊都以它為準。
- 產生器程式在 `.claude/skills/storyboard-video-render/scripts/`。它已用第 2 版成片逐格驗證：1,569 個時間點像素完全相同。2026-10-13 修了「推拉運鏡在轉場重疊時縮到 100% 以下、露出黑邊」的問題，之後只有那些轉場窗的格子和第 2 版不同（第 2 版本身在 2:13 附近有這個黑框）。
- 子代理不能問使用者問題。需要裁決時（例如 fx-lab 的預覽），子代理會停下來回報；主控端轉問使用者後，再把結果帶回去。
- `wedding-photo-slideshow.pen` 已升級成 v2，第 3 版成片（I Won't Give Up，4:00）就是用新產線從它產生的。其他 **v1 格式**的分鏡稿產生器不能直接讀（缺版型欄與特效參數），要用新產線重產，先請 `storyboard-artist` 以 `upgrade` 模式升級成 v2。
- **照片片裡要有 3D 角色互動**（照片與運鏡仍是 2D）：鏡頭卡多畫一列 `列-角色`（寫法見 `storyboard-pen-format` §4.1，動作用動作庫代號）。解析器會檢查並寫進 `storyboard.json` 的 `shots[].characters`；**渲染器還不會合成角色**，之後要補「Blender 渲染透明角色片段 → 疊到照片上」這一段。

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
- `zepeto-analyze-photo-3d-model`：ZEPETO 大頭生成端（風格分析 → Hyper3D 生成 → 存 OBJ）。工具含整個 `mcp__blender`。
- `zepeto-avatar-crafter`：ZEPETO 大頭後處理端（匯入置中 → 網格修復 → 亮澤材質 → .blend＋驗收圖），只用背景 Blender。
  - 兩者共用 skill `zepeto-character-face-generation-workflow` 底下的 `scripts/` 與 `references/handoff.md`（不預載，用到時讀）。
- `zepeto-face-rigger`：ZEPETO 大頭可動臉端（跑 AI 網格路線一鍵產線 `run_face_rig.py` → 看自動檢查報告與預覽圖 → 自動偵測不準時改這張臉的 `face.json` 重跑），只用背景 Blender、不改產線程式。
  - 對應 skill：`zepeto-face-rig`（產線腳本與坑）；交接格式同上 `handoff.md`。
- `film-director`：影片導演・劇本發想（描述、參考影片、參考網站 → 劇本提案 → 修訂 → 劇本檔）。不碰 3D 與各產線。
  - 子代理沒有 AskUserQuestion（官方會從所有子代理拿掉），它用使用者層級外掛 `ask-panel` 的 `mcp__ask-panel__ask_user` 提問：問題送回主對話，主控端收到「［ask-panel］…請呼叫 relay」訊息時**立刻呼叫 `mcp__ask-panel__relay`**，問答框就會開給使用者，答案自動交回子代理。

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
    ├── agents\                # 15 個（含 film-director）：front-end-angular-engineer、code-reviewer、
    │                          #        figma-reader、pen-drawer、design-question-curator、
    │                          #        storyboard-artist、storyboard-video-renderer、fx-lab、
    │                          #        blender-creator、blender-scenario-creator、blender-animation-append、
    │                          #        zepeto-analyze-photo-3d-model、zepeto-avatar-crafter、zepeto-face-rigger
    ├── skills\                # 36 個（angular-* 6、ui-bootstrap5、common-user-browser、
    │                          #        git-commit-convention、design-* 與 pen-* 8、
    │                          #        storyboard-* 3、fx-* 5、blender-* 5、
    │                          #        zepeto-character-face-generation-workflow、zepeto-face-rig、
    │                          #        zepeto-clothing-generation-workflow、zepeto-body-generation-workflow、
    │                          #        zepeto-animation-generation-workflow、zepeto-film-director-workflow）
    ├── commands\
    │   ├── design-lead.md     # 設計稿產線組長入口 /design-lead
    │   ├── fix-animation.md   # 修 3D 影片某一幕的動作：近照確認頁 → 使用者指出要修哪裡 → 確認才渲整幕
    │   ├── git-worktree-create.md  # 以當前分支另開 worktree（分支名＋-WT，目錄在 repo 上一層）
    │   ├── git-worktree-list.md    # 列出所有 worktree 與推導的來源分支
    │   ├── git-worktree-merge.md   # worktree 合併回來源分支（回 main 時問部署、不部署自動加 [CF-Pages-Skip]）→ 確認後刪 worktree
    │   └── zepeto-scenes-generation-workflow.md  # 黏土風場景與道具：描述／參考照片 → 素材庫重用、找免費素材或自建 → 場景示意＋展示頁
    ├── workflows\
    │   ├── figma-pen-team.js  # 產線編排（read／draw-flow／draw-screen／draw-scenario／annotate）
    │   ├── pen-export-png.js  # 下游交付：設計檔 → png ＋ _index.md ＋ _layout-spec.md
    │   ├── blender-character-studio.js  # 3D 角色：建角色 → 情境 → 發布成果網頁
    │   ├── film-scene-review.js         # 多幕 3D 影片批次審看：各幕快速預覽／修正 → 審看網頁
    │   ├── zepeto-character-face-generation.js  # ZEPETO 大頭：生成 OBJ → 後處理 .blend → 可動臉
    │   └── zepeto-shot-breakdown.js  # ZEPETO 開場片分鏡展開：每鏡一個子代理寫分鏡展開檔 → 整支片銜接檢查＋缺件清單
    ├── mods\                  # 專案外掛（mod）：zepeto-picker（見「專案外掛（mod）」）
    ├── docs\data\blender\     # 3D 角色專案（projects/）、預設資料庫（library/）、ZEPETO 大頭（zepeto/）
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
| `require-body-release.ps1` | PreToolUse `Bash\|PowerShell\|mcp__blender__execute_blender_code` | 身體出廠閘門：ZEPETO 身體沒出廠時，用 Blender 跑動畫或服裝（指令含 `zepeto-anim`、`zepeto-costume`，或 `-P` 跑 `suit_build`、`cuff_probe`、`outfit_build`、`b12_*`）。**只擋用到的那副身體**：指令裡點名了哪幾副（`build/<人>/body.blend` 路徑、服裝 `OUT=…/zepeto-costume/<服裝>/<人>`、或 `BODY=<人>`，可逗號分開），就只核對那幾副在 `D:/render-work/zepeto-body/build/RELEASE.json` 的 `bodies` 裡、status 是 `released`（那副沒寫 status 的舊格式改看總 `status`）、sha256 對得上；點名的身體不在 `bodies` 裡也擋。沒點名就照舊看總 `status`＋全部 sha256。紀錄不存在或讀不懂一律擋。⚠️ 腳本內部偷開沒點名的身體會漏掉：腳本會開哪幾副，指令就要全部點名。只讀檔不擋；身體端自己做身體（只碰 `zepeto-body`）不擋 |

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

## 專案外掛（mod）

- `zepeto-picker`：ZEPETO 挑選器（身體、大頭選單）。原始碼在 `.claude/mods/zepeto-picker/`，由 ZEPETO 身體端（zepeto-body）維護。2026-10-12 由 `zepeto-body-menu` 改名（工具全名跟著變成 `mcp__zepeto-picker__…`）。
  - 安裝在專案層級：`.claude/settings.json` 的 `extraKnownMarketplaces`（`wedding-invitation-mods` → `.claude/mods/`）＋ `enabledPlugins`。
  - Claude Code 直接讀這個資料夾。改了檔案後打 `/reload-plugins` 就生效，不用重開。
  - 外掛以你的權限執行，不受沙箱限制。
- `render-settings`：渲染參數面板（2026-10-12，動畫端維護）。原始碼在 `.claude/mods/render-settings/`。
  - `/render-settings [film|render] [demo]`；工具 `mcp__render-settings__pick_film_settings`（整支片設定：畫面方向、fps、前後多渲、背景、換景遮擋、字卡留白，劇本定案後由導演端問一次 → `<片名>-breakdown/film.json`）、`mcp__render-settings__pick_render_settings`（完整渲染設定：解析度最高 4K、取樣、陰影、效果、專家選項、要渲哪幾鏡，所有鏡定案後由動畫端問）。
  - 按 y 時有給 `out` 就寫檔，再送出「渲染參數（…）：<片名>」＋ JSON 的使用者訊息；格式寫在 `register.js` 的 `message()` 上方註解，改了要通知導演端。
  - 「整支片設定」另有一組「字卡與轉場」：選項、說明、縮圖都從**剪接樣式庫** `.claude/docs/data/blender/library/edit-styles-zepeto/` 讀（新增樣式不用改 mod），按 p 用瀏覽器看動態預覽，選好寫進 film.json 旁邊的 `edit.json`（只影響剪接；film.json 是片子規格、影響動畫）。樣式庫的效果程式只有一份 `edit_styles.js`，展示頁、預覽、正式剪接（`render_edit.py` 用本機 Chrome 逐格截圖）共用，所以預覽＝成品。展示頁：https://claude.ai/artifact/VmCmdM4CKkNChZtqij1XQ1 。說明見該資料夾 `README.md`。
  - 按 t 試渲：背景 Blender 用目前的值渲一格「樣張」顯示在面板裡（約 12 秒）；「試渲鏡頭／試渲畫面」讀樣張總表 `D:/render-work/zepeto-anim/sample/samples.json`。**動畫端每一鏡定案時要存樣張並登記**（做法見動畫 skill `zepeto-animation-generation-workflow` 的 SKILL.md 定案步驟：`zanim_sample` 的 bake／save／register；`D:/render-work/zepeto-anim/README.md` 是 10-12 搬進 skill 前的封存）。各參數的效果比較頁：https://claude.ai/artifact/KaC1ZqHyfqnJgbrULR3dq9
- ⚠️ 登記的外掛位置是**完整路徑**（`D:\SideProject\wedding-invitation\.claude\mods`）。專案 clone 到別的位置或別台電腦，要改這一行，或在那邊重跑兩行指令：
  - `claude plugin marketplace add ./.claude/mods --scope project`
  - `claude plugin install zepeto-picker@wedding-invitation-mods --scope project`
- 送出訊息的格式是和服裝工作流約定的，要改先通知服裝端。目前的格式寫在 `register.js` 的 `message()` 上方註解。

## 版控

- **`.claude/` 底下的骨架（agents／skills／commands／hooks／workflows／settings.json）都進版控。** clone 下來就是完整的工作區，不必再跑一次籌組腳本。`git status` 會多出幾十個檔，那是預期的，不是複製出錯。
- **骨架裡只有兩類東西不進版控**：`.env*` 與 `.claude/settings.local.json`（後者裝的是 MCP 密鑰真值）。資料區另外排除角色專案的 `.blend`／`source/`、捏臉 VRM 與真人照片原檔、動態分鏡預覽 mp4（見 `.gitignore`）。
- **骨架有兩條更新路徑，會打架**：重跑母工作區的 `scaffold-project.ps1`（以母版覆寫，`-Force` 時 `agents/`／`skills/` 整個清掉重建）vs 直接改本專案的檔案再 commit。**要在本專案客製骨架，就不要再重跑腳本**，否則客製會被無聲蓋掉。
- `.gitattributes` 把 `.claude/workflows/*.js` 釘成 LF。**不要拿掉** —— Windows 的 `core.autocrlf` 換成 CRLF 後，Workflow 工具會以 `script contains control characters` 拒絕執行那些 script。

### 合併回 main 與部署（必守）

- **push 到 `main` 就會觸發 Cloudflare Pages 部署正式喜帖網站**（https://roger-amy-wedding.pages.dev/）。所以：
- **合併回 `main` 之前一律先問使用者**，就算使用者先前說過「commit」也一樣 —— 要問兩件事：
  1. 要不要合併回 `main`（還是先留在分支）。
  2. 這次要不要部署。
- **不部署時**：push 上去的最新一筆 commit（合併時就是合併 commit）訊息**開頭**必須是 `[CF-Pages-Skip]`，例：`[CF-Pages-Skip] Merge branch 'feat/xxx'`。
  - Cloudflare 只認**寫在訊息最開頭**的標記（不分大小寫；`[CI Skip]`、`[Skip CI]` 等也可以），寫在中間或結尾無效。
  - 合併要用 `git merge --no-ff -F <訊息檔>` 產生合併 commit；快轉合併（fast-forward）的話，最新一筆是分支上的普通 commit，沒有標記就會部署。
  - 這則訊息無法同時符合 Conventional Commits 格式，是唯一允許的例外；內文要寫明「依使用者要求不部署」。commit 格式 hook 不檢查 `-F` 讀入的訊息，所以不會被擋。
  - push 後確認沒部署：GitHub 上該 commit 的 check runs 不應出現「Cloudflare Pages」（`https://api.github.com/repos/Roger-Hung-Dev/wedding-invitation/commits/<sha>/check-runs`）。
- **要部署時**：照一般 Conventional Commits 訊息合併即可，push 後同一個網址確認「Cloudflare Pages」檢查是 success。

### 共用工作目錄與 worktree

- **本專案的主工作目錄由多個 session 共用**（大頭、身體、服裝、動畫、場景、導演…），平常就有幾十筆各端沒 commit 的檔。
  - **不要在主工作目錄 checkout／switch 分支**：只存在於目前分支的已 commit 檔會從磁碟消失，別的 session 正在用的檔就不見了。
  - 各端要 commit 到自己的分支時，用暫時 index＋`git commit-tree`（或 `git merge-tree --write-tree`）組 commit、`git update-ref` 移分支，不動共用的 index 和 HEAD；合併回 main 也一樣，`update-ref` 要帶舊值核對。
  - 要在獨立分支上大改時，改用 worktree：`/git-worktree-create` 另開資料夾、`/git-worktree-list` 查看、`/git-worktree-merge` 合併回來源分支並清掉。新 worktree 只有已 commit 的檔，沒 commit 的檔與 `.gitignore` 排除的檔（`settings.local.json`、`.blend`、參考照片）不會跟過去。
  - `/git-worktree-merge` 已照上面「合併回 main 與部署」改過：合併回 main 時會問要不要部署、不部署自動加 `[CF-Pages-Skip]`；主工作目錄不在來源分支上就停下來，不會自己切過去。

## 語言規則

- 與使用者互動時全程使用繁體中文。
- 例外：程式碼識別名稱、專有名詞（API、CLI、JSON 等）、終端機指令與路徑、引用原文可保留原樣。

## 工作規範

1. **動手前先理解**：修改既有內容前，先閱讀相關檔案，確認脈絡再動作。
2. **小步前進**：偏好小而清晰的變更，方便檢視與回復。
3. **不臆測**：資訊不足時，先提問釐清，不要自行假設。
4. **忠實回報**：如實說明結果；測試失敗或步驟跳過都要明講。
5. **暫存檔案**：臨時檔案請放在系統暫存目錄，不要污染專案。
