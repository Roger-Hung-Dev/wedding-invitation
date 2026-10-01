# v2 分鏡稿標註範例（Our Moments，由第 2 版成片反推）

> 這份是「v2 稿上每個 `值` 文字節點該寫什麼」的完整範例。把它畫進 .pen，`build_storyboard.py` 解析出來的結果與第 2 版成片逐格相同（已用 1,569 個時間點驗證像素差為 0）。

## 規格-*（00 總覽）

| 列名 | 值 |
| --- | --- |
| `規格-解析度` | `1920×1080` |
| `規格-影格率` | `60` |
| `規格-總長` | `4:00` |
| `規格-配樂` | `D:\婚禮籌備\婚紗輪播影片\產生器\music_240.wav` |
| `規格-照片原檔` | `D:\婚禮籌備\婚紗照\全部毛片` |
| `規格-字型目錄` | `D:\婚禮籌備\婚紗輪播影片\fonts` |
| `規格-底色` | `#1E2A33` |

## 參數-*（01 片頭字卡／參數表-片頭）

| 列名 | 值 |
| --- | --- |
| `參數-photo` | `dobe-5488.jpg` |
| `參數-grade` | `暖褐復古・暗部壓` |
| `參數-scale` | `1.08, 1.04, 1` |
| `參數-blur` | `27` |
| `參數-brightness` | `0.55` |
| `參數-focusStart` | `5` |
| `參數-focusEnd` | `7.5` |
| `參數-fadeIn` | `1.5` |
| `參數-gradient.color` | `#0A0C0E` |
| `參數-gradient.alpha` | `0.6` |
| `參數-gradient.height` | `378` |
| `參數-title.text` | `Roger & Amy` |
| `參數-title.font` | `CG-Italic.ttf` |
| `參數-title.size` | `182` |
| `參數-title.wght` | `300` |
| `參數-title.tracking` | `7.28` |
| `參數-title.color` | `#FFFFFF` |
| `參數-title.cx` | `960` |
| `參數-title.boxTop` | `389` |
| `參數-title.boxH` | `220` |
| `參數-title.in` | `1` |
| `參數-title.fade` | `1.5` |
| `參數-title.exitScale` | `1.12` |
| `參數-title.exitBlur` | `23` |
| `參數-title.exitBox` | `380, 330, 1540, 670` |
| `參數-subtitles.in` | `8` |
| `參數-subtitles.fade` | `1` |
| `參數-subtitles.lines.0.text` | `A WEDDING FILM` |
| `參數-subtitles.lines.0.font` | `CG.ttf` |
| `參數-subtitles.lines.0.size` | `42` |
| `參數-subtitles.lines.0.wght` | `500` |
| `參數-subtitles.lines.0.tracking` | `12.6` |
| `參數-subtitles.lines.0.color` | `#E7C873` |
| `參數-subtitles.lines.0.x` | `134` |
| `參數-subtitles.lines.0.boxTop` | `860` |
| `參數-subtitles.lines.0.boxH` | `51` |
| `參數-subtitles.lines.1.text` | `洪承孝　李怡安` |
| `參數-subtitles.lines.1.font` | `NotoSerifTC-VF.ttf` |
| `參數-subtitles.lines.1.size` | `33` |
| `參數-subtitles.lines.1.wght` | `400` |
| `參數-subtitles.lines.1.tracking` | `13.2` |
| `參數-subtitles.lines.1.color` | `#FFFFFFE0` |
| `參數-subtitles.lines.1.x` | `134` |
| `參數-subtitles.lines.1.boxTop` | `925` |
| `參數-subtitles.lines.1.boxH` | `47` |

## 參數-*（02 片尾字卡／參數表-片尾）

