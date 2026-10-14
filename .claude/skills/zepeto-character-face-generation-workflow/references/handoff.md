# ZEPETO 大頭產線的交接格式

生成端 `zepeto-analyze-photo-3d-model`、後處理端 `zepeto-avatar-crafter`、可動臉端 `zepeto-face-rigger` 之間只靠這個資料夾交接；三邊都以本檔為準。

## 資料夾

```
.claude/docs/data/blender/zepeto/<名稱>/        ← OUT；名稱小寫英數與 -（例：groom、bride）
├── source/photo.<jpg|png>                       生成端：使用者照片的副本（不進版控）
├── analysis.md                                  生成端：五官分析表、描述、每次生成的紀錄
├── stylized_face_generated.obj                  生成端：模型（臉朝 +Z、Y 朝上）
├── stylized_face_generated.mtl                  生成端：材質設定，指向下面兩張貼圖
├── stylized_face_generated_diffuse.png          生成端：顏色貼圖（後處理端只用這張）
├── stylized_face_generated_normal.png           生成端：凹凸貼圖
├── stylized_face_generated_metallic_roughness.png   生成端：光澤度貼圖（OBJ 格式記不了，.mtl 沒引用）
├── stylized_face_zepeto.blend                   後處理端：成品（不進版控，可由 OBJ＋postprocess.py 重建）
├── qa/front.png、34.png、side.png、back.png     後處理端：驗收渲染
└── rig/                                         可動臉端（zepeto-face-rig 產線，run_face_rig.py --work 指這裡）
    ├── face.json                                這張臉的設定（第一次跑自動寫；眼睛、唇縫、髮色等自動偵測不準時手動改這裡）
    ├── eyes.json、landmarks.json                眼睛偵測結果、五官位置
    ├── cage/                                    籠子：模板包到 AI 頭上＋52 表情（中間檔，可刪）
    ├── xfer.blend、face.blend、pack.blend       中間檔：表情轉移後／材質眼睛後／整理成交接格式後（可刪，--steps 從某一步重跑時會用到）
    ├── diffuse_blackhair.png                    成品貼圖的原檔（已打包進 head_rig.blend，成品不讀它）
    ├── head_rig.blend                           成品：AI 網格＋52 表情＋控制骨架＋長髮已避開身體，貼圖打包在裡面
    ├── head_rig_<日期>.blend、preview_<日期>/    封存的舊版
    ├── check/                                   自動檢查：report.html、summary.json、總表、五官近照、張嘴序列、耳朵 ear.png、後頸 nape.png（不進版控）
    └── preview/                                 mat_front／mat_34 的 _ai 對 _new、sheet_combos.png、sheet_keys.png（52 表情，最後才產）、rig.png、body_side.png
```

`.blend` 與 `rig/cage/`、`rig/check/` 都不進版控。52 表情影格、試接的身體（`body_try/`）放 `D:\render-work\blender-work\zepeto-rig\<名稱>\`，不放專案裡。

2026-10-14 之前用舊路線（模板當成品）做的資料夾還留著 `aligned.blend`、`wrapped.blend`、`head_v1.blend`、`head_arkit.blend`、`head_color.png`：舊版 `head_rig_<日期>.blend` 和更早出廠的身體會讀 `head_color.png`，**不要刪**。

## 交接條件

| 從 → 到 | 條件 |
| --- | --- |
| 生成端 → 後處理端 | `stylized_face_generated.obj` 與 `_diffuse.png` 都在；`export_obj.py` 的 `readback_ok` 是 true，且讀回物件的正面截圖看得到臉；生成時正面、側面、背面都看過 |
| 後處理端 → 可動臉端 | `verify.py` 的數值都對；四張驗收圖都看過；`stylized_face_zepeto.blend` 裡有物件 `ZEPETO_Head` |
| 可動臉端 → 使用者 | `check/summary.json`：`total_issues` 0、`rest_nonzero` 0、`rig_ok` true、長髮插進身體 0 點；`check/report.html` 與 `preview/` 的圖都看過 |
| 使用者 → 身體端 | 使用者看過說可以 → 主控端寫狀態紀錄 `released`（見入口 skill 第 6 節）。成品的物件、材質名照舊頭（`Head`、`Hair`、`Ears`、`ZEPETO_Skin`、`ZEPETO_Lips`、`Face_Rig` 的 `head` 骨頭），服裝、動畫兩端程式不用改。**脖子接口環**（2026-10-14 起）：Head 有 `neck_ring_ver`、點屬性 `neck_ring`（48 點），身體端照抄座標接上，合約見 `zepeto-face-rig/references/ai-mesh-route.md`「頭身接縫」 |

## 座標慣例

- Rodin 匯入 Blender 時，臉朝 **−Y**（Blender 的正面）。生成端**不轉方向**。
- OBJ 以 forward −Z、up Y 匯出／匯入，所以在 Y 朝上的軟體裡臉朝 +Z。
- 成品 `.blend` 裡頭的原點在模型幾何中心、位於世界原點，鏡頭在 (0, −5.6, 0.05) 朝 +Y 看。

## 腳本

| 檔案 | 誰用 | 在哪跑 |
| --- | --- | --- |
| `scripts/work_scene.py` | 生成端 | GUI Blender（MCP `execute_blender_code` 裡 `exec`） |
| `scripts/export_obj.py` | 生成端 | GUI Blender（同上） |
| `scripts/postprocess.py` | 後處理端 | 背景 Blender（`-b --factory-startup`） |
| `scripts/verify.py` | 後處理端 | 背景 Blender（`-b <blend>`） |
| `zepeto-face-rig` skill 的 `scripts/run_face_rig.py` | 可動臉端 | 系統 Python，它自己叫背景 Blender（長髮步驟會借身體端的 `body_build.py` 試接身體，只讀不改） |
