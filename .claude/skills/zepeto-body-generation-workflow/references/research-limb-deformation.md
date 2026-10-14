# 四肢關節變形：手腕扭轉、變形方式、張指、權重污染、關節活動範圍、併腳（研究報告，2026-10-14）

> 交辦內容：身體端剩下的六項（前臂扭轉不塌、三種變形方式比較、手指張開併攏、權重跨指污染、一般動作關節不塌、腳併攏站），上網研究並給出做法、驗證方式、對下游的影響與優先順序。
> 研究方式：讀專案程式＋上網查資料。**沒有改任何現有檔案、沒有跑 git、沒有開 Blender。** 文中的數字分三種：查到的（附來源）、從我們程式算出來的（寫「估算」）、本報告提的建議門檻（寫「建議值」，第 0 步量完要校正）。
> 讀過的程式：`scripts/body_build.py`（`bones_layout`、`build_armature`、`bind`、`tpl_weights`）、`scripts/hand_template.py`、`scripts/body_checks.py`（量法 v2、`v2ref`、`feet`、指紋）、`blender-motion-library/scripts/mixamo_retarget.py`、`pose_lib.py`（`twist_forearm`）、`zepeto-clothing-generation-workflow/scripts/garment_lib.py`（`transfer_weights`、`trousers`、`shoes`、`hide_body`、`corrective_smooth`）、`zepeto-animation-generation-workflow/scripts/zanim_sample.py`、`zanim.py`；`D:/render-work/zepeto-body/build/_tplF3.work/build.json`、`D:/render-work/mixamo/raw/`（只列檔名）。
> 文中 `[代號]` 對應文末來源表；`research-hands-feet.md` 的代號寫成「手腳研究 [D6]」。

> **2026-10-14 實作狀態**（做法、數字、工具的現況以 `limbs.md` 為準）：① 前臂扭轉 → 做了，左右各 2 根扭轉骨（`TWIST=1` 預設；limbs.md 2.5），檢查 `wrist` 擋出廠；② 變形方式 → 比過三種，手維持一般變形＋手部保留體積（2.7）；③ 手指張開併攏 → 量了，當參考（3.4）；④ 權重污染 → 連續清理做了（`WEIGHTCLEAN=1`；2.6），檢查 `weights` 擋出廠；⑤ 一般動作關節 → 量了；半轉輔助骨、關節平滑試做後，**使用者選維持一般變形**（2.7）；⑥ 併腳 → 量了，交給服裝（鞋寬）、動畫（新郎併腳站改小八字）（3.4、第 5 節）。

---

## 結論（先看這段）

**一句話：前臂扭轉要靠「加兩根只負責扭轉的輔助骨」，而不是把「保留體積」擴大；這兩根骨頭只要做成「葉子骨」（底下不掛任何骨頭），套 Mixamo 動作的程式完全不用改，服裝抄權重也會自動跟上。其他五項以「先量、再定門檻」為主，大部分只要加檢查，不用改身體。**

### 六個重點

1. **手腕扭轉（糖果紙效應）是現在最可能出事的地方**
   - 糖果紙效應：手掌繞前臂轉的時候，手腕那圈皮膚像糖果包裝紙兩端一樣被扭細。
   - 現在手腕那圈是「前臂一半、手掌一半」的權重，扭轉全部擠在手腕 2～3 cm 內。
   - 估算：手心朝上（相對 T 字扭約 150°）時，手腕截面積只剩約 **4 成**；扭 80° 剩約 8 成（第 1.1 節）。拿手機、端盤子、比讚這類 Mixamo 動作都會碰到。
   - 業界做法一致：前臂加扭轉輔助骨（Unreal 每段 2 根、ZEPETO 官方骨架有 `lowerArmTwist`）[I2][Z2]。
   - 建議：每隻前臂加 2 根扭轉骨，分到手掌扭轉的 1/3、2/3。估算扭 150° 時截面積回到約 8 成、扭 80° 約 95%。

2. **三種變形方式：全身底子維持一般變形（LBS），不要擴大「保留體積」（DQS）**
   - 服裝只用 LBS。身體某處改用 DQS 或修正平滑，那裡的身體和衣服就會變形得不一樣，袖口、褲管會穿模。
   - DQS 彎曲時會鼓起來，官方文件也說膝蓋、手肘會凸出 [I5]；專案也實測過全身開會讓肩膀、屁股鼓起來。
   - 手指維持現行（手才開 DQS）。另外做一次「LBS／DQS／修正平滑」三方比較，用數字決定要不要換（第 2.5 節列了要量哪些數字）。

3. **手指張開、併攏、對掌：加檢查就好**
   - 真人手指外展約 20～30°、拇指外展 60～70° [R1]。
   - 測四件事：張開時指蹼拉多開、只動一根手指時隔壁被拖多少、併攏擠壓時互陷多深、拇指捏食指（交換戒指的動作）。

4. **權重跨指污染：把定義從「只看第 2、3 節」擴大成三類**
   - 三類：跨指、跨肢（左右腿互相吃到）、遠距（點吃到離它很遠的骨頭）。
   - 另加一個「動一根看鄰居」的功能測試，連 0.01 以下的小權重也抓得到。
   - 修法：每個部位列一張「允許的骨頭表」，不在表上的清掉，再清碎權重、限 4 根、正規化。

5. **一般動作關節不塌：照業界 ROM 做法，每個關節逐步掃描**
   - ROM：關節活動範圍測試，把關節從 0 度一路彎到極限，看網格會不會壞。
   - 做法是「中立 → 正 → 中立 → 負 → 中立」逐格掃描 [R7]。手肘、膝蓋、腳踝、髖、肩都量。
   - 量截面積、彎曲面厚度、內側擠壓與接觸、外側拉伸、翻面、壓扁。
   - 測試片大多能用已下載的 Mixamo 動作（傳簡訊、坐著喝東西、跪、蹲、跑、推重物…，第 5.4 節）。

6. **腳併攏站：算出來兩腿本來就很近，要量清楚、交給服裝**
   - 估算：髖關節左右各 6.6 cm、腳直直往下。每條腿往內收約 **4°** 兩踝就碰在一起，這時兩膝內側只剩約 0.6 cm。
   - 長褲每條褲管比皮膚外擴 8～18 mm [程式]，所以穿長褲的併腳一定會讓兩條褲管互撞；皮鞋外擴 10～14 mm，同理。
   - 建議：身體端量出「從站姿最多能內收幾度才不撞」，寫進出廠資料給服裝、動畫。**不要為了這件事改腿距**：那是骨架變動，代價大。

### 建議順序

| 順序 | 做什麼 | 工時 | 為什麼排這裡 |
| --- | --- | --- | --- |
| 0 | 共同第 0 步：統計 Mixamo 動作裡的扭轉、張指、站距，並量現行身體的基準 | 0.5 天 | 決定要幾根扭轉骨、要測幾度、門檻定多少 |
| 1 | 權重污染檢查＋修（第 4 節） | 0.5～1 天 | 便宜，也是扭轉骨與 ROM 的前提 |
| 2 | 前臂扭轉骨（第 1 節） | 1.5～2 天 | 手每一鏡都看得到；新娘禮服露手臂 |
| 3 | 四肢 ROM 檢查，先手臂再腿（第 5 節） | 1.5～2 天 | 走路、坐、跪是動畫的日常 |
| 4 | 變形方式三方比較（第 2 節） | 1 天 | 決定手指要不要從 DQS 換成修正平滑 |
| 5 | 張指／併指／對掌（第 3 節）、併腳（第 6 節） | 1～1.5 天 | 便宜，可以跟第 3 項同一次跑 |

合計約 **6～8 個工作天**（不含使用者審看的等待）。

---

## 先解釋幾個會一直出現的詞

| 詞 | 白話 |
| --- | --- |
| 糖果紙效應（candy wrapper） | 骨頭繞自己的長軸轉（扭轉）時，兩根骨頭交界那圈皮膚被扭細，像糖果紙兩端 [I4] |
| LBS（一般線性混合） | Blender 預設的骨架變形：一個點跟幾根骨頭動，就把那幾根骨頭的「搬移」照權重平均。彎到底會塌、扭轉會細 |
| DQS（保留體積） | Blender 叫 Preserve Volume：改用「對偶四元數」平均骨頭的轉動。不塌、不細，但彎曲時會鼓 [K1][I5] |
| 修正平滑（Corrective Smooth） | Blender 版的 Delta Mush：先把變形後的網格抹平，再把靜止時的細節加回去。摺痕變圓順，但會把刻意的稜角也抹軟 [B8]（手腳研究 [D4][D5]） |
| 扭轉骨（twist bone） | 只負責分攤扭轉的輔助骨。不會出現在動畫資料裡，由約束自動算出要轉多少 |
| 葉子骨 | 底下沒有掛任何子骨頭的骨頭。Unreal 的扭轉骨都是葉子骨 [I2] |
| 約束（constraint） | 骨頭上的自動規則，例如「抄另一根骨頭轉動的 1/3」 |
| 擺動＋扭轉拆解（swing / twist） | 把一個轉動拆成兩段：先讓骨頭指向新方向（擺動），再繞自己的長軸轉（扭轉）。要抄「只有扭轉」就要先拆 [B1] |
| B-Bone（彎曲骨） | Blender 可以把一根骨頭切成好幾小段、各段漸進轉動的骨頭 [B5] |
| 截面積保留率 | 在關節中間切一刀算切口面積，變形後 ÷ 靜止。小於 1 是塌、大於 1 是鼓 |
| ROM 測試 | Range of Motion，關節活動範圍測試：每個關節從 0 度掃到極限，看網格會不會壞 |
| 外展／內收 | 手指（或腿）往外張開／往中間併攏 |
| 對掌 | 拇指橫過手掌去碰其他手指，例如拇指尖碰小指尖。臨床用 Kapandji 0～10 分評分 [R3] |
| 跨指污染 | 某根手指的點，吃到別根手指骨頭的權重。彎那根別的手指時，這根也會被拉動 |
| `_scale` 骨 | ZEPETO 官方骨架裡「專門帶權重、用來改體型」的骨頭；動作骨本身不帶權重 [Z3][Z4] |

