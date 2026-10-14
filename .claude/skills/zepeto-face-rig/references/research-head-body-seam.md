# 頭和身體無縫接合：業界做法與我們的方案（2026-10-14）

> **2026-10-14 已實作方案 A**（使用者選：環照每顆頭量、先不焊、現在就做）：頭端 `scripts/neck_ring.py`、身體端 `body_build.py` 的 `fit_neck_ring`。實作與合約定案見 [ai-mesh-route.md](ai-mesh-route.md)「頭身接縫」；跟本報告草案不同的地方：環以下的胸像接在環下面（不切開）、環附近的表情位移漸變到 0、後頸整片補皮。
>
> 研究範圍：上網查業界怎麼把分開做的頭和身體接到看不出接縫，再對照我們的程式提方案。
> 研究方式：只讀專案程式、上網查資料。**沒有改任何程式、沒有跑 Blender、沒有上傳任何模型或照片。**
> 讀過的程式：頭端 `scripts/pack_head.py`、`scripts/hair_fit.py`（局部）、`references/ai-mesh-route.md`「接身體」；身體端 `zepeto-body-generation-workflow/scripts/body_build.py`（`measure_head`、`skin_body`、`attach_head`、`blend_head_neck`、`weld_head`、`seam_normals`）、`neck_probe.py`、`SKILL.md`；服裝端 `garment_lib.py`（怎麼找頭和身體）；動畫端 `zanim_lib.py`（怎麼找頭和身體）；身體端的 ZEPETO 身體研究報告；新娘試接的 `build.json`。

先解釋幾個會一直出現的詞：

| 詞 | 白話 |
| --- | --- |
| 接縫 | 頭的網格和身體的網格在脖子相接的那一圈 |
| 邊環（edge loop） | 網格上首尾相接繞一圈的一串邊；這裡指脖子上一圈點 |
| 接口環 | 兩邊約好的那一圈點：點數、高度、每個點的位置都一樣 |
| 法線（normal） | 每個點「朝哪個方向」，決定光打上去的明暗；兩邊法線不同，接縫就會出現一條明暗不連續的線 |
| 權重（weight） | 每個點跟哪根骨頭動、跟多少；兩邊權重不同，轉頭時接縫會裂開 |
| 形態鍵（shape key） | 同一個網格存好的變形（例：ARKit 52 個表情），在 Head 物件上 |
| 焊（weld／merge） | 把兩個位置重合的點合併成一個點，兩塊網格變一塊 |

---

## 1. 結論（先看這段）

1. **業界沒有人靠「兩塊不相干的網格硬貼」做到無縫。** 做法只有三種：
   - **同一塊網格**：Daz Genesis、MakeHuman、Character Creator（Headshot 會把 CC 的標準網格「鋪」到你的頭上）。
   - **兩塊網格，但接縫那一圈點完全重合**，再把法線、權重、顏色做成一樣：MetaHuman（遊戲裡頭和身體仍是兩個網格）、FaceGen（頭可以定義一圈「永遠不變形的脖子接縫」）、柏德之門 3 模組社群的「脖子移植」、一般遊戲的模組化角色。
   - **對不齊，就用衣服蓋**：Ready Player Me 官方文件直接建議用衣服或配件蓋住脖子。
2. **「焊成同一塊」不是無縫的必要條件。** 真正必要的是四件事在接縫兩側一致：**點的位置、法線、權重、顏色**。柏德之門 3 的換頭教學就是把原版頭底部兩圈點移植到新頭上，頭仍是獨立網格，接縫照樣消失。
3. **我們現在的方向是對的，差在「位置」這一項。** 法線（`seam_normals`）、權重（脖子頂端 100% 跟頭骨）、顏色（`blend_head_neck`）都已經在做。但頭的切口是不規則的一圈，靠「把頭的邊吸到身體表面」硬貼上去（新娘最多吸了 13～14 mm）。身體脖子是橢圓管，AI 頭的脖子不是橢圓，所以**頭被拉變形，兩邊的點也不重合**。
4. **推薦方案 A：約定一圈「標準脖子接口環」，頭和身體仍是兩個物件，但接縫點對點重合。**
   - 頭端在 AI 頭上做出這一圈：48 點、固定高度、固定起點和方向。
   - 身體端**不再量、不再吸**，直接把身體脖子頂端那一圈做成同樣的 48 個座標，往下 1～2 cm 平順過渡回身體。
   - 臉部 52 個表情、服裝端、動畫端的程式都不用改，看起來等同焊成一塊。
   - 身體端提議的「之後焊成一塊」（方案 B）可以留到以後：環重合之後，焊只是多一步「合併距離 0 的點」。現在就焊，會動到服裝、動畫、臉部骨架三邊的介面，風險大、好處小。
5. **後頸的深色鋸齒邊**：報告交出後主控端實測（見 4.3）——推測**成立而且更大**：整片後頸（正後方左右各約 60°，從肩頸底座到下巴以上）都不在 Head 上，是身體的脖子圓管從後面補的。下面是研究員當時的推測，保留做紀錄：
   **（原推測）最可疑的原因是「後頸破了一個洞」（推測，還沒實測）。**
   - 頭端把頭髮切成 Hair 物件時，AI 畫成頭髮色的後頸面會跟著頭髮走，Head 的後頸就留下一個鋸齒邊的洞。
   - `hair_fit.py` 只固定下巴往下 5 公分以內的頭髮接縫，更下面的頭髮被往後推，洞就露出來。
   - 從洞看進去，是頭髮內側（材質設成較深的髮色）或身體藏在頭裡的那段脖子管。
   - 用現成的分色診斷圖（`dbg_body_parts.py`＋`neck_probe.py`）就能確認，見第 4.2 節。
6. **從程式找到一個具體疑點：切口沒落在「水平邊」上。**
   - 頭端從下巴往下每 0.02 切一圈水平邊。新娘的下巴是 −0.1898，所以切在 −0.2098、−0.2298…−0.2698、−0.2898。
   - 身體端的切口是 0.02 的整數倍：新娘是 −0.28。
   - 兩者差 0.0102 頭檔單位，約 2.7 mm。所以切口仍落在不規則三角面上，是鋸齒。
   - 這個數字是用新娘 `route/landmarks.json` 和試接 `ob_M/build.json` 推算的，還沒實測。