| 列名 | 值 |
| --- | --- |
| `參數-photo.name` | `dobe-5575.jpg` |
| `參數-photo.grade` | `原色` |
| `參數-photo.panelWidth` | `720` |
| `參數-photo.push` | `1, 1.05` |
| `參數-photo.pushDur` | `5` |
| `參數-photo.dim.from` | `0.15` |
| `參數-photo.dim.to` | `0.6` |
| `參數-photo.dim.at` | `5` |
| `參數-photo.dim.dur` | `1` |
| `參數-divider.color` | `#E7C873` |
| `參數-divider.alpha` | `0.7` |
| `參數-divider.width` | `2` |
| `參數-thanks.text` | `Thank You` |
| `參數-thanks.font` | `GreatVibes.ttf` |
| `參數-thanks.size` | `180` |
| `參數-thanks.color` | `#E7C873` |
| `參數-thanks.cx` | `1322` |
| `參數-thanks.boxTop` | `339` |
| `參數-thanks.boxH` | `225` |
| `參數-thanks.in` | `1.5` |
| `參數-thanks.fade` | `1` |
| `參數-thanks.ornament.y` | `585` |
| `參數-thanks.ornament.inner` | `21` |
| `參數-thanks.ornament.outer` | `161` |
| `參數-thanks.ornament.diamond` | `6` |
| `參數-thanks.ornament.color` | `#E7C873` |
| `參數-lines.0.text` | `謝謝每一位陪伴我們走到這裡的人，` |
| `參數-lines.0.font` | `NotoSerifTC-VF.ttf` |
| `參數-lines.0.size` | `40` |
| `參數-lines.0.wght` | `400` |
| `參數-lines.0.color` | `#FFFFFFCC` |
| `參數-lines.0.cx` | `1322` |
| `參數-lines.0.boxTop` | `606` |
| `參數-lines.0.boxH` | `68` |
| `參數-lines.0.in` | `5.5` |
| `參數-lines.0.fade` | `1` |
| `參數-lines.1.text` | `今天，謝謝你們在這裡。` |
| `參數-lines.1.font` | `NotoSerifTC-VF.ttf` |
| `參數-lines.1.size` | `40` |
| `參數-lines.1.wght` | `400` |
| `參數-lines.1.color` | `#FFFFFFCC` |
| `參數-lines.1.cx` | `1322` |
| `參數-lines.1.boxTop` | `674` |
| `參數-lines.1.boxH` | `68` |
| `參數-lines.1.in` | `7.5` |
| `參數-lines.1.fade` | `1` |
| `參數-monogram.in` | `10.5` |
| `參數-monogram.dissolve` | `1` |
| `參數-monogram.bg` | `#0E1216` |
| `參數-monogram.ring.diameter` | `128` |
| `參數-monogram.ring.stroke` | `1.5` |
| `參數-monogram.ring.color` | `#E7C873` |
| `參數-monogram.text.text` | `R & A` |
| `參數-monogram.text.font` | `GreatVibes.ttf` |
| `參數-monogram.text.size` | `45` |
| `參數-monogram.text.color` | `#E7C873` |
| `參數-monogram.text.cx` | `960` |
| `參數-monogram.text.boxTop` | `512` |
| `參數-monogram.text.boxH` | `56` |

## 章節標頭的 資訊-調色

| 分鏡列 | 值 |
| --- | --- |
| 11 分鏡列・第 1 章 台中國漫館 | `暖褐復古` |
| 12 分鏡列・第 2 章 苗栗環保公園 | `明亮通透｜S2-06～S2-13：明亮通透・副歌` |
| 13 分鏡列・第 3 章 苗栗火炎山 | `金黃暖調` |
| 14 分鏡列・第 4 章 苗栗松柏港 | `粉橘夕陽` |

## 鏡頭卡（全部 55 張）