---

## 0. 共同第 0 步：先量 Mixamo 動作和現行身體（0.5 天）

六項的門檻和扭轉骨數量，都要看「我們的動畫實際會用到多大角度」，所以先量。這步完全唯讀，不改身體。

| 量什麼 | 怎麼量 | 拿來決定什麼 |
| --- | --- | --- |
| 前臂扭轉落在哪 | 對 `D:/render-work/mixamo/raw/` 每支 FBX：`mr.read_fbx` → `mr.retarget` 套到一副身體 → 每格用 `mr._twist_about` 算「手肘處扭轉」（上臂→前臂）和「手腕處扭轉」（前臂→手掌） | 扭轉大多在手腕：只要前臂扭轉骨。手肘處也很大：要加「手肘反扭」骨（第 1.5 節選配） |
| 前臂扭轉最大幾度 | 同上，取每支片的最大值與第 95 百分位 | 要 2 根還是 3 根扭轉骨（第 1.1 節的表） |
| 上臂、大腿扭轉 | 肩胛→上臂、骨盆→大腿的扭轉 | 要不要做上臂、大腿的扭轉骨（目前列為之後再做） |
| 手肘、膝、腳踝、腳趾、手腕的最大彎曲 | 兩節骨頭方向夾角，每支片取最大值與在哪一格 | ROM 測試角度（第 5.2 節），以及第 5.4 節自動挑格 |
| 手指張開角度 | 相鄰兩指第 1 節方向投影到手掌平面的夾角 | 張指測試角度（第 3 節） |
| 站立時兩腳距離 | 待機類（standing_idle、female_idle、happy_idle、breathing_idle）兩踝 x 距離 | 併腳測試與站距（第 6 節） |
| 現行身體的基準 | 用 `_tplF3.work`（手腳模板版）跑第 1～6 節所有新檢查 | 每個門檻的「現況值」 |

- 建議寫成新的唯讀程式 `scripts/limb_survey.py`：背景 Blender、讀 FBX、輸出一份 JSON 加摘要表。
- 已有的 `D:/render-work/mixamo/tools/arm_twist.py` 只印開場片某幾秒的扭轉，沒有整庫統計。

---

## 1. 手腕彎曲與前臂扭轉不塌（糖果紙效應）

### 1.1 問題在哪、會怎樣

**現在的權重**（`hand_template.py`）：

- 前臂接口環到手腕前：籠子兩圈，100% `LowerArm`。
- 手腕那一圈（`uW`）：`LowerArm` 一半、`Hand` 一半。
- 手掌第一圈起：100% `Hand`。

所以手掌繞前臂轉多少，就全部擠在手腕這 2～3 cm 裡扭完。手腕這一帶的 `HAND_DQS` 權重是 0.5，等於一半 DQS、一半 LBS。

**理想化估算**（圓形截面、看最糟的那一圈）：

- 兩根骨頭各分一半、彼此扭差 Δ 度時，LBS 會把那圈的半徑縮成 cos(Δ/2)。
- DQS 不縮。
- 截面積約等於半徑比的平方。

| 手掌相對 T 字扭轉 | 現行（手腕一半 DQS） | 純 LBS、沒扭轉骨 | 1 根扭轉骨（ZEPETO 式） | **2 根扭轉骨（建議）** | 3 根扭轉骨 |
| --- | --- | --- | --- | --- | --- |
| 80°（比讚、側掌） | 0.78 | 0.59 | 0.88 | **0.95** | 0.97 |
| 120° | 0.56 | 0.25 | 0.75 | **0.88** | 0.93 |
| 150°（手心朝上：端盤子、看手機） | **0.40** | 0.07 | 0.63 | **0.82** | 0.90 |

（表內是截面積保留率。N 根扭轉骨平均分配時，相鄰兩段扭差 = 總扭轉 ÷ (N+1)。）

**會怎樣**：

- 手心朝上的動作，手腕會變成一條細頸，而且扭紋集中在一小段，像擰毛巾。
- 新娘禮服是露肩、露手臂的，這個在畫面上看得到。
- 現行檢查完全測不到：`body_checks.py` 沒有任何手腕扭轉的姿勢（H10 只是手腳研究裡的建議，還沒做）。

> **Mixamo 的 T 字是掌心朝下**（`mixamo_retarget.py` 檔頭）。從掌心朝下轉到掌心朝上，真人前臂可以轉約 160～180°：旋前、旋後各約 80～90° [R1][R4]。所以 150° 不是極端，是日常會出現的角度。

### 1.2 業界怎麼做

| 系統 | 扭轉怎麼處理 | 來源 |
| --- | --- | --- |
| **Unreal（UE5 Manny）** | 上臂、前臂、大腿、小腿**每段 2 根扭轉骨**，都是直接掛在肢體骨頭下的葉子骨，不串成一串 | [I2] |
| **ZEPETO 官方** | 有 `lowerArmTwist`、`lowerLegTwist`（各有 `_scale`）。衣服綁骨時「要包含 lowerArm(Leg)Twist 與其 scale，手腕與小腿才會平順變形」 | [Z1][Z2] |
| **Unity Humanoid** | 沒有扭轉骨也能分攤：設定 `lowerArmTwist` 預設 0.5，前臂的扭轉手肘、手腕各分一半；上臂、大腿、小腿也各有一個 | [I1] |
| **Cascadeur** | 扭轉骨抄上一根骨頭轉動的一部分（強度 0.5＝抄 50%）；上臂、大腿另有「反扭」骨抵銷自己的扭轉 | [I3] |
| **Maya／Softimage** | 承認 LBS 扭轉會塌；DQS 可解，但膝肘彎曲時會凸出，建議用權重混合兩種 | [I4][I5] |
| **Blender 社群** | 扭轉骨：先用 Damped Track 把彎曲去掉，再用 Copy Rotation 只抄 Y 軸、影響 0.5、Local 空間；只抄 Y 軸不先去彎曲的話，手腕同時彎和扭就會亂 | [I8] |
| **Blender 官方手冊** | 「擺動＋扭轉」拆解常用來驅動修正形態鍵與骨頭；傳統做法是 Damped Track 輔助骨＋子骨頭 Copy Transforms | [B1] |
| **Rigify** | 肢體用額外的 tweak 控制點＋B-Bone 分段 | [B6] |
| **只用 DQS** | Blender 裡可以，但匯出到 UE4 等只支援 LBS 的引擎就失效（我們不匯出，所以不受影響） | [I7]（搜尋摘要） |

**歸納**：成品角色幾乎都是「LBS＋扭轉骨」。DQS 只當局部補救。Unity 那種「把扭轉分給手肘和手腕」是沒有扭轉骨時的折衷。

### 1.3 ZEPETO 官方骨架查到什麼

| 骨頭（照官方頁原字） | 出現在哪 | 說明 |
| --- | --- | --- |
| `hips`、`hips_scale` | [Z2][Z3] | 綁骨一定要包含；衣服的 hips 權重要是 0 |
| `pelvis` | [Z2] | 只提到名字 |
| `spine`、`spine_scale` | [Z4] | 「spine 群組沒權重時，權重在同名的 scale 群組」 |
| `shoulder_L／R`、`upperArm_L／R` | [Z3][Z6] | A 字站姿：肩 rotateZ 7.5°、上臂 40° |
| `upperLeg_L` | 特殊體型頁 | 只是舉例 |
| `lowerArmTwist_L／R_scale`、`lowerLegTwist_L／R_scale` | [Z2] | 衣服要把遮罩的權重抄到這些 `_scale` 骨上 |
| `lowerArm(Leg)Twist` | [Z1][Z2] | 「手腕與小腿才會平順變形」 |
| `head`、`jBone`、`hand`、`foot`、`thumbPro` | [Z1] | 鞋子建議只選這幾根加 hips；左右後綴沒寫 |

**`_scale` 骨是做什麼的**：

- 官方說：「ZEPETO 用 scale 骨讓基本身體適應多種體型」「權重放在 scale 骨上，沒有 scale 的骨頭不放權重」[Z3]。
- 動作骨（base bone）負責動作，scale 骨負責體型 [Z4]。也就是說，每根會變形的骨頭底下都掛一根 `_scale` 子骨頭來帶權重。玩家改體型時只縮放 scale 骨，衣服也跟著縮。
- **我們不需要 `_scale` 骨**：我們每副身體都照那顆頭重新長、衣服也每副身體重新長，沒有「同一件衣服套到不同體型」的需求。

**查不到的**：

- 完整骨頭清單。
- 有沒有上臂、大腿扭轉骨。官方頁只提到前臂、小腿兩種。
- 扭轉骨的位置和父子關係。
- 執行時誰去轉扭轉骨（Unity 腳本？動作檔烤好？）。

要確認只能下載官方 `creatorBaseSet` 檔（本次沒下載）。鞋子頁提到「鞋子的腳趾、腳踝關節加在下身服裝上，所以 lowerLegTwist 和 lowerLegTwist_scale 佔同一區」[Z1]，推測小腿扭轉骨靠近腳踝；前臂的推測靠近手腕。**這是推測。**

### 1.4 在我們的前提下有四條路

前提：動畫只來自 Mixamo、Mixamo 和 VRoid 骨架都沒有扭轉骨（`mixamo_retarget.py` 的 `MAP`；VRM 規格同樣沒有 [手腳研究 S10]）。