---

## 2. 業界做法比較表

| 系統 | 頭和身體幾塊 | 接縫的點怎麼對齊 | 法線 | 骨頭權重 | 貼圖顏色 |
| --- | --- | --- | --- | --- | --- |
| **MetaHuman**（Epic，免費、在 Unreal 裡跑） | **兩塊**：Body、Face 是兩個骨架網格元件；臉每格從身體複製骨頭姿勢 [M4][M5] | 頭和身體「必須在脖子接縫區對齊」；比例差太大接縫會很差，小縫會被融合掉 [M1]。有「脖子接縫平滑」選項：平滑往外幾圈（Seam Rings）、幾次（Seam Iterations）、平滑程度（Seam Laplacian）[M1]。建議先做身體，讓頭身交界那一圈邊沿用來源 [M3，搜尋摘要]。打開「Isolate Head From Body」＝頭保持 1:1，但看得到接縫 [M2] | 官方查不到接縫法線的專門步驟；社群做法是把重疊點的法線對齊，有形態鍵時匯出後仍有小偏差 [M6] | 臉直接複製身體的骨頭姿勢，兩邊同一套骨頭 [M4]；接縫點的權重細節查不到 | 查不到官方說明 |
| **Character Creator＋Headshot**（Reallusion，Windows 本機軟體） | 做完是 **CC 標準網格**（頭身同一套拓撲） | 流程：自動偵測 → 對位點 → AI 補頭 → 修網格 → **Attach to Body** [C1][C2]。使用者形容是「把 CC 網格的拓撲鋪到掃描上」[C3]。脖子形狀誇張時可在脖子加對位點；選體型時會「接上對應的脖子形狀」[C1] | 同一塊網格，不需要另外處理（推論） | CC 標準骨架（推論，官方明文查不到） | Headshot 3 可自動把身體膚色配到頭 [C4]；照片模式有混合遮罩。使用者常回報脖子色差或白塊 [C5][C6] |
| **Daz Genesis**（＋geograft 外掛網格） | 角色本身是一塊網格，分材質區與 UV 區（從 G8／8.1 的 UV 討論推知，官方明文查不到）[D4] | geograft（嫁接件）記錄兩樣東西：「自己哪些點焊到基底哪些點」、「要藏掉基底哪些面」；套上時藏掉基底的面、把嫁接件焊進去 [D1]。點位置偏一點就焊不起來 [D2]。Blender 匯入外掛合併時，刪掉被藏的身體點、合併共用的邊界點 [D3，搜尋摘要] | 焊起來後是同一塊，自然一致 | 嫁接件本身就是有權重的角色（官方定義：「把一個有權重的角色無縫整合進另一個」）[D1] | G8.1 把後腦和脖子拆成另一張貼圖，貼錯版本就出現接縫 [D4] |
| **VRoid** | Body、Face、Hair 三塊 [V1]；本專案 `character_setup.py` 也是照這三塊拆 | 查不到 | 本專案經驗：補皮膚時接縫法線差 13° 就看得到一條線，要抄既有皮膚的法線（`blender-character-build/references/body-fill.md`）；MToon 輪廓線會描出網格切口（`pitfalls.md`） | 查不到 | 查不到 |
| **Ready Player Me** | Wolf3D_Head（有表情形態鍵）和 Wolf3D_Body **分開** [R1] | 官方文件直說：頭在脖子處和身體不完全吻合，**強烈建議用衣服或配件蓋住** [R1] | 查不到 | 蓋到脖子的頭飾可以刷權重跟頭動 [R1] | 查不到 |
| **MakeHuman** | **一塊**基底網格 hm08（含頭身）＋輔助幾何 [H1] | 換拓撲用 proxy 套在基底上，骨架不變 [H2] → 沒有頭身接縫 | — | — | — |
| **FaceGen**（頭部生成軟體，整合進遊戲身體） | 兩塊 | 可以定義一圈**「不做形狀變形」的脖子接縫**，所有生成的臉都不動那一圈，身體就不用跟著每張臉改。不定義的話，每張臉都要改身體形狀 [F1] | 查不到 | 查不到 | 身體只用一張很小的單色貼圖（32 px），因為身體是固定顏色 [F1] |
| **柏德之門 3 模組社群**（換頭） | 兩塊（頭、身體） | **「脖子移植」**：新頭刪掉底部兩圈 → 從原版頭複製底部兩圈點 → 雕塑貼合 → 把點一個個吸到原版環上 → 合併 → 合併距離（預設 0.0001 m）。**合併數量要剛好等於環的點數（教學例子是 40）才算吸對** [B1]。兩邊 UV 名稱要一樣 [B1] | 用 Data Transfer 把原版頭的法線抄到「接縫點群組」，對應方式「Nearest Corner and Best Matching Face Normal」[B2] | 接縫三大原因：法線、權重、貼圖；權重不對，過場動畫時接縫會被拉開 [B1] | 前兩項修好還有線，就是貼圖接縫，要改貼圖 [B1][B2] |
| **遊戲模組化角色**（一般原則） | 多塊 | 零件之間要共用**位置完全相同**的點（Simplygon 的模組接縫分析：容差＝場景半徑 × 0.0001）[G1] | 分開網格時，建模軟體會把邊上的法線重算成不一樣，造成接縫 [G3]。Sims 舊教學：領口法線要和原版完全一樣，否則脖子兩種膚色 [G4]。每塊各自算光照、角度不同就看到線 [G5] | 接縫邊上的點要有**同樣的骨頭與權重** [G2] | 接縫放在身體自然的分界處比較不明顯 [G3] |
| **ZEPETO** | 身體端研究報告觀察到頭和身體是同一塊網格（基底模型截圖）；**官方文件查不到「頭身同一塊」的明文** | — | — | 官方 Masking 頁：用黑白遮罩讓衣服底下的身體部位不啟用，遮罩帶的權重和預設 avatar 一樣 [Z1] | — |

**比較下來：**

| 類型 | 代表 | 適合我們嗎 |
| --- | --- | --- |
| 同一塊網格 | Daz、MakeHuman、CC、（ZEPETO） | 要把 AI 頭整個重拓撲成標準網格。跟大頭端「AI 頭本身當成品」的決定相反，而且 52 個表情要重做轉移 → 現在不適合 |
| 兩塊、接縫環重合 | MetaHuman、FaceGen、柏德之門 3、模組化角色 | **最適合。** 頭、身體各自的程式都保留，只約定接縫那一圈 |
| 用衣服蓋 | Ready Player Me | 新娘露肩禮服蓋不住 → 不適合 |

