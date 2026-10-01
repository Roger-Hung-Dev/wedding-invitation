---
name: fx-lab-preview
description: 特效實驗室的工作方法 —— 把使用者對新運鏡／轉場／片頭／片尾的文字描述，設計成可調參數的特效提案、用預覽樣板做成 claude artifact 網頁（16:9 舞台＋時間軸＋參數滑桿＋分鏡寫法）、存提案檔、等使用者裁決，裁決通過後把條目寫進 fx-* 特效 skills（狀態「已定案・待實作」）。發想新特效、預覽特效效果、或把使用者拍板的特效登記進特效庫時使用。
metadata:
  version: "1.0"
---

# 特效實驗室：描述 → 預覽 → 裁決 → 入庫

## 流程總覽

```
使用者描述 ──① 設計提案（2～3 個版本）
           ──② 做預覽網頁（assets/preview-template.html）→ 發布 artifact
           ──③ 寫提案檔 .claude/docs/fx-lab/{id}.md（狀態：待裁決）
           ──④ 回報連結＋要使用者決定的事 → 停
使用者裁決 ──⑤ 依裁決修改／再預覽，或入庫：寫進 fx-* SKILL.md（狀態：已定案・待實作）
```

⚠️ 子代理不能問使用者問題（AskUserQuestion 在子代理裡不可用）。**④ 一定要停下來回報**，由主控端轉給使用者；使用者的決定會在下一次呼叫時帶進來。⛔ 沒有收到明確的「通過」，不准寫進 fx-* skills。

## ① 設計提案

先讀既有特效庫，避免重複造輪子：

| 類別 | skill | 條目 id 慣例 |
| --- | --- | --- |
| 運鏡 | [[fx-camera-motion]] | `zoom`、`pan`… 英文小寫連字號 |
| 轉場 | [[fx-transition]] | `dissolve`、`flash`… |
| 片頭樣式 | [[fx-title-opening]] | `focus-pull`… |
| 片尾樣式 | [[fx-title-ending]] | `photo-thanks-monogram`… |

- 使用者的描述若和既有特效**只差參數**（例「慢一點的溶接」），直接告訴他用既有特效改參數，不必新增條目。
- 提案要能落到**產生器做得到的事**：產生器是 Python＋Pillow＋numpy 逐格合成（見 `storyboard-video-render`）。可以做：縮放、位移、模糊、混合、遮罩、漸層、調色、文字逐字排版。**做不到或很貴的**：3D 透視、粒子系統、光流、影片素材疊加 —— 遇到就提出可行的近似做法，並在提案裡明說差異。
- 每個提案給 **2～3 個版本**（例：時長短／長、方向、強度），讓使用者比較，不要只給一個。
- 一律寫清楚：分類、中文詞彙、分鏡寫法（含所有參數）、JSON、圖示（lucide 名稱）、適用版型、演算法、使用時機、已知坑；轉場另外標**交疊型或覆蓋型**。

**分鏡寫法的規則**（要能被正規式解析，見 `storyboard-video-render/scripts/fx_notation.py`）：

- 開頭是中文詞彙，後面接參數；參數帶單位（`%`、`s`、`px`）。
- 方向用 `→`／`←`；兩段時間用 `0.5+1.5s`。
- 不能和既有寫法的開頭詞彙衝突（例：新轉場不能叫「溶接…」）。
- 說明一律放全形括號，解析器會忽略。

## ② 預覽網頁

1. 複製 `assets/preview-template.html` 到 scratchpad（或系統暫存目錄），檔名 `fx-{id}.html`。
2. 載入 `artifact-design` skill 後再改檔（Artifact 的頁面規則）。
3. **只改樣板裡「fx-lab 只改這一段」那一塊**：`FX` 物件（名稱、參數、版本、寫法、JSON、render 函式）與 `PHOTOS`。
   - `render(ctx, t, P, img)` 在 960×540 畫布上畫一格，要**照提案的演算法寫**，不要畫一個「看起來像」的替代品 —— 使用者拍板的是這個畫面，產生器之後要照同一套演算法實作。
   - 從成片 px 換算用 `S`（0.5）。照片版型用工具函式 `drawPortrait`（A 版型）／`drawFull`（H 版型）。
   - 片頭片尾樣式要畫字：用 `ctx.font`＋`ctx.fillText`，字型用 Google Fonts 載入（Cormorant Garamond、Great Vibes、Noto Serif TC 都有）。
4. 示範照片：用 Python 把 `.claude/docs/design/wedding-photo/1800px/` 裡 2～4 張照片縮成長邊 640px、JPEG 品質 80，轉成 data URI 填進 `PHOTOS`（每張約 50～80KB）。找不到照片就留空，樣板會畫示意圖。
5. 發布：`Artifact`（`file_path` 指向該檔、`icon: "film"`、`description` 一句話說明這個特效）。同一個特效改版時用同一個檔案路徑重新發布，連結不變。

## ③ 提案檔

路徑：`.claude/docs/fx-lab/{分類}-{id}.md`。格式見 [references/proposal-format.md](references/proposal-format.md)。提案檔是裁決紀錄，**不刪除**；被否決的也留著（狀態改「否決」並寫理由），避免之後又提一樣的東西。

## ④ 回報（然後停）

回報給主控端，內容：

- artifact 連結
- 各版本差在哪（一句話一個）
- **要使用者決定的事**，寫成可以直接轉問的選項：例「採用哪一版？A 0.3s／B 0.6s／都不要」「中文詞彙用『光暈溶接』還是『柔光溶接』？」
- 已知限制（產生器做不到、和預覽會有差異的地方）

## ⑤ 裁決後

| 使用者說 | 做什麼 |
| --- | --- |
| 改某處再看 | 改 `FX`、重新發布同一個檔，提案檔加一筆修訂紀錄，回到 ④ |
| 否決 | 提案檔狀態改「否決」＋理由，結束 |
| 通過（指定版本） | 入庫（下面） |

**入庫**：在對應 fx-* SKILL.md 的「條目」區加一個條目，格式照該檔既有條目（`### \`id\` 中文名` ＋ 屬性表），並且：

- 狀態寫「**已定案・待實作**（提案：`.claude/docs/fx-lab/…md`）」
- 參數值用使用者通過的那一版
- 演算法寫到工程師不用看預覽也能實作的程度（含曲線、基準點、單位）
- 提案檔狀態改「已入庫」並記下入庫日期

⛔ **不要動** `storyboard-video-render/scripts/` 底下的程式 —— 實作與回歸驗證是 `storyboard-video-renderer` 的工作。也不要把狀態寫成「已實作」。

## 已知坑

- **預覽和成片不會逐像素相同**：瀏覽器 canvas 的模糊與縮放取樣和 Pillow 不同。提案裡要寫「以演算法描述為準」。
- canvas 的 `ctx.filter = "blur(Npx)"` 的 N 是標準差 σ（和 CSS 一樣）；Pencil 的模糊半徑是 2σ。寫進條目時統一用 Pencil 半徑，並註明換算。
- Artifact 不能載入外部圖片網址，照片一定要嵌成 data URI。整頁上限 16MB。
