---
description: 修 3D 影片某一幕的某個動作：只拍那個部位的多角度近照、附客觀檢查數字，做成近照確認頁給使用者看；使用者指出哪裡不對就照著修、更新同一頁，說「可以」才渲整幕。
argument-hint: [幕＋動作＋問題，例：⑦a 新娘握叉子的手，側面看手背折到餐桌]
---

請修正以下動作，全程使用繁體中文、用白話回報：

**要修的動作**：$ARGUMENTS

這個指令的重點是**先給使用者看近照、由使用者決定哪裡要修**，不要自己用眼睛看小圖就覺得可以、直接渲整幕交出去（⑦a 握叉子修了五輪都不對，就是這樣出事的）。範例頁：https://claude.ai/artifact/UmtR9YTfUbHEX7WKRdn5eP

## 步驟

1. **找到那一幕、那個動作**
   - 幕的程式在 `.claude/docs/data/blender/productions/opening-v12/scripts/mx_scene_<幕>.py`（② 在 `mx_skeleton.py` 的 `scene_02`），預覽是 `mx_preview.py`。
   - 從使用者的描述對出：哪個角色、哪根骨頭（手 `J_Bip_R_Hand`／`J_Bip_L_Hand`、頭 `J_Bip_C_Head`、腳 `J_Bip_L_Foot`…）、哪段時間。對不出來就先問，不要猜。
   - 使用者附了審看頁的回饋或截圖時，先讀（審看頁 db `review/prev-<幕>`、圖片用 Artifact read 的 `path`）。

2. **先查原因，再動手**
   - 先拍一次**現況**近照（下面第 3 步的指令），自己看側面、正面、背面，講得出「為什麼會這樣」再改。
   - 用數字確認，不靠眼睛猜：例如手指彎幾度、道具離皮膚幾 mm、哪個網格（`TINTOBJ=`）、法線（`TINTMODE=normal`）、rest 座標（`TINTMODE=restpos`）、影子（`NOSHADOWOBJ=`）。工具與排除順序見動作庫 `references/fast-iteration.md` §0.6。
   - 手拿道具：道具先放在手的 rest 空間、手指照道具彎到剛好碰到（`scripts/fork_grip.py` 是範例），不要「先擺固定手勢再把道具塞過去」。

3. **拍近照**（背景 Blender，不出影片）
   ```
   "$BL" -b "$PROD/blend/couple.blend" -P "$PROD/scripts/prod_cli.py" -- --run mx_preview SID=<幕> STEP=15 T0=<起> T1=<訖> TAG=<標籤> CLOSE=<角色>:<骨頭>:<距離>
   ```
   - 出圖在 `D:\render-work\mixamo\preview\s<幕>\<標籤>\close_<角色>_<骨頭>\<秒>_{main,front,side,back}.jpg`（main＝影片鏡頭方向放大）。
   - 時刻挑動作的關鍵點（開始、做到最滿、收回、結束），6～10 個；距離手 0.25～0.3、頭 0.5、全身 1.5。
   - 有道具或接觸時一起跑客觀檢查（例：⑦a 的 `FORKCLIP`＝手的皮膚跑進叉子幾點、最近幾 mm；`TABLECLIP`＝兩隻手的皮膚低於桌面幾點），**整段每一格**都要過。
   - 穿模檢查要**兩隻手、整段**都跑，不只檢查使用者提到的那隻：⑦a 修比讚時才發現另一段左手放桌上，指尖一直插進桌面 4.8 cm，前幾輪都沒人發現。
   - 改手的方向時一定量手腕角度（⑦a `WRIST`：手掌相對前臂的屈伸、偏），超過 30° 先改手臂位置，不要用手腕去凑方向（比讚第 1 版手腕往手背折 80°）。
   - 手指、指節看不清楚時先看身體皮膚材質的 MToon 描邊有沒有開（`outline_width_mode`；新娘的身體原本是 none，臉才有）。

4. **做近照確認頁、發布**
   - 寫 spec.json（格式在 `.claude/skills/blender-motion-library/scripts/close_review_page.py` 開頭），放 scratchpad；`python close_review_page.py spec.json` 產出 `index.html`，用 Artifact 發布（第一次給 `icon`）。
   - 頁上要有：這頁只看什麼、**每一版改了什麼（照使用者的哪句話）**、客觀檢查的數字、請使用者回什麼。
   - 每列最左邊放「影片裡同一格的畫面」（另跑一次不加 CLOSE 的同一段、裁切後存成 `<秒>_cam.jpg` 放進近照資料夾，`views` 加 `["cam", "影片畫面（同一格）"]`）：使用者要判斷的是觀眾看到的樣子，近照只是輔助。
   - 自己先看一遍近照，把「我覺得還不像的地方」照實寫在回報裡，不要藏。

5. **等使用者看**
   - 使用者說哪個時刻、哪個角度不對 → 回到第 2 步，改完**更新同一個網址**（spec 的 `changes` 加一版、同一個 file_path 重新發布）。
   - 使用者說「可以」→ 才渲整幕：`STEP=2 TAG=r<輪> bash D:/render-work/mixamo/preview/run_lane.sh A <幕>`，再更新那一關的審看頁（`make_preview_page.py` 的 ROUND／TAGS、`_notes.json` 寫改了什麼）。
   - 使用者沒回不算確認。

## 不要做的事

- 不要沒給使用者看近照就渲整幕。
- 不要改共用的 `couple.blend`、動作庫 `actions.py`；要改模型先問、先備份。
- 完整品質渲染、commit、合併 main 都要先問。
- 改檔內含 Windows 路徑時用 Write／Edit，不要用 Bash heredoc（`\b`、`\n` 會被吃掉）。
