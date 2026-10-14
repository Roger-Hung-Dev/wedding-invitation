---
name: zepeto-body-generation-workflow
description: ZEPETO 風角色的身體產生入口（/zepeto-body-generation-workflow）。從挑選器面板選大頭（可複選）→ 比對頭有沒有更新 → 關閘門 → 依那顆頭自動量尺寸，長出照 ZEPETO 官方比例的 4.5 頭身身體（VRoid 同名骨架＋前臂扭轉骨、手腳固定模板、頭身接口環、權重清理、膚色、UV、交接尺寸）→ 16 項出廠檢查＋多角度近照自我審查 → 審看網頁（Claude Artifact）→ 照回饋修 → 使用者說可以才出廠（RELEASE.json＋產線狀態紀錄）→ 通知服裝、動畫。使用者說「幫新郎／新娘做身體」「頭更新了，身體重做」「身體要改…」「重新出廠身體」時使用。
argument-hint: "[要做誰／要改什麼]（不用給檔案路徑，頭從面板選）"
---

# ZEPETO 身體產生（入口）

使用者這次給的需求：`$ARGUMENTS`

你是主控端，**在對話裡直接做，不派給子代理**：中途要讓使用者選頭、看審看頁給回饋，出廠也要使用者說可以。全程繁體中文、白話回報。

身體是整條 ZEPETO 產線的上游：頭 → **身體** → 服裝、動畫。身體一改，下游都要重跑，所以出廠前一定要過檢查、使用者說可以。分工與紀錄格式見 `.claude/docs/data/blender/zepeto/pipeline/README.md`（zepeto-director 維護）。

> **2026-10-14 起是 ZEPETO 新版做法**（照 ZEPETO 官方預設身體研究）：4.5 頭身＋官方身形、頭身接口環、手腳固定模板（腳長身高 17%、五根分開雕的腳趾）、前臂扭轉骨、權重清理、表面加密。
> 黏土風時期的做法（5 頭身直管身形、拼裝的手、方塊手、一坨腳、灰色假人比例實驗）已從程式移除，封存在 `D:/render-work/archive/zepeto-body-clay-route-20261014/`，只供查舊版怎麼做的，**不要拿回來用**。
> 已出廠的新郎 v8、新娘 v3、攝影師 v1 是黏土風時期做的，檔案沒動；開場片 B 鎖定新娘 v3。

## 會用到的東西

| 東西 | 位置 |
| --- | --- |
| 身體產生器（背景 Blender，開頭檔跑） | `scripts/body_build.py`（手、腳模板：`hand_template.py`、`foot_template.py`；交接尺寸：`body_measure.py`） |
| 出廠檢查（背景 Blender，開 body.blend 跑） | `scripts/body_checks.py` → `checks.json`（內部會呼叫 `weight_audit.py`、`twist_probe.py`、`limb_probe.py`、`ring_check.py`） |
| 近照 | `neck_probe.py`（脖子）、`hand_probe.py`（手勢）、`twist_probe.py`（手腕扭轉）、`foot_probe.py`（腳）、`limb_shots.py`（手肘膝蓋、胯下、小腿） |
| 開工／取消／出廠（兩份紀錄一起改） | `scripts/body_status.py` |
| 頭清單、身體清單（輸出 JSON，介面契約見檔頭） | `scripts/list_heads.py`、`scripts/list_bodies.py` |
| 審看頁 | `scripts/body_page.py` |
| 診斷工具 | `posture_probe.py`（站姿）、`finger_bend_probe.py`（指節）、`finger_compare.py`（和 Mixamo 比手指）、`surface_probe.py`（表面直紋）、`limb_survey.py`（Mixamo 動作實際轉多大） |
| 身體階段要負責的事、實測過的坑 | [references/checklist.md](references/checklist.md)（**動手前先讀**） |
| 四肢（手臂、腿、手、腳）的製作順序、技術、驗證標準、工具 | [references/limbs.md](references/limbs.md) |
| 身形、頭身接口環、膚色、**參數總表** | [references/zepeto-body-v2.md](references/zepeto-body-v2.md) |
| 研究報告（依據） | `references/research-hands-feet.md`、`research-limb-deformation.md`、`research-body-surface-handoff.md` |
| 挑選器外掛（面板） | 專案 `.claude/mods/zepeto-picker/`（本 skill 的負責人維護） |
| 出廠標記（閘門 hook 讀這份） | `D:/render-work/zepeto-body/build/RELEASE.json` |
| 產出 | 製作中 `D:/render-work/zepeto-body/build/<人>.work/`；出廠後 `build/<人>/`；舊版封存 `build/_archive/<人>_<版本>/`（都不進版控） |

