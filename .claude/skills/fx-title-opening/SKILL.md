---
name: fx-title-opening
description: 照片輪播影片的「片頭樣式」技術文件 —— 目前收錄「對焦轉移」（focus-pull：背景由糊轉清、大字糊掉放大淡出、左下片名淡入）的時間軸、分鏡卡寫法、片頭參數表（參數-*）的每個欄位、演算法與已知坑。在分鏡稿畫片頭與參數表、依分鏡產影片的片頭、或要新增片頭樣式時使用。
metadata:
  version: "1.0"
  source: 婚紗輪播影片第 2 版 render.py（2026-09-15）＋ wedding-photo-slideshow.pen「01 片頭字卡」
---

# 片頭樣式（Opening Title）

片頭是**一整段由樣式控制的連續演出**，不是幾個獨立鏡頭。分鏡稿上分成幾張卡只是為了標出時間點；實際參數寫在「01 片頭字卡」裡的**參數表**。

## 分鏡稿上的寫法

### 片頭卡（「10 分鏡列・片頭」裡的每張卡）

| 欄 | 寫法 |
| --- | --- |
| 版型 | `片頭：{樣式名}`，例 `片頭：對焦轉移`。同一段片頭的每張卡都要相同 |
| 運鏡 | 照實描述這段在做什麼（例 `慢拉 108→104%`），**只給人看，渲染以參數表為準** |
| 轉場 | 除最後一張外寫 `無切換`；**最後一張寫 `黑場 a+bs`**（接正片第一鏡的方式） |
| 字卡 | 這段出現的字（給人看） |
| 素材 | 背景照片檔名 |

片頭的起點＝第一張卡的起點（必須是 0:00），終點＝最後一張卡的終點。

### 參數表（「01 片頭字卡」裡）

在 `01 片頭字卡` frame 裡放一個名為 `參數表-片頭` 的 frame，每個參數一列：

```
frame 參數-title.size          ← 列名＝「參數-」＋參數路徑
├ text 標籤   "大字字級"        ← 給人看
└ text 值     "182"             ← 解析器只讀名為「值」的文字節點
```

- 參數路徑用 `.` 分層；陣列用數字索引，例 `subtitles.lines.0.text`。
- 值：純數字 → 數字；`1.08, 1.04, 1` → 數字陣列；其餘照字串（顏色寫 `#RRGGBB` 或 `#RRGGBBAA`）。
- 照片寫檔名（`dobe-5488.jpg`），會到總覽「規格-照片原檔」目錄找原檔。
- 字型寫檔名（`CG-Italic.ttf`），會到「規格-字型目錄」找。

## 條目

### `focus-pull` 對焦轉移

| 項目 | 內容 |
| --- | --- |
| 狀態 | 已實作（`render_storyboard.py` 的 `op_focus_pull()`） |
| 分鏡寫法 | 版型 `片頭：對焦轉移` |
| 圖示 | `focus` |
| 長度 | 本片 15 秒；建議 12～18 秒 |
| 意境 | 像攝影機對焦：先看到名字，再看清楚兩個人 |

**時間軸**（秒，相對片頭起點；括號內是參數名）：

| 時段 | 背景 | 文字 |
| --- | --- | --- |
| 0 → `fadeIn` | 自黑場淡入 | — |
| 0 → `focusStart` | 放大 `scale[0]`、模糊 `blur`、亮度 `brightness` | `title.in` 起，大字以 `title.fade` 秒淡入 |
| `focusStart` → `focusEnd` | 對焦：模糊→0、亮度→100%、`scale[0]`→`scale[1]`（smoothstep） | 大字放大到 `exitScale`、模糊到 `exitBlur`、淡出 |
| `focusEnd` → 結尾 | `scale[1]`→`scale[2]`（線性） | `subtitles.in` 起，左下兩行以 `subtitles.fade` 秒淡入 |
| 結尾前 `out` 秒 | 淡出至黑（由最後一張卡的「黑場」決定） | 一起淡出 |

