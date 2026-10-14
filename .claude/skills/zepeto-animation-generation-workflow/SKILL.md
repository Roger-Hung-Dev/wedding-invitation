---
name: zepeto-animation-generation-workflow
description: ZEPETO 黏土風角色的動畫製作入口（/zepeto-animation-generation-workflow）。一次做一鏡：讀分鏡展開檔（導演端發「動畫開工：B2」，或使用者單獨下指令、沒有分鏡展開時自己問齊寫一份）→ 比對上游（身體、服裝、整支片設定）→ 先上網查真人姿勢 → 選 Mixamo 動作原樣套上 → 貼地、鎖腳 → 擺道具、一開始就穿衣服 → 手指碰到就停、拇指、嘴 → 皮膚與衣服逐格量數字＋自我審查 → 改過的動作先用固定機位小片段＋腳和身體的數字自我檢驗 → 近照確認頁（附低畫質短片，同一頁逐版更新）→ 使用者說可以才定案（狀態紀錄、樣張、交接）→ 通知導演端。也用於改已定案的鏡（「動畫修改：B1」或「改 B1：…」）。全部鏡定案後，用 render-settings 面板選畫質做完整渲染。
argument-hint: "<鏡號>｜改 <鏡號>：<要改什麼>｜<測試情境描述>"
---

# ZEPETO 動畫製作（入口）

使用者這次給的需求：`$ARGUMENTS`

你是主控端，**在對話裡直接做，不派給子代理**：要操作開著的 Blender（MCP），中途要讓使用者看確認頁、給回饋，定案要使用者說可以。全程繁體中文、白話回報。一次做一鏡；好幾鏡就照順序一鏡一鏡走。

動畫在 ZEPETO 產線的位置：頭 → 身體 → 服裝、場景道具 → **動畫** → 剪接。分工與狀態紀錄格式見 `.claude/docs/data/blender/zepeto/pipeline/README.md`（zepeto-director 維護）。導演端發動、這個 session 實際跑（使用者 2026-10-12 選定）；**Blender 同一時間只給一個 session 操作**。

**動手前先讀 [references/checklist.md](references/checklist.md)**（固定要量的項目、實際踩過的坑）。交接格式在 [references/handoff.md](references/handoff.md)。

## 會用到的東西

| 東西 | 位置 |
| --- | --- |
| 共用程式庫（MCP 裡 import） | `scripts/`：`zanim`（場景、讀 Mixamo、接段、擺姿勢、拍照、清場景）、`zanim_lib`（重定向、量角色、滑步）、`zanim_fix`（接縫、鎖腳、貼地；蓬裙 `skirt_arms`／`skirt_gap`；站著小角度轉身 `pivot_turn`）、`zanim_pose`（低頭、掌心、起步不沉）、`zanim_hand`（手指碰到就停、拇指、手放到位置）、`zanim_dress`（穿衣服、量衣服）、`zanim_sample`（樣張、短片）、`zanim_cast`（兩人以上同場）、`zanim_check`（第 7.5 步的腳、身體數字） |
| 自我檢驗（背景跑） | `scripts/self_check.py`＋`close_clip.py`（第 7.5 步的固定機位小片段）、`gown_check.py`（禮服穿模網格實量） |
| 狀態紀錄（開工／定案） | `scripts/zanim_status.py`（一般 Python） |
| 分鏡展開檔讀寫 | `scripts/zanim_spec.py`（導演端的格式；單獨使用時 `write_standalone()`） |
| 背景渲樣張、短片 | `scripts/sample_render.py` |
| 確認頁產生器 | `.claude/skills/blender-motion-library/scripts/close_review_page.py`（spec 可帶 `videos`） |
| 每一鏡的程式、規格、定案參數（進版控） | `.claude/docs/data/blender/zepeto/anim/<片名>/<鏡>/`：`<鏡>_shot.py`、`spec.md`（單獨使用時）、`final.json`；測試情境放 `anim/_tests/<id>/` |
| 圖、確認頁、短片（不進版控） | `D:/render-work/zepeto-anim/<片名>/<鏡>/` |
| 樣張 | `D:/render-work/zepeto-anim/sample/<id>.blend`、總表 `samples.json` |
| 範例（照著寫） | `anim/opening-proposal-b/b1_b2/`（走路、停下、雙手拿手機、拇指按開關、道具冒出來）、`anim/_tests/sit_test/`（坐椅子、捏杯腳喝、手擱大腿、穿西裝） |
| Mixamo 原檔 | `D:/render-work/mixamo/raw/*.fbx`（缺的要請使用者下載，見 checklist） |
| 渲染參數面板 | 專案 mod `render-settings`（`mcp__render-settings__pick_render_settings`） |

