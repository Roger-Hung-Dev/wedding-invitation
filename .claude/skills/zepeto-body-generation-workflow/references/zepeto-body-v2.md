# ZEPETO 身體技術文件：身形、頭身接口環、膚色、檢驗工具、參數總表

> 2026-10-14 整理；同日**整合進 SKILL.md**（使用者：「整合到 /zepeto-body-generation-workflow，並把原本黏土風的製作相關移除，改用目前最新研究的」）。
> 工作流步驟看 `SKILL.md`；四肢（手臂、腿、手、腳）的流程、技術、驗證、工具看 [limbs.md](limbs.md)；這份放身形、頭身接口環、膚色、檢驗工具總表、**全部參數**。
> 黏土風時期的做法（5 頭身直管身形、拼裝手、方塊手、一坨腳、灰色假人比例實驗）已從程式移除，封存在 `D:/render-work/archive/zepeto-body-clay-route-20261014/`。

## 0. 狀態總覽

| 項目 | 狀態 | 依據 |
| --- | --- | --- |
| 身形：4.5 頭身、窄軀幹、長腿、手臂腿漸細 | ✅ 工作流預設 | 使用者 2026-10-14：「可以」「照 ZEPETO」；2.1 |
| 頭身接縫：48 點接口環（`fit_neck_ring`） | ✅ 身體端完成、整合測試全 0；`body_checks` 的 `neck_ring` 擋出廠（頭有環時）；頭端正式頭還沒出 | 使用者 2026-10-14 選方案 A；2.2 |
| 膚色取臉（`SKINSRC=face`）、頭貼圖打包 | ✅ 定案 | 新娘 v2、v3；2.3 |
| 手、腳固定模板（腳長身高 17%、五根分開雕的腳趾） | ✅ 工作流唯一做法 | 使用者 2026-10-14 看過手說「可以」、選腳的官方比例；limbs.md 2.3、2.4 |
| 表面加密、光影抄光滑網格、權重清理、前臂扭轉骨、交接尺寸 | ✅ 工作流預設；`weights`、`wrist` 擋出廠 | 研究兩份＋實測；limbs.md 第 2 節 |
| 手肘、膝蓋：一般變形（不加半轉骨、關節平滑） | ✅ 使用者 2026-10-14 看比較圖選「A 維持現狀」 | limbs.md 2.7 |
| 四肢活動範圍、腳（`limbs`、`feet`） | 參考、不擋出廠，門檻等使用者看過數字再定 | limbs.md 3.5 |
| 手指檢查數字在及格線跳 ±1 mm | ✅ 查明是量法的錯，量法 v2 修好 | limbs.md 3.2 |
| 黏土風做法（5 頭身直管、拼裝手、方塊手、掌緣直線、手分開減面、一坨腳、拼裝腳趾、灰色假人比例實驗） | ❌ 已移除（封存） | 被上面幾項取代 |

新版身體**還沒出廠過**。新郎 v8、新娘 v3、攝影師 v1 都是黏土風時期的舊身形；開場片 B 鎖定新娘 v3（導演端）。換成新版要先問導演和使用者（SKILL.md 第 9 步）。

## 1. 流程

工作流的 10 步見 `SKILL.md`；`body_build.py` 內部的順序（量頭 → 骨架 → Skin → 體素 → 掛頭、接口環 → 手腳模板 → 光影 → 綁骨架 → 頭身權重 → 權重清理 → 交接尺寸）與理由見 limbs.md 1.1。

## 2. 技術文件

### 2.1 身形

依據：ZEPETO Studio 官方預設身體正面截圖量的比例（研究頁 https://claude.ai/artifact/JudBvPg4xRPimxfBwRZcwL），單位＝下巴到腳底。

| 參數 | 黏土風（已移除） | 現行（ZEPETO 身形） | 官方對照 |
| --- | --- | --- | --- |
| `N` 頭身（含頭髮） | 5（150 cm） | 4.5（135 cm） | 約 4～4.5 |
| `LEGR` 髖關節高 ÷ 下巴到腳底 | 0.46＋0.06k（約 0.52） | 0.615（胯下 0.53） | 胯下 0.55 |
| `BW` 軀幹寬倍率 | 1.10 | 0.92 | 腋下寬 0.21 |
| `BD` 軀幹厚倍率 | 1.05 | 0.96 | — |
| 手臂節點 | 5 點直線內插 | 三角肌 0.046 → 上臂 0.040 → 手肘上 0.034 → 手肘 0.030 → 前臂肌 0.032 → 前臂下 0.025 → 手腕（`WRF`） | 漸細、手腕細 |
| 腿節點 | 5 點 | 大腿根 0.068 → 上段 0.058 → 前側 0.048 → 膝上 0.040 → 膝 0.040 → 小腿肚 0.039／0.044（往後 9 mm）→ 下段 0.031 → 腳踝 0.025 | 大腿根 0.10、膝 0.075、腳踝 0.05（寬） |

