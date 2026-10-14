---
name: zepeto-film-director-workflow
description: ZEPETO 黏土風開場片的導演工作流入口（/zepeto-film-director-workflow）。整支片從劇本到成片的 11 步：劇本發想與定案（film-director 子代理）→ 整支片設定（render-settings 面板：片子規格＋字卡與轉場）→ 選角（zepeto-picker）→ 分鏡展開（workflow zepeto-shot-breakdown）→ 補素材（通知場景、服裝）→ 逐鏡發動畫（通知 zepeto-animation）→ 整支片審看 → 完整渲染 → 配樂與對拍 → 剪接輸出。可以從任何一步接著做（看檔案與狀態紀錄判斷做到哪）。使用者說「做一支新的開場片」「B 劇本往下走」「下一步」「B3 要改…」「開始剪接」時使用。不做 3D、不操作 Blender。
argument-hint: "<片名>｜新片：<描述／參考連結>｜<片名> 從第 N 步｜<片名> 改 <鏡號>：<要改什麼>"
---

# ZEPETO 開場片・導演工作流（入口）

使用者這次給的需求：`$ARGUMENTS`

你是主控端，也是導演（總協調）。**在主對話裡做**：要開面板給使用者、收面板送回的訊息、轉發 ask-panel 的提問，這些子代理做不到。全程繁體中文、白話回報。

- **不碰 3D**：Blender 同一時間只給一個 session 操作，動畫一律交給 zepeto-animation。
- **交接靠檔案**：分鏡展開檔、film.json／edit.json、狀態紀錄（`.claude/docs/data/blender/zepeto/pipeline/`，分工表在那裡的 README，由你維護）。訊息只是通知。
- **不 commit、不下載素材**（素材由場景、服裝端下載，下載前它們會問使用者）。
- **ask-panel**：子代理（film-director、分鏡子代理）有問題時，主對話會收到「［ask-panel］… 請立刻呼叫 mcp__ask-panel__relay {id}」→ 立刻呼叫 `mcp__ask-panel__relay`。

## 會用到的東西

| 東西 | 位置 |
| --- | --- |
| 劇本 | `.claude/docs/storyboard/<片名>-script.md`（格式見 `.claude/agents/film-director.md`） |
| 分鏡展開 | `.claude/docs/storyboard/<片名>-breakdown/<鏡號小寫>.md`；範本 `_breakdown-template.md`；寫法 [references/breakdown-guide.md](references/breakdown-guide.md) |
| 整支片設定 | `<片名>-breakdown/film.json`（片子規格，動畫的上游）、`edit.json`（字卡與轉場，只給剪接） |
| 導演工具 | `scripts/director.py`：`status`（做到哪）、`lint`（檢查分鏡展開＋缺件清單）、`record`（登記 film／edit 狀態紀錄）、`program`（剪接清單） |
| 和動畫端的交接格式 | `.claude/skills/zepeto-animation-generation-workflow/references/handoff.md` |
| 剪接程式（動畫端維護，**不要自己改**） | `.claude/docs/data/blender/library/edit-styles-zepeto/render_edit.py`（README 有參數） |
| 比較頁 | 參數效果 https://claude.ai/artifact/KaC1ZqHyfqnJgbrULR3dq9 、字卡轉場展示 https://claude.ai/artifact/VmCmdM4CKkNChZtqij1XQ1 |

## 先判斷做到哪

有片名就先跑 `python .claude/skills/zepeto-film-director-workflow/scripts/director.py status <片名>`，再讀劇本的「鏡表」狀態欄，從第一個沒完成的步驟接著做。使用者指定「從第 N 步」就從那步開始（前面的檔要在）。

| 看到 | 代表 | 從哪步 |
| --- | --- | --- |
| 沒有劇本檔 | 新片 | ① |
| 劇本鏡表全是「提案」，使用者還沒說定案 | 劇本修訂中 | ② |
| 沒有 film.json | 還沒選整支片設定 | ③④ |
| 有 film.json，分鏡展開缺鏡或 lint 有錯 | 分鏡展開中 | ⑤ |
| lint 的 `missing` 不是空的 | 缺素材 | ⑥（可和 ⑦ 並行：不缺素材的鏡先開工） |
| 有鏡的動畫「未開工」或不是 released | 動畫製作中 | ⑦ |
| 全部鏡 released、使用者還沒看過整支 | — | ⑧ |

## 11 步

### ① 劇本發想
派 `film-director` 子代理（Agent 工具），把使用者的描述、參考影片／網站連結、圖片路徑（Alt+V 貼的圖先換成檔案路徑）原樣轉給它，指定片名代號。它會用 ask-panel 問使用者挑提案。

### ② 劇本定案
同一個子代理繼續修訂（SendMessage），直到使用者說定案。改順序、地點時它會處理連帶影響（接縫位置、鏡號重編）。定案後確認劇本鏡表每一鏡都有秒數、地點、標題、內容。

### ③④ 整支片設定（片子規格＋字卡與轉場）
1. 先把兩個比較頁給使用者，說明：面板裡按 `t` 試渲用的是已定案的樣張、按 `p` 預覽用的是示範節目，**都不是這支片的鏡頭**。
2. 建議「前後多渲」選**各 1 秒**（⑩ 對拍時每一刀才有 ±1 秒可挪；4K 每鏡多約 9 分鐘渲染）。
3. 呼叫 `mcp__render-settings__pick_film_settings`（`film`＝片名、`out`＝`<片名>-breakdown/film.json` 完整路徑），結束這一輪等訊息。
4. 收到「渲染參數（…）：<片名>，已寫入 …」＋ JSON（`{film, edit}`）後跑 `director.py record <片名>`。
   - 訊息第二行是「片子規格：未變（沿用 film.json）」→ 只有 edit 會升版，動畫不受影響。
   - 規格有變而且已經有鏡在做或定案 → 告訴使用者哪幾鏡會被標成「上游已更新」、要重做。

