# 服裝規格（costume.json）

`costume.py` 讀 `PROJ/costume.json`（沒有就用 `LIB/costumes/pink-ballgown.json`）。座標全是**新娘座標**（腰線 z 0.985、肩 1.27、地面 0），程式自動乘體型比例。

## 1. 欄位

```jsonc
{
  "name": "粉色歐根紗平口蓬裙",          // 網頁 03 的標題
  "source": "新娘婚紗照（正面、背面）",
  "summary": "…",                        // 網頁 03 的說明，寫看得到的特徵
  "colors": { "main": [r,g,b], "main_shade": [r,g,b], "organza": …, "lining": …, "tulle": …, "sash": …, "hair_bow": …, "metal": … },
  "organza_alpha": 0.9, "tulle_alpha": 0.38,   // 半透明程度（1＝不透明）
  "keep_vroid": ["Shoes"],               // 穿服裝時保留的 VRoid 原本部件（Shoes/Tee/Shorts/Socks…）
  "needs_body_fill": true,               // 會露肩/露背 → build_costume 自動補皮膚
  "components": {
    "bodice":   {"enabled": true, "neckline": "strapless", "top_z": 1.232, "top_slant": 0.28, "bottom_z": 0.955, "offset": 0.006},
    "ruffle":   {"enabled": true, "layers": [[高, 外翻, 波幅, 波數, 相位], …]},
    "sash":     {"enabled": true, "z0": 0.962, "z1": 0.997, "offset": 0.0105},
    "rosette":  {"enabled": true, "center": [0.05, -0.125, 0.985], "scale": 1.6},
    "sash_tails": {"enabled": true, "top": [0.05, -0.12, 0.975]},
    "skirt":    {"enabled": true, "profile": "ball|aline|mermaid|column", "length": "floor|ankle|midi|knee|mini", "lining": true, "tulle_layers": 2, "train": 0.2},
    "drape":    {"enabled": true, "high_z": 0.78, "low_z": 0.38, "high_angle": -60, "folds": 7},
    "cascade":  {"enabled": true, "tiers": 5, "side": "right|left"},
    "hair_bow": {"enabled": true, "z": 1.50, "scale": 1.0},
    "earrings": {"enabled": true, "style": "flower|drop"},
    "shoes":    {"recolor": [r,g,b]}     // null＝不換色
  },
  "layers": { … },                       // 自訂元件用的參數（pink-ballgown 的層次元件讀這裡，欄位見該 .py 檔頭）
  "extra_scripts": ["costume_extra_jacket"]   // 自訂元件：先找 PROJ/scripts/，再找 LIB/costumes/
}
```

`pink-ballgown.json` 的 `extra_scripts` 是 `costume_extra_pink_ballgown`（放在 `LIB/costumes/`）：垂墜、背後瀑布、軟蝴蝶結、荷葉邊、各層分色都由它做，所以規格裡 `drape`／`cascade`／`rosette`／`sash_tails` 是關的。複製這份預設到專案後，要微調層次就改 `layers`；要改程式就把那支 .py 複製到 `PROJ/scripts/` 再改（同名時專案的優先）。

顏色是 MToon 的 linear 值：`main` 是受光面、`*_shade` 是陰影面（通常比受光面暗 15～20%、略偏紫）。照片的 sRGB 值 `c/255` 再做 `c**2.2` 大約就是 linear。

## 2. 照片 → 規格（怎麼看）

| 照片上看到 | 規格 |
| --- | --- |
| 平口、露肩 | `bodice.neckline: strapless`、`needs_body_fill: true` |
| 胸口有花瓣、抓摺、荷葉邊 | `ruffle` 開；層數＝看得到幾層；最外層前高後低 |
| 腰間緞帶、蝴蝶結、花 | `sash` ＋ `rosette`（位置看照片偏哪邊：角色左手邊＝ +x）、`sash_tails` |
| 大蓬裙／A 字／魚尾／直筒 | `skirt.profile` ＝ ball／aline／mermaid／column |
| 裙長 | `skirt.length` |
| 半透明紗、看得到裡層 | `lining: true` ＋ `tulle_layers` 2～3、`tulle_alpha` 0.3～0.45 |
| 一側拉高的垂墜布 | `drape`：`high_angle` 是最高點的方向（−90＝正前、0＝角色左、90＝正後、180＝角色右），`high_z`／`low_z` 是最高、最低下擺 |
| 背後一層層往下的荷葉 | `cascade`（`side` 看偏哪邊） |
| 拖尾 | `skirt.train` 0.1～0.3 |
| 髮飾（後腦） | `hair_bow` |
| 耳環 | `earrings.style` |
| 鞋子顏色 | `shoes.recolor`；被裙子蓋住看不到也照做，跳躍時會露出來 |

⚠️ 正面照拍的是「她的右手邊在畫面左邊」：照片左側的玫瑰結＝角色右側＝ `x < 0`。

## 3. 規格做不到的

- 有袖子、外套、褲子、領子：寫 `PROJ/scripts/costume_extra_<名>.py`：

  ```python
  def build_extra(M, spec):
      mat = mtoon(P + "JacketMat", (0.12, 0.12, 0.16), (0.08, 0.08, 0.11))
      keep = lambda c: 0.85 * S < c.z < 1.42 * S
      j = shell_piece(O[f"{WHO}_SRC"], P + "Jacket", keep, 0.012 * S, mat)   # 從原始身體（含 T 恤）撐開
      v_cut(j, 0.02, 1.32, 0.09, 1.02, lapel=0.03)                             # 前襟 V 字＋翻領
      for side in ("L", "R"):
          sleeve(A, P + f"Sleeve{side}", side, 0.05 * S, 0.042 * S, 0.038 * S, 0.0, mat)
  ```

  物件名稱一定用 `P`（`<WHO>_Cos_`）開頭，`wear()` 才換得掉。
- 頭髮造型（盤髮、捲髮）：目前做不到，寫進 `report.limits`。可以加髮飾、改髮色（改頭髮材質的 base color factor）。

## 4. 改服裝的回報要寫

改了哪些欄位（前→後）、依據是照片的哪個部位或描述的哪句話、檢查圖看到的差異還剩什麼。