---

## 3. 技術手段

### 3.1 一覽表：做什麼、能不能用程式自動化

全部都能用 Blender Python（`bpy`／`bmesh`）在背景 Blender 自動跑，不需要手動操作。

| 手段 | 做什麼 | 自動化用的 API | 注意 |
| --- | --- | --- | --- |
| **平面切割（bisect）** | 用一個水平面把網格切開，切口是一條準確的平面線 | `bmesh.ops.bisect_plane(..., plane_co, plane_no, clear_inner, clear_outer)`：可同時刪掉平面下面或上面的部分 [B-ops] | 現行 `pack_head` 已在有形態鍵的頭上用它，整合測試自動檢查 0，表示形態鍵沒被切壞 |
| **把不規則切口重新取樣成 N 點** | 切口有 47～50 個間距不一的點，換成固定 N 點 | 自己算：從脖子中心往 N 個角度射線，和切口折線求交點。或用 Geometry Nodes 的 **Resample Curve**，Count 模式會均勻分點 [B-resample] | **照角度**：第 i 點永遠是同一個方向（例：第 0 點正前方），換人也一樣，適合當合約；脖子要「從中心看出去每個方向只碰到一次表面」。**照弧長**：間距最均勻，但第 i 點的方向會隨脖子形狀飄。脖子截面接近橢圓，**建議照角度** |
| **橋接兩圈（Bridge Edge Loops）** | 在兩圈點之間長出一圈面 | `bmesh.ops.bridge_loops(edges, use_merge, merge_factor, twist_offset)` [B-ops] | 點數不同也能橋接：手冊有「點數不同的兩圈」範例圖 [B-bridge]；舊版要求兩邊點數相同，2.63 起才放寬 [B-bridge-old]。點數不同時會長出三角面；要整齊的四邊形，就先把兩圈都取樣成同樣 N 點再橋接。`twist_offset` 用來對齊兩圈的起點 |
| **合併距離（Merge by Distance）／焊** | 把位置重合的點合成一個 | `bmesh.ops.remove_doubles`、`bmesh.ops.weld_verts(targetmap)` [B-ops]；或 Weld 修改器（可只作用在某個點群組）[B-weld] | 柏德之門 3 的驗收法很好用：**合併數量＝環的點數**才算吸對 [B1]。方案 A 不真的焊，但可以在暫存副本上跑一次，當「環有沒有重合」的檢查 |
| **吸附到表面（Shrinkwrap／BVH）** | 把點移到另一個網格表面最近處，或沿某方向投影 | Shrinkwrap 修改器（最近表面點／投影）[B-shrink]；或 `mathutils.bvhtree.BVHTree.find_nearest`／`ray_cast`（現行 `weld_head` 用這個） | 吸附會改形狀：現在是**頭被吸向身體**，所以頭被拉變形 |
| **抄資料（Data Transfer 修改器）** | 從另一個網格抄自訂法線、點群組（權重）、顏色、UV | `obj.modifiers.new(type="DATA_TRANSFER")`；`vertex_group` 控制每點抄多少；Mix Factor 調整體強度 [B-dt] | 對應方式有「Nearest Corner and Best Matching Normal」「…Face Normal」等 [B-dt]。**只能單向抄**：頭抄身體、同時身體抄頭，會互相依賴 |
| **直接設自訂法線** | 指定每個點的法線，不用修改器 | `mesh.normals_split_custom_set_from_vertices(normals)`（給零向量＝保留自動算的）[B-mesh] | Blender 4.1 起不用再開 Auto Smooth，有自訂法線就直接用 [B-41] |
| **權重一致** | 接縫兩側的點用同一根骨頭、同樣比例 | 點群組 `vertex_groups[...].add(...)`；或 Data Transfer 抄點群組 | 我們的情況最簡單：頭是整顆跟頭骨走（掛在 head 骨頭下），身體脖子頂端設 100% 頭骨，兩邊就一起剛體移動 |
| **顏色漸層** | 接縫附近的頭貼圖慢慢變成身體膚色 | 材質節點：物件座標 Z → Map Range → Mix（現行 `blend_head_neck`） | 要確定漸層在**接口環那一圈剛好 100%＝身體膚色**，而且兩邊材質的粗糙度、透光參數一樣（身體材質本來就是複製頭的） |
| **遮罩切口變平滑（Mask 修改器 Smooth）** | 藏掉切口以下時，照權重等高線把面切開，切口變平滑直線 | Mask 修改器的 `use_smooth`＋`threshold`；點群組改成連續權重（例：照高度 0～1 漸變）[B-mask] | 現行 `attach_head` 是 0／1 權重，Mask 只能整面藏或不藏，切口就是三角面的鋸齒。這是最便宜的修法，但切出來的點只存在算繪時，不能當「兩邊約好的點」 |
| **新點的形態鍵** | 在頭上新增點時，52 個表情裡這些點的位置也要給 | `bmesh` 的形態鍵圖層 `bm.verts.layers.shape`：每個形態鍵存的是點的絕對位置 [B-types] | 新點的形態鍵預設值查不到官方說明，**一律明確寫入**（脖子底部在所有表情都不動的話，就寫＝基底位置），寫完逐鍵量位移 |
| **跟著另一塊變形（Surface Deform）** | 讓一塊網格跟著另一塊表面動 | Surface Deform 修改器 [B-sdef] | 我們的接縫兩側都是剛體跟頭骨走，用不到；列出來備用 |
| **合併物件（Join）** | 把兩個物件合成一個 | `bpy.ops.object.join()` | 官方手冊：材質、點群組、UV 會合併；**修改器、限制、父子關係會被忽略** [B-join]。**形態鍵怎麼合併，手冊沒寫，查不到** → 要實測 |

### 3.2 點數不同時怎麼辦

