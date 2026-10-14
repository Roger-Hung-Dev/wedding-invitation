# 身體表面直條紋、全身固定網格、交接尺寸、審看網頁（研究報告，2026-10-14）

> 委託內容：研究四件事——(1) 身體表面一條條直的明暗紋怎麼來、怎麼修；(2) 業界怎麼用「一套固定網格」做出不同身材；(3) 交接給服裝要量哪些尺寸（鞋楦、袖口、褲腳）；(4) 身體審看網頁該放什麼，特別是「手」「腳」兩區。
> 研究方式：只讀專案程式與現有紀錄、上網查資料。**沒有改任何程式、沒有跑 Blender。** 所以第 1 節「直條紋的成因」是從程式推算出來的，要用 1.4 節的方法實測確認。
> 讀過的程式與資料：`scripts/body_build.py`（`skin_body`、`build_mesh`、`smooth_normals`、`make_uv`）、`body_checks.py`（腳的量法、指紋）、`body_page.py`、`hand_probe.py`、`foot_probe.py`、`hand_template.py`、`foot_template.py`（接口半徑係數）；`references/zepeto-body-v2.md`、`research-hands-feet.md`、`checklist.md`；服裝端 `zepeto-clothing-generation-workflow/scripts/garment_lib.py`（基準高度、`inflate`、`shoes`、`laces`、`transfer_weights`）；`D:/render-work/zepeto-body/build/_tplF3.work/build.json`、`RELEASE.json`（只讀）。
> 文中 `[代號]` 對應文末來源表。標「推算」「推測」「本報告建議」的，是沒有查到出處或還沒實測的判斷。

> **2026-10-14 實作狀態**（做法、數字、工具的現況以 `limbs.md` 為準）：(1) 直條紋 → 實測確認是 Skin 的 16 邊形稜，改 `SKINSUB` 4，手腳都是模板時再改 3 mm 體素、不減面（limbs.md 2.2）；(2) 一套固定網格做不同身材 → 沒做（長期方向）；(3) 交接尺寸 → `body_measure.py`，出廠自動列和上一版的差（3.4、第 5 節）；(4) 審看頁 → `body_page.py` 加了手腕、腳、手肘膝蓋胯下小腿、活動範圍、尺寸區塊（第 4 節）。

---

## 結論（先看這段）

**一句話：直條紋最可能是「Skin 修改器每一節的截面只有 4 個角，我們又只細分 2 次」造成的。** 所以每條腿、每條手臂、整個軀幹，其實都是 16 塊平面拼成的長管。後面的體素重建把這 16 條稜原樣「拓印」下來，平滑抹不掉，減面又沿著稜切出長三角形。之前加的「抄光滑法線」，抄的來源本身就有稜，所以沒用。**改一行（細分 2 次 → 4 次）很可能就能從源頭消掉。** 先花半天用「截面量圓度」確認，再改。

### 四個項目一覽

| # | 項目 | 結論 | 建議先做什麼 | 優先 |
| --- | --- | --- | --- | --- |
| 1 | 直條明暗紋 | 主因推測是 Skin 的 16 邊形截面（原始碼確認每節 4 個角 [B1]；紋路寬度和位置用程式推算吻合，**未實測**）。次要：減面長三角形，加上自訂法線和實際形狀不一致造成的陰影邊紋 | ① 診斷（截面量圓度）② Skin 後細分改 4 次 ③ 手腳模板開著時改成「粗體素、不減面」 | ①② P0；③ P1 |
| 2 | 全身固定基礎網格 | 業界全部是「一套固定網格＋改骨頭長度或形態鍵」。我們的頭、雙手、雙腳已經有 5 個固定接口環，**只剩軀幹與四肢中段每次都是融出來的**。可行，約 2～3 週 | 現在不做。先做第 1 項；等要做身材形態鍵、或表面修完還不夠乾淨時再做 | P3 |
| 3 | 交接尺寸 | 現在只量 4 個鞋子尺寸，定義和業界不同，而且**沒有任何「圍度」**。服裝端還有寫死的距離（鞋帶位置、鞋口高度），新腳會讓它們失準 | 新增 `body_measure.py`，照 IBV／ISO 定義量約 20 個尺寸，寫進 `build.json` 與 `RELEASE.json`，出廠時自動列出變化 | P1（重做鞋子之前） |
| 4 | 審看網頁 | 業界審看＝轉檯（各角度）、關節活動範圍測試、權重檢查、極端姿勢。我們缺：ROM 掃描條、權重熱圖、新舊並排、尺寸表 | `body_page.py` 加「手」「腳」兩區（清單見 4.3、4.4），外加一小區「表面品質」 | P1 |

### 不處理會怎樣

- **直條紋**：衣服是「複製身體 → 往外推出厚度」長出來的（`garment_lib.inflate` 用的是網格本身的法線）。身體的稜會原樣跑到褲管、袖子、裙子上。特寫鏡頭、側光時最明顯。
- **尺寸**：服裝端的鞋帶寫死在 y = −48、−61、−74 mm（`laces`），是照舊腳放的。新腳長 232 mm、腳踝往上往後移，鞋帶會跑到錯的位置。鞋口高度「腳踝關節 + 75 mm」≈ 158 mm，剛好落在小腿接口環（0.158 m）上，那裡網格密度會突然改變，切邊可能鋸齒（推測）。
- **審看**：使用者現在看不到手腳彎到極限的樣子、也看不到權重怎麼分。問題要等動畫端做到那個動作才會被發現，那時要回頭改身體、服裝、動畫三邊。

### 會一直出現的詞

| 詞 | 白話 |
| --- | --- |
| Skin 修改器 | Blender 的工具：沿著一串點和線「長出一根管子」。我們用它沿骨架長出軀幹和四肢 |
| 截面 | 把手臂或腿橫著切一刀，切口的形狀 |
| 細分（Catmull-Clark） | 把每個面切成 4 個小面、再把角磨圓。細分 1 次，一圈的點數變 2 倍 |
| 體素重建 | 把物體放進很細的 3D 格子，重新包一層皮。好處是能把好幾塊融成一塊、沒有接縫 |
| 平滑（拉普拉斯平滑） | 每個點往周圍點的平均位置挪一點，重複幾次，表面變順 |
| 減面 | 把面數減少。Blender 的做法是一次合併一條邊，挑「合併後形狀改變最少」的那條 |
| 法線 | 表面每一點「朝外的方向」。光影就是用它算的 |
| 自訂法線 | 不照網格的實際形狀，另外指定每一點的法線。只改光影，不改形狀 |
| 稜 | 兩個平面交界的折線。光打上去一邊亮一邊暗，就是一條明暗紋 |
| 弓高 | 一段弧和它的弦（直線）之間最大的距離。用來說「平面和真正的圓差多少 mm」 |
| 斑馬紋 | 讓表面反射一排平行的黑白條紋。表面順，條紋就順；有稜，條紋就折彎 |
| 固定拓撲 | 點數、點的編號、誰連誰都固定，只有位置可以變 |
| 形態鍵 | 同一塊網格的「另一組點位置」，用滑桿在兩組之間調 |
| 鞋楦 | 做鞋用的腳形模具。鞋子照它的形狀做 |
| 圍度 | 繞一圈的長度，像用皮尺量腰圍 |
| ROM 測試 | 關節活動範圍測試：把每個關節從 0 彎到極限，看網格會不會壞 |
| 權重熱圖 | 用顏色顯示「每個點跟某根骨頭動多少」 |
| 轉檯 | 讓角色原地轉一圈，從每個角度拍 |

---

## 1. 身體表面的直條明暗紋

### 1.1 白話成因（推算，未實測）

照現在的程式，一條小腿是這樣做出來的：

| 步驟 | 程式在哪 | 做了什麼 | 對紋路的影響 |
| --- | --- | --- | --- |
| 1 | `skin_body` 的 `SKIN` 修改器 | 每個節點放一個「4 個角的方框」。Blender 原始碼裡這個方框（`Frame`）就是 4 個角 `co[4][3]` [B1]。兩個節點之間用平面連起來 | 一開始是**方管** |
| 2 | 同一個函式的 `SUBSURF`，`levels = 2` | 細分 2 次：每圈 4 → 8 → 16 個點 | 方管變成 **16 邊形管**。每一面是平的，相鄰兩面夾約 22.5° |
| 3 | `build_mesh` 的 `REMESH`（體素 1.2 mm）＋`LAPLACIANSMOOTH`（4 次、0.6） | 重新包一層皮，再抹平 | 格子（1.2 mm）比稜的高度還細，**稜被拓印下來**。平滑 4 次只抹得掉幾 mm 寬的起伏（1.3 節） |
| 4 | `DECIMATE`（留 9%） | 合併邊 | 平面上合併不會改變形狀，所以平面被收成**很長的三角形**，點集中在稜線上 [B9][B10] |
| 5 | `smooth_normals` | 法線抄「減面前」的網格 | 那個網格（步驟 3 的結果）本身就有 16 條稜，**抄過來的光影也是 16 條** |

有人在論壇遇過一模一樣的事：低面數模型直接體素重建，結果還是一面一面的；把著色改成平滑也沒用，因為形狀本身沒變；解法是「先細分、再體素重建」[B4]。Blender 手冊也寫明，重建只看原始網格資料，沒套用的修改器不算 [B3]。我們的細分是先套用才重建的，所以重建看到的正是 16 邊形。

**用程式裡的 Skin 半徑推算，每條長條面有多寬、稜有多高**（把 16 邊形當正多邊形算，實際會有一點不均勻）：

| 部位（`skin_body` 節點） | Skin 半徑（左右, 前後） | 一圈周長約 | 每條長條面寬 | 稜的弓高（平面和圓差多少） |
| --- | --- | --- | --- | --- |
| 小腿肚（`s1`） | 39, 44 mm | 261 mm | **約 16 mm** | 約 0.8 mm |
| 上臂（`u1`） | 40, 38 mm | 245 mm | 約 15 mm | 約 0.75 mm |
| 大腿根（`hp`，×LW 1.05） | 71, 74 mm | 455 mm | 約 28 mm | 約 1.4 mm |
| 胸（`c2`，×BW 0.92、BD 0.96） | 112, 83 mm | 620 mm | **約 39 mm** | 約 1.9 mm |

