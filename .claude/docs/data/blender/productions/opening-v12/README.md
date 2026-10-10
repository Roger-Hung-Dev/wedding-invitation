# 開場影片 V12「押花情書・紙質手寫風」的 3D 製作

> 製作說明（使用者原話、修改、成品規格、分工）：`.claude/docs/storyboard/opening-v12-production.md`（以它為準）
> 分鏡：`.claude/docs/storyboard/wedding-becarefulinfo-show-plan-2.md` 版本 12
> 3D 設計素材清單（每幕的景、道具、鏡頭、燈光、站位、動作、合成分工、渲染輸出）：[design.md](design.md)

## 資料夾

```
opening-v12/
├── README.md            本檔
├── design.md            3D 設計素材清單（第一階段的主要交付）
├── scripts/             全部程式（背景 Blender 用 prod_cli.py 當入口）
│   ├── prod_cli.py      背景 Blender 入口（照 bl_cli.py；主命名空間＝新娘專案）
│   ├── run_prod.py      工作入口：MODE=couple｜preview｜full｜painting｜save｜info
│   ├── prod_env.py      共用：路徑、30fps、配色、材質（pmat、顯影材質）、MB 快速網格、角色（新郎＝G）、時間軸 Actor、分層、追蹤點
│   ├── set_desk.py      「俯拍木桌信紙」景與道具
│   ├── set_garden.py    「花園拱門」景與道具（含 ③ 進度條、⑤ 老相機、⑦ 下午茶桌、花瓣）
│   ├── shots_desk.py    ①、②前段、④、⑥、⑧前段／結尾
│   ├── shots_garden.py  ②後段、③、⑤、⑦、⑧中段
│   ├── make_assets.py   2D 素材（系統 Python）：拍立得照片裁切、手機螢幕、郵戳、紙膠帶、押花、明信片、蕾絲、草地、水彩小畫
│   ├── export_segments.py  影格 → 段落預覽 mp4（720p、無字）、抽格拼圖、裁切（⑥ 明信片照片）
│   └── render_lane.sh   一條渲染線：依序渲好幾幕（每幕一個背景 Blender），log 在 D:\render-work\opening-v12\logs\
├── assets/
│   ├── photos/          polaroid_groom.jpg、polaroid_bride.jpg（簡介照裁成拍立得照片區 0.852 比例、900×1056）
│   └── tex/             貼圖（make_assets.py 產生；watercolor_arch.png 由 garden_for_painting.png 轉出）
├── pictures/preview/    每幕代表格（960×540、16 取樣，不跑物理）：<幕>_<秒>.jpg
├── pictures/stills/     正式渲染的代表格（960×540，從 1080p 影格縮）
├── compose-handoff.md   合成交接（影格路徑、72 秒時間軸、分層、track.json、每幕的 2D 元素、轉場）
├── videos/segments/     段落預覽 mp4（無字、720p；成品由 storyboard-video-renderer 合成）
└── blend/               ⛔ 不進版控：couple.blend（新娘服裝檔＋附加新郎）、opening_v12_sets.blend（給人開檔看）
```

影格與中間檔一律在 **D 槽** `D:\render-work\opening-v12\`（`shots/<幕>/<層>/0001.png…`、`timing/` 是估時測試）。C 槽不放任何影格。

## 怎麼跑

```bash
export TEMP='D:\render-work\tmp' TMP='D:\render-work\tmp'      # Python 暫存也走 D 槽
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
S="D:/SideProject/wedding-invitation/.claude/docs/data/blender/productions/opening-v12/scripts"
B="D:/SideProject/wedding-invitation/.claude/docs/data/blender/productions/opening-v12/blend"
P="D:/SideProject/wedding-invitation/.claude/docs/data/blender/projects"

