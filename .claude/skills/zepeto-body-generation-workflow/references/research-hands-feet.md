# 雙手與雙腳：怎麼檢驗、怎麼調整（研究報告，2026-10-14）

> 使用者原話：「需要另開研究技術，如何檢驗與調整雙手與雙腳」。
> 研究方式：只讀專案程式與舊的檢查紀錄、上網查資料。**沒有改任何程式、沒有跑 Blender。**
> 讀過的程式與資料：`scripts/body_build.py`（`skin_body`、`finger_bm`、`box_hand`、`hands_feet`、`build_mesh`、`bind`、`fit_neck_ring`）、`scripts/body_checks.py`、`scripts/hand_probe.py`、`references/checklist.md`、`references/zepeto-body-v2.md`；`D:/render-work/zepeto-body/build/` 底下各版的 `checks.json`、`build.json`、`_sw_*/chk.log`（只讀）；先前的 ZEPETO 身體研究頁、頭身接縫研究 `zepeto-face-rig/references/research-head-body-seam.md`。
> 文中 `[代號]` 對應文末來源表。標「推測」的是還沒實測的判斷。

---

## 結論（先看這段）

**一句話：業界讓手腳「好看又穩定」的共同做法，是「固定的網格模板＋固定的權重」，不是每次從圓管、圓球融出來再自動算。我們推薦把手和腳改成程式產生的固定模板（延伸已經試做的方塊手），在前臂中段、小腿中段用接口環接回身體（跟頭身 48 點接口環同一套思路）。動工之前，先花約 1 天修好量測程式，因為數字跳動有一部分是量測本身造成的。**

### 七個重點

1. **手的造型為什麼「修一處壞一處」**
   - 現在手的形狀，是幾十個膠囊、橢球的交界決定的。例如「手指根部像 L 形直角」，其實就是掌心橢球和手指膠囊相交的那條線。
   - 這些形狀再經過體素融合、平滑、減面，沒有任何一條邊是「設計」出來的。所以只能再加一塊形狀去補，補丁之間又互相影響。
   - 業界控制手的形狀，靠的是**邊環（一圈一圈的邊）怎麼走**：每個關節 3 圈、手指 6～8 邊、掌緣一條連續的邊從手腕走到小指根 [T1][T2][T4]。

2. **檢查數字為什麼跳，有兩個原因**
   - **(a) 網格真的變了**：減面是全身一起排順序、自動權重是對整塊網格解方程式。腳一改，手的點和權重就跟著變。之前試過「手分開減面」（`HANDKEEP`），紀錄寫「試了無效（權重仍受全身影響）」，也符合這個推論。
   - **(b) 量測本身在跳（這次查到的新發現）**：舊試做留下的 4 份紀錄（`_sw_*/chk.log`）裡，同一個握拳姿勢、參數只差一點，量到的 4～6 mm 擠壓被分到不同類別。有時算「關節內側擠壓」，有時算「指尖插進掌心」或「手指互相穿插」，有時乾脆量到 0。詳見 1.2 節。
   - 所以「±1 mm 跳動」甚至「0 和 5 mm 之間跳」，不全是網格真的變了。

3. **業界的手腳是不是獨立做、重複用？是，而且拓撲幾乎都固定。**
   - 建模階段常把手、腳另外做好，再在手腕對齊邊環接上 [T1]。Blender 官方免費的基底網格（CC0）就有獨立的手、腳 [S1][S2]。
   - 成品多半是一整塊**固定拓撲**的網格，換角色只換形狀或骨頭比例。ZEPETO、VRoid、MetaHuman、MakeHuman 都是這樣 [S4][S7][S13]。
   - Roblox 更直接：手、腳本來就是獨立的網格部件 [S3]。
   - **ZEPETO 改手腳大小是縮放手、腳的骨頭**（官方特例），衣服的權重是從官方基底身體「照骨頭名字抄」過來的 [S4][S6]。

4. **怎麼檢驗**
   - 業界的標準做法，是做一段「關節活動範圍測試動畫」加一組手勢，然後看近照 [R6][R7][R8]。
   - **公開資料裡查不到**遊戲或動畫公司的「自動化量化檢查」流程。
   - 可以用 Blender Python 自動化的項目：截面積保留、三角形互相穿插（`BVHTree.overlap`）[R11]、權重（每點幾根骨頭、總和、有沒有串到隔壁手指、過渡寬度）、翻面或壓扁的面、腳底貼地、結構指紋（同樣的輸入要長出一模一樣的手）。

5. **怎麼調整**
   - **權重**：拓撲固定時，最穩的是「照點號抄模板權重」或「照位置直接算」。Blender 的自動權重（bone heat）在手指常常串到隔壁手指，官方手冊、論壇、外掛廠商都提過 [W1][W4][W5]。
   - **變形**：
     - 「保留體積」（Preserve Volume）會鼓脹 [D1][D2]。我們彎曲檢查最大值 1.08～1.19，就是鼓起來。
     - Corrective Smooth 是 Blender 版的 Delta Mush，可以只套在手腳上修摺痕 [D4][D5]。
     - 修正形態鍵（用 rotational difference 驅動）適合指根、腳背的摺痕 [D6][D7][D8]。拓撲固定之後可以做一次、重複用。
     - 輔助扭轉骨等到手腕扭轉真的出問題再加 [D10]。

6. **推薦方案 A：「手腳固定模板＋前臂、小腿接口環」**
   - 做法：
     - 手、腳用程式產生，每次長出一樣的四邊形網格，**不經過體素融合、不經過減面**。
     - 權重照位置直接算。
     - 在前臂中段、小腿中段用接口環接回身體。接縫位置放在只跟一根骨頭動的地方，所以永遠不會裂開。
   - 效果：改腳、腿、軀幹，手的網格與權重**完全不變**，可以用「指紋檢查」證明。
   - 工作量約 5～8 個工作天，含 1～2 輪使用者審看。
   - 三個方案比較見第 6 節。

7. **不論選哪個方案，第 0 步先修量測（約 1 天）**
   - 部位改用「靜止姿勢下的位置」來標記，不再看「最大權重是哪根骨頭」。
   - 排除「同一塊皮膚」改看網格上相連的距離，不再用 6 mm 直線距離。
   - 角度改成逐步掃描。
   - 修好後，用現有的新郎、新娘、方塊手版本重量一次，才知道真正的數字。

### 三個方案一覽

| | A 手腳固定模板＋接口環（推薦） | B 最小改動：隔離手腳＋修量測 | C 整身固定拓撲基底網格 |
| --- | --- | --- | --- |
| 一句話 | 手腳改成程式長出的固定網格，接到體素融合的軀幹 | 手腳照舊用形狀拼、但自己單獨融合與綁骨，再接回身體 | 像 ZEPETO 一樣，全身一塊固定網格，換人只換比例 |
| 造型問題（L 形、指蹼、掌緣） | **解決**（邊環走向直接決定形狀） | 沒解決（仍是拼接） | 解決 |
| 數字穩定 | **解決**（指紋可驗證） | 大致解決 | 解決 |
| 工作量 | 5～8 天 | 2～3 天 | 2～3 週以上 |
| 影響服裝、動畫 | 手腳網格換新，鞋子、袖口要重長一次 | 小 | 全部重做 |

---

## 先解釋幾個會一直出現的詞

| 詞 | 白話 |
| --- | --- |
| 拓撲 | 網格的「點怎麼連成面」。固定拓撲＝點數、點的編號、誰連誰都固定，只有位置可以變 |
| 邊環（edge loop） | 網格上首尾相接繞一圈的一串邊。手指上就是一圈一圈的「環」 |
| 籠子（cage） | 細分之前的粗網格。方塊建模先做籠子，再細分變圓滑 |
| 權重 | 每個點跟哪根骨頭動、跟多少 |
| 自動權重（bone heat） | Blender 的「With Automatic Weights」：用熱擴散自動算權重 [W1][W2] |
| ROM 測試 | Range of Motion，關節活動範圍測試：把每個關節從 0 彎到極限，看網格會不會壞 |
| LBS／DQS | 兩種骨骼變形算法。LBS 是一般線性混合，彎到底會塌陷；DQS 是對偶四元數，Blender 叫 Preserve Volume，不塌但會鼓脹 [D2][D3] |
| 修正形態鍵 | 關節彎到某角度時，自動疊上一個事先做好的形狀來修摺痕 |
| 接口環 | 兩塊網格約好的一圈點，點數、順序、位置一樣，接起來就看不到縫（頭身已經用 48 點環做到距離 0） |
| 指紋 | 把手的所有點座標和權重算成一個雜湊值。同樣的參數要得到同樣的指紋，才算「可重現」 |

---