- 稜的弓高（0.75～1.9 mm）**比體素格子（1.2 mm）還大或差不多**，所以體素重建一定記得住。
- 小腿最明顯，推測是因為小腿又長又直、長條面窄（16 mm），看起來就是一條條直紋。胸口的長條面寬（39 mm），看起來比較像「一塊塊的面」，和使用者「胸口、肩膀有面感」的描述一致。
- 肩膀、髖部是 Skin 的「分叉點」。手冊說分叉點的拓撲比較亂、可能互相重疊 [B2]，所以那裡的面更不規則。

**細分次數提高後**（同樣算法）：

| 細分次數 | 一圈幾面 | 相鄰兩面夾角 | 小腿稜高 | 胸稜高 |
| --- | --- | --- | --- | --- |
| 2（現在） | 16 | 22.5° | 0.8 mm | 1.9 mm |
| 3 | 32 | 11.3° | 0.2 mm | 0.47 mm |
| 4 | 64 | 5.6° | 0.05 mm | 0.12 mm |

細分 4 次時，稜高只剩體素格子的十分之一以下，體素重建本身就會把它抹掉。

### 1.2 其他可能來源，怎麼分辨

| 來源 | 紋路長相 | 間距 | 從哪一步開始有 | 可能性 |
| --- | --- | --- | --- | --- |
| **Skin 16 邊形截面** | 沿著手腳的軸「直的」；軀幹上下直條 | 固定：小腿約 16 mm、胸約 39 mm（一圈剛好 16 條） | Skin＋細分之後就有 | **高** |
| 減面長三角形 | 細長三角形。圓柱上沿軸方向不彎，減面會沿軸拉長三角形 [B9] | 不規則 | 減面後 | 中（疊加在上面） |
| 自訂法線和實際形狀不一致 → 陰影邊紋 | 只出現在背光面、陰影交界附近 | 跟三角形的邊對齊 | 抄法線後 | 中。EEVEE 開發者說，剩下的陰影瑕疵「都來自著色用的法線和實際幾何法線不一致」[B11] |
| 體素階梯 | 跟世界 X／Y／Z 格線對齊的細紋 | 1.2 mm 的倍數 | 體素後 | 低。我們是從距離場重建、又平滑過，比醫學影像那種階梯小很多 [B17] |

### 1.3 為什麼「平滑多做幾次」不是好解法（推算）

拉普拉斯平滑對「寬 W 的起伏」，每做一次大約剩下 `1 − λ × (1 − cos(2π × 邊長 ÷ W))`（標準的頻率分析，本報告推算）。用我們的數字（邊長 1.2 mm、λ 0.6）：

| 部位 | 起伏寬 W | 每次剩下 | 做 4 次剩下 | 要剩 10% 要做幾次 |
| --- | --- | --- | --- | --- |
| 小腿 | 16 mm | 93.5% | **76%** | 約 34 次 |
| 胸 | 39 mm | 98.9% | **96%** | 約 200 次 |

- 4 次幾乎抹不掉。要抹掉胸口的稜得做兩百次，那會把膝蓋、鎖骨、胯下這些真的形狀一起抹糊，而且整個身體會縮小。
- 手冊也提醒：次數或係數大時縮小很明顯，要開「保留體積」[B5]。
- 所以平滑是治標。**源頭（16 邊形）改掉才是治本。**

### 1.4 怎麼診斷：是幾何的稜，還是法線／著色

建議做 6 個測試。都在背景 Blender 跑，新增一支 `scripts/surface_probe.py`，`body_build.py` 加 `SURFDIAG=1` 把 4 個階段的網格另存（Skin＋細分後、體素＋平滑後、減面後、抄法線後）。

| # | 測試 | 做法 | 看什麼、怎麼判讀 |
| --- | --- | --- | --- |
| T1 | 分階段拍照 | 4 個階段的網格，用同一盞燈、同一機位拍小腿、胸口近照；另拍平面著色＋線框各一張 | 紋路**從哪一步開始出現**，就是那一步造成的 |
| T2 | 截面量圓度（數字） | 在小腿肚、上臂、大腿、胸口，垂直骨頭切一刀，量「每個角度的半徑」，做傅立葉分析，看第 4、8、16、32 個「波」各多大（mm） | 第 16 個（細分 3 次則第 32 個）明顯突出＝Skin 截面造成。沒突出、只有雜訊＝不是 |
| T3 | 曲率 × 半徑 | 截面上每一點的轉角 ÷ 弧長 × 平均半徑。完美的圓處處＝1 | 有稜時一圈出現 16 個尖峰、中間接近 0。記最大值和標準差 |
| T4 | 法線圖 | 用發光材質把 (a) 抄過的自訂法線 (b) 面本身的法線，各換成顏色拍一張；再算每個角「自訂法線和面法線差幾度」 | (a) 光滑但成品還有紋 → 陰影、幾何類問題；(a) 本身有 16 條 → 來源網格有稜；差角大的地方＝陰影邊紋的風險區 |
| T5 | 斑馬紋 | 材質用「反射座標 → 條紋」（Texture Coordinate 的 Reflection 接 Wave Texture），拍小腿、胸口、肩膀 | 條紋在稜線處折彎＝表面有稜 [B12]。這是 CAD 業界檢查曲面順不順的標準看法 |
| T6 | 三角形形狀 | 每個面算「最長邊 ÷ 最短高」，畫直方圖、上色 | 長寬比 > 6 的面占多少、在哪裡 |

另外，Cycles 的 Geometry 節點有 Pointiness（尖銳度）輸出，可以把凸的地方塗亮、凹的塗暗，當目視輔助 [B13]。我們平常用 EEVEE，這個要切 Cycles 才有。

T2 的寫法示意（未實測；Blender 內建 numpy）：

```python
import math, numpy as np
def harmonics(p2, c):
    """p2：切面上的點（2D，單位 m）；c：截面中心。回傳第 k 個波的振幅（mm）"""
    ang = np.array([math.atan2(y - c[1], x - c[0]) for x, y in p2])
    rad = np.array([math.hypot(x - c[0], y - c[1]) for x, y in p2])
    o = np.argsort(ang)
    grid = np.linspace(-math.pi, math.pi, 720, endpoint=False)
    r = np.interp(grid, ang[o], rad[o], period=2 * math.pi)
    F = np.abs(np.fft.rfft(r)) * 2 / len(r)
    return {k: round(float(F[k]) * 1000, 3) for k in (4, 8, 16, 32, 64)}
```

建議門檻（本報告建議，實測後校正）：

| 數字 | 門檻 |
| --- | --- |
| 第 16、32 個波的振幅 | ≤ 0.05 mm |
| 曲率 × 半徑 | 最大 ≤ 2、標準差 ≤ 0.3 |
| 長寬比 > 6 的三角形 | ≤ 1%（不含手腳接口過渡帶） |

### 1.5 解法比較

| 解法 | Blender 怎麼做 | 效果 | 代價 | 對 UV | 對權重 | 對服裝 | 建議 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A. Skin 後細分提高（2 → 4 次）** | `skin_body` 的 `sub.levels` 改成參數 `SKINSUB`，預設 4 | **從源頭消掉稜**。形狀幾乎不變（圍度差約 1% 以內，推算） | Skin 輸出面數 ×16（約十幾萬面，仍很小）；體素重建時間幾乎不變。**要重校接口常數**（見 1.6） | 不影響（UV 在後面才展） | 不影響（權重在後面才算） | 衣服跟著變順；要重長一次 | **P0** |
| **B. 粗體素、不減面** | 手腳模板開著時：`VOXEL` 1.2 → 約 3 mm、跳過 `DECIMATE` | 沒有長三角形；面大小均勻、以四邊形為主（手冊：adaptivity > 0 才會出現三角形 [B3]，我們設 0） | 胯下、腋下比 2 格（約 6 mm）窄的縫可能被填；要重校接口常數 | Smart UV 在均勻網格上比較不會有細長島 | 自動權重在均勻網格上比較穩（推測） | 衣服的切邊、加厚少了碎三角形 | **P1** |
| C. 更強的平滑 | 拉普拉斯次數加多、限定頂點群組；或自己寫 Taubin 平滑（先縮再撐，不會整體變小 [B8]）；或 Blender 5.x 的幾何節點 `Mesh to SDF Grid → SDF Grid Mean → Grid to Mesh`，在格子裡先模糊再包皮 [B7] | 稜變淡 | 真的形狀一起糊、整體縮小（1.3 節）；寫新程式 | 不影響 | 不影響 | 衣服變順 | P2：A、B 做完還有殘留才用 |
| D. QuadriFlow／Instant Meshes 四邊形重建 | `bpy.ops.object.quadriflow_remesh()`（內建）；Instant Meshes 是外部程式 [B15] | 四邊形、順著形狀走 | 手冊明說**不適合當會變形角色的最終拓撲**、不會清掉互相穿插的幾何、不同 seed 排法不同 [B3]；舊版有開 seed 會當掉的回報 [B16]；每副身體拓撲還是不同 | 要重展 | 要重算 | 沒好處 | **不建議** |
| E. Shrinkwrap 投影到光滑代理面 | 做一個光滑的代理（例：A 的結果、或大量平滑過的副本），成品用 Shrinkwrap（最近表面點）貼上去 [B14] | 網格不變、只移動點到光滑面上 | 要先有光滑代理（等於先做 A）；多一步 | 在展 UV 之前做就不影響 | 在綁骨前做就不影響 | 同 A | 現在不需要；**固定網格方案（第 2 節）會用到** |
| F. 自訂法線（已做，改來源） | `smooth_normals` 改抄更光滑的來源（A 之後的網格） | 只修光影 | **輪廓、陰影、衣服都不受影響**：陰影邊紋來自「著色法線和實際形狀不一致」[B11]；衣服用網格本身的法線往外推（`inflate`） | 不影響 | 不影響 | **沒幫助**（推測，依程式讀到的做法） | 保留當保險；A、B 做完後評估要不要關 |
| G. Corrective Smooth | 骨架變形後加一層 [B6] | 修「動起來」的擠壓摺痕 | 它會把靜止時的細節加回去，**靜止時就有的稜會原樣保留** | — | — | — | 不適用於這個問題；留給手肘、膝蓋變形 |
| H. 試驗：Skin＋細分直接當成品 | 跳過體素、減面，直接用 Skin＋細分 3 次的網格 | 網格順著肢體一圈一圈，同一副骨架拓撲可能固定 | Skin 在分叉點（肩、髖、脖子底）可能互相重疊 [B2]；拓撲在不同參數下是否固定**沒驗證過** | 要展 | 要算 | — | 0.5 天的試驗，結果可當第 2 節的參考 |
| I. 全身固定基礎網格 | 見第 2 節 | 根治 | 2～3 週 | 固定 UV | 固定 | 衣服可照點號對應 | P3 |

