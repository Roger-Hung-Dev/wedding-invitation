# 背景 Blender 指令

```bash
BL="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
ML="D:/SideProject/wedding-invitation/.claude/skills/blender-motion-library/scripts"
P="D:/SideProject/wedding-invitation/.claude/docs/data/blender/projects/<名稱>"
"$BL" -b "$P/<要開的 .blend>" -P "$ML/bl_cli.py" -- --project "$P" --run <腳本> [KEY=值 ...]
```

`KEY=值` 會設成全域變數：值先試 JSON（`true`、`40`、`["a","b"]`），名稱以 `KEYS` 結尾的一律整理成清單（`KEYS=a,b`、`KEYS=40` 都可以）。

| --run | 開哪個檔 | 參數 | 產出 |
| --- | --- | --- | --- |
| `run_analyse` | `<名稱>.blend` | `KEYS`、`FORCE=true` | `QA/metrics.json`（穿模、腳底、轉速，不渲染） |
| `render_actions` | `<名稱>.blend`（便服）或 `_costume.blend` | `RKEYS`、`OUTFIT=base\|costume`、`RES`、`YAW`、`SAMPLES` | `WORK/actions(_costume)/<代號>/*.png`、`QA/motion(_costume).json` |
| `build_costume` | `<名稱>.blend` | `SPEC=<json>`、`CHECK=false` | `<名稱>_costume.blend`、`WORK/check/costume/*.png` |
| `showcase` | `MODE=base` 開 `.blend`；`MODE=costume` 開 `_costume.blend` | `ONLY=["turn_body",...]` | `WORK/showcase/<項目>/` |
| `run_scene` | `_costume.blend`（便服情境也用它） | `SCENE=<模組>`、`MODE=preview\|full`、`KEYS` | 預覽 `WORK/check/<id>/`；完整 `WORK/scenes/<id>/` |

影格轉成品（系統 Python，不在 Blender 裡）：

```bash
python .claude/skills/blender-report-page/scripts/export_media.py --project "$P" [--only showcase,actions,actions_costume,scenes,refs]
```

## 注意

- **VRM 匯入只能在 GUI Blender**（背景模式沒有 window，匯入器會炸）。其他步驟都能背景跑。
- 渲染很久的工作用 Bash `run_in_background`，完成後再讀輸出；不要用 sleep 輪詢。
- GUI Blender 和背景 Blender 可以同時跑，但**不要兩邊同時寫同一個 .blend**。
- 連續渲染幾百格後 Blender 偶爾會當掉：`render_actions` 以動作為單位寫進度檔（`progress.txt`），重跑會從沒做完的動作接著做；`render_seq` 已存在的影格會跳過。
- Windows 主控台預設 cp950，系統 Python 腳本已 `reconfigure(utf-8)`；自己寫的要記得，否則中文輸出是亂碼。