## 1. 現況診斷

### 1.1 造型：為什麼一直在補

| 使用者指出的問題 | 在現在程式裡是怎麼來的 | 為什麼補丁會互相干擾 |
| --- | --- | --- |
| 手指根部像 L 形直角 | 掌心橢球（`PALMW`）、指根條（`KBW`）、手指膠囊三塊的交界 | 加寬掌心，外側指根被包住，但手掌輪廓也跟著變 |
| 手背、掌緣不自然 | 掌緣是橢球的邊；加 `EDGERAIL` 膠囊讓它變直，結果手背跟著變直、延伸到後面 | 放手心側，彎下來的指尖、拇指又會壓進去（穿插 3.4～4.7 mm） |
| 指蹼 | 手指之間的縫比 2 格體素窄就被填平（`VOXEL` 從 2.2 mm 降到 1.2 mm 才改善） | 體素越小，面越多，減面越重 |
| 腳趾（新加的） | 五根膠囊，趾縫約 1 mm，體素後黏在一起留淺溝 | 骨架只有一根 `ToeBase`，五根腳趾只能一起彎（見 1.3） |

方塊手（`box_hand`）方向是對的：手指從手掌的四個端面一節一節擠出來，手指和手掌本來就是同一塊，沒有拼接轉角。所以使用者說「外觀好很多」。

但目前它還是會和身體一起體素融合、一起減面、一起自動權重。拇指與拇指根肉墊也還是膠囊、橢球，靠體素黏上去。所以它的檢查數字一樣在跳。

### 1.2 數字跳：網格在變，量測也在變

**(a) 全身一起做的步驟**

| 步驟 | 為什麼腳一改、手就變 | 依據 |
| --- | --- | --- |
| Decimate 減面（全身 9%） | 減面是整塊網格一起排「先收哪條邊」。總面數一變，手被收掉哪些邊就變 | 官方手冊：Collapse 是「逐步合併頂點」、比例是對整個網格算 [D13] |
| 自動權重 | 每根骨頭對整塊連通的網格解一次熱擴散方程式。點的數量、順序一變，結果就有細微差異（推測） | Blender 的實作來自 Baran & Popović 2007，先算初值再擴散平滑 [W2] |
| Smart UV 展開 | UV 島是全身一起排版，手的 UV 位置會隨別處改變（推測；影響布紋，不影響形狀） | — |
| 體素重建＋Laplacian 平滑 | 這兩步應該是局部的（推測，體素格子對齊物件原點）。手腕附近會受前臂粗細影響 | 未實測 |

`HANDKEEP` 只把「減面」分開，自動權重仍是全身一起，所以沒效。紀錄寫的是「試了無效（權重仍受全身影響）」。

**(b) 量測本身的不穩：從舊紀錄看到的證據**

下面是 `D:/render-work/zepeto-body/build/_sw_*/chk.log` 的 `DIAG` 行（`body_checks.py -- DIAG=1` 印的分類）。四個版本只差一點參數，只列有數字的姿勢：

| 版本 | 握拳 fist | 比讚 thumbs_up | 四指彎 90° curl90 | 其他 |
| --- | --- | --- | --- | --- |
| `_sw_0.6_0.08` | 0 | thumb_on_finger **5.43** | 0 | — |
| `_sw_0.6_0.15` | 0 | 0 | 0 | hold crease 6.03、fork_grip crease 6.21 |
| `_sw_0.7_0.08` | tip_in_palm **5.76** | crease 4.42 | crease 6.06、tip_in_palm 3.0 | peace crease 2.38 |
| `_sw_0.7_0.15` | crease 4.3、finger_finger **5.16** | finger_finger 5.09 | tip_in_palm 3.0、finger_finger 5.16 | cup crease 5.92 |

看得出來，**同樣大小（4～6 mm）的擠壓，一下被算成「關節內側擠壓」（標準 ≤ 4.64 mm），一下被算成「不同部位穿插」（標準 ≤ 1 mm），一下又完全沒量到。** 從 `body_checks.py` 的 `penetration()` 找到三個原因：

1. **部位分類靠「最大權重是哪根骨頭」**（`main_bone`）。
   - 指根摺痕兩側，一邊是手掌（`Hand`）、一邊是第一節（`Index1`），程式把它歸成 `tip_in_palm`，也就是「指尖插進掌心」，但它其實是指根的關節內側擠壓。
   - 權重稍微一變，同一個點最大的骨頭就換人，類別跟著換。
2. **「同一塊皮膚」用「靜止時 6 mm 內」判斷**。
   - 手指半徑 5.8 mm，指根摺痕兩側在靜止時的直線距離大約就在 6 mm 上下。
   - 網格稍微一變，同一處擠壓就在「排除」和「算進去」之間跳。
3. **先射線、再找最近表面，兩步都是有或沒有。**
   - 只要射線沒打到（12 mm 內），這點就不算。所以數字常在 0 和 5 mm 之間跳，而不是連續變化。

**會怎樣**：

- 出廠閘門擋下的版本，可能只是量測分類換了，手其實沒變差。
- 反過來，真正的穿插也可能被「排除」掉。
- 只要量測不穩，造型怎麼改都看不出有沒有變好。

所以第 6 節的每個方案，**第 0 步都是先修量測**。

### 1.3 腳

- 骨架只有 `J_Bip_*_Foot` 和 `J_Bip_*_ToeBase` 兩根。Mixamo 也一樣，只有一根腳趾骨；VRM 規格裡腳趾也只有 `toes` 一根 [S10]。**五根腳趾不可能各自動**，只會跟 `ToeBase` 一起彎。
- 所以腳趾分得多開沒有動畫上的意義，只影響光腳時的外觀。分太開反而讓 `ToeBase` 的權重更難分（推測）。
- 穿鞋時，腳被鞋子蓋住；服裝產線本來就會藏住被蓋住的身體。腳的細節只在光腳鏡頭才看得到。
- 目前腳**完全沒有檢查**。

---

## 2. 業界怎麼做手和腳

### 2.1 手腳是不是獨立建模、重複使用

| 系統 | 手腳和身體的關係 | 換角色時手腳怎麼變 | 權重怎麼來 |
| --- | --- | --- | --- |
| **ZEPETO**（官方創作者指南） | 官方基底檔 `creatorBaseSet`：骨架＋一塊遮罩身體 [S5] | 改骨頭：一般骨頭只能縮放專用的 scale 骨，**頭、手、腳骨頭是例外，可以直接縮放**；全身縮放 0.3～1.35 [S4] | 衣服綁骨時，從基底身體 Transfer Weights，**照骨頭名字抄** [S6] |
| **VRoid** | Body、Face、Hair 三塊，手腳在 Body 裡 [S14] | 滑桿調形狀（官方沒寫網格是否固定拓撲，推測固定） | 內建 |
| **MetaHuman**（Epic） | 頭、身體兩塊；身體所有輸入「必須是標準 MetaHuman 拓撲」 [S7] | 標準拓撲＋比例；核心骨架涵蓋手、腳 [S7] | 自動配合；另有「輔助關節」保持體積，由 RBF 解算器驅動 [S7][S8] |
| **MakeHuman** | 一塊基底網格 hm08 含全身 [S13] | 形態目標（morph）改形狀，拓撲不變 | 固定 |
| **Roblox**（R15） | **15 塊獨立網格**，左右手、左右腳各自一塊；每塊要封口、水密 [S3] | 換整塊部件 | 每點最多 4 根骨頭；手指骨頭是選配（進階 R15）[S3] |
| **Ready Player Me** | 半身 VR 版有獨立的手網格 `Wolf3D_Hands`；全身版手在身體裡 [S11] | 模板 | 骨架接近 WebXR 手部追蹤，缺掌骨（社群說法）[S11]。官網已停止服務，資料取自索引 |
| **Mixamo 自動綁骨** | 使用者上傳的一塊網格 | — | 自動；手指靠太近會少長骨頭，要先把手指拉開 [S12] |
| **Blender 官方基底網格**（2023，CC0） | 17 個網格，**手、腳、頭都有獨立一份**，全是四邊形、有 UV [S1][S2] | 拿來雕刻、修改 | 不含骨架（查到的資料沒提） |
| **建模教學（華盛頓大學 CSE458）** | 手另外做：方塊手掌 → 切指根 → 擠出手指 → 複製手指 → **手腕上下的點要一一對齊** → 擠出接到手臂 [T1] | — | — |

**歸納**：

- 「手腳獨立建模、可重複使用」在**建模階段**很常見，例如 Blender 基底網格、市售手腳基底庫、教學流程。
- 到了**成品**，幾乎都是**固定拓撲**：
  - 不是整身一塊模板（ZEPETO、VRoid、MetaHuman、MakeHuman），
  - 就是手腳本身是固定部件（Roblox）。
