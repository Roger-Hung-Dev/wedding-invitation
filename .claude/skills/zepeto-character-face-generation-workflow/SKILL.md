---
name: zepeto-character-face-generation-workflow
description: 真人大頭照 → ZEPETO 風 3D 大頭的入口（/zepeto-character-face-generation-workflow）。使用者用 Alt+V 貼上照片或 @照片檔，主控端找出照片的檔案路徑、問齊名稱，呼叫 zepeto-character-face-generation workflow（zepeto-analyze-photo-3d-model 生成 OBJ → zepeto-avatar-crafter 後處理成 .blend → zepeto-face-rigger 用 AI 網格路線做成可動臉：AI 頭本身當成品，ARKit 52 表情＋臉部控制骨架＋長髮避開身體），再回報成果與驗收圖。使用者說「把這張照片做成 ZEPETO 風的 3D 臉」「生成 ZEPETO 大頭」時使用。只想調材質重產 .blend（stages 只帶 craft）、只重做可動臉（stages 只帶 rig）時也走這裡。
argument-hint: "[名稱] [補充描述]（照片用 Alt+V 貼上，或 @照片檔）"
---

# ZEPETO 大頭生成（入口）

你是主控端。workflow 裡的子代理**不能問使用者、也看不到對話裡貼上的圖**，所以照片路徑、名稱都要在這裡準備好，再一次派工。

使用者這次給的參數：`$ARGUMENTS`

## 1. 找出照片的檔案路徑

| 使用者怎麼給 | 怎麼換成路徑 |
| --- | --- |
| `@照片檔` | 訊息裡的路徑；相對路徑以專案根目錄 `${CLAUDE_PROJECT_DIR}` 為準，換成絕對路徑 |
| Alt+V 貼上（訊息裡出現 `[Image #N]`） | Claude Code 把貼上的圖存在本 session 暫存資料夾的 `images\N.png`，也就是你的 scratchpad 上一層的 `images` 資料夾（見下方指令） |
| 一般路徑文字 | 直接用 |
| 都沒有 | 用一般訊息請使用者貼上或給路徑，**不要拿舊照片猜** |
| 沒有真人照片、只有文字設定（配角、路人，例：開場片的婚禮攝影師） | 不帶 `photo`，把設定原話放進 `notes`（2026-10-14 起支援）。生成端照文字設定寫描述，一樣是 ZEPETO 風（V 字臉、杏仁眼、亮澤） |

貼上的圖找不到時，用 PowerShell 搜（把 `N` 換成 `[Image #N]` 的數字）：

```powershell
Get-ChildItem "$env:TEMP\claude" -Recurse -Filter "N.png" | Where-Object FullName -match "${CLAUDE_SESSION_ID}\\images"
```

- 找到後用 `Read` 打開，確認跟使用者給的是同一張。
- 有好幾張圖時，問要用哪一張。
- 暫存的貼上圖會被定期清掉，沒關係：生成端第一步就會把它複製到成品資料夾的 `source/`。

## 2. 問齊參數

| 參數 | 必要 | 怎麼取得 |
| --- | --- | --- |
| `name` | ✅ | `$ARGUMENTS` 的第一個字若是小寫英數與 `-` 就用它；否則用 AskUserQuestion 問，並從照片檔名或人物給建議選項（例：新郎 → `groom`、新娘 → `bride`） |
| `notes` | | `$ARGUMENTS` 其餘的文字，原話照帶。沒有就不問 |
| `overwrite`／`stages` | | 成品資料夾 `.claude/docs/data/blender/zepeto/<name>/` 已經有 `stylized_face_generated.obj` 時才問：「覆寫重新生成」／「只重做後處理（stages 只帶 craft）」／「換個名字」 |
| `material` | | 使用者有指定材質值才帶（例：「透光權重 0.5」→ `{ sssWeight: 0.5 }`） |

`outDir` 一律是 `${CLAUDE_PROJECT_DIR}\.claude\docs\data\blender\zepeto\<name>` 的絕對路徑。
例外：這個人已經出廠、使用者要「先做新版候選、不動現役版」時，`outDir` 改放測試資料夾（例：`D:/render-work/blender-work/zepeto-fullrun/<name>-v2`），不改狀態紀錄；使用者看過說要換版，再搬進正式資料夾、照第 6 節出廠。

