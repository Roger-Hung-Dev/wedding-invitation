---
name: storyboard-video-render
description: 讀取 v2 分鏡稿 .pen、輸出指定規格影片的產線 —— 用 Pencil MCP 唯讀抽取標註（extract_raw.js）、轉成 storyboard.json 並檢查（build_storyboard.py）、預處理照片、抽格檢查、片段預覽、正式輸出 mp4（render_storyboard.py），以及畫質鐵律、工作目錄規則、擴充特效的實作位置與回歸驗證。依分鏡稿產影片、重產既有影片、或為新特效補實作時使用。
compatibility: Python 3.10+（Pillow、numpy）、ffmpeg（含 libx264、aac）、Pencil Desktop 與 pencil-server MCP
metadata:
  version: "1.0"
  verified: 2026-10-02 以範例 storyboard.json 與第 2 版 render.py 逐格比對 1,569 個時間點，像素差 0
---

# 分鏡稿 → 影片

```
.pen（v2 分鏡稿）
  │ ① extract_raw.js（pencil execute，唯讀）
  ▼
raw.json ── ② build_storyboard.py（解析＋檢查；有錯就停）
  ▼
storyboard.json ── ③ prep → ④ still 抽格 → ⑤ 片段預覽 → ⑥ video
  ▼
成品 .mp4
```

格式契約見 [[storyboard-pen-format]]；每種特效的寫法與演算法見 [[fx-camera-motion]]、[[fx-transition]]、[[fx-title-opening]]、[[fx-title-ending]]；storyboard.json 的欄位見 [references/storyboard-json.md](references/storyboard-json.md)；調色預設見 [references/grading.md](references/grading.md)。

腳本都在 `.claude/skills/storyboard-video-render/scripts/`，以下指令**從專案根目錄執行**（下文以 `$SK` 代表這個 scripts 目錄）。

## 0. 工作目錄

- 使用者要指定**成品輸出路徑**。工作目錄一律是 `<成品所在目錄>/render-work/`：`raw.json`、`storyboard.json`、`cache/`（預處理素材，約 100 張 png）、`stills/`（抽格）都放這裡。
- ⛔ **不要放進專案 repo**（素材快取上百 MB），也不要放在照片原檔目錄。
- 改了照片調色或照片本身，要刪掉 `cache/` 重跑 prep；只改時間、運鏡、轉場則不用。

## ① 抽取標註（唯讀）

1. `get_app_state` 確認分鏡稿已在 Pencil Desktop 開啟。**沒開就停下來請使用者開**，不要自己開檔（專案鐵律，hook 也會擋）。
2. `Read` `$SK/extract_raw.js`，把**整段**內容當作 `mcp__pencil-server__execute` 的 `input`，`filePath` 帶分鏡稿的 Windows 絕對路徑（`D:\...`，⛔ 不要用 `/D:/...`，那會安靜地讀到另一份 active 檔）。
3. 把印出的那一行 JSON **原樣**用 `Write` 存成 `render-work/raw.json`。

⚠️ 這一步是**人工謄寫**：Pencil 的輸出只能經過你再寫進檔案。所以 JSON 裡帶了核對碼（字數＋hash），② 會重算；**抄錯一個字就會被擋**。被擋時重新執行 ①，不要手動修 raw.json。

## ② 轉成 storyboard.json（檢查）

```
python $SK/build_storyboard.py <work>/raw.json -o <work>/storyboard.json --title "片名"
```

- 會一次列出**所有**問題（缺規格、寫法不符、時間碼不連續、照片原檔不存在、版型與運鏡不相容…），每條帶鏡號。
- ⛔ **有錯就停，回報給使用者或畫稿的 storyboard-artist 去改稿。** 不要手改 storyboard.json 來「過關」—— 那會讓稿與片從此不一致，下次重產又會壞。
- 唯一例外：使用者明確要求「這次不改稿、直接用某個值」時，可在 storyboard.json 改，並在回報中逐項列出改了什麼。

## ③ 預處理

```
python $SK/render_storyboard.py prep <work>/storyboard.json
```

把每一鏡的照片從原檔一次縮到最大倍率時的尺寸、調色、銳化、做模糊底，存到 `cache/`。第一次約數分鐘。

