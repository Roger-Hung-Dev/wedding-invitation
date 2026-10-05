# 擴充新動作

給 `blender-animation-append` 用。新動作放 `scripts/actions_custom.py`，**所有專案共用**。

## 1. 流程

1. **先查有沒有現成的**：讀 `LIB/actions_catalog.json`。描述和既有動作只差幅度或速度時，回報「用 `wave` 就是」並說明差在哪，不新增。
2. **寫函式**到 `actions_custom.py`，在 `CUSTOM_ACTIONS` 登記 `(代號, 中文名, 函式, 格數)`：
   - 代號：英文小寫，不可和既有重複（載入時重複會直接報錯）。
   - 頭尾相接：`t=0` 和 `t→1` 的姿勢要一樣（一次性的動作用 `bump(t, a, b, c, d)` 讓它從站姿出發、回到站姿）。
   - 格數：一般 48（2 秒）；有轉身、大動作用 72～96，讓每格轉角 ≤ 15°。
   - 可用工具：`arms_down`、`legs`、`breathe`、`seg`、`bump`、`ease`、`s`、`bs`、`SMILE`、`TUNE`（見 conventions.md）。
   - 手要碰到身體/臉/另一隻手 → 用 `ik`，座標用 `bs(...)`；掌心要轉 > 120° → 用 `twist`。
3. **快速看姿勢**（GUI Blender，幾張小圖）：

   ```python
   use("studio", "pose_lib", "actions")
   for t in (0.0, 0.25, 0.5, 0.75):
       pose_frame(ARM, ACT["<代號>"][1](t)); ...shot(...)
   ```

4. **跑檢查**（背景 Blender，開測試專案的 `<名稱>.blend`）：`--run run_analyse KEYS=<代號> FORCE=true`，讀 `QA/metrics.json`。
5. **修到通過**：穿模 ≤ 5 mm、腳底貼地、渲染後 `body_vmax` ≤ 15、`body_jerk` ≤ 6。修法對照見 qa-checks.md 第 3 節。碰觸類用 `contact_shots` 拍近照目視。
6. **渲染預覽**：`--run render_actions RKEYS=<代號>`，再 `export_media.py --only actions` → `PROJ/videos/actions/<代號>.mp4`。
7. **入庫**：
   - `LIB/actions_catalog.json` 加一筆：`{"key","name","frames","source":"custom","note","contact_note","added":"<日期>","by_request":"<使用者原話>"}`。
   - 預覽圖複製一份到 `LIB/previews/actions/<代號>.jpg`。
   - `references/actions-catalog.md` 的表格加一列（數字照實填）。

⛔ 檢查沒過不准入庫。真的修不好（例如動作本身就會穿模），回報 `blocked`：哪一項沒過、數字多少、試過哪些修法。

## 2. 測試用專案

預設用 `projects/bride`（新娘，30 個動作都已驗證）。使用者指定別的專案就用那個；動作要給哪些角色用，就在哪些專案各跑一次檢查（體型不同，TUNE／IK 結果會不同）。

## 3. 範例（寫法參考，沒有跑過檢查；照抄也要走完第 1 節的 4～7 步）

```python
def a_bow_deep(t):
    b = bump(t, 0.1, 0.4, 0.6, 0.9)                       # 0.1～0.4 彎下、停到 0.6、0.9 回正
    P = arms_down({}, l_fwd=10 * b, r_fwd=10 * b, l_el=18 + 30 * b, r_el=18 + 30 * b)
    P["Spine"] = [("X", 45 * b)]; P["Chest"] = [("X", 10 * b)]; P["Head"] = [("X", 10 * b)]
    return dict(P, face={"Fcl_ALL_Fun": 0.5, "Fcl_EYE_Close": 0.7 * b})


def a_hand_on_heart(t):
    u = bump(t, 0.1, 0.35, 0.7, 0.95)
    P = arms_down({}); P["Head"] = [("X", 8 * u)]
    rest = bs(-0.19, -0.05, 0.86); heart = bs(0.05, -0.16, 1.18)   # 右手貼左胸
    return dict(P, hands=("relax", ("relax", "flat", u)),
                ik=[("R", rest.lerp(heart, u), bs(-0.4, -0.1, 0.9))], face={"Fcl_ALL_Fun": 0.6})


CUSTOM_ACTIONS = [("bow_deep", "深鞠躬", a_bow_deep, 72), ("hand_on_heart", "手放胸口", a_hand_on_heart, 72)]
```
