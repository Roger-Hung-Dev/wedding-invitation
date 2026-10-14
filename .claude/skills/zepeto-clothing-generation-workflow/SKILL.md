---
name: zepeto-clothing-generation-workflow
description: ZEPETO 風人物的穿戴物品（衣服、褲子、裙子、鞋子、領結、首飾、髮飾等）產生入口（/zepeto-clothing-generation-workflow）。照參考照刻出細節（摺、荷葉邊、層次、緞帶做在模型上）＋寫實布料質感（2026-10-14 起取代黏土風）。使用者用 Alt+V 貼參考照片、@圖片檔或文字描述（可混用）→ 從已出廠的身體清單選要穿在誰身上 → 分析參考 → 用共用配方寫成服裝設計檔 outfit.py → 背景 Blender 從身體長出衣物（會垂的布用布料模擬在站姿垂一次定形）、綁骨架、藏住被蓋住的身體 → 多角度近照＋Mixamo 動作穿模檢查 → 審看網頁（Claude Artifact）→ 照回饋修到使用者說可以。使用者說「幫我做這套衣服」「設計這雙鞋／這個領結」「新娘要穿…」「幫新郎加一條項鍊」「改一下西裝顏色」時使用。
argument-hint: "[描述]（參考照片用 Alt+V 貼上，或 @圖片檔；可以只給照片）"
---

# ZEPETO 穿戴物品產生（入口）

使用者這次給的需求：`$ARGUMENTS`

你是主控端，**在對話裡直接做，不派給子代理**：中途要讓使用者選身體、確認看不懂的細節、看審看頁給回饋，而且貼上的圖只有主控端看得到。全程繁體中文、白話回報。

## 會用到的東西

| 東西 | 位置 |
| --- | --- |
| 共用配方與工具 | `scripts/garment_detail.py`（**新衣服用這個**：照參考照刻細節的配方、布料模擬定形、寫實布料 `fabric`、給動畫端的交接資料）＋ `scripts/garment_lib.py`（從身體長衣服的基本動作、舊黏土風配方；已定案的舊衣服還在用，不要刪） |
| 產生器入口 | `scripts/outfit_build.py`（背景 Blender） |
| 審看頁 | `scripts/outfit_page.py` |
| 產線狀態紀錄（比對上游、寫定案） | `scripts/outfit_status.py`；格式與分工表在 `.claude/docs/data/blender/zepeto/pipeline/README.md` |
| 配方一覽與實測過的坑 | [references/recipes.md](references/recipes.md)（**動手前先讀**） |
| 風格與材質（照參考照刻細節＋寫實布料） | [references/style.md](references/style.md)（**動手前先讀**） |
| 服裝素材庫 | `.claude/docs/data/blender/library/outfits-zepeto/`（`README.md`、`catalog.json`、每套一個資料夾） |
| 身體清單 | `python -I D:/SideProject/wedding-invitation/.claude/skills/zepeto-body-generation-workflow/scripts/list_bodies.py --released`（由 zepeto-body 維護） |
| 產出 | `D:/render-work/zepeto-costume/<服裝代號>/<身體名稱>/`（`outfit.blend`、`build.json`、檢查圖；不進版控） |

```bash
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
SK="D:/SideProject/wedding-invitation/.claude/skills/zepeto-clothing-generation-workflow/scripts"
LIB="D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/outfits-zepeto"
```

## 1. 收齊輸入

需求可以是**文字描述**、**參考照片**，或兩者都有。

| 使用者怎麼給 | 怎麼換成路徑 |
| --- | --- |
| `@圖片檔` | 訊息裡的路徑；相對路徑以專案根目錄 `${CLAUDE_PROJECT_DIR}` 為準 |
| Alt+V 貼上（訊息裡出現 `[Image #N]`） | 本 session 暫存資料夾的 `images\N.png`，也就是 scratchpad 上一層的 `images` 資料夾 |
| 一般路徑文字 | 直接用 |

