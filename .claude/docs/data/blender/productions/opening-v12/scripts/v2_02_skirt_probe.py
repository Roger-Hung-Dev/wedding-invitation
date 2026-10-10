# ② 跳舞版（2026-10-10 第 5 輪）前置量測：新娘蓬裙每個高度的半徑（站姿 idle、站在原點），兩人的體型比例、腿長、手臂長。
#   "$BL" -b couple.blend -P prod_cli.py -- --run v2_02_skirt_probe
import bpy, math
from mathutils import Vector

MODE = "setup"
use("run_prod")
for o in (ARM, G["ARM"]):
    mesh_eval(True, o.name)
pose_frame_at(ARM, ACT["idle"][1](0.0), 0.0, 0.0, 0.0)
G["pose_frame_at"](G["ARM"], G["ACT"]["idle"][1](0.0), 3.0, 0.0, 0.0)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
SK = ("bride_Cos_Tulle", "bride_Cos_Frill", "bride_Cos_Peplum", "bride_Cos_Lining", "bride_Cos_Ruffle", "bride_Cos_Cascade", "bride_Cos_Petal")
hips = ARM.matrix_world @ ARM.pose.bones["J_Bip_C_Hips"].head
prof = {}
for o in bpy.data.objects:
    if o.type != "MESH" or not any(o.name.startswith(p) for p in SK) or o.hide_render:
        continue
    oe = o.evaluated_get(dg); me = oe.to_mesh(); M = oe.matrix_world
    for v in me.vertices:
        p = M @ v.co; zb = round(p.z, 1)
        r = math.hypot(p.x - hips.x, p.y - hips.y)
        a = math.degrees(math.atan2(p.x - hips.x, -(p.y - hips.y)))      # 0＝正前方（−Y）
        key = (zb, int(((a + 180) // 45) % 8))
        prof[key] = max(prof.get(key, 0.0), r)
    oe.to_mesh_clear()
print("SKIRT_OBJS", [o.name for o in bpy.data.objects if o.type == "MESH" and any(o.name.startswith(p) for p in SK)])
for z in sorted({k[0] for k in prof}):
    print("SKIRT_R z=%.1f" % z, " ".join("%d:%.2f" % (s * 45 - 180, prof.get((z, s), 0)) for s in range(8)))
for nm, ns in (("bride", B), ("groom", G)):
    A = ns["ARM"]; bb = A.data.bones
    leg = (bb["J_Bip_L_LowerLeg"].head_local - bb["J_Bip_L_UpperLeg"].head_local).length + (bb["J_Bip_L_Foot"].head_local - bb["J_Bip_L_LowerLeg"].head_local).length
    armL = (bb["J_Bip_L_LowerArm"].head_local - bb["J_Bip_L_UpperArm"].head_local).length + (bb["J_Bip_L_Hand"].head_local - bb["J_Bip_L_LowerArm"].head_local).length
    print("BODY", nm, "BODY_S", round(ns["BODY_S"], 3), "hips_z", round(bb["J_Bip_C_Hips"].head_local.z, 3), "hip_joint_z", round(bb["J_Bip_L_UpperLeg"].head_local.z, 3),
          "leg", round(leg, 3), "arm", round(armL, 3), "shoulder_z", round(bb["J_Bip_L_UpperArm"].head_local.z, 3), "head_z", round(bb["J_Bip_C_Head"].head_local.z, 3))
print("HIPS_W", [round(x, 3) for x in hips])
