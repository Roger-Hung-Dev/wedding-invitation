# 碰觸類姿勢的近照：先設 JOBS = [(動作代號, t, 'hands'|'head'), ...]，輸出到 WORK/check/contact/<代號>_f.png、_s.png
import bpy, os, math
use("studio", "pose_lib", "actions")
mesh_eval(True)
cam = O["Camera"]; out = os.path.join(WORK, "check", "contact"); os.makedirs(out, exist_ok=True)
sc.render.resolution_x = sc.render.resolution_y = 320
for k, t, focus in JOBS:
    pose_frame(ARM, ACT[k][1](t)); bpy.context.view_layer.update()
    mw = ARM.matrix_world
    if focus == "head":
        c = mw @ ARM.pose.bones["J_Bip_C_Head"].head; c.z += 0.07; dist = 1.0
    else:
        c = (mw @ ARM.pose.bones["J_Bip_L_Hand"].head + mw @ ARM.pose.bones["J_Bip_R_Hand"].head) / 2; dist = 1.4
    for tag, ang in (("f", 0), ("s", 70)):
        r = math.radians(ang); aim(cam, (c.x + math.sin(r) * dist, c.y - math.cos(r) * dist, c.z + 0.05), tuple(c), 85)
        sc.render.filepath = os.path.join(out, f"{k}_{tag}.png"); bpy.ops.render.render(write_still=True)
pose_frame(ARM, dict(STAND))