**為什麼現在可以考慮 B**：當初體素縮到 1.2 mm，是為了手指之間的縫不被填平（`checklist.md` 第 5 列）。現在手、腳改成固定模板，不進體素重建了。軀幹四肢最細的地方（前臂接口、小腿接口、脖子）半徑都在 25 mm 以上，用 3 mm 體素足夠。

面數推算（用 `_tplF3.work` 的實數字）：體素後 622,588 面 → 減面後成品共 101,226 面。改 3 mm 體素不減面，軀幹四肢約 622,588 × (1.2 ÷ 3)² ≈ **10 萬面**，加手腳模板約 12 萬面。和現在同一個量級。

| 體素 | 軀幹四肢面數（推算） |
| --- | --- |
| 2.5 mm | 約 14.3 萬 |
| 3.0 mm | 約 10.0 萬 |
| 3.5 mm | 約 7.3 萬 |

### 1.6 建議做法（Blender 怎麼實作）

1. **診斷（P0，0.5 天）**：寫 `surface_probe.py`（T1～T6），`body_build.py` 加 `SURFDIAG=1`。先用現有的 `_tplF3.work` 跑一次，確認第 16 個波是不是突出。
2. **細分改 4 次（P0，0.5～1 天）**：
   - `skin_body`：`sub.levels = SKINSUB`（新參數，預設 4；可設 3 對照）。
   - **一定要重校的常數**（都是照「細分 2 次＋體素＋平滑」的收縮率實測出來的，源頭變了就會偏）：
     - 手模板接口半徑 `SHR` 0.906（`hand_template.py`）
     - 腳模板接口半徑 `SHR_X` 0.92、`SHR_Y` 0.91（`foot_template.py`）
     - 脖子 Skin 半徑 ×1.19（有接口環時，`skin_body`）
   - 不重校會怎樣：接口處身體和模板粗細差一點點（推算約 0.5 mm），接縫會多一圈看得到的台階。
   - 重校方法：照原本的做法，量「Skin 半徑」對「成品半徑」的比例，換掉常數。
3. **粗體素、不減面（P1，1 天）**：
   - 條件：`HANDTPL=1` 且 `FOOTTPL=1`（手腳模板開著才行，手指不能進 3 mm 體素）。
   - `VOXEL` 試 2.5／3／3.5 mm；`DECIMATE` 設 1（跳過）；平滑次數重調（3 mm 格子上，4 次抹的範圍是現在的 2.5 倍）。
   - `smooth_normals`：先保留在手腳接口過渡帶；身體其他地方看 T4 結果決定要不要關。
   - 第 2、3 步之後，常數再校一次。
4. **必要時補強平滑（P2）**：拉普拉斯限定在軀幹側面頂點群組，或改用 SDF Grid Mean。
5. **文件**：`zepeto-body-v2.md` 的參數表、`checklist.md` 加「表面品質」一列。

### 1.7 怎麼驗證

| 項目 | 方法 | 標準 |
| --- | --- | --- |
| 稜消失 | T2、T3、T6 數字，改前改後對照 | 1.4 的門檻 |
| 看起來順 | T5 斑馬紋、T1 近照；**加一盞側面掠射光**（紋路在斜光下最明顯） | 斑馬條紋不折彎 |
| 形狀沒變 | 小腿、上臂、大腿、胸、腰五處截面的圍度 | 改前改後差 ≤ 1% |
| 接縫沒壞 | `ring_check.py`（脖子）、`build.json` 的 `limb_templates.*.gap_mm`、近照 | 距離 0、夾角 < 1° |
| 腿沒黏住 | `body_checks` 的 `basic`（胯下 ≥ 身高 × 0.30） | 通過 |
| 手腳沒被動到 | `fingerprint`（手、腳的指紋） | **完全不變**（模板區不在體素範圍內，指紋應該一樣；變了代表有東西漏改） |
| 全部檢查 | `body_checks.py` | 全過 |

### 1.8 對服裝端、動畫端的影響

- **服裝**：好處是衣服跟著變順。網格換新，所有衣服要重長一次（重跑 `outfit.py` 即可，產生器本來就是這樣設計的）。權重照骨頭名字抄，不受影響。B 方案沒有碎三角形，`inflate` 前的清理步驟（合併太近的點、清退化面）會比較少動到。
- **動畫**：骨頭位置不變，形狀差 1 mm 以內，動作不用改；已定案的鏡只要重渲。
- **時機**：新版身體（4.5 頭身、手腳模板）**還沒出廠**，出廠時服裝、動畫本來就要全部重做。把這項修正併進同一次出廠，**下游不會多花工**。
- **頭端**：脖子接口常數重校後，跑一次 `ring_check.py` 即可，頭端不用改。

### 1.9 優先順序

1. P0：診斷＋細分 4 次（含重校常數）——新版身體出廠前做完。
2. P1：粗體素、不減面——同一次出廠前做完最好。
3. P2：補強平滑——只在前兩項做完還有殘留時。
4. P3：全身固定網格——見第 2 節。

---

## 2. 全身固定基礎網格：業界怎麼做

### 2.1 結論

- 業界的做法幾乎一致：**一套固定拓撲的網格**（點數、編號、UV、權重一次做好），身材差異靠「移動骨頭」或「形態鍵」改。沒有人每次從圓管融出新網格。
- 我們已經走了一半：頭（48 點環）、雙手（64 點環）、雙腳（64 點環）都是固定的。**只剩軀幹與四肢中段，每次都是 Skin＋體素融出來的。**
- 可行性高：我們的產生器本來就是「沿骨頭放節點、給半徑」，固定網格只是把「節點＋半徑」換成「一圈一圈固定點數的環」，和手模板同一套寫法。
- 工作量約 2～3 週，主要難在肩膀、腋下、胯下三處的邊怎麼走。**現在不建議做**，第 1 節的修正先做；觸發條件見 2.8。

### 2.2 各系統怎麼做

| 系統 | 網格 | 身材怎麼變 | 骨頭怎麼跟著變 | 衣服怎麼配合 |
| --- | --- | --- | --- | --- |
| **ZEPETO** | 官方基底身體（`creatorBaseSet`）。建模指南要求手肘、膝蓋、肩膀各有 3 條很靠近的邊環，彎的時候保持體積 [M1] | 改手臂、腿、軀幹「用移動骨頭（translation）」；縮放只用專用的 scale 骨，頭、手、腳例外；全身縮放 0.3～1.35；腿加長要把臀部骨頭抬高，腳才不會穿地；不准轉骨頭 [M2] | 就是改骨頭本身 | 從基底身體照骨頭名字抄權重 [M3] |
| **Ready Player Me** | 男、女各一套模板身體＋骨架 [M4] | 每種體型 4 種身材（官方部落格，網站已關閉，取自搜尋摘要）[M4] | 查不到 | 衣服照模板身體建模；身體部位的 UV 不能改；身體網格上限 2,000 三角形 [M4] |
| **MetaHuman**（Epic） | 標準拓撲；外部資料要「符合 MetaHuman 拓撲與骨架定義」才能套進來 [M5] | 參數化身體工具；另有舊版 18 種固定體型的相容模式 [M5] | 自動配合（細節查不到） | 市售衣服宣稱自動適應所有體型（廠商說法）[M5] |
| **MakeHuman／MPFB** | 基底網格 hm08，**點數、面數永遠一樣**，改身材只移動點 [M6] | 形態目標（每點位移） | **「關節方塊」**：網格裡專門的一小群點，骨頭的頭尾就放在它們的位置。例：大腿骨從膝蓋方塊拉到腳踝方塊 [M6] | 「輔助網格」：例如裙子輔助面，裙子、禮服掛在它上面 [M6]。核心素材 CC0 [M6] |
| **SMPL**（學術標準人體模型） | 6,890 點、23 個關節，男女同一套拓撲 [M7] | 10 個「身材形態鍵」（從掃描資料統計出來）＋隨姿勢變的修正形態鍵 [M7] | **關節位置用固定公式從網格點算出來**（關節回歸矩陣）[M7] | — |
| **Character Creator 4**（Reallusion） | CC3+ 基底拓撲，標好關節環與肌肉線，同一套網格做寫實和卡通 [M8] | 形態滑桿 | 做滑桿時可以「自動調整骨頭貼合形態」[M8] | 衣服自動貼合（功能列表）[M8] |
| **Daz** | Genesis 固定拓撲 | 形態滑桿 | 「依形狀調整骨架」把關節中心移回網格裡，再把移動量綁到滑桿上（論壇說明）[M9] | 衣服跟隨（Auto-Follow） |
| **Roblox** | 身體要附「外籠子」；衣服要有內、外兩個籠子；建議從官方模板開始，**籠子的 UV 不要改**，否則會有瑕疵 [M10] | 換整塊部件 | — | 籠子對籠子變形，衣服可以穿在任何身體上 [M10] |
| **CLO（服裝設計軟體）** | 固定的虛擬人台 | 輸入尺寸；沒給的尺寸照數千筆掃描資料自動推 [M14] | — | 打版直接在人台上 |
| **VRoid** | Body、Face、Hair 三塊 | 滑桿 | 官方查不到 | 查不到。第三方工具會「加密網格讓方塊感變順」[M13]（廠商說法） |

