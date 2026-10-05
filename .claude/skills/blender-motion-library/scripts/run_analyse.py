# 動作數字檢查（不渲染）：穿模、腳底、每格轉角。結果累加寫入 QA/metrics.json（已做過的跳過，FORCE=True 重做）。
# 可設：KEYS（清單；預設全部動作）、FORCE、BUDGET（秒；MCP 裡用 80，背景 Blender 不限）
import bpy, os, json, time
use("studio", "pose_lib", "actions", "check_lib")
MF = os.path.join(QA, "metrics.json")
M = json.load(open(MF, encoding="utf8")) if os.path.exists(MF) else {}
keys = globals().get("KEYS") or [k for k, *_ in ACTIONS]
t0 = time.time(); done = []
for k in keys:
    if k in M and not globals().get("FORCE"):
        continue
    if time.time() - t0 > globals().get("BUDGET", 1e9):
        break
    M[k] = analyse(k); done.append(k)
    json.dump(M, open(MF, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("done", done, "total", len(M), round(time.time() - t0, 1))
for k in done:
    print(M[k])