| 情況 | 做法 |
| --- | --- |
| 頭和身體**之間**的接縫 | **不要橋接，要重合。** 兩邊各自把自己那一圈做成同樣 N 點、同樣座標。這是 MetaHuman、FaceGen、柏德之門 3 共同的做法 |
| 頭**內部**：AI 頭不規則的網格 → 標準環 | 在環上方切一刀，刪掉中間一小段，用 `bridge_loops` 把上面不規則的那一圈接到標準環（點數不同沒關係，會長三角面） |
| 身體**內部**：體素重建後的不規則網格 → 標準環 | 同上，在環下方 1～2 cm 切一刀，中間用幾圈過渡環接起來 |

---

## 4. 長髮與後頸

### 4.1 業界怎麼避免接縫露出、後頸出現深色帶

| 做法 | 出處 | 對我們的意思 |
| --- | --- | --- |
| 頭髮底下有一層**頭皮**：從角色頭部直接切出頭皮網格，髮片都從頭皮長出來，不懸空、不插進頭皮 | CC 髮型製作規範 [C7] | 頭髮和皮膚之間的縫，看進去應該是髮色（頭皮），不是皮膚的洞或黑色 |
| **垂直交叉比平行交叉明顯**，先修垂直的 | CC 髮型製作規範 [C7] | 頭髮下緣如果是「直直插向脖子」，會比「沿著脖子貼下去」明顯 |
| 動態頭髮（布料模擬）**離身體越遠越好** | CC 髮型製作規範 [C7] | 我們 `hair_fit` 往後壓縮，是同一個方向 |
| 長髮**100% 綁在頭骨**上；綁到脖子、肩膀、脊椎的頭髮動起來會扭曲 | Reallusion 論壇 [C8] | 我們頭髮掛在 head 骨頭下（剛體），是對的；轉頭時碰到肩膀，靠物理或改頭髮形狀 |
| 頭和身體對不齊，**用衣服或配件蓋住** | Ready Player Me [R1] | 長髮本身會蓋住後頸，所以接縫在**後面**本來就容易藏；露肩禮服的**前面和側面**蓋不住，要靠接縫本身做好 |
| 頭髮背面（內側）**另給顏色，不要比正面暗** | 查不到權威來源，屬常見做法（搜尋結果的一般建議） | 我們頭髮內側現在是「髮色 × 0.8」（`pack_head.py` 第 214 行），比正面暗 |

### 4.2 我們後頸深色鋸齒邊的可疑原因（從程式讀出來的推測，還沒實測）

| # | 可疑點 | 從程式看到的根據 | 怎麼確認 | 對應修法 |
| --- | --- | --- | --- | --- |
| **H1（最可疑）** | **後頸破洞**：Head 的後頸被挖掉一塊，邊緣是鋸齒 | ① `pack_head.py` 從頭頂往下長「顏色像頭髮」的區域，超過一半的點是頭髮的面就整面切給 Hair。AI 把後頸畫成髮色的話，Head 的後頸就被挖走，留下沿三角形邊的鋸齒洞。② `hair_fit.py` 第 97 行只固定「下巴往下 5 公分以上」的頭髮與臉的接縫，更下面的頭髮被往後推，洞就露出來。③ `weld_head` 只吸「切口那一圈」，洞的邊不在那一圈，不會被補 | 跑 `dbg_body_parts.py`＋`neck_probe.py`，看背面和側面那條帶子是什麼顏色：紅＝頭、藍＝身體、灰＝頭髮正面、洋紅＝頭髮背面。再用 bmesh 數 Head 在切口以上、後頸（y > 0）有沒有「只連一個面的邊」（開放邊） | 頭端切完頭髮後，把 Head 脖子補成一圈封閉的皮膚（從接口環往上到髮際）；後頸靠近頭髮的皮膚貼圖改成「髮色往膚色漸層」（業界的頭皮層概念） |
| H2 | 留在 Head 的後頸面，貼圖本身是頭髮陰影色 | `blend_head_neck` 只把「切口到下巴往下 1/4」那段漸層成身體膚色，更上面的後頸保持 AI 原貼圖 | 同上的分色圖：帶子是紅色（頭）而且在漸層範圍以上 | 頭端把後頸貼圖（耳後到切口）整理成「膚色，靠髮際漸層成髮色」 |
| H3 | 身體脖子從頭裡穿出來 | `skin_body` 在切口以上還有兩節圓管（`c4b`：頭脖子 0.9 倍粗、`c5`：0.75 倍）藏在頭裡；AI 脖子截面不是橢圓，某些角度可能比圓管細 | 分色圖出現藍色（身體）在頭的範圍裡 | 方案 A 會把身體在接口環以上的部分整段刪掉，這個問題自然消失 |
| H4 | 切口本身是鋸齒、吸附造成折痕，陰影裡看起來是深色帶 | 第 1 節第 6 點：切口沒落在水平邊上（差約 2.7 mm）；吸附最大 13.72 mm（`ob_M/build.json`；使用者提供的試接是 14.34 mm） | 近照看是不是正好在切口高度 | 方案 A（或最小修補方案 C）處理 |
| H5 | 縫裡的陰影（環境光遮蔽） | 頭髮被往後推，頭髮和脖子之間有一道縫，縫裡本來就暗 | 關掉陰影再拍一次比較 | 屬於正常的陰影；嫌太重再調頭髮離脖子的距離 |

**建議順序**：先跑分色診斷圖確定是哪一個，再修。不要同時改好幾個地方，不然不知道是哪個修好的。

### 4.3 實測補充（2026-10-14，主控端在報告交出後量的）

對象：整合測試的新娘成品 `D:/render-work/blender-work/zepeto-rig/integration-test/bride/rig/head_rig.blend`，試接身體 `D:/render-work/blender-work/zepeto-rig/bride-integration-test/body_try/final/out/`（用現行 `body_build.py`，`HEADWELD` 預設開）。

