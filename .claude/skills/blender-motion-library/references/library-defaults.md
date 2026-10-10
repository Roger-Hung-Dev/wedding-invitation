# 預設資料庫

全部來自新娘專案（`.claude/docs/data/blender/projects/bride/`，成果頁 https://claude.ai/artifact/12T6gowAFGaBVvSUAawPfa ）。新專案直接沿用，不夠再擴充。

## 1. 手勢（`pose_lib.HANDS`）

預覽：`LIB/previews/hands_sheet.jpg`（上排掌心、下排手背：放鬆、張開、握拳、指、比 YA、握持）。

| 名稱 | 用途 | 每根手指 (第1,2,3 節) 彎曲度 |
| --- | --- | --- |
| `relax` | 預設垂手 | 拇指 8/12/10、食 8/14/10 … 小 20/26/16 |
| `open` | 揮手、雙手揮手、歡呼 | 幾乎伸直（原意略張開，但 spread 方向是反的，實際微微往中指收，見下方「spread 的正負號」） |
| `fist` | 踏步、握拳 | 80～95 |
| `point` | 指、按快門、點下巴 | 食指伸直，其他握 |
| `grip` | 拿東西（捧花、刀柄、手機） | 45～62 |
| `pinch` | 比小愛心、提裙 | 拇指食指捏 |
| `peace` | 比 YA | 食指中指伸直並分開（`spread_mid`） |
| `flat` | 遮眉、敬禮 | 全部伸直併攏 |
| `seam` | 男性鞠躬、立正（手貼褲縫） | 四指伸直併攏，拇指在手掌平面內收到食指旁（`thumb_in`）；2026-10-05 新增，沒有在手勢預覽圖裡 |
| `clap_flat` | 拍手、跳舞第 2 拍的合掌 | 四指伸直併攏（沿用 `open`，spread +4＝往中指收）；拇指往手背收 45°（第 1 節 −45）再往食指靠 40°（`thumb_in`），貼在手掌平面裡。預設 `open` 的拇指垂在掌心側、比掌根突出約 6 mm，合掌時拇指會先撞在一起。定義在 `actions.py`（`HANDS.setdefault`），2026-10-06 新增，沒有在手勢預覽圖裡 |

兩種手勢內插：`("open", "grip", u)`（u 取到小數兩位快取）。新手勢加在 `HANDS`，欄位：`Thumb/Index/Middle/Ring/Little=(三節角度)`、`spread`（張開／收攏，正負號見下）、`spread_mid`（中指另外張）、`thumb_in`（拇指在手掌平面內收，選填）。

### spread 的正負號（2026-10-06 實測）

`_hand_pose` 在 rest（T 字、掌心朝下）時繞世界 Z 轉每根手指的第 1 節：食指轉 `spread`、中指轉 `spread × spread_mid`、無名指 `× −0.6`、小指 `× −1.2`（左右手規則相同）。結果和欄位名稱的直覺相反：

- **`spread` 正值＝手指往中指收攏；負值＝往外張開。** `spread_mid=-1` 的中指同理：配正值時往食指倒，配負值時往無名指那側張。
- 踩過兩次：
  - `peace` 原本 `+9`：食指、中指互相往內倒、交叉成 X，指尖只差 10 mm（比手指還窄），正面看像只伸一根手指。改成 `−11` 後指尖相距約 4 cm。
  - `seam` 原本 `−5`：原意四指併攏，實際散開成扇形（第 2、3 節空隙 4～6 mm）。改成 `+3` 後空隙 1～2 mm；`+4` 起食指會穿進中指 1 mm 以上（`seam` 沒設 `spread_mid`，中指不動，食指最先碰到）。
- 方向正確的：`clap_flat`（+4，沿用 `open`）要四指併攏，給正值是對的。
- 方向和原意相反、但**依使用者決定保留不改**的：
  - `open`（+4，原意略張開）：實際比 spread=0 收攏，相鄰手指空隙 3.9 → 1.5～2.4 mm、指尖距 20 → 16 mm。
  - `pinch_open`（+2，定義在 `actions_custom.py`）：差約 1 mm，看不出來。
  - `relax`、`fist`、`point`、`grip` 的負值（−2～−3）其實是微微張開 2～3°。
- **新增手勢照這個規則寫**：要張開給負值、要併攏給正值。寫完用手勢預覽圖的姿勢（`showcase.py` 的 hands：左手、前臂繞 X −90）量相鄰手指第 2、3 節的空隙與穿入；第 1 節連著指蹼，會量到假的穿入，不要算進去。

## 2. 表情（VRoid 標準 shape key，`set_face({...})`）

預覽：`LIB/previews/face_feet.jpg` 上排（大笑、微笑、驚訝、眨右眼、張嘴「啊」）。