## ④ 抽格檢查（必做，不能跳）

```
python $SK/render_storyboard.py still <work>/storyboard.json 7.5 15.2 38.7 98 108.1 208 236.2
```

挑這些時間點：片頭對焦中、每章第一鏡（黑場淡入中）、每種轉場的交疊中、B 版型、C 版型進場中、片尾字標。輸出到 `stills/`，**用 `Read` 開圖逐張看**：

- 照片有沒有被裁到臉、模糊底是不是同一張照片
- 文字有沒有超出畫面或安全框（左右 96、上下 54）
- 調色是否符合章節意圖（[references/grading.md](references/grading.md)）

## ⑤ 片段預覽（建議）

```
python $SK/render_storyboard.py video <work>/storyboard.json <work>/preview_92-100.mp4 --start 92 --end 100
```

正式輸出整支要十幾分鐘；先輸出有疑慮的段落（新特效、快切段）給使用者看。

## ⑥ 正式輸出

```
python $SK/render_storyboard.py video <work>/storyboard.json <成品>.mp4
```

輸出規格來自 storyboard.json 的 `output`（預設 H.264 High@4.2、CRF 16、上限 20M、BT.709、yuv420p、AAC 48k 320k、faststart）。完成後用 `ffprobe` 核對：

```
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration -of compact <成品>.mp4
```

解析度、影格率、長度都要與分鏡稿「規格-*」一致才算完成。

## 畫質鐵律（不要「簡化」掉）

這些都是第 1 版被退件後修好的，程式碼裡看起來像多餘的複雜度，其實每一條都對應一個投影時看得見的問題：

| 實作 | 拿掉會怎樣 |
| --- | --- |
| 原檔一次縮到最大倍率尺寸（`kmax`），逐格只縮小 | 照片變軟 |
| 子像素定位＋2px 邊緣遮罩（`place_sub`／`padded`） | 運鏡時邊緣每幾格跳 1px |
| 靜止鏡對齊整數像素（`snap`） | 靜止照片微糊 |
| UnsharpMask（radius 1.2、percent 70） | 縮圖後整體偏軟 |
| 60fps | 30fps 的慢推在大螢幕上會抖 |
| 不加底片顆粒 | 投影時像胡椒鹽雜訊 |

## 擴充特效（遇到「已定案・待實作」的特效時）

分鏡用了 fx-* skill 裡狀態為「已定案・待實作」的特效時，② 會報「不符合任何寫法」。實作步驟：

1. 讀該特效條目的「分鏡寫法／JSON／演算法」。
2. 三處一起改：
   - `fx_notation.py`：加解析規則（寫法要和條目一字不差）
   - `render_storyboard.py`：依檔頭的「特效實作對照表」改對應函式
   - `build_storyboard.py` 的 `validate()`：有長度或版型限制時加檢查
3. **回歸驗證**：既有特效的畫面不能變。用範例重跑抽格並和改動前比對：

   ```
   python $SK/render_storyboard.py still .claude/skills/storyboard-video-render/examples/our-moments.storyboard.json 3 15.2 37.9 98 108.1 145 208 236 --work <暫存目錄>
   ```

   改動前後同一時間點的 png 必須逐像素相同（用 numpy 比 `max(abs(a−b)) == 0`）。範例需要的照片原檔與字型在 `D:\婚禮籌備\`，不在時跳過並在回報中說明。
4. 新特效本身：輸出含該特效的片段預覽給使用者確認。
5. 把 fx-* 條目的狀態改成「已實作」，寫上實作函式名與驗證方式。

## 已知坑

- **Windows 主控台亂碼**：腳本已固定以 UTF-8 輸出；若用其他方式呼叫 Python 看到亂碼，加 `PYTHONIOENCODING=utf-8`。
- **shell 指令裡出現 `.pen` 路徑**會被 `block-pen-file-ops` hook 檢查；只要不是建檔、開檔、寫檔、刪檔的指令就會放行。`--pen` 參數不需要也可以省略。
- **配樂長度**要等於總長；產生器不剪音樂，只用 `-t` 截在總長。
- 多工：`--jobs` 預設 CPU 數−2。記憶體不足時降低。