MCP 每段程式開頭固定：

```python
# BODY=groom        ← 身體出廠閘門只核對點名的身體（用到哪幾副就點名哪幾副，逗號分開）
import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
import zanim as Z; Z.use_shot("<片名>", "<鏡>")
```

## 走位版（素材還沒到齊時先做；使用者 2026-10-12 同意）

開工訊息第三行寫「模式：走位版」，或使用者說「先做走位」時：

- **做**：第 2 步（查姿勢，只查走位、轉身、並肩這類身體動作）、第 3～4 步（Mixamo 選段、接段、節奏、秒數、貼地、鎖腳）、新郎的路線與轉身時間、鏡頭機位（照鏡頭表＋字卡留白）、兩人之間的站位與換位。
- **代替品**：還沒出廠的人用**替身**（灰色膠囊人形＋朝向標記，身高照身體端給的預估；新娘目前和新郎同身形＝同高），只拿來排位置、看會不會擋到；道具、場景、柱子、門框用灰色方塊與平面，尺寸照素材庫 catalog 或分鏡展開寫的。
- **不做**：手指碰道具、拇指、嘴（道具真的尺寸到了才準）；兩人接觸（牽手、拉走、並肩間距）；穿模檢查數字、近照確認頁、定案。
- **交出**：一支低畫質走位短片（附秒數、Mixamo 段落、站位說明）給導演放進審看頁；狀態紀錄維持 in_progress，notes 寫「走位版」與用了哪些代替品。
- **素材到齊後（第二階段）**：換真的人、道具、場景 → 第 5 步起照常（互動、檢查、近照確認頁、定案）。走位版定下的選段、節奏、路線、機位沿用，使用者已看過的不再重問。

## 0. 選鏡、讀交接

| 進來的方式 | 做法 |
| --- | --- |
| 導演端訊息「動畫開工：B2」／「動畫修改：B1」 | 讀訊息裡的分鏡展開檔、整支片設定；修改時直接跳到「回饋」段的那一輪 |
| 使用者打 `<鏡號>`（例 `B2`） | 找 `.claude/docs/storyboard/*-breakdown/<鏡號小寫>.md`；找不到就當單獨使用 |
| 使用者打「改 <鏡號>：…」 | 讀那一鏡的 `final.json`、確認頁、狀態紀錄，把使用者這次說的當回饋 |
| 測試情境描述（不屬於任何片） | 單獨使用 |
| 什麼都沒給 | 列出狀態紀錄 `status/anim/` 與分鏡展開資料夾裡的鏡，讓使用者選（`AskUserQuestion`，或 `mcp__ask-panel__ask_user`） |

**單獨使用**：用 `AskUserQuestion` 一次問齊：角色（已出廠的身體）、衣服（已出廠的服裝）、動作描述、道具、鏡頭（景別、角度）、大約幾秒、要碰到什麼。問完用 `zanim_spec.write_standalone()` 寫成同格式的 `spec.md`，之後流程完全一樣。沒有整支片設定時用預設（橫式 16:9、30 fps）並告訴使用者。

`python scripts/zanim_spec.py <檔>` 會印出解析結果：「基本」、三張表（鏡頭、互動接觸、字卡時間碼）、回饋各輪。`missing` 不是空的就回報導演端（「動畫卡住」）。

## 1. 比對上游、開工

```bash
python "<scripts>/zanim_status.py" check <id>        # 已經有紀錄的鏡
```

- 身體、服裝要 released（閘門 hook 也會擋）；整支片設定（`status/film/<片名>.json`）有的話也要一致。
- 「上游已更新」→ 停下來告訴使用者哪個上游、從哪版變哪版，問要不要照新版重做。
- 開工：`python zanim_status.py start <id> --changes "這次要做什麼"`（紀錄改 in_progress）。