## 3. 派工

開跑前用一兩句話告訴使用者：

- Blender 5.2 要開著。沒開的話生成端會自己開，但開好要十幾秒。
- 用的是 Hyper3D Rodin 的**免費試用額度**，每跑一次用掉 1～3 次。**只送文字描述，照片不會上傳。**
- 生成端會在你開著的 Blender 裡另開一個 `ZEPETO_WORK` 場景作業，做完就刪掉，不動你原本的場景。
- 全程大約 12～18 分鐘（每次生成實測 35～70 秒，加上檢查、後處理、四張驗收圖；可動臉約 5 分鐘，其中兩次是照這顆頭試接一副身體來調長髮）。

**先改狀態紀錄**（見第 6 節）：這個人已有 `status/head/<name>.json` 時，把 `status` 改成 `in_progress`、`updated_at` 改成現在，`artifact` 不動。沒有紀錄就跳過。

然後呼叫：

```
Workflow({ name: 'zepeto-character-face-generation', args: {
  name, photo, outDir, notes, stages: ['generate', 'craft', 'rig'], overwrite: false, material
}})
```

`name` 找不到這個 workflow 時，改用 `scriptPath: '${CLAUDE_PROJECT_DIR}/.claude/workflows/zepeto-character-face-generation.js'`。

## 4. 回來之後

照「白話解說」的規則回報，先講結論：

- `needsUser` 有東西（最常見：Blender 連不上、試用額度用完、資料夾已有舊檔）→ 原樣轉告，說明處理完再跑一次。
- 成功 → 回報：
  - 成品 `.blend` 的位置，問要不要幫忙打開（另開一個 Blender 視窗：`Start-Process "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -ArgumentList '"<blend 路徑>"'`，不要在使用者開著的視窗裡開檔，會丟掉裡面沒存的東西）。提醒第一次開檔要等著色器編譯完，模型才會出現。
  - 用了幾次生成；有重生的話，每次為什麼重來。
  - 可動臉：`<outDir>/rig/head_rig.blend`（52 表情＋控制骨架，貼圖已打包）。自動檢查報告 `<outDir>/rig/check/report.html`（可以用瀏覽器打開給使用者看）。
  - 預覽圖在 `<outDir>/rig/preview/`：`mat_front_ai.png` 對 `mat_front_new.png`（像不像 AI 原頭）、`sheet_combos.png`（14 個代表表情）、`sheet_keys.png`（52 個單一表情）、`rig.png`（控制骨頭拉到底）、`body_side.png`（接上身體拉遠看長髮）。自己用 Read 看過再描述，特別是可動臉端回報的「哪裡不一樣」、改了 `face.json` 的哪些值。
  - 耳朵、後頸近照：`<outDir>/rig/check/ear.png`（左右耳附近的髮際線）、`check/nape.png`（接上身體的耳下到後頸）。這兩區總表縮圖看不出來，一定要看。
  - **脖子接口環**：成品的脖子上有一圈 48 點的接口環（後頸被分給頭髮的頭會補一片「墊底皮」），身體端照抄座標接上、看不出接縫。可動臉端回報的 `checks.ringOk` 要是 true；不是的話身體接不上，照實轉告。合約見 skill `zepeto-face-rig` 的 `references/ai-mesh-route.md`「頭身接縫」。
  - **ZEPETO 比例**（`checks.neckRatio`、`checks.zepetoRatio`；報告「ZEPETO 比例」一節）：脖子 AI 生成時常比 ZEPETO 粗，產線會修細到頭寬的 38%（超過 40% 才修，臉不動；目標和身體端約定）。`neckRatio` 不在 0.35～0.40 就照實轉告。其他項（下巴寬、眼寬、兩眼間距、嘴寬）是參考，用「比 ZEPETO 寬／窄幾成」講給使用者聽，偏離兩成以上的要點出來（那是生成描述的事，可動臉端改不了）。
  - 已知限制：手臂放下的姿勢，上臂會從長髮後面頂出來（頭髮固定在頭上）；使用者 2026-10-14 決定交給動畫端。
  - **授權提醒**：牙齒、舌頭、表情動法來自模板（CC BY 4.0），對外分享成品要標註作者（`.claude/docs/data/blender/zepeto/templates/cartoon-head-lucadrech/ATTRIBUTION.md`）。
  - 最後用的英文描述。
  - 驗收圖四張的位置（`qa/front.png`、`34.png`、`side.png`、`back.png`），用 `Read` 自己看過再描述。
  - 網格與材質數字（合併幾個頂點、破洞邊數、透光權重）。