- **沒有一個系統是「每次從基本形狀融出來、再自動算權重」。** 我們現在的做法在業界找不到同類。

### 2.2 拓撲（邊環怎麼走）的規則

這些多半來自論壇、教學。沒有一份「官方標準」，但說法一致。

| 部位 | 規則 | 來源 |
| --- | --- | --- |
| 手指截面 | 6 或 8 邊的圓柱；教學把每根手指做成 8 邊再接到手掌 | [T2][T1] |
| 指關節 | **每個關節 3 圈邊環**：中間那圈兩根骨頭分，兩側各給最近的骨頭（自動權重才分得乾淨） | [T2][T4] |
| 不彎的地方 | 指節中段、掌心中間可以稀疏，順著骨頭直線走 | [T2][T7] |
| 指根（掌指關節） | 指根要排成一條弧，位置比想像中高（偏向手背） | [T3] |
| 五極點 | 指根附近不要有 6 條邊交會的點，彎起來會擠出尖角；手掌的極點越少越不容易凹凸 | [T6] |
| 手掌 | 分成拇指根肉墊、食指根、四指根肉墊、掌根幾區，各自微鼓，中間是摺痕；指根要有足夠的邊才控制得住彎曲 | [T5] |
| 拇指 | 從手掌靠手腕的側邊擠出 3 次，先做成和四指 90°，再調到約 45° | [T1] |
| 手腕 | 往手腕方向漸少；上面每個點都要對到下面一個點 | [T1] |
| 極點位置（全身通則） | 全四邊形、面大小均勻；極點不要放在摺痕和大彎曲處 | [T9] |
| 手肘、膝蓋（可類比到腳踝） | 關節內側多一兩條邊收攏，對關節位置比較寬容 | [T11] |
| 腳 | 腳踝、腳掌前端（球部）、每根腳趾周圍要有一圈一圈的邊環；足弓、腳跟要有足夠的邊撐形 | [T8]（部落格，參考就好） |
| 測試 | 擺 T 字好看的拓撲，握拳時可能塌陷或出尖角，**一定要測握拳** | [T7] |

**跟我們的關係**：

- 方塊手已經有「指根四段 → 擠出手指」。
- 但目前每個關節只有 1 圈籠子環，加上中段環。細分後環很多，但**彎曲區沒有被明確定義**。
- 掌緣也還沒有一條「從手腕直走到小指根」的連續邊。
- 第 6 節的方案 A 會把這些規則寫成產生器的固定規格。

### 2.3 建模姿勢：業界說「半彎」，我們要「全直」

- 業界常建議手以「放鬆、手指微彎」的姿勢建模，因為那是握拳和全張開的中間點，兩邊都比較好變形 [T10]。
- **我們不能照做**：出廠檢查要求靜止手指方向和 Mixamo 差 ≤ 3°（`rest_fingers`），四指要併攏平行，這是 v8 的教訓（張成扇形會讓動畫變耙子）。
- 折衷：靜止姿勢保持全直，但**邊環照「會彎到 90° 以上」來配置**，再用 ROM 掃描驗證。

---

## 3. 怎麼檢驗手和腳

### 3.1 要測哪些姿勢

先列真人的關節活動範圍，再定「我們要測到多少」。卡通角色不一定要做到真人極限，但**動畫用得到的範圍要再多留一點**。

**真人參考值**

| 關節 | 真人範圍 | 來源 |
| --- | --- | --- |
| 指根（MCP）彎曲 | 約 84～90° | [R1][R2] |
| 中節（PIP）彎曲 | 約 92～100°（部分研究到 107°） | [R1][R2] |
| 末節（DIP）彎曲 | 約 80～85° | [R1][R2] |
| 指根往手背翹 | 約 −20°（Kapandji 類型的表） | [R2] 搜尋摘要 |
| 拇指根（CMC）往掌心張／往側邊張 | 約 45°／60° | [R1] |
| 腳踝往上（背屈） | 10～20°（走路至少 10°） | [R3][R5] |
| 腳踝往下（蹠屈） | 約 45～50° | [R3][R5] |
| 大拇趾往上翹 | 走路需要約 65°，一般 70～90° | [R4] |

**手的測試姿勢集（建議）**

| 類別 | 姿勢 | 為什麼 |
| --- | --- | --- |
| 靜止 | T 字靜止 | 基準、指紋 |
| 共用手勢（現有） | peace、fist、thumbs_up、grip、hold、fork_grip、relaxed、cup、flat | 動畫真的會用 |
| **單關節掃描（新）** | 每根手指 MCP 0→90°、PIP 0→100°、DIP 0→80°，每 15° 一格；先一根一根、再四指一起 | 找出「從幾度開始壞」，比只看 60°、90° 兩點穩 |
| **張合（新）** | 四指張開（食指 −15°、中指 0、無名指 +10°、小指 +20°）、四指併攏、指根往手背翹 −20° | 指縫、指蹼、掌緣 |
| **拇指（新）** | 拇指往掌心 45°、往側邊 60°；拇指尖碰食指尖（OK 手勢）、碰小指根（對掌） | 虎口深淺、拇指根肉墊 |
| **手腕（新）** | 往掌心彎 70°、往手背 60°、往拇指側 20°、往小指側 30°、手掌繞前臂扭 ±80° | 手腕塌陷、扭轉時的「糖果紙」扭曲 [D10] |
| **雙手（新）** | 雙手合十（兩掌貼合）、拍手、雙手交握 | 使用者點名的手勢；左右手互相穿插 |
| Mixamo 抽格（現有＋擴充） | 揮手、拍手、拿東西、比讚等動作裡手最彎的那一格 | 實際動畫 |

**腳的測試姿勢集（建議）**

| 類別 | 姿勢 | 為什麼 |
| --- | --- | --- |
| 靜止 | T 字靜止、站立（Mixamo idle 第 0 格） | 指紋、腳底貼地 |
| 腳踝 | 往上 20°、30°（蹲、跪）；往下 45°、50°；往內 20°、往外 15° | 腳背摺痕、腳跟、腳踝前側塌陷 |
| 腳趾 | `ToeBase` 往上 60°、70°（墊腳、走路蹬地）；往下 30° | 腳趾上方摺痕、腳趾壓進前腳掌 |
| 組合 | 墊腳尖（腳踝往下 45°＋腳趾往上 60°）、跪姿腳趾撐地（腳趾往上約 90°） | 最極端的組合 |
| 雙腳 | 併腳站、交叉站 | 左右腳互相穿插 |
| Mixamo 抽格 | 走路蹬地那一格、跑步、蹲、跪、盤腿坐 | 實際動畫 |

業界也有現成的 ROM 測試動作檔可參考（例：一個 1053 格、含手指的動作捕捉 ROM 包，CC BY-NC 不可商用）[R7]；手部綁骨商品也常附「握拳、張開、範圍測試」分段動作 [R8]。我們的骨架和 Mixamo 對得上，**直接用程式產生掃描姿勢最簡單**，不必下載。

### 3.2 量化指標

學界的自動綁骨論文多半用「權重和正解差多少」打分。但有論文指出這種分數反映不了動起來的品質 [R12]，所以下面以「動起來量得到的東西」為主。

| 指標 | 量什麼、怎麼算 | Blender Python 做得到嗎 | 我們現在有沒有 |
| --- | --- | --- | --- |
| **截面積保留** | 關節中間（兩節骨頭夾角的平分面）切一刀，算切口面積：彎曲後 ÷ 靜止。< 1 是塌、> 1 是鼓 | 可以：`bmesh.ops.bisect_plane` 或自己算網格和平面的交線多邊形面積 | 現在是「沿一個方向射兩條線量厚度」（`bend`），只看一個方向、容易受單點影響 |
| **部位之間穿插深度** | 不同部位（手指對手指、指尖對掌心、拇指對手指、左右手）互相陷進去多深 | 可以：`BVHTree.find_nearest_range`、射線 [R11] | 有（`interpen`），但分類方法不穩（1.2 節） |
| **三角形交叉數** | 變形後有幾對三角形真的相交（不是靠近，是穿過） | 可以：`BVHTree.overlap()` 回傳相交的面編號對 [R11]；排除共用頂點的相鄰面 | 沒有 |
| **關節內側擠壓深度** | 同一根手指相鄰兩節在摺痕處皮膚擠進去多深 | 可以 | 有（`crease`） |
| **權重：每點骨頭數、總和** | 每點最多幾根骨頭有權重（建議 ≤ 4，和 Roblox 等引擎一致 [S3]）、總和 = 1 | 可以 | 只查「有沒有沒綁到的點」 |
| **權重：串到隔壁手指** | 標記為食指的點，對中指骨頭的權重 > 0.01 就算污染 | 可以（要先有「部位標記」） | 沒有 |
| **權重過渡寬度** | 關節處權重從 0.1 到 0.9 跨多寬 ÷ 手指直徑 | 可以 | 有（`weight_trans`，0.6～1.2 倍） |
| **翻面、壓扁的面** | 變形後面的方向和靜止時（跟著骨頭轉過去）相反＝翻面；面積 ÷ 靜止面積 < 0.3＝壓扁 | 可以 | 沒有 |
| **腳底貼地** | 站立時，腳跟區、前腳掌區最低點離地 ≤ 2 mm；沒有點低於地面 1 mm 以上；足弓內側離地 ≥ 3 mm | 可以 | 沒有 |
| **接觸距離（手勢）** | 比讚拇指貼食指、握拳指尖貼掌心：目標 0～1 mm（貼住但不陷進去） | 可以 | 部分（`thumb_contact` 是用掃描調出來的） |
| **結構指紋** | 手（或腳）的點座標四捨五入到 0.01 mm、權重四捨五入到 0.001，算 sha256 | 可以 | 沒有 |
| **套 Mixamo 方向** | 同一格動作，手指方向和 Mixamo 原樣差幾度 | 可以 | 有（`retarget`、`rest_fingers`） |