# 0. 同框檔（只做一次；角色或服裝改過才重做）
"$BL" -b "$P/bride/bride_costume.blend" -P "$S/prod_cli.py" -- --run run_prod MODE=couple
# 1. 2D 素材
python "$S/make_assets.py"                                   # 照片裁切與貼圖
"$BL" -b "$B/couple.blend" -P "$S/prod_cli.py" -- --run run_prod MODE=painting && python "$S/make_assets.py" watercolor
# 2. 預覽（幾十秒；SHOT 可以一次給好幾幕）
"$BL" -b "$B/couple.blend" -P "$S/prod_cli.py" -- --run run_prod MODE=preview SHOT=01,02a,02,03,04,05,06,07,08a,08,08c
# 3. 正式渲染（第二階段；背景跑；中斷後重跑會跳過已存在的影格，物理照樣從頭模擬）
"$BL" -b "$B/couple.blend" -P "$S/prod_cli.py" -- --run run_prod MODE=full SHOT=03 LAYERS=beauty
"$BL" -b "$B/couple.blend" -P "$S/prod_cli.py" -- --run run_prod MODE=full SHOT=08 LAYERS=beauty,cast   # 一次模擬渲兩層
# 估時：加 N=12 只算前 12 格（輸出到 D:\render-work\opening-v12\timing\）
```

- ⛔ **只用背景 Blender**：GUI Blender 開新檔會蓋掉別的子代理正在做的東西。
- 每次執行都會重建景（花園 2.6 秒、桌面 1 秒內），改了 `set_*.py` 不用另外存檔。
- 幕的代號：`01` `02a`（②前段桌面）`02`（②後段花園）`03` `04` `05` `06` `07` `08a`（⑧前段桌面）`08`（⑧中段花園）`08c`（⑧結尾桌面）。

## 新郎新娘同框的做法

1. 開新娘的 `bride_costume.blend`（主命名空間：`PROJ`／`WHO`＝bride，裙擺物理 `skirt` 也在這裡）。
2. `scene_lib.add_character(groom 專案)`：從 `groom_costume.blend` 附加所有 `groom_*` 物件與 VRM 碰撞體（`J_Bip_… Collider`，同名的自動變 `.001`）到 `Cast_groom` 集合，再用新郎的 `project.json` 建一份**新郎自己的命名空間** `G`（`G["ARM"]`、`G["ACT"]`、`G["BODY_S"]`、`G["TUNE"]`、鞋底取樣點、表情都是新郎的）。新娘的物件搬進 `Cast_bride`，兩人可以整組開關。存成 `blend/couple.blend`，之後都開這個檔。
3. 擺姿勢：`pose_frame_at(ARM, P, x, y, rz)`（新娘）、`G["pose_frame_at"](G["ARM"], P, x, y, rz)`（新郎）。這是 `scene_lib` 新加的「站到場景某處」版 `pose_frame`：原本的腳底鎖定（`feet`）與動作裡的 IK 目標都假設角色站在原點面向 -Y，直接改 `root` 會把腳留在原點拉長；這裡把 root、腳踝目標、膝蓋方向、IK、掌心方向都換到站位。
4. 物理：VRM 外掛的 `update_pose_bone_rotations` 一次會模擬場景裡**所有**開了 `enable_animation` 的骨架，所以每個子步驟「兩人都擺好 → 新娘裙擺 step → 頭髮更新一次」。包成 `scene_lib.render_cast()`。
5. 換動作時用 `pose_blend_at()` 淡入淡出（兩個姿勢各擺一次、骨頭四元數 slerp），不會一格跳過去。

`scene_lib.py` 新增的通用函式（只新增、既有行為不變）：`add_character`、`place_matrix`、`plant_feet_at`、`pose_frame_at`、`pose_blend_at`、`physics_setup`、`render_cast`。

## 第二階段（正式渲染）

- 新動作 `walk_fwd`、`pull_walk`、`toast`、`taste` 已接上（接法見 design.md §10）。
- 兩條渲染線並行（最多 2 個背景 Blender）：`bash scripts/render_lane.sh A 03:beauty 05:beauty 08:beauty,set,cast`、`bash scripts/render_lane.sh B 02:beauty 07:beauty 01:beauty …`（腳本裡的路徑是本機絕對路徑）。
- 每幕渲完：`python scripts/export_segments.py <幕>` 出段落預覽、`python scripts/export_segments.py --sheet <幕> 秒,秒,…` 抽格檢查。
- 預覽（MODE=preview）不跑物理；正式渲染（MODE=full）跑頭髮與裙擺物理，並量著地腳的滑步（`qa_feet.json`）。

## 情境版（preview-v2，2026-10-06 起）

使用者要先看 ② 玩具槌敲頭、⑦ 圓桌餵食與紅酒乾杯、⑤ 路人甲擋鏡頭的 3D 效果（動作庫第 6、7 節的新動作）。幕代號 `v2_02`、`v2_07`、`v2_05`，和第一版 `02`／`05`／`07` 並存。

| 檔案 | 內容 |
| --- | --- |
| `scripts/set_v2.py` | 新道具：充氣玩具槌（握點＝動作庫 `held_prop('mallet')` 的慣例）、⑦ 圓桌晚餐（落地長桌巾、餐點、紅酒杯＋液面保持水平、叉子、椅子、畫架小黑板）、⑤ 手機 |
| `scripts/shots_v2.py` | 三幕的站位、時間軸、道具每格更新、鏡頭；`Actor2`（每段自己的淡入秒數、舊動作的 palms 改走 palmsw）、`release_arms`、`mallet_carry`、`bow_carry` |
| `scripts/v2_check.py` | 幾何檢查：擺到指定秒數、用變形後的網格量道具／角色之間的穿插與最近距離（`DETAIL=1` 列出哪兩個物件、`VARIANTS=[…]` 一次比較好幾組站位） |
| `scripts/export_v2.py` | 影格 → `videos/preview-v2/<名>.mp4`、封面、抽格總覽（標秒數、22% 字幕線） |
| `scripts/v2_walk_check.py` | ② 走路段快速迭代：逐格量滑步、腳底、穿模、轉速、膝蓋、骨盆、手腕、臉被擋（分段：走路／停步／站定／接站姿＋轉身）＋快速預覽 mp4＋多角度檢查圖（`TAG`、`SHEET_KEYS`、`PREVIEW=0`、`SHEET=0`、`NO_TURN=1`） |
| `scripts/v2_quick_check.py` | ⑤ ⑦ 整幕快速迭代（2026-10-09）：逐格數字檢查（滑步、腳底、穿模、轉速、骨盆、膝蓋、手腕、臉被擋；`MRATE`、`PEN_EVERY`）＋整幕快速預覽 mp4（960×540、EEVEE 8 取樣、無物理；`NAME`、`FROM`／`UPTO`）＋多角度檢查圖（`pictures/preview-v2/<幕>_check[_<TAG>].jpg`）；`BEFORE=1` 關掉男性站姿修正做改前對照。影格在 `D:
\render-work\opening-v12\preview-v2-quick-0507\` |
| `scripts/v2_phys_check.py` | 整段數字檢查（物理開啟）：用已渲好的影格重跑同一個物理迴圈（不重渲），逐格量穿模、腳底、裙擺穿腿、裙子×新郎、槌×人 → `shots/<幕>/phys_check.json` |
| `scripts/quick_tweak.py` | **快修**：只算 T0～T1（前後各加 0.5 秒）、Workbench 出圖、不跑物理、骨頭層級快速檢查（滑步、鞋底、轉速）→ `D:\render-work\opening-v12\quick\<幕>\<TAG>\quick.mp4`、`check.json`。② 走路 116 格約 4.5 分鐘。擺姿勢前關掉所有網格修改器的視窗評估（每格擺姿勢 5.5 秒降到 0.35 秒）。例：`--run quick_tweak SHOT=v2_02 RATE=24 T0=0.8 T1=4.6 TAG=try1` |
| `scripts/set_v2_milestone.py`、`scripts/shots_v2_s0308.py` | 2026-10-09 ③ `v2_03`「愛情里程碑」進度條（兩根白立柱、米白軌道、薰衣草→乾燥玫瑰填色、4 個節點、白圓把手＋玫瑰外框、婚禮光環）＋新郎真人動作接段（35_01 走 → 16_33 停 → 站著卡住 → 82_08 起步 → 16_33 停，`mocap_pull_chain`）；⑧ `v2_08` 拱門下（6.0～9.5 秒）：新郎右手 `wave_arc`（2026-10-09 第 3 輪起；動作庫第 10 節 IK 水平弧形揮手、肩胛跟著抬，取代真人 `wave_r`＋外張 15°——真人資料的肩胛骨轉位後往下壓 43～46°，肩膀塌掉、脖子變長）、新娘 `heart_head` |
| `scripts/set_v2_carpet.py`、`scripts/shots_v2_s03carpet.py` | 2026-10-09 ③ 改版 `v2_03c`「推紅毯」（v2_03 保留）：紅毯卷（越鋪越小 0.52→0.2 m）、石頭、毯上 3D 平貼字「相遇、交往、求婚、婚禮」（霞鶩文楷）；新郎 CMU 81_05 推重物走 → 82_06 頂住推不動／推動往前衝／停步站直，新娘 CMU 16_57 跑來急停 → 站著前傾雙手頂他背 → 82_08 起步＋16_33 停步走到他旁邊；真人資料的手骨會往回折，這裡改成順著前臂、推的時候用 IK 的 hand_tip 轉手掌。檢查：`v2_s0308_check SHOT=v2_03c` |
| 同上（2026-10-10 第 4 輪改版，第 3 輪程式備份在 D:/render-work/opening-v12/backup_r5/） | **拿掉石頭與毯上平貼字** → 立體文字牆 ×4（`cp_wall`：暖白牆板＋金框＋底座＋頂上玫瑰＋一圈小燈泡，字是擠出 1.4 cm 的玫瑰色霞鶩文楷；`cp_light(i, 0～1)` 亮燈＝字發光＋燈泡發光＋前方小點光，0.25 秒亮起後一直亮）：「相遇」「交往」「求婚」在紅毯遠側 x=−2.4 排成一排（左右隔 0.68 m、架高 1.50 m 到新娘頭頂以上：推的那段她站在遠側），紅毯卷推過三個等分點時（0.15／1.65／2.17 秒）依序亮（推的 2 秒卷只走約 0.4 m，照卷的位置排會擠成 0.2 m、字看不清）；「婚禮」在拱門左柱內側 (−0.80, 0.24)、下方「2026.12.12」，紅毯卷停下時亮。新郎：真人推重物沿行進方向整段縮成 0.6 倍（`_stride_scale`：骨盆和腳一起縮、腿 IK 重新對腳、骨盆補高保持膝蓋彎曲）＋前 0.9 秒緩入（`_warp_fn`）＋卡住那段上身多前傾 8°；紅毯卷跟著雙手走（只往前），衝到最快（`t_rel`）放手、卷自己減速滾到拱門前。雙手掌心貼卷（`palm_place`：掌心取樣點來自身體網格、掌心中心落在表面、手指＝前臂投影到切平面；接觸點的弧面角度 a 與卷前後微調 δ 用解析式＋動態規劃挑，讓手腕往上翹接近 40°、手臂伸展 ≤ 0.93）。新娘：16_57 跑來，路線最後 0.55 秒從「他背後」彎到「他左邊」（`yaw`），急停後兩小步靠近 0.17 m（`b_feet_corr`／`leg_shift` 腳照實踩）、上身前傾 55°×0.65、雙手貼他左後腰側（`back_points`，外套 rest 頂點掛在 Spine 骨頭上），推完退回；蓬裙下擺在她靠近時朝他那側壓扁到 0.6（`skirt_squash`：Skirt_Sway 骨頭縮放）。結尾：往右踏步轉身（`step_turn`：2～4 步、重心移到支撐腳、著地腳不動），揮手 `wave_arc('both')`（新郎肩胛抬 20°、新娘 hz 1.3）。 |
| `scripts/v2_03c_contact.py` | ③ 第 4 輪接觸量測：新郎掌心頂點到紅毯卷圓柱面、新娘掌心頂點到新郎外套（帶正負）、蓬裙各層到新郎網格最近距離、手腕角；`CLOSE=1` 手掌近照 → `pictures/preview-v2/v2_03c_hands_<TAG>.jpg`；`OVR={...}` 臨時覆寫 C3 參數做站位掃描 |
| `scripts/v2_03c_shoulder.py` | ③ 第 4 輪肩頸量測（由 `v2_s08_shoulder.py` 複製，`WHO_=groom/bride`）：上臂粗細、脖子露出長度和待機比；`CLOSE=1` 近照 → `pictures/preview-v2/v2_03c_shoulder_<who>_<TAG>.jpg` |
| `scripts/v2_03c_diag.py`、`scripts/v2_03c_diag2.py` | ③ 步幅診斷（新郎每個支撐期落點、步長、兩腳前後距離）／候選真人片段的腳步（試過 81_06、82_07，步幅一樣大，沒用） |
| `scripts/v2_s0308_check.py` | 上面兩幕的快速迭代：逐格數字檢查＋快速預覽 mp4（⑧ 預覽時疊 set 層做 6.4 秒淡入）＋多角度檢查圖（`SHOT=v2_03／v2_08`、`TAG`、`PEN_EVERY`、`STILL_KEYS` 只試看構圖）。⑤⑦ 用的 `v2_quick_check.py` 是另一支 |
| `scripts/v2_07_close.py` | 2026-10-09 ⑦ 臉部近照：新郎、新娘各兩列（頭部正前方 0.6 m／從這一幕鏡頭位置長焦裁臉），每格印出實際套到臉上的 Fcl_MTH_A／MTH_Fun／EYE_Close → `pictures/preview-v2/v2_07_close_<TAG>.jpg`（`V2_07_FACE_LEGACY=1`＝改前、`CF_KEYS`）。⑦ 的表情覆寫在 `shots_v2.py` 的 `F07`／`face07`（Actor2 的 mod；動作庫不動）：新娘 2.64 秒咬下後張眼、2.78～4.18 小幅咀嚼 4 下再閉嘴微笑，新郎 2.6 秒後張眼微笑，舉杯與喝酒都閉嘴微笑、只留眨眼 |
| `scripts/v2_05_hand.py` | 2026-10-09 ⑤ 第 3 輪：路人甲右手逐時間點量測（網格變形打開）：掌心中心／掌心那側頂點到頭髮表面的距離（負＝穿進去）、哪一節手指穿進去、手腕角、手腕與手肘位置（`HKEYS`、`OUT`）。`v2_05_close.py` 會先跑它，把距離標在近照上 |
| `scripts/v2_hand_diag.py`、~~`scripts/v2_hand_close.py`~~ | ⚠ `v2_hand_close.py` 已遺失（2026-10-09 被 ⑧ 的同名檔誤蓋，無備份；⑧ 版改名 `v2_s08_hands.py`）。② 的近照成品已交出，要再拍時以 `v2_s08_hands.py` 為底重建。2026-10-09 手掌反折修正：逐格量 mocap_action 套出來的手腕角（每個 BVH）；② 新郎／新娘手腕＋新郎臉近照 → `pictures/preview-v2/v2_02_hands_<TAG>.jpg`（`HAND_LEGACY=1`＝改前算法）。`v2_quick_check.py` 也加了 `SHOT=v2_02` 與 `HAND_LEGACY=1` |
| `scripts/v2_s08_shoulder.py` | 2026-10-09 ⑧ 第 3 輪「新郎肩膀消失、破圖」：`DIAG=1` 每 `STEP` 秒量新郎骨長／縮放誤差、肩胛骨（Shoulder）相對 rest 抬幾度、上臂抬到水平以上幾度與外張、外套肩頂高度、脖子露出長度、上臂中段粗細（和 `REF_T` 待機比）→ `quick/<幕>_shoulder_<TAG>/diag.json`；`CLOSE=1` 肩頸近照（正面、斜前 45°、背面）→ `pictures/preview-v2/<幕>_shoulder_<TAG>.jpg`。`V2_08_WAVE=wave_r`（環境變數）＝第 2 版對照 |
| `scripts/v2_08_face.py` | 2026-10-10 ⑧ 第 4 輪「新娘微笑笑開」：新娘臉部近照（正面 0.6 m／這一幕鏡頭長焦）× `FK` 時間點，左邊並排 `lib_face_before_after.jpg` 新娘第 4、5 格，每格標實際形狀鍵 → `pictures/preview-v2/v2_08_face_<TAG>.jpg`；`PROBE=1` 比較候選組合（`F08_CANDS`）。表情覆寫在 `shots_v2_s0308.py` 的 `F08`／`b08_face_mod`／`b08_face_keys`（Fcl_MTH_Joy 1＋Fcl_BRW_Joy 1、眼睛全開、7.25／8.75 秒眨眼；`V2_08_FACE_LEGACY=1`＝改前） |
| `scripts/v2_07_fork.py`、`v2_07_grip_search.py`、`v2_07_glass.py` | 2026-10-10 ⑦ 第 5 輪：新郎左手每根手指到叉柄的距離＋手部近照（`pictures/preview-v2/v2_07_fork_<TAG>.jpg`）；握叉手指彎曲與叉柄位置搜尋；酒杯檢查（碰杯間隙、舉杯停留位移、手指到杯腳、唇到杯緣，`V2_07_R2=1` 量第 2 版） |
| `scripts/shots_v2.py` 的 `v2_02_setup_dance`、`scripts/v2_02_dance_check.py`、`scripts/v2_02_skirt_probe.py`（2026-10-10 第 5 輪） | ② 改成跳舞版（`V2_02_DANCE=1` 預設；`=0` 退回敲槌版）：走路停點拉開到 (−0.45, 0.80)／(0.50, 1.08) → 3.80 起真人轉身（新郎 CMU 69_18 第 135～290 格、新娘 69_16 第 2～150 格）→ 5.09 起兩人同一段 CMU 93_03 查爾斯頓（60 fps，第 53～221 格）→ 7.89 起只彎上身的鞠躬（腳不動、膝蓋漸進打直）。三段接成一條 120 fps 序列、交叉淡入 0.25 秒、整條重新鎖腳。新娘：手臂碰到蓬裙就繞胸口前方軸往外張（`arm_clear`）、踢腿穿出裙子時腿往內收（`leg_clear`）。檢查：`v2_quick_check SHOT=v2_02`、`v2_02_dance_check`（腿穿出裙子、手在裙子裡、裙子×新郎、新郎×新娘） → `videos/preview-v2/s02_dance_quick.mp4`、`pictures/preview-v2/v2_02_check.jpg`、`s02_dance_quick_sheet.jpg` |
| `scripts/v2_lib_preview.py` | 動作庫預覽圖（單人正面＋側面、N 個時間點）：`ACT_KEY=wave_arc` → `library/previews/actions/<代號>.jpg` |
| `scripts/v2_walk_diag.py`、`v2_reach_diag.py`、`v2_knee_diag.py` | 診斷：每格轉最多的骨頭、新娘伸手路徑、站定那格的膝角 |
| `scripts/mx_skeleton.py`、`scripts/mx_scene_<幕>.py`（2026-10-10 起，Mixamo 版） | **第 1 關骨骼動作**：Mixamo 動畫（`D:\render-work\mixamo\raw\`，清單 `manifest.json`）原樣套到兩人骨架（動作庫 `mixamo_retarget.py`），只選段落、開始秒數、站位、面向，0.3 秒漸變 → `D:\render-work\mixamo\review\s<幕>\skeleton.json`，給骨骼審看網頁（樣板：動作庫 `assets/skeleton_review/viewer.html`）。② 寫在 `scene_02`，其他幕各自一支 `mx_scene_<幕>.py`（定義 `scene()`）。例：`"$BL" -b "$B/couple.blend" -P "$S/mx_skeleton.py" -- 02`。流程見動作庫 `references/fast-iteration.md` §0、§0.5。② 第 1 輪審看頁：https://claude.ai/artifact/3FfKygCEk1omhUu7QkY9NA |

```bash
# 預覽圖（不跑物理）→ pictures/preview-v2/
"$BL" -b "$B/couple.blend" -P "$S/prod_cli.py" -- --run run_prod MODE=preview SHOT=v2_02 RATE=24 PDIR="<PROD>/pictures/preview-v2" [KEYS=5.3,6.0] [RES=1920,1080]
# 檢查
"$BL" -b "$B/couple.blend" -P "$S/prod_cli.py" -- --run v2_check SHOT=v2_02 RATE=24 KEYS=5.3,6.0 [DETAIL=1]
# 整段（預覽版 1280×720、24fps；影格在 D:\render-work\opening-v12\preview-v2\shots\v2_02\beauty\）
"$BL" -b "$B/couple.blend" -P "$S/prod_cli.py" -- --run run_prod MODE=full SHOT=v2_02 RATE=24 RES=1280,720 OUT="D:/render-work/opening-v12/preview-v2"
python "$S/export_v2.py" v2_02 --name s02_hammer --cover 5.3 --sheet 1.0,2.6,…
# 正式版：拿掉 RATE／RES／OUT（30fps、1920×1080、影格進 D:\render-work\opening-v12\shots\v2_02\）
```

② 的走路（2026-10-09 定案）：純真人動作捕捉 CMU 35_01 ＋ 16_33 停步（`shots_v2.mocap_walk_stop`，資料在 `library/mocap/`），0.78 秒出發、3.95 秒到站定點，停步段膝蓋拉直；4.0～4.45 原地轉身不檢查滑步（`qa_skip`）。說明見 `design.md` §15。舊版成品改名 `videos/preview-v2/s02_hammer_old.*`、影格 `shots/v2_02/beauty_old/`。

⚠️ `scene_lib.pose_frame_at` 會把舊動作 palms 的目標再乘一次站位旋轉（站位 rz≠0 時掌心偏掉）。共用檔沒改（2026-10-07 主控端決定），情境裡用 `shots_v2.Actor2` 把 palms 改走 palmsw 繞過去。

`run_prod.py` 為此加了四個選填參數（不給時行為和以前相同）：`RATE`（影格率）、`PDIR`（預覽圖資料夾）、`OUT`（影格根目錄）、幕的 `skirt=False`（不跑裙擺物理）。