| | **A 葉子扭轉骨＋約束（推薦）** | B 前臂改成 B-Bone 分段 | C 拉長權重＋DQS 擴到前臂 | D 套動作時把扭轉分給前臂（Unity 式） |
| --- | --- | --- | --- | --- |
| 做法 | 每隻前臂加 2 根葉子骨，約束抄手掌扭轉的 1/3、2/3；前臂權重沿長度分給它們 | `LowerArm` 切 6～8 段，尾端把手連到 `Hand`，讓扭轉沿前臂漸進 | 前臂下半段權重改成 `LowerArm`→`Hand` 漸變，`HAND_DQS` 擴到前臂 | `mixamo_retarget` 把手掌的扭轉一半轉給 `LowerArm`（手掌方向不變） |
| 誰的事 | 身體端 | 身體端 | 身體端 | **動畫端**（共用程式，VRoid 角色也受影響） |
| 加骨頭 | 加 4 根（左右各 2） | 不加 | 不加 | 不加 |
| LBS 下不塌 | ✅（150° 約 0.82） | 理論上可以，**要實測** | ❌，要靠 DQS | 部分（各分一半，150° 約 0.63） |
| 衣服自動一致 | ✅ 衣服抄權重就抄到扭轉骨群組 | ✅ 同一根骨頭、同一份權重 | ❌ 衣服是 LBS，**身體不細、袖子變細**，袖口穿模 | ✅ |
| 手腕彎時前臂會不會跟著彎 | 不會（只抄扭轉） | 不會（尾端緩和要設 0） | **會**：權重拉長後，彎手腕整段前臂也跟著彎 | 不會 |
| 套動作要不要改 | 不用（第 1.6 節） | 不用 | 不用 | 要改，且違反「Mixamo 原樣」原則 |
| 不確定處 | 約束選項名稱要在 5.2 讀一次確認 | 手冊沒寫「尾端把手的扭轉會不會傳進 B-Bone」[B5]；和 Preserve Volume 疊加沒查到 | DQS 鼓脹 | 手肘處會出現扭紋（真人手肘不扭） |

**推薦 A 的理由**：

- 和 Unreal、ZEPETO 官方同一種結構。
- 只動身體端，套動作程式不用改。
- 服裝抄權重自動跟上。
- LBS 下就成立，所以不依賴 DQS。

B 可以當 1 小時的對照實驗：如果實測扭轉真的會沿 B-Bone 漸進，就是「不加骨頭」的更省版本。

### 1.5 建議做法（Blender 怎麼實作）

**骨頭**（加在 `bones_layout()`／`build_armature()`）：

| 設定 | 值 | 白話 |
| --- | --- | --- |
| 名字 | `J_Adj_L_LowerArmTwist1`、`J_Adj_L_LowerArmTwist2`（右手 `_R_`） | `J_Adj_` 是 VRoid「調整用骨頭」的慣例。**不要用 `J_Bip_` 開頭，也不要含 Hand／Thumb／Index／Middle／Ring／Little**（理由見第 1.6 節） |
| 父骨頭 | `J_Bip_L_LowerArm`，不連接（use_connect 關） | 葉子骨：底下不掛任何骨頭 |
| 位置 | 頭在前臂 1/3、2/3 處（手肘算 0、手腕算 1）；尾巴沿前臂方向，長約前臂 1/4 | 前臂長 `fa` ≈ 20.5 cm（`_tplF3.work`） |
| roll | 和 `LowerArm` 一樣（現行全部 roll＝0） | 自己的 Y 軸＝前臂長軸 |
| use_deform | 自動權重（`ARMATURE_AUTO`）時先關，`tpl_weights` 之後打開再寫權重 | 不讓自動權重亂分（手腳研究 [W9] 同一招） |

**約束**（每根扭轉骨一個 Transformation 約束）：

| 屬性 | 值 | 白話 |
| --- | --- | --- |
| type | `TRANSFORM` | 「從目標讀一種變換，換算後寫到自己身上」 |
| target／subtarget | 身體骨架／`J_Bip_L_Hand` | 讀手掌 |
| target_space／owner_space | `LOCAL`／`LOCAL` | 讀「手掌相對前臂轉了多少」，寫在自己的座標裡 |
| map_from | `ROTATION` | |
| from_rotation_mode | `SWING_TWIST_Y` | **只取繞長軸的扭轉**，手腕彎多少不算進來 [B1][B2] |
| from_min_y_rot／from_max_y_rot | −π／+π | |
| map_to／map_to_y_from | `ROTATION`／`Y` | |
| to_min_y_rot／to_max_y_rot | −π·k／+π·k（Twist1：k＝1/3；Twist2：k＝2/3） | 照比例分 |
| X、Z 軸的 to 範圍 | 全部 0 | 只轉 Y |
| mix_mode_rot | `REPLACE` | 不管骨頭本身的姿勢值（動畫端烤成關鍵影格也無害） |

- ⚠️ `from_rotation_mode` 的選項名稱來自 API 文件引用的「Driver Target Rotation Mode Items」[B3]。照 Blender MCP 的規矩，**5.2 實作時先用 `bl_rna.properties["from_rotation_mode"].enum_items` 讀一次確認**。
- 如果沒有這個選項，就用社群做法 [I8]：每根扭轉骨配一根輔助骨，輔助骨用 Damped Track（−Y）把彎曲去掉，扭轉骨再用 Copy Rotation 只抄 Y、Local 對 Local、影響 k。
- 不要只用 Copy Rotation 抄 Y（Euler 單軸）：手腕又彎又扭時，Euler 拆出來的 Y 不是純扭轉，扭轉骨會跟著彎手腕亂晃 [I8]。

**權重**（新函式 `twist_weights(body)`，放在 `bind()` 裡 `tpl_weights` 之後、建 `HAND_DQS` 之前）：

- 對每個有 `LowerArm` 權重 w 的點，算它投影到前臂骨頭的位置 t（手肘 0、手腕 1）。
- 把 w 分出去（`Hand`、`UpperArm` 的權重不動）：

| t 範圍 | `LowerArm` | `Twist1` | `Twist2` |
| --- | --- | --- | --- |
| 0 ～ 1/3 | w·(1−3t) | w·3t | 0 |
| 1/3 ～ 2/3 | 0 | w·(2−3t) | w·(3t−1) |
| 2/3 ～ 手腕 | 0 | 0 | w |

- 每點骨頭數：手肘最多 3 根（上臂、前臂、Twist1），手腕最多 3 根（Twist2、手掌、拇指 1）。合乎 ZEPETO、Unity 的 4 根上限 [Z2]。
- **手模板那段前臂（前臂 60% 到手腕）也用同一個函式分**，所以接口環兩側同一個位置的權重一定一樣。手腳研究的 J3「接縫前後 100% `LowerArm`」要改成 J5「接縫兩側權重相同」（第 1.8 節）。
- `HAND_DQS` 是用名字挑手的骨頭（`bind()` 的 `hand_bones`），扭轉骨不會被挑進去。手腕那圈仍是一半 DQS，不用改。

**選配（第 0 步量到手肘處扭轉也很大才做）**：

- 手肘反扭骨 `J_Adj_L_LowerArmUntwist`：前臂的葉子骨、放在手肘到前臂 15% 處。約束讀 `LowerArm` 自己相對上臂的扭轉，k＝−0.5。
- 上臂、大腿同理（Cascadeur 的 Untwist、Unreal 的 upperarm_twist [I3][I2]）。先不做。

### 1.6 會不會影響 `mixamo_retarget` 套動作

**不會，只要守三條規矩。**

| 程式裡的事實 | 所以 |
| --- | --- |
| `MAP` 只列 VRoid 骨頭和 Mixamo 骨頭的對應；`Target.keys` 只收 `MAP` 裡的骨頭 | 新骨頭不會被讀、也不會被寫 |
| `basis_from_world` 只算 `keys`；`apply_pose(reset=True)` 會把**所有**骨頭的姿勢值歸零 | 扭轉骨每格都從 0 開始，轉多少完全由約束算 |
| `basis_from_world` 遇到「中間有沒對應的骨頭」時**假設它不動**（程式註解：「中間有沒對應的骨頭（例：Root）：視為不動」） | **規矩 1：扭轉骨不能插在 `LowerArm` 和 `Hand` 中間。** 插進去的話，約束轉了它，手會被多轉一次；而且約束讀 `Hand`、`Hand` 又是它的子骨頭，會形成循環相依 |
| `fix_arm_twist`（IK 用）把扭轉一半給前臂、一半留在手腕 | 扭轉骨讀的是「手掌相對前臂」，所以留在手腕那一半照樣分攤；給前臂那一半出現在手肘，若要處理就加選配的反扭骨 |

**規矩 2：名字不要 `J_Bip_` 開頭。** 有幾支程式用這個開頭挑「身體骨頭」：

- `zanim_sample.bake` 會把所有 `J_Bip_*` 烤成關鍵影格：多餘，但無害。
- `check_lib.py`、`render_actions.py` 逐格比較 `J_Bip*` 轉角：扭轉骨轉得快，可能被當成跳格。
- `body_build.tpl_weights` 清權重時只挑 `J_Bip` 群組。

**規矩 3：名字不要含 `Hand`、`Thumb`、`Index`、`Middle`、`Ring`、`Little`。** `bind()` 用這幾個字串挑 `HAND_DQS` 的骨頭，名字撞到會把前臂也開成 DQS。

**驗證**：H11（同一格 Mixamo 動作手指方向差 ≤ 2°）、`finger_compare.py` 結果要和加骨頭前完全一樣（第 1.8 節 W7）。

### 1.7 對動畫端、服裝端的影響

