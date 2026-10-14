---
description: ZEPETO 黏土風場景與道具：使用者給情境描述、參考照片（Alt+V 貼上或 @圖片檔）或兩者都給 → 拆出要的景與道具 → 先用素材庫現有的，缺的照來源清單上網找免費素材（下載前先問）或自己用 Blender 建 → 加進素材庫、組場景示意、更新展示頁。新查到的素材網站一律記進來源清單。
argument-hint: "[情境描述]（參考照片用 Alt+V 貼上，或 @圖片檔；可以只給照片）"
---

請依照以下需求做 ZEPETO 黏土風的場景與道具，全程使用繁體中文、用白話回報：

**需求**：$ARGUMENTS

你是主控端，這個指令**在對話裡直接做，不派給子代理**。原因有兩個：

- 中途要問使用者：素材用下載的還是自建、下載前要先同意、場景要不要調整。
- 貼上的參考照片只有主控端看得到。

## 會用到的檔案

素材庫在 `.claude/docs/data/blender/library/props-zepeto/`（下面簡稱「素材庫」）。動手前先讀這三份：

| 檔案 | 內容 |
| --- | --- |
| `README.md` | 慣例：原點、方向、尺寸、材質、怎麼加道具與場景 |
| `catalog.json` | 現有道具：代號、中文名、尺寸、分類 |
| `sources.md` | 素材來源清單：每個網站的搜尋網址、授權、註冊條件、適合度，以及查詢紀錄 |

其他會改到的檔案：

| 檔案 | 用途 |
| --- | --- |
| `build_props.py` | 自建道具（`@item`） |
| `external_items.py` | 外部素材登記（`ext_item`） |
| `scenes/<key>.py` | 場景外掛（照 `scenes/_example.py`） |
| `ATTRIBUTION.md` | CC BY 素材要標註的作者 |
| `refs/<key>/` | 參考照片的副本與分析（照片不進版控，`analysis.md` 進版控） |
| `page.json` → `make_page.py` → `index.html` | 展示頁，網址 https://claude.ai/artifact/JSpQF8txGhkEgckXeL6d9w |

```bash
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
LIB="D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/props-zepeto"
export TEMP='D:\render-work\tmp' TMP='D:\render-work\tmp'
```

## 1. 收齊輸入

需求可以是**文字描述**、**參考照片**，或兩者都有。

### 參考照片：找出檔案路徑

| 使用者怎麼給 | 怎麼換成路徑 |
| --- | --- |
| `@圖片檔` | 訊息裡的路徑；相對路徑以專案根目錄 `${CLAUDE_PROJECT_DIR}` 為準，換成絕對路徑 |
| Alt+V 貼上（訊息裡出現 `[Image #N]`） | Claude Code 把貼上的圖存在本 session 暫存資料夾的 `images\N.png`，也就是你的 scratchpad 上一層的 `images` 資料夾 |
| 一般路徑文字 | 直接用 |

貼上的圖找不到時，用 PowerShell 搜（把 `N` 換成 `[Image #N]` 的數字）：

```powershell
Get-ChildItem "$env:TEMP\claude" -Recurse -Filter "N.png" | Where-Object FullName -match "${CLAUDE_SESSION_ID}\\images"
```

- 找到後用 `Read` 打開，確認跟使用者給的是同一張。好幾張圖時，每張都要看。
- 暫存的貼上圖會被定期清掉，所以第 3 步定下場景代號後，馬上把照片複製到 `refs/<key>/`。

### 都沒有、或看不懂

只有一句很短的描述、照片又看不出重點時，用一般訊息問使用者，不要自己猜。
例：「海邊」→ 要問白天還是黃昏、有沒有人物要站的位置、要不要特定道具。

## 2. 拆成清單

把描述和照片拆成一張表：

- 景：地面、背景、天空
- 道具：每一樣
- 每樣的大約尺寸（公尺）、主色、在畫面上的位置
- 白天或夜晚、燈光感覺
- 鏡頭角度

