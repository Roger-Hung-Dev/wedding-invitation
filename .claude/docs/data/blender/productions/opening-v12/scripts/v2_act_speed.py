# 動作庫動作的逐骨轉速診斷（2026-10-09 wave_arc 用）：角色站在原點、24 fps 逐格擺，列出每格轉最多的骨頭與角度（°/格）
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_act_speed ACT_KEY=wave_arc [WHO_=groom] [TOP=12]
import bpy, math
from mathutils import Vector

MODE = "setup"
use("run_prod")
use("shots_v2_s0308")
KEY_ = str(globals().get("ACT_KEY", "wave_arc"))
NS = GR if str(globals().get("WHO_", "groom")) == "groom" else B
for o in bpy.data.objects:
    if o.type == "MESH":
        for m in o.modifiers:
            m.show_viewport = False
A = NS["ARM"]; name, fn, nfr = NS["ACT"][KEY_]
BONES = [pb.name for pb in A.pose.bones if pb.name.startswith("J_Bip_") and not any(f in pb.name for f in ("Thumb", "Index", "Middle", "Ring", "Little"))]
prev = None; rows = []
for i in range(nfr + 1):
    t = (i % nfr) / nfr
    P = NS["posture"](dict(fn(t))) if NS is GR else fn(t)
    NS["pose_frame"](A, P); bpy.context.view_layer.update()
    cur = {b: A.pose.bones[b].matrix.to_quaternion() for b in BONES}
    if prev:
        d = sorted(((min(a_, 360 - a_), b) for b in BONES for a_ in [math.degrees(prev[b].rotation_difference(cur[b]).angle)]), reverse=True)   # 四元數正負號：345° 其實是 15°
        rows.append((i, d[0][0], d[0][1], d[1][0], d[1][1]))
    prev = cur
rows.sort(key=lambda r: -r[1])
for r in rows[:int(globals().get("TOP", 12))]:
    print("SPD", KEY_, "frame", r[0], f"t={r[0] / 24:.3f}s", r[2], round(r[1], 1), r[4], round(r[3], 1), flush=True)
# PALMDBG=1：列出每格「palms 之前」的掌心方向與 face_palm 需要轉的角度（找翻面）
if int(globals().get("PALMDBG", 0)):
    for i in range(int(globals().get("F0", 14)), int(globals().get("F1", 26))):
        t = i / nfr
        P = NS["posture"](dict(fn(t))) if NS is GR else fn(t)
        Q = dict(P); pal = Q.pop("palms", [])
        NS["pose_frame"](A, Q); bpy.context.view_layer.update()
        out = []
        for item in pal:
            sd = item[0]; n, ax = NS["palm_normal"](A, sd)
            fa = (A.pose.bones[f"J_Bip_{sd}_LowerArm"].tail - A.pose.bones[f"J_Bip_{sd}_LowerArm"].head).normalized()
            ua = (A.pose.bones[f"J_Bip_{sd}_UpperArm"].tail - A.pose.bones[f"J_Bip_{sd}_UpperArm"].head).normalized()
            ik_ = [it for it in Q.get("ik", []) if it[0] == sd]
            def rollv(b):
                pb_ = A.pose.bones[b]; R_ = pb_.matrix.to_3x3() @ pb_.bone.matrix_local.to_3x3().inverted()
                return [round(x, 2) for x in (R_ @ Vector((0, 0, -1)))]
            out.append((sd, "rollUA", rollv(f"J_Bip_{sd}_UpperArm"), "rollLA", rollv(f"J_Bip_{sd}_LowerArm")))
            out.append((sd, "palm", [round(x, 2) for x in n], "hand_ax", [round(x, 2) for x in ax], "forearm", [round(x, 2) for x in fa],
                        "upper", [round(x, 2) for x in ua], "W", [round(x, 3) for x in ik_[0][1]] if ik_ else None))
        print("PALM", i, out, flush=True)