## 2. 查真人姿勢（使用者 2026-10-12 的規則）

握東西、碰東西、關節方向，先用 WebSearch 查真人怎麼做（例「how to hold a wine glass」「how to hold phone with both hands texting」），整理出各手指、手腕、手肘該在哪裡，寫成這一鏡的目標條件（評分、目標位置）。**回報時附來源**，說明照哪一種做。

## 3. 選動作

- 動作一律用 Mixamo 現成動畫**原樣**套上：劇情不改、挑最接近的、只選段與接段；之後的修正不破壞動作結構。
- 分鏡展開有候選就逐一驗證（套上去看節拍、接縫、能不能做互動）；都不能用 → 問使用者（附理由與替代候選），或回報導演端「動畫卡住」。
- 缺 Mixamo 檔：請使用者從 mixamo.com 下載（**下載前先問**），放 `D:/render-work/mixamo/raw/`。

## 4. 套動作＋基本修正

照範例寫 `<鏡>_shot.py`：`Z.setup()` → `Z.load_clips()` → 接段（`Z.sequence()`，接縫用 `zanim_fix.match_phase`）→ `zanim_fix.ground()` 貼地 → `foot_lock()` 鎖腳 → 其他微調（低頭太深 `zanim_pose.lift_head`、起步不沉 `straighten_stance`）。手指預設用共用手勢 `relaxed`。

## 5. 道具＋衣服

- 道具從素材庫 `library/props-zepeto/` 拿（`use_props.py` 的 `place_prop()`），照 ZEPETO 比例；缺的發給場景端（副本給導演端），告訴使用者。
- **衣服一開始就穿**：`zanim_dress.dress("<服裝代號>")`。手擱在身上要對衣服表面、靠椅背要量衣服。

## 6. 手和道具的互動

道具寫成距離場 `sdf(q)`（道具座標，負＝裡面）。手放到位置（`zanim_hand.put_hand`／`put_hand_pole`）→ 每一指、每一節往目標手勢彎、碰到就停（`close_fingers`）→ 拇指（`thumb_to`）→ 握法照第 2 步查到的寫成評分搜尋。嘴、大腿這類要碰的點用變形後的網格算。

## 7. 量數字＋自我審查

照 checklist 的「固定要量」逐格量（皮膚網格＋衣服；骨頭估的距離比皮膚少約 1 mm，交出去的數字一律用網格量）。兩人同場、穿禮服時加跑 `scripts/gown_check.py`（背景 Blender 量新郎進裙子、手進裙子、裙子碰場景）。再拍多角度近照（`Z.shots`），自己先看四件事：**生硬、接觸、方向、穿模**。有問題自己先修。

## 7.5 動作小片段自我檢驗（使用者 2026-10-13 的規則）

**改了任何身體動作（轉身、起步、停下、跨步、換位、加微調）之後、交確認頁之前，一定先做這一步**；使用者指出動作問題、修完也一樣。只看整段低畫質短片看不出碎步、微蹲、抖動（B3 新郎轉身：整段看起來還好，量出來兩腳同時離地亂動）。

1. **先量數字**（MCP、不用渲圖）：`import zanim_check as K` → `K.foot_motion(起秒, 迄秒)`、`K.body_jitter(起秒, 迄秒)`，範圍＝改到的那段前後各多 0.3 秒。
   - 站著轉身、換位：每隻腳每次只抬 1 次（`lifts`）、方向來回 `reversals` 0、兩腳同時離地 `both_off_frames` 0、站著那隻腳 `slide_max_mm` ≤ 1。
   - 身體：面向 `yaw_reversals` 0（不來回抖）；骨盆高度 `hips_range_mm` 站著時 ≤ 2 cm（大過就是微蹲或浮起來）。
   - 走路的格子會有兩腳同時離地，這兩條只套在站著的動作上。
