# 新娘伸手到背後的路徑診斷：reach_spec 單獨擺（不經 Actor2 淡入）與實際（經淡入），印右手肘、手腕位置與每格轉角
import bpy, math
from mathutils import Vector
MODE = "setup"
use("run_prod")
S = SHOTS["v2_02"]; S["build"](); stage(S["set"], cast=True)
ST = V2S["02"]; A = ARM
use("check_lib"); CK = Checker(ARM, WHO)
cs = bpy.data.objects.get(WHO + "_Cos_Shoes")
if cs is not None: CK.shoes = cs
def armpts():
    Mw = A.matrix_world; pb = A.pose.bones
    return [Mw @ pb[f"J_Bip_R_{n}"].head for n in ("UpperArm", "LowerArm", "Hand")], {n: (Mw @ pb[f"J_Bip_R_{n}"].matrix).to_quaternion() for n in ("UpperArm", "LowerArm", "Hand")}
for mode in ("actor",):
    prev = None
    for i in range(0, 9):
        tl = i / 24.0; t = 4.0 + tl
        if mode == "spec":
            pose_frame_at(A, Actor2._fix(ST["reach_spec"](tl)), *ST["place_b"](t))
        else:
            ST["AB"].pose(t)
        bpy.context.view_layer.update()
        p, q = armpts()
        d = {n: round(min(360 - a, a), 1) for n, a in ((n, math.degrees(prev[n].rotation_difference(q[n]).angle)) for n in q)} if prev else {}
        prev = q
        mesh_eval(True, ARM.name); c = CK.frame(); wa = CK.worst_at.get("core") if c["pen_core"] > 0.5 else None
        d["pen"] = round(c["pen_core"], 1); d["at"] = wa
        print("REACH", mode, round(t, 3), "elbow", [round(v, 3) for v in p[1]], "wrist", [round(v, 3) for v in p[2]], d, flush=True)
