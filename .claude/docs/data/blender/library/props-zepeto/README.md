# ZEPETO 黏土風道具素材庫

場景與道具的共用素材庫，風格和 ZEPETO 大頭一致：霧面黏土、邊角全部倒圓、造型加粗、粉嫩低彩度。

- **自建**：用 Blender 程式建模，不用標註作者。
- **下載**：匯入後自動換成同一套黏土材質。CC BY 的素材記在 `ATTRIBUTION.md`。

**要新增場景或道具，用 `/zepeto-scenes-generation-workflow`**。可以給情境描述、參考照片（Alt+V 貼上或 @圖片檔），或兩者都給。流程寫在 `.claude/commands/zepeto-scenes-generation-workflow.md`。

- 第一批（2026-10-11）：V12 開場影片 3D 幕（②③⑤⑦a⑦b⑧）用到的 26 樣道具，加上 4 個場景示意。
- 第二批（2026-10-12）：開場片提案 B 的婚宴會館，10 樣道具（`lounge_door`、`ballroom_doors`、`pillar`、`door_frame`、`buffet_table`、`mini_cake`、`valet_sign`、`car_key`、`dslr`、`photo_backdrop`）＋3 個場景外掛（`venue_corridor`、`venue_photo_zone`、`venue_foyer`）。
  - 三個場景共用一組座標：角色走 y＝0 往 +X，鏡頭在 y＝-3，牆面在 y＝0.75（2026-10-12 照動畫端走位從 1.2 移過來）；只有走廊的牆（連同休息室門）在 y＝1.52（2026-10-13 讓出新娘走線：新娘走 y≈0.69、裙擺半徑 0.32），轉角 x 10.2 有側牆接起來。動畫端用的座標 x 比素材庫少 0.654（休息室門中心在 x -0.654）。走廊 x -3.0～10.2 → 攝影區 10.2～14.8 → 門廳 14.8～19.6（2026-10-13 B3 拉長，攝影區、門廳整段 +3.3 m；走廊 x 6.4 以後是牆面 y 1.9 的泊車區凹處），三個一起擺在原點就接成一條連續的會館。每鏡的站位寫在各場景檔開頭。
  - 比例照 ZEPETO 角色（新郎 1.48～1.50 m）：門照動畫端定的 0.75×1.75 m 同比例縮，大門 1.7×2.2 m、門框 1.7×2.1 m；手碰的東西照手長縮。
  - 門片是獨立物件、原點在門軸：要開門用 `append_prop`，再轉門片的 `rotation_euler.z`（休息室門 0 → -90°；大門左 +90°、右 -90°）。
  - 場景外掛可加 `figures`（灰色比例人形）、`views`（各鏡頭視角）、`context`（示意圖補隔壁的牆與地板）；這三樣只出現在示意圖，不進素材庫。**場景檔的模組常數要加檔案前綴**：所有外掛共用同一個命名空間，同名會互相蓋掉。
- 展示頁：https://claude.ai/artifact/JSpQF8txGhkEgckXeL6d9w
  - 頁面由 `make_page.py` 產生，存在 `index.html`。**展示頁不進版控、發布前產生**（2026-10-14）：內嵌圖片後約 5 MB、和 `previews/` 重複，clone 後要看就先跑一次 `make_page.py`。
  - 重發布時帶這個網址當 `url`。**一律用 `python make_page.py --inline`**：圖片轉成 base64 內嵌（約 5 MB），不用帶 `files`。使用者在 Claude app 看不到外部圖檔（2026-10-12）。

## 資料夾

```
props-zepeto/
├── build_props.py           建模＋匯入＋算預覽＋標資產（自建道具的 @item 寫在這裡）
├── external_items.py        下載素材的登記：一個模型一行 ext_item()
├── scenes/<key>.py          場景外掛（範本 scenes/_example.py；底線開頭的不會讀）
├── use_props.py             在別的場景載入道具：place_prop()／append_prop()／list_props()
├── catalog.json             目錄：代號、中文名、用在哪、尺寸（公尺）、分類、預覽圖、外部來源（build_props 產生）
├── sources.md               ⭐ 素材來源清單：網站、搜尋網址、授權、註冊條件、適合度＋查詢紀錄
├── ATTRIBUTION.md           CC BY 素材的作者標註
├── refs/<key>/              參考照片副本（不進版控）＋ analysis.md（照片分析，進版控）
├── external/<代號>/source/   下載的模型原檔（不進版控；網址在 external_items.py）
├── previews/items/<代號>.jpg   單品 3/4 視角（900×900）
├── previews/scenes/<key>.jpg   場景示意（1600×900）
├── page.json、page_style.css、make_page.py → index.html   展示頁（index.html 不進版控，發布前產生）
├── blender_assets.cats.txt  Asset Browser 的分類（build_props 產生）
└── zepeto_props.blend       ⛔ 不進版控（約 8MB）：clone 後先重建一次
```