```bash
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
SK="D:/SideProject/wedding-invitation/.claude/skills/zepeto-body-generation-workflow/scripts"
BUILD="D:/render-work/zepeto-body/build"
```

## 1. 選頭（不要叫使用者找檔案）

### 1a. 優先：挑選器面板

工具清單裡有 `mcp__zepeto-picker__pick_head` 時：

1. 先用一句話告訴使用者：「我開大頭選單給你：按數字或字母鍵勾選（可以勾好幾個），按 y 送出，Esc 取消。」
2. 呼叫 `pick_head({ ready_only: true, multi: true })`。工具立刻回傳 → **馬上結束這一輪**，等使用者送出的訊息。
3. 收到的使用者訊息格式固定：
   ```
   我選 2 個頭：
   - 新郎 groom（legacy）：D:/SideProject/wedding-invitation/stylized_face_rig/head_rig.blend
   - 新娘 bride（v1）：D:/SideProject/.../zepeto/bride/rig/head_rig.blend
   ```
   每行最後一個全形「：」後面是頭檔路徑；全形「（」前面最後一個詞是名稱＝身體名稱。拿名稱回 `list_heads.py --ready` 對一次（`ready` 是 true、`blend` 一樣）。
4. 使用者按 Esc、或沒按 y 就打字 → 照打的字處理；看不出選了誰就走 1b。

### 1b. 退回：內建選單

沒有 `pick_head`（請使用者打 `/reload-plugins`；或不是在本專案開的 session）：

```bash
python -I "$SK/list_heads.py" --ready
```

用 AskUserQuestion 複選（`multiSelect: true`），標籤用中文名＋英文名，說明寫版本。超過 4 個就先列出全部、請使用者用文字回。

### 選頭的規則
- 每個人只有一個**現役版本**的頭（`zepeto/<人>/rig/head_rig.blend`；新郎的頭在專案根目錄 `stylized_face_rig/`，不搬）。封存檔、中間檔不會出現在清單上。
- 頭沒做完（`ready` 是 false）不能拿來做身體，照實告訴使用者要等大頭端（分工表 `head`）。
- 身體名稱＝頭的名稱（新郎的頭 → `groom`）。
- **頭身接口環**：大頭端 2026-10-14 起的 AI 網格路線會在脖子做一圈 48 點的接口環（Head 有 `neck_ring_ver`），身體照抄接上，看不出接縫。舊路線的頭（新郎 legacy、新娘 v4、攝影師 v1）沒有環，產生器自動走舊接法（脖子粗細貼合頭的脖子＋把頭縫到身體上，`NECKFIT`、`HEADWELD`）。第 5 步 log 的 `RING` 會寫用了哪種，**沒有環的要寫進回報**。

## 2. 比對上游

```bash
python -I "$SK/body_status.py" check <人> [<人> ...]
```

| 結果 | 做法 |
| --- | --- |
| `[新身體]` | 照常開工 |
| `[一致]` | 頭沒變。使用者是要**改身體**（例：手指、比例）才開工；只是想「重跑」就先問清楚要改什麼 |
| `[頭已更新]` | 告訴使用者哪顆頭從哪版變哪版，這就是要重做的理由，照常開工 |
| `[製作中]` | 上次做到一半沒出廠也沒取消：問使用者要接著做，還是 `cancel` |
| `[沒有頭]`／`[頭未就緒]` | 不開工，回報 |

## 3. 身形（平常跳過）

預設 **4.5 頭身（含頭髮）、ZEPETO 官方身形**：窄軀幹、長腿、手臂腿漸細（三角肌、小腿肚、細手腕腳踝）、手腳固定模板。依據是 ZEPETO Studio 官方預設身體的量測（`zepeto-body-v2.md` 2.1、`limbs.md` 2.1～2.4），使用者 2026-10-14 看對照後同意。

使用者要改頭身比或身材時，用同一顆頭做 2～3 副試做身體並排比，不要自己猜：

```bash
"$BL" -b "<頭檔路徑>" -P "$SK/body_build.py" -- OUT=$BUILD/_n40.work N=4.0 QA=rest,close
"$BL" -b "<頭檔路徑>" -P "$SK/body_build.py" -- OUT=$BUILD/_n45.work N=4.5 QA=rest,close
```