### 2.3 歸納：四個共同模式

1. **一套固定網格**：點數、編號、UV、權重一次做好，之後每個角色都一樣。
2. **身材用「移動骨頭」或「形態鍵」改**：ZEPETO 用前者 [M2]，SMPL、MPFB 用後者 [M6][M7]。
3. **骨頭位置從網格算**：MPFB 的關節方塊、SMPL 的關節回歸、CC4 與 Daz 的「依形狀調骨架」，都是同一個意思 [M6][M7][M8][M9]。
4. **衣服靠一個固定的參考面來套**：Roblox 的籠子、MPFB 的輔助網格、RPM 的模板身體 [M4][M6][M10]。

### 2.4 套到我們身上：可行性

**我們已經有的**：

| 部位 | 現況 |
| --- | --- |
| 頭 | 48 點接口環（固定，合約已定） |
| 雙手 | 手模板，前臂 64 點接口環（固定） |
| 雙腳 | 腳模板，小腿 64 點接口環（固定） |
| 骨架 | `bones_layout()` 照參數算骨頭位置 |
| 身材參數 | `N`（頭身）、`BW`、`BD`、`LW`、`LEGR`、`WRF`、`FOOTL`、`ANKH` |
| 軀幹、四肢中段 | **每次 Skin＋體素＋減面融出來，拓撲每次不同** |

**兩條路**：

| | 路線一：程式產生籠子（推薦） | 路線二：拿現成基底網格改 |
| --- | --- | --- |
| 做法 | 延伸 `hand_template` 的寫法：沿骨頭一圈一圈放固定點數的環（軀幹每圈約 24～32 點、四肢 16 點），肩膀、腋下、胯下用固定的「補片」接起來，兩端直接接上頭環、手環、腳環；細分 1～2 次 | 拿 MPFB 的 hm08（CC0 [M6]）或 Blender 官方基底網格 [M11]，先改成 ZEPETO 4.5 頭身，再接我們的頭、手、腳環 |
| 頭身比、身形 | 現在 `skin_body` 的「節點位置＋半徑」直接變成「環的位置＋半徑」，參數不用改 | 用移動骨頭（ZEPETO 做法）＋「套用為靜止姿勢」[M12]；或做形態鍵 |
| 好處 | 全程自己控制；和手腳模板同一套程式 | 拓撲是專業做好的 |
| 壞處 | 肩膀、胯下的邊怎麼走要自己設計 | 寫實比例改成卡通很費工；手腳拓撲和我們的模板不同，要切掉重接；Blender 基底網格的授權說法不一（2.8 節） |

**做了之後各方面的變化**：

| 面向 | 變化 |
| --- | --- |
| UV | 接縫固定在模板上。衣服是複製身體長的，**衣服的 UV 也跟著固定**，布紋位置每版都一樣 |
| 權重 | 照「這個點在哪一節骨頭上」算（手模板已經這樣做）。肩膀、髖部多骨頭交會處要特別處理，必要時退回自動權重 |
| 尺寸 | 手腕圍、腳踝圍、脖子圍都變成「第幾號邊環」，量法固定、不會跳（第 3 節） |
| 服裝 | 可以照點號對應衣服（以後換身材時，衣服用形態鍵跟著變，不必重長） |
| 動畫 | 骨架不變。關節處有 3 條邊環，彎曲變形更穩（ZEPETO 指南的做法 [M1]） |
| 表面 | 沒有體素、沒有減面，第 1 節的問題整個不存在 |

**工作量（粗估，不含使用者審看等待）**：

| 工作 | 天數 |
| --- | --- |
| 軀幹籠子：骨盆、腰、胸、肩線各圈；肩膀與腋下、胯下與臀部的補片；接頭環 48 點 | 4～6 |
| 手臂、腿：每段的環，肩膀、手肘、膝蓋各 3 條邊環；接手環、腳環 | 1～2 |
| 權重（照位置算＋自動權重備案）、檢查 | 2～3 |
| 固定 UV（接縫位置、島排版） | 1 |
| 審看、修改、下游重跑 | 2～4 |
| **合計** | **10～16 天** |

### 2.5 建議做法（Blender 怎麼實作）

1. 新增 `scripts/body_template.py`，介面和 `hand_template.build()` 一樣：輸入骨頭位置與身材參數，輸出一塊四邊形籠子＋點屬性（部位、環號、地標）。
2. 每一圈是橢圓（半徑 = 現在 Skin 節點的左右、前後半徑），點數固定。關節處前、中、後各一圈（ZEPETO 指南的「3 條很靠近的邊環」[M1]）。
3. 兩端直接用現有的接口合約：脖子頂＝頭環 48 點，前臂＝手環 64 點，小腿＝腳環 64 點。不再需要 `fit_neck_ring`、`fit_tpl_rings` 的「切開、拉鍊、過渡帶」。
4. 細分 1～2 次後直接用。要更順時加 Shrinkwrap 貼到光滑代理面（1.5 的 E）。
5. 權重：籠子點上寫好，細分時內插（手模板的做法）。肩膀、髖部先試自動權重。
6. UV：在籠子上標接縫（腋下內側、身體兩側、腿內側），展一次就固定。
7. 舊路線（Skin＋體素）保留成開關，對照用。

### 2.6 怎麼驗證

| 項目 | 方法 | 標準 |
| --- | --- | --- |
| 拓撲固定 | 改 `N`、`BW`、`LW` 各做一次，比點數與「誰連誰」的雜湊 | 完全相同 |
| 形狀 | 和現行身體並排，五處截面圍度、身高、胯下 | 差 ≤ 2%（本報告建議） |
| 變形 | 現有 `body_checks` 全部、ROM 掃描（肩膀舉過頭、交叉抱胸、深蹲） | 全過；肩膀、胯下近照沒塌 |
| 表面 | 1.4 的 T2、T5 | 門檻同 1.4 |
| 接縫 | `ring_check`、手腳接口 | 距離 0 |

### 2.7 對服裝端、動畫端的影響

- **服裝**：所有衣服要重長、重驗一次（`garment_lib` 的配方不用改，但要確認新網格上的切割、加厚、抄權重都正常）。長期好處：UV 固定、尺寸固定、可以照點號對應。
- **動畫**：骨架不變，動作不用改；但身體外形和變形會變，已定案的鏡要重看近照。
- **導演**：新娘 v3 被開場片 B 鎖定，換網格要先經導演排程。

### 2.8 優先順序與觸發條件

**P3，現在不做。** 出現下列任一情況時再開工：

1. 第 1 節的修正做完，表面還是不夠乾淨。
2. 要做新郎、新娘的身材差（`checklist.md`：「新娘的身高、身材形態鍵：等所有工作流成熟再做」）。形態鍵需要固定拓撲。
3. 服裝端需要穩定的 UV 或點號對應（例：印花位置要每版一樣）。

---

## 3. 交接給服裝的尺寸

### 3.1 結論

- 現在出廠紀錄只有 3 樣服裝在用的東西（骨頭位置、脖子切口高度、拇指根位置），外加 `checks.json` 裡 4 個鞋子尺寸（長、腳掌寬、腳跟寬、腳背高）。**沒有任何圍度**，而這 4 個尺寸的量法和業界定義也不一樣。
- 建議新增 `body_measure.py`，照 IBV（西班牙瓦倫西亞生物力學研究所）與 ISO 的定義量約 20 個尺寸，寫進 `build.json` 的 `measure`，出廠時複製到 `RELEASE.json`，並自動列出和上一版的差異。
- 量法：用「切一刀的截面」算。圍度用「凸包周長」，就是皮尺量法（皮尺會跨過凹下去的地方）。

### 3.2 現況與問題

**身體端現在怎麼量**（`body_checks.py` 的 `feet.shoe`）：

| 尺寸 | 現在的量法 | 業界定義 [F1] | 差在哪 |
| --- | --- | --- | --- |
| 腳長 | 腳的點在 y 方向的最大減最小 | 腳跟最後點到最前點，投影到「腳軸」上 | 腳朝正前方時一樣；腳有轉角時會偏 |
| 腳掌寬 | 腳趾骨頭那條橫線上、離地 4 cm 內的點的左右寬 | 通過**第 1、第 5 蹠骨頭**（大拇趾根、小趾根的骨頭凸點）的斜截面，投影到地面的寬 | 真的腳掌線是斜的（大拇趾根比小趾根前面），橫線會量偏 |
| 腳跟寬 | 腳踝到腳跟中間那條線的寬 | 離腳跟 16% 腳長處的截面寬 | 位置不同，數字不能跟真鞋比 |
| 腳背高 | 從腳尖往腳踝 60% 處的最高點 | 離腳跟 50% 腳長、垂直腳軸的截面最高點 | 位置不同 |
| 圍度 | **沒有** | 腳掌圍、腳背圍等 | 鞋子是包著腳長出來的，加厚量和圍度有關 |

**服裝端寫死的數字**（`garment_lib.py`；每個在新腳上的後果）：

| 寫死的地方 | 數字 | 新腳上會怎樣 |
| --- | --- | --- |
| `laces` 鞋帶位置 | y = −48、−61、−74 mm | 照舊腳放的。新腳長 232 mm、腳踝往後移，鞋帶會跑到錯的位置 |
| `shoes` 鞋口高度 | 腳踝關節 + 75 mm | 新腳踝關節約 84 mm 高 → 鞋口約 158 mm，**剛好在小腿接口環（0.158 m）上**。那裡網格密度突然變，切邊可能鋸齒（推測） |
| 褲腳 | 腳踝關節 + 45 mm | 新腳踝抬高，褲腳跟著抬高約 6 cm（舊腳踝約 23 mm 高）。要確認是不是想要的長度 |
| 鞋頭往前拉 | 15 mm | 腳變長，比例改變 |
| 袖口、外套袖口 | 手腕前 12 mm、35 mm | 新手模板的手腕形狀不同；只有位置、不知道那裡多粗 |

### 3.3 業界量哪些

#### 鞋（鞋楦）

