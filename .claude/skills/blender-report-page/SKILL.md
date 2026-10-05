---
name: blender-report-page
description: 把 Blender 角色專案的成果做成 Claude Artifact 網頁 —— export_media.py 把暫存影格轉成專案裡的 mp4／jpg，gen_page.py 依 project.json 與量測檔產生「01 身體完成度／02 動作測試／03 服裝／04 情境／還沒做到的」五章網頁（版型照新娘工作簿），再用 Artifact 工具連同影片圖片一起發布或更新同一個網址。workflow 最後一步、或使用者要看某個角色專案的成品時使用。
compatibility: Python 3.10+（Pillow）、ffmpeg、Artifact 工具
metadata:
  version: "1.0"
  verified: 2026-10-04 新娘專案重新產生的頁面與原版（https://claude.ai/artifact/12T6gowAFGaBVvSUAawPfa）章節、數字一致（30/30）
---

# 成果網頁

```
WORK 影格 ──① export_media.py ──▶ PROJ/videos、PROJ/pictures
project.json ＋ qa/*.json ＋ library/actions_catalog.json ──② gen_page.py ──▶ PROJ/report.html ＋ PROJ/report_files.json
                                                                ──③ Artifact 發布（file_path＝report.html、root＝PROJ、files＝report_files.json）
```

腳本在 `scripts/`，版型在 `assets/page_template.html`。章節與每格資料來源見 [references/page-sections.md](references/page-sections.md)。

## 步驟

1. **轉檔**：`python scripts/export_media.py --project <PROJ>`。看輸出的 `skipped`：還在渲染的不要硬發布，等它好或在回報說明。
2. **補文字**（project.json 的 `report`）：`s1_text`／`s1_facts`（這個角色實際補了什麼）、`s3_summary`、`limits`（還沒做到的，照實寫）、`title`／`h1`／`lede`（選填）。⛔ 文字只寫做了的事；數字一律由程式從量測檔帶出，不手抄。
3. **產生**：`python scripts/gen_page.py --project <PROJ>`，輸出一行 JSON（檔案數、動作通過數、情境數）。
4. **看一次**：用瀏覽器開 `PROJ/report.html`（本機路徑可以直接播影片），看一張截圖確認沒有破版，有問題修一次就好。
5. **發布**：Artifact 工具 `publish`：
   - `file_path`＝`PROJ/report.html`、`root`＝`PROJ`、`files`＝讀 `report_files.json` 的內容（物件 `{發布路徑: 來源路徑}`）。
   - 第一次發布帶 `icon`（例 `sparkle`）與一句 `description`；之後更新同一個網址要帶 `url`（存在 `project.json.report.artifact_url`），不要再帶 icon。
   - 拿掉不再使用的檔案：在 `files` 裡把那個發布路徑設成 `null`。
6. **記網址**：把 artifact 網址寫回 `project.json.report.artifact_url`。

⚠️ 網頁裡有使用者的真人照片（和照片對照那格）。Artifact 預設私人；回報時提醒「只有本人看得到，分享要從頁面的 Share 選單開」。