用 `page.json` 的 `extra` 把各副的 `rest_*.png`、`idle_*.png` 並排成一頁（第 7 步），發布給使用者挑。身材倍率另有 `BW`（軀幹寬）、`BD`（厚）、`LW`（上臂大腿粗）、`LEGR`（腿長），見參數總表。

新娘要和新郎不同身高、身材時，要在身體上加形態鍵（**還沒做**：使用者 2026-10-12 說等所有工作流成熟再做）。到時先問兩人身高差與身材程度。

## 4. 開工（關閘門）

每個人一次：

```bash
python -I "$SK/body_status.py" begin <人> --head "<頭檔路徑>"
```

- 狀態紀錄改 `in_progress`；這個人**已經出廠過**的話，`RELEASE.json` 裡這個人的 status 和總 status 也改 `in_progress`。閘門 hook（2026-10-12 起逐身體）：指令點名這個人（`build/<人>/body.blend`、服裝 `OUT=…/<人>`、`BODY=<人>`）的擋，點名別人的照常放行，沒點名任何身體的看總狀態。**新身體不動 RELEASE.json**。
- 開工後用 SendMessage 告訴 zepeto-director「○○ 身體開工」（照分工表；不在就略過，回報裡寫）。
- 已出廠的 `build/<人>/` 整個製作期間都不動；全部在 `build/<人>.work/` 做。

## 5. 產生身體

好幾個人時可以並行（`run_in_background`，每個約 2 分鐘）：

```bash
"$BL" -b "<頭檔路徑>" -P "$SK/body_build.py" -- OUT=$BUILD/<人>.work QA=rest,close,motion
```

- **直接開頭檔，產生器只會另存 body.blend，不會動到頭檔。**
- 先看 log：
  - `HEAD {...}`：自動量的頭尺寸，`chin`（下巴）、`cut`（脖子切口，以下藏掉）、`mouth`、`pivot`；後面的 `CHIN` 寫下巴從哪來：`head neck_chin_bottom`（頭端寫進頭檔的下巴底，新頭都有）或 `rule`（舊頭，用前緣往後退的規則，碰到長 V 字下巴會量太高）。量不到下巴會直接停下來；量得怪（例：切口高過下巴）就加 `CHIN=`、`NECKCUT=`（頭檔座標）覆寫，並寫進回報。
  - `RING`：頭有接口環時是環的來源；`RINGFIT` 是接上的結果（`gap_mm` 12＝在環下 12 mm 切開重接）。
  - `LIMBFIT`：手、腳模板接上的結果（四個接口各一筆）；`WCLEAN`：權重清理掉多少。
- 膚色：預設 `SKINSRC=neck`（取頭的脖子）；頭的脖子貼圖比臉深時用 `SKINSRC=face`（取臉的下半部）。新娘用 face（使用者 2026-10-12：「白一點、貼近臉部顏色」）。`build.json` 的 `skin_source` 記這次用哪個，重做同一個人要沿用。
- 參數都有預設（使用者定過的、研究定的），平常不給。主要的：`N=4.5`、`BW=0.92`、`BD=0.96`、`LW=1.05`、`LEGR=0.615`、`FOOTL=0.17`（腳長÷身高）、`ANKH=0.362`（腳踝高÷腳長）、`SKINSUB=4`、`VOXEL=0.003`、`DECIMATE=1`（不減面）、`TWIST=1`、`WEIGHTCLEAN=1`。全部的值與理由在 `zepeto-body-v2.md` 第 4 節參數總表。使用者要改外型才動，改了寫進回報。
- 產生器做了什麼、順序為什麼不能換：`limbs.md` 1.1。
- 產生器同時存 `build.json`（頭的路徑與 sha、量到的尺寸、接口環、手腳模板、權重清理、交接尺寸 `measure`、這次給的參數 `args`…）和近照。

## 6. 出廠檢查＋自己看