### 3.3 工具

| 工具 | 用途 | 適用性 |
| --- | --- | --- |
| Blender `mathutils.bvhtree`（`FromObject(deform=True)`、`overlap`、`find_nearest_range`、`ray_cast`）[R11] | 變形後網格的穿插、距離 | **主力**，背景 Blender 可跑 |
| Blender Mesh Analysis 疊加顯示（Intersect、Thickness、Distortion）[R9] | 編輯模式下把相交、太薄、扭曲的面上色 | 目視輔助；手冊說只在有變形修改器時顯示，高面數會慢 |
| 3D Print Toolbox（Intersections、Thickness、Distorted）[R10] | 找出相交面、太薄的面 | 拿來當第二意見；本來是給 3D 列印用 |
| Maya「Skinning a hand」教學 [R6] | 拇指靠向食指時，用影響物件＋驅動鍵讓虎口肌肉鼓起 | 觀念參考：手的修正多半綁在拇指、指根 |
| Maya Geodesic Voxel Binding [W6] | 對有破洞、相交、多塊的網格也能算出平順權重 | 我們用不到 Maya；說明「體素式算權重」是業界做法之一 |
| 遊戲引擎的手部 QA | — | **查不到**公開的自動化流程（見第 7 節） |

---

## 4. 怎麼調整

### 4.1 權重

| 做法 | 是什麼 | 優點 | 缺點、坑 | 適合我們的手指、腳趾嗎 |
| --- | --- | --- | --- | --- |
| **自動權重（bone heat，現在用的）** | Blender 依骨頭到點的距離＋熱擴散算權重 [W1][W2] | 一鍵 | 手冊：「重疊處決定哪根骨頭影響哪些點時會出問題」，常要手修 [W1]；網格不乾淨時會整個失敗 [W3]；手指靠太近時權重串到隔壁手指 [W4]；全身一起算，結果隨別處改變 | 不適合當最終權重；可以當對照 |
| 體素熱擴散（Voxel Heat Diffuse Skinning 外掛） | 先體素化再擴散 | 對破洞、相交的網格比較強 | 評論與廠商都說手指、嘴巴容易黏在一起，**手指腳趾建議改用表面熱擴散** [W5] | 不適合 |
| 測地線體素（Maya Geodesic Voxel） | 依體素內的測地距離算權重 [W6] | 對雜亂網格很穩 | 只有 Maya | 不適用 |
| **Data Transfer 從模板抄**（Blender 修改器） | 從另一塊網格依最近面內插（`POLYINTERP_NEAREST`）抄權重（`VGROUP_WEIGHTS`）[W7] | 形狀不同也能抄；ZEPETO 衣服就是這樣綁（Transfer Weights）[S6] | 形狀差很多時，抄到的權重會錯；要先「Generate Data Layers」建好群組 [W7] | 換角色時好用 |
| 穩健權重轉移（Robust Skin Weights Transfer） | Epic 的論文（SIGGRAPH Asia 2023）：先只抄「有把握的點」，其他點用內插補 [W8] | 形狀差很多時比一般轉移好；有 Blender 外掛（第三方） | 第三方外掛、要另外裝 | 備用（模板形狀差很多時） |
| **照點號抄模板權重** | 拓撲固定時，第 i 個點直接拿模板第 i 個點的權重 | **完全穩定、零誤差** | 前提是拓撲固定 | **最適合（方案 A、C）** |
| **照位置直接算（解析權重）** | 每個點知道自己在哪一節、離關節多遠，用平滑曲線算出兩根骨頭的比例 | 完全可控；過渡寬度直接等於設定值 | 要自己寫；手掌、拇指根這種多骨頭交會處要特別處理 | **最適合（方案 A）**；這是本報告的建議，不是查到的業界標準 |
| 手刷 | 人工刷權重 | 最精細 | 不能自動化、不可重現 | 只在模板上刷一次（方案 C） |

另外兩個細節：

- **排除不該參與的骨頭**：把骨頭的 Deform 關掉，它就不參與自動權重 [W9]。方案 A 綁軀幹時，要先關掉手指、腳趾骨頭的 Deform，避免前臂末端被分到手的權重；綁完再打開。
- **Mixamo 自動綁骨的經驗**也指向同一件事：手指靠太近，連骨頭都會長錯；要先把手指拉開 [S12]。

### 4.2 變形方法

| 方法 | 原理 | 對手指、腳趾的效果 | 自動化 | 建議 |
| --- | --- | --- | --- | --- |
| LBS（一般線性混合） | 權重混合骨頭的變換 | 彎到底會塌（指節內側陷下去） | Blender 預設 | 底子 |
| **Preserve Volume（DQS，現在手上疊的）** | 用四元數混合 [D1] | 不塌，但**彎曲時會鼓**（Kavan 的論文與教材都提到）[D2]；接近 180° 有不連續 [D1] | 已做（`HAND_DQS` 群組＋第二個 Armature 修改器） | 我們彎曲最大值 1.08～1.19（方塊手 1.186 超過 1.15）就是鼓。要和下面兩個比較再決定 |
| 最佳化旋轉中心（Optimized CoR） | 每點預先算旋轉中心，同時減少 LBS 塌陷和 DQS 鼓脹 [D3] | 論文說兩種毛病都減輕 | Blender 沒有內建 | 不建議（要自己寫變形器） |
| **Corrective Smooth（Blender 版 Delta Mush）** | 先平滑變形、再把靜止時的細節加回來 [D4]；Rhythm & Hues 從 2010 年起所有角色都用 Delta Mush [D5] | 摺痕變圓順、減少擠壓；可用頂點群組只套手腳 [D4] | 一個修改器，程式加上去就好；前面有細分修改器時要 Bind [D4] | **建議試**：Armature 之後加一層，只套手腳 |
| **修正形態鍵（PSD）** | 關節彎到某角度時，疊上事先做好的修正形狀 [D7]；Blender 用 rotational difference 驅動器讓形狀鍵跟關節角度走 [D6]；手部有專門的加權 PSD 研究 [D8] | 指根、腳背摺痕最有效；也能做出「拇指靠過來時虎口肌肉鼓起」[R6] | 可以：Python 建形狀鍵＋驅動器（`ROTATION_DIFF` 變數）。拓撲固定時可做一次、按手長縮放重複用 | 第二階段：結構穩定後再做 |
| 輔助骨（扭轉骨、指節骨） | 加幾根不直接動畫的骨頭，用約束跟著主骨頭轉一部分 | 手腕扭轉時的「糖果紙」扭曲；論壇說常見解法是前臂加扭轉骨，或把扭轉的權重分布到前臂中段 [D10] | 可以，但要確認動畫重定向（`mixamo_retarget`）和服裝抄權重不受影響 | 等手腕扭轉測試出問題再加 |
| RBF 驅動的輔助關節 | MetaHuman 身體的做法：輔助關節由 RBF 解算器依姿勢自動驅動 [S7][S8] | 效果好 | 工具鏈複雜 | 不建議 |
| 隱式蒙皮（Implicit Skinning） | 用隱函數表面修正頂點，能做出手指彎曲時摺痕處的「接觸面」和肌肉鼓起 [D9] | 研究上最好 | Blender 沒有 | 不建議 |
| 手掌骨（Rigify 的 super_palm） | 用掌骨讓手掌可以拱起 [D11] | 雙手合十、握東西時手掌更自然 | 會多骨頭，Mixamo 沒有對應 | 不建議（Mixamo 沒有掌骨資料） |