| 推測 | 實測 | 結論 |
| --- | --- | --- |
| H1 後頸破洞 | 在 −0.28 切開 Head：截面**不是一整圈**，是 61 點、開口兩端的一段弧（x −0.200～0.199、y −0.234～−0.001），只涵蓋前面和兩側約 240°。開口兩側的邊界是兩條幾乎垂直的鋸齒線（角度約 ±60～70°，從肩頸底座一路到下巴以上），藏起頭髮從後面看，整個後腦、後頸都不在 Head 上（`D:/render-work/blender-work/zepeto-rig/integration-test/neck/nohair.png`）。原因：AI 把後頸畫成頭髮色，`pack_head.py` 切頭髮時整片後頸跟著頭髮走 | **成立，而且比「洞」大**：後頸整片沒有皮膚，是身體端伸進頭裡的脖子圓管（`c4b`、`c5`）從後面補起來的。⚠️ 第一次量時用「正後方 ±60°」數開放邊，剛好把這兩條邊界算成「側面」，誤判成「沒有洞」 |
| 深色鋸齒是什麼 | 右側近拍脖子後面，原色對分色（`tools/dbg_body_parts.py`）：鋸齒＝Hair 內側的切口邊（灰）和 Head 後頸開口的鋸齒邊，帶子裡的黑色＝從頭髮和脖子之間的空隙看到的頭髮背面（洋紅），後面墊的是身體脖子（藍）。對照圖 `D:/render-work/blender-work/zepeto-rig/integration-test/neck/neck_side_cmp.png` | 頭端要：補出後頸皮膚（方案 A 的頭端第 6 步，見 5.5）、頭髮切口邊與內側顏色 |
| 第 1 節第 6 點：切口沒落在水平邊上 | 下巴 −0.1898、身體切口 −0.2800，頭端最近的水平切邊 −0.2898，差 **0.0098** 頭檔單位（約 2～3 mm） | **成立** |
| 縫合本身 | `build.json` 的 `head_weld`：第一圈 47 點全部貼上、最大縫隙 14.34 mm | 有縫上，但頭被吸 14 mm（方案 A 要解決的） |

另外量到：Head 在切口到下巴之間，**前側 22 條、側面 13 條開放邊**（不在後頸），位置還沒查；接上身體的側面圖看不出來，做方案 A 時一起處理。

---

## 5. 我們的方案

### 5.1 現況（從程式讀到的）

| 環節 | 現在的做法 | 問題 |
| --- | --- | --- |
| 頭端 `pack_head.py` | 從下巴（landmarks 的 `chin_z`）往下每 0.02 切一圈水平邊 | 切的高度和身體端的切口高度不一定對齊（第 1 節第 6 點） |
| 身體端 `measure_head` | 自己量下巴、自己找切口（量出來會落在 0.02 的整數倍）、量切口處頭的脖子寬和厚 | 頭和身體各量一次下巴，兩個數不一樣（新娘：頭端 −0.1898、身體端 −0.1994） |
| `skin_body`（NECKFIT） | 身體脖子在切口處做成「和頭脖子一樣寬、一樣厚」的**橢圓**，往上兩節縮進頭裡 | AI 脖子不是橢圓。新娘量到：身體前緣比頭前緣後退約 7.5 mm、左右窄約 2 mm（`ob_M` 的 `neck_section`） |
| `attach_head` | Mask 修改器藏掉切口以下（0／1 權重） | 切口是三角面的鋸齒 |
| `weld_head` | 頭切口往上三圈的點吸到身體表面（100%／60%／25%），所有形態鍵一起平移；身體脖子頂端 100% 跟頭骨 | **頭被拉向身體**，最多 13～14 mm；兩邊的點仍不重合 |
| `seam_normals` | 頭靠近切口那段的法線抄身體（Data Transfer，切口 100%、往上漸淡） | 方向對；點不重合時抄得不準 |
| `blend_head_neck` | 頭的脖子貼圖從切口（100% 身體膚色）漸層到下巴往下 1/4 | 方向對 |

### 5.2 三個方案比較

| | **A：兩個物件，接縫點對點重合**（推薦） | **B：標準環，焊成同一塊** | **C：最小修補（不換結構）** |
| --- | --- | --- | --- |
| 一句話 | 約定一圈 48 點的接口環。頭端在 AI 頭上做出這一圈，身體端把脖子頂端做成同樣的 48 個座標。法線、權重、顏色照現在的做法收尾 | 所有人用**同一圈固定形狀**的接口環（像 FaceGen），頭和身體各自貼合到這一圈，最後合併成一個網格 | 只修現在看得到的問題：切口對齊水平邊、Mask 平滑切、補後頸洞、漸層加長 |
| 頭端改哪裡 | `pack_head.py`：把「每 0.02 切一圈」換成「做接口環」（第 5.4 節），補封閉後頸；在頭檔寫入環的資料。`run_face_rig.py` 的檢查加環的驗收 | A 的全部，再加：把 AI 脖子底部一小段變形到標準形狀（形態鍵一起處理）；之後頭不再是獨立物件，`face_rig.py`、`rig_check.py` 都要配合合併後的結構 | `pack_head.py`：水平邊改成切在身體會用的切口高度（或改由頭端決定切口、寫進頭檔）；補後頸洞 |
| 身體端改哪裡 | `body_build.py`：`measure_head` 改讀頭檔的環（不再自己量切口）；`skin_body` 脖子管只做到環下面；新增「接口過渡帶」函式；`weld_head` 拿掉吸附、保留權重；`blend_head_neck` 改用環的高度；`build.json` 加驗收數字 | A 的全部，再加：合併、頭改成用骨架變形（不再掛在骨頭下）、處理形態鍵和臉部驅動器、改出廠檢查 | `attach_head`：Mask 改連續權重＋Smooth；`skin_body`：拿掉切口以上的圓管 |
| 服裝、動畫端 | **不用改**（還是找 `Body`、`Head` 兩個物件）。身體重出新版時照原流程重跑 | **要改**：服裝 `garment_lib.py` 用 `O["Body"]`、`O["Head"]` 分別抓；動畫 `zanim_lib.py` 用「骨架修改器、點最多的網格＝身體」「名稱 Head 的子物件＝頭」。合併後兩個都要改 | 不用改 |
| 兩邊要約定 | 點數 48、環的高度、起點與方向、座標系、環的點怎麼標記、權重規則、顏色規則（第 5.3 節） | A 的全部，再加：標準環的固定形狀（寬、厚、中心，以頭高為單位） | 切口高度由誰決定（建議頭端） |
| 優點 | 接縫點對點重合，**頭不再被拉變形**（改成身體遷就頭）；身體在環以上的部分刪掉，不會從頭裡穿出來；52 個表情、三端介面都不動；每一步都可量化驗收 | 真正同一塊網格，平滑著色自動連續；所有人同一個脖子，服裝領口可以共用，往 ZEPETO「一副基底身體換頭」的方向走 | 最快，半天內做完 |
| 缺點、風險 | 頭端要在 AI 網格上動手術（新點要給形態鍵、UV）；AI 脖子形狀怪的人（例：脖子上還黏著衣領）取樣可能失敗，要有退路 | 合併會動到臉部 52 個表情的驅動器、Mask、三端程式；Blender 合併時形態鍵怎麼處理，官方文件查不到，要實測；脖子粗細會被統一，AI 頭的脖子外型會變 | 兩邊的點仍不重合、頭仍被吸 13～14 mm，可能還看得到淡淡一條線；之後還是要做 A |
| 工作量（代理實作＋自我檢查，不含使用者審看） | 約 2～3 個工作天（頭端約 1 天、身體端約 1～1.5 天、新娘新郎攝影師三顆頭整合測試約 0.5 天） | A 再加 3～5 天，外加服裝、動畫、臉部三邊協調 | 約 0.5 天 |

