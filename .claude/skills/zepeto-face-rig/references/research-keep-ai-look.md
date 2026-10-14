# 研究：保住 AI 生成頭的外觀，又能做 ARKit 表情（2026-10-13）

> 起因：使用者「目前 AI 生成的效果很好，但是開始捏表情就會開始偏掉，要能捏成像 AI 生成的那樣」，
> 接著定目標「先以能夠透過 blender 捏出和 AI 生成的頭一致表情為目標」。
> 研究員（general-purpose 子代理）上網查做法＋做最小實驗後的報告整理；實驗檔在
> `D:/render-work/blender-work/zepeto-sculpt-trial/research/`（`transfer2.py`、`eyelid.py`、`compare_front.png`）。
> 結論變成 AI 網格路線（[ai-mesh-route.md](ai-mesh-route.md)）。

## 結論

1. **AI 網格當成品、模板只當「籠子」把 52 個表情轉移過去**：外型、貼圖都是 AI 原本的，因為根本沒換網格。
   舊產線的包子臉、下巴陰影、眼線對不上，都是「拿模板當成品、再把 AI 的樣子轉印上去」造成的。
2. **嘴巴**：在 AI 網格上沿畫好的唇線切縫，後面接口腔（最後做成自建口腔袋）。
3. **眼睛**：材質眼皮（閉眼時材質從上往下蓋膚色＋閉眼線），像 2D 卡通角色眨眼；眼珠也改材質畫（AI 的眼珠畫死在貼圖上，不會轉）。
4. **Blender 內建 Surface Deform 不能直接用**：綁定時報「Target contains overlapping vertices」（模板有重疊頂點）→ 自己寫轉移（重心座標綁到籠子三角形）。
5. 付費、要上傳模型的工具只當備案；**AI 生成的模型能不能上傳要使用者決定**（照片一律不上傳）。

## 做法比較

| 做法 | 怎麼保住 AI 外觀 | 眼睛、嘴巴 | 工具／費用／上傳 | 風險 |
| --- | --- | --- | --- | --- |
| **甲：AI 網格當成品＋自寫表情轉移（採用）** | 不換網格、不轉印 | 嘴：切縫＋口腔；眼：材質 | 只用 Blender＋Python，免費、不上傳 | 眼睛不會轉要另外做；長髮會被臉頰動作帶到 |
| 乙：Surface Deform 修改器 | 同甲 | 同甲 | Blender 內建 | 實測綁定失敗 |
| 丙：舊做法（模板當成品） | 靠釘點拉＋轉印顏色 | 模板本身有 | 免費 | 外型本來就會偏，越調釘點越多 |
| 丁：重新拓樸＋烘焙 | 乾淨網格貼外型、烘焙法線顏色 | 要另做 | 免費 | 換網格就對不準畫在貼圖上的東西 |
| 戊：Faceit 外掛 | 原網格上做形態鍵 | 需要真的眼皮口腔幾何 | 78～99 美元、支援 Blender 3.0～5.2、不上傳 | AI 網格沒有眼皮嘴縫，一樣做不出閉眼張嘴 |
| 己：R3DS Wrap | 同丙 | 同丙 | 舊報價約 370 美元起、不上傳 | 本質同丙 |
| 庚：Polywink | 對方在原網格做 52 表情 | 對方做 | 舊報價約 299 美元／個、**要上傳模型** | 對「眼睛畫在貼圖上」效果不明 |
| 辛：Character Creator Headshot 2、MetaHuman | 換成它們的網格 | 它們的 | 付費、換軟體 | 卡通比例失真 |
| 壬：AI 直接生成會動的頭（Meshy、Tripo、RigAnyFace） | 原網格＋形態鍵 | 不明 | 雲端**要上傳** | Meshy 宣稱有臉部形態鍵但查不到細節；Rodin、Hunyuan3D 沒有表情輸出 |

業界卡通角色（Ready Player Me、VRoid）多半是「形態鍵管臉型、眼睛嘴巴細節靠貼圖或換貼圖」，跟甲同路線。ZEPETO、Memoji 內部做法查不到官方資料。

## 畫在貼圖上的眼睛、嘴巴，動起來會怎樣

| 部位 | 不處理 | 處理（最後做法） |
| --- | --- | --- |
| 閉眼 | 畫上去的虹膜被壓扁成黑色皺摺 | 材質眼皮（`eyes_shader.py`） |
| 看方向 | 虹膜畫死，眼睛不會轉 | 程式畫的眼珠、虹膜跟著 `LOOK_*` 移（平移貼圖座標會跳到別塊，貼圖是零碎拼貼） |
| 張嘴 | 嘴唇被拉成一大片粉紅、沒有開口 | 照唇線切縫＋自建口腔袋（`transfer.py`） |
| 瞪大、瞇眼 | 只有周圍皮膚動 | 眼睛範圍用 `rest` 座標黏在皮膚上，跟著變形 |

## 來源

- Faceit：https://superhivemarket.com/products/faceit 、https://faceit-doc.readthedocs.io/en/latest/
- Sumner & Popović 2004 表情轉移：https://people.csail.mit.edu/sumner/research/deftransfer
- Landmark-Guided Deformation Transfer（ICCVW 2019）：https://openaccess.thecvf.com/content_ICCVW_2019/html/3DRW/Onizuka_Landmark-Guided_Deformation_Transfer_of_Template_Facial_Expressions_for_Automatic_Generation_ICCVW_2019_paper.html
- RigAnyFace：https://arxiv.org/html/2511.18601v1
- arkit-blendshape-tool：https://github.com/digitalp/arkit-blendshape-tool
- Morphbridge：https://superhivemarket.com/products/shapekey-transfer-addon
- R3DS Wrap：https://www.cgchannel.com/2019/06/r3ds-ships-wrap-3-4/ 、WrapX：https://cgpress.org/archives/wrapx-batch-topology-transfer-tool.html
- Polywink：https://www.cgchannel.com/?p=95681
- Headshot 2：https://manual.reallusion.com/Headshot_for_CC/ENU/2.0/06-Mesh-Mode/Intro-Mesh-Mode.html
- Mesh to MetaHuman：https://dev.epicgames.com/documentation/metahuman/from-mesh
- Meshy 自動綁定：https://www.meshy.ai/use-cases/free-game-assets/character-rigging
- Ready Player Me ARKit：https://docs.readyplayer.me/ready-player-me/api-reference/avatars/morph-targets/apple-arkit
- VRM 表情設定：https://vrm.dev/en/univrm/blendshape/blendshape_setup/

查不到或無法驗證：Faceit 詳細文件頁 404、Tripo 部落格擋爬蟲、Wrap／Polywink 只找到 2019 年舊報價。