### 從照片分析

1. 逐樣列出畫面裡的東西。前景、中景、背景都要列。
2. 每樣東西：
   - 估尺寸：用畫面裡已知大小的東西當比例尺，例如門高約 2 m、椅面高約 0.45 m、成人約 1.7 m。
   - 取主色：寫成 hex，再對到素材庫 `PAL` 裡最接近的色票。
   - 記位置：相對於畫面中心的左右、前後。
3. 判斷鏡頭：高度、往上或往下看、廣角或長焦。再判斷光線：光從哪個方向來、是白天還是夜晚。
4. **照片是寫實的，我們做的是黏土玩具風**：
   - 造型簡化成大形，細節省略，細的部分加粗。
   - 顏色粉嫩化，但色相跟照片一樣。
   - 不要逐片葉子、逐塊磚去還原。
5. 分析寫成 `refs/<key>/analysis.md`，格式見下方「analysis.md 格式」。

### 對照素材庫

清單裡每一樣都要對照 `catalog.json`：

- **已有的**：直接用。尺寸不同時用縮放，不要重做。
- **類似但不夠像的**：例如照片裡是方桌，素材庫只有圓桌。問使用者要沿用，還是做新的。
- **沒有的**：進第 3 步。

## 3. 缺的道具：找素材，或自己建

1. **先照 `sources.md` 逐站查**：
   - 照「搜尋網址」換關鍵字（英文），用 WebFetch 讀。
   - WebFetch 讀不到內容的站，改用 chrome-devtools 瀏覽器開頁面看。
   - Poly Pizza、Poly Haven、Sketchfab 也可以用 Blender MCP 的搜尋工具。
   - **授權以模型自己的頁面為準。**
2. **清單裡的站都沒有，才用 WebSearch 找新的來源。** 找到新網站時，不管這次有沒有用上，都在 `sources.md` 的「來源」表加一列：
   - 網址、搜尋網址
   - 授權、要不要標註、註冊或付費條件
   - 下載方式、黏土風適合度
   - 哪些資訊驗證過
3. **每次查詢都在 `sources.md` 的「查詢紀錄」加一筆**：日期、情境、要找什麼、查了哪些站、結果。
4. 判斷能不能用：
   - ✅ CC0：直接可用。
   - ✅ CC BY：可用，但要標註作者。
   - ⛔ CC BY-NC、BY-ND、BY-SA：不用。
   - ⛔ 條款不明、禁止再散布：預設不用。
   - 風格不合的不硬用：寫實掃描模型、面數很高、造型細碎。
5. **一次問使用者**（AskUserQuestion，每樣道具一題，最多 4 題一批）：
   - 選項：「下載〈模型名〉（授權、作者、要不要標註）」或「自己用 Blender 建」。
   - 附模型頁網址。
   - 推薦的選項放第一個。
   - 從照片來的道具，也要說明你打算怎麼簡化。
6. **下載一定要使用者同意後才做。**
   - 存到 `external/<代號>/source/`（不進版控）。
   - 需要登入的網站（例如 Sketchfab），請使用者自己下載後把檔案給你，或請使用者設定 Blender MCP 的 API key。**不要要使用者在對話裡貼密碼或金鑰。**

## 4. 加進素材庫

- **下載的**：在 `external_items.py` 加一行 `ext_item(...)`（範例寫在檔案開頭）。
  - `source` 要寫：site、page、title、author、license、downloaded。
  - 匯入後會自動：換成粉嫩化的黏土材質、倒圓、縮到真實尺寸、原點移到底部。
  - 縮放要用 `size`＋`fit`；方向不對用 `rz` 修。
  - 授權是 CC BY → `ATTRIBUTION.md` 加一列。
- **自建的**：在 `build_props.py` 加 `@item("代號", "中文名", "用在哪", cat="分類key:中文")` 函式。
  - 照 `README.md` 的慣例：`p_box`／`p_cyl`／`p_lathe`／`p_sphere`／`p_tube`＋`clay(色票)`。
  - 新顏色先加進 `PAL`。
  - 有參考照片時，照 `analysis.md` 的尺寸與色票做。
