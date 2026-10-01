# storyboard.json（schema `storyboard/v2`）

`build_storyboard.py` 的產出、`render_storyboard.py` 的輸入。完整範例：[../examples/our-moments.storyboard.json](../examples/our-moments.storyboard.json)（第 2 版成片，49 鏡＋片頭片尾）。

⛔ 這是**產物**，不是原稿。要改影片就改分鏡稿再重新抽取；直接改 JSON 的話，稿和片從此不一致。

## 頂層

| 欄位 | 型別 | 來源 | 說明 |
| --- | --- | --- | --- |
| `schema` | str | 固定 | `storyboard/v2` |
| `title` | str | `--title` | 片名 |
| `source` | obj | `--pen` | `pen`：分鏡稿路徑；`note` |
| `output` | obj | 規格-解析度／影格率／總長／CRF／位元率上限 | `width`、`height`、`fps`、`duration`（秒）、`video`（codec／preset／crf／maxrate／bufsize／profile／level）、`audio`（codec／bitrate／rate） |
| `audio.file` | str | 規格-配樂 | 已剪好的音檔 |
| `assets` | obj | 規格-照片原檔／字型目錄 | `photoDir`、`fontDir` |
| `palette.backdrop` | str | 規格-底色 | `#RRGGBB` |
| `quality` | obj | 固定 | `sharpen`（radius／percent／threshold）、`tileSharpenPercent` |
| `grades` | obj | 固定（`GRADE_PRESETS` 全份） | 名稱 → 運算串列，見 grading.md |
| `opening` | obj | 片頭列＋參數表-片頭 | `style`、`start`、`end`、`out`（片頭接正片的轉場，必為 black）、`params` |
| `shots` | list | 各章節列 | 見下 |
| `ending` | obj | 片尾列＋參數表-片尾 | `style`、`start`、`end`、`params`（含 `fadeOut`） |

## shots[]

```json
{"id": "S1-05", "start": 34, "end": 39, "chapter": "台中國漫館", "grade": "暖褐復古",
 "layout": "B", "photos": ["dobe-5186.jpg", "dobe-5172.jpg"],
 "motion": {"type": "split-counter", "left": [1.0, 1.06], "right": [1.06, 1.0]},
 "out": {"type": "push", "dir": "right", "duration": 0.6}}
```

| 欄位 | 說明 |
| --- | --- |
| `id` | 鏡號 |
| `start`／`end` | 秒（可為小數），全片首尾相接 |
| `chapter` | 章名（章節標頭的「章名」） |
| `grade` | 調色預設名（章節基底或區段覆寫後的結果） |
| `layout` | `A`／`H`／`B`／`C` |
| `photos` | 檔名，相對 `assets.photoDir` |
| `motion` | 見 fx-camera-motion 各條目的 JSON |
| `out` | 本鏡→下一鏡的轉場，見 fx-transition |

## 時間規則

- `opening.start` = 0；`opening.end` = 第一鏡 `start`。
- 最後一鏡 `end` = `ending.start`；`ending.end` = `output.duration`。
- 第一鏡的「上一個轉場」＝ `opening.out`；片尾的淡入＝最後一鏡 `out.in`。
