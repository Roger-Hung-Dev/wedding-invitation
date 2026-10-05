# 預設資料庫

全部來自新娘專案（`.claude/docs/data/blender/projects/bride/`，成果頁 https://claude.ai/artifact/12T6gowAFGaBVvSUAawPfa ）。新專案直接沿用，不夠再擴充。

## 1. 手勢（`pose_lib.HANDS`）

預覽：`LIB/previews/hands_sheet.jpg`（上排掌心、下排手背：放鬆、張開、握拳、指、比 YA、握持）。

| 名稱 | 用途 | 每根手指 (第1,2,3 節) 彎曲度 |
| --- | --- | --- |
| `relax` | 預設垂手 | 拇指 8/12/10、食 8/14/10 … 小 20/26/16 |
| `open` | 揮手、拍手、歡呼 | 幾乎伸直、略張開 |
| `fist` | 踏步、握拳 | 80～95 |
| `point` | 指、按快門、點下巴 | 食指伸直，其他握 |
| `grip` | 拿東西（捧花、刀柄、手機） | 45～62 |
| `pinch` | 比小愛心、提裙 | 拇指食指捏 |
| `peace` | 比 YA | 食指中指伸直並分開（`spread_mid`） |
| `flat` | 遮眉、敬禮 | 全部伸直併攏 |
| `seam` | 男性鞠躬、立正（手貼褲縫） | 四指伸直併攏，拇指在手掌平面內收到食指旁（`thumb_in`）；2026-10-05 新增，沒有在手勢預覽圖裡 |

兩種手勢內插：`("open", "grip", u)`（u 取到小數兩位快取）。新手勢加在 `HANDS`，欄位：`Thumb/Index/Middle/Ring/Little=(三節角度)`、`spread`（張開）、`spread_mid`（中指另外張）、`thumb_in`（拇指在手掌平面內收，選填）。

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