## 重建

```bash
BL="C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
"$BL" -b --factory-startup -P build_props.py && python make_page.py          # 整套約 30 秒
"$BL" -b --factory-startup -P build_props.py -- SCENE=<key> OUT=D:/render-work/zepeto-props/try   # 只試一個場景＋它的道具
"$BL" -b --factory-startup -P build_props.py -- ONLY=arch,taxi OUT=D:/render-work/zepeto-props/try  # 只試幾樣道具
```

- 試做時一定要給 `OUT=`。程式會擋住沒給 `OUT` 的 `ONLY=`／`SCENE=`，避免半套結果蓋掉素材庫。
- `EXTRA_DIR=<資料夾>`：另外讀那裡的 `external_items.py` 和 `scenes/`。測試用，不會放進素材庫。
- 外部素材的原檔不在（例如剛 clone）會印 `EXT_MISSING` 並跳過那一樣，其他照常建。

## 用法

**程式（情境、製作腳本）**

```python
exec(open(r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\library\props-zepeto\use_props.py", encoding="utf8").read())
place_prop("arch", (0, 0.3, 0))                    # 集合實例：輕、可擺很多個、跟著素材庫更新
place_prop("chicken", (0, 0, 0.75), rz=20)         # 桌面高 0.75 m
col = append_prop("taxi")                          # 複製一份真物件：要改形狀、拆零件、打關鍵影格時用
```

**手動（Blender 介面）**：偏好設定 → File Paths → Asset Libraries 加入本資料夾，Asset Browser 就能直接拖道具進場景。

## 慣例（新增道具也照這些）

| 項目 | 規則 |
| --- | --- |
| 集合 | 一樣道具一個集合，名稱 `ZP_<代號>`。自建的寫 `@item("代號", "中文名", "用在哪", cat="分類key:中文")` 函式；下載的寫 `ext_item(...)`。兩種都會自動建、算預覽、標資產 |
| 代號 | 小寫英數與底線，不能和 `catalog.json` 已有的重複 |
| 座標 | 原點在底部中心（放地上或桌面就是 z＝面高）、正面朝 **-Y**、真實尺寸（公尺） |
| 材質 | `clay(色票名)`：粗糙度 0.75、SSS 權重 0.3、縮放 0.05（和大頭同一組）。SSS 半徑用中性 (1,1,1)：大頭的偏紅半徑會讓淺色道具的陰影泛粉紅 |
| 造型 | 方的用 `p_box`（倒角＋平面維持銳利），圓的用 `p_cyl`／`p_lathe`（旋轉成形）／`p_sphere`，管狀用 `p_tube`；細的部分加粗 1.3～1.5 倍 |
| 下載素材 | `ext_item` 匯入後：只留網格、同平面三角形合回整面、倒圓（最長邊 4%）、原色粉嫩化（飽和 ×0.65、亮度往白 20%）。可用 `colors` 指定、`bevel`／`sat`／`light` 調整 |
| 配色 | 色票在 `PAL`；新顏色先加進 `PAL` 再用 |
| 分類 | V12 第一批：garden／carpet／dinner／street；之後：studio（攝影棚）、daily（日常小物）、venue（婚宴會館）；新的用 `cat="key:中文"` 自動登記 |
| 算圖 | EEVEE、AgX Medium High Contrast（Medium Low 會太灰）、軟太陽光 22°；場景示意白天天空 `#A9CFF0`、夜晚 `#1E2748` |

## 還沒做的

- 計程車右後門還沒拆成獨立零件（⑦b 新郎要開門上車；現在影片用的是 3D Warehouse 的 Camry）。
- 還沒換進 V12 各幕的製作程式。現在的預覽影片仍用 `productions/opening-v12/scripts/set_*.py` 的舊道具。
- V12 第一批的 4 個場景示意還寫在 `build_props.py` 的 `build_scenes`，還沒改成 `scenes/` 外掛。