| 對象 | 影響 | 要做的事 |
| --- | --- | --- |
| **服裝** | `transfer_weights` 只建「名字是骨頭」的群組，扭轉骨是骨頭，所以會一起抄。袖子跟身體一樣分段扭。`limit_total(4)` 不受影響。`NO_ARM`（平口上緣用）是比對 `LowerArm` 字串，會同時抓到扭轉骨，行為一致 | **舊衣服要重長一次**：沒重長的袖子仍是手腕集中扭，身體不細了、袖子還是細，看起來會更怪。ZEPETO 官方也要求衣服綁骨時包含扭轉骨 [Z2] |
| **動畫** | 套動作、手勢（`thumb_contact`、`gesture_overrides`）都不受影響 | 已定案鏡頭的手腕近照要重看一次，樣張（`samples.json`）重渲 |
| **出廠** | 骨架多了骨頭＝身體新版本 | `RELEASE.json` 的 changes 寫明「新增 4 根扭轉骨（約束驅動，動畫資料不用改）；衣服要重長」。新娘 v3 被開場片 B 鎖定，換版要經導演排程 |

### 1.8 怎麼驗證

| # | 項目 | 姿勢 | 量什麼 | 門檻（建議值） |
| --- | --- | --- | --- | --- |
| W1 | 扭轉截面積 | 手腕打直，手掌繞前臂轉 −30°、+80°、+150° | 前臂 t＝0.2～1.0 每 0.1 切一刀，取最小截面積比 | +80°：≥ 0.90；+150°：≥ 0.78；−30°：≥ 0.95 |
| W2 | 扭轉分布寬度 | +150° | 靜止時前臂最上面那條點，扭轉後每圈轉了幾度；「最陡 2 cm 內完成的扭轉 ÷ 總扭轉」 | ≤ 0.40（現在估計接近 1.0） |
| W3 | 手腕彎曲 | 往掌心 70°、往手背 60°、往拇指側 20°、往小指側 30°（手腳研究 H10） | 手腕平分面截面積、內側擠壓深度 | 0.85～1.10；擠壓 ≤ 手腕厚度 × 0.4 |
| W4 | 只彎不扭時扭轉骨不動 | 同 W3 | 扭轉骨的轉角 | ≤ 2°（驗證「擺動＋扭轉」拆對了） |
| W5 | 組合 | 往掌心 60°＋扭 +90°（看手機） | W1＋W3 | 截面積 ≥ 0.85 |
| W6 | 翻轉 | 扭 +170°、+180° 掃過去 | 相鄰兩格扭轉骨轉角跳動 | ≤ 30°（抓 ±180° 附近的翻面） |
| W7 | 套動作不變 | Mixamo 第 0 格、靜止 | H11、`rest_fingers`；靜止時扭轉骨姿勢＝靜止 | 和加骨頭前完全一樣；≤ 0.01° |
| W8 | Mixamo 抽格 | `texting_standing`、`thumbs_up`、`open_door`、`waving_one_hand`、`push_heavy`、`sitting_drinking` 各取扭轉最大、手腕最彎的格 | W1、W3 | 同上 |
| J5 | 接縫權重 | 靜止 | 前臂接口環兩側同位置的權重差；扭 +150° 時 `ring_check` | ≤ 0.01；距離 0 |
| G4 | 骨頭數 | 靜止 | 每點骨頭數 | ≤ 4 |

- 近照：`hand_probe.py` 加「手腕扭 0／80／150°」的手背、側面、手心三張。
- 審看頁放新舊對照。

### 1.9 優先順序

**高（第 2 順位，排在權重檢查之後）**：

- 手每一鏡都看得到，新娘手臂外露。
- 目前完全沒測，估算在手心朝上時塌到 4 成。
- 改動只在身體端。

---

## 2. 三種變形方式比較：LBS、LBS＋保留體積、LBS＋修正平滑

### 2.1 白話比較

| | LBS（一般） | LBS＋Preserve Volume（DQS） | LBS＋Corrective Smooth（Delta Mush） |
| --- | --- | --- | --- |
| 原理 | 骨頭的搬移照權重平均 | 改用對偶四元數平均「轉動」 | 先用 LBS 變形，再抹平，最後把靜止時的細節加回去 |
| 彎曲 | 內側塌，扁掉 | 不塌，但**會鼓**：Softimage 文件說膝蓋、手肘彎曲會「不自然凸出」[I5]；論文稱為「關節鼓脹」[K2][K3] | 摺痕變圓順、減少擠壓 [B8] |
| 扭轉 | **糖果紙**（會細）[I4] | 不細 [K1][I5] | 有改善但不會完全消失（它只是抹平，不知道「扭轉」這件事）。**推測，沒查到量化資料** |
| 其他毛病 | — | 接近 180° 會突然跳（Blender 手冊）[B7]；轉超過一圈不可預測 [I5] | 會把刻意的稜角（指節、膝蓋骨形狀）抹軟；靠很近的面（握拳）不知道彼此，可能更陷或更開 |
| Blender 設定 | Armature 修改器 | Armature 的 Preserve Volume；用 Multi Modifier＋點群組只套局部 [B7] | Corrective Smooth 修改器，放在 Armature 之後 [B8] |
| 效能 | 最快 | 小幅增加；兩個 Armature 修改器＝骨架變形算兩次 | 每格要做「重複次數 × 點數」的平滑；**官方沒給數字，要實測** |
| 和服裝一致嗎 | ✅ 服裝也是 LBS | ❌ 服裝沒開，身體和衣服變形不同 | ❌ 除非衣服也加同樣的修改器（`garment_lib.corrective_smooth()` 已有，選用） |

### 2.2 Blender 5.x 的實際設定與坑

**Preserve Volume（現行用在手）**：

- 現行做法：第二個 Armature 修改器開 Preserve Volume＋Multi Modifier，點群組 `HAND_DQS`。
- Multi Modifier 的意思：兩個修改器都從「沒變形的網格」算，再依點群組權重混合兩個結果 [B7]。
- 坑 1：`HAND_DQS` 的權重是「手骨頭權重的總和」，手腕那圈只有 0.5，等於一半 DQS。
- 坑 2：專案已實測全身開會讓肩膀、屁股鼓（`checklist.md`）。

**Corrective Smooth**：

| 選項 | 建議 | 為什麼 |
| --- | --- | --- |
| Rest Source（靜止來源） | `ORCO`（原始座標） | 我們的修改器順序是 Armature → Armature_HandVolume →（服裝加的）HideUnderOutfit 遮罩。新加的 Corrective Smooth 放在兩個 Armature 之後、遮罩之前，點數不變，ORCO 就能用。前面若有細分、遮罩這類「會改點數」的修改器，就要改用 Bind [B8] |
| Smooth Type | Length Weight | 依鄰點距離加權，比較能保留原形 [B8]；`garment_lib.corrective_smooth` 也是這樣設 |
| Repeat／Factor | 5～10 次／0.5 起試 | 太多次會抹掉指節形狀 |
| Scale | 1.0 起，塌的地方試 1.02～1.05 | 用來補體積流失 [B8] |
| Vertex Group | 只套要修的部位，邊緣漸變 | 硬邊會在交界出現一條明暗；**手指用的群組要在手腕前 2 cm 淡到 0**，袖口才不受影響 |

### 2.3 業界怎麼用

| 場合 | 主流 | 依據 |
| --- | --- | --- |
| 遊戲、即時 | **LBS＋扭轉骨／輔助骨＋修正形態鍵**。Unity 沒有內建 DQS（社群說法）[K7]；Unreal 只支援 LBS，DQS 要靠第三方外掛 [I7][K8] | 引擎 GPU 蒙皮的預設 |
| 遊戲研究 | Delta Mush 每格要反覆抹平，即時引擎用不起；EA SEED 2019 年提出 Direct Delta Mush，把它改成可以並行的單點計算 [K5] | 說明即時引擎原本不用 Delta Mush |
| 影視、離線渲染 | Delta Mush 很普遍（Rhythm & Hues 2010 年起所有角色都用）（手腳研究 [D5]）；Maya 可以用權重把 LBS 和 DQS 混在一起 [I4]；Disney 也把 DQS 和 LBS 混用 [K4] | 品質優先、可以多花運算 |
| 混合 | 「容易扭轉的地方用 DQS、其他地方 LBS」是常見做法 [I5] | Softimage 文件 |

### 2.4 適合我們的選擇

我們的情況：離線渲染、卡通風、動畫全來自 Mixamo、衣服從身體抄權重、身體軀幹每副拓撲都不同（體素重建＋減面）。

| 部位 | 建議 | 理由 |
| --- | --- | --- |
| 全身底子 | **LBS** | 衣服也是 LBS，兩邊一致；結果可預測 |
| 前臂扭轉 | **LBS＋扭轉骨**（第 1 節），不擴大 DQS | 擴大 DQS 會讓袖口穿模（第 1.4 節 C） |
| 手指、手掌 | **先維持現行 LBS＋DQS**，做一次三方比較再決定 | 現行檢查全過；但截面積最大 1.08～1.19 就是 DQS 的鼓。修正平滑可能不鼓，但會改變手勢接觸距離 |
| 手肘、膝蓋 | LBS；ROM 測不過再加**修正平滑（只套關節帶）** | 軀幹拓撲每副不同，修正形態鍵每副都要重做；修正平滑和拓撲無關 |
| 肩、髖 | LBS（不要 DQS） | 已實測 DQS 會鼓 |
| 手、腳模板 | 之後可以加修正形態鍵（手腳研究 [D6]） | 拓撲固定，可以做一次、重複用 |

### 2.5 比較時該量哪些數字

在 `bind()` 加一個開關 `DEFORM=lbs|dqs|cs`，三種各做一副身體，跑同一套檢查：