| 鍵 | 效果 | 常用值 |
| --- | --- | --- |
| `Fcl_ALL_Joy` | 瞇眼大笑、張嘴 | 0.6～1 |
| `Fcl_ALL_Fun` | 微笑、眼睛半瞇 | 0.3～0.8（待機 0.35） |
| `Fcl_ALL_Surprised` | 驚訝 | 1 |
| `Fcl_ALL_Angry`、`Fcl_ALL_Sorrow` | 生氣、難過 | |
| `Fcl_EYE_Close`、`_L`、`_R` | 閉眼／單眼（眨眼：1 格 1.0） | |
| `Fcl_MTH_A/I/U/E/O` | 嘴型（說話、親吻用 U） | |
| `Fcl_MTH_Small`、`Fcl_BRW_Sorrow` | 嘟嘴、皺眉（思考） | 0.3～0.5 |

完整鍵名看 `<WHO>_Face` 的 shape keys（VRoid 有 58 個）。`set_face` 只會動 `pose_lib.FACE_KEYS` 列的鍵，要用其他的先加進那張表。

### 表情風格（角色專案的 `project.json` → `"face"`，2026-10-09）

使用者回饋（V12 第 2 輪）：「笑的時候眼睛不要咪咪眼，眼睛要大一點正常就好，嘴巴也是微笑就好」「新郎的眼睛可以大一點」。
動作檔的表情不用改，`set_face` 會依角色設定換算（`pose_lib.face_style`／`styled_face`）：

| 設定 | 效果 |
| --- | --- |
| `"smile": "open"` | `Fcl_ALL_Fun`／`Fcl_ALL_Joy`（瞇眼＋張嘴大笑）改成 `Fcl_MTH_Fun`（閉嘴微笑，min(1, 1.6×Fun＋Joy)）＋`Fcl_BRW_Fun`（×0.4）。有笑的時候 `Fcl_EYE_Close` 低於 0.6 的部分拿掉（鞠躬低頭半閉、笑瞇），1.0 的眨眼照舊；單眼眨（`_L`／`_R`）不動 |
| `"base": {鍵: 值}` | 每格加上去的底；眼睛類的底在閉眼時跟著淡掉 |

目前：`groom` ＝ `{"smile": "open", "base": {"Fcl_EYE_Surprised": 0.4}}`（眼睛開大一點；`Fcl_EYE_Spread` 試過，只往橫向開、看不出變大）；`bride` ＝ `{"smile": "open"}`。
沒有 `"face"` 的專案行為和以前一樣。改前／改後對照：`productions/opening-v12/pictures/preview-v2/lib_face_before_after.jpg`。
⚠️ 動作預覽影片（`videos/actions/*.mp4`）是改之前渲的，重渲才會換成新表情。

## 3. 腳

- VRoid 匯出的鞋子（`<WHO>_Shoes`）保留，鞋底下的腳皮膚通常被刪了，所以**不要拿掉鞋子**。
- 每個姿勢預設 `ground=True`：取鞋子 rest 時 z < 1.2 cm 的頂點當鞋底取樣點，每格用腳骨矩陣換算，整體上下平移讓最低點剛好貼地。走路、跳舞、屈膝禮都靠它不陷地也不浮空。
- 預覽：`LIB/previews/face_feet.jpg` 下排（正、斜、側、背）。
- 服裝可以替鞋子換色（`costume.json` → `shoes.recolor`，黑→指定色、白保留）。

## 4. 30 種動作

清單、機制、新娘實測數字見 [actions-catalog.md](actions-catalog.md)；預覽 `LIB/previews/actions/<代號>.jpg`。

## 5. 服裝：粉色歐根紗平口蓬裙

`LIB/costumes/pink-ballgown.json`（規格格式見 blender-character-build 的 references/costume-spec.md）＋層次元件 `LIB/costumes/costume_extra_pink_ballgown.py`。預覽 `LIB/previews/costume_front.jpg`、`costume_back.jpg`。

新娘專案第 3 版（2026-10-04 使用者定案）：平口馬甲（上緣翻摺、斜向腰中央的大花瓣）＋胸口褶邊、腰帶正中央的軟蝴蝶結（兩個圓耳圈＋結＋兩條 V 字剪尾緞帶）、兩層不對稱歐根紗垂墜（貼著裙身往下垂、下擺捲邊）、背後右側四片從腰帶垂下的荷葉瀑布、深粉襯裙＋兩層長短不一的半透明紗裙（下擺各一圈荷葉邊）、後腦蝴蝶結、花朵耳環，鞋子換粉色。新娘基礎檔由這份預設重建，17 個服裝物件與定案版逐點相同。

## 6. 其他

- `LIB/tune_default.json`：碰觸類動作的參數（新娘骨架）。
- `LIB/textures/paper_*.png`：情境「看報紙」的報紙貼圖（`blender-scenario/scripts/examples/make_paper.py` 產生）。
