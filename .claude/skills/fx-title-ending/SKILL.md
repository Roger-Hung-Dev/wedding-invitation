---
name: fx-title-ending
description: 照片輪播影片的「片尾樣式」技術文件 —— 目前收錄「左照右字」（photo-thanks-monogram：左側直式照片慢推壓暗、右側 Thank You 與感謝文依序淡入、最後溶接到新人字標並淡出至黑）的時間軸、分鏡卡寫法、片尾參數表（參數-*）的每個欄位、演算法與已知坑。在分鏡稿畫片尾與參數表、依分鏡產影片的片尾、或要新增片尾樣式時使用。
metadata:
  version: "1.0"
  source: 婚紗輪播影片第 2 版 render.py（2026-09-15）＋ wedding-photo-slideshow.pen「02 片尾字卡」
---

# 片尾樣式（Ending Title）

和片頭一樣，片尾是**一整段由樣式控制的連續演出**。分鏡卡只標時間點；參數寫在「02 片尾字卡」裡的 `參數表-片尾`（格式與片頭相同，見 [[fx-title-opening]] 的「參數表」一節）。

## 分鏡稿上的寫法

| 欄 | 寫法 |
| --- | --- |
| 版型 | `片尾：{樣式名}`，例 `片尾：左照右字`。每張卡都要相同 |
| 轉場 | 除最後一張外寫 `無切換`；**最後一張寫 `淡出至黑 1s`**（全片結尾） |
| 運鏡／字卡／素材 | 照實描述，只給人看；渲染以參數表為準 |

- 片尾起點＝第一張卡的起點，必須等於正片最後一鏡的終點。
- 片尾終點必須等於總長。
- **片尾的淡入由正片最後一鏡的轉場決定**（`黑場 0.5+1.5s` 的 1.5 秒）。

## 條目

### `photo-thanks-monogram` 左照右字

| 項目 | 內容 |
| --- | --- |
| 狀態 | 已實作（`render_storyboard.py` 的 `ed_photo_thanks_monogram()`） |
| 分鏡寫法 | 版型 `片尾：左照右字` |
| 圖示 | `heart-handshake` |
| 長度 | 本片 15 秒；建議 12～20 秒（感謝文越長越要拉長） |
| 意境 | 畫面安靜下來，讓賓客讀完感謝文，最後只留下兩人的名字縮寫 |

**時間軸**（秒，相對片尾起點）：

| 時段 | 左側照片 | 右側文字 |
| --- | --- | --- |
| 0 → 前一鏡黑場的 `in` | 自黑場淡入 | — |
| 0 → `photo.pushDur` | 慢推 `photo.push[0]`→`[1]`，壓暗 `dim.from` | `thanks.in` 起 Thank You＋金色飾線淡入 |
| `dim.at` → `dim.at + dim.dur` | 壓暗加深到 `dim.to`（讓文字更突出） | `lines.N.in` 起感謝文逐行淡入 |
| `monogram.in` → `+ monogram.dissolve` | 整張溶接到深色底字標 | — |
| 最後 `fadeOut` 秒 | 淡出至全黑（`fadeOut` 取自最後一張卡的「淡出至黑 Ns」） | — |

**參數表**：

| 參數 | 意思 | 本片值 |
| --- | --- | --- |
| `photo.name`／`photo.grade` | 左側照片、調色預設 | `dobe-5575.jpg`／`原色` |
| `photo.panelWidth` | 照片區寬（照片置中在這個寬度內） | `720` |
| `photo.push`／`photo.pushDur` | 慢推倍率起訖、推多久後停住 | `1, 1.05`／`5` |
| `photo.dim.from`／`.to`／`.at`／`.dur` | 壓暗：起始、加深後、開始加深的秒數、加深秒數 | `0.15`／`0.6`／`5`／`1` |
| `divider.color`／`.alpha`／`.width` | 照片與文字間的直線 | `#E7C873`／`0.7`／`2` |
| `thanks.text`／`.font`／`.size`／`.color` | 主標 | `Thank You`／`GreatVibes.ttf`／`180`／`#E7C873` |
| `thanks.cx`／`.boxTop`／`.boxH` | 水平中心、文字框上緣與高 | `1322`／`339`／`225` |
| `thanks.in`／`.fade` | 淡入開始、秒數 | `1.5`／`1` |
| `thanks.ornament.y`／`.inner`／`.outer`／`.diamond`／`.color` | 飾線：y、離中心的內外端點、中央菱形半徑、顏色 | `585`／`21`／`161`／`6`／`#E7C873` |
| `lines.N.text`／`.font`／`.size`／`.wght`／`.color`／`.cx`／`.boxTop`／`.boxH`／`.in`／`.fade` | 感謝文每一行 | 見下 |
| `monogram.in`／`.dissolve`／`.bg` | 字標開始溶接的秒數、溶接秒數、底色 | `10.5`／`1`／`#0E1216` |
| `monogram.ring.diameter`／`.stroke`／`.color` | 圓框直徑、線寬、色 | `128`／`1.5`／`#E7C873` |
| `monogram.text.*` | 圓框內文字（`text`／`font`／`size`／`color`／`cx`／`boxTop`／`boxH`） | `R & A`／`GreatVibes.ttf`／`45`／`#E7C873`／`960`／`512`／`56` |

本片感謝文兩行（`NotoSerifTC-VF.ttf` 40px 字重 400、`#FFFFFFCC`、cx 1322、boxH 68）：
- `謝謝每一位陪伴我們走到這裡的人，`：boxTop 606、in 5.5、fade 1
- `今天，謝謝你們在這裡。`：boxTop 674、in 7.5、fade 1

**已知坑**：

- **字標字級要配合圓框**：v1 規格表寫圓框 128＋字 50px，但 50px 的「R & A」寬度超出圓框。實作改用縮圖比例「字級＝圓徑 × 0.354」→ 45px。改圓框大小時字級要一起算。
- **細線要超取樣**：1.5px 圓框直接畫會鋸齒，實作是 4 倍解析度畫再 LANCZOS 縮回。
- v1 稿上 ED-01「原色」與縮圖「壓暗 15%」矛盾，實作照縮圖（`dim.from 0.15`）。v2 起以參數表為準。
- 感謝文要讓長輩讀得完：每行停留至少 4 秒、字級不低於 36px（1080p）。

## 新增片尾樣式時

1. 先走 `fx-lab` 做預覽、使用者拍板，以「已定案・待實作」寫成新條目：時間軸表＋參數表。
2. 實作端：在 `render_storyboard.py` 新增 `ed_xxx(t, P, dur, prev_out)` 與 `ed_xxx_assets(P)`，登記到 `ENDINGS`；在 `fx_notation.py` 的 `ENDING_STYLES` 加「中文樣式名 → id」。
3. 樣式函式必須自己處理：依 `prev_out` 自黑場淡入、最後 `fadeOut` 秒淡出至黑。