貼上的圖找不到時（把 `N` 換成數字）：

```powershell
Get-ChildItem "$env:TEMP\claude" -Recurse -Filter "N.png" | Where-Object FullName -match "${CLAUDE_SESSION_ID}\\images"
```

- 每張圖都用 `Read` 打開看過。暫存圖會被清掉，第 3 步定下代號後馬上複製到 `<服裝資料夾>/refs/`。
- 只有很短的描述、照片又看不出重點（例：「做件禮服」）→ 用一般訊息問：顏色、長度、領口、要不要參考照。**不要自己猜。**
- 使用者分好幾次補圖（例：先給西裝、再給鞋子）是常態，收到就併進同一套。

## 2. 選身體（不要叫使用者找檔案）

身體清單一律來自 zepeto-body 維護的 `list_bodies.py`（在 skill `zepeto-body-generation-workflow/scripts/`，介面契約見該腳本檔頭；舊路徑 `D:/render-work/zepeto-body/scripts/` 有轉接，輸出一樣）。可以勾好幾個，每個人各做一份合身的。

### 2a. 優先：身體選單面板（mod `zepeto-picker`）

工具清單裡有 `mcp__zepeto-picker__pick_body` 時用它（mod 原始碼在專案 `.claude/mods/zepeto-picker/`，由 zepeto-body 維護；只在本專案開的 session 載入。2026-10-12 前叫 `zepeto-body-menu`）：

1. 先用一句話告訴使用者：「我開身體選單給你：按數字或字母鍵勾選（可以勾好幾個），按 y 送出，Esc 取消。」
2. 呼叫 `pick_body({ released_only: true, multi: true })`。工具會立刻回傳「已開啟身體選單…」→ **馬上結束這一輪**，不要在同一輪繼續做，等使用者送出的訊息。
3. 使用者按 y 後，會收到一則固定格式的使用者訊息（只勾一個也是複選格式）：
   ```
   我選 2 個身體：
   - 新郎 groom（body-v8-fingers-20261012）：D:\render-work\zepeto-body\build\groom\body.blend
   - 新娘 bride（…）：D:\render-work\zepeto-body\build\bride\body.blend
   ```
   - 解析：每一行**最後一個全形冒號「：」後面**是 body.blend 路徑（Windows 反斜線，原樣）；身體名稱是全形括號「（」前面最後一個詞。
   - 拿名稱回 `list_bodies.py --released` 的結果對一次：確認 `released` 是 true、`blend` 一樣，並取 `handoff`。
4. 沒收到這種格式（使用者按 Esc 取消、或沒按 y 就自己打字）→ 照使用者打的字處理；看不出選了誰就走 2b。
5. 面板開不出來（工具回傳 `isPlaced` 等錯誤、或「沒有可選的身體」）→ 照實告訴使用者，走 2b。

### 2b. 退回：內建問題選單

工具清單裡沒有 `pick_body`（例如 mod 還沒載入：請使用者打 `/reload-plugins`；或不是在本專案開的 session）時：

```bash
python -I D:/SideProject/wedding-invitation/.claude/skills/zepeto-body-generation-workflow/scripts/list_bodies.py --released
```

- 輸出是 UTF-8 JSON（`bodies[]`：`name`、`blend`、`version`、`released`、`preview`、`handoff`、`height_m`…）。用 Python 接時讀 `sys.stdin.buffer` 再用 utf-8 解碼（Windows 主控台是 cp950）。
- 用 AskUserQuestion **複選**（`multiSelect: true`）讓使用者勾要穿的身體：選項標籤用中文名（例：新郎 groom、新娘 bride），說明寫版本與身高。題目寫明「可以勾好幾個，每個人各做一份合身的」。
  - 身體超過 4 個（選單一次最多 4 個選項）：先列出全部，問「要哪幾個」，讓使用者用文字回；或分兩題問。
  - 只有一個時也要用一句話確認「穿在新郎身上」。

