# photographer — 風格分析與生成紀錄

- 照片：**無**。使用者 2026-10-12 決定用通用路人頭，依文字設定做（不用真人照片）。
- 角色：開場片配角「婚禮攝影師」。一般成年亞洲男性、乾淨短黑髮、無任何配件、溫和微笑。配角不搶戲、五官普通，和新郎同一類型（短髮）。
- 生成：Hyper3D Rodin 文字生成（只送文字）
- 日期：2026-10-12

## 五官設定（依文字）

| 部位 | 設定 | 轉成 ZEPETO 風格的英文 |
| --- | --- | --- |
| 髮型 | 乾淨短黑髮，頭頂自然、短瀏海；後面與兩側剃短 | neat short black hair with a soft natural fringe, smooth rounded top, tightly cropped back and sides |
| 眉毛 | 普通、自然平直、深色 | soft straight dark eyebrows |
| 眼睛 | 一般深棕 | large round dark brown eyes |
| 鼻子 | 普通 | cute tiny nose |
| 嘴與表情 | 溫和微笑、閉嘴 | gentle closed-mouth warm smile |
| 臉型、下巴 | 普通圓潤臉 | soft rounded face with a smooth rounded chin |
| 耳朵 | 短髮露耳 | small ears visible |
| 膚色 | 一般亞洲膚色 | light warm beige skin tone |
| 配件 | 無（不寫進描述，避免用否定句） | — |

## 最後用的描述

```
Stylized 3D cartoon head bust of a young adult East Asian man, ZEPETO K-pop avatar style, smooth matte clay texture, large round dark brown eyes, soft straight dark eyebrows, cute tiny nose, gentle closed-mouth warm smile, soft rounded face with a smooth rounded chin, small ears visible, neat short black hair with a soft natural fringe, smooth rounded top, tightly cropped back and sides, light warm beige skin tone, head and neck only
```

## 生成紀錄

共生成 1 次（用掉 1 次 Rodin 免費試用額度）。

| 次 | 結果 | 尺寸（x, y, z） | 正面 | 側面 | 背面 |
| --- | --- | --- | --- | --- | --- |
| 1 | 通過 | 1.335 × 1.39 × 1.901（深度／高度 0.731） | 大圓深棕眼、粗平黑眉、小鼻、閉嘴溫和微笑；黑短髮，瀏海斜向一側；只有頭和脖子；無配件 | 短髮收在後頸上方，沒有馬尾或長髮；耳朵露出 | 整片圓順黑短髮，無綁髮、無配件 |

## 匯出

- `stylized_face_generated.obj`：18,712 頂點、23,332 面
- 貼圖 3 張：diffuse、normal、metallic_roughness
- 讀回驗證：最大誤差 1e-06（`readback_ok: true`）；讀回物件正面截圖看得到臉

## 跟設定不同的地方

- 描述寫 tightly cropped back and sides，實際後腦與兩側是一整片圓順短髮蓋住，沒有剃短的層次；仍是短髮，不影響。
- 眉毛偏粗；右眉上緣有一小塊淺色亮點（貼圖小瑕疵）。