| # | 量什麼 | 姿勢 | 好的方向 | 現有工具 |
| --- | --- | --- | --- | --- |
| V1 | 截面積保留率（MCP、PIP、DIP、手腕） | 四指 0～110° 掃描、握拳、W3 | 0.90～1.10 越接近 1 越好 | `section_area`（目前只有 PIP、DIP，要加 MCP、手腕） |
| V2 | 鼓脹：關節帶的點離骨頭線最遠距離 ÷ 靜止 | 同上 | ≤ 1.10 | 新加 |
| V3 | 內側擠壓、翻面、壓扁、三角形交叉 | 9 個手勢＋掃描 | 越少越好 | `penetration_v2` |
| V4 | 手勢接觸距離 | 比讚、比 YA、握拳 | 0～1 mm | `thumb_contact`、`gesture_overrides` 是照現行 DQS 校的，**換方式要重校** |
| V5 | 套 Mixamo 方向 | 第 0 格 | ≤ 2° | H11（三種方式應該一樣，當健全檢查） |
| V6 | 每格評估時間 | 全身，100 格 | 記錄 ms | 新加：`eval_mesh()` 前後計時 |
| V7 | 袖口一致性 | W1、W3 姿勢穿一件長袖 | 袖口帶身體皮膚到袖子內面的最小距離 ≥ 0（不穿出） | 新加，借服裝的 `outfit_build` |
| V8 | 可重現 | 同一副身體算兩次 | 完全一樣 | 指紋 |

決定規則（建議）：V1、V3 不輸現行，V2 明顯較好，V4 重校後過關，V7 不變差，才換。

### 2.6 對動畫端、服裝端的影響

- **換手指變形方式**：比讚、比 YA 的接觸距離會變，`thumb_contact`（`THC`）與比讚彎度（`TUF`）要重掃；已定案鏡頭的手勢近照要重看。
- **任何不是 LBS 的方式**：衣服要加同樣設定才一致。手套、戒指這類吃手部權重的配件，要麼抄 `HAND_DQS`（現在刻意不抄），要麼也加修正平滑。這要通知服裝端。

### 2.7 優先順序

**中（第 4 順位）**。現行手指檢查全過，這是「能不能更好」的比較，不是救火。但要在新娘新版出廠前做完，免得出廠後又改手勢校正。

---

## 3. 手指張開、併攏的活動範圍，與拇指對掌

### 3.1 真人範圍

| 動作 | 真人範圍 | 來源 |
| --- | --- | --- |
| 手指外展（張開） | 20～30°（量法以中指為基準） | [R1][R9] |
| 指根往手背翹 | 30～45° | [R1] |
| 拇指外展 | 60～70° | [R1] |
| 拇指對掌 | 拇指碰得到小指；Kapandji 0～10 分：1～2 分碰食指側面，3～6 分碰食指到小指的指尖，7～9 分沿小指往下，10 分碰掌心遠端橫紋 | [R1][R3] |

**Mixamo 動作裡手指實際張多開：查不到，要在第 0 步量。**

### 3.2 建議做法（Blender 怎麼實作）

- 全部用現有的 `mr.finger_pose(curl, spread, thumb_to)` 擺姿勢。spread 的正負號：往拇指側為正，例如比 YA 是食指 +9、中指 −9。
- 不用改身體，只加檢查。
- 檢查寫在 `body_checks.py`（新段落 `spread`），近照寫在 `hand_probe.py`。

| # | 姿勢 | spread（度，往拇指側為正） | 量什麼 |
| --- | --- | --- | --- |
| S1 | 靜止 | 0 | 相鄰兩指皮膚最小距離；三角形交叉數 |
| S2 | 四指張開 | 食指 +20、中指 0、無名指 −15、小指 −25（若第 0 步量到更大，取「最大值＋5°」） | 指蹼帶的面積比、邊長拉伸、翻面；指根（MCP）截面積 |
| S3 | 併攏擠壓 | 食指 −5、無名指 +5、小指 +8 | 不同手指互陷深度 |
| S4 | 只張一根 | 只有食指 +20 | 中指那一區（指蹼帶除外）被拖動的距離。**這也是權重污染的功能測試**（第 4 節） |
| S5 | 對掌 | `thumb_to`：食指尖（捏＝OK 手勢＝交換戒指）、小指尖、小指根 | 接觸距離、拇指對手掌互陷、拇指根肉墊的壓扁與翻面 |

指蹼帶的定義：指根連線往掌心算起，沿網格走 0.5 個手指直徑以內的點（用量法 v2 的 `geo_near`）。

### 3.3 怎麼驗證（門檻）

| # | 門檻（建議值） |
| --- | --- |
| S1 | 距離 ≥ 0.2 mm（靜止時不能已經相交）；三角形交叉 0 |
| S2 | 指蹼帶面積比 ≤ 2.0、邊長拉伸 ≤ 1.6、翻面 0；MCP 截面積 0.90～1.10 |
| S3 | 互陷 ≤ 1 mm（沿用 H4，接觸可以、穿過不行） |
| S4 | 被拖動 ≤ 0.3 mm |
| S5 | 接觸 0～1 mm；互陷 ≤ 1 mm；肉墊壓扁、翻面 0 |

### 3.4 對動畫端、服裝端的影響

- **動畫**：沒有影響，只是多知道「手指能張到幾度不出事」。若 S2 只在超過 Mixamo 最大值時才壞，就不用修。
- **服裝**：沒有影響（目前沒有手套）。

### 3.5 優先順序

**中低（第 5 順位）**。S1～S4 便宜，可以和第 4、5 節同一次跑。S5 和婚禮有關（交換戒指、拿捧花的捏法），排在 S1～S4 之後。

---

## 4. 權重跨指污染

### 4.1 定義

現行 `v2ref.weights.cross_finger` 只看「第 2、3 節的點有沒有吃到別根手指（含 `Hand`）> 0.01」，量到 4 點、不擋出廠。建議擴大成下面三類，加上數量與總和：

| # | 類別 | 定義 | 會怎樣 |
| --- | --- | --- | --- |
| G1 | 跨指 | 手指 A 的點（靜止時離 A 某節骨頭最近，用 `region_of`），吃到手指 B 任一骨頭 > 0.01。**例外**：指蹼帶（第 3.2 節）可以吃相鄰手指的第 1 節，不能吃第 2、3 節 | 彎中指，食指的皮膚被拉歪；握拳時兩指之間出現尖角 |
| G2 | 越節 | 第 2、3 節的點吃到 `Hand`；第 3 節吃到第 1 節 | 彎手指時，指尖被手掌「拉住」，像橡皮筋 |
| G3 | 跨肢、左右 | 點吃到另一側（L↔R）的骨頭 > 0.01（正中線兩側 0.3 倍局部半徑的帶除外）；或吃到某根骨頭，但那根骨頭離這點超過「2.5 倍該處肢體半徑」 | 抬左腿時右大腿內側被拉過去（自動權重在胯下的老毛病）；手臂點吃到軀幹遠處 |
| G4 | 數量 | 每點有權重的骨頭數 | 超過 4 根：ZEPETO、Unity 上限是 4 [Z2]；服裝 `limit_total(4)` 會砍掉，身體和衣服不一致 |
| G5 | 總和 | 每點權重總和 | Blender 會自己除以總和、不影響變形（`body_checks` 註解）；但服裝抄過去後會正規化，**兩邊比例不同就不一致** |
| G6 | 碎權重 | 0 < 權重 < 0.01 的項目數 | 看不出來，但會讓 G4 超標、讓指紋在小數點跳 |

### 4.2 怎麼檢查

| # | 做法 | 門檻（建議值） |
| --- | --- | --- |
| G1～G3 | 擴大 `region_of`：從「只有手的骨頭」擴到所有會變形的骨頭（`SEGS` 加入四肢、軀幹）；每點列出不在允許表上的骨頭權重 | 0 點（指蹼帶例外照表） |
| G4 | 數每點 > 1e-4 的骨頭數 | ≤ 4 |
| G5 | 總和 | 1 ± 0.001 |
| G6 | 數碎權重 | 0 |
| G7 | **功能測試**：「動一根看鄰居」。每次只轉一根骨頭（手指各節 60°、大腿外展 30°、上臂 45°），量「不在那根骨頭允許範圍內」的點最大位移 | ≤ 0.3 mm。這會抓到 0.01 以下、G1～G3 數不到的小權重 |

### 4.3 怎麼修（Blender 實作）

在 `body_build.py` 加 `clean_weights(body)`，放在 `tpl_weights`、`twist_weights` 之後、建 `HAND_DQS` 之前：

1. **允許表**：每個部位（靜止位置決定）列可以有權重的骨頭。例：

   | 部位 | 允許的骨頭 |
   | --- | --- |
   | 食指第 2 節 | 食指 1、2、3 |
   | 手掌 | `Hand`、四指第 1 節（只在指根帶）、拇指 1、Twist2（只在手腕帶） |
   | 左大腿 | 骨盆、左大腿、左小腿（膝帶）、脊椎（胯上帶） |

2. 不在表上的權重直接清掉（Python 迴圈，同 `tpl_weights` 的寫法）。
3. `vertex_group_clean(limit=0.01)`：清碎權重 [B9]。
4. `vertex_group_limit_total(limit=4)`：每點最多 4 根 [B9]。
5. `vertex_group_normalize_all(lock_active=False)`：總和變 1 [B9]。

服裝的 `transfer_weights` 已經做第 3～5 步，身體自己做完，兩邊就一致。

**注意**：

- 手模板的權重本來就寫在籠子點上，污染很少。主要風險在**自動權重的軀幹、腿**（胯下左右互吃），以及細分時指蹼那面把兩指第 1 節混在一起（這是允許的）。
- 平滑權重（Smooth）會把鄰近骨頭抹進來，**平滑一定要配允許表一起用**，平滑完再清一次。

### 4.4 對動畫端、服裝端的影響