### 兩種方式都適用
- 衣服是照每個身體各自長出來的，**沒有不屬於任何人的通用衣服**；勾了幾個身體，就做幾份，每份都合身。
- 同一套服裝之後要加人穿，不用改設計，選那個身體再跑一次（第 6 步）就好。
- 想穿的人不在清單裡：不加 `--released` 再跑一次，看是不是「製作中」，照實告訴使用者要等身體出廠；**不要拿沒出廠的身體做**。
- 讀選到的身體的 `handoff`，照它的注意事項做（例如抄權重要略過的群組）。
- 身體出廠閘門（hook `require-body-release.ps1`）會擋：身體沒出廠或 body.blend 被改過時，跑 Blender 指令會被擋下來。被擋就停下來回報，**不要繞過**。

## 3. 決定是新的一套，還是改既有的

讀 `$LIB/catalog.json`：

| 情況 | 做法 |
| --- | --- |
| 全新的一套 | 新代號（小寫英數與 `-`，例：`bride-ballgown`），建 `<代號>/outfit.py`、`outfit.json`、`refs/` |
| 在既有的一套上加東西（例：新郎加胸花） | 改那套的 `outfit.py`，在 `build()` 回傳清單加一件 |
| 只改顏色、長度 | 改 `outfit.py` 的材質或參數 |
| 同一套換另一個身體穿 | 不用改檔，第 6 步換身體跑；`outfit.json` 的 `for_bodies` 加上去 |
| 已定案、下游在用的一套要大改（例：黏土風重做成細節版） | 在 `$LIB/_drafts/<代號>-v2/` 試做，輸出到 `zepeto-costume/<代號>-v2/<身體>`，**不要蓋掉下游正在用的 outfit.blend**；使用者說可以後，換版時機先問導演端（會影響已做好的動畫），確認了才搬回 `<代號>/`、發定案紀錄 |

拿不準時問使用者（例：「新娘的頭紗要做成另一套，還是加進婚紗那套？」）。

## 3b. 開工前比對上游（產線狀態紀錄）

交接不靠訊息，靠狀態紀錄：每套服裝 × 每個身體一筆 `zepeto/pipeline/status/outfit/<服裝>@<人>.json`。格式與規則見 `.claude/docs/data/blender/zepeto/pipeline/README.md`（zepeto-director 維護）；id＝素材庫代號把 `-` 換成 `_`，再接 `@<身體名稱>`（例：`groom_beige_3piece@groom`）。

選好身體（第 2 步）、決定好是哪一套（第 3 步）之後、動手之前，每個身體都比對一次：

```bash
python -I "$SK/outfit_status.py" check <服裝代號> <身體> [<身體> ...]
```

| 結果 | 做法 |
| --- | --- |
| `[一致]` | 照常開工 |
| `[沒有紀錄]` | 新的組合（這套衣服第一次給這個人穿），照常開工 |
| `[上游已更新]` | **停下來**告訴使用者：哪個身體、從哪版變成哪版、上游寫的 `changes`，問要不要重跑。要重跑就不用改設計檔，直接走第 6 步 |
| `[上游未就緒]`／`[製作中]`（身體） | **不開工**，回報使用者要等身體出廠 |

要修改一套**已定案**的服裝時，動手前先把它的紀錄標成製作中，讓動畫端知道先別拿去用：

```bash
python -I "$SK/outfit_status.py" begin <服裝代號> <身體> [<身體> ...]
```

## 4. 拆清單、分析參考

把需求拆成一張表，寫進 `<代號>/refs/analysis.md`（沒有參考照也寫，格式照 `groom-beige-3piece/refs/analysis.md`）：

- 每件物品：照片裡的樣子、主色（hex）、哪些細節做在模型上（摺、荷葉邊、層次、緞帶）、用什麼布料（`fabric` 的 `kind`）、用哪個配方。
- **照參考照刻細節**：輪廓、摺子、層次照照片做，不再簡化成大形；會垂的布用布料模擬在站姿垂一次定形；材質用寫實布料（規則見 `references/style.md`）。
- 照片沒拍到、或看不清的部分（例：背心扣子顏色）你自己補，**在回報和審看頁的「已知問題」寫明是補的**。