半徑單位 m；兩個數字是 Skin 的（左右, 前後）。`body_checks` 的胯下標準已改成比例（≥ 身高 × 0.30），舊的 0.50 m 在 135 cm 身體會誤判。

### 2.2 頭的量測與接口環

- `measure_head`：頂、下巴、轉軸、嘴、切口（下巴底面結束處，2 cm 一格），切口截面寬厚中心。
- **接口環合約**（頭端寫、身體端讀；全文在 `zepeto-face-rig/references/research-head-body-seam.md` 5.4）：
  - Head 物件自訂屬性：`neck_ring_ver`（1）、`neck_ring_z`、`neck_ring_yc`、`neck_ring_n`（48）；Head 網格點屬性 `neck_ring`（INT、POINT，1～48，其他 0）。
  - 第 1 點正前方（−Y），從上往下看逆時針：13＝+X、25＝+Y、37＝−X。座標＝Head 本地＝頭檔座標（Head.matrix_world 必須是單位矩陣）。
  - 52 個表情在環上位移＝0（頭端把環上方 0.10 頭檔單位內的位移漸變到 0）。
  - 環下面接著胸像，交給身體端 Mask 藏。
- 身體端：
  - `read_neck_ring`：讀環；`RINGTEST=1` 時在舊頭表面射線取假環（只供開發）。
  - `skin_body`：有環時脖子管做到環上方 3 cm（體素＋平滑會收圓管口），不做伸進頭裡的兩節。
  - `fit_neck_ring`：環下 `RINGGAP`（12 mm）切掉上半截 → 拉鍊三角形接到 48 點 → `RINGK`（3）圈 Hermite 過渡（兩端斜率沿身體、頭表面）→ 最上圈＝`head_ring_world`（頭**算完 Mask＋Subdivision 後**的環位置）→ 重展 UV；身體那圈也標 `neck_ring` 1～48。
  - `weld_head`：有環不吸附，只把脖子頂端 100% 給頭骨（切口下 1.2 cm 以上，往下 3.5 cm 漸變）。
  - 坑：bmesh 加圖層會讓手上的點參照失效（先建圖層）；Face_Rig 擺好後要 `view_layer.update()`；Mask 會壓緊點編號，但細分輸出前 M 個點是原始點、屬性值不變。

### 2.3 膚色、材質

- 身體材質複製頭的 `ZEPETO_Skin`（新頭是亮澤：粗糙度 0.5、次表面 0.15），身體自動跟上。
- 膚色取色 `SKINSRC`：`neck`（頭脖子）或 `face`（臉下半部）；新娘用 face。
- 頭貼圖打包進 body.blend（`pack_all`）；頭那段脖子顏色漸層到身體（`blend_head_neck`）。

### 2.4 手 → 已搬到 [limbs.md](limbs.md) 2.3

做法演變（拼裝 → 掌緣直線 → 方塊建模 → **固定模板，現行唯一做法**）、模板的籠子、權重、接身體、定案的形狀參數、調參時踩到的坑，都在 limbs.md 2.3；手勢校正（`thumb_contact`、`gesture_overrides`）在 2.8；手指穿插量法 v2 在 3.2。

### 2.5 腳 → 已搬到 [limbs.md](limbs.md) 2.4

腳模板 v2（現行唯一做法，照 ZEPETO 官方：腳長身高 17%、腳踝關節約 6%、五根分開雕的腳趾；和黏土風版本比，腳的骨頭位置變了）的骨架、籠子、腳趾、權重、結果、坑都在 limbs.md 2.4。`FOOTSHAPE`、v1 趾塊已不用。

## 3. 檢驗工具