- **服裝**：權重變了要重長（抄新權重）；通常變好，不會變差。
- **動畫**：手勢接觸可能微變，要重跑 `gestures` 檢查；套動作不受影響。
- **指紋**：手、腳指紋會變一次，要重定基準。

### 4.5 優先順序

**高（第 1 順位）**。便宜（半天到一天）。第 1 節扭轉骨的權重和第 5 節 ROM 都建立在「權重乾淨」上；G3 也直接關係到第 6 節併腳。

---

## 5. 一般動作下關節不塌：ROM 測試

### 5.1 業界怎麼設計 ROM 測試

| 做法 | 內容 | 來源 |
| --- | --- | --- |
| 逐關節掃描 | 每個可動的軸依序打「中立 → 正值 → 中立 → 負值 → 中立」的關鍵影格，各關節錯開時間，一支片掃完全身（Maya 工具 defQA） | [R7] |
| 看什麼 | 綁骨、權重、關節活動範圍 | [R7] |
| 實際動作 | Blender Studio 先做走路循環，再做更複雜的身體力學動作；手、臉另做姿勢庫 | [R8] |
| 手部 | 要測握拳、張開（手腳研究 [T7][R8]） | — |
| 公開的量化門檻 | **查不到**。defQA、Blender Studio 都是目視為主 | — |

我們的做法：照 defQA 的節奏用程式產生掃描姿勢（不用下載 ROM 檔）。每 10° 一格，量數字。再從 Mixamo 片自動挑「這個關節最彎的那一格」補實際動作。

### 5.2 要測哪些關節、幾度

| 關節（骨頭） | 真人範圍 | 動畫常用 | 建議測試角度（第 0 步量完再調） |
| --- | --- | --- | --- |
| 肩（`UpperArm`） | — | **手臂放下**（T 字往下 80～90°）最常見；揮手、舉手過頭 | 往下 45／85°、往上 80°、往前 90°、往後 40°、扭 ±60° |
| 手肘（`LowerArm`） | 彎 140～150° [R4] | 喝東西、看手機 100～140° | 0／45／90／120／145° |
| 前臂扭轉、手腕 | 見第 1 節 | — | 第 1.8 節 W1～W6 |
| 髖（`UpperLeg`） | 屈 100～130°、外展 40～50°、內收 20～30° [R4] | 坐 90°、撿東西 110～120° | 屈 45／90／120°、伸 20°、外展 40°、內收 15°、扭 ±40° |
| 膝（`LowerLeg`） | 彎 130～150° [R4] | 走路擺盪期 60～65°（擺盪期＝腳離地往前擺的那段）[R5]；坐 90°；蹲、跪 120～150° | 0／30／60／90／120／150° |
| 腳踝（`Foot`） | 往上 10～20°、往下 45～50°（手腳研究 [R3][R5]） | 走路腳跟離地時往下約 20° [R5]；蹲需要往上約 15° 以上 [R6] | 往上 20／30°、往下 45／50°、往內 20°、往外 15° |
| 腳趾（`ToeBase`） | 大拇趾翹 70～90°（手腳研究 [R4]） | 走路蹬地、跪姿腳趾撐地 | 往上 40／70／90°、往下 30° |

### 5.3 量什麼、門檻

把現有手指的量法推廣到四肢：

- 部位＝靜止時離哪一節骨頭最近。
- 截面在兩節骨頭的角平分面上切。
- 同一肢體上下兩節之間的擠壓算「關節內側」，不算穿插。

| # | 指標 | 量法 | 門檻（建議值） |
| --- | --- | --- | --- |
| L1 | 截面積保留率 | 角平分面切口面積 ÷ 靜止（`section_area` 推廣到四肢，半徑改用該處肢體半徑） | ≤ 90°：0.85～1.10；120°：≥ 0.75；≥ 140° 只看 L3 |
| L2 | 彎曲面厚度 | 在彎曲平面上，內側到外側的距離 ÷ 靜止（同手指的 `bend`） | 90°：≥ 0.80 |
| L3 | 內側接觸與擠壓 | 同一肢體上下兩節（小腿↔大腿、前臂↔上臂）互陷深度 | ≥ 120° 時允許接觸；互陷 ≤ 0.3 × 局部半徑；翻面只出現在摺痕帶 |
| L4 | 不同部位互穿 | 手臂↔軀幹、腿↔腿、手↔頭 | ≤ 1 mm（沿用 H4） |
| L5 | 外側拉伸 | 膝蓋、手肘尖那一帶的邊長比、面積比 | 邊長 ≤ 1.6、面積 ≤ 2.5 |
| L6 | 壓扁、翻面 | 摺痕帶以外 | 0 |
| L7 | 掃描連續 | 每 10° 一格，相鄰兩格同一指標的跳動 | 截面積比跳動 ≤ 0.05（抓「突然塌一下」） |
| L8 | Mixamo 抽格 | 每支測試片自動挑該關節最彎的格 | L1～L6 |

> **為什麼 120° 以上門檻放寬**：LBS 在兩根骨頭各一半權重的那圈，彎曲方向會縮成 cos(θ/2)，90° 約 0.71、120° 約 0.50（理想化估算）。真人深蹲時大腿和小腿也會壓在一起。所以 ≥ 120° 改看「接觸得合不合理」，不硬要截面積。實際門檻要等第 0 步量完現況再定。

### 5.4 Mixamo 測試片

**已下載、可以直接用**（`D:/render-work/mixamo/raw/`）：

| 片 | 主要測什麼 |
| --- | --- |
| `female_walk`、`male_standard_walk` | 膝 60～65°、腳踝往下、腳趾蹬地 |
| `female_run`、`male_run`、`run_fast_stop` | 膝深彎、腳踝往上往下 |
| `crouch_idle` | 膝、髖深彎、腳踝往上 |
| `kneeling_idle` | 膝 120～150°、腳背或腳趾撐地 |
| `sitting_idle`、`sitting_drinking`、`sitting_talking`、`seated_table_idle` | 髖、膝 90°；手肘最彎（喝東西） |
| `picking_up`、`bow_formal` | 髖深屈、脊椎 |
| `entering_car` | 髖、膝不對稱的組合 |
| `swing_charleston`、`booty_hiphop` | 膝、腳踝往內往外、全身扭轉 |
| `waving_one_hand`、`waving_both_hands` | 肩舉高、手肘、前臂扭轉 |
| `texting_standing`、`walk_texting` | 手肘 100～120°、手心朝上（**前臂扭轉最佳測試片**） |
| `thumbs_up`、`sitting_thumbsup`、`open_door` | 前臂扭轉 |
| `push_heavy`、`push_forward` | 手腕往手背翹 |
| `standing_idle`、`female_idle`、`happy_idle`、`breathing_idle` | 站距、腳底（第 6 節） |

**建議補下載**（名字是常見說法，**查不到 Mixamo 官方目錄，要在 Mixamo 搜尋框確認**；有第三方轉檔用過「Air Squat」這個名字 [M2]）：

- 深蹲（Squat／Air Squat）
- 跪下過程（Kneeling Down）
- 開合跳（Jumping Jacks：肩舉到頂＋腿外展）
- 拍手、雙手合十（Clapping、Praying：H9 雙手合十）
- 聳肩、攤手（Shrugging：手心朝上）
- 伏地挺身或爬行（手腕往手背 90° 撐地）

### 5.5 建議做法（Blender 實作）

- `body_checks.py` 新增 `limbs` 段：
  - 部位標記推廣到四肢（同第 4.2 節的 `SEGS`）。
  - 截面積函式改成可指定兩根骨頭與半徑。
  - 掃描表照第 5.2 節。
  - Mixamo 抽格用 `mr.read_fbx`＋`mr.retarget`＋每格算關節角，挑最大的。
- 新增 `scripts/limb_probe.py`：手肘、膝蓋、腳踝、肩在各測試角度的側面、內側近照。另外輸出一支低畫質掃描短片（照 defQA 節奏），放進審看頁。
- **測不過時的修法，依代價排序**：
  1. **權重過渡寬度**：自動權重在手肘、膝蓋的過渡可能太窄。比照手指標準 0.6～1.2 倍肢體直徑（手腳研究 H7），用「依位置算」的方式蓋掉（同 `tpl_weights`）。
  2. **關節帶修正平滑**：只套手肘、膝蓋前後一個直徑的帶，邊緣漸變（第 2.2 節）。
  3. **半轉輔助骨**：膝蓋、手肘各加一根葉子骨，用 Copy Rotation 抄下一節轉動的 50%，關節內外側的點分一部分給它，摺痕處等於「只轉一半」。規矩同第 1.6 節。這是常見的 helper joint 概念；本報告沒查到 Blender 專文，**要實測**。
  4. **修正形態鍵**：只適合拓撲固定的手腳模板（手腳研究 [D6]）；軀幹、手肘、膝蓋每副拓撲不同，不建議。

### 5.6 對動畫端、服裝端的影響

- **動畫**：檢查本身不影響。量出的極限（例如「膝蓋超過 140° 會穿插」）寫進出廠資料，分鏡展開時可以避開，或在那幾格擺腳。
- **服裝**：權重改了要重長。用了修正平滑的部位，褲子、袖子也要開 `corrective_smooth()`，否則褲管、袖子在關節處和身體不一致。身體在衣服下面的部分大多被 `hide_body` 藏起來，影響只在衣服邊緣。

### 5.7 優先順序

**中（第 3 順位）**。

- 先做手臂（肩、手肘）：新娘露手臂。
- 再做腿：膝蓋多被禮服、長褲蓋住。
- 腳踝、腳趾已有 `feet` 參考指標，這次補 L7、L8 即可。

---

## 6. 腳併攏站

### 6.1 現況估算（從 `_tplF3.work/build.json` 的參數算，不是量的）

