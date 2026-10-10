---
name: blender-motion-library
description: VRoid 角色在 Blender 裡的共用動作庫與檢查工具 —— 開機檔 blender_env（專案路徑、物件前綴、暫存區）、姿勢工具 pose_lib（世界軸角度慣例、8 種手勢、表情、IK、前臂扭轉、腳底自動貼地）、30 種預設動作 actions（＋擴充 actions_custom）、自動檢查 check_lib（穿模／腳底／每格轉角）、動作渲染（含頭髮物理）、背景 Blender 入口 bl_cli。建角色跑動作測試、擴充新動作、在情境裡擺姿勢時使用。
compatibility: Blender 5.2（VRM add-on、Blender MCP）、Python 3.10+（Pillow）、ffmpeg
metadata:
  version: "1.0"
  verified: 2026-10-04 以新娘專案（projects/bride）重跑 30 個動作，30/30 通過；重構後 nod／think 數字與重構前完全相同
---

# Blender 動作庫

```
blender_env.py ── 每支 Blender 端腳本先 exec 它：PROJ / WHO / WORK / QA / LIB / use()
   │
   ├─ pose_lib.py    角度慣例、手勢 HANDS、表情 set_face、IK ik_arm、twist_forearm、face_palm、pose_frame（貼地）
   ├─ actions.py     30 個預設動作 ACTIONS／ACT（＋ actions_custom.py 的擴充動作）、TUNE 參數、bs() 體型縮放
   ├─ check_lib.py   Checker：穿模（手/前臂 vs 身體頭、雙手互穿、雙腿互穿）、腳底高度、每格轉角
   ├─ run_analyse.py → QA/metrics.json        render_actions.py → WORK/actions/<代號>/ ＋ QA/motion.json
   └─ fit.py / contact_shots.py（碰觸姿勢微調與近照）、studio.py（棚燈相機）、render_lib.py（分段渲染）
```

腳本在 `.claude/skills/blender-motion-library/scripts/`（下文 `$ML`）。

## 1. 兩種執行方式

**GUI Blender（Blender MCP）**：短的、要即時看結果的操作。⚠️ 一次呼叫只有 120 秒，超過會回「No data received」但 Blender 仍在跑。

```python
PROJECT = r"D:\SideProject\wedding-invitation\.claude\docs\data\blender\projects\<名稱>"
exec(open(r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts\blender_env.py", encoding="utf8").read())
use("studio", "pose_lib", "actions")
pose_frame(ARM, ACT["wave"][1](0.25))
```

**背景 Blender（Bash）**：長的渲染與檢查，可和 GUI 並行、不受 120 秒限制。

```bash
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b "<PROJ>/<名稱>.blend" -P "$ML/bl_cli.py" -- --project "<PROJ>" --run run_analyse KEYS=wave,clap FORCE=true
```

成功最後一行印 `BL_CLI_DONE`，失敗印 `BL_CLI_FAIL` 加 traceback。用 Bash 的 `run_in_background` 跑，完成再讀輸出。完整參數見 [references/cli.md](references/cli.md)。

## 2. 路徑規則

| 變數 | 位置 | 放什麼 |
| --- | --- | --- |
| `PROJ` | `.claude/docs/data/blender/projects/<名稱>/` | project.json、.blend、costume.json、qa/、pictures/、videos/ |
| `WORK` | `D:/render-work/blender-work/<名稱>/`（環境變數 `BLENDER_WORK_ROOT` 可覆寫；沒有 D 槽才退回 `%TEMP%/blender-work/`） | 影格 png、檢查圖（量大，⛔ 不進 repo） |
| `QA` | `PROJ/qa/` | metrics.json（穿模/腳底）、motion.json（轉速）、metrics_first.json（第一輪）、tune.json |
| `LIB` | `.claude/docs/data/blender/library/` | 預設庫：actions_catalog.json、tune_default.json、costumes/、textures/、previews/ |