---

## 5. 怎麼讓結果穩定、可重現（含接縫）

### 5.1 四條原則

1. **手腳的網格不經過任何「全身一起算」的步驟。** 體素重建、減面、自動權重、UV 排版都只對軀幹做；手腳在旁邊獨立產生。Roblox 的部件、模組化角色、建模教學「手另外做再接」都是這個思路 [S3][T1]。
2. **手腳用固定拓撲。** 同樣的參數，點數、編號、位置都一樣，權重也照點號或照位置算。ZEPETO、MetaHuman、MakeHuman 都是固定拓撲 [S4][S7][S13]。
3. **接縫放在「只跟一根骨頭動」的地方。**
   - 前臂中段：手腕的彎曲區是 ±2～3 cm，往手肘方向約前臂長的 1/3 處，兩邊都 100% 跟 `LowerArm`。
   - 小腿中段：100% 跟 `LowerLeg`。
   - 接縫兩側的點、權重、法線完全一樣，動起來也不會裂（頭身研究的結論：位置、法線、權重、顏色四樣一致就看不到縫 [S15]）。
4. **用指紋把「穩定」變成可檢查的事實。** 每次產生都記錄手、腳的指紋；改腳、腿、軀幹參數重做一次，手的指紋必須不變；同參數連做兩次也必須一樣。

### 5.2 接縫怎麼做（沿用頭身接口環）

| | 頭身（已完成） | 手腕／腳踝（建議） |
| --- | --- | --- |
| 環在哪 | 頭檔切口 48 點 | 前臂中段、小腿中段；**模板那一側固定 48 點**（籠子 12 點細分 2 次剛好 48 點，和脖子一致） |
| 兩邊是不是同一個物件 | 不是：頭有 52 個表情形態鍵和驅動器，不能合併 | **可以合併**：手腳模板沒有獨立的形態鍵，合併後焊接，就是真正的一塊網格 |
| 身體那側怎麼接 | `fit_neck_ring`：環下 12 mm 切掉、拉鍊三角形接到 48 點、3 圈 Hermite 過渡 | 同一套程式泛化成 `fit_ring(body, 環座標, 切面)`：軀幹的手臂在環的手肘側切開、拉鍊接上、短過渡帶 |
| 權重 | 脖子頂端 100% 給頭骨 | 接縫前後各 1～2 cm 100% `LowerArm`（腳是 `LowerLeg`），兩側相同 |
| 法線 | 頭抄身體法線（`seam_normals`） | 焊成一塊後自然連續；兩側網格密度差太多時，再對過渡帶做一次局部平滑 |
| 驗收 | `ring_check.py`：距離 0、夾角 < 1° | 同一支程式加手腕、腳踝兩組環：靜止、手腕彎 70°、扭 80°、腳踝 ±45° 時距離 0（合併焊接後必定 0，主要驗法線與權重） |

### 5.3 「只對軀幹做體素重建」要注意的地方

- 自動權重綁軀幹時，手、腳的骨頭要先關掉 Deform [W9]。不然前臂末端會被分到手的權重，接縫處就不是 100% 一根骨頭。
- 軀幹的減面也會在胸口、肩膀留下大三角面的明暗（`zepeto-body-v2.md` 第 3 節已觀察到）。這和手腳無關，但同樣是「減面」造成的。長期解法是方案 C；短期可以試「體素大一點、不減面」或只對軀幹減面（未實測）。

---

## 6. 方案比較與推薦

### 6.1 比較

| | **A 手腳固定模板＋接口環（推薦）** | B 最小改動 | C 整身固定拓撲基底網格 |
| --- | --- | --- | --- |
| 做法 | 手（含手腕、半截前臂）、腳（含腳踝、半截小腿）用程式產生四邊形籠子 → 固定次數細分 → 解析權重 → 前臂、小腿中段接口環接到體素融合的軀幹 | 手腳照舊用形狀拼，但從身體分出來**單獨**體素融合、減面、自動權重（只開手的骨頭），再用接口環接回 | 像 ZEPETO、MetaHuman：做一塊全身的固定網格（方塊建模，或改 Blender 官方 CC0 基底網格），換人用骨頭比例（調骨頭後套用為靜止姿勢）變形，權重照點號抄 |
| 改哪些程式 | `body_build.py`：新增 `hand_template()`、`foot_template()`（由 `box_hand` 擴充）、`fit_ring()`（由 `fit_neck_ring` 泛化）；`skin_body` 手臂、腿只做到接縫外 3 cm；`bind` 綁軀幹時關手腳骨頭 Deform；`body_checks.py` 重寫手部量測、新增腳；`hand_probe.py` 加掃描、雙手；新增 `foot_probe.py` | `body_build.py` 的 `build_mesh` 拆成軀幹、手、腳三塊各自處理；`fit_ring()`；`body_checks.py` 修量測 | 幾乎全部：`skin_body`、`hands_feet`、`build_mesh` 改成「載入模板＋調比例」；`fit_neck_ring` 改成模板內建環；UV 用模板的；服裝 `garment_lib` 要驗證 |
| 工作量（粗估） | 5～8 個工作天（含 1～2 輪審看） | 2～3 天 | 2～3 週以上，外加服裝、動畫全部重跑 |
| 造型（L 形、指蹼、掌緣、虎口） | **用邊環直接決定**，不再補丁 | 仍是拼接，問題還在 | 解決 |
| 穩定 | **手腳指紋完全不變** | 手腳只受自己的參數影響；但體素、減面、自動權重仍可能讓手本身的參數微調時跳動 | 全身穩定 |
| 風險 | 手的新外觀要使用者重新認可；接縫若密度差太大可能有淡淡明暗（可局部平滑）；鞋子、袖口要重長一次 | 低 | 最高：外觀、服裝、動畫、接口環全部重驗；新娘 v3 已被開場片 B 鎖定 |
| 和長期方向 | **是 C 的第一步**：手腳模板之後可以直接併進整身模板 | 過渡用 | 終點 |

**推薦 A 的理由**：

- 它同時解決使用者在意的兩件事：造型自然、數字穩定。B 只解決一半。
- 它重用了已經驗證過的兩塊程式：方塊手、接口環。
- 改動範圍只在手腕、腳踝以外，不碰軀幹、脖子、頭。
- 做出來的手腳模板，將來可以直接成為方案 C 整身模板的一部分。

**A 的變形版（A2）**：

- 手腳模板也可以不從頭寫，而是拿 Blender 官方 CC0 基底網格裡的手、腳 [S1][S2]，改成 ZEPETO 的短胖比例。
- 每個角色再用「調骨頭長度 → 套用為靜止姿勢」貼合。這跟 ZEPETO 縮放手、腳骨頭是同一個意思 [S4]。
- 優點：拓撲是專業做好的。缺點：寫實比例要先手動改成卡通，而且要自己先綁一次骨。
- 建議先用程式產生（A），A2 當備案。

### 6.2 方案 A 的實作步驟

**第 0 步：先修量測（不論哪個方案都要做，約 1 天）**

> **2026-10-14 已做完（1～7 項）**，結果與量法說明在 `limbs.md` 3.2。重點：舊量法的 8～9 mm 是彎曲內側皮膚翻面造成的假穿插；修好後新郎 v8、新娘 v3、攝影師 v1、`_z45` 全部過關、數字穩定；方塊手 `_box` 仍不過（比 YA 拇指壓進無名指 2.73 mm）。H3 的截面積目前只量 PIP、DIP（MCP 要等模板定出手掌邊界）。

1. `body_checks.py` 加「部位標記」：每個點在**靜止姿勢下**屬於哪一區（手掌、拇指 1～3、四指各 1～3、手腕、前臂），依它到各節骨頭的距離決定。不再看「最大權重是哪根骨頭」。之後拓撲固定了，標記直接寫進模板的點屬性。
2. 「同一塊皮膚」改用**網格上相連的距離**（沿邊走的最短距離，例如 < 1.5 倍手指直徑），不再用 6 mm 直線距離。
3. 指根摺痕（手掌 ↔ 該指第一節）明確歸到「關節內側擠壓」，不算成「指尖插進掌心」。
4. 加 `BVHTree.overlap` 的三角形交叉數、截面積保留、翻面與壓扁的面、權重的骨頭數與跨指污染。
5. 角度改成掃描，記錄「最差值」和「從幾度開始超標」。
6. 加指紋：手、腳各一個。
7. 用現有的新郎 v8、新娘 v3、`_box.work`、`_z45.work` 重量一次，看真正的數字。**如果分類修好後，方塊手其實已經過關，A 的優先順序可以重新討論。**

