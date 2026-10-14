# 穿戴物品配方與實測過的坑

兩個配方檔：`scripts/garment_lib.py`（從身體長衣服的基本動作＋舊黏土風配方，2026-10-11～12 新郎西裝起）、`scripts/garment_detail.py`（2026-10-14 起的「照參考照刻細節＋寫實布料」配方，**新衣服用這個**，見 §4）。
新物品先找最接近的配方改參數；真的沒有才加新配方（細節配方寫進 `garment_detail.py`，並補進 §4 的表）。材質一律用 `garment_detail.fabric`，不用 `garment_lib.material`（那是黏土風）。

## 1. 基準高度 `G.A`（全部從身體量，不寫死）

| 鍵 | 意思 | 來源 |
| --- | --- | --- |
| `SH_Z` | 肩關節高 | `J_Bip_L_UpperArm` |
| `WRIST_X` | T 字站姿的手腕 x | `J_Bip_L_Hand` |
| `NECK_Z`、`HIP_Z`、`ANKLE_Z`、`FOOT_X` | 脖子根、髖、腳踝高；腳的 x | 骨頭 |
| `CROTCH` | 胯下高（正中線最低點） | 身體網格 |
| `SEAM` | 頭模型切口高（約 1.176 m） | 頭網格套 Mask 後最低點 |
| `COLLAR_TOP` | 有領上衣的領子上緣＝切口上方 1.8 cm | 推算 |
| `SLEEVE_X`／`CUFF_X` | 外套袖口（手腕前 3.5 cm）／襯衫袖口（多露 2.3 cm） | 推算 |
| `HEM` | 外套下襬＝髖關節下 4.5 cm | 推算 |

> 例外：少數造型高度（V 領底 0.83～0.95、翻折點 0.86、褲腰 0.74）目前寫在 outfit.py 裡，是 150 cm 新郎量出來的。換到身高差很多的身體時要改成比例（例如 `A["HIP_Z"] + 0.12`）。

## 2. 配方

| 配方 | 做什麼 | 重點參數 |
| --- | --- | --- |
| `shirt` | 有領襯衫（立領蓋接縫） | `show`：只保留會露出來的面；`collar_top`、`cuff_x` |
| `jacket` | 西裝外套 | `open_pts`（前襟開口折線）、`lapel_pts`＋`break_z`（領片）、`hem`、`flare` |
| `vest_front` | 背心前片 | `top`、`v_bottom`、`hem` |
| `trousers` | 長褲 | `waist`、`hem`、`flare` |
| `shoes` | 包鞋 | `top`、`toe`（鞋頭往前拉多少） |
| `laces` | 鞋帶 | `ys`（腳背上的位置） |
| `bowtie` | 領結 | `wing`（翼的半徑） |
| `collar_tips` | 襯衫尖角翻領 | 貼在 `on_obj` 領口 |
| `buttons` | 一排扣子 | `zs`、`x`、`size` |
| `patches` | 貼在表面的圓角扁方塊（口袋、胸袋） | `specs`＝[(x, z, 半尺寸)] |
| `material` | 黏土風材質（舊；新衣服改用 `garment_detail.fabric`） | `rough`（0.65～0.85）、`sheen`（緞面）、`coat`（皮革、飾品）、`metallic`、`alpha` |
| `hide_body` | 藏住被蓋住的身體（只藏不刪） | `covered(位置)` |

### 還沒有配方的類別（第一次做時照這個方向，做完補進上表）