## 5. 寫 outfit.py

- 照 `_drafts/bride-blush-ballgown-v2/outfit.py` 的寫法：`import garment_detail as D`，上面用 `D.fabric(名稱, 顏色, 布料種類)` 定材質 `M`，`build()` 依序呼叫配方，回傳物件清單。物件設 `o["role"]`（布料角色），之後要換材質比較時用得到。
- 裙子比手寬（手垂下會陷進裙子）時，手的姿勢交給動畫端（走路提裙、停下來手搭裙側）：`build()` 最後呼叫 `D.skirt_grips`、`D.skirt_radius_table`，寫回 `outfit.json` 的 `anim_handoff`（做法見 recipes.md §4）。**不要為了讓手露出來把裙子縮小**（2026-10-14 試過，使用者說質感變差）。
- 先找 `references/recipes.md` 裡最接近的配方改參數。沒有配方的類別（裙子、首飾…）照該檔「還沒有配方的類別」的方向，在 `garment_lib.py` 加新配方，並補進 recipes.md 的表。
- 露出皮膚的款式（短袖、平口、短裙）要自己寫 `covered(位置)`，不然露出來的地方會被藏掉、變成透明。
- 高度一律從 `G.A` 推（例：`A["HIP_Z"] + 0.12`），少寫死數字，換身體才不會跑掉。

## 6. 試做 → 自己看 → 修

選了好幾個身體時：**先只用第一個身體走完 1～4**（設計還在改，每個身體都跑很浪費）。第一個身體的靜態圖沒問題了，再把每個身體都跑一次完整檢查（第 4 步）。每個身體一個輸出資料夾 `<代號>/<身體名稱>`；背景 Blender 可以同時開好幾個並行跑（`run_in_background`），每個約 5 分鐘。

1. 快速試做（只出靜態圖，約 3 分鐘）：
   ```bash
   "$BL" -b "<身體的 blend 路徑>" -P "$SK/outfit_build.py" -- OUTFIT="$LIB/<代號>" OUT=D:/render-work/zepeto-costume/<代號>/<身體名稱> QA=rest,close
   ```
   - **直接開 body.blend，不要先複製一份**（複本會過期、閘門也核對不到）。產生器只會另存 `outfit.blend`，絕不存回 body.blend。
   - 指令一定要寫 `OUT=D:/render-work/zepeto-costume/...`（閘門靠這段辨認服裝工作）。
2. **自己一張一張看**（`idle_*`、`neck_*`、`chest_*`、`cuff_*`、`feet_*`），檢查：
   - 像不像參考照：並排看，列出「哪裡不像」。
   - 邊緣有沒有尖刺、鋸齒、破洞；配件有沒有被別的衣服蓋住（例：鞋帶被褲管蓋住）。
   - 領口有沒有蓋住脖子接縫的細線；袖口有沒有被拇指撐皺。
   - `build.json` 的 `clips`：「→ 頭」超過 5% 要看是哪個姿勢。
   - 有用布料模擬的：log 裡 `DRAPE <物件> flung N`（被彈飛、已補回的點數）。幾百個以內正常；整件都飛或畫面出現長針（某個點離身體幾公尺）就是模擬或加厚度爆了，看 recipes.md §4 的坑。
3. 有問題就改 `outfit.py`（或配方）再試，最多 3 輪；超過 3 輪還有問題就照實寫進回報。
4. 靜態圖沒問題，再跑完整檢查（加動作，約 5 分鐘）：`QA=rest,close,motion`，看走路、雙手舉高、坐下、握叉子餵食。
5. 跑完核對身體檔沒被改：`sha256sum <body.blend>` 和 `list_bodies.py` 的 `sha256` 一樣。
6. 好幾個身體時，自己並排比較每個人的 `idle_0`、`chest_30`：身形差很多時（例如身高差 10 cm 以上），寫死在 outfit.py 的高度（V 領底、翻折點、褲腰）可能跑掉，要改成從 `G.A` 推算（見 recipes.md §1 的例外說明）。