不推薦、只列出來的做法：

| 做法 | 為什麼不推薦 |
| --- | --- |
| D：用衣服蓋住接縫（Ready Player Me 的建議） | 新娘露肩禮服蓋不住 |
| E：把 AI 頭整個重拓撲成標準網格（Headshot、MetaHuman 的做法） | 跟「AI 頭本身當成品」的決定相反；52 個表情、嘴縫、口腔袋都要重做 |

### 5.3 推薦方案 A 的理由

1. **業界主流就是這樣做。** MetaHuman、FaceGen、柏德之門 3 都是兩塊網格、接縫環重合，不是焊成一塊。
2. **改掉現在最根本的問題「頭被吸變形」。** 方向反過來：頭的外型一點都不動，身體遷就頭。這也符合大頭端「AI 頭本身當成品」的原則。
3. **不動任何下游介面。** 臉部 52 個表情與驅動器、服裝端、動畫端都照舊。
4. **之後要焊成一塊（方案 B）也不會白做。** 環重合之後，焊只是「合併距離 0 的點」；要不要統一成同一個標準脖子，也只是把「環的形狀照頭量」換成「環的形狀用固定值」。
5. **每一步都能量化驗收**：重合距離、法線夾角、權重差、顏色差，都可以寫進 `build.json`。

### 5.4 接口環合約草案（v1，給頭端和身體端討論用）

| 欄位 | 內容 | 誰寫、誰讀 |
| --- | --- | --- |
| 版本 | `neck_ring_ver = 1`（Head 物件的自訂屬性） | 頭寫、身體讀；沒有這個屬性就走舊做法（相容舊頭） |
| 點數 N | **48**（每 7.5° 一點，正前、正後、左、右正好都落在點上；新娘現在切口第一圈是 47～50 點，密度差不多；新娘脖子一圈約 29 cm，點距約 6 mm） | 固定 |
| 高度 | 頭檔座標的一個水平面 `neck_ring_z`。**由頭端決定一次**（沿用身體端現在「下巴底面結束、脖子開始」的規則，搬到頭端算），身體端不再自己量 | 頭寫、身體讀 |
| 起點與方向 | 第 0 點＝正前方（−Y，下巴正下方）；從上往下看逆時針：−Y → +X（角色左側，第 12 點）→ +Y（正後方，第 24 點）→ −X（角色右側，第 36 點） | 固定 |
| 每點的位置 | 從脖子中心（`neck_ring_center`，x = 0）往第 i 個角度射線，和 AI 頭表面在 `neck_ring_z` 的交點 | 頭算 |
| 標記 | Head 網格的整數點屬性 `neck_ring`：環上的點＝1～48（照上面的順序），其他＝0 | 頭寫、身體讀 |
| 座標系 | 頭檔座標；身體端照 `attach_head` 的換算（× S、平移到頭骨轉軸）得到身體座標。兩邊座標重合到 0.01 mm 以內 | 身體算 |
| 權重 | 身體上環那一圈及往上（如果有）100% `J_Bip_C_Head`；往下 1.2 cm 起漸變回自動權重（沿用 `weld_head` 的權重段） | 身體 |
| 法線 | 第一版沿用 `seam_normals`（頭抄身體，環上 100%、往上漸淡）；身體過渡帶設計成在環上和頭表面同一個斜率，抄過去才不會折。還有淡線，再改成兩邊直接設同一組自訂法線 | 身體 |
| 顏色 | `blend_head_neck` 的起點改成環的高度，保證環上剛好 100%＝身體膚色；身體材質沿用複製頭的皮膚材質（同粗糙度、同透光） | 身體 |
| 環以下 | 頭的胸像留著、用 Mask 藏（身體端取膚色 `SKINSRC=neck` 還讀得到）；Mask 的點群組改成「環上與環以上＝1」，切口就剛好是環 | 頭留、身體藏 |

### 5.5 方案 A 的實作步驟

**頭端（`pack_head.py`，在切完頭髮、耳朵之後）**

1. 算 `neck_ring_z` 與脖子中心。
2. 在 `neck_ring_z` 和往上一點（約 0.02 頭檔單位）各用 `bisect_plane` 切一刀，刪掉兩刀之間的面。
3. 用射線算出 48 個環點的位置，新增這 48 點，並寫入：
   - **每個形態鍵的位置**：照附近原點的位移內插；脖子底部預期都是 0。
   - **UV**：從射線打到的原三角形內插。
4. 用 `bridge_loops` 把上面那一圈不規則的點接到 48 點環；環和下面的胸像也接起來，或不接，留著藏掉也可以。
5. 寫 `neck_ring` 屬性、`neck_ring_z`、`neck_ring_center`、`neck_ring_ver`。
6. **補封閉後頸**（第 4.2 節 H1，確認是破洞之後）：Head 的脖子從環到髮際要是一圈封閉的皮膚。
7. 檢查：
   - 環點數＝48；
   - 52 個表情在環上的最大位移＝0（或 < 0.01 mm）；
   - 環以上沒有開放邊（嘴、眼睛等本來就開的除外）；
   - `rig_check` 照樣通過。

**身體端（`body_build.py`）**