| 類別 | 建議做法 |
| --- | --- |
| 短袖、無袖上衣 | `shirt` 改 `cut_sleeves` 的 x；**`covered` 要自己寫**，手臂露出來的地方不能藏 |
| 裙子、婚紗裙擺 | **已有配方 `lathe_skirt`**（2026-10-12 新娘禮服）：不從腿複製（兩腿會變兩條管），用身體腰圍剖面當上緣、照 `bell` 張成鐘形到 `r_hem`；`lobes` 做下襬波浪或外層垂片。權重用 `bind_skirt` 自訂：上緣全給骨盆、越往下越多分給同側大腿（`leg_share`），走路會跟著腿擺。細節版改用 `garment_detail.tulle_layer`（§4）。坐下時裙擺會往上翻，要坐的鏡頭另外處理 |
| 平口、露肩禮服 | **已有配方 `strapless_bodice`＋`petal_neckline`**：上緣在 `A["ARMPIT"]`（從上臂量出的腋下高）下 1.2 cm，水平切不會切到 T 字手臂。上緣權重用 `drop=NO_ARM`：手臂權重只留 25%、其餘轉給胸口，舉手時上緣不會被拉走（直接刪掉手臂權重會讓只綁手臂的點停在原地、變成尖刺）。藏身體要自己寫 `covered`（上緣以下全藏）。腰帶 `sash`、布花 `rosette`、背後大蝴蝶結 `back_bow`（給 `drape_obj`＝外層裙，尾巴沿裙子背面貼著往下、抄裙子的權重；直直垂會埋進往外張的裙子） |
| 頭紗 | 一片半透明面（`alpha` 0.3～0.5）＋ 2～3 串骨頭；權重抄 `J_Bip_C_Head` |
| 首飾（耳環、項鍊、戒指） | **耳環已有配方 `flower_earrings`**（耳垂從頭網格左右最外側那圈的最低點找，`bind_rigid` 只跟頭骨頭）。其餘：小配件：`blob` 串珍珠、圓環用 `create_cone` 或 torus。權重抄最近的骨頭（耳環→頭、項鍊→上胸、戒指→那根手指第一節）。尺寸放大一點，才看得到 |
| 髮飾 | 掛在頭上，權重全部給 `J_Bip_C_Head`；位置用頭網格射線找 |
| 手套 | 從手複製加厚 1～2 mm；手指彎曲時看指節有沒有破 |

## 3. 實測過的坑（都發生過）

| 坑 | 會怎樣 | 怎麼避 |
| --- | --- | --- |
| 先切再推厚 | 切口的點抹不到，邊緣鋸齒、出現尖刺 | **先 `inflate` 再切**；`inflate` 會先合併過近的點、清退化面 |
| 領口整個水平面切 | T 字站姿上臂比領口高，肩膀被切出一個洞 | 用 `cut_neck`（只切脖子那一圈） |
| 領子高度跟脖子骨頭走 | 身體降肩時領子跟著掉，露出頭切口那條細線 | 跟 `SEAM` 走（`COLLAR_TOP`） |
| 袖口切在手腕 | 拇指根部把袖口撐成一圈皺折 | 外套袖口在手腕前 3.5 cm |
| 外套下襬用胯下當基準 | 舊身體胯下黏到 0.37 m，下襬跟著亂掉 | 用 `HIP_Z` |
| 襯衫整件都做 | 動作時從外套底下冒出來 | `shirt(show=…)` 只做露出來的部分 |
| 身體沒藏 | 動作時身體從衣服底下戳出來 | `hide_body`；露皮膚的款式要自己寫 `covered` |
| 開口折線最後一點沒收成 0 | 那個半寬一路延用到下襬，整條前襟被挖開成鋸齒縫 | 只開到某高度時，最後加一點半寬 0 |
| 鞋帶放太後面 | 被褲管蓋住看不到 | 排在腳背 y −0.048 之前 |
| 抄權重時把非骨頭群組也抄過來 | HAND_DQS 之類的群組混進衣服 | `transfer_weights` 只建骨頭名的群組 |
| 存回 body.blend | sha 變了，身體出廠閘門會擋住所有人 | `outfit_build.py` 只用 `save_as_mainfile(copy=True)` 存成 outfit.blend |
| Bash heredoc 寫含 Windows 路徑的 Python | `\r`、`\n` 被吃掉，只出 SyntaxWarning | 改檔用 Write／Edit；要跑的 patch 寫成 .py 再 `python -I` 執行 |

## 4. 細節配方（`garment_detail.py`，2026-10-14 新娘細節版禮服起）

實做範例：`library/outfits-zepeto/_drafts/bride-blush-ballgown-v2/outfit.py`。