物件一律以 `WHO`（project.json 的 `who`）為前綴：`<WHO>_Armature`、`_Body`、`_BodyFill`、`_Face`、`_Hair`、`_Shoes`、`_Cos_*`（服裝）。

## 3. 姿勢怎麼寫

一個動作＝函式 `t∈[0,1) → 姿勢 dict`，頭尾相接。dict 的鍵：骨頭（`"L_UpperArm": [("Y", 72), ("X", -20)]`，世界軸、依序轉）、`hands`、`ik`、`twist`、`palms`、`root`、`rz`、`hop`、`ground`、`face`。角度慣例、IK、貼地的規則見 [references/conventions.md](references/conventions.md)。

⛔ 三個一定會踩的坑：

1. **手要碰到身體或道具就用 IK**，不要掃角度湊。掃角度在「思考」這種姿勢會卡在 2～7 公分誤差。
2. **掌心轉向接近 180° 會翻面**（畫面突然甩一下）。固定角度用 `twist`，不要用 `palms`。
3. **IK 目標不能超出手臂長度**。伸直後再回到構得到的範圍，手肘會一格彎回來（速度突變）。

## 4. 檢查標準（入庫門檻）

| 項目 | 通過 | 怎麼量 |
| --- | --- | --- |
| 穿模 | ≤ 5 mm（碰觸類動作見例外） | 手/前臂頂點對身體＋頭、雙手互相、雙腿互相；最近點＋平滑法線＋射線交叉確認 |
| 腳底 | 不陷地（≥ −0.5 cm）、不浮空（≤ 0.5 cm，跳躍類除外） | 鞋底取樣點 |
| 流暢 | 身體骨頭每格 ≤ 15°、速度突變 ≤ 6；腳踝、腳趾（Foot、ToeBase）另計每格 ≤ 35°、不套速度突變 | 渲染時逐格量（手指另計不擋）。腳踝腳趾另計是 2026-10-08 套用真人走路時定的：蹬地那幾格腳踝本來就會到 20～32°/格 |
| 滑步 | 著地腳每格 ≤ 1 mm（真人走路 `walk_fwd` 的 `style='mocap'` 例外 ≤ 1.1 mm）、整段累計 ≤ 5 mm（`slide_step`／`slide_total`） | 鞋底取樣點離地 5 mm 內算著地，量相鄰兩格的水平位移。真人走路的例外（2026-10-08）：步幅 0.4～0.5 m 時腳跟著地後腳掌放平那一格量到 1.04～1.08 mm（1 px ≈ 3 mm，看不出來）。2026-10-05 才加；`walk`、`turn`、`spin`、`curtsy`、`squat`、`march`、`jump` 目前超標（使用者還沒決定要不要修），網頁也還沒顯示這一項 |

數字沒過不准說「通過」。手指交握、手搭在衣服上會量到幾毫米接觸 —— 要用 `contact_shots` 拍近照目視，確認後在 actions_catalog 的 `contact_note` 寫原因。細節見 [references/qa-checks.md](references/qa-checks.md)。調整階段怎麼縮短每一輪（快速預覽、多角度檢查圖、一次收齊問題、瀏覽器即時預覽）見 [references/fast-iteration.md](references/fast-iteration.md)。

**2026-10-10 起動作一律用 Mixamo 現成動畫原樣套上**（不再用 CMU）：`scripts/mixamo_retarget.py`（FBX → VRoid 骨架、接段、0.3 秒漸變），多幕影片先審骨骼（樣板 `assets/skeleton_review/viewer.html`）、再審低畫質預覽，兩關網頁都要有回覆框＋Ctrl+V 貼圖。規則見 fast-iteration.md §0、§0.5。

## 5. 預設資料庫

手勢 8 種、表情 13 個鍵、腳（鞋底貼地）、30 種動作、粉色蓬裙禮服 —— 全部來自新娘專案，清單與預覽圖見 [references/library-defaults.md](references/library-defaults.md)、30 個動作的參數與檢查數字見 [references/actions-catalog.md](references/actions-catalog.md)。擴充新動作的流程見 [references/adding-actions.md](references/adding-actions.md)。
