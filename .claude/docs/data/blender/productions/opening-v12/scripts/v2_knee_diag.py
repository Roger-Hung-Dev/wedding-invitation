# 膝蓋打直的診斷：片段最後一格，解析 FK（rig.fk）與實際擺出來的骨架各量一次膝角、腿伸直比例
import bpy, math
from mathutils import Vector
MODE = "setup"
use("run_prod")
S = SHOTS["v2_02"]; S["build"](); stage(S["set"], cast=True)
ST = V2S["02"]
def ang(a, b): return math.degrees(a.angle(b))
for who, ns, F in (("groom", GR, ST["WG"]), ("bride", B, ST["WB"])):
    rig = F.rig
    for idx in (len(F.R) - 1,):
        Hd = rig.fk(F.R[idx], F.roots[idx])
        for s in "LR":
            h, k, a = Hd[f"{s}_UpperLeg"], Hd[f"{s}_LowerLeg"], Hd[f"{s}_Foot"]
            L = (k - h).length + (a - k).length
            print("KNEE_FK", who, s, "knee", round(ang(k - h, a - k), 1), "ext", round((a - h).length / L, 4), flush=True)
    P = F.pose_at(1.0); ns["pose_frame_at"](ns["ARM"], P, 0.0, 0.0, 0.0); bpy.context.view_layer.update()
    A = ns["ARM"]; Mw = A.matrix_world
    for s in "LR":
        h, k, a = (Mw @ A.pose.bones[f"J_Bip_{s}_{n}"].head for n in ("UpperLeg", "LowerLeg", "Foot"))
        L = (k - h).length + (a - k).length
        print("KNEE_POSED", who, s, "knee", round(ang(k - h, a - k), 1), "ext", round((a - h).length / L, 4), "keys", [kk for kk in P if "Leg" in kk], flush=True)