| 工具 | 跑法（背景 Blender） | 量什麼 | 標準／看什麼 |
| --- | --- | --- | --- |
| `body_checks.py` | `-b body.blend -P body_checks.py [-- DIAG=1 OUT=… PENV=1 GEO=1.5 LIMBS=0]` → `checks.json` | 16 項：擋出廠 12 項（彎曲厚度、穿插、關節內側擠壓、權重過渡、靜止手指、手勢、套 Mixamo、基本、UV、權重 `weights`、手腕 `wrist`、頭身接口環 `neck_ring`）；參考 3 項（`v2ref`、`feet`、`limbs`）；資訊 1 項（`fingerprint`） | 檔頭；四肢各項的標準見 limbs.md 3.1 |
| `ring_check.py` | `-b body.blend -P ring_check.py` → 印 `RINGCHECK`（`body_checks` 的 `neck_ring` 也是它） | 接口環距離（靜止、轉頭 35°、低頭／抬頭 25°）、法線夾角、張嘴時環移動 | 縫 ≤ 0.1 mm、夾角 ≤ 1°、張嘴環動 ≤ 0.1 mm（只對有環的頭；實測都是 0） |
| `neck_probe.py` | `-- OUT=<資料夾>` | 脖子接口近照：正、右前、右、左、背、從下往上、低頭、抬頭、轉頭 | 目視：粗細、顏色、縫線。**直接開原檔不存**（複製到別處會斷貼圖） |
| 四肢的工具（`hand_probe`、`twist_probe`、`foot_probe`、`limb_shots`、`limb_probe`、`weight_audit`、`body_measure`、`limb_survey`、`surface_probe`、`finger_bend_probe`、`finger_compare`） | 見 limbs.md 第 4 節 | 手、手腕、腳、手肘膝蓋、胯下、小腿、權重、尺寸 | 標準見 limbs.md 3.1、看什麼見 3.3 |
| `posture_probe.py` | `-- OUT=…` | 脊椎前後、上半身正側面 | 駝背、聳肩診斷 |
| `body_page.py` | `python -I body_page.py <工作資料夾> <html> [--prev <出廠版>]` | 審看頁：檢查表＋站姿、脖子近照（含張嘴）、手、手勢、動作、腳、UV；四肢區塊（手腕、腳近照、手肘膝蓋胯下小腿、活動範圍表、交接尺寸）見 limbs.md 第 4 節 | 給使用者 |

### 3.1～3.6 → 已搬到 [limbs.md](limbs.md)

| 原本的節 | 搬到 |
| --- | --- |
| 3.1 手指穿插量法 v2（重量結果、四指掃描、指紋實驗） | limbs.md 3.2 |
| 3.2 四肢第 0 步量測（Mixamo 實際轉多大、表面直條紋確認）、權重清理 | limbs.md 3.4、2.2、2.6 |
| 3.3 表面直條紋修正（`SKINSUB` 4、手腳模板時 3 mm 不減面） | limbs.md 2.2 |
| 3.4 前臂扭轉骨 | limbs.md 2.5 |
| 3.5 四肢活動範圍、跪坐、併腳、手指張合、手指變形方式、手肘膝蓋（使用者選 A） | limbs.md 3.4、2.7 |
| 3.6 交接尺寸、審看頁 | limbs.md 3.4、第 4、5 節 |

### 3.7 頭身接口環整合測試紀錄

2026-10-14 第二顆測試頭（sha 83ab2ff5，頭端修了後頸墊底皮、長髮、碎片）＋新預設身形：`_ringtest2.work`，ring_check 全 0、接縫看不到；剩頭端耳垂下髮際線鋸齒、背面肩膀從頭髮露出一小塊（請頭端用新身形重跑 hair_fit）。身體端觀察：ZEPETO 身形的胸口、肩膀可以看到減面留下的大三角面明暗（面感），之後和手腳的「減面穩定」一起處理。

整合測試範例（2026-10-14，新娘接口環測試頭）：`D:/render-work/zepeto-body/build/_ringtest.work`（全 0）、ZEPETO 身形試做 `_z45.work`、`_z45b.work`（腳趾修正後）。

## 4. 參數總表