**第 1 步：手的模板產生器（`hand_template()`，約 2 天）**

> **2026-10-14 第 1、2 步試做完成**：`scripts/hand_template.py`＋`body_build.py HANDTPL=1`。和下面規格的差異：接口環是 16 點籠子 → 64 點（不是 12 → 48）；權重沒有另寫解析式，直接寫在籠子點上讓細分內插（過渡寬度量出來 0.67～0.95 倍直徑，在標準內）；UV 仍跟全身一起展（模板自己的固定 UV 還沒做）。檢查全過、改腳改腿手的指紋不變。細節與調參過程在 `limbs.md` 2.3，審看頁 https://claude.ai/artifact/NCwf1LZPwoezVfY4ysvSrp 。

- 以 `box_hand` 為底，籠子規格固定下來：
  - 前臂半截＋手腕：12 點一圈（細分 2 次後 48 點，最外圈就是接口環），往手腕漸少、上下對齊 [T1]。
  - 手掌：橫向照四根手指排欄、縱向 4～5 排；**最外側兩欄從手腕直走到食指根、小指根**，掌緣就是一條連續的邊，L 形轉角從結構上消失。
  - 手指：籠子每圈 4 點（細分後 16 邊；要更方的卡通感可改 8 點）；**每個關節 3 圈**（關節前、關節、關節後各約半個手指半徑）[T2][T4]；中段 1 圈；指尖收口。
  - 指縫：指根之間的面只到指根那一排，**指蹼深度**當成一個參數（指縫底到 MCP 的距離 ÷ 第一節長度，使用者要的是約 0）。
  - 拇指：從手掌靠手腕的側邊籠子面擠出 3 節 [T1]，拇指根肉墊是籠子本身的形狀，不再是另外的橢球。
- 細分固定 2 次，直接套用，不經體素、不減面。
- 在籠子的面上寫「部位」整數屬性，細分後每個點取周圍面的多數（細分後屬性會不會照預期傳下去，**要實測確認**）。
- UV：模板自己的固定 UV（手背、手心兩塊，接縫放在手掌側邊）。

**第 2 步：解析權重（約 0.5 天）**

- 每個手指點：投影到該指的骨頭鏈，得到位置 t；在每個關節，用平滑曲線（smoothstep）把權重從上一節過渡到下一節，**過渡寬度＝0.9 倍手指直徑**（現有標準 0.6～1.2 的中間值）。
- 手掌：100% `Hand`，在 MCP 和各指第一節過渡；拇指根肉墊在 `Hand` 與 `Thumb1` 之間過渡。
- 手腕：`LowerArm` ↔ `Hand` 過渡，寬度約手腕厚度；接縫前後 100% `LowerArm`。
- 用自動權重算一份當對照（只對手模板、只開手的骨頭），兩份都跑檢查，留好的那份。

**第 3 步：接回身體（約 1 天）**

- `skin_body` 的手臂只做到接縫外 3 cm（跟脖子管同理：體素、平滑會把管口收圓）。
- 綁軀幹前，把手、腳骨頭的 Deform 關掉 [W9]，綁完再打開。
- `fit_neck_ring` 泛化成 `fit_ring()`：在接縫手肘側切開 → 拉鍊三角形接到模板的 48 點 → 短 Hermite 過渡 → 合併、焊接。
- 接縫兩側 1～2 cm 權重設成 100% `LowerArm`。

**第 4 步：腳的模板（`foot_template()`，約 1 天）**

> **2026-10-14 試做完成**：`scripts/foot_template.py`＋`body_build.py FOOTTPL=1`；第 3 步「接回身體」也一起做了（`fit_tpl_rings` 手腳共用）。腳趾照建議做成趾塊（四道淺溝）——同日使用者說不像 ZEPETO，研究官方後改成 v2（腳長 17%、腳踝骨抬高、五根分開雕的腳趾）；鞋子尺寸寫進 `checks.json` 的 `feet.shoe`（還沒寫進 `build.json`）。第 5 步（變形方式比較）沒做：現行 LBS＋手腳 Preserve Volume 下檢查已全過。細節在 `limbs.md` 2.4。

- 小腿半截 12 點一圈（→ 48 點）→ 腳踝（前側多一兩圈，對應腳背摺痕）→ 腳跟、足弓、腳掌、前腳掌 → 腳趾。
- ~~**腳趾建議做成一塊有淺溝的「趾塊」**（五個小凸起），不做五根分開的膠囊。~~ **2026-10-14 更正**：ZEPETO 官方是五根分開雕的腳趾、只有一根腳趾骨，見 `limbs.md` 2.4。（原理由「骨架只有一根 `ToeBase`，五趾只能一起彎；分開的膠囊只增加穿插和權重風險」不成立：五根腳趾綁同一根骨頭照樣可以分開雕，v2 實測沒有穿插。）
- 權重：`LowerLeg` ↔ `Foot` 在腳踝過渡；`Foot` ↔ `ToeBase` 在腳掌前端那條線過渡；腳趾 100% `ToeBase`。
- 記錄鞋子要量的尺寸：腳長、腳掌最寬、腳跟寬、腳踝高、足弓高。寫進 `build.json`，出廠時在 changes 寫明有沒有變。

**第 5 步：選變形方式（約 0.5 天）**

- 三種組合各跑一次完整檢查：(1) 只有 LBS、(2) LBS＋手腳 Preserve Volume（現行）、(3) LBS＋手腳 Corrective Smooth。
- 依截面積（不塌也不鼓）與擠壓深度選一種，寫進預設。

**第 6 步：近照工具與審看頁（約 1 天）**

- `hand_probe.py` 加：掃描姿勢、雙手合十、OK 手勢、手腕扭轉。
- 新增 `foot_probe.py`：站立（正、側、從下往上看腳底）、墊腳、蹲、跪、走路蹬地那格。
- `body_page.py` 加手腳兩區。

**第 7 步：文件與交接**

- 更新 `checklist.md` 第 5、6 列與「腳只做一坨」那條；`limbs.md` 的 2.3、2.4 節；`SKILL.md` 第 5、6 步。
- 交接給服裝：手腳網格換新，袖口（量拇指根）、鞋子要重長一次。
- 交接給動畫：已審過的鏡頭只有手、腳近照需要重看。

**第二階段（結構穩定、使用者認可外觀之後再做）**

- 指根、腳背的修正形態鍵：在掃描找出的「開始超標角度」做修正形狀，用 `ROTATION_DIFF` 驅動器接到關節角度 [D6]，存成「骨頭座標系裡的位移」，換角色時照手長縮放重複用。
- 手腕扭轉若超標，再加前臂扭轉輔助骨 [D10]，並確認 `mixamo_retarget`、服裝抄權重都不受影響。

### 6.3 新的檢查清單

標「建議值」的門檻，是根據現有標準和業界做法推出來的。**第 0 步重量現有版本後，要依實際數字校正一次再定案。**

**手**

| # | 項目 | 姿勢 | 量什麼 | 門檻 |
| --- | --- | --- | --- | --- |
| H1 | 結構穩定 | 靜止 | 改腳、腿、軀幹參數重做，手的指紋不變；同參數連做兩次也一樣 | 完全相同 |
| H2 | 拓撲規格 | 靜止 | 每個指關節 3 圈籠子環；接口環 48 點；指蹼深度 | 符合規格；指蹼深度 ≤ 第一節長 × 0.15（建議值） |
| H3 | 截面積保留 | 掃描、握拳 | 各指 MCP、PIP、DIP 的截面積比 | 90° 時 0.85～1.10；60° 時 0.92～1.08（建議值，延續現有 bend 的 0.85／0.92／1.15） |
| H4 | 部位之間穿插 | 9 個手勢、掃描、張合、拇指、雙手 | 不同部位最深陷入（部位依靜止位置標記） | ≤ 1 mm（沿用） |
| H5 | 三角形交叉 | 同上 | 排除同一關節摺痕帶後，相交的三角形對數 | 0（建議值） |
| H6 | 關節內側擠壓 | 掃描、握拳 | 同一根手指（含指根↔手掌）摺痕深度 | ≤ 手指半徑 × 0.8（沿用） |
| H7 | 權重 | 靜止 | 每點骨頭數、總和、跨指污染、過渡寬度 | ≤ 4 根；總和 1 ± 0.001；污染 0 點；過渡 0.6～1.2 倍直徑（沿用） |
| H8 | 面品質 | 所有姿勢 | 翻面的面、壓扁的面 | 摺痕帶以外 0；壓扁比 ≥ 0.3（建議值） |
| H9 | 手勢接觸 | thumbs_up、fist、OK、雙手合十 | 該貼的地方距離 | 0～1 mm（貼住不陷進）；雙手合十掌心中央 ≤ 2 mm（建議值） |
| H10 | 手腕 | 彎 70°／翹 60°／扭 ±80° | 手腕截面積比 | 彎曲 ≥ 0.85；扭轉 ≥ 0.70（建議值） |
| H11 | 套 Mixamo | Mixamo 第 0 格、靜止 | 手指方向差 | ≤ 2°／≤ 3°（沿用） |
| H12 | 造型（目視＋數字） | 靜止、flat、張開 | 手掌輪廓在食指、小指根的轉角、虎口深度，加手背、手心、拇指側近照 | 轉角 ≤ 25°（建議值，需實測定）；使用者看近照確認 |