| 配方 | 做什麼 | 重點參數 |
| --- | --- | --- |
| `fabric` | 寫實布料材質 | `kind`＝organza／satin／tulle／lining／canvas／metal（實測過）、wool／cotton／knit／denim／leather／pearl（起始值）；`override` 蓋個別值 |
| `tulle_layer` | 鐘形蓬裙的一層紗：不規則直摺（幾組不同數量的波疊起來）、腰上細抽皺、下襬微高低 | `r_hem`、`bell`、`folds`、`fold_amp`、`hem_wave`；疊 3 層（襯裙 `lining`＋兩層 `tulle`，半徑各大 2 cm 左右） |
| `draped_bodice` | 平口上身＋從腰間布花往右肩散開的放射摺 | `knot`（摺的中心）、`folds`、`amp` |
| `ring_bodice` | 同上，但每個高度量一圈身體外框排成乾淨網格（備用：修得掉胸下暗痕，使用者整體上選了 `draped_bodice`） | 同上＋`ease` |
| `rolled_neckline` | 平口上緣：往上立起、再往外翻下來的捲邊摺紗，高低不平 | `z`（上緣高） |
| `wrap_fold` | 斜斜包過胸口的一片摺紗 | `p0`、`p1`＝(x, z) 起點終點 |
| `peplum` | 腰下外層紗：大軟摺、正前方斜開口、後面較長；布料模擬垂一次 | `length`、`open_front`、`rolls`、`roll_amp` |
| `cascade` | 瀑布荷葉邊：沿裙面一層層往下疊；布料模擬垂一次 | `z_top`、`length`、`span`（角度範圍）、`wave_len`、`amp`、`drop_back` |
| `ribbon_rose` | 一條緞帶捲成的玫瑰 | `size`、`turns` |
| `ribbon_tails` | 會扭轉、末端燕尾的緞帶垂帶，貼著衣服表面 | `surfaces`（貼哪幾件）、`length`、`ends`、`back` |
| `ribbon_bow` | 中空緞帶圈的大蝴蝶結 | `size`、`ribbon`（帶寬） |
| `drape` | 布料模擬垂一次定形（上面幾個配方內部用） | `pin_fn`（釘住哪裡）、`stiff`（彎曲剛性） |
| `copy_weights` | 抄另一件衣服的權重（掛在裙子上的東西跟著裙子動） | `src` |
| `skirt_grips` | 提裙掛點（給動畫端） | `z`（抓點高）、`angle_deg`、`radius` |
| `skirt_radius_table` | 裙面半徑表（給動畫端擺手） | `step` |

### 大蓬裙要交接給動畫端（`anim_handoff`）

裙子比手寬時（手垂下會陷進裙子），手的姿勢交給動畫端：走路時提裙、停下來時手指搭在裙子最外層。服裝端要在 `build()` 裡做兩件事：
- `skirt_grips(...)`：外層紗與荷葉邊加 Hook 修改器（排在 Armature 後面）＋ `SkirtGrip_L/R`（父物件是骨架**物件**）＋ `SkirtGripAnchor_L/R`（掛在骨盆骨頭上、跟著身體走）。動畫端每格：`SkirtGrip.location = grip_rest + 骨架物件旋轉的反矩陣 @ (手指捏住的世界座標 − 錨點的世界座標)`。
- `skirt_radius_table(...)`：每 5 cm 一列 `[z, 正面, 側面, 背面]`。
- 兩樣都寫回 `outfit.json` 的 `anim_handoff`（動畫端從這裡讀；換身體重長自動更新），也存一份 `<OUT>/skirt_handoff.json`。寫法照範例 `outfit.py`。

### 細節做法踩過的坑（2026-10-14，都發生過）

| 坑 | 會怎樣 | 怎麼避 |
| --- | --- | --- |
| 布料模擬時布貼得太近碰撞面、布太軟 | 皺成一堆碎摺，一些點被彈飛成尖刺 | 布離碰撞面 ≥ 1 cm 再垂；彎曲剛性 18（歐根紗挺）、品質 10、只算 16 格；`drape` 會把被彈飛的點用鄰點平均補回、再抹平 |
| 彈飛的點直接拉回原位 | 和旁邊已經垂下的點脫節，拉成更長的尖刺 | 用沒爆的鄰點平均補（`drape` 已內建） |
| Solidify 開「厚度一致」（even offset） | 頭尾重疊的尖角算爆，一個點飛到 6 m 外，畫面出現一根長針 | `thicken` 一律關掉 even offset |
| 從身體複製的上身再細分、或往內抹平 | 身體網格的小凹凸放大成斑點；抹平時網格交疊成鋸齒 | 不細分；要修胸下暗痕用 `ring_bodice`（只往外填） |
| Hook 的空物件放到手指的絕對位置 | 裙子已經跟身體走過一次，又被拉一次（人走 2 m 裙子多拉 2 m） | 空物件掛骨架物件、只給「相對靜止」的位移；另給跟身體走的錨點（`skirt_grips`） |
| 量裙子剖面時用胯下以下的高度 | 兩腿分開，正前方的射線穿過腿縫，剖面量不準 | 胯下以下改用胯下上方那一圈當外框 |
| 為了讓手露出來把裙子縮成 A 字 | 使用者覺得質感變差（2026-10-14） | 裙子照照片；手的問題交給動畫端（提裙、手搭裙側） |
