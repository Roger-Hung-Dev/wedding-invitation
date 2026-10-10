# 動作捕捉資料（BVH）

`walk_fwd(style="mocap")`（預設）用的真人走路資料。讀取與重新對應的程式在
`.claude/skills/blender-motion-library/scripts/mocap_retarget.py`（Blender 內建 BVH 匯入，不裝外掛）。

| 檔案 | 內容 | 用到的格 |
| --- | --- | --- |
| `35_01.bvh` | CMU 受試者 35、第 01 段「walk」（正常速度直線走路，120 fps） | 第 60～324 格（2.2 秒，約 4 步）；步態週期取其中左腳跟兩次著地之間（約 1.1 秒） |
| `16_33.bvh` | CMU 受試者 16、第 33 段「slow walk, stop」（放慢走、併腳停下，120 fps） | V12 ② 情境的停步（`productions/opening-v12/scripts/shots_v2.py` 的 `mocap_walk_stop`）：第 2～236 格，從第 89～90 格（左腳剛踩下）和 35_01 第 293～294 格交叉淡入 0.2 秒；第 217 格起兩腳併好不動。35 號的 walk 段（01～16、28～34）全是等速走、沒有停步，才換受試者 |
| `143_25.bvh` | CMU 受試者 143、第 25 段「Waving」（先左手揮、再雙手在頭前交叉開合，**照 60 fps 播**） | 動作庫 `wave_r`／`wave_l`／`wave2_mocap`（`actions_custom.wave_mocap`，src="143"，預設）：取第 255～385 格的左手揮（手臂往側前方舉、前臂直立），循環段第 270～370 格（週期 30 格＝每秒 2 下）。右手版＝左右鏡射。雙手段（第 395～540 格）沒用：兩手在臉前交叉開合、會擋臉 |
| `141_16.bvh` | CMU 受試者 141、第 16 段「Wave Hello」（右手揮，**照 60 fps 播**） | 備用來源（`wave_mocap(src="141")`）：第 34～200 格，手肘約與肩同高、手在耳朵旁，週期 25 格（每秒 2.4 下） |
| `82_08.bvh` | CMU 受試者 82、第 08 段「stand still; casual walk forward」（站著不動 → 從站姿起步往前走，120 fps） | V12 ③ 情境（拉緞帶版 `shots_v2_s0308.py` 的 `mocap_pull_chain`、推紅毯版新娘走到新郎身邊 `shots_v2_s03carpet.py` 的 `bride_chain`）：取第 900～1250 格；新郎卡在 99% 站著用力拉之後從站姿起步——在第 1069 格右腳剛要離地時從 16_33 的停步站姿淡入 0.2 秒（對齊不離地的左腳），起步後第一個右腳支撐期（第 1138 格）再接 16_33 第 154 格的最後一步停下。③ 的新郎也用 35_01 第 225 格接 16_33 第 154 格（急停）。同時試過沒用的：81_07／81_08「pull／drag heavy object」（面向重物倒退走）、18_03「A pulls B」（身體側對前進方向、回頭看人） |
| `81_05.bvh` | CMU 受試者 81、第 05 段「push heavy object」（彎腰前傾、雙手在腰到膝的高度推重物往前走，120 fps） | V12 ③ 推紅毯版（`productions/opening-v12/scripts/shots_v2_s03carpet.py` 的 `groom_chain`）：新郎推紅毯卷往前走，用到第 580 格（右腳支撐期）接 82_06。推重物腳步慢，著地判斷門檻用 0.25 m/s |
| `82_06.bvh` | CMU 受試者 82、第 06 段「Pushing on heavy object」（跨成弓箭步頂住、推不動 → 推動了往前衝 → 停步站直，120 fps） | V12 ③ 推紅毯版：第 202 格（右腳跨成弓箭步）接進來＝卡在石頭；第 2.6 秒「推動了」對齊場景 3.05 秒；往前衝一步後第 437 格接同一段第 952 格的停步、站直 |
| `93_03.bvh` | CMU 受試者 93、第 03 段「charleston_01」（單人查爾斯頓：前後踢腿、小彈跳、手臂前後擺，開頭結尾站著；**照 60 fps 播**） | V12 ② 跳舞版（`productions/opening-v12/scripts/shots_v2.py` 的 `v2_02_setup_dance`，2026-10-10）：第 50～221 格（60 fps 的第 0.8～3.65 秒，從站姿起跳到兩腳都踩地的那一拍），新郎新娘同一段、同一時間開始。影格率判斷：同受試者 93_07「Casual Walk」在 60 fps 才是 1.85 步/秒、1.08 m/s（120 fps 會變成 3.7 步/秒） |
| `69_18.bvh` | CMU 受試者 69、第 18 段「turn in place (opposite direction)」（原地順時針轉身，每次約 90°，120 fps） | V12 ② 跳舞版：新郎走完後轉向鏡頭，第 135～300 格（轉約 79°，腳先踩、骨盆肩頭跟著轉） |
| `69_16.bvh` | CMU 受試者 69、第 16 段「turn in place」（原地逆時針轉身，每次約 90°，120 fps） | V12 ② 跳舞版：新娘走完後轉向鏡頭，第 2～150 格（轉約 72°） |
| `16_57.bvh` | CMU 受試者 16、第 57 段「run/jog, sudden stop」（跑步急停，120 fps） | V12 ③ 推紅毯版：新娘從畫面左邊跑來急停（整段，第 185 格兩腳踩定），之後站著前傾雙手頂在新郎背上 |

