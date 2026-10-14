# 分鏡展開怎麼寫（給分鏡子代理）

一鏡一份，照範本 `.claude/docs/storyboard/_breakdown-template.md` 寫到 `.claude/docs/storyboard/<片名>-breakdown/<鏡號小寫>.md`（經過段 `B1→B2` 寫成 `b1_b2.md`）。動畫端用程式（`zanim_spec.py`）讀這份檔：**二級標題、順序、三張表的表頭一個字都不能改**，沒內容寫「（無）」。

寫完一定跑 `python .claude/skills/zepeto-film-director-workflow/scripts/director.py lint <片名> --shot <鏡號>`，exit 0 才算寫完；錯誤照訊息修。

## 要先讀的

| 東西 | 位置 | 用來 |
| --- | --- | --- |
| 劇本 | `.claude/docs/storyboard/<片名>-script.md` | 這一鏡的秒數、地點、標題、內容，以及「已定案的細節」「轉場與字卡」（例：哪兩鏡之間是柱子遮擋） |
| 片子規格 | `<片名>-breakdown/film.json` | 畫面方向 `aspect`、字卡留白 `caption_safe`（左欄留 40% → 角色與主要動作要擺在右側 60%） |
| 字卡與轉場 | `<片名>-breakdown/edit.json`、`.claude/docs/data/blender/library/edit-styles-zepeto/catalog.json` | 轉場名稱只能用 catalog 的 `transitions[].name`（或 id）；字卡樣式的進場時間長度 |
| 道具與場景素材庫 | `.claude/docs/data/blender/library/props-zepeto/catalog.json`、`scenes/` | 有的寫 key，沒有的寫「缺：<中文描述>」 |
| 服裝素材庫 | `.claude/docs/data/blender/library/outfits-zepeto/catalog.json` | 角色穿什麼；沒有的寫進「道具與場景」的「缺：服裝 <描述>」 |
| 已定案的動畫 | `.claude/docs/data/blender/zepeto/pipeline/status/anim/*.json`、`zepeto/anim/<片名>/<鏡>/final.json` | 上一鏡定案時角色停在哪、往哪走，這一鏡要接得上 |

## 每一段的寫法

- **基本**：秒數照劇本；上一鏡／下一鏡照播放順序（經過段也算一鏡，例：B1 的下一鏡是 `B1→B2`、`B1→B2` 的下一鏡是 B2）；轉場寫「接上一鏡」用哪個（連續跟拍寫「側面捲動（不切）」）。
- **鏡頭**：從 0 秒寫到這一鏡結束，不留空檔。景別只用遠景／全景／中景／近景／特寫；機位寫相對角色的方向與高度（「正面偏左 30°、胸口高」）；同一段連續場景的鏡，機位與運鏡要延續（側面跟拍就一直側面跟拍）。
- **角色與動作**：動作用白話寫「誰在第幾秒做什麼」，再列 1～3 個 Mixamo 候選動畫名稱（動畫端最後決定，劇情不改、挑最接近的）。一鏡開頭要接上一鏡結尾的姿勢與位置；有明確起點的動作（門打開的那一刻）在「備註」寫「起點固定」。
- **互動接觸**：手、腳、臉碰到東西的每一段都要寫（拿手機、牽手、拉走對方、蹲下時膝蓋碰地）。「要求」寫看得出對錯的條件（「握住，螢幕朝臉」「指尖碰到就停」）。
- **道具與場景**：場景、道具兩行，頓號分開。
- **字卡時間碼**：標題、內容照劇本原文。進場時間配合動作（例：「角色一停下，標題就蓋章彈入」→ 寫角色停下的那一秒）；退場空白＝到這一鏡結束。
- **回饋**：新寫的寫「（無）」；修改模式在最後加「### 第 N 輪（日期）」，舊的不刪。

時間一律是**鏡內秒數**：這一鏡正片第 0 秒起，不含頭尾多渲的部分，寫到小數 0.1。

## 什麼時候問使用者

用 `mcp__ask-panel__ask_user`（`asker` 寫「分鏡展開・<鏡號>」）。**只問劇本沒寫、而且會改變畫面的事**（例：新郎被拉走時是拉手還是拉手臂；兩人自拍誰拿手機）。整份最多問一次、一次最多 4 題，推薦的放第一個並在 label 後加「（推薦）」，`context` 寫清楚目前寫到哪、各選項的差別。回傳 `cancelled` 就照推薦寫，並在回報的 `unanswered` 列出來。

## 不要做的事

- 不改劇本檔、不改別的鏡的分鏡展開（發現銜接問題寫進回報）。
- 不碰 3D、Blender、動畫產線的檔案；不 commit；不下載素材。