全程有底部漸層（讓左下小字讀得清楚）。背景以**畫面上緣中點**為縮放基準（人物頭部不會被推出畫面）。

**參數表**（路徑 → 意思 → 本片值）：

| 參數 | 意思 | 本片值 |
| --- | --- | --- |
| `photo` | 背景照片 | `dobe-5488.jpg` |
| `grade` | 背景調色預設（見 storyboard-video-render 的 grading） | `暖褐復古・暗部壓` |
| `scale` | 背景倍率三段：起始、對焦後、結尾 | `1.08, 1.04, 1` |
| `blur` | 對焦前模糊，**Pencil 半徑 px**（＝2σ） | `27` |
| `brightness` | 對焦前亮度 | `0.55` |
| `focusStart`／`focusEnd` | 對焦開始／結束秒數 | `5`／`7.5` |
| `fadeIn` | 自黑場淡入秒數 | `1.5` |
| `gradient.color`／`gradient.alpha`／`gradient.height` | 底部漸層色、最深處不透明度、高度 px | `#0A0C0E`／`0.6`／`378` |
| `title.text` | 大字 | `Roger & Amy` |
| `title.font`／`title.size`／`title.wght`／`title.tracking` | 字型檔、字級、字重（可變字型）、字距 px | `CG-Italic.ttf`／`182`／`300`／`7.28` |
| `title.color` | 顏色 | `#FFFFFF` |
| `title.cx`／`title.boxTop`／`title.boxH` | 水平中心、文字框上緣、文字框高 | `960`／`389`／`220` |
| `title.in`／`title.fade` | 淡入開始、淡入秒數 | `1`／`1.5` |
| `title.exitScale`／`title.exitBlur` | 退場放大倍率、退場模糊（Pencil px） | `1.12`／`23` |
| `title.exitBox` | 退場時裁切的範圍 x1,y1,x2,y2（可省略，省略時用文字外框） | `380, 330, 1540, 670` |
| `subtitles.in`／`subtitles.fade` | 左下字淡入開始、秒數 | `8`／`1` |
| `subtitles.lines.N.*` | 每一行：`text`／`font`／`size`／`wght`／`tracking`／`color`／`x`（左緣）／`boxTop`／`boxH` | 見下 |

本片左下兩行：
- `A WEDDING FILM`：`CG.ttf` 42px 字重 500、字距 12.6、`#E7C873`、x 134、boxTop 860、boxH 51
- `洪承孝　李怡安`：`NotoSerifTC-VF.ttf` 33px 字重 400、字距 13.2、`#FFFFFFE0`、x 134、boxTop 925、boxH 47

**已知坑**：

- **模糊單位**：Pencil 的模糊半徑＝高斯 σ 的 2 倍。實作在半解析度上做 σ/2，等效全解析度 σ。照稿上的數字直接填，不要自己換算。
- **字距**：PIL 不支援字距，實作是逐字排版。字距的單位是 px（Pencil 的 letterSpacing），不是 em。
- **文字垂直位置**：以字型 ascent＋descent 在 Pencil 文字框（`boxTop`、`boxH`）內垂直置中，所以要填**文字框**的 y 與高，不是基線。
- 標題安全區：大字與小字都要落在 90% 安全框內（左右 96、上下 54），投影機常會裁邊。

## 新增片頭樣式時

1. 先走 `fx-lab` 做預覽、使用者拍板，以「已定案・待實作」寫成新條目：時間軸表＋參數表（路徑、意思、建議值）。
2. 實作端：在 `render_storyboard.py` 新增 `op_xxx(t, P, dur, out)` 與 `op_xxx_assets(P)`，登記到 `OPENINGS`；在 `fx_notation.py` 的 `OPENING_STYLES` 加「中文樣式名 → id」。
3. 樣式函式必須自己處理：自黑場淡入、結尾依 `out` 淡出至黑。