1. `measure_head`：有 `neck_ring_ver` 就讀環，`cut` 改用 `neck_ring_z`；沒有就走舊做法。
2. `skin_body`：脖子管只做到環下面一點；刪掉 `c4b`、`c5`（伸進頭裡那兩節）。
3. 新增 `fit_neck_ring`（放在 `build_mesh` 之後、`bind` 之前）：
   1. 在環下 1～2 cm 切一刀，刪掉以上的部分；
   2. 切口用 `bridge_loops` 接到一圈 48 點的「身體環」；
   3. 往上 3～4 圈過渡到「頭環」，最上面那一圈的座標**直接等於**頭環的座標；過渡環的形狀用兩端的斜率內插，接口不折。
4. UV：沿用 `make_uv`，在 `fit_neck_ring` 之後再展一次，或單獨展過渡帶。
5. `weld_head`：拿掉吸附那段（頭不再被移動），保留權重段。
6. `seam_normals`、`blend_head_neck`：高度改用環。
7. `build.json` 加驗收數字：
   - `ring_n`（48）；
   - `ring_gap_max_mm`（應為 0.00）；
   - `ring_normal_diff_max_deg`（目標 < 1°）；
   - `ring_weight_head`（環上全部 100% 頭骨）；
   - 「暫存副本上合併距離 0.0001 m 合併了幾點」（應＝48，柏德之門 3 的驗收法）。
8. `neck_probe.py` 照拍（正面、側面、背面、低頭、抬頭、轉頭）。

---

## 6. 需要使用者決定的事

| # | 問題 | 選項與後果 |
| --- | --- | --- |
| 1 | 接口環的形狀：**照每顆頭的脖子量**，還是**全部人用同一個標準脖子**？ | 照頭量（方案 A）：AI 頭外型一點不變，身體跟著每顆頭。標準脖子（方案 B 的環）：脖子粗細全部人統一，可以順便往 ZEPETO 的細脖子靠（身體研究報告：ZEPETO 脖子約頭寬 34%，我們約 45%），但 AI 頭的脖子底部會被改形。建議先照頭量 |
| 2 | 要不要真的**焊成同一塊網格**？ | 建議先不要。點重合之後外觀已經等同一塊；真的合併會動到臉部表情驅動器和服裝、動畫兩端的程式 |
| 3 | 什麼時候換？ | 新娘新頭本來就要重出身體，這時候一起換，多花的成本最少。但新娘 v3 已被導演鎖給開場片 B：換新身體後，服裝、已定案的鏡都要照「上游更新」重跑。要先問導演端排程 |

---

## 7. 查不到、沒能驗證的

- ZEPETO「頭和身體同一塊網格」：官方 Masking 頁沒寫，只有身體端研究報告從截圖觀察到。
- VRoid 臉和身體在脖子的接縫怎麼處理：查不到。
- MetaHuman 接縫兩側法線、貼圖顏色的官方做法：查不到；只有社群做法。
- Character Creator Headshot：「Attach to Body」時脖子貼圖怎麼融合，官方說明查不到；AI 生成那一步是否在雲端跑，也查不到。
- Faceform Wrap（業界常用的「把標準拓撲包到掃描上」軟體）的價格：查不到。
- Blender 合併物件時形態鍵怎麼合併：手冊沒寫，要實測。
- bmesh 新增點的形態鍵預設值：查不到，所以建議一律明確寫入。
- Ready Player Me 的官方文件網站已連不上：該公司 2025-12 被 Netflix 收購，服務 2026-01-31 關閉 [R2]。文中引用的內容來自搜尋引擎索引。
- 第 1 節第 6 點（切口錯位 2.7 mm）、第 4.2 節（後頸破洞）都是**從程式推算的**，還沒在 Blender 裡實測。

---

## 8. 來源

**MetaHuman（Epic Games）**

- [M1] From Custom Mesh 工具（頭身要在脖子接縫區對齊、Neck Seam 平滑選項）：https://dev.epicgames.com/documentation/metahuman/metahuman-creator-from-custom-mesh-tool-in-unreal-engine
- [M2] From DNA 工具（Isolate Head From Body）：https://dev.epicgames.com/documentation/metahuman/metahuman-creator-from-dna-tool-in-unreal-engine
- [M3] Body Conform Controls（先做身體讓交界邊環沿用來源；頁面抓不到全文，內容取自搜尋摘要）：https://dev.epicgames.com/documentation/metahuman/body-conform-controls
- [M4] Play a Custom Animation（臉從身體複製骨頭姿勢）：https://dev.epicgames.com/documentation/metahuman/play-a-custom-animation
- [M5] Assets Overview（Body、Face 骨架網格元件）：https://dev.epicgames.com/documentation/metahuman/assets-overview
- [M6] 社群：對齊重疊點法線的 Maya 腳本：https://forums.unrealengine.com/t/vertex-normal-rotation-alignment-tool-v1-0-maya-script/1995007

**Character Creator／Headshot（Reallusion）**

- [C1] Headshot 網格流程（五步驟、脖子對位點、接上對應脖子形狀；價格頁另見下）：https://www.reallusion.com/character-creator/headshot/3d-head-from-mesh.html
- [C2] Headshot 2 手冊 Mesh Mode：https://manual.reallusion.com/Headshot_for_CC/ENU/2.0/06-Mesh-Mode/Intro-Mesh-Mode.html
- [C3] 論壇（把 CC 拓撲鋪到掃描上）：https://forum.reallusion.com/538084/Group1.aspx
- [C4] Headshot 3 手冊（身體膚色自動配頭）：https://manual.reallusion.com/Headshot_Plugin/ENU/3.0/08-Texture-Adjustment/Colors.htm
- [C5] 使用者回報：Headshot 後脖子白塊：https://discussions.reallusion.com/t/white-patch-on-neck-after-headshot-character-creator-5/16806
- [C6] 使用者回報：脖子顏色沒和頭融合：https://reallusion.com/FeedBackTracker/Issue/NECK-area-on-headshot-not-blending-colors-with-head
- [C7] CC 髮型網格製作規範（頭皮、髮片從頭皮長、離身體遠、垂直交叉較明顯）：https://wiki.reallusion.com/Content_Dev:CC_3.4_Hair_Mesh_Production
- [C8] 論壇：頭髮 100% 綁頭骨：https://forum.reallusion.com/550828/Resolving-Hair-Collision-with-Shoulders
- 價格：Headshot 3 USD 199（登入會員 149）、CC5＋Headshot 3 組合 329、Headshot 2 升級 129，皆為 Windows 買斷授權（取自搜尋摘要，官方頁面：https://www.reallusion.com/character-creator/headshot ；實際價格以官方商店為準）

