# ③ v2_03c 步幅診斷（2026-10-10 第 4 輪）：新郎接好的整段（縮步之後）每個支撐期的時間、腳踝落點（場景座標）、和上一個落點的距離（步幅）、
# 每 0.25 秒兩腳前後距離。  "$BL" -b couple.blend -P prod_cli.py -- --run v2_03c_diag
import bpy, math, json
MODE = "setup"
use("run_prod"); use("shots_v2_s0308"); use("shots_v2_s03carpet")
st = v2_03c_setup(); FG = st["FG"]; off = st["offG"]
rows = []
for s in "LR":
    for a, b in FG.contacts[s]:
        ta, tb = a / 120.0 - FG.shift, b / 120.0 - FG.shift
        if tb < 0 or ta > C3["dur"]:
            continue
        H = FG.fk(max(0.0, (ta + tb) / 2)); p = H[f"{s}_Foot"] + off
        rows.append((round(ta, 2), round(tb, 2), s, round(p.x, 3), round(p.y, 3)))
rows.sort()
prev = {}
for r in rows:
    q = prev.get(r[2]); oth = prev.get("L" if r[2] == "R" else "R")
    print("STEP", r, "same-foot stride", None if q is None else round(math.hypot(r[3] - q[3], r[4] - q[4]), 3),
          "ahead of other foot", None if oth is None else round(r[4] - oth[4], 3), flush=True)
    prev[r[2]] = r
for i in range(0, 32):
    t = i * 0.25; H = FG.fk(t)
    print("SEP", t, round(abs(H["L_Foot"].y - H["R_Foot"].y), 3), "hips_y", round(H["Hips"].y + off.y, 3), flush=True)
