# 開場影片剪接樣式庫（ZEPETO 3D 開場片）

字卡樣式、轉場、配色、字型、版面的預設素材庫（2026-10-12 建立，第一批：4 種字卡、7 種轉場、3 種配色、4 種字型、2 種版面）。

**重點：效果程式只有一份（`edit_styles.js`）。** 展示頁、render-settings 面板的動態預覽、正式剪接的逐格截圖都載入同一份，所以預覽看到的就是成品。

## 檔案

| 檔案 | 用途 |
|---|---|
| `catalog.json` | 樣式清單：每一筆的 id、名稱、說明、適合用在哪；配色色碼、字型（Google Fonts，皆 SIL OFL）；數值選項；預設值；展示用的示範節目 |
| `edit_styles.js` | 唯一的效果實作：字卡（`CAPTIONS`）、轉場（`TRANSITIONS`）、播放器 `EditStyles.player()`（`renderAt`／`seek`／`play`） |
| `page_template.html` | 頁面樣板：展示頁（view）、mod 預覽（preview）、逐格截圖（render）三種模式共用 |
| `build_showcase.py` | 產生器：檢查 catalog 的 id 都有實作 → 展示頁 `showcase/` → 本機預覽樣板 → 縮圖 `thumbs/` |
| `cdp_capture.py` | 本機 Chrome 無頭模式逐格截圖（只用 Python 內建＋已裝的 websockets，不用另外安裝） |
| `render_edit.py` | 正式剪接：逐格截圖 → ffmpeg 接成 mp4 |
| `thumbs/*.png` | 每個樣式一張縮圖（mod 面板顯示） |
| `showcase/` | 展示頁（Artifact）：https://claude.ai/artifact/VmCmdM4CKkNChZtqij1XQ1 ；`showcase/vid/*.mp4` 是素材，不進版控 |

## 怎麼用

- **看全部樣式**：展示頁（上面網址），可以切換、拖時間軸、複製設定。
- **選定**：render-settings 面板的「整支片設定」（`/render-settings film`）有一組「字卡與轉場」，選項從這裡的 `catalog.json` 讀；聚焦在一項時顯示縮圖，按 `p` 用瀏覽器看動態預覽。選好寫進 film.json 旁邊的 `edit.json`（只影響剪接，改了不會讓動畫被標成要重做）。
- **正式剪接**：
  ```bash
  python render_edit.py --settings <edit.json> --program <program.json> --out <資料夾> --size 1920x1080 --fps 30
  ```
  `program.json`：`{"shots": [{"id", "label", "src": 影片完整路徑, "dur"（鏡內秒數）, "in_s"（影片開頭跳過的秒數＝頭尾多做的）, "cap": [標題, 內容], "cue": [進場秒, 退場秒或 null]}]}`。`--program demo` 用示範節目。 最上層加 `"caption_hold": "until_next"`＝退場秒空白的字卡跨鏡留到下一張字卡進場前（左欄不空掉；舊的先退完、空 0.15 秒新的才進，不會兩張疊在一起；最後一張留到片尾）；不加的話，退場空白的字卡會在那一鏡畫面消失時直接消失。
  2026-10-12 實測：960×540 一格約 0.11 秒（Chrome 截圖），1080p 會再慢一些。
  配樂：加 `--audio <檔> --music-from <配樂從第幾秒取> --audio-at <片子第幾秒開始響> --fade-out <結尾淡出秒>`，另出 `edit_audio.mp4`（影像不重新編碼；片子比配樂長補靜音）。
- **分工**（2026-10-12 使用者決定）：剪接由導演端（zepeto-director）做；這個樣式庫、`render_edit.py` 由動畫端維護，要加功能找動畫端。

## 新增樣式

1. 先做成實驗版給使用者看（可以直接在 `edit_styles.js` 加一個新的鍵，用展示頁看），**使用者說可以才算入庫**。
2. 在 `catalog.json` 加一筆（id 和 `edit_styles.js` 的鍵同名，寫 `added` 日期）。
3. 跑 `python build_showcase.py`（會擋下「catalog 有、程式沒實作」的 id），再用 Artifact 發布 `showcase/index.html` 到上面同一個網址（`files` 帶 `vid/*.mp4`）。
4. mod 不用改：選項、說明、縮圖都從這裡讀。

## 已知限制

- 「側面捲動」「柱子擦過」的 2D 版只是示意：劇本裡這兩種要在 3D 裡做（連續跟拍、柱子真的從鏡頭前掃過），正式剪接時那兩個接點用 3D 渲好的畫面，不用 2D 效果。
- 示範節目的 B2 是坐餐桌喝紅酒的測試動畫代替，B2 做好後換掉 `catalog.json` 的 `demo`。
- 縮圖是靜態的，動態效果要按 `p` 或看展示頁。