業界的鞋楦比腳略長（留腳趾空間）、圍度比腳略大（走路時腳會脹）[F6]。一份參數化鞋楦的社群模型，鞋楦長固定比腳長多約 11.5 mm（僅供參考）[F10]。台灣一份 2,486 人的研究指出，**腳長和腳掌圍是設計鞋楦的兩個主要因素** [F11]。

| 尺寸 | 定義 | 出處 | 服裝端用在哪 |
| --- | --- | --- | --- |
| 腳軸 | 腳跟最後點，到「第 1、第 5 蹠骨頭中點」的連線（投影到地面） | IBV [F1] | 其他尺寸的基準線 |
| 腳長 | 腳跟最後點到最前點，投影到腳軸 | IBV；ISO 7250-1 §6.3.7、ISO 8559-1 §5.5.5 [F1] | 鞋長、鞋頭位置 |
| 第 1、5 蹠骨頭位置 | 大拇趾根、小趾根的骨頭凸點 | IBV [F1] | 鞋子最寬處、鞋子彎折線 |
| **腳掌圍** | 通過第 1、5 蹠骨頭、垂直地面的截面周長 | IBV；ISO 8559-1 §5.4.7 [F1]；鞋楦上是「前腳最大的一圈」[F7] | 鞋頭的寬鬆度、加厚量 |
| 腳掌寬、腳掌高 | 同一截面的寬（投影到地面）、最高點 | IBV [F1] | 鞋頭形狀 |
| 腰圍（鞋楦） | 腳掌圍和腳背圍之間最小的一圈 | 鞋楦定義 [F7] | 鞋子中段收腰 |
| **腳背圍** | 離腳跟 50% 腳長、垂直腳軸的截面周長 | IBV [F1]；鞋楦上是「通過腳背點的一圈」[F7] | 鞋帶、鞋舌的位置與高度 |
| 腳背高、腳背寬 | 同一截面的最高點、最寬 | IBV [F1] | 鞋帶、魔鬼氈位置 |
| 腳背到腳跟圍 | 從腳跟繞過腳背點（50% 腳長）的斜截面周長 | IBV；ISO 19408-1 §6.3.7 [F1] | 鞋口開多大才「穿得進去」（3D 不用真的穿，作為靴子比例參考） |
| **腳跟寬** | 離腳跟 16% 腳長處、截面最凸那點的寬 | IBV [F1] | 鞋跟、後跟杯 |
| 腳趾高、腳趾圍 | 通過大拇趾、小趾關節的截面最高點；周長用**凸包** | IBV [F1] | 鞋頭高度（鞋頭不能壓到腳趾） |
| 足弓高（舟骨高） | 足弓最高點（舟骨凸點）離地高度 | IBV [F1] | 鞋墊形狀；我們的腳模板目前量的是內側邊離地 4 mm |
| 腳踝關節高 | `J_Bip_*_Foot` 骨頭高度 | 我們自己的定義 | 鞋口、褲腳的基準 |
| 外踝高 | 外踝骨最凸點的高度 | ISO 8559-1 §5.1.17 [F3] | 短靴、襪子高度 |
| **腳踝圍** | 內踝高度的水平周長 | IBV（自訂）[F2] | 鞋口、褲腳 |
| **最小腿圍** | 腳踝骨正上方、小腿最細的一圈 | ISAK §6.2.25；ISO 18825-2 §2.2.27 [F2] | 褲腳收口、長靴筒 |
| 腳跟到前掌長 | 腳跟最後點到第 1 蹠骨頭，沿腳軸 | 本報告建議（鞋業稱 heel-to-ball；查不到正式定義） | **高跟鞋**要的角度（見下） |

**高跟鞋要的角度（本報告推導）**：穿高跟鞋時，腳跟被墊高、前腳掌還貼地。腳往下壓的角度約 = arcsin（跟高 ÷ 腳跟到前掌長）。

- 我們的腳模板：腳趾關節離腳尖 0.311 腳長（`limbs.md` 2.4），所以腳跟到前掌約 0.69 × 232 ≈ 160 mm。
- 跟高 5 cm → 約 18°；8 cm → 約 30°。腳趾要往上翹差不多同樣角度。
- 都在現有腳的檢查範圍內（腳踝往下 50°、腳趾往上 40°／70°）。新娘如果穿高跟鞋，服裝端與動畫端可以直接用這個數字擺腳。
- 業界高跟鞋鞋楦的「鞋頭翹度」在跟高約 100 mm 時約 7～10 mm（一份專利的數字，非標準）[F9]。

#### 袖口、褲腳、領口

| 尺寸 | 定義 | 出處 | 服裝端用在哪 |
| --- | --- | --- | --- |
| **手腕圍** | 手腕點（小指側手腕骨凸點）高度的周長 | ISO 8559-1 §5.3.19；ISO 7250-1 §6.4.12 [F2][F3] | 襯衫袖口 |
| 前臂最大圍 | 手肘到手腕 1/3 處的最大周長 | ISO 7250-1 §6.3.20 [F2] | 袖子收窄 |
| 上臂圍 | 肩點到肘點中間的周長 | ISO 8559-1 §5.3.16 [F2] | 袖子 |
| 小腿最粗圍 | 小腿最粗處的水平周長 | ISO 8559-1 §5.3.24 [F3] | 褲管 |
| 膝圍 | 膝蓋中心高度的水平周長 | ISO 8559-1 §5.3.22 [F2] | 褲管 |
| 大腿圍 | 臀下摺線下方、大腿最粗處的水平周長 | ISO 8559-1 §5.3.20 [F3] | 褲管、裙擺 |
| 脖子圍 | 垂直脖子軸量的周長 | ISO 8559-1 §5.3.2 [F2] | 領口 |
| 脖子根圍 | 經過後頸點的脖子底部周長 | ISO 8559-1 §5.3.3 [F3] | 領口、露肩 |
| **圍度曲線** | 沿前臂、小腿每 5 mm 量一個圍度 | 本報告建議 | 服裝端在任何位置切袖口、褲腳都查得到「那裡多粗」，不用身體端知道服裝要切在哪 |

> ISO 8559-1 原文要付費，上面的定義是 IBV、Bodygram 的轉述 [F2][F3]。

### 3.4 建議的出廠紀錄欄位

寫在 `build.json` 的 `measure`；出廠時 `body_status.py release` 把它複製到 `RELEASE.json` 這個身體底下，並和上一個出廠版比對。

```json
"measure": {
  "ver": 1, "pose": "T 字靜止", "unit": "mm", "side": "L（右邊鏡像，另記左右差）",
  "landmarks": {"heel_back": [], "toe_tip": [], "mtp1": [], "mtp5": [], "instep_pt": [],
                "navicular": [], "ankle_joint": [], "wrist_pt": [], "thumb_root": []},
  "foot": {"length": 232.0, "ball_girth": null, "ball_width": null, "ball_height": null,
           "waist_girth": null, "instep_girth": null, "instep_height": null, "instep_width": null,
           "instep_heel_girth": null, "heel_width": null, "toe_height": null, "toe_girth": null,
           "arch_height": null, "heel_to_ball": null, "ankle_joint_height": null,
           "outer_ankle_height": null, "ankle_girth": null, "min_leg_girth": null},
  "arm":  {"wrist_girth": null, "forearm_max_girth": null, "upper_arm_girth": null,
           "hand_length": null, "hand_breadth": null},
  "leg":  {"calf_girth": null, "knee_girth": null, "thigh_girth": null},
  "neck": {"ring_girth": null, "base_girth": null, "cut_z": null},
  "profile": {"forearm": [[0, 0.0]], "shin": [[0, 0.0]]}
}
```

- `landmarks` 存世界座標（m）。手、腳模板是固定拓撲，地標可以直接寫成模板的**固定點號**（在 `hand_template.py`、`foot_template.py` 加點屬性 `landmark`），每次都量同一個點，數字不會跳。
- `profile`：`[離手腕（或腳踝）的距離 mm, 圍度 mm]`，每 5 mm 一筆。
- **出廠時自動寫 changes**：任何欄位變化 ≥ 1 mm 或 ≥ 1%（本報告建議）就列一行，例：「腳掌圍 214 → 218 mm（+4）」。`SKILL.md` 第 9 步本來就要求「服裝要量的東西有變就要寫」，改成自動列出，就不會漏。
- 現在 `RELEASE.json` 的 `handoff` 是一大段文字。建議另外加一個機器讀得懂的 `measure`，服裝端程式直接讀，不用從文字裡找數字。

### 3.5 怎麼從網格自動量（截面周長）

1. **姿勢**：T 字靜止，修改器算完（depsgraph 評估過的網格），世界座標。
2. **切面**：用地標或骨頭算一個平面（一點＋法線）。
   - 腳掌圍：通過 MTP1、MTP5、垂直地面 → 法線 = (MTP5 − MTP1) × Z。
   - 腳背圍：腳軸 50% 處、法線 = 腳軸方向。
   - 手腕圍：手腕點、法線 = 前臂骨頭方向。
3. **找交點**：每條邊兩端點在平面兩側，就算交點。只留離目標中心一定距離內的（避免量到另一隻腳）。
4. **周長**：交點投影到切面上的 2D 座標，用 `mathutils.geometry.convex_hull_2d` 取凸包，算凸包周長＝**皮尺圍**。IBV 的腳趾圍就是用凸包周長 [F1]。手腳、小腿的截面本來就接近凸形，凸包周長和實際周長幾乎一樣。
5. **寬、高**：交點在指定方向（地面上的左右、垂直）的最大減最小。

寫法示意（未實測）：

