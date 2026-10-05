---
name: blender-scenario
description: 用已建好的 Blender 角色專案做情境短片或靜態圖 —— 把使用者的情境描述拆成道具、場景、鏡頭、時間軸，寫成情境模組（scene_<id>.py），用 IK 讓手抓到道具、頭髮與裙擺物理、背景 Blender 渲染，成品存到專案的 videos/scenes、pictures/scenes。內含 6 個實測過的範例（看報紙翻頁、攝影棚拍照、拋捧花、切蛋糕、自拍、轉圈跳舞）。blender-scenario-creator 子代理的工作手冊。
compatibility: Blender 5.2＋VRM add-on、Python 3.10+（Pillow）、ffmpeg；角色專案需已完成 blender-character-build 的 01（便服情境）或 03（服裝情境）
metadata:
  version: "1.0"
  verified: 2026-10-04 新娘專案 6 個情境完整渲染；重構後 scene_s1、scene_s4 預覽實跑通過
---

# 情境

```
情境描述 ──① 拆解：場景／道具／角色在做什麼／手碰哪裡／鏡頭／長度／便服或服裝
  ▼
PROJ/scripts/scene_<id>.py（參考 examples/scene_s1~s6.py）──② preview（5 格小圖）── 看圖修 ──┐
  ▲                                                                                          │
  └──────────────────────────────────────────────────────────────────────────────────────────┘
  ▼ ③ full（物理＋960×540）→ WORK/scenes/<id>/ ── ④ export_media → PROJ/videos/scenes/<id>.mp4
```

工具都在 `scripts/scene_lib.py`（道具、IK 抓點、關鍵格內插、坐姿、背景色、渲染迴圈）；入口 `scripts/run_scene.py`（用 [[blender-motion-library]] 的 `bl_cli.py` 跑）。

## 1. 先確認專案

- 讀 `PROJ/project.json`：`who`、`stages`、`costume`、已有的 `scenes`。
- 服裝情境需要 `stages.03` 完成且 `<名稱>_costume.blend` 存在；便服情境需要 `stages.01`。不符合就 `blocked`，回報缺哪一步。
- 情境一律開 `<名稱>_costume.blend`（`wear("base")` 會換回便服）；沒有服裝檔時開 `<名稱>.blend`。

## 2. 情境模組格式

```python
S9_N = 168                                     # 格數（24 格＝1 秒）
def s9_build(): clear_props(); set_world((r,g,b), 地板色或 False); ...建道具...
def s9_props(f): ...每格更新道具（相機、紙張、飛出去的捧花）...
def s9_frame(f): return dict(P, rz=..., ground=True, hands=..., ik=[...], face=...)   # 角色姿勢
def s9_cam(i): aim(bpy.data.objects["Camera"], 位置, 看哪裡, 焦距)
SCENE = dict(id="s9", title="…", desc="…", N=S9_N, build=s9_build, frame=s9_frame, props=s9_props, cam=s9_cam,
             outfit="costume", res=(960, 540), stills=(格數, …))
```

`stills` 列出的格數會另存成靜態圖到 `PROJ/pictures/scenes/<id>_<格>.png`。使用者只要圖片時：`N` 設小（例 1～24）、`stills` 列要的格。

完整寫法、每個範例用到的技巧見 [references/scene-recipes.md](references/scene-recipes.md)；道具與鏡頭的經驗值見 [references/props-and-camera.md](references/props-and-camera.md)。

## 3. 指令

```bash
"$BL" -b "$P/<名稱>_costume.blend" -P "$ML/bl_cli.py" -- --project "$P" --run run_scene SCENE=scene_s9 MODE=preview [KEYS=0,60,120]
"$BL" -b "$P/<名稱>_costume.blend" -P "$ML/bl_cli.py" -- --project "$P" --run run_scene SCENE=scene_s9 MODE=full     # 背景跑
python ".claude/skills/blender-report-page/scripts/export_media.py" --project "$P" --only scenes
```

`MODE=full` 完成會把情境登記到 `project.json.scenes`（id、title、desc、outfit、frames），網頁的 04 章就是讀這張表。

## 4. 鐵律

1. **先 preview 再 full**。preview 每次只要幾十秒；full 要 7～12 分鐘。preview 看構圖、手有沒有抓到道具、臉有沒有被擋。
2. **手碰道具一律 IK**：抓點定義在道具的局部座標，每格用道具矩陣換算成世界座標再丟給 `ik`（見範例 s2、s3、s4、s5）。
3. **IK 目標要在手臂構得到的範圍**（肩膀起算 < 0.4 m × 體型比例），否則手伸直、道具浮在手外面。道具要搬近角色，不是把手臂拉長。
4. **蓬裙佔地半徑約 0.5 m**：桌子、椅子要放在裙子外面；坐姿情境的裙子不會被壓扁，改穿便服或在描述裡寫明。
5. **背景色、地板色每個情境自己設**（`set_world`），不要沿用上一個情境的。
6. **看每一張 preview 圖**（`Read`），寫進回報：看了哪幾格、看到什麼。
