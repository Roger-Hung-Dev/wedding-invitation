# 網頁章節與資料來源

版型照新娘工作簿（https://claude.ai/artifact/12T6gowAFGaBVvSUAawPfa ）：左側固定目錄、右側五章，玫瑰灰色系，支援深色模式與手機寬度。

| 區塊 | 內容 | 來源 |
| --- | --- | --- |
| 標頭 | 標題、說明、4 個數字（動作通過／360°／服裝配件數／情境數） | `report.title/h1/lede`；通過數＝gen_page 依量測判定；配件數＝`costume.parts` 長度；情境數＝`scenes` 長度 |
| 01 身體完成度 | 全身 360°、臉部 360°、「做了什麼」清單、手勢圖、表情與腳 | `videos/turn_body.mp4`、`turn_face.mp4`；`report.s1_text`、`s1_facts`；`pictures/hands_sheet.jpg`、`face_feet.jpg` |
| 02 動作測試 | 每個動作一張卡：影片、通過／問題標籤、穿模、最大轉速、腳底、長度、接觸說明、修正前後 | `library/actions_catalog.json`（順序、名稱、備註）、`qa/metrics.json`、`qa/motion.json`、`qa/metrics_first.json`；`videos/actions/<代號>.mp4`、`pictures/posters/actions/<代號>.jpg` |
| 03 服裝 | 標題、說明、服裝 360°、和照片對照（正背各一組）、穿著服裝動起來 | `costume.name`、`report.s3_summary`（空的就用 `costume.summary`）；`videos/turn_costume.mp4`、`costume_moves.mp4`；`pictures/ref_front/back.jpg`、`costume_front/back.jpg` |
| 04 情境 | 每段一張卡：標題、便服/服裝標籤、影片、說明；有靜態圖再加一張圖庫卡 | `scenes`（id、title、desc、outfit）；`videos/scenes/<id>.mp4`；`pictures/scenes/*.png` |
| 還沒做到的 | 條列 | `report.limits` |

## 判定（gen_page.verdict）

- 穿模 > 5 mm 且 catalog 沒有 `contact_note` → 「穿模 N mm」
- 有渲染數字時：`body_vmax` > 15 → 「轉太快」、`body_jerk` > 6 → 「速度突變」
- 腳陷地 < −0.5 cm，或非騰空動作浮空 > 0.5 cm → 「腳沒貼地」
- 量測過但沒有影片 → 「還沒渲染」；沒量測 → 「未檢查」

## 改版型

改 `assets/page_template.html`。所有顏色都是 `:root` 變數（亮色）＋兩個深色區塊；新增欄位就在 gen_page 的 `rep` 表加一個 `{{佔位}}`。改完用新娘專案重產一次，確認五章都正常再發布。