```python
import bpy, math
from mathutils.geometry import convex_hull_2d

def section(obj, co, no, center, rmax, ax_w, ax_h):
    """co, no：切面上一點與法線；center, rmax：只留這個範圍內的交點；ax_w, ax_h：量寬、量高的方向（單位向量）"""
    dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me = ev.to_mesh()
    V = [obj.matrix_world @ v.co for v in me.vertices]
    pts = []
    for e in me.edges:
        a, b = V[e.vertices[0]], V[e.vertices[1]]
        da, db = (a - co).dot(no), (b - co).dot(no)
        if da * db < 0:
            p = a.lerp(b, da / (da - db))
            if (p - center).length < rmax:
                pts.append(p)
    ev.to_mesh_clear()
    p2 = [((p - co).dot(ax_w), (p - co).dot(ax_h)) for p in pts]
    hull = [p2[i] for i in convex_hull_2d(p2)]
    tape = sum(math.dist(hull[i], hull[i - 1]) for i in range(len(hull)))
    w = [q[0] for q in p2]; h = [q[1] for q in p2]
    return dict(girth_mm=round(tape * 1000, 1), width_mm=round((max(w) - min(w)) * 1000, 1),
                height_mm=round((max(h) - min(h)) * 1000, 1), n=len(pts))
```

`ax_w`、`ax_h` 要和切面垂直（先把它們投影到切面上再正規化）。

### 3.6 怎麼驗證

| 項目 | 方法 | 標準 |
| --- | --- | --- |
| 程式算得對 | 量一根已知的圓柱（半徑 30 mm → 周長 188.5 mm）、一個已知的方塊 | 差 ≤ 0.1 mm |
| 可重現 | 同一副身體量兩次；同參數做兩副身體 | 完全一樣 |
| 和現有數字對得上 | 腳長和 `feet.shoe.length_mm`（232）比 | 差 ≤ 0.5 mm |
| 位置對 | 審看頁「腳」區放一張示意圖，把每個截面畫在腳上（4.4 的 F9） | 使用者、服裝端看圖確認 |
| 左右對稱 | 左右各量一次 | 差 ≤ 0.5 mm |

參考：真人腳的 3D 掃描和手量比，腳長、腳掌寬、腳掌圍、腳跟寬差 ≤ 4 mm，腳踝圍差比較大 [F8]。我們量的是網格本身，沒有「人站不穩、皮尺鬆緊」的誤差，所以可以要求得更嚴。

### 3.7 對服裝端、動畫端的影響

- **服裝端**（要通知它改，不是身體端改）：
  - `laces` 的鞋帶位置改用 `instep_pt`、`mtp1` 推，不再寫死。
  - 鞋口高度改用 `ankle_girth`、`outer_ankle_height`，避開小腿接口環的過渡帶。
  - 鞋子加厚量可以參考 `ball_girth`、`instep_girth`。
  - 袖口、褲腳查 `profile` 拿到那個位置的圍度。
  - 高跟鞋用 `heel_to_ball` 算腳的角度。
- **動畫端**：高跟鞋鏡頭用 `heel_to_ball` 算腳踝、腳趾角度；其他不受影響。
- **身體端**：出廠紀錄多一段，出廠時自動列變化。

### 3.8 優先順序

**P1。** 服裝端「之後要照新的腳重做鞋子」，最好在那之前把 `measure` 做好，鞋子一次照尺寸重做。手模板、腳模板加地標點屬性要一起做。

---

## 4. 身體審看網頁該放什麼

### 4.1 結論

- 業界的角色綁定審看，核心是：**轉檯（各角度）、素模＋線框、一次只動一個關節的壓力測試、超過動畫需要的極端姿勢、權重檢查、固定的一段測試動作當回歸**（每次都跑同一段，才看得出有沒有變壞）[R1][R2][R3][R4][R6]。
- 查不到正式的「審看網頁格式標準」，以下清單是依這些做法、加上我們現有的檢查數字整理的。
- 我們的 `body_page.py` 目前有：檢查表、站姿、T 字、脖子、手（4 張）、9 個手勢、動作、腳（3 張）、UV。
- 缺的：**手腳的 ROM 掃描條、權重熱圖、接口近照、腳底接觸圖、新舊同機位並排、尺寸表、線框**。

### 4.2 業界做法（依據）

| 做法 | 內容 | 來源 |
| --- | --- | --- |
| 轉檯 | 從所有角度看；中性、均勻的燈光，讓每個角度都一樣公平；角色置中 | [R4] |
| 素模＋線框 | 素模看形狀；線框看邊怎麼走、適不適合動畫 | [R4] |
| 壓力測試 | 直接轉控制器、找權重問題；問題回給綁定或建模，重複到動得對為止 | Blender Studio [R3] |
| 一次動一個關節、多角度看 | 能分出是關節、權重還是拓撲的問題；彎超過動畫需要的範圍；左右都要測 | 廠商檢查清單（參考）[R6] |
| 固定的測試動作 | 做一段包含極端姿勢與過渡格的動作，和展示用的動畫分開，當回歸工具 | 廠商檢查清單（參考）[R6] |
| 常用循環動作 | Roblox 的 Calisthenics 工具：走、跑、移動、待機循環，停在出問題的格子直接修權重 | Roblox [R2] |
| 自然姿勢 | 轉身體骨頭，確認在自然姿勢下彎得對 | Roblox [R1] |
| 拉時間軸找鼓包 | 肩膀舉起時胸口內側會鼓，拉時間軸找出來再修權重 | 華盛頓大學課程作業 [R5] |
| 權重是 0 的地方 | Blender 有「零權重」顯示，0 顯示成黑色 | [R7] |

### 4.3 「手」區清單

| 小區 | 放什麼 | 產生的程式（現有／新增） | 使用者看什麼 | 旁邊放的數字 |
| --- | --- | --- | --- | --- |
| H1 結論列 | 一列通過／沒過標籤（H1～H12，見 `research-hands-feet.md` 6.3）＋一句白話 | `checks.json` | 有沒有紅的 | — |
| H2 靜止造型 | 手背、手心、拇指側、小指側、指尖方向、斜 45°（現在只有 4 張） | `body_build` 現有 4 張＋`hand_probe.py` 補 2 個角度 | 指根 L 形、指蹼、虎口、掌緣 | 手長、手寬、拇指根位置 |
| H3 線框 | 手背、手心，線框疊在膚色上 | 新增：複製一份加 Wireframe 修改器（細線）一起渲 | 每個關節 3 圈邊、掌緣一條連續的邊 | 點數、指紋 |
| H4 手勢 | 9 個共用手勢（現有）＋雙手合十、拍手、交握、OK 手勢 | `hand_probe.py -- GEST=lib`＋新增雙手 | 穿插、拇指位置 | 每個手勢旁列「穿插最深」「關節內側擠壓最深」 |
| H5 ROM 掃描條 | 一排小圖：四指 0／30／60／90／110°（側面）；拇指往掌心 45°、往側 60°；手腕彎 70°、翹 60°、扭 ±80° | 新增 `hand_probe.py -- MODE=rom` | **從幾度開始塌、鼓、穿** | 每格下面寫截面積比、最深穿插 |
| H6 權重熱圖 | 「每點最主要的骨頭」分區上色 1 張＋Hand、Index1、Thumb1 三根骨頭的漸層各 1 張 | 新增 `weight_probe.py`：權重寫成顏色屬性，用發光材質渲 | 串到隔壁手指、過渡太急 | 跨指污染點數、過渡寬度 |
| H7 接縫 | 前臂接口環：靜止、手腕彎 70°、扭 80° | 新增 `hand_probe.py -- MODE=seam` | 有沒有線、明暗斷層 | 距離、法線夾角、權重 |
| H8 新舊並排 | 出廠版和這版：手背、手心、握拳、比 YA，**同機位、同燈光**；可加左右拖曳的對照滑桿 | `body_page.py --prev`（擴充到這幾張） | 哪裡變了 | 每個數字的上一版與變化 |

### 4.4 「腳」區清單

| 小區 | 放什麼 | 產生的程式（現有／新增） | 使用者看什麼 | 旁邊放的數字 |
| --- | --- | --- | --- | --- |
| F1 結論列 | 一列通過／沒過＋「參考、不擋」標籤 | `checks.json` 的 `feet` | — | — |
| F2 靜止造型 | 外側、內側、前、後、上、腳底（現在有外側、前、內側、腳底） | `foot_probe.py` 補後、上 | 腳趾、腳踝骨、腳跟形狀 | 腳長、腳掌寬 |
| F3 線框 | 外側、上方 | 同 H3 | 腳背、腳趾根的邊環 | 點數、指紋 |
| F4 腳底接觸圖 | 從下往上看，**離地距離上色**：紅＝低於地面、綠＝0～2 mm、藍＝3 mm 以上 | 新增 `foot_probe.py -- MODE=sole` | 腳跟、前腳掌貼地，足弓懸空 | 腳跟最低、前腳掌最低、最低點、足弓高 |
| F5 ROM 掃描條 | 腳踝往上 20／30°、往下 45／50°、往內 20°、往外 15°；腳趾往上 40／60／70／90°、往下 30°；墊腳尖（腳踝下 45°＋腳趾上 60°）；跪姿（腳趾上 90°） | `foot_probe.py` 的 `POSES` 擴充（現在只有 4 個） | 腳背摺痕、腳趾壓進前腳掌 | 每格寫埋住點數、最深、翻面、壓扁 |
| F6 動作抽格 | 走路蹬地、跑、蹲、跪、盤腿坐，腳的近照 | 新增（抽 Mixamo 動作的腳最彎那格） | 穿地、滑動 | — |
| F7 權重熱圖 | LowerLeg／Foot／ToeBase 分區＋漸層 | `weight_probe.py` | 過渡位置對不對 | 過渡寬度 |
| F8 接縫 | 小腿接口環：靜止、腳踝上 30°、下 50° | `foot_probe.py -- MODE=seam` | 線、明暗斷層 | 距離、夾角 |
| F9 鞋楦尺寸表＋示意圖 | 第 3 節的尺寸表；一張腳的側面、上方圖，**把每個截面畫上去** | `body_measure.py` 輸出＋`body_page.py` 畫 SVG | 量的位置對不對 | 這版、上一版、變化 |
| F10 新舊並排 | 同 H8：外側、腳底、墊腳 | `--prev` | 哪裡變了 | — |

### 4.5 另加一小區「表面品質」（和第 1 節配套）

