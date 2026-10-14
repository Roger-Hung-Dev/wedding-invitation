---
name: zepeto-face-rig
description: ZEPETO 風大頭的「可動臉」產線（AI 網格路線）—— AI 生成的頭本身當成品（外型、貼圖原封不動），通用模板只當「籠子」算出 ARKit 52 個表情再轉移到 AI 網格；照 AI 畫好的唇線切嘴縫、自建口腔袋（牙齒舌頭來自模板）、材質眼睛（眨眼、看方向）、臉部控制骨架、整理成身體端要的交接格式、長髮避開身體（自動試接一副身體來調），附自動檢查報告。使用者要「讓 ZEPETO 頭能眨眼張嘴」「做 ARKit 52 表情」「做臉部骨架」「把新的臉做成可動臉」時使用。輸入是 zepeto-avatar-crafter 產出的 stylized_face_zepeto.blend。
argument-hint: "<這張臉的資料夾（一條龍是 <OUT>/rig）>"
---

# ZEPETO 可動臉產線（AI 網格路線）

AI 生成的頭（Hyper3D Rodin）長得很像 ZEPETO，但它是一層殼：眼睛、嘴巴、眉毛畫在貼圖上，沒有眼皮、沒有口腔。這條產線**不換網格**，在 AI 頭上補出會動的東西：

- **表情**：通用模板頭先包到 AI 頭上當「籠子」（有 52 個 ARKit 表情），每個 AI 網格點綁到籠子最近的三角形，表情照籠子的動法轉移過來。
- **嘴巴**：照 AI 畫好的唇線切嘴縫，從唇縫往內長出口腔袋，牙齒、牙齦、舌頭借籠子的。
- **眼睛**：材質眼睛 —— 程式畫的杏仁形眼珠（會轉）、閉眼時材質眼皮從上往下蓋。
- **外觀**＝AI 原圖（V 臉、眼線、腮紅都在），只多了：頭髮換黑（Rodin 常生成藍灰）、皮膚亮澤（粗糙度 0.5、次表面散射 0.15，使用者選定）。

2026-10-14 取代舊路線（模板當成品、AI 的樣子轉印上去 → 包子臉、眼線對不上）。舊路線的程式封存在 `D:/render-work/archive/zepeto-face-rig-old-route-20261014/`；新郎（legacy）、新娘 v4、攝影師 v1 是舊路線做的，成品沒動。

模板：LucaDrech〈Cartoon Stylized Character Face Head Base Mesh〉，CC BY 4.0（可商用、**對外分享要標註**），
在 `.claude/docs/data/blender/zepeto/templates/cartoon-head-lucadrech/`（`ATTRIBUTION.md` 有標註原文）。成品裡的牙齒、舌頭、表情動法來自它。

## 怎麼跑

```powershell
python -u .claude/skills/zepeto-face-rig/scripts/run_face_rig.py --work <這張臉的資料夾>
```

- 一條龍（`/zepeto-character-face-generation-workflow` 的第三段）：`--work <OUT>/rig`，AI 頭預設讀 `<OUT>/stylized_face_zepeto.blend`。
- 全程背景 Blender，不碰使用者開著的 Blender；實測約 5 分鐘（新娘 280 秒，其中兩次試接身體各 45 秒）。
- 只重跑某幾步：`--steps transfer,shade,check,rig,hairfit,finish`（從某步起就把它和後面全部列上）。
- 這次換一顆 AI 頭、換身體：`--ai-blend <檔>`、`--body auto|none|<body.blend>`（只用在這一次，不寫進設定檔）。
- 每個人只留一個現役 `head_rig.blend`（身體端的頭清單只認這個檔名）：`rig` 步驟先把舊的連同 `preview/` 改名封存成 `head_rig_<日期>.blend`、`preview_<日期>/`（同一天第二次加 `_<時分>`）。
- 影格、試接的身體放 `D:/render-work/blender-work/zepeto-rig/<name>/`（`keys/`、`body_try/`、`body_side_*.png`）。