### ⑤ 分鏡展開
1. **選角**：呼叫 `mcp__zepeto-picker__pick_body`（`multi: true`）讓使用者勾這支片出場的角色（只能勾已出廠的；劇本裡有、但還沒出廠的角色記成「未出廠」，交給 ⑥）。子代理開不了這個面板（它收不到使用者按 y 送回的訊息），所以一定在這裡由主控端開。
2. **跑 workflow `zepeto-shot-breakdown`**（會派「鏡數＋1」個子代理；第一次跑要先問使用者）。args：`film`、`date`（今天）、`cast`、`shots`（每鏡 `mode`：新的 `new`；動畫已定案但沒有分鏡展開的 `backfill`；改的 `revise`＋`feedback`＋`round`）。
3. 結果裡的 `film_check.issues`、各鏡 `unanswered` 轉給使用者決定；`fixes` 照實回報。
4. 給使用者看分鏡展開（可以做成一頁 Artifact：每鏡一張卡，列鏡頭、動作、字卡時間）；要改的回到 2 用 `revise`。
5. 使用者說可以 → 劇本鏡表該鏡狀態改「定案」。

### ⑥ 補素材
`director.py lint <片名>` 的 `missing`（或 workflow 的 `film_check.missing`）合併成一張清單，照分工表傳給負責的 session（場景與道具 → zepeto-scense，服裝 → zepeto-clothing-models，身體未出廠 → zepeto-body）。每一筆寫：要什麼、哪幾鏡用、劇本裡的描述、分鏡展開檔路徑。對方不在線就在回報寫「已留清單，未通知到 ○○」。素材補好後把分鏡展開的「缺：…」改成素材庫 key 並重跑 lint。

### ⑦ 逐鏡發動畫
照播放順序一次發一鏡（Blender 只給一個 session），不缺素材的先發。SendMessage 給 zepeto-animation，第一行固定：

```
動畫開工：B2
分鏡展開檔：<完整路徑>
整支片設定：<film.json 完整路徑>
片名：<片名>
```

**素材還沒到齊時**（缺場景、道具，或有角色身體未出廠）：問使用者要不要先做「走位版」，同意的話在第三行加「模式：走位版（新郎＋替身，素材用代替品）」。走位版只定 Mixamo 選段、秒數、路線、鏡頭、站位，不定案（狀態維持製作中），交一支低畫質走位短片給使用者看；素材到齊後同一鏡再發一次「動畫開工」（不加模式行），動畫端補手的接觸、角色互動、檢查與確認頁才定案。

收到「動畫定案：B2 v1」→ 把回報的實際值（秒數、字卡進場改了多少）寫回分鏡展開、劇本鏡表狀態改「動作定案」並附確認頁網址，再發下一鏡。收到「動畫卡住：B2」→ 照原因處理（缺素材回 ⑥、上游沒出廠通知負責端、候選動作都不能用就改分鏡展開再發）。

### ⑧ 整支片審看
所有鏡 released 後，把各鏡確認頁的低畫質短片串成一頁給使用者一次看（Artifact）。回饋照鏡分開：
- 動作、鏡頭的 → 寫進那一鏡分鏡展開「回饋」段的新一輪，發「動畫修改：B2」＋「回饋：第 N 輪」。
- 只改字卡或轉場的 → 重開 ③④ 的面板（`current` 帶現有 film.json），動畫不用重做。
- 改字卡文字、出現時間 → 只改分鏡展開的「字卡時間碼」。

### ⑨ 完整渲染
請 zepeto-animation 做完整渲染（它會開完整渲染設定面板問使用者畫質）。等它傳「動畫渲染完成：<片名>」，每鏡附成片 mp4、影格、鏡內秒數、頭尾多做秒數。把成片路徑與鏡內秒數存成 `<片名>-breakdown/clips.json`：`{"B0": ["<mp4>", 3.0], …}`。

### ⑩ 配樂與對拍
1. 問使用者用哪首（候選：喜帖網站背景音樂 `src/assets/audio/wedding-bgm.mp3`、婚紗輪播的卡農 `D:/婚禮籌備/婚紗輪播影片/產生器/`、另找免費配樂（請場景端照來源清單找、下載前問）、使用者提供），以及要不要對拍（每個轉場／只對換景與片尾／不對）。
2. 對拍工具由動畫端加在剪接程式裡（抓拍點、每個轉場的建議挪動量、配樂起點建議、±3% 變速）；用它的建議值寫 program.json 每段的 `trim_head`、`dur`，挪動量超過頭尾多做的鏡列出來給使用者決定要不要重渲。
3. 做一頁試聽頁（低畫質、有聲）讓使用者用耳朵確認，照回饋調。
4. 工具還沒做好、或要加功能 → 找 zepeto-animation，不要自己改 `render_edit.py`／`edit_styles.js`。

### ⑪ 剪接輸出
```bash
python .claude/skills/zepeto-film-director-workflow/scripts/director.py program <片名> --clips <clips.json> --out <program.json>
python .claude/docs/data/blender/library/edit-styles-zepeto/render_edit.py --settings <edit.json> --program <program.json> --out <資料夾> --size <依 film.json> --fps <依 film.json> [--audio … --music-from … --audio-at … --fade-out …]
```
輸出放 `D:/render-work/zepeto-edit/<片名>/`（不進版控）。給使用者看成片，照回饋回到對應的步驟。定案後在劇本修訂紀錄寫一行「成片定案」與檔案路徑。

## 回報

每一步做完都先講結論（做到哪、下一步要使用者做什麼），再列細節。使用者沒回、暫用推薦的事要逐條寫明。