| 放什麼 | 程式 | 看什麼 | 數字 |
| --- | --- | --- | --- |
| 斑馬紋：小腿、胸口、肩膀各一張（含側面掠射光） | `surface_probe.py`（T5） | 條紋有沒有折彎 | 第 16／32 個波的振幅、曲率×半徑最大值、長三角形占比 |
| 截面圓度圖：小腿、胸口的「半徑 vs 角度」曲線 | 同上（T2） | 有沒有一圈 16 個波 | — |

### 4.6 共通：數字怎麼呈現、轉檯、新舊並排

- **每區開頭先講結論**：一個標籤（通過／要看）＋一句白話（例：「握拳到 110° 指尖碰掌心 2.4 mm，真人也會碰到，只當參考」）。
- **數字表欄位**：項目、結果、這版、上一版、變化、標準、會不會擋出廠。不擋的項目用灰色標「參考」。
- **同機位、同燈光**：新舊並排才有意義。燈光固定加一盞側面掠射光，表面的稜在斜光下最明顯。
- **轉檯**：靜態頁面放 8 個角度（每 45°）一排的小圖，分素模、線框兩排。要動的話可以用小的動態 WebP，但頁面會變大。
- **左右**：現在的近照只拍左手、左腳。至少加一個數字檢查：左右鏡像後的點位置差（手腳是固定模板，應該是 0）。
- **大小**：圖片 360～520 px 的 JPEG。整頁控制在 16 MB 內（Artifact 圖片用 base64 內嵌的上限）。

### 4.7 建議做法（要改哪些程式）

| 檔案 | 改什麼 |
| --- | --- |
| `body_page.py` | 新增 `hands_section()`、`feet_section()`、`surface_section()`；讀 `checks.json` 的 `feet`、`fingerprint`、`v2ref`、`interpen`、`crease`，以及 `build.json` 的 `measure`；`--prev` 擴充到手腳近照；數字表加「上一版、變化」兩欄 |
| `hand_probe.py` | 加 `MODE=rom`（掃描條）、`MODE=seam`（接口）、雙手姿勢、補小指側與 45° |
| `foot_probe.py` | `POSES` 擴充；加 `MODE=sole`（離地上色）、`MODE=seam`；補後、上兩個角度 |
| 新增 `weight_probe.py` | 權重轉顏色屬性 → 發光材質 → 渲手、腳 |
| 新增 `surface_probe.py` | 第 1 節的 T1～T6 |
| 新增 `body_measure.py` | 第 3 節的量測；`body_build.py` 結尾呼叫，結果寫進 `build.json` |
| `SKILL.md` 第 6、7 步 | 加入這些程式的跑法 |

### 4.8 怎麼驗證

- 用現有的 `_tplF3.work` 產生一頁，確認每一區都有圖、有數字、沒有空區。
- 故意拿一個已知有問題的版本（例：`_box.work` 方塊手，比 YA 拇指壓進 2.73 mm）產生一頁，確認 H1 會亮紅、H4 那個手勢旁邊的數字會標出來。
- 新舊並排：拿 `_tplF3.work` 對 `_z45b.work`，確認同檔名的圖都有對到。

### 4.9 對服裝端、動畫端的影響

- **不影響產物**，只是審看頁變完整。
- 服裝端可以直接看 F9 的尺寸圖確認量的位置；動畫端可以看 H5、F5 的掃描條，知道手腳能彎到幾度。

### 4.10 優先順序

**P1。** 手腳模板目前「等使用者看外觀」，加了這兩區，使用者一次就能看完整。先做 H1、H2、H4、H5、H8、F1、F2、F4、F5、F9、F10（現有程式擴充就能做）；權重熱圖、線框、表面品質次之。

---

## 5. 總表

| 項目 | 建議做法 | 要改哪個檔 | 預估工時 | 風險 |
| --- | --- | --- | --- | --- |
| 1a 表面診斷 | 分階段拍照、截面量圓度（傅立葉）、曲率×半徑、法線差、斑馬紋、三角形長寬比 | 新增 `scripts/surface_probe.py`；`body_build.py` 加 `SURFDIAG=1` 存 4 個階段網格 | 0.5 天 | 低 |
| 1b Skin 細分 2 → 4 次 | 新參數 `SKINSUB` 預設 4；重校接口常數（手 `SHR` 0.906、腳 `SHR_X`／`SHR_Y` 0.92／0.91、脖子 ×1.19） | `body_build.py`（`skin_body`）、`hand_template.py`、`foot_template.py` | 0.5～1 天 | 低～中：常數沒重校，接縫會多一圈約 0.5 mm 台階 |
| 1c 粗體素、不減面 | 手腳模板開著時 `VOXEL` 約 3 mm、跳過 `DECIMATE`、平滑次數重調；`smooth_normals` 只留接口過渡帶 | `body_build.py`（`build_mesh`、`smooth_normals`）、`zepeto-body-v2.md` | 1 天 | 中：胯下、腋下窄縫可能被填（看 `basic` 檢查）；常數再校一次 |
| 1d 補強平滑（必要時） | 限定頂點群組的拉普拉斯，或 SDF Grid Mean | `body_build.py` | 0.5～1 天 | 中：真的形狀被抹糊、整體縮小 |
| 2 全身固定基礎網格 | 程式產生軀幹四肢籠子，接 5 個固定環；關節 3 條邊環；固定 UV；權重寫在籠子上 | 新增 `scripts/body_template.py`；`body_build.py` 大改；`body_checks.py`；服裝端驗證 `garment_lib.py` | 10～16 天＋審看 | 高：肩膀、胯下變形；外觀要重新認可；下游全部重跑；新娘 v3 被開場片 B 鎖定 |
| 3 交接尺寸 | `body_measure.py` 照 IBV／ISO 定義量約 20 個尺寸＋圍度曲線；地標寫成模板固定點號；寫 `build.json` 的 `measure`、`RELEASE.json`；出廠自動列出 ≥ 1 mm 或 ≥ 1% 的變化 | 新增 `scripts/body_measure.py`；`body_build.py`、`body_checks.py`、`body_status.py`、`hand_template.py`、`foot_template.py`；通知服裝端改 `garment_lib.py`（鞋帶、鞋口、褲腳） | 1.5～2 天 | 低。風險在服裝端要改寫死的數字 |
| 4 審看頁手腳兩區 | 手 8 小區、腳 10 小區、表面品質 1 小區；新舊同機位並排；數字表加上一版與變化 | `body_page.py`；`hand_probe.py`（`MODE=rom`／`seam`、雙手）；`foot_probe.py`（姿勢、`MODE=sole`／`seam`）；新增 `weight_probe.py` | 2～3 天 | 低：頁面變大（控制在 16 MB 內） |

建議順序：1a → 1b → 1c →（4 與 3 可並行）→ 出廠 →（看情況）1d → 2。

---

## 6. 查不到或不確定的地方

| 項目 | 狀況 |
| --- | --- |
| 直條紋的成因 | **推算，未實測**。原始碼確認 Skin 每節是 4 個角 [B1]，紋路寬度用 Skin 半徑推算，和「小腿最明顯、胸口有面感」吻合。要用 1.4 的 T1、T2 確認 |
| Skin 截面的官方說明 | 手冊只說輸出「大多是四邊形」[B2]，沒寫截面幾個角；4 個角是從原始碼看到的 |
| 細分 4 次後圍度變化 | 推算約 1% 以內；未實測 |
| EEVEE 有沒有像 Cycles「Geometry Offset」那樣的物件設定 | 沒查到 EEVEE 的官方手冊頁；只查到開發者的問題回報與修正討論 [B11] |
| QuadriFlow 在 Blender 5.2 的穩定性 | 舊版有開 seed 會當掉的回報 [B16]；新版沒查到 |
| Instant Meshes 的命令列參數、授權 | 網頁沒抓到原文；沒有確認 |
| SDF Grid 幾何節點 | 5.2 手冊有這些節點 [B7]；沒實測，也沒查到「縮小多少」的說明 |
| ZEPETO 官方身體的點數、UV | 查不到；指南只講邊環原則 [M1] |
| VRoid 身體是不是固定拓撲 | 官方查不到 |
| Ready Player Me 身材怎麼做（形態鍵或分開的網格） | 網站已關閉，取自搜尋摘要 [M4] |
| MetaHuman 參數化身體的內部做法 | 查不到細節 |
| Blender 官方基底網格的授權 | CG Channel 報導說 CC0（前一份報告）；官方開發者文件頁尾寫 CC-BY-SA（可能是指文件本身）[M11]。要用之前看下載包裡的授權檔 |
| ISO 8559-1、ISO 19408 原文 | 要付費，沒讀到。定義取自 IBV、Bodygram 的轉述 [F1][F2][F3]；腳踝圍在 IBV 是自訂的「內踝高度」定義 |
| 鞋楦要比腳大多少 | 沒有統一公式；各來源數字不同 [F6][F9][F10] |
| 腳跟到前掌長（heel-to-ball） | 鞋業常用詞，查不到正式定義；高跟鞋角度公式是本報告推導 |
| 審看網頁的業界格式 | 查不到正式標準；多數來源是廠商部落格、課程筆記、遊戲平台文件 |
| 工時 | 依現有程式規模粗估，沒算使用者審看等待時間 |

---

## 7. 來源表

### 表面（第 1 節）