| 參數 | 預設 | 狀態 | 說明 |
| --- | --- | --- | --- |
| `N` | 4.5 | 定案 | 頭身比（含頭髮） |
| `BW`／`BD`／`LW`／`LEGR` | 0.92／0.96／1.05／0.615 | 定案 | 見 2.1 |
| `WRF` | 1.0 | 定案 | 手腕粗細倍率（0.92 會讓手指權重變、關節內側擠壓超標） |
| `VOXEL`／`DECIMATE` | 0.003／1（不減面） | 定案 | 體素、減面（見 limbs.md 2.2；黏土風時期 0.0012／0.09） |
| `SKINSUB` | 4 | 預設 | Skin 後細分次數（2 次＝16 邊形管、直條紋；改了要重校接口係數，見 limbs.md 2.2、第 6 節） |
| `NECKFIT`／`NECKBLEND`／`SEAMFIX`／`HEADWELD` | 1 | 沿用 | 脖子貼合、顏色漸層、法線、權重（有環時不吸附） |
| `RINGGAP`／`RINGK`／`RINGEVALTOL`／`RINGTEST` | 0.012／3／0.003／0 | 定案 | 接口環 |
| `SKINSRC` | neck | 沿用 | 新娘用 face |
| `FARING`／`ARMGAP`／`ARMK`、`THC`／`TUF`、`TPL_*` | 0.60／0.012／3、0.0175／0.8 | 定案 | 手模板（一律）：接口、手勢校正、模板形狀，見 limbs.md 2.3、2.8 |
| `FOOTL`／`ANKH`、`FLRING`／`LEGGAP`／`LEGK`、`FTPL_*` | 0.17／0.362、0.70／0.012／3 | 定案 | 腳模板 v2（一律，照 ZEPETO 官方）：骨架、接口、模板形狀，見 limbs.md 2.4 |
| `TWIST` | 1 | 預設 | 前臂扭轉骨（見 limbs.md 2.5） |
| `HALFJ`／`HALFB`、`JOINTCS`／`JCSW`／`JCSF`／`JCSN` | 0／1.0、0／1.6／0.5／10 | 不用（使用者選 A 維持現狀，開關保留對照） | 手肘膝蓋半轉骨、關節帶修正平滑（見 limbs.md 2.7） |
| `HANDDEF` | dqs | 定案（比較過） | 手的變形方式 dqs／lbs／cs（見 limbs.md 2.7） |
| `WEIGHTCLEAN`／`MIDBAND` | 1／0.02 | 預設 | 權重清理（見 limbs.md 2.6） |
| `SMOOTHNRM` | 1 | 預設 | 減面後的光影抄減面前的光滑網格（手腳模板與過渡帶漸變）；只影響之後新做的身體 |
| ~~`ZSHAPE`、`HANDTPL`、`FOOTTPL`、`BOXHAND`／`BOX*`、`FOOTSHAPE`、`EDGERAIL`、`HANDKEEP`／`HANDDEC`、`PALMW`、`KBW`、`RAILZ`、`RAILR`~~ | — | 已移除（2026-10-14） | 黏土風時期的開關，程式已拿掉，給了也沒作用；封存資料夾有舊程式 |
| `CHIN`／`NECKCUT` | — | 備用 | 量錯時覆寫 |

## 5. 整合紀錄（2026-10-14）

- **做了**：SKILL.md 全部步驟改成新版（選頭時說明接口環、第 3 步改用試做身體比頭身比、第 5 步新預設與 log、第 6 步 16 項檢查＋5 組近照、第 9 步換版要先問導演和使用者＋changes 範本、第 10 步給服裝的做法）；`body_build.py` 拿掉黏土風路線（v10）；`body_checks.py` 併進接口環檢查；刪比例實驗工具；`checklist.md` 改寫。細節見 limbs.md 第 8 節。
- **驗證**：新預設重做的 `_v10.work` 和整合前的 `_final.work` 完全一樣（手腳指紋、尺寸、檢查數字）。
- **沒做**：`list_heads.py` 輸出「有沒有接口環」（要開 .blend 才知道，太慢；改成看產生器 log 的 `RING`）；頭端的頭髮內側切邊、插進身體的頭髮點、後頸單色皮（頭端在修，見 `integration-test` 回報）。
- **換版**：新身形出廠時，服裝（衣服全部重長）、動畫（骨頭位置全變，已定案的鏡要照上游更新重跑）都要先經導演排程；新娘 v3 被開場片 B 鎖定。

## 6. 相關文件與頁面

| 內容 | 位置 |
| --- | --- |
| ZEPETO 身體研究（官方預設身體對照） | https://claude.ai/artifact/JudBvPg4xRPimxfBwRZcwL |
| ZEPETO 身形試做對照頁 | https://claude.ai/artifact/SdGfXqvjgQLZNvU8Yvr6zk |
| 接口環整合測試頁 | https://claude.ai/artifact/Voed3yFYxNmtvpNSKXFqNS |
| 手腳模板新舊對照頁（方案 A） | https://claude.ai/artifact/NCwf1LZPwoezVfY4ysvSrp |
| ZEPETO 腳掌研究＋腳模板 v2 | https://claude.ai/artifact/Cuefy2mtUSjs87pzmnpBS8 |
| 四肢強化試做（權重、表面、扭轉骨、四肢、尺寸） | https://claude.ai/artifact/To5UKLJRN7rn9iY86gUEdQ |
| **四肢：製作流程、技術、驗證、工具（單一出處）** | `references/limbs.md` |
| 四肢研究報告（兩份） | `references/research-limb-deformation.md`、`references/research-body-surface-handoff.md` |
| 頭身無縫研究＋接口環合約 | `.claude/skills/zepeto-face-rig/references/research-head-body-seam.md` |
| ZEPETO 臉研究 | `.claude/skills/zepeto-face-rig/references/research-zepeto-face.md` |
| 手腳檢驗與調整研究（2026-10-14 完成；推薦方案 A：手腳固定模板＋前臂、小腿接口環；第 0 步先修量測） | `references/research-hands-feet.md` |
| 身體階段的檢查清單與坑 | `references/checklist.md` |
| 黏土風時期的程式與文件（封存，只供查） | `D:/render-work/archive/zepeto-body-clay-route-20261014/` |