**腳**

| # | 項目 | 姿勢 | 量什麼 | 門檻 |
| --- | --- | --- | --- | --- |
| F1 | 結構穩定 | 靜止 | 腳的指紋（同 H1） | 完全相同 |
| F2 | 截面積保留 | 腳踝上 20°／30°、下 45°／50°；腳趾上 60°／70° | 腳踝前側、腳趾根截面積比 | 0.85～1.10（建議值） |
| F3 | 穿插 | 腳踝上 30°（腳背對小腿）、腳趾上 70°（腳趾對前腳掌）、併腳、交叉站 | 最深陷入 | ≤ 1 mm |
| F4 | 摺痕擠壓 | 同上 | 腳背、腳趾上方摺痕深度 | ≤ 該處厚度 × 0.4（建議值，需實測定） |
| F5 | 腳底貼地 | 站立 idle | 腳跟區、前腳掌區最低點離地；有沒有點低於地面；足弓內側離地 | ≤ 2 mm；≤ 1 mm；≥ 3 mm（建議值） |
| F6 | 權重 | 靜止 | 腳趾區 100% `ToeBase`；`Foot`↔`ToeBase`、`LowerLeg`↔`Foot` 過渡寬度；骨頭數、總和 | 過渡 0.6～1.2 倍該處厚度（建議值）；≤ 4 根；總和 1 |
| F7 | 面品質 | 所有姿勢 | 翻面、壓扁 | 同 H8 |
| F8 | 鞋子尺寸 | 靜止 | 腳長、腳掌寬、腳跟寬、腳踝高、足弓高 | 記錄；和上一版不同時寫進 changes |
| F9 | 動畫抽格 | 走路蹬地、跑、蹲、跪、盤腿坐 | F2～F4 的數字＋近照 | 同上 |

**接縫（手腕、腳踝各一）**

| # | 項目 | 門檻 |
| --- | --- | --- |
| J1 | 接口環距離（靜止、手腕彎曲與扭轉、腳踝屈伸） | 0 mm（焊接後必然） |
| J2 | 接縫兩側法線夾角 | < 1°（沿用 ring_check） |
| J3 | 接縫前後 1～2 cm 權重 | 100% `LowerArm`／`LowerLeg` |
| J4 | 近照 | 看不到線或明暗斷層 |

---

## 7. 查不到或不確定的地方

| 項目 | 狀況 |
| --- | --- |
| ZEPETO 官方手、腳的網格拓撲 | 官方指南只說基底檔有骨架和遮罩、手腳骨頭可縮放、衣服抄權重 [S4][S5][S6]；**沒有**手指、腳趾的網格或骨頭細節 |
| VRoid 身體是否固定拓撲 | 官方查不到。推測是模板＋滑桿。可以拿專案裡以前匯入的 VRoid 新娘、新郎身體比點數確認 |
| Ready Player Me 全身版的手指、腳趾骨頭 | 官網已連不上（服務已關閉），只剩半身版說明與社群說法 [S11] |
| Mixamo 骨架細節等級（Skeleton LOD）選項 | 只有論壇提到「no fingers」等選項，查不到官方說明 [S12] |
| MetaHuman 手部的修正關節或 RBF 細節 | 只查到身體、脖子的 RBF 說明，手部沒有 [S7][S8] |
| 遊戲、動畫公司的自動化手腳 QA 流程 | GDC、SIGGRAPH 的搜尋只找到相關但不直接的分享（EA DICE 模組化綁骨、Animal Logic 鏡頭雕刻）；**查不到公開的量化檢查清單**。第 6.3 節的門檻是本報告的建議 |
| Polycount 拓撲貼文 | 網站擋了直接讀取（403），內容取自搜尋摘要 [T2][T3][T6][T11]；Polycount Wiki 的 Limb Topology 頁連不上 |
| 「三角形交叉數」的業界門檻 | 查不到；建議值 0 是本報告提的 |
| 體素重建是否完全局部（腳改了，手的體素會不會變） | 推測是局部的，**未實測**；可以用第 0 步的指紋直接驗證 → **2026-10-14 實測：手會變**（只改腳，手的點數 6,742 → 6,167；只改腿粗也會變）。體素和減面哪一個造成的沒有拆開測，全身一起減面最可疑 |
| 細分後整數面屬性怎麼傳 | 方案 A 第 1 步要實測 |
| 工作天數 | 是依現有程式規模粗估，沒有把使用者審看等待時間算進去 |
| Houdini 的做法 | 沒有深入查（Houdini 有 Biharmonic、Bone Capture 等權重工具，但我們不用 Houdini） |

---

## 8. 來源表

### 拓撲與建模

- [T1] 華盛頓大學 CSE458 Project 1b：Hand Modeling（方塊手掌、擠出手指、8 邊手指、拇指 45°、手腕上下對齊接手臂）：https://courses.cs.washington.edu/courses/cse458/23au/content/projects/project1b
- [T2] Polycount：手指 6 或 8 邊、指節 3 圈、不彎處稀疏（403，內容取自搜尋摘要）：https://polycount.com/discussion/comment/2739057
- [T3] Polycount：指根排成一排且偏高、指根之後 3 節（拇指 2 節）（403，搜尋摘要）：https://polycount.com/discussion/comment/2714600
- [T4] Blender Artists：關節 3 圈，中間那圈兩骨分、兩側給最近的骨頭：https://blenderartists.org/t/character-basic-mesh-modeling-help/581784
- [T5] Blender Artists：手掌分區與摺痕、指節要有足夠的邊：https://blenderartists.org/t/hand-topology-proportions/490517
- [T6] Polycount：避免六極點、減少手掌極點（403，搜尋摘要）：https://polycount.com/discussion/comment/2628578 、https://polycount.com/discussion/comment/2628552
- [T7] Tripo 部落格：手的低面數拓撲、要測握拳（廠商部落格，參考就好）：https://www.tripo3d.ai/blog/explore/smart-mesh-topology-for-hands-fingers-low-poly
- [T8] Tripo 部落格：腳、鞋的拓撲（廠商部落格，參考就好）：https://www.tripo3d.ai/blog/explore/smart-mesh-topology-for-feet-shoes-boots-low-poly
- [T9] ZBrush 小技巧：依解剖重拓撲、極點避開摺痕、扭轉測試：https://novedge.com/blogs/design-news/zbrush-tip-anatomy-driven-retopology-for-predictable-deformation
- [T10] 建模姿勢：放鬆半彎的手、關節建在活動範圍中點：https://blenderartists.org/t/character-model-pose/604469 、https://polycount.com/discussion/comment/887164
- [T11] Polycount：手肘、膝蓋內側多一兩條邊（403，搜尋摘要）：https://polycount.com/discussion/comment/1402970

### 各系統