1. 自動檢查（約 3.5 分鐘）：
   ```bash
   "$BL" -b "$BUILD/<人>.work/body.blend" -P "$SK/body_checks.py"
   ```
   16 項，標準寫在 `body_checks.py` 檔頭，白話說明與基準數字在 `limbs.md` 3.1、3.4：
   - **擋出廠（12 項）**：手指彎曲 `bend`、穿插 `interpen`、關節內側擠壓 `crease`、9 個手勢 `gestures`、權重過渡 `weight_trans`、靜止手指 `rest_fingers`、套 Mixamo `retarget`、基本（沒綁點、胯下）`basic`、UV `uv`、權重乾淨 `weights`、手腕扭轉 `wrist`、頭身接口環 `neck_ring`（舊頭沒有環時不檢、算通過）。
   - **參考（3 項）**：四肢活動範圍 `limbs`、腳 `feet`、手指掃描 `v2ref`。門檻還沒定，數字和 `limbs.md` 3.4 差很多就要查。
   - **資訊**：手腳指紋 `fingerprint`。手腳是固定模板，同一副骨架的指紋應該不變；改了身體別處、指紋卻變了，就是模板被動到了。
2. 近照（都只讀 body.blend、可並行；審看頁會自動收這些資料夾）：
   ```bash
   W=$BUILD/<人>.work
   "$BL" -b $W/body.blend -P "$SK/neck_probe.py"  -- OUT=$W/neck_probe          # 脖子接口（露肩的衣服一定要看）
   "$BL" -b $W/body.blend -P "$SK/hand_probe.py"  -- GEST=lib OUT=$W/gestures   # 9 個手勢
   "$BL" -b $W/body.blend -P "$SK/twist_probe.py" -- OUT=$W/twist.json IMG=$W/twist   # 手腕扭 0／80／150°
   "$BL" -b $W/body.blend -P "$SK/foot_probe.py"  -- OUT=$W/feet                 # 轉腳踝、翹腳趾
   "$BL" -b $W/body.blend -P "$SK/limb_shots.py"  -- OUT=$W/limbs                # 手肘膝蓋、胯下、小腿
   ```
3. **自己一張一張看**（照 `references/checklist.md` 的清單；四肢每張「不對的樣子」見 `limbs.md` 3.3）：
   - 站姿（不駝背、不聳肩）、兩腿分開。
   - 脖子接口（沒鋸齒、破口、色差）。
   - 手：沒蹼、沒膜；9 個手勢；手腕扭轉不扭成細頸。
   - 腳：腳底貼地、腳趾不穿進腳掌、縫裡不透出地板。
   - 手肘膝蓋：90° 以上會塌是已知、使用者接受（一般變形的特性）；要看的是有沒有凹口或破面。胯下、下腹扭腿抬腿不皺；小腿沒有直紋。
   - 動作（走路、揮手、坐、比讚、叉子到嘴邊、YA）、UV 格子大小一致。
4. 檢查沒過或看到問題 → 改參數或 `body_build.py` 重跑第 5 步，最多 3 輪；還不行就照實寫進回報。改了 `body_build.py` 的做法，要把原因寫進該處註解、`checklist.md`，四肢的寫進 `limbs.md`。

## 7. 審看頁

1. 寫 `$BUILD/<人>.work/page.json`：`title`、`lead`（一兩句結論）、`changes`（這版改了什麼）、`issues`（已知問題、你自己補或妥協的地方）、`asks`（要使用者決定的事，2～3 題）；要另外並排的圖放 `extra`（`[{"title","note","cols","items":[[絕對路徑, 說明], …]}]`）。
2. 產頁（已出廠過就加 `--prev`，最上面放出廠版和這版並排）：
   ```bash
   python -I "$SK/body_page.py" "$BUILD/<人>.work" <scratchpad>/body_<人>.html --prev "$BUILD/<人>"
   ```
   頁面內容：出廠檢查表（每項白話說明）、站姿、脖子、手、手勢、動作、腳、UV、手腕扭轉、腳近照、手肘膝蓋胯下小腿、四肢活動範圍表、交接尺寸表。
3. 用 Artifact 發布；同一個人之前有審看頁（狀態紀錄的 `page`）就用 `url` 更新同一個網址。好幾個人就各一頁，或在回報裡一起列。

## 8. 回報與回饋迴圈

- **先講結果**：做了誰的身體、出廠檢查幾項通過、審看頁網址。
- 改了什麼、哪裡還不好、要使用者決定的事；頭沒有接口環的要寫。
- 使用者給回饋 → 回第 5 步改，更新同一頁。使用者說「可以」才進第 9 步。
- 使用者決定不做了 → `python -I "$SK/body_status.py" cancel <人>`（已出廠版沒被動過，兩份紀錄改回 released、閘門打開）。

## 9. 出廠