| 步驟 | 腳本 | 做什麼 |
| --- | --- | --- |
| post | 一條龍的 `postprocess.py` | （`face.json` 有 `obj` 才跑）OBJ → 後處理成 .blend；一條龍由後處理端做，不用這步 |
| eyes | `eyes_auto.py`、`eyes_find.py` | 眼睛自動偵測（貼圖原色正面圖找眼珠＋眼白）；不準時停下來叫人填 `eyes_manual` |
| landmarks | `cage/detect_landmarks.py`、`eyes_find.find_seam` | 五官位置；唇縫高度用細線偵測（閉嘴微笑的唇縫是 U 形） |
| cage | `cage/align.py`、`wrap.py`、`materials.py`、`arkit52.py` | 籠子：模板包到 AI 頭上（V 臉 `ZEPETO_CONTOUR`）＋ 52 表情 → `cage/head_arkit.blend` |
| transfer | `transfer.py` | 表情轉移到 AI 網格、切嘴縫、自建口腔袋、牙齒舌頭推到皮後 → `xfer.blend` |
| shade | `eyes_shader.py`、`gloss.py` | 材質眼睛（`BLINK_*`、`LOOK_*`）、黑髮貼圖 `diffuse_blackhair.png`、亮澤 → `face.blend` |
| check | `check.py`、`render_set.py`、`closeup.py`、`open_series.py`、`slice_colors.py` | 自動檢查數字＋總表、五官近照、張嘴序列與切片 → `check/report.html` |
| rig | `pack_head.py`、`neck_ring.py`、`face_rig.py`、`rig_check.py` | 封存舊版 → 貼圖還原成 shade 的原版 → 整理成交接格式（刪耳朵旁邊以下的頭髮碎片、頭髮和臉皮交界抹順、頭髮邊緣畫成髮色）→ **標準脖子接口環**（48 點；後頸缺皮就鋪墊底皮；環附近表情位移淡到 0）→ 控制骨架 → **`head_rig.blend`**；骨架檢查（每根控制骨頭拉到底） |
| hairfit | `hair_fit.py`（＋身體端 `body_build.py`） | 長髮避開身體：`body: auto` 照這顆頭試接一副身體來調；後頸墊底皮範圍裡的頭髮不固定在臉上；收尾把還插在身體裡的點、被頂穿的面推出去；改寫 `head_rig.blend`（同一檔只能跑一次，會擋）。只對 T 字姿勢：手臂放下時上臂會從長髮後面頂出來，交給動畫端 |
| finish | `previews.py`、`tools/shot_body_side.py` | 貼圖打包進 `head_rig.blend` → 用成品再試接一次身體、拉遠拍側面 → `preview/` 預覽圖 → `check/summary.json` |

### 設定檔 `face.json`

第一次跑自動寫一份（`name`、`ai_blend`、`body`），之後手動修正都改這裡；預設值在 `run_face_rig.py` 的 `FACE_DEFAULTS`。

| 欄位 | 預設 | 什麼時候改 | 從哪步重跑 |
| --- | --- | --- | --- |
| `eyes_manual` | 自動 | 眼睛偵測失敗或框錯：`[左眼x, 右眼x, 高度, 半寬, 半高]`，用 `check/eyes_front.png`＋`eyes_front.json` 量 | `eyes` |
| `mouth_zc` | 自動 | 嘴縫切錯位置（一張嘴整片下唇連皮膚掉下來）：唇縫中央高度 | `landmarks` |
| `mouth_cut`、`lip_smooth`、`lip_rz`、`corner_smooth`、`tongue_len` | 0.8、40、0.18、6、0.75 | 嘴巴形狀（見 ai-mesh-route.md 2.3） | `transfer` |
| `brow_gain` | 1.6 | 粗黑眉動作太誇張 → 1.2（攝影師） | `transfer` |
| `hair_rgb` | 黑 `[0.075, 0.068, 0.072]` | 只換「像頭髮又偏藍灰」的點；照片不是黑髮時填照片髮色 | `shade` |
| `iris_rgb` | 深棕 `[0.26, 0.15, 0.10]` | 照片眼睛顏色 | `shade` |
| `gloss` | `{rough: 0.5, sss: 0.15}` | 質感 | `shade` |
| `body` | `auto` | `none`＝短髮不用調、想省時間；或指定身體檔 | `rig` |
| `name` | 資料夾名 | 影格資料夾名 | — |

## 驗收（每次都要看圖，不要只看「完成」）

1. `check/summary.json`：`total_issues` 0、`rest_nonzero` 0、`rig_ok` true、`hairfit.inside_after` 0。
2. `preview/mat_front_ai.png` 對 `mat_front_new.png`（`mat_34_*` 同）：成品就是 AI 頭本身，應該幾乎一樣。
3. `check/report.html`：表情總表、嘴巴近照（正面＋兩側斜面）、眼睛眉毛近照、張嘴序列與正中切片、眼睛偵測。
4. `preview/sheet_keys.png`：52 個單一表情（`tongueOut`、`mouthClose` 照 ARKit 規格配張嘴）。單格原圖在 `D:/render-work/blender-work/zepeto-rig/<name>/keys/`。
5. `preview/rig.png`：控制骨頭拉到底；`preview/body_side.png`：接上身體拉遠看長髮。
6. `check/ear.png`：左右耳附近的髮際線；`check/nape.png`：接上身體的耳下到後頸。

## 成品裡有什麼（`head_rig.blend`）

跟舊路線同一套名字，身體、服裝、動畫三端程式不用改：