## 來源

- 原始資料：CMU Graphics Lab Motion Capture Database，http://mocap.cs.cmu.edu/
- BVH 轉檔：Bruce Hahne（cgspeed.com）2010 年 MotionBuilder 相容版（第 1 格是補上的 T 字站姿，面向 +Z、Y 軸朝上）
- 下載自 GitHub 轉存：https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/035/35_01.bvh（2026-10-07）
- 143_25、141_16（2026-10-09）：同一個轉存 …/data/143/143_25.bvh、…/data/141/141_16.bvh
- 16_33 同一個轉存：https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/016/16_33.bvh（2026-10-09）；82_08：…/data/082/82_08.bvh；81_05：…/data/081/81_05.bvh；82_06：…/data/082/82_06.bvh；16_57：…/data/016/16_57.bvh（以上 2026-10-09）；93_03：…/data/093/93_03.bvh、69_16／69_18：…/data/069/（2026-10-10）；片段說明查 `cmu-mocap-index-text.txt`（同一個 repo）

## 授權

CMU 原文：「This data is free for use in research and commercial projects worldwide.」轉檔者 Bruce Hahne 也沒有另加限制。
不得把資料本身轉賣（含轉檔後的版本）。

致謝文字（有發表時請附上）：

> The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217.

## 已知的資料特性

- CMU（cgspeed 版）的膝蓋在資料裡就偏彎：16_33 站定時兩膝約 30°、35_01 支撐期最直也有 21°（BVH 原始關節角，套到 VRoid 之前）。站定接站姿時膝蓋會從約 30° 打直到 4°。
- 16_33 第 ~342 格（接好的片段裡）右手骨在 120 fps 的一格裡轉 28°（標記點雜訊），情境裡把那一下攤到前後 0.15 秒。
- 停步最後一兩步與站定（片段結束前 0.75 秒起）骨盆漸進抬高約 3 cm、往兩腳中間移 4～7 cm，讓兩膝拉直到約 3°（2026-10-09 使用者裁決；腳踝位置不變）。

- **影格率**：cgspeed 版檔頭一律寫 `Frame Time: .0083333`（120 fps），但 141、143 號照 120 fps 播，揮手是每秒 5 下、舉手 0.25 秒，不像真人；照 60 fps 播是每秒 2～2.6 下，和一般人揮手一樣。所以揮手一律 `src_fps=60`（2026-10-09 判斷，沒有找到官方說明可以對照）。
- 揮手時找過的其他片段：111_37、113_27「Wave」（都是右手、113_27 頭仰得很高）、13_26「direct traffic, wave」（指揮交通，整個人一直轉身）。CMU 沒有「雙手同方向左右揮」的乾淨片段，`wave2_mocap` 是把 143_25 的單手揮鏡射到另一隻手、晚半個週期合成的。

## 注意

- 下載的 BVH 是外部資料：只用 Blender 內建匯入器（`bpy.ops.import_anim.bvh`）讀，不執行檔案內容。
- 只放正式用到的檔。新增檔案時在上表加一列，寫明受試者、片段編號與用到的格。
- **手掌方向**：cgspeed 版的 `LeftFingerBase`／`RightFingerBase` 在 BVH 裡 `OFFSET 0 0 0`（和手腕同一點），不能拿來當手掌方向（2026-10-09 之前 `mocap_retarget` 這樣用，手掌整個往回折、手腕 168～178°）。改用手腕→`HandIndex1`；CMU 走路時手腕一直量到 25～30°（標記點偏差），套用時只取一半、最多 30°。
