---
name: blender-character-build
description: 從使用者的 VRoid 臉部模型（.vroid）與真人照片（大頭照、全身正面、全身背面）建出可演出的 3D 角色 —— 建專案資料夾、匯入 VRM、補回 VRoid 刪掉的皮膚、360° 檢查（01 身體完成度）、跑動作測試（02，用 blender-motion-library）、照照片或描述做服裝（03，規格驅動的 costume.json），以及事後依描述或新照片改服裝。blender-creator 子代理的工作手冊。
compatibility: Blender 5.2＋VRM add-on＋Blender MCP（GUI 要開著）、Python 3.10+（Pillow）、ffmpeg
metadata:
  version: "1.0"
  verified: 2026-10-04 以新娘專案驗證：build_costume 由 pink-ballgown.json 重建的禮服與原版一致；showcase、run_scene、export_media、gen_page 重構後實跑通過
---

# 建角色（01～03）

```
.vroid ＋ 照片 ＋ 描述
  │ ① new_project.py（檢查輸入、建資料夾、找 VRM）── 沒有 VRM → blocked：請使用者在 VRoid Studio 按 F8 匯出
  ▼
PROJ/project.json ── ② GUI：character_setup（匯入、改名、拆材質）→ body_fill（補皮膚）→ 便服 → 存 <名稱>.blend
  ▼
01 身體完成度 ── showcase MODE=base（全身/臉 360°、手勢、表情、腳）
02 動作測試   ── run_analyse（30 個＋擴充）→ 修到通過 → render_actions
03 服裝       ── 照片＋描述 → costume.json → build_costume → showcase MODE=costume → 對照照片修
  ▼
export_media.py → PROJ/videos、PROJ/pictures（給 blender-report-page 做網頁）
```

腳本：本 skill `scripts/`（下文 `$CB`）＋ [[blender-motion-library]] 的 `scripts/`（`$ML`，含開機檔與 `bl_cli.py`）。逐步指令見 [references/pipeline.md](references/pipeline.md)。

## 1. 輸入規則

| 輸入 | 規則 |
| --- | --- |
| 臉部模型 | **只收 `*.vroid`**。其他副檔名（含 .vrm、.fbx）直接拒收並回報。 |
| VRM | VRoid MCP 不能匯出 VRM。找「同資料夾同檔名的 .vrm」或 `PROJ/source/model.vrm`；都沒有就 `blocked`，請使用者用 VRoid Studio 開 .vroid → F8 → VRM 1.0 存到指定路徑。 |
| 大頭照 | 選填。看髮型、髮色、配件（耳環、髮飾）、膚色。 |
| 全身正面／背面照 | 03 服裝的主要依據；沒有就只能照描述做，網頁上會少「和照片對照」。 |
| 描述 | 原話存進 `project.json.description`；性別/體型影響 `body.bust`（`--bust yes|no`）。 |
| 專案名稱 | 小寫英數與 `-`。同名專案已存在 → 視為「繼續／修改」，不覆蓋既有輸入。 |

## 2. 鐵律

1. **VRM 匯入只能在 GUI Blender**，而且「開新檔」和「匯入」要分兩次 MCP 呼叫（同一次呼叫裡 window 是 None，匯入器會炸）。
2. **基礎檔 `<名稱>.blend` 不放服裝**；服裝存 `<名稱>_costume.blend`。改服裝永遠從基礎檔重建，不在舊服裝上疊。
3. **轉台要轉角色、不要轉相機**：燈光固定，背面才打得到光（MToon 背光面是粉色陰影，接縫和破洞都看不出來）。
4. **檢查一定要看圖**：每一步用 `Read` 看渲染出的檢查圖。「程式跑完」不算檢查。
5. **影格放 WORK（系統暫存）**，成品才進 `PROJ/videos`、`PROJ/pictures`。

## 3. 01 身體完成度

- `character_setup.skin_holes()` 看破洞：上半身有大環（胸口、背、上臂）＝要補。服裝會露出那些地方（平口、露肩、無袖）或要展示便服時一定要補；全包的服裝（西裝、長袖）可以不補。
- `body_fill.run_fill()` 一鍵補，然後渲染 `fill_check` 檢查：接縫有沒有線、顏色有沒有差、背面有沒有凸起。細節與調整方法見 [references/body-fill.md](references/body-fill.md)。
- 便服：`outfit_lib.make_base_top()`（平口小可愛）＋ VRoid 原本的短褲和鞋。男性或不需要時用 VRoid 原本的上衣（`MANIFEST.base_parts`）。
- 展示：`showcase MODE=base` → `export_media --only showcase`。

## 4. 02 動作測試

照 [[blender-motion-library]]：`run_analyse`（全部）→ 把第一輪結果另存 `QA/metrics_first.json`（網頁要顯示修正前後）→ 不通過的修到通過（體型不同時多半是 TUNE 類，用 `fit.py` 調、存 `QA/tune.json`）→ `render_actions` → `export_media --only actions`。

## 5. 03 服裝

1. 看照片（`Read` 原圖），把看到的東西逐項寫進 `PROJ/costume.json`：先複製最接近的預設（`LIB/costumes/*.json`），再改顏色、元件開關、尺寸。規格欄位與「照片 → 規格」對照見 [references/costume-spec.md](references/costume-spec.md)。
2. `build_costume`（背景 Blender）→ 看 `WORK/check/costume/` 的 8 張檢查圖，和照片並排比，修規格再建，直到輪廓、顏色、主要配件都對上。
3. `showcase MODE=costume`（360°、正背面、穿著服裝動起來）→ `export_media --only showcase,refs`。
4. 規格做不到的部位（西裝外套、褲子、袖子…）：在 `PROJ/scripts/costume_extra_<名>.py` 寫 `build_extra(M, spec)`，用 `outfit_lib` 的 `shell_piece`／`sleeve`／`v_cut`／`pinch`，物件名稱用 `<WHO>_Cos_` 前綴，規格 `extra_scripts` 列出它。

**改服裝**（使用者給描述或新照片）：讀現有 `costume.json` → 改 → 重跑第 2～3 步。改了什麼、為什麼，寫進回報。

## 6. 常見坑

見 [references/pitfalls.md](references/pitfalls.md)（輪廓線描出接縫、法線貼圖、鞋子材質、MCP 120 秒、Blender 長時間渲染當掉…）。