| 數字 | 值 | 白話 |
| --- | --- | --- |
| 髖關節左右距中線 `hip_x` | 66 mm | 兩腳中心相距 13.2 cm；腳直直往下 |
| 腳踝 Skin 半徑 | 約 25 mm | 兩踝內側皮膚相距約 8 cm |
| 大腿根 Skin 半徑 | 68 mm | 比 66 mm 大，大腿根本來就在胯下貼在一起（胯下 0.556 m） |
| 每條腿要內收幾度兩踝才碰 | 約 **4.2°** | atan((66−25) ÷ (髖 646 − 踝 83 mm)) |
| 這時兩膝內側 | 約 **0.6 cm** | 膝蓋往內移 ≈ 312 mm × sin 4.2° ≈ 23 mm，膝半徑 40 mm |
| 長褲每條褲管比皮膚外擴 | 大腿 8 mm → 下段 18 mm（`trousers`：外擴＋厚度往內） | 兩條褲管在皮膚距離 < 16～36 mm 時就互撞 |
| 皮鞋比腳外擴 | 10～14 mm（`shoes`） | 兩隻鞋在皮膚距離 < 20～28 mm 時就互撞 |

**會怎樣**：

- 光腳、穿禮服（新娘）：併腳時膝蓋、大腿會碰到。正常的「接觸」可以，要量有沒有「穿過去」。
- 穿長褲（新郎）：**只要併腳，兩條褲管一定互撞**。這是衣服外擴的必然結果，不是身體的錯，但身體端要把數字交出去。

### 6.2 業界怎麼看站距

- **卡通、ZEPETO 的標準站距：查不到。**
- 自動綁骨服務都要求靜止姿勢「兩腿分開、有明顯空隙」，避免權重左右互吃 [M1]。這跟 G3 是同一件事。
- 我們的動畫站距由 Mixamo 決定，第 0 步量待機類片的兩踝距離，當作「常見站距」。

### 6.3 建議做法與驗證

**不改身體，只加檢查和交接數字。** 改 `hip_x` 或腿粗是骨架、外形變動，服裝、動畫全要重做；除非 F12 不過，否則不動。

| # | 項目 | 姿勢 | 量什麼 | 門檻（建議值） |
| --- | --- | --- | --- | --- |
| F10 | 靜止站距 | T 字靜止 | 兩腿在腳踝、小腿、膝、大腿各高度的皮膚最小距離 | 記錄（出廠資料） |
| F11 | 光腳併腳 | 兩條大腿各往內收，直到兩踝皮膚距離 ≤ 2 mm | 需要內收幾度；大腿、膝蓋左右互陷深度；胯下的翻面、壓扁 | 互陷 ≤ 1 mm（可接觸、不穿過）；胯下翻面、壓扁 0 |
| F12 | Mixamo 站姿 | 待機類 4 支片每一格 | 左右腿互陷 | ≤ 1 mm |
| F13 | 衣服留空 | F11 的掃描 | 「從站姿最多內收幾度，兩邊皮膚距離仍 ≥ 2 × 衣服外擴」：長褲用 16～36 mm、皮鞋 20～28 mm | 記錄，寫進出廠資料給服裝、動畫 |
| G3 | 左右權重 | 靜止 | 左腿點吃右腿骨頭（第 4 節） | 0 |

- 檢查寫在 `body_checks.py`（`feet` 段旁邊加 `stance`）。左右互陷用左腿面建 BVH、右腿點查最近距離，搭配量法 v2 的 `inside` 奇偶判斷。
- 近照用 `foot_probe.py` 加「併腳」的正面、背面、從下往上。

### 6.4 對動畫端、服裝端的影響

- **服裝**：拿到 F13 的數字後，長褲可以考慮「大腿內側少外擴一點」（服裝端的事）；鞋子併攏時互撞要接受或調鞋寬。
- **動畫**：分鏡寫「新郎併腳站」時要知道褲管會撞，可以改成小八字站，或請服裝端處理。新娘穿禮服不受影響。

### 6.5 優先順序

**低（第 5 順位，和第 3 節一起）**。半天就能做完，可以跟第 5 節 ROM 同一次跑；先給數字，修不修看服裝端。

---

## 7. 總表

| 項目 | 建議做法 | 要改哪個檔 | 預估工時 | 風險 |
| --- | --- | --- | --- | --- |
| 0 共同量測 | 新增唯讀統計：Mixamo 扭轉（手肘、手腕）、各關節最大角、張指、站距；現行身體基準 | 新增 `scripts/limb_survey.py` | 0.5 天 | 低（唯讀） |
| 1 前臂扭轉 | 左右各 2 根葉子扭轉骨（`J_Adj_*_LowerArmTwist1/2`），Transformation 約束抄手掌扭轉 1/3、2/3（擺動＋扭轉拆解）；前臂權重依位置分段；選配手肘反扭 | `body_build.py`（`bones_layout`、`build_armature`、`bind` 新增 `twist_weights`）；`body_checks.py`（W1～W8、J5）；`hand_probe.py`（手腕近照）；`zepeto-body-v2.md`、`checklist.md` | 1.5～2 天 | 中：骨架變動要出新版、衣服重長；約束選項名稱要先確認；扭 180° 附近可能翻 |
| 2 變形方式比較 | `bind()` 加 `DEFORM=lbs/dqs/cs` 開關，三副身體跑 V1～V8；全身維持 LBS，DQS 不擴大 | `body_build.py`（`bind`）；`body_checks.py`（V2、V6、V7） | 1 天 | 低（只比較）；真的換手指方式時，手勢校正 `THC`／`TUF` 要重掃（中） |
| 3 張指、併指、對掌 | 用 `finger_pose` 的 spread、`thumb_to` 加 S1～S5 姿勢 | `body_checks.py`（`spread` 段）；`hand_probe.py` | 0.5～1 天 | 低 |
| 4 權重污染 | 定義擴成 G1～G7；`clean_weights()`：允許表 → 清除 → clean 0.01 → 限 4 根 → 正規化；「動一根看鄰居」功能測試 | `body_checks.py`（擴大 `region_of`、`v2ref.weights` 升級）；`body_build.py`（新增 `clean_weights`） | 0.5～1 天 | 低～中：權重變了，指紋重定、衣服重長 |
| 5 四肢 ROM | 程式產生逐關節掃描＋Mixamo 自動挑格；L1～L8；測不過依序試權重過渡、關節帶修正平滑、半轉輔助骨 | `body_checks.py`（`limbs` 段）；新增 `scripts/limb_probe.py`；`body_page.py`（新區塊）；必要時 `body_build.py` | 1.5～2 天（不含修） | 中：門檻要校正；120° 以上「接觸／穿插」的分類要實測調 |
| 6 併腳 | 不改身體；量 F10～F13、G3，數字交服裝、動畫 | `body_checks.py`（`stance` 段）；`foot_probe.py`（併腳視角） | 0.5 天 | 低；若 F12 不過要改腿距＝骨架變動（高） |
| 合計 | | | **6～8 天** | |

---

## 8. 查不到或不確定的地方

| 項目 | 狀況 |
| --- | --- |
| ZEPETO 完整骨頭清單 | 官方頁只零散提到名字（第 1.3 節）；沒看到上臂、大腿扭轉骨。要下載 `creatorBaseSet` 才能確認 |
| ZEPETO 扭轉骨的位置、怎麼驅動 | 查不到。「小腿扭轉骨靠近腳踝」是從鞋子頁推測的 |
| Mixamo 動作的扭轉放在前臂還是手掌 | 查不到公開資料，第 0 步自己量 |
| Mixamo 動作目錄與名字 | 查不到官方目錄；第 5.4 節補下載的名字要在 Mixamo 搜尋確認 |
| Transformation 約束 `SWING_TWIST_Y` 的識別字 | API 文件只寫引用「Driver Target Rotation Mode Items」[B3]，手冊確認有「擺動＋扭轉」模式 [B1][B2]；5.2 要讀 enum 確認 |
| B-Bone 會不會從尾端把手讀到扭轉 | 手冊只說 Tangent 型把手看把手骨頭的方向、Roll 會沿分段內插 [B5]，沒明寫手的扭轉會傳進來；要實測 |
| DQS 和 B-Bone、修正平滑和 DQS 疊加的行為 | 沒查到 |
| 修正平滑的效能 | 手冊沒寫 [B8]；V6 自己量 |
| 修正平滑對扭轉的改善幅度 | 沒查到量化資料（第 2.1 節標推測） |
| 四肢 ROM 的業界量化門檻 | 查不到；defQA、Blender Studio 都是目視 [R7][R8]。第 5.3 節是建議值 |
| 卡通／ZEPETO 標準站距 | 查不到 |
| 人體活動範圍 | 各來源數字略有出入（例如肘彎 140 或 150°、旋前旋後 80 或 90°）[R1][R4]；本報告取常見範圍 |
| Unity、Unreal 有沒有內建 DQS | Unity 是論壇說法（沒有日期）[K7]；Unreal 是 Polycount 貼文（UE4，內容取自搜尋摘要）[I7]＋第三方外掛頁 [K8]，沒查到官方文件 |
| 第 1.1、5.3、6.1 節的數字 | 理想化幾何估算或用 Skin 半徑推算，不是量的；第 0 步量完要更新 |

---

## 9. 來源表

### ZEPETO 官方

