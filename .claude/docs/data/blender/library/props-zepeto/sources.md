# 素材來源清單

`/zepeto-scenes-generation-workflow` 找外部素材時，**先照這份清單逐站查**，查不到才上網找新的來源。
**找到新的來源網站就加一列**，不管這次有沒有用上。每次查詢也在最下面的「查詢紀錄」記一筆，下次就知道哪裡查過、查到什麼。

## 怎麼用這份清單

1. 依「搜尋網址」把關鍵字換進 `{q}`（英文關鍵字，例：`wedding cake`），用 WebFetch 讀結果頁。
   - WebFetch 讀不到內容的站（要跑 JavaScript 的），改用 chrome-devtools 瀏覽器開頁面看。
   - 專案的 Blender MCP 另外有 Poly Haven、Poly Pizza、Sketchfab 的搜尋工具可用。
2. 授權**以模型自己的頁面為準**。網站寫的授權只是預設，Poly Pizza、Sketchfab 這種每個模型都可能不同。
3. 能不能用：
   - ✅ **CC0**：直接可用，不用標註。
   - ✅ **CC BY**：可用，但要在 `ATTRIBUTION.md` 記下作者，影片片尾或喜帖網站的致謝區要列出來。
   - ⛔ **CC BY-NC**（不能商用）、**CC BY-ND**（不能修改；我們一定會換材質）、**CC BY-SA**（改過的成品要用同樣授權釋出）：不用。
   - ⛔ **條款不明**、**禁止再散布**（例如 3D Warehouse）：預設不用，要用先問使用者。
4. **下載前一定先問使用者。**
5. 風格不合的不硬用，改成自己用 Blender 建。不合的例子：寫實掃描模型、面數太高、造型細碎。

## 來源

