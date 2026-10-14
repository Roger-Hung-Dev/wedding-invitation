# 動畫工作流的交接格式（2026-10-12 和 zepeto-director 約定）

交接以**檔案**為準（分鏡展開檔、整支片設定、狀態紀錄），訊息只是通知。動畫端不在線時，下次開工讀檔一樣接得上。

## 導演端 → 動畫端（SendMessage）

第一行固定，二行起逐行寫：

```
動畫開工：B2              ← 經過段寫「動畫開工：B1→B2」
分鏡展開檔：D:/SideProject/wedding-invitation/.claude/docs/storyboard/opening-proposal-b-breakdown/b2.md
整支片設定：D:/SideProject/wedding-invitation/.claude/docs/storyboard/opening-proposal-b-breakdown/film.json
片名：opening-proposal-b
```

修改：第一行「動畫修改：B1」，多一行「回饋：第 N 輪」（直接跳到分鏡展開檔「回饋」段的那一輪讀）。

## 動畫端 → 導演端

定案：

```
動畫定案：B2 v1
實際秒數：4.2（鏡內秒數，同 status notes.duration_s）
頭尾多做：0.5／0.5
確認頁：https://claude.ai/artifact/…
狀態紀錄：.claude/docs/data/blender/zepeto/pipeline/status/anim/b2.json
樣張：已登記 samples.json（或「樣張：未登記（原因）」）
和分鏡展開不同的地方：字卡進場 1.2 → 1.4（人停下來比預計晚）
```

完整渲染做完（剪接由導演端做，2026-10-12 使用者決定）：

```
動畫渲染完成：opening-proposal-b
渲染設定：<render.json 路徑>（解析度、fps、透明背景…）
B1→B2：D:/render-work/zepeto-anim/opening-proposal-b/b1_b2/final/edit_in.mp4（影格 final/frames/、鏡內 11.2 秒、頭尾多做 0.5／0.5）
B2：…
```

每一鏡給成片 mp4（剪接用，含頭尾多做的部分；剪接的 program.json 用 `in_s`＝頭尾多做的秒數跳過開頭）、PNG 影格資料夾、鏡內秒數、頭尾多做秒數。

做不下去：第一行「動畫卡住：B2」，後面寫原因（缺素材、上游沒出廠、候選動作都不能用、分鏡展開缺段…）。

## 分鏡展開檔（導演端寫；單獨使用時動畫端照同格式寫）

- 路徑：`.claude/docs/storyboard/<片名>-breakdown/<鏡號小寫>.md`；經過段一份 `b1_b2.md`、鏡號寫「B1→B2」。
- 二級標題固定、順序不變、文字不改；沒內容寫「（無）」：
  `## 基本`、`## 鏡頭`、`## 角色與動作`、`## 互動接觸`、`## 道具與場景`、`## 字卡時間碼`、`## 回饋`
- 「基本」條列：片名、鏡號、秒數、地點、角色、上一鏡、下一鏡、轉場（接上一鏡）。
- 表格（固定表頭）：
  - 鏡頭：`| 起秒 | 迄秒 | 景別 | 機位 | 運鏡 | 備註 |`（景別：遠景／全景／中景／近景／特寫）
  - 互動接觸：`| 起秒 | 迄秒 | 角色 | 部位 | 接觸對象 | 要求 |`
  - 字卡時間碼：`| 字卡 | 標題 | 內容 | 進場秒 | 退場秒 |`（退場空白＝到這一鏡結束；直接對到剪接 program.json 的 cap、cue）
- 時間一律是**鏡內秒數**：正片第 0 秒起，不含頭尾多做的，可寫到 0.1 秒。
- 「回饋」每輪一個 `### 第 N 輪（YYYY-MM-DD）`，往下加、舊的不刪。
- 讀檔：`scripts/zanim_spec.py`。

## 狀態紀錄（`status/anim/<id>.json`）

- id：單鏡 `b2`、經過段 `b1_b2`；測試情境不寫紀錄。
- artifact＝這一鏡的 `final.json`（動畫不存 .blend；改任何值＝換版本）。
- upstream：body、outfit、film（導演端的 `status/film/<片名>.json`）、用到的道具（kind prop，不追蹤）。
- notes：`shot`（例 "B2"）、`duration_s`、`handles_s`、`film`、`sample`。
- 工具：`scripts/zanim_status.py`（check／start／release）。