- [Z1] 3D Rigging – Shoes（lowerLegTwist 與 _scale、建議選的關節）：https://docs.zepeto.me/studio-guide/3d-rigging-shoes
- [Z2] 3D Rigging – Clothing（lowerArm(Leg)Twist 與 _scale 讓手腕小腿平順、每點最多 4 根、hips 權重 0）：https://docs.zepeto.me/studio/docs/rigging_clothing
- [Z3] Rigging（scale 骨讓基本身體適應多種體型、權重放 scale 骨、扭轉骨不能刪、Blender 骨頭沿 Y 軸、最多 4 根）：https://docs.zepeto.me/studio-guide-n/rigging
- [Z4] Rigging, Masking（scale 骨管體型、base 骨管動作；spine／spine_scale；Transfer Weights By Name）：https://docs.zepeto.me/studio-guide/rigging-masking
- [Z5] Deformation Custom（只縮放 scale 骨；頭、手、腳例外；全身 0.3～1.35）：https://docs.zepeto.me/studio-guide/deformation-custom
- [Z6] Modeling basics（shoulder_L、upperArm_L 的 A 字站姿）：https://docs.zepeto.me/studio-guide/modeling-basics
- 特殊體型（upperLeg_L、hips）：https://docs.zepeto.me/studio/docs/rigging_special_body_blender

### 業界扭轉做法

- [I1] Unity HumanDescription.lowerArmTwist（預設 0.5，前臂扭轉手肘、手腕各半）：https://docs.unity3d.com/ScriptReference/HumanDescription-lowerArmTwist.html ；upperArmTwist：https://docs.unity3d.com/cn/2022.1/ScriptReference/HumanDescription-upperArmTwist.html
- [I2] Reallusion 回報（UE 骨架每段 2 根扭轉骨、都是葉子骨）：https://www.reallusion.com/FeedBackTracker/Issue/Inconsistent-twist-bone-hierarchy-in-Unreal-Engine-skeletons
- [I3] Cascadeur Twists and Untwists（強度 0.5＝抄 50%、上臂與大腿的反扭、UE5 Manny 例子）：https://cascadeur.com/help/rig/advanced_rigging/advanced_rigging_techniques/twist_bones
- [I4] Autodesk Maya Smooth skinning methods（LBS 糖果紙、DQS、權重混合）：https://help.autodesk.com/cloudhelp/ENU/MayaCRE-CharacterAnimation/files/GUID-630C335C-B63E-4F2E-A4A4-AEA1DD00B0D6.htm
- [I5] Autodesk Softimage Dual Quaternion Skinning（DQS 解扭轉、膝肘彎曲會凸出、可逐點混合）：https://download.autodesk.com/global/docs/softimage2014/en_us/files/idef_deforms_DualQuaternionSkinning.htm
- [I7] Polycount：Blender Preserve Volume 匯出 UE4 失效（只支援 LBS）（內容取自搜尋摘要）：https://polycount.com/discussion/comment/2681302
- [I8] Blender Artists「Forearm twist bug」（Damped Track 去彎曲＋Copy Rotation Y 0.5）：https://blenderartists.org/t/forearm-twist-bug/695187 ；Polycount 同類討論（Local 對 Local，搜尋摘要）：https://polycount.com/discussion/comment/2389827
- [I9] Blender Artists 糖果紙求助（真人前臂兩根骨頭負責扭轉、建議扭轉骨）：https://blenderartists.org/t/beginner-to-blender-and-require-help-please-candy-wrapper-deformation/1545879
- [I10] CG Cookie 社群（前臂扭轉的「氣球」變形用修正形態鍵）：https://cgcookie.com/community/3000-what-if-i-want-to-twist-the-arm-so-that-the-palm-of-the-hand-is-facing-outwards-i-played-around-with-weight-painting-a-lo

### Blender 官方

- [B1] Drivers Panel（Swing and X/Y/Z Twist；Damped Track＋Copy Transforms 拆解；Rotational Difference）：https://docs.blender.org/manual/en/4.1/animation/drivers/drivers_panel.html
- [B2] Transformation Constraint（Map From 的旋轉模式、Mix）：https://docs.blender.org/manual/en/latest/animation/constraints/transform/transformation.html
- [B3] API TransformConstraint（map_from、map_to_y_from、to_min_y_rot、mix_mode_rot 等）：https://docs.blender.org/api/current/bpy.types.TransformConstraint.html
- [B4] Copy Rotation Constraint（軸、Order、Mix、空間）：https://docs.blender.org/manual/en/latest/animation/constraints/transform/copy_rotation.html
- [B5] Bendy Bones（分段、Roll 內插、把手類型 Absolute／Tangent、Ease）：https://docs.blender.org/manual/en/latest/animation/armatures/bones/properties/bendy_bones.html
- [B6] Rigify Limbs（Limb Segments＝tweak 控制點、B-Bone Segments）：https://docs.blender.org/manual/en/dev/addons/rigify/rig_types/limbs.html
- [B7] Armature 修改器（Preserve Volume、接近 180° 跳動、Multi Modifier、Vertex Group）：https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html
- [B8] Corrective Smooth 修改器（Factor、Repeat、Scale、Smooth Type、Rest Source：Original／Bind）：https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/corrective_smooth.html
- [B9] 權重編輯工具（Normalize All、Clean、Limit Total、Smooth、Levels）：https://docs.blender.org/manual/en/latest/sculpt_paint/weight_paint/editing.html

### 蒙皮研究

- [K1] Kavan 等 Skinning with Dual Quaternions（解 LBS 的糖果紙、限制：轉超過半圈走捷徑）：https://users.cs.utah.edu/~ladislav/dq/ ；https://dcgi.fel.cvut.cz/en/publications/2007/kavan-i3d-sdq/
- [K2] Le & Hodgins 2016 Optimized Centers of Rotation（LBS 體積流失、DQS 關節鼓脹）：https://la.disneyresearch.com/wp-content/uploads/Real-time-Skeletal-Skinning-with-Optimized-Centers-of-Rotation-Paper.pdf ；報導：https://m.phys.org/news/2016-07-character-animation-technique-realistic-joints.html
- [K3] Bulging-free dual quaternion skinning（DQS 鼓脹與法線失真）：https://scholar.korea.ac.kr/handle/2021.sw.korea/98685
- [K4] Disney Animation：Enhanced Dual Quaternion Skinning for Production Use（DQS 和 LBS 混用）：https://disneyanimation.com/publications/enhanced-dual-quaternion-skinning-for-production-use
- [K5] EA SEED：Direct Delta Mush（Delta Mush 反覆抹平不適合即時引擎、改成可並行）：https://www.ea.com/seed/news/siggraph2019-direct-delta-mush
- [K6] Bittner 等 2019：Evaluation of Optimised Centres of Rotation Skinning：https://www.cg.cs.tu-bs.de/publications/bittner2019evaluation
- [K7] Unity 論壇：Unity and dual quaternion skinning（沒有內建 DQS，社群說法）：https://discussions.unity.com/t/unity-and-dual-quaternion-skinning/431001
- [K8] Fab：DualSkin Toolkit（UE5 第三方 DQS，LBS／DQS 逐點混合）：https://www.fab.com/listings/8a387dae-f33b-4ec2-a678-2412914024eb

### 活動範圍與測試

- [R1] Physiotutors：手腕與手的主動活動範圍（腕屈 80～90、腕伸 70～90、橈偏 15、尺偏 30～45、旋前旋後 90、指外展 20～30、拇指外展 60～70、對掌碰小指）：https://www.physiotutors.com/wiki/wrist-hand-active-range-of-motion/
- [R2] Eaton Hand：手部活動範圍表：https://eatonhand.com/clf/clf218.htm
- [R3] Kapandji score（拇指對掌 0～10 分的位置）：https://en.wikipedia.org/wiki/Kapandji_score
- [R4] WikEM：各關節活動範圍（肘彎 140、旋前旋後 80、髖屈 100、膝彎 150 等）：https://wikem.org/wiki/Range_of_motion_by_joint
- [R5] 正常步態：密蘇里大學講義（擺盪期膝彎到 65°）：https://medicine.missouri.edu/sites/default/files/pm-r/Normal_Gait.pdf ；Kaiser 步態摘要（腳跟離地時腳踝往下 20°）：https://scal-pt-residencyfellowship.kaiserpermanente.org/wp-content/uploads/2008-Resources/foot-region-docs/03GaitMechanics&DeviationsSummary.pdf
- [R6] 深蹲與腳踝：Journal of Human Kinetics（腳踝背屈與深蹲深度相關）：https://johk.pl/?p=3255 ；物理治療診所（約需 15°）：https://cbphysicaltherapy.com/are-your-ankles-affecting-your-squats/
- [R7] defQA（Maya 綁骨與 ROM 測試動畫產生器：中立→正→中立→負→中立）：https://github.com/zebraed/defQA
- [R8] Blender Studio：Animation Testing：https://studio.blender.org/tools/artist-guide/asset-creation/animation-testing
- [R9] 手部活動範圍評估（外展以中指為基準量）：https://arxiv.org/pdf/1903.06949

### 站姿與 Mixamo

- [M1] Kenney：用 Mixamo 綁骨（手臂張開、兩腿分開）：https://kenney.nl/knowledge-base/asset-forge/rigging-a-character-using-mixamo ；Adobe 社群（兩腿沒有空隙是常見錯誤原因）：https://community.adobe.com/t5/mixamo/t-pose/m-p/11546723
- [M2] 第三方 Mixamo 轉檔「Air Squat」（只證明名字存在，非 Mixamo 官方）：https://3dsale.gumroad.com/l/ezndg

### 專案內

- 手腳研究（方案 A、H1～H12、F1～F9、J1～J4、來源 [D*]／[W*]／[T*]）：`references/research-hands-feet.md`
- 現行做法與數字：`references/zepeto-body-v2.md`
- 身體端責任與分界：`references/checklist.md`
- 套動作程式：`.claude/skills/blender-motion-library/scripts/mixamo_retarget.py`
- 服裝抄權重、長褲、鞋子外擴：`.claude/skills/zepeto-clothing-generation-workflow/scripts/garment_lib.py`