| 網站 | 搜尋網址 | 內容 | 授權 | 標註 | 註冊／付費 | 下載方式 | 黏土風適合度 | 驗證 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Kenney](https://kenney.nl/assets/category:3D) | 無站內搜尋。看 3D 分類頁：`https://kenney.nl/assets/category:3D`，套件頁 `https://kenney.nl/assets/<套件名>` | 低面數套件：Furniture Kit（家具）、Food Kit（食物）、Holiday Kit（節慶）、City Kit、Car Kit… | CC0 | 不用（不能用 Kenney logo） | 免註冊、免費 | 套件頁按 Download 下載 zip，裡面有 GLB／OBJ／FBX | ⭐⭐⭐ 低面數、方塊感，加倒圓後很合 | 授權已驗證（kenney.nl/support）；套件內容未逐一看 |
| [Quaternius](https://quaternius.com/) | 無站內搜尋。首頁就是全部套件清單 | Ultimate Furniture、House Interior、Food、Stylized Nature MegaKit、Cars… | CC0 | 不用 | 免費（Patreon 是可選的贊助） | 套件頁連到 Google Drive 或 itch.io 下載 zip（GLB／FBX／OBJ／Blend） | ⭐⭐⭐ 卡通低面數 | 授權已驗證（quaternius.com/faq.html） |
| [Poly Pizza](https://poly.pizza/) | `https://poly.pizza/search/{q}`（WebFetch 讀得到標題、作者、模型頁；授權要開模型頁 `https://poly.pizza/m/<id>` 才看得到） | 低面數單件模型（承接 Google Poly）。婚禮類有 Wedding Cake、Diamond ring | **每個模型不同**：CC0 或 CC BY 3.0 | CC BY 的要 | 下載免註冊 | 模型頁原始碼裡有 `https://static.poly.pizza/<uuid>.glb`（模型）與同名 `.jpg`（預覽圖，WebFetch 看不到圖，用 curl 抓 jpg 來看） | ⭐⭐⭐ | 搜尋網址已驗證；條款禁止拿來訓練 AI |
| [Poly Haven](https://polyhaven.com/models) | `https://polyhaven.com/models?s={q}`；HDRI：`https://polyhaven.com/hdris` | HDRI、貼圖、寫實模型 | CC0 | 不用 | 免註冊 | 模型頁選解析度與格式（glTF／blend）；或用 API `https://api.polyhaven.com/files/<id>` | ⭐ 寫實為主，模型少用；HDRI 可當環境光 | 授權已驗證（polyhaven.com/license） |
| [ambientCG](https://ambientcg.com/) | `https://ambientcg.com/list?q={q}`（未驗證） | 貼圖材質、HDRI | CC0 | 不用 | 免註冊 | 資產頁下載 zip | ⭐ 黏土風幾乎不用貼圖，少用 | 授權已驗證（docs.ambientcg.com/license） |
| [Sketchfab](https://sketchfab.com/) | 網頁：`https://sketchfab.com/search?features=downloadable&q={q}&type=models`（要跑 JavaScript，WebFetch 讀不到）。⭐ **公開 API 不用登入**：`https://api.sketchfab.com/v3/search?type=models&q={q}&downloadable=true&count=8`（回 JSON：名稱、作者、`license.label`、`faceCount`、`viewerUrl`、縮圖）；單一模型 `https://api.sketchfab.com/v3/models/<uid>` | 量最大、各種風格 | **每個模型不同**：CC0／CC BY／BY-NC／BY-ND／BY-SA | CC0 以外都要 | ⚠️ **要註冊帳號**才能下載；另有付費商店 | 登入後模型頁 Download（選 glTF）；或 Blender MCP 的 Sketchfab 工具（要 API key） | ⭐⭐ 要挑 low poly／stylized（`faceCount` 幾千以下） | 授權種類已驗證（help.sketchfab.com）；搜尋 API 2026-10-11 實測可用。作者事後可以改授權，**下載當下就要記錄** |
| [BlenderKit](https://www.blenderkit.com/) | 在 Blender 外掛裡搜 | 免費庫有數萬個模型、材質、HDRI | CC0 或免版稅商用授權 | 依條款 | ⚠️ 要裝外掛、要登入；完整庫要付費訂閱 | 只能透過外掛下載 | ⭐⭐ | 來源：CG Channel 報導、Blender 手冊；未實際試用 |
| [OpenGameArt](https://opengameart.org/) | `https://opengameart.org/art-search?keys={q}`（未驗證） | 遊戲素材；Kenney、Quaternius 的部分套件也有放 | 每件不同（常見 CC0、CC BY、GPL） | 依授權 | 免註冊 | 作品頁下載 | ⭐⭐ | 只看過 Kenney Furniture 那一頁 |
| [3D Warehouse](https://3dwarehouse.sketchup.com/) | `https://3dwarehouse.sketchup.com/search/?q={q}` | SketchUp 模型，量大、寫實 | 免費但**不能再散布** | — | 要登入 | 模型頁下載 | ⭐ | ⛔ 預設不用。V12 ⑦b 的 Camry 計程車是使用者自己選的特例 |
| [Coohom](https://www.coohom.com/) | — | 室內設計平台。有「低面數花拱門」 | 自訂的「免費使用」條款，不是 CC | 不明 | 不明 | — | ⭐ | ⛔ 不建議，條款不透明 |

## 查詢紀錄

| 日期 | 情境 | 要找什麼 | 查了哪些站 | 結果 |
| --- | --- | --- | --- | --- |
| 2026-10-11 | 攝影棚加攝影機（`photo_studio`，參考照片 ref_2） | 立在地上的攝影機（現代機身＋頂上監看螢幕＋油壓雲台搖桿＋三腳架） | Poly Pizza（video camera／camera tripod／film camera）、Sketchfab（API：video camera tripod low poly／cinema camera tripod／film camera tripod stylized） | Poly Pizza：Franziska Haaf「Movie / film camera on tripod」（CC BY 3.0，白色廣播攝影機＋腳架，最接近）、dook「Video Camera」（底片捲盤圖示風、沒有腳架）、「Camera stand」（小相機＋細腳架）。Sketchfab：jmadden64「Simple cinema camera on a tripod」（CC BY、4,884 面、腳架很細）、其餘是數萬到數百萬面的寫實掃描。素材庫的 `oldcam` 是復古木頭相機，不同款。⚠️ Poly Pizza 用 Python urllib 會被 403 擋，要用 curl |
| 2026-10-11 | 攝影棚（`photo_studio`，參考照片） | 八角深口柔光罩＋燈架、雷達罩燈＋燈架、空 C 型燈架、白色背景紙卷＋捲軸 | Kenney（3D 分類頁）、Quaternius（首頁）、Poly Haven（API lighting 分類 29 件）、Poly Pizza（softbox／studio light／photo studio）、Sketchfab（API：softbox／beauty dish／c-stand／photo studio backdrop／studio light low poly） | Kenney、Quaternius、Poly Haven 都沒有攝影器材。Poly Pizza：Peter Simcoe「Large Studio Light」（CC BY，其實是遮光板聚光燈）、「Large Support for Lighting」（CC BY，只是一根桁架柱）、Quaternius「Light Stand」（CC0，其實是檯燈）→ 都不合。Sketchfab：方形柔光罩 4 件（Drake ×2、renanz、LagzDesign，CC BY、400～1300 面）外型不像八角深口；KilianPohl「C-Stand」（CC BY，4.3 萬面太細碎）；雷達罩、背景紙卷查無 |
| 2026-10-11 | ZEPETO 風場景研究（V12 開場影片） | 花拱門、結婚蛋糕、桌椅、氣球、紅毯 | Poly Pizza、Sketchfab（搜尋引擎）、Coohom、Kenney、Quaternius | 蛋糕、鑽戒在 Poly Pizza 有（授權要逐個看）；桌椅、餐點、花草 Kenney／Quaternius 有 CC0；花拱門、紅毯、氣球拱門沒有合用的 → 全部自建（V12 第一批 26 樣） |
| 2026-10-12 | 開場片提案 B 婚宴會館（`venue_corridor`／`venue_photo_zone`／`venue_foyer`，導演端委託） | 手持單眼相機、單塊小蛋糕、代客泊車 A 字牌、車鑰匙（另 6 樣門、柱、餐檯、背板直接自建：門要能轉、尺寸要照 ZEPETO 比例） | Poly Pizza（dslr camera／camera／cupcake／cake slice／sandwich board／car key／double door／pillar） | 相機：Poly「Camera」（CC BY 3.0，黑色寫實單眼）、Gabriel「Camera」（CC BY 3.0，方塊復古相機）。蛋糕：Kenney「Cupcake」、Quaternius「Cupcake」、Isa「Cake Birthday Slice」（都 CC0）。A 字牌：「Sandwich Board」（CC BY 3.0，空白黑板）。鑰匙：iPoly3D「Key With Tag」（CC0，沒有圓鑰匙圈）。使用者四樣都選自建（風格與配色統一、不用標註） |