**Daz**

- [D1] Geo-Grafting 名詞說明：https://docs.daz3d.com/public/software/dazstudio/4/referenceguide/terms/geo-grafting/start
- [D2] 論壇：Geografts won't weld（點偏一點就焊不起來）：https://hpclscruffy.daz3d.com/forums/discussion/comment/8093016/
- [D3] Diffeomorphic 匯入外掛 Merge Geografts（直接開啟回 404，內容取自搜尋摘要）：https://bitbucket.org/Diffeomorphic/import_daz/wiki/Setup/Finishing/Merge%20Geografts
- [D4] Genesis 8.1 後腦與脖子另一張貼圖：https://render.otoy.com/forum/viewtopic.php?p=395666

**其他系統**

- [V1] VRoid 模型在 Unity 裡是 Body、Face、Hair 三塊：https://styly.cc/tips/blender-vrm-export1/
- [R1] Ready Player Me 自訂服裝文件（頭和身體在脖子不完全吻合、建議用衣服蓋；網站已連不上，內容取自搜尋索引）：https://docs.readyplayer.me/ready-player-me/customizing-guides/create-custom-outfits
- [R2] Netflix 收購 Ready Player Me、服務關閉：https://www.pocketgamer.biz/netflix-acquires-avatar-creation-platform-ready-player-me
- [H1] MakeHuman 基底網格與輔助幾何：https://static.makehumancommunity.org/mpfb/docs/assets/basemesh_and_helpers.html
- [H2] MakeHuman 替代拓撲（proxy）：https://static.makehumancommunity.org/about/concepts/alternative_topologies.html
- [F1] FaceGen 頭部整合（不變形的脖子接縫、身體單色小貼圖）：https://facegen.com/man_int_head.htm
- [B1] 柏德之門 3 模組社群：脖子移植：https://wiki.bg3.community/Tutorials/Visual/Neck-Transplant
- [B2] 柏德之門 3 Wiki：修脖子接縫（Data Transfer 抄法線）：https://bg3.wiki/wiki/Modding:Fixing_neck_seams
- [Z1] ZEPETO Studio 指南 Masking：https://docs.zepeto.me/studio-guide/rigging-masking
- 身體端 ZEPETO 身體研究報告：https://claude.ai/artifact/JudBvPg4xRPimxfBwRZcwL
- inZOI 社群：頭身接縫多半是法線與切線不一致：https://forum.playinzoi.com/t/topic/13339

**遊戲模組化角色**

- [G1] Simplygon：模組化角色接縫（點要完全同位置、容差）：https://simplygon.com/posts/44180d50-2257-416c-bec7-facb1e3eeb02
- [G2] Tech-Artists 論壇：接縫點的骨頭與權重要一致：https://www.tech-artists.org/t/vertex-weights-unreal/15655
- [G3] Unreal Answers：多部件角色的接縫（分開網格改了法線）：https://answers.unrealengine.com/questions/221564/view.html
- [G4] ModTheSims：領口法線要和原版一樣：https://db.modthesims.info/article.php?p=1058796
- [G5] Second Life 網格頭說明（每塊各自算光照）：https://marketplace.secondlife.com/s/JJ-Portrait-Mesh-Head-Jun/7270809

**Blender 官方文件**

- [B-dt] Data Transfer 修改器（5.2）：https://docs.blender.org/manual/en/5.2/modeling/modifiers/modify/data_transfer.html
- [B-bridge] Bridge Edge Loops：https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/bridge_edge_loops.html
- [B-bridge-old] 舊版 Bridge 說明（2.63 起允許點數不同）：https://archive.blender.org/wiki/2015/index.php/User:RedTriangle/Bridge
- [B-mask] Mask 修改器（Smooth 選項）：https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/mask.html
- [B-weld] Weld 修改器：https://docs.blender.org/manual/en/5.2/modeling/modifiers/generate/weld.html
- [B-shrink] Shrinkwrap 修改器：https://docs.blender.org/manual/en/5.2/modeling/modifiers/deform/shrinkwrap.html
- [B-sdef] Surface Deform 修改器：https://docs.blender.org/manual/en/5.2/modeling/modifiers/deform/surface_deform.html
- [B-join] Join（合併物件）：https://docs.blender.org/manual/en/5.2/scene_layout/object/editing/join.html
- [B-resample] Resample Curve 節點：https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/curve/operations/resample_curve.html
- [B-ops] bmesh.ops（bisect_plane、bridge_loops、remove_doubles、weld_verts）：https://docs.blender.org/api/current/bmesh.ops.html
- [B-types] bmesh.types（形態鍵圖層 shape）：https://docs.blender.org/api/current/bmesh.types.html
- [B-mesh] bpy.types.Mesh（normals_split_custom_set_from_vertices）：https://docs.blender.org/api/current/bpy.types.Mesh.html
- [B-41] Blender 4.1 建模更新（Auto Smooth 改成修改器、自訂法線直接生效）：https://developer.blender.org/docs/release_notes/4.1/modeling/

**專案內檔案（只讀）**

- 頭端：`.claude/skills/zepeto-face-rig/scripts/pack_head.py`（每 0.02 水平切：第 247～250 行；頭髮背面 ×0.8：第 214 行）、`scripts/hair_fit.py`（只固定下巴以上的接縫：第 97 行）、`references/ai-mesh-route.md`「接身體」
- 身體端：`.claude/skills/zepeto-body-generation-workflow/scripts/body_build.py`（`measure_head` 第 56～105 行、`skin_body` 脖子第 233～244 行、`attach_head` 第 603～620 行、`weld_head` 第 550～600 行、`seam_normals` 第 534～547 行、`blend_head_neck` 第 510～531 行）
- 下游介面：服裝 `.claude/skills/zepeto-clothing-generation-workflow/scripts/garment_lib.py` 第 16 行；動畫 `.claude/skills/zepeto-animation-generation-workflow/scripts/zanim_lib.py` 第 22～33 行
- 新娘試接數字：`D:/render-work/blender-work/zepeto-sculpt-trial/bride/body_try/ob_M/build.json`（`head_weld`、`neck_section`）、`bride/route/landmarks.json`（`chin_z`）