**這個人已出廠的是黏土風時期的版本**（新郎 v8、新娘 v3、攝影師 v1）時，這次出廠＝換成新版骨架和身形：身高 150 → 約 135 cm、骨頭位置全變（腳的骨頭照官方比例重排、前臂多 4 根扭轉骨），服裝要全部重長、動畫已定案的鏡要重套。**出廠前先問導演和使用者換版時機**（開場片 B 鎖定新娘 v3），不要自己決定。

使用者說可以、時機也排好之後，每個人一次：

```bash
python -I "$SK/body_status.py" release <人> --changes "這版改了什麼（一兩句白話，下游重跑時會秀給使用者）" --page <審看頁網址> --tag <英文短代號>
```

- 會檢查 `checks.json` 全過且比 body.blend 新；舊版封存到 `build/_archive/`；暫存資料夾複製到 `build/<人>/`；`RELEASE.json` 寫這個身體的版本、sha、頭、檢查數字、交接尺寸、交接說明；狀態紀錄版本加 1、上游記頭的 sha；最後跑 `status_check.py` 列出哪些服裝、動畫變成「上游已更新」。
- 交接尺寸和上一版差 ≥ 1 mm 或 ≥ 1% 的，會自動接在 changes 後面（`measure_changes`），不用手寫。
- `changes` 要具體。服裝從身體量的東西（骨頭位置、脖子切口高度、拇指根位置）有變就一定要寫。換成新版的第一次出廠，範本見 `limbs.md` 第 5 節：
  - 「4.5 頭身 ZEPETO 身形（身高約 135 cm），骨頭位置全變；腳照官方比例（腳長身高 17%、腳踝關節約 6%），鞋子褲腳要重做。」
  - 「新增 4 根前臂扭轉骨 `J_Adj_*_LowerArmTwist1／2`（約束從手掌算，動畫資料不用改）；衣服要重長。」
  - 「權重已清理：每點最多 4 根、總和 1、左右不互吃。」
  - 頭有接口環的加：「頭和身體用接口環接，看不出接縫。」

## 10. 交接

交接以紀錄為主（下游開工時自己比對），訊息只是加分：

1. 照 pipeline `README.md` 第 1 節分工表，找目前開著的 `outfit`、`anim`、`director` 的 session，用 SendMessage 告訴它們：哪個身體出了哪一版、`changes`、哪些產物要重跑（第 9 步 status_check 的結果）。
2. 換成新版的第一次出廠，給服裝多附這幾條做法（`limbs.md` 第 5 節）：
   - 服裝的 `transfer_weights` 不要再一刀切清 0.01 以下的權重（會皺），改連續版或跳過（身體已經 ≤ 4 根、總和 1）。
   - 鞋子照新腳的 `measure` 做；鞋帶位置要改；鞋口高度約在小腿接口環附近；兩腳併攏很近，鞋寬要收。
3. 找不到的在回報寫「已留紀錄，未通知到 ○○」。
4. **commit、合併 main 一律先問。**

## 不要做的事

- 叫使用者自己找頭或身體的檔案路徑。
- 在 `build/<人>/`（已出廠版）上直接改；存回頭檔；在使用者開著的 Blender 視窗裡做（一律背景 Blender）。
- 檢查沒過、或使用者還沒說可以就出廠；手改 `RELEASE.json` 或狀態紀錄（一律走 `body_status.py`）。
- 黏土風版本的身體要換新版時，沒問導演和使用者就出廠。
- 把封存的黏土風做法（拼裝手、方塊手、一坨腳、5 頭身直管）拿回來用：手腳一律用固定模板，要改形狀就改模板參數（`TPL_*`、`FTPL_*`）。
- 改共用動作程式（`blender-motion-library` 的 `mixamo_retarget.py`）或共用手勢：會動到 V12 已審過的幕，要先問使用者。這副身體專用的手勢微調寫在骨架自訂屬性（`thumb_contact`、`gesture_overrides`）。
- 改頭身接口環的合約（高度、點數、順序）沒通知大頭端：兩邊要一起改（合約見 `zepeto-face-rig/references/research-head-body-seam.md` 5.4）。
- 改 `SKINSUB` 卻沒重校手、腳、脖子的接口係數（`limbs.md` 第 6 節）。
- 改閘門 hook `require-body-release.ps1`：hook 由 zepeto-animation 維護，要改先告訴 zepeto-director。
- 改檔內含 Windows 路徑時用 Bash heredoc：`\r`、`\n` 會被吃掉。改用 Write／Edit，或 Python 寫檔。