- `partial` 或有 `knownIssues` → 照實講，不要說「都完成了」。

## 5. 不走 workflow 的情況

| 使用者要的 | 直接呼叫 |
| --- | --- |
| 只想重新生成模型，不做後處理 | `zepeto-analyze-photo-3d-model` |
| 只調材質、燈光，重產 .blend | 走這個 skill，`stages: ['craft']`；或直接叫 `zepeto-avatar-crafter` |
| 只重做可動臉（例：產線程式改過、要調 `face.json`） | `stages: ['rig']`；或直接叫 `zepeto-face-rigger` |
| 想要寫實的頭、願意上傳照片 | 這條產線不做；先跟使用者講清楚照片會上傳到第三方，再另外處理 |

交接格式與資料夾結構見 [references/handoff.md](references/handoff.md)。

## 6. 狀態紀錄（交給身體、服裝的交接）

下游（身體、服裝、動畫）靠 `.claude/docs/data/blender/zepeto/pipeline/status/` 的紀錄判斷頭有沒有換過，不靠訊息。規則與欄位見那裡的 `README.md`。大頭的紀錄是 `status/head/<name>.json`（`kind` `head`、`owner` `head`、`upstream` `[]`）。

| 時機 | 要做的事 |
| --- | --- |
| 開工改頭（跑 workflow、只重做可動臉、改產線程式後重跑、手動修 `head_rig.blend`） | 已有紀錄 → `status` 改 `in_progress`，`artifact` 不動 |
| 使用者看過說可以 | 寫 `released`：`version` 加 1、`artifact.path` 指 `<outDir>/rig/head_rig.blend`、`artifact.sha256` 實算、`changes` 一兩句白話（這句會秀給下游的使用者看） |
| 寫完 | 跑 `python status_check.py --verify`，有下游變成「上游已更新」→ 照 README 分工表找開著的 session 通知；找不到就在回報裡寫「已留紀錄，未通知到 ○○」 |

- 下游比對的是 **sha256**，不是版號。只要 `head_rig.blend` 重存過（就算只是打開存檔），sha 就會變、下游會被判成要重跑 —— 沒有要出新版就不要存回正式檔。
- 每個人只留一個現役版本：新版直接覆寫同一份紀錄。成品檔也一樣，身體端只認 `rig/head_rig.blend`；舊版由 `run_face_rig.py` 的 `rig` 步驟自動改名封存成 `head_rig_<日期>.blend`（它的預覽圖一起改名成 `preview_<日期>/`），手動改檔時也照這個命名。
- 2026-10-14 起成品的貼圖打包在 `head_rig.blend` 裡（`finish` 步驟）。之前用舊路線做的頭（新娘 v4、攝影師 v1）讀的是外部 `rig/head_color.png`，更早出廠的身體也直接讀它：**新路線重做這兩個人時，不要刪也不要改 `head_color.png`**，等身體端用新頭重新出廠、舊身體不用了再清。
- 新郎現役的頭是產線建好前手動做的（紀錄的 `version` 是 `legacy`）。2026-10-14 使用者決定不用了，原本在專案根目錄的 `stylized_face_*`（含 `stylized_face_rig/`、`stylized_face_expressions/`）整包封存到 `D:/render-work/archive/groom-head-legacy-20261014/`，紀錄的 `artifact.path` 已改指那裡（sha 不變，已出廠的新郎身體 v8 照舊）。新郎之後用這條一條龍重做。