2. **再渲小片段**（存好樣張後，一般 Python 背景跑）：`python scripts/self_check.py <樣張.blend> <輸出資料夾> <誰> <起秒>-<迄秒>[,…] --views side,feet --body groom,bride`
   - 固定機位（看碎步、抖動不能跟拍）、其他人先藏起來；角度：`side` 全身、`feet` 腳部特寫、`front` 斜前方、`hands` 手部特寫，看改到哪裡就選哪幾個。
   - 產出 `<段>_<角度>_strip.jpg`（11 格縮圖條，自己逐格看）和 `<段>_check.mp4`（各角度並排的小短片）。
3. **自己看縮圖條**：鞋子有沒有飄、抖、滑；身體有沒有突然沉下去、轉一下又轉回去；手有沒有穿過身體或裙子。
4. **不過就修、再從 1 重來**，直到數字和畫面都過，才進第 8 步。
5. **交出去時**：`<段>_check.mp4` 放進確認頁 `videos` 的最前面（說明寫「自我檢查：幾秒到幾秒、左全身右腳部」），checks 寫上第 1 步的數字；回報使用者時說清楚「自己檢查了什麼、量到多少」。

## 8. 近照確認頁

1. 存樣張（`zanim_sample.bake()`、`save()`；鏡頭照分鏡展開的鏡頭表）→ 背景渲整段低畫質短片：`zanim_sample.render_clip()` 回傳的指令用 Bash 跑（`run_in_background`，一鏡約 2 分鐘）。
2. 近照：全身照（關鍵時刻×2 角度）＋互動的近照。
3. `close_review_page.py`：intro（這一鏡做什麼、用了哪個 Mixamo、道具、衣服）、changes（每一版改了什麼）、checks（數字）、videos（短片）、rows。發布成 Artifact，**之後每一版都更新同一個網址**。
4. 回報使用者：先講結論，再講改了什麼、數字、參考來源；等回饋。使用者指出問題 → 修 → 更新同一頁，直到說「可以」。

## 9. 定案交接

1. `final.json`：這一鏡全部的定案參數（`run()` 從這裡讀，改任何值＝換版本）。
2. 樣張登記：`zanim_sample.register()`（3～4 格：動作重點、接觸、動得最快的那一格說明寫「動得快」）。
3. 狀態紀錄：`python zanim_status.py release <id> --artifact <final.json> --changes "…" --page <確認頁> --body groom --outfit <服裝> --film <片名> --prop <道具…> --notes '{"shot": "B2", "duration_s": 4.2, "handles_s": 0.5}'`。
4. 清掉工作場景（`cleanup()`），不存任何 .blend 到身體、服裝的檔。
5. 屬於某支片時，SendMessage 給導演端（格式見 handoff.md「動畫定案」），找不到導演端就在回報寫「已留紀錄，未通知到導演端」。單獨使用的測試情境不通知。

## 10. 完整渲染（全部鏡定案、總審看也過了才做）

1. `zanim_status.py check` 全部「一致」才開始。
2. `pick_render_settings({ film, film_json, shots: [已定案的鏡], out })` 開面板讓使用者選畫質（可以按 t 試渲）；收到「渲染參數（完整渲染設定）…」的訊息後照著渲。
3. 每鏡：背景 Blender 從樣張渲 PNG 影格（fps、前後多渲照整支片設定；透明背景出 RGBA PNG）＋一支 H.264 mp4 預覽；可以同時跑幾個照面板設定（4K 只能 1 個）。
4. 渲完 SendMessage 給導演端「動畫渲染完成：<片名>」，附每一鏡的成片路徑、鏡內秒數、頭尾多做秒數（格式見 handoff.md）。**剪接由導演端做**（2026-10-12 使用者決定）：導演端用剪接樣式庫 `library/edit-styles-zepeto/render_edit.py`（字卡、轉場照 edit.json，配樂用 `--audio`）；剪接程式和樣式庫由動畫端維護。

## 鐵律

- 不存 `body.blend`、`outfit.blend`；所有動作在另開的工作場景做，做完刪掉。
- MCP 單次 120 秒：渲圖一次約 12 張；長的工作拆開或改背景 Blender。
- 下載任何素材前先問使用者；不自己 commit。
- 對使用者的回報一律附來源（姿勢參考）、數字（網格量的）、確認頁網址。
