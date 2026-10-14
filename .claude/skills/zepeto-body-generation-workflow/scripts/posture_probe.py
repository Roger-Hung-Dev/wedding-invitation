# 姿勢診斷：開 body.blend，T 字（rest）與 Mixamo 待機第一格各拍正面、側面正交上半身，並印出脊椎各點的前後位置（駝背）與肩膀高度（聳肩）。
# 用法：blender -b body.blend -P posture_probe.py -- OUT=<資料夾>
import bpy, sys, os, math, json
from mathutils import Vector, Matrix
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr
ARGS = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
OUT = ARGS.get("OUT", r"D:\render-work\zepeto-body\build\posture"); os.makedirs(OUT, exist_ok=True)
CLIP = ARGS.get("CLIP", "female_idle.fbx")
sc = bpy.context.scene; O = bpy.data.objects
arm = O["Body_Armature"]; cam = O["Camera"]; tgt = mr.Target(arm)


def shot(name, a, z=1.0, scale=0.9):
    r = math.radians(a)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = scale
    cam.location = Vector((-math.sin(r) * 5, -math.cos(r) * 5, z))
    cam.rotation_euler = (Vector((0, 0, z)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = sc.render.resolution_y = 640
    sc.render.filepath = os.path.join(OUT, name); bpy.ops.render.render(write_still=True)


def report(tag):
    g = lambda n: arm.matrix_world @ arm.pose.bones[n].head
    pts = {n: g(n) for n in ("J_Bip_C_Hips", "J_Bip_C_Spine", "J_Bip_C_Chest", "J_Bip_C_UpperChest", "J_Bip_C_Neck", "J_Bip_C_Head",
                             "J_Bip_L_UpperArm", "J_Bip_R_UpperArm", "J_Bip_L_Shoulder")}
    hips = pts["J_Bip_C_Hips"]
    out = {n.replace("J_Bip_", ""): dict(y_cm=round((p.y - hips.y) * 100, 1), z=round(p.z, 3)) for n, p in pts.items()}
    # 頭的前傾：頭骨方向和垂直的夾角；脊椎總前傾：臀→頸的方向
    hb = arm.pose.bones["J_Bip_C_Head"]; hv = (arm.matrix_world.to_3x3() @ (hb.tail - hb.head)).normalized()
    sp = (pts["J_Bip_C_Neck"] - hips).normalized()
    out["head_tilt_fwd_deg"] = round(math.degrees(math.atan2(-hv.y, hv.z)), 1)
    out["spine_lean_fwd_deg"] = round(math.degrees(math.atan2(-sp.y, sp.z)), 1)
    out["shoulder_above_neckbase_cm"] = round((pts["J_Bip_L_UpperArm"].z - pts["J_Bip_C_Neck"].z) * 100, 1)
    print(tag, json.dumps(out, ensure_ascii=False))
    return out


res = {}
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
bpy.context.view_layer.update()
res["rest"] = report("REST")
shot("rest_front.png", 0); shot("rest_side.png", 90)
clip = mr.retarget(mr.read_fbx(os.path.join(r"D:\render-work\mixamo\raw", CLIP)), tgt)
R, h = clip["R"][0], clip["hips"][0].copy(); h.x = h.y = 0
mr.apply_pose(arm, tgt, R, h); arm.rotation_euler = (0, 0, -clip["yaw"][0]); bpy.context.view_layer.update()
res["idle"] = report("IDLE")
shot("idle_front.png", 0); shot("idle_side.png", 90)
json.dump(res, open(os.path.join(OUT, "posture.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