- 代號用小寫英數與底線，不能和 `catalog.json` 裡已有的重複。

## 5. 組場景示意

複製 `scenes/_example.py` 成 `scenes/<key>.py`：

- `props` 列出用到的所有道具代號。
- 地面、牆這種只屬於這個場景的東西，直接在 `build` 裡用 `MB` 建。
- 夜景設 `night=True`、`sky`，再寫 `lights`。
- 有參考照片時：
  - 鏡頭照 `analysis.md` 的鏡頭判斷。
  - 擺放照照片的相對位置。
  - 目標是「一眼看得出是同一個場景」，不是逐格對齊。

## 6. 試做 → 自己看 → 正式重建

1. 試做（只建這個場景用到的東西，不覆寫素材庫）：
   ```bash
   "$BL" -b --factory-startup -P "$LIB/build_props.py" -- SCENE=<key> OUT=D:/render-work/zepeto-props/<key>-try1
   ```
2. **自己一張一張看**（`previews/items/*.jpg`、`previews/scenes/<key>.jpg`），檢查：
   - 比例對不對：人物站得進去嗎、桌子高度對嗎。
   - 有沒有懸空、穿插。
   - 顏色有沒有跟素材庫統一。
   - 倒圓有沒有出現。
   - 字讀不讀得到、方向對不對。
   - 有參考照片時，把照片和場景示意拼成一張並排看，列出「哪裡不像」。
3. 有問題就改，再試一輪。最多 3 輪。超過 3 輪還有問題，就照實寫進回報。
4. 正式重建：先跑 `"$BL" -b --factory-startup -P "$LIB/build_props.py"`，再跑 `python "$LIB/make_page.py" --inline`。
   - `--inline` 把圖片轉成 base64 內嵌成單一檔（約 5 MB）：使用者在 Claude app 看不到外部圖檔。
   - 新分類的那一段說明寫進 `page.json` 的 `group_subs`。
5. 發布展示頁：用 Artifact 發布 `$LIB/index.html` 到同一個網址（`url` 帶上方網址），不用帶 `files`、`root`。
   - `index.html` 不進版控（`.gitignore` 已排除），每次發布前重新產生。

## 7. 回報

- **先講結果**：新增幾樣道具、幾個場景、展示頁網址。
- 每樣道具的來源：自建，或下載（網站、作者、授權）。
- 要標註作者的有哪些。
- `sources.md` 新增了哪些網站、查詢紀錄寫了什麼。
- 有參考照片時：哪裡做得像、哪裡簡化了、哪裡還不像。
- 要放進哪部影片、commit、合併 main，都**先問**。

## analysis.md 格式

```markdown
# <場景中文名>（<key>）
- 參考照片：refs/<key>/ref_1.jpg（原檔：<使用者給的路徑或「Alt+V 貼上」>）
- 鏡頭：高約 1.6 m、略往下看、約 35 mm；光：左前方暖陽、白天
| 東西 | 估計尺寸（寬×深×高 m） | 照片主色 | 對到色票 | 位置 | 素材庫 | 做法 |
| --- | --- | --- | --- | --- | --- | --- |
| 木頭長桌 | 1.8×0.8×0.75 | #B98A5E | trunk | 畫面中央 | 無 | 自建 p_box＋p_lathe 桌腳 |
```

## 不要做的事

- 沒問過使用者就下載素材。
- 用 NC、ND、SA 授權，或條款不明的素材。
- 要使用者在對話裡貼密碼或 API 金鑰。
- 只有試做時，就直接覆寫素材庫：試做一定要給 `OUT=`。
- 改 V12 影片的製作程式（`productions/opening-v12/`）。要換進影片是另一件事，先問。
- 改檔內含 Windows 路徑時用 Bash heredoc：`\r`、`\n` 會被吃掉。改用 Write／Edit。