| 物件／材質 | 內容 |
| --- | --- |
| `Head` | AI 網格的臉＋脖子＋自建口腔袋，49 個 ARKit 形態鍵（眨眼改用材質，網格的 `eyeBlink*_geo` 停用）；**脖子接口環**：點屬性 `neck_ring`（1＝正前 −Y、俯視逆時針 13＝+X、25＝正後、37＝−X，其他 0）、物件屬性 `neck_ring_ver`（1）、`neck_ring_n`（48）、`neck_ring_z`、`neck_ring_yc`（本地座標＝頭檔座標）；後頸被分給頭髮的頭會鋪一片**後頸墊底皮**（從環到耳朵下面，有臉皮的地方墊在下面、缺口直接露出；點屬性 `nape_underlay`、物件屬性 `nape_patch_top`／`nape_patch_ang`） |
| `Hair` | 頭髮＋臉旁細髮絲（`strand` 屬性），同樣的形態鍵（瀏海、鬢角跟表情動）；長髮已避開身體（`hairfit_done`） |
| `Ears` | 兩隻耳朵（服裝端找耳垂掛耳環） |
| `upper_teeth`、`bottom_teeth`、`upper_gum`、`bottom_gum`、`Tongue` | 籠子的，每個表情都推到皮後；舌頭跟下顎剛體轉 |
| 材質 `ZEPETO_Face` | 臉上半部：貼圖＋材質眼珠、眼皮；控制值 `BLINK_*`、`LOOK_*`、`JAW_OPEN` |
| 材質 `ZEPETO_Skin`、`ZEPETO_Lips`、`ZEPETO_Hair`、`ZEPETO_Ears`、`LipInner` | 嘴巴以下（身體端取膚色）、嘴唇面（身體端量嘴巴位置）、頭髮、耳朵、口腔袋 |
| `Face_Rig` | `head` 骨頭（藏起來；所有零件掛在下面，轉軸在下巴往上 3.5% 頭高）＋ 11 根控制骨頭 |
| 貼圖 | 打包在檔案裡（`finish` 步驟），不讀外部檔 |

控制骨頭（從鏡頭看在臉右側，點圓圈；打開就是姿勢模式、沒選任何骨頭）：`CTRL_Jaw`（下拉張嘴、左右）、`CTRL_Smile`、`CTRL_Mouth`（上笑下撇左右）、`CTRL_Blink_L/R`、`CTRL_Eyes`（看方向）、`CTRL_Brow_L/R`、`CTRL_Brow_Inner`、`CTRL_Tongue`（下拉吐舌頭，自動帶張嘴 0.45）、`CTRL_MouthClose`（下拉＝下巴往下、嘴唇閉著）。驅動器都是簡單運算式，開檔不用允許自動執行 Python。

沒接控制骨頭的 ARKit 形態鍵（瞇眼、睜大、鼓臉頰、嘟嘴…）留給表情捕捉，值都是 0。**眨眼、左右看方向是材質數值，不是形態鍵**：表情捕捉（ARKit 直接推形態鍵）要另外把 `eyeBlink*`、`eyeLookIn/Out*` 接到 `BLINK_*`、`LOOK_*`。

## 已知限制

- 驗證過兩張臉：新娘（新描述生成、長髮、腮紅、閉嘴微笑）、攝影師（舊描述生成、短髮、圓眼、粗黑眉）。第三種臉型第一次跑仍要逐張看。
- 「閉嘴下巴」（`CTRL_MouthClose`）嘴角有一點拉扯；張到最大時下唇邊緣有一點點不平（放大才看得到）。
- 鼻子沒有專門檢查；人中有幾道 AI 網格本身的摺線。
- 右斜前方看脖子旁頭髮內側邊緣有一點不規則（AI 頭髮殼原本的切口）。
- 眼睛一律是產線的統一畫法（杏仁形程式眼珠），不照 AI 原本畫的眼珠。

## 文件與工具

- 流程、痛點總覽、每一步的做法與坑、五官檢查工具、截圖分析修正流程：[references/ai-mesh-route.md](references/ai-mesh-route.md)。
- 籠子程式（`scripts/cage/`，舊路線留下來的包覆與 52 表情）的細節與坑：[references/cage-pipeline.md](references/cage-pipeline.md)。
- 研究報告：[research-zepeto-face.md](references/research-zepeto-face.md)（ZEPETO 臉比例、舊路線為什麼不像）、[research-keep-ai-look.md](references/research-keep-ai-look.md)（保住 AI 外觀做表情的做法比較）。
- 頭和身體怎麼無縫接合（業界做法、標準脖子接口環方案、後頸深色鋸齒的實測）：[research-head-body-seam.md](references/research-head-body-seam.md)。還沒實作，等使用者決定。
- 除錯、近照工具在 `scripts/tools/`（用法見 ai-mesh-route.md 第 3 節；接身體之後的檢查順序見 4.1）：五官近照 `scripts/closeup.py`；耳朵 `ear_closeup.py`、後頸 `nape_closeup.py`、缺皮 `nohair_view.py`、截面 `neck_section.py`、頭髮體檢 `hair_check.py`、近照找部位 `probe_pick.py`、張嘴喉嚨 `jaw_side.py`。改了 `check.py` 要用壞版本 `D:/render-work/blender-work/zepeto-sculpt-trial/bride/route_badcage/` 驗證仍抓得到問題。
- `cage/prep_template.py` 只在換模板時跑一次（整理模板、找模板的五官）；`cage/preview_wrap.py` 是包覆比對圖。