- [B1] Blender 原始碼 `MOD_skin.cc`（`Frame` 結構：`co[4][3]`，每節 4 個角）：https://projects.blender.org/blender/blender/src/branch/main/source/blender/modifiers/intern/MOD_skin.cc
- [B2] Blender 手冊 Skin 修改器（輸出大多是四邊形；分叉點拓撲複雜、可能重疊；Branch Smoothing 會縮小）：https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/skin.html
- [B3] Blender 手冊 Remeshing（體素：不適合動畫角色、adaptivity > 0 會出現三角形；QuadriFlow：不適合變形角色的最終拓撲、不清互相穿插、seed 不同排法不同；重建只看原始網格資料）：https://docs.blender.org/manual/en/latest/modeling/meshes/retopology.html
- [B4] Nomad Sculpt 論壇：低面數模型體素重建後仍是一面一面的，先細分再重建：https://forum.nomadsculpt.com/t/faceted-after-voxel-remesh/2283
- [B5] Blender 手冊 Laplacian Smooth（次數、係數大時縮小明顯；保留體積；Normalized）：https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/laplacian_smooth.html
- [B6] Blender 手冊 Corrective Smooth：https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/corrective_smooth.html
- [B7] Blender 5.2 手冊 Volume 節點（SDF Grid Mean、SDF Grid Laplacian 等）：https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/volume/index.html ；SDF Grid Mean：https://docs.blender.org/manual/en/5.2/modeling/geometry_nodes/volume/operations/sdf_grid_mean.html ；Mesh to SDF Grid：https://docs.blender.org/manual/en/dev/modeling/geometry_nodes/mesh/operations/mesh_to_sdf_grid.html ；SDF Grid Laplacian API：https://docs.blender.org/api/5.0/bpy.types.GeometryNodeSDFGridLaplacian.html
- [B8] Taubin λ|μ 平滑（不縮小的平滑）：普林斯頓課程講義 https://www.cs.princeton.edu/courses/archive/spring20/cos426/c90694ca3bafb37f565db530c8a8278f/ImplicitFairing.pdf ；實作說明 https://ofb.net/~jtr/software/174c
- [B9] Heckbert & Garland 1999，減面誤差與曲率、三角形長寬比的理論：https://mgarland.org/papers/qtheory.pdf
- [B10] 細長三角形造成光影問題：減面指南 https://arxiv.org/pdf/2512.19959 ；Polycount https://polycount.com/discussion/232923/long-thin-triangles ；Blender 減面均勻度功能請求 https://lists.blender.org/pipermail/bf-funboard/2016-February/006415.html
- [B11] 陰影交界瑕疵：Cycles 修正 https://developer.blender.org/rB9c6a382 ；說明 https://developer.blender.org/T68920 ；EEVEE-Next 回報 https://projects.blender.org/blender/blender/issues/121194 ；EEVEE-Next 修正討論（剩下的瑕疵來自著色法線和幾何法線不一致）https://projects.blender.org/blender/blender/pulls/121088
- [B12] 斑馬紋判讀曲面連續：Rhino https://www.rhino3d.com/docs/guides/modeling/rhino-continuity-surfaces/ ；Rhino Zebra 指令 https://docs.mcneel.com/rhino/8/help/en-us/commands/zebra.htm ；Blender 斑馬 matcap 討論 https://devtalk.blender.org/t/call-for-content-matcaps/737?page=7
- [B13] Blender 手冊 Geometry 著色節點（Pointiness，只在 Cycles）：https://docs.blender.org/manual/en/latest/render/shader_nodes/input/geometry.html
- [B14] Shrinkwrap：Blender 4.1 手冊 https://docs.blender.org/manual/en/4.1/modeling/modifiers/deform/shrinkwrap.html ；重拓撲流程（Blender 3D Cookbook）https://www.oreilly.com/library/view/blender-3d-cookbook/9781783984886/OEBPS/ch04s04.html
- [B15] Instant Meshes：https://github.com/wjakob/instant-meshes
- [B16] QuadriFlow 問題回報：https://projects.blender.org/blender/blender/issues/70546 ；https://developer.blender.org/T70342
- [B17] 體素階梯：https://discourse.vtk.org/t/vtkmarchingcubes-vtkimagethreshold-generate-noticeable-staircase-like-textures/15525

### 固定基礎網格（第 2 節）

- [M1] ZEPETO Studio 指南 Modeling Applications（拓撲、手肘膝蓋肩膀 3 條邊環）：https://docs.zepeto.me/studio-guide/modeling-applications
- [M2] ZEPETO Studio 指南 Deformation Custom（移動骨頭改比例、scale 骨、頭手腳例外、全身 0.3～1.35）：https://docs.zepeto.me/studio-guide/deformation-custom
- [M3] ZEPETO Studio 指南 Rigging, Masking（照骨頭名字抄權重）：https://docs.zepeto.me/studio-guide/rigging-masking
- [M4] Ready Player Me 全身服裝（模板身體、保留 UV、三角形上限）：https://docs.readyplayer.me/ready-player-me/customizing-guides/create-custom-assets/create-custom-outfits ；身材功能部落格（網站已連不上，取自搜尋摘要）：https://readyplayer.me/blog/introducing-avatar-body-shape-customization
- [M5] MetaHuman Body Controls：https://dev.epicgames.com/documentation/metahuman/body-controls ；在 UE 建立 MetaHuman（Conform、相容模式 18 種體型）：https://dev.epicgames.com/documentation/unreal-engine/creating-your-metahuman-in-unreal-engine ；Body Conform Controls：https://dev.epicgames.com/documentation/metahuman/body-conform-controls
- [M6] MPFB 基底網格與輔助網格（點數固定、關節方塊、裙子輔助面）：https://static.makehumancommunity.org/mpfb/docs/assets/basemesh_and_helpers.html ；授權（核心素材 CC0）：https://static.makehumancommunity.org/mpfb/faq/can_i_sell_models.html
- [M7] SMPL：論文頁 https://is.mpg.de/publications/smpl-2015 ；Meshcapade Wiki https://meshcapade.wiki/SMPL ；MPI 講義 https://virtualhumans.mpi-inf.mpg.de/VH23/slides/pdf/Lecture_04_2_Vertex_Based%20Models.pdf
- [M8] Reallusion CC3+ 基底：https://manual.reallusion.com/Character-Creator-4/Content/ENU/4.0/05_Character/CC3-Plus-Characters.htm ；https://www.reallusion.com/Character-Creator/cc-avatar.html
- [M9] Daz 論壇：Adjust Rigging to Shape、ERC Freeze：https://www.daz3d.com/forums/discussion/comment/22067/
- [M10] Roblox 分層服裝規格（內外籠子、身體外籠子）：https://create.roblox.com/docs/avatar/layered-accessories/specifications ；籠子實務（模板、不要改籠子 UV）：https://create.roblox.com/docs/avatar/layered-accessories/caging-best-practices
- [M11] Blender 官方基底網格：https://developer.blender.org/docs/features/asset_system/asset_bundles/human_base_meshes/ ；3.6 版說明（四邊形、封閉、有 UV）：https://developer.blender.org/docs/release_notes/3.6/asset_bundles/ ；CG Channel：https://www.cgchannel.com/2023/06/download-blender-studios-free-human-base-meshes
- [M12] Blender 手冊 Apply Pose as Rest Pose：https://docs.blender.org/manual/en/5.3/animation/armatures/posing/editing/apply.html
- [M13] VRoid 第三方身形工具（廠商說法）：https://booth.pm/ja/items/8506445
- [M14] CLO 人台尺寸：https://support.clo3d.com/hc/en-us/articles/360013257553

### 尺寸（第 3 節）

- [F1] IBV 腳部量測目錄（腳軸、腳長、腳掌圍、腳背圍、腳跟寬 16%、腳趾圍凸包等，附 ISO 條號）：https://personales.upv.es/alrego/Feet/Feet_DigitalMeasuringTape.html
- [F2] IBV 身體量測目錄（手腕圍、腳踝圍、最小腿圍、前臂圍、上臂圍、膝圍、脖子圍，附 ISO 條號）：https://services.ibv.org/3dmodel/doc/DigitalMeasuringTape_3dModel.html
- [F3] Bodygram 量測定義（ISO 8559-1 條號：手腕圍 5.3.19、小腿圍 5.3.24、大腿圍 5.3.20、外踝高 5.1.17、脖子根圍 5.3.3）：https://docs.bodygram.com/platform/measurement-definitions
- [F4] ISO 8559-1:2017：https://www.iso.org/standard/61686.html
- [F5] ISO 19408:2023 鞋類尺碼詞彙：https://www.iso.org/standard/83107.html
- [F6] Shoemakers Academy 鞋楦各部位與量法：https://shoemakersacademy.com/shoe-last/ ；腳掌圍：https://shoemakersacademy.com/glossary/ball-girth/
- [F7] 鞋楦專利（腳掌圍、腳背圍、腰圍、短跟圍定義）：https://patents.justia.com/patent/5661864
- [F8] 3D 腳掃描與手量比較研究（Elinvision 3DST）：https://pmc.ncbi.nlm.nih.gov/articles/PMC12309729/
- [F9] 高跟鞋專利（鞋頭翹度、跟高）：https://patents.google.com/patent/US20160051007A1/en
- [F10] 參數化鞋楦社群模型（鞋楦長 ≈ 腳長 + 11.5 mm，僅供參考）：https://makerworld.com/models/2510243
- [F11] 台灣鞋楦設計研究（腳長、腳掌圍是主要因素）：https://ir.lib.nycu.edu.tw/handle/11536/30955?locale=en

### 審看（第 4 節）

- [R1] Roblox：在 Blender 測試角色身體（轉骨頭看自然姿勢、檢查清單）：https://create.roblox.com/docs/avatar/character-bodies/test-blender
- [R2] Roblox Calisthenics 工具（走、跑、移動、待機循環）：https://create.roblox.com/docs/art/modeling/calisthenics-tool
- [R3] Blender Studio 動畫測試（壓力測試、回饋迴圈）：https://studio.blender.org/tools/artist-guide/asset-creation/animation-testing
- [R4] 轉檯、素模、線框：https://3d.irpr.agency/glossary/turntable/ ；https://3d.irpr.agency/glossary/wireframe/ ；課程筆記 https://media.confetti.ac.uk/tsvetinad-xs20-yr2/?p=1101
- [R5] 華盛頓大學 CSE490J 姿勢測試作業（肩膀舉起時胸口鼓包）：https://courses.cs.washington.edu/courses/cse490j/21su/assignments/assignment_4/Character%20assignment%204%20-%20gray%20model%20pose%20test.pdf
- [R6] 綁定與權重檢查清單（廠商頁面，參考就好）：https://www.seeles.ai/features/tools/dcc-rigging-skinning-weights-checklist
- [R7] Blender 零權重顯示：https://projects.blender.org/blender/blender/issues/72552
- 手腳測試姿勢、真人關節活動範圍：見 `research-hands-feet.md` 第 3 節與其來源表 [R1]～[R5]