- [S1] Blender 官方 Human Base Meshes（手、腳、頭各有獨立網格，四邊形、有 UV）：https://developer.blender.org/docs/features/asset_system/asset_bundles/human_base_meshes/
- [S2] CG Channel：Blender Studio 基底網格 17 個、CC0：https://www.cgchannel.com/2023/06/download-blender-studios-free-human-base-meshes
- [S3] Roblox 角色身體規格（15 塊、手腳獨立、封口水密、每點 ≤ 4 骨、選配手指骨）：https://create.roblox.com/docs/art/characters/specifications
- [S4] ZEPETO Studio 指南 Deformation Custom（頭、手、腳骨頭可縮放；全身 0.3～1.35）：https://docs.zepeto.me/studio-guide/deformation-custom
- [S5] ZEPETO Studio 指南 Modeling basics（creatorBaseSet：骨架＋遮罩）：https://docs.zepeto.me/studio-guide/modeling-basics
- [S6] ZEPETO Studio 指南 Rigging, Masking（從基底遮罩 Transfer Weights、By Name）：https://docs.zepeto.me/studio-guide/rigging-masking
- [S7] MetaHuman Body Conform Controls（標準拓撲、核心關節與 RBF 驅動的輔助關節）：https://dev.epicgames.com/documentation/metahuman/body-conform-controls
- [S8] MetaHuman Maya Pose Editor（RBF、swing twist、拓撲不可變）：https://dev.epicgames.com/documentation/metahuman/maya-pose-editor
- [S9] MetaHuman DNA：https://dev.epicgames.com/documentation/metahuman/metahuman-dna-rig-definition-and-rig-operation
- [S10] VRM 1.0 Humanoid 規格（手指各 3 節、腳趾只有 toes 一根）：https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/humanoid.md
- [S11] Ready Player Me 半身 VR 版（Wolf3D_Hands）：https://docs.readyplayer.me/ready-player-me/api-reference/avatars/vr-avatar （已連不上）；Babylon.js 論壇（手部骨架、缺掌骨）：https://forum.babylonjs.com/t/adding-webxr-hand-tracking-to-ready-player-me-avatars/42760
- [S12] Adobe 社群：Mixamo 手指靠太近只長出部分手指骨：https://community.adobe.com/questions-696/mixamo-auto-rig-messing-up-hands-not-including-all-fingers-589141 ；Skeleton LOD「no fingers」：https://community.adobe.com/t5/mixamo-discussions/auto-rigging-part-doesn-t-work/td-p/11758306
- [S13] MakeHuman 基底網格與輔助幾何：https://static.makehumancommunity.org/mpfb/docs/assets/basemesh_and_helpers.html
- [S14] VRoid 模型是 Body、Face、Hair 三塊：https://styly.cc/tips/blender-vrm-export1/
- [S15] 先前研究：ZEPETO 身體研究頁 https://claude.ai/artifact/JudBvPg4xRPimxfBwRZcwL ；頭身接縫研究 `.claude/skills/zepeto-face-rig/references/research-head-body-seam.md`（[G2] 接縫點權重要一致：https://www.tech-artists.org/t/vertex-weights-unreal/15655）
- [S16] 模組化角色接縫：Polycount（搜尋摘要）https://polycount.com/discussion/comment/2715177 ；Unreal 論壇 https://forums.unrealengine.com/t/how-do-you-create-a-segmented-model-with-no-normal-seams/337171

### 檢驗

- [R1] Eaton Hand：手部正常活動範圍表：https://eatonhand.com/clf/clf218.htm
- [R2] 印度手部活動範圍常模研究（390 隻手）：https://thieme-connect.de/products/ejournals/abstract/10.1055/s-0044-1788593
- [R3] Physiotutors：腳踝與足部主動活動範圍：https://book.physiotutors.com/?p=1149
- [R4] QUT：第一蹠趾關節活動範圍：https://podiatry-anatomy-app.qut.edu.au/content/joints/1st-mtp-joint-rom.html
- [R5] QUT：腳踝活動範圍：https://podiatry-anatomy-app.qut.edu.au/content/joints/ankle-rom.html
- [R6] Autodesk Maya：Skinning a hand（拇指靠近時虎口鼓起、影響物件＋驅動鍵）：https://help.autodesk.com/cloudhelp/2017/ENU/Maya/files/GUID-99A8D786-4A4C-4280-A130-27D2B5F004C6.htm
- [R7] 動作捕捉 ROM 包（1053 格、含手指，CC BY-NC）：https://milio-serrano.gumroad.com/l/pjnxg
- [R8] Fab 手部綁骨商品（握拳、張開、範圍測試分段）：https://www.fab.com/listings/60828e7b-090c-485e-8cff-8db9d2d7fb64
- [R9] Blender 手冊 Mesh Analysis：https://docs.blender.org/manual/en/4.2/modeling/meshes/mesh_analysis.html
- [R10] Blender 手冊 3D Print Toolbox：https://docs.blender.org/manual/en/3.6/addons/mesh/3d_print_toolbox.html
- [R11] Blender Python API mathutils.bvhtree（overlap、find_nearest_range、FromObject）：https://docs.blender.org/api/current/mathutils.bvhtree.html
- [R12] 蒙皮評估：權重誤差分數反映不了動畫品質（A Geodesic Cut-Cell Prior for Neural Skinning）：https://arxiv.org/pdf/2608.11272 ；LBS 體積流失：https://pubs.cs.uct.ac.za/id/eprint/403/1/skinning_afrigraph.pdf

### 權重

- [W1] Blender 手冊 Armature Deform Parent（With Automatic Weights 的限制）：https://docs.blender.org/manual/en/latest/animation/armatures/skinning/parenting.html
- [W2] Blender bone heat 原始提交（依 Baran & Popović 2007）：https://projects.blender.org/archive/blender-archive/src/commit/ddbd9182d41b89f7bec11400a1949759dcfcf3fe/source/blender/include
- [W3] Blender Artists：Bone Heat Weighting failed：https://blenderartists.org/t/bone-heat-weighting-failed-to-find-solution-for-one-or-more-bones/701412
- [W4] 手指權重串到隔壁：https://blenderartists.org/t/issues-rigging-a-hand/1527110 、https://app.cinevva.com/guides/blender-weight-painting-problems
- [W5] Voxel Heat Diffuse Skinning FAQ（手指腳趾建議表面熱擴散）：https://superhivemarket.com/products/voxel-heat-diffuse-skinning/faq ；CG Dive 評論：https://cgdivetest.super.site/tools/voxel-heat-diffuse-skinning
- [W6] Maya Geodesic Voxel Binding：https://help.autodesk.com/cloudhelp/2016/ENU/Maya/files/GUID-E9FC4C94-CDEB-41DC-AF8E-95469EC69BEE.htm ；論文：https://diglib.eg.org/handle/10.2312/15001
- [W7] Blender 手冊 Data Transfer 修改器：https://docs.blender.org/manual/en/5.2/modeling/modifiers/modify/data_transfer.html
- [W8] Robust Skin Weights Transfer（Epic，SIGGRAPH Asia 2023）：https://www.dgp.toronto.edu/~rinat/projects/RobustSkinWeightsTransfer/ ；程式：https://github.com/rin-23/RobustSkinWeightsTransferCode ；Blender 外掛介紹：https://digitalproduction.com/2025/04/23/weight-no-more-streamlining-blenders-weight-painting-with-robust-weight-transfer/
- [W9] Blender 手冊 Bone Deform（關掉就不參與自動權重）：https://docs.blender.org/manual/en/dev/animation/armatures/bones/properties/deform.html

### 變形

- [D1] Blender 手冊 Armature 修改器（Preserve Volume、Multi Modifier）：https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html
- [D2] Kavan 等 2007 Skinning with Dual Quaternions：https://users.cs.utah.edu/~ladislav/kavan07skinning/kavan07skinning.html ；PSD 課程頁（DQS 彎曲鼓脹）：https://imagine.inrialpes.fr/people/Francois.Faure/htmlCourses/PoseSpaceDeformation.html
- [D3] Le & Hodgins 2016 Optimized Centers of Rotation（Disney Research）：https://la.disneyresearch.com/publication/skinning-with-optimized-cors/
- [D4] Blender 手冊 Corrective Smooth 修改器：https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/corrective_smooth.html
- [D5] Delta Mush（Mancewicz 等，SIGGRAPH 2014）：https://history.siggraph.org/?p=138877 ；Maya Delta Mush：https://help.autodesk.com/cloudhelp/2016/ENU/Maya/files/GUID-139B703C-28E7-4787-8FD4-C2991BD6C990.htm
- [D6] Blender 手冊 Drivers Workflow & Examples（rotational difference 驅動修正形態鍵）：https://docs.blender.org/manual/en/2.81/animation/drivers/workflow_examples.html
- [D7] Lewis、Cordner、Fong 2000 Pose Space Deformation：https://www.scribblethink.org/Work/PSD/PSD.pdf
- [D8] Kurihara & Miyata 2004 Modeling Deformable Human Hands from Medical Images（加權 PSD）：https://diglib.eg.org/handle/10.2312/SCA.SCA04.357-365
- [D9] Vaillant 等 2013 Implicit Skinning（手指摺痕接觸）：https://imagine.inrialpes.fr/people/Damien.Rohmer/documents/publications/13_siggraph_implicit_skinning/13_siggraph_implicit_skinning.html
- [D10] 手腕扭轉塌陷與扭轉骨：https://forums.unrealengine.com/t/wrist-twist-collapse-in-editor/430689 ；Cascadeur Twist：https://cascadeur.com/help/category/103
- [D11] Blender 手冊 Rigify limbs（super_palm）：https://docs.blender.org/manual/en/dev/addons/rigify/rig_types/limbs.html
- [D12] Blender 手冊 Surface Deform：https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/surface_deform.html
- [D13] Blender 手冊 Decimate 修改器：https://www.blender.org/manual/en/modeling/modifiers/generate/decimate.html
