# ② 走路段的診斷（2026-10-09）：逐格（24fps）擺姿勢，列出每格轉最多的骨頭（世界旋轉，度/格），不量網格（幾秒就跑完）
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_walk_diag RATE=24 T0=3.5 T1=4.5 [TOP=3]
import bpy, math
from mathutils import Vector

MODE = "setup"
use("run_prod")
T0 = float(globals().get("T0", 3.5)); T1 = float(globals().get("T1", 4.5)); TOP = int(globals().get("TOP", 3))
S = SHOTS["v2_02"]; S["build"](); stage(S["set"], cast=True)
CAST = [("groom", GR), ("bride", B)]


def snap(ns):
    A = ns["ARM"]; Mw = A.matrix_world
    return {pb.name: (Mw @ pb.matrix).to_quaternion() for pb in A.pose.bones
            if pb.name.startswith("J_Bip_") and not any(k in pb.name for k in ("Thumb", "Index", "Middle", "Ring", "Little"))}


prev = {}
n = int(round((T1 - T0) * FPS)) + 1
for i in range(n):
    t = T0 + i / FPS
    S["frame"](t, props=False, cam=False); bpy.context.view_layer.update()
    out = []
    for who, ns in CAST:
        cur = snap(ns)
        if who in prev:
            d = []
            for k, q in cur.items():
                q0 = prev[who][k]; a = math.degrees(q0.rotation_difference(q).angle)
                d.append((min(a, 360 - a), k.replace("J_Bip_", "")))
            d.sort(reverse=True)
            out.append(who + " " + ", ".join(f"{k} {a:.1f}" for a, k in d[:TOP]))
        prev[who] = cur
    print("DIAG", round(t, 3), " | ".join(out), flush=True)
