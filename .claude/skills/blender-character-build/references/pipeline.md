# 建角色：逐步指令

以下 `$REPO=D:/SideProject/wedding-invitation`、`$CB=$REPO/.claude/skills/blender-character-build/scripts`、`$ML=$REPO/.claude/skills/blender-motion-library/scripts`、`$BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"`、`$P=$REPO/.claude/docs/data/blender/projects/<名稱>`。

## ① 建專案（系統 Python）

```bash
python "$CB/new_project.py" --name <名稱> --vroid "<.vroid>" --face "<大頭照>" --front "<全身正面>" --back "<全身背面>" \
       --desc "<使用者原話>" [--who <物件前綴>] [--bust yes|no] [--vrm "<已匯出的 .vrm>"]
```

輸出一行 JSON。`ok:false` → 把 `errors` 原樣回報（例：「臉部模型只接受 .vroid 檔」）。`vrm_status: needs_vrm_export` → `blocked`，把 `next` 欄的指示原樣回報。

## ② 匯入與整理（GUI Blender，Blender MCP）

先 `get_addon_status` 確認 Blender 開著、MCP 連得上。目前開著的檔若有未存變更（`bpy.data.is_dirty`），先回報，不要直接開新檔蓋掉。

```python
# 呼叫 1
PROJECT = r"<$P 的 Windows 路徑>"
exec(open(r"<$ML>\blender_env.py", encoding="utf8").read()); use("character_setup")
new_empty_file()
```

```python
# 呼叫 2（每次 MCP 呼叫都是新的命名空間：一律重設 PROJECT、重新 exec 開機檔）
PROJECT = r"<$P>"
exec(open(r"<$ML>\blender_env.py", encoding="utf8").read()); use("character_setup")
import_vrm(); print(organize()); print(skin_holes()[:6]); print(save_base())
```

`organize()` 回傳拆出來的部位（Body、HairBack、Tee、Shorts、Shoes…）。物件名稱都會是 `<WHO>_*`。

## ③ 補皮膚（GUI 或背景都可）

```python
use("studio", "outfit_lib", "body_fill")
print(run_fill())                      # {verts, snapped, band_faces_removed, scale, bust}
```

檢查圖（GUI）：

```python
use("studio")
O[f"{WHO}_Hair"].hide_render = True; O[f"{WHO}_HairBack"].hide_render = True
for tag, (loc, tgt) in {"f": ((0,-1.0,1.2),(0,0,1.17)), "armfront": ((0.22,-0.45,1.27),(0.2,0,1.27)),
                         "armback": ((0.22,0.45,1.3),(0.2,0,1.27)), "waist": ((0.35,0.35,1.02),(0,0,1.02))}.items():
    aim(O["Camera"], tuple(v*S_BODY for v in loc), tuple(v*S_BODY for v in tgt), 50)
    shot(os.path.join(WORK, "check", f"fill_{tag}.png"), (500, 500))
```

背面接縫要用「轉角色」看：`ARM.rotation_euler = (0,0,math.radians(180))` 再拍正面相機。

## ④ 便服、存檔

```python
use("outfit_lib"); make_base_top()       # 女性；男性跳過，改設 MANIFEST["base_parts"] = [f"{WHO}_Tee", f"{WHO}_Shorts"]
use("costume"); wear("base"); save_manifest()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROJ, MANIFEST["blend"]["base"]))
```

## ⑤ 01 展示

```bash
"$BL" -b "$P/<名稱>.blend" -P "$ML/bl_cli.py" -- --project "$P" --run showcase MODE=base
python "$REPO/.claude/skills/blender-report-page/scripts/export_media.py" --project "$P" --only showcase,refs
```

看 `PROJ/videos/turn_body.mp4` 的封面、`pictures/hands_sheet.jpg`、`face_feet.jpg`。project.json 寫 `stages.01 = "done"`，`report.s1_text`／`s1_facts` 寫這個角色實際做了什麼（補了哪裡、哪些沒補）。

## ⑥ 02 動作測試

```bash
"$BL" -b "$P/<名稱>.blend" -P "$ML/bl_cli.py" -- --project "$P" --run run_analyse     # 約 30 個 × 20 秒
cp "$P/qa/metrics.json" "$P/qa/metrics_first.json"                                    # 第一輪留底
# 修不通過的（見 blender-motion-library/references/qa-checks.md），再：
"$BL" -b "$P/<名稱>.blend" -P "$ML/bl_cli.py" -- --project "$P" --run run_analyse KEYS=<修過的> FORCE=true
"$BL" -b "$P/<名稱>.blend" -P "$ML/bl_cli.py" -- --project "$P" --run render_actions  # 約 30 × 2 分鐘，背景跑
python ".../export_media.py" --project "$P" --only actions
```

`stages.02 = "done"`。

## ⑦ 03 服裝

```bash
cp "$REPO/.claude/docs/data/blender/library/costumes/<最接近的>.json" "$P/costume.json"   # 再依照片改
"$BL" -b "$P/<名稱>.blend" -P "$ML/bl_cli.py" -- --project "$P" --run build_costume
# 看 WORK/check/costume/c_*.png，和 source/front.*、back.* 並排比；改 costume.json 重建，直到對上
"$BL" -b "$P/<名稱>_costume.blend" -P "$ML/bl_cli.py" -- --project "$P" --run showcase MODE=costume
python ".../export_media.py" --project "$P" --only showcase,refs
```

`stages.03 = "done"`、`report.s3_summary` 寫服裝摘要，`report.limits` 寫做不到的地方（例：頭髮造型沒改、某個配件簡化）。

## 時間參考（新娘專案實測）

| 步驟 | 時間 |
| --- | --- |
| 匯入＋整理＋補皮膚 | 5～10 分鐘（含檢查圖來回） |
| showcase base | 約 4 分鐘 |
| run_analyse 30 個 | 約 10 分鐘 |
| render_actions 30 個 | 50～70 分鐘 |
| build_costume＋檢查 | 約 1 分鐘／次 |
| showcase costume | 約 8 分鐘 |