## 7. 審看頁

1. 更新 `<代號>/outfit.json`：`title`、`status`（`draft`／`approved`）、`for_bodies`、`lead`、`items`（`object` 要對到物件名稱）、`refs`、`issues`、`asks`（要使用者決定的事，2～3 題）。
2. 產頁（同時把小預覽圖存進 `<代號>/previews/<身體>/`）。好幾個身體就把每個身體的輸出資料夾都接在後面，頁面最上面會先放「每個人穿起來」並排比較，下面依身體分節：
   ```bash
   python -I "$SK/outfit_page.py" "$LIB/<代號>" <scratchpad>/<代號>.html \
     D:/render-work/zepeto-costume/<代號>/groom D:/render-work/zepeto-costume/<代號>/bride
   ```
   `outfit.json` 可加 `"body_labels": {"groom": "新郎", "bride": "新娘"}`，頁面就會顯示中文名。
3. 用 Artifact 發布。這套已經有 `review_url` 時，用 `url` 更新同一個網址；沒有就新發布，把網址寫回 `outfit.json` 和 `catalog.json`。
4. 更新 `catalog.json`（新的一套加一筆；狀態、適用身體、網址同步）和 `README.md` 的表。

## 8. 回報與回饋迴圈

- **先講結果**：做了哪幾件、穿在誰身上、審看頁網址。
- 用表格列每件物品的做法；哪些地方是你補的、哪裡還不像。
- 穿模：只講會被看到的（例：「只有雙手舉高時外套會碰到頭」）。
- 列出要使用者決定的事。
- 使用者給回饋 → 回到第 5 步改，更新同一個審看頁。使用者說「可以」→ `outfit.json` 的 `status` 改 `approved`、寫 `approved_at`，同步 catalog，再**每個身體各寫一筆定案紀錄**：
  ```bash
  python -I "$SK/outfit_status.py" release <服裝代號> <身體> --changes "這版改了什麼（一兩句白話）" --page <審看頁網址>
  ```
  - 版本自動加 1（沒有舊紀錄就是 v1）；成品 sha 讀 `outfit.blend`、上游 sha 讀這次實際用的 body.blend。
  - 它說「body.blend 和身體紀錄的 sha 不一樣」→ 身體在你做的期間又改過，不要定案，回報使用者。
  - `changes` 會在下游（動畫）要重跑時秀給使用者看，寫具體（例：「外套改成黑色、加胸花」）。
  - 寫完跑 `python -I "<pipeline>/status_check.py"`，看有沒有動畫段落因此變成「上游已更新」。
- 通知（只是加分，紀錄才是主）：照 pipeline `README.md` 第 1 節分工表，找目前開著的下游 session（動畫）和 zepeto-director，用 SendMessage 告訴它們網址與定案狀態；找不到就在回報裡寫「已留紀錄，未通知到 ○○」。
- **commit、合併 main 一律先問。**

## 不要做的事

- 叫使用者自己找 body.blend 路徑；用沒出廠的身體；繞過身體出廠閘門。
- 存回 body.blend，或在使用者開著的 Blender 視窗裡做（一律背景 Blender）。
- 在動畫時跑布料模擬：布料模擬只能在靜止姿勢垂一次定形、套用成形狀（`D.drape`），動畫時衣服只跟骨架動。
- 新衣服用 `garment_lib.material` 的黏土霧面材質：一律用 `garment_detail.fabric`。
- 拿 ZEPETO 官方的模板或商店服裝；沒問過就下載外部素材。
- 手改 `outfit.blend`：衣服每次都從 outfit.py 重新長，手改的東西下次就不見了。
- 改檔內含 Windows 路徑時用 Bash heredoc：`\r`、`\n` 會被吃掉。改用 Write／Edit。