| 鏡號 | 時間碼 | 秒 | 版型 | 運鏡 | 轉場 | 素材 |
| --- | --- | --- | --- | --- | --- | --- |
| OP-01 | 0:00–0:05 | 5 秒 | `片頭：對焦轉移` | `靜止` | `無切換` | dobe-5488.jpg |
| OP-02 | 0:05–0:07.5 | 2.5 秒 | `片頭：對焦轉移` | `慢拉 108→104%` | `無切換` | dobe-5488.jpg |
| OP-03 | 0:07.5–0:15 | 7.5 秒 | `片頭：對焦轉移` | `慢拉 104→100%` | `黑場 0.5+1.5s（章節轉換）` | dobe-5488.jpg |
| S1-01 | 0:15–0:18 | 3 秒 | `A 直式置中＋模糊底` | `慢拉 115→100%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5182.jpg |
| S1-02 | 0:18–0:24 | 6 秒 | `A 直式置中＋模糊底` | `慢拉 110→100%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5249.jpg |
| S1-03 | 0:24–0:29 | 5 秒 | `H 橫式滿版` | `平移 → 160px @110%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5113.jpg |
| S1-04 | 0:29–0:34 | 5 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5123.jpg |
| S1-05 | 0:34–0:39 | 5 秒 | `B 分割畫面` | `分割一推一拉 左100→106% 右106→100%` | `推移 → 0.6s` | wedding-photo/1800px/dobe-5186.jpg<br>wedding-photo/1800px/dobe-5172.jpg |
| S1-06 | 0:39–0:43 | 4 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `硬切` | wedding-photo/1800px/dobe-5121.jpg |
| S1-07 | 0:43–0:48 | 5 秒 | `A 直式置中＋模糊底` | `微推 100→103%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5212.jpg |
| S1-08 | 0:48–0:52 | 4 秒 | `A 直式置中＋模糊底` | `平移 → 90px @105%` | `硬切` | wedding-photo/1800px/dobe-5228.jpg |
| S1-09 | 0:52–0:58 | 6 秒 | `A 直式置中＋模糊底` | `平移 ← 90px @105%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5150.jpg |
| S1-10 | 0:58–1:04 | 6 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5190.jpg |
| S1-11 | 1:04–1:10 | 6 秒 | `A 直式置中＋模糊底` | `慢拉 110→100%` | `黑場 0.5+1.5s（章節轉換）` | wedding-photo/1800px/dobe-5240.jpg |
| S2-01 | 1:10–1:13 | 3 秒 | `A 直式置中＋模糊底` | `慢拉 115→100%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5388.jpg |
| S2-02 | 1:13–1:19 | 6 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5253.jpg |
| S2-03 | 1:19–1:24 | 5 秒 | `A 直式置中＋模糊底` | `慢拉 110→100%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5280.jpg |
| S2-04 | 1:24–1:29 | 5 秒 | `B 分割畫面` | `分割一推一拉 左100→106% 右106→100%` | `推移 → 0.6s` | wedding-photo/1800px/dobe-5329.jpg<br>wedding-photo/1800px/dobe-5294.jpg |
| S2-05 | 1:29–1:34 | 5 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5308.jpg |
| S2-06 | 1:34–1:38 | 4 秒 | `A 直式置中＋模糊底` | `平移 ← 90px @105%` | `閃白 0.08+0.22s 85%` | wedding-photo/1800px/dobe-5425.jpg |
| S2-07 | 1:38–1:42 | 4 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `硬切` | wedding-photo/1800px/dobe-5439.jpg |
| S2-08 | 1:42–1:45 | 3 秒 | `H 橫式滿版` | `平移 → 160px @110%` | `硬切` | wedding-photo/1800px/dobe-5347.jpg |
| S2-09 | 1:45–1:48 | 3 秒 | `A 直式置中＋模糊底` | `靜止` | `硬切` | wedding-photo/1800px/dobe-5410.jpg |
| S2-10 | 1:48–1:51 | 3 秒 | `B 分割畫面` | `分割右格晚進 延遲0.2s 淡入0.3s` | `推移 ← 0.6s` | wedding-photo/1800px/dobe-5436.jpg<br>wedding-photo/1800px/dobe-5438.jpg |
| S2-11 | 1:51–1:54 | 3 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `硬切` | wedding-photo/1800px/dobe-5441.jpg |
| S2-12 | 1:54–1:57 | 3 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `硬切` | wedding-photo/1800px/dobe-5419.jpg |
| S2-13 | 1:57–2:00 | 3 秒 | `H 橫式滿版` | `慢推 100→108%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5352.jpg |
| S2-14 | 2:00–2:05 | 5 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5310.jpg |
| S2-15 | 2:05–2:10 | 5 秒 | `A 直式置中＋模糊底` | `慢拉 110→100%` | `黑場 0.5+1.5s（章節轉換）` | wedding-photo/1800px/dobe-5418.jpg |
| S3-01 | 2:10–2:13 | 3 秒 | `H 橫式滿版` | `慢拉 115→100%` | `溶接 1.5s` | wedding-photo/1800px/dobe-5488.jpg |
| S3-02 | 2:13–2:20 | 7 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 1.5s` | wedding-photo/1800px/dobe-5461.jpg |
| S3-03 | 2:20–2:25 | 5 秒 | `A 直式置中＋模糊底` | `平移 → 90px @105%` | `溶接 1.5s` | wedding-photo/1800px/dobe-5456.jpg |
| S3-04 | 2:25–2:32 | 7 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 1.5s` | wedding-photo/1800px/dobe-5494.jpg |
| S3-05 | 2:32–2:37 | 5 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 1.5s` | wedding-photo/1800px/dobe-5492.jpg |
| S3-06 | 2:37–2:44 | 7 秒 | `A 直式置中＋模糊底` | `平移 → 90px @105%` | `溶接 1.5s` | wedding-photo/1800px/dobe-5471.jpg |
| S3-07 | 2:44–2:49 | 5 秒 | `A 直式置中＋模糊底` | `平移 ← 90px @105%` | `溶接 1.5s` | wedding-photo/1800px/dobe-5480.jpg |
| S3-08 | 2:49–2:55 | 6 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 1.5s` | wedding-photo/1800px/dobe-5474.jpg |
| S3-09 | 2:55–3:00 | 5 秒 | `A 直式置中＋模糊底` | `平移 → 90px @105%` | `溶接 1.5s` | wedding-photo/1800px/dobe-5464.jpg |
| S3-10 | 3:00–3:05 | 5 秒 | `H 橫式滿版` | `慢拉 110→100%` | `黑場 0.5+1.5s（章節轉換）` | wedding-photo/1800px/dobe-5485.jpg |
| S4-01 | 3:05–3:07 | 2 秒 | `A 直式置中＋模糊底` | `慢拉 115→100%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5505.jpg |
| S4-02 | 3:07–3:10 | 3 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `硬切` | wedding-photo/1800px/dobe-5533.jpg |
| S4-03 | 3:10–3:12 | 2 秒 | `A 直式置中＋模糊底` | `平移 → 90px @105%` | `硬切` | wedding-photo/1800px/dobe-5549.jpg |
| S4-04 | 3:12–3:15 | 3 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `硬切` | wedding-photo/1800px/dobe-5557.jpg |
| S4-05 | 3:15–3:17 | 2 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `硬切` | wedding-photo/1800px/dobe-5559.jpg |
| S4-06 | 3:17–3:20 | 3 秒 | `A 直式置中＋模糊底` | `平移 → 90px @105%` | `硬切` | wedding-photo/1800px/dobe-5569.jpg |
| S4-07 | 3:20–3:22 | 2 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `閃白 0.08+0.22s 85%` | wedding-photo/1800px/dobe-5521.jpg |
| S4-08 | 3:22–3:25 | 3 秒 | `A 直式置中＋模糊底` | `慢拉 110→100%` | `硬切` | wedding-photo/1800px/dobe-5507.jpg |
| S4-09 | 3:25–3:27 | 2 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `閃白 0.08+0.22s 85%` | wedding-photo/1800px/dobe-5555.jpg |
| S4-10 | 3:27–3:30 | 3 秒 | `C 回顧格` | `多格依序進場 間隔0.3s 淡入0.4s` | `閃白 0.08+0.22s 85%` | wedding-photo/1800px/dobe-5249.jpg<br>wedding-photo/1800px/dobe-5253.jpg<br>wedding-photo/1800px/dobe-5439.jpg<br>wedding-photo/1800px/dobe-5461.jpg |
| S4-11 | 3:30–3:33 | 3 秒 | `A 直式置中＋模糊底` | `靜止` | `硬切` | wedding-photo/1800px/dobe-5552.jpg |
| S4-12 | 3:33–3:39 | 6 秒 | `A 直式置中＋模糊底` | `慢推 100→108%` | `溶接 0.8s` | wedding-photo/1800px/dobe-5575.jpg |
| S4-13 | 3:39–3:45 | 6 秒 | `A 直式置中＋模糊底` | `慢拉 110→100%` | `黑場 0.5+1.5s（章節轉換）` | wedding-photo/1800px/dobe-5543.jpg |
| ED-01 | 3:45–3:50 | 5 秒 | `片尾：左照右字` | `慢推 100→105%` | `無切換` | dobe-5575.jpg |
| ED-02 | 3:50–3:55.5 | 5.5 秒 | `片尾：左照右字` | `靜止` | `無切換` | dobe-5575.jpg |
| ED-03 | 3:55.5–4:00 | 4.5 秒 | `片尾：左照右字` | `靜止` | `淡出至黑 1s` | — |

> 片頭片尾卡的運鏡、字卡、素材只給人看，渲染以參數表為準；片尾 `淡出至黑 1s` 會寫入參數 `fadeOut`。

> ⚠️ 片頭 OP-01～03、片尾 ED-01～03 的分段時間是依樣式時間軸推定的示意，與 v1 稿的卡片分段不一定相同；渲染只用片頭片尾的起訖與參數表，不受分段影響。
