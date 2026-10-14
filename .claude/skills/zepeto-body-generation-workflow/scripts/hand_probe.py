# 手部近照診斷：開 body.blend，套 Mixamo 動作某一格，拍左右手多角度近照。
# 用法：blender -b body.blend -P hand_probe.py -- OUT=<資料夾> [CLIP=female_idle.fbx] [F=0] [TAG=idle]
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr
A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
OUT = A.get("OUT", r"D:\render-work\zepeto-body\build\hand"); os.makedirs(OUT, exist_ok=True)
TAG = A.get("TAG", "idle")
sc = bpy.context.scene; O = bpy.data.objects
arm = O["Body_Armature"]; cam = O["Camera"]; tgt = mr.Target(arm)
if A.get("GEST"):
    # 手勢檢查：T 字靜止姿勢，左手擺手勢，拍手背、手心、拇指側
    G = {"open": {}, "fist": {"Index": (75, 95, 65), "Middle": (75, 95, 65), "Ring": (75, 95, 65), "Little": (75, 95, 65), "Thumb": (25, 35, 30)},
         "point": {"Middle": (75, 95, 65), "Ring": (75, 95, 65), "Little": (75, 95, 65), "Thumb": (25, 35, 30)},
         "ya": {"Ring": (80, 90, 60), "Little": (80, 90, 60), "Thumb": (30, 40, 30)}}
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    R0 = {n: (arm.matrix_world.to_quaternion() @ arm.data.bones[n].matrix_local.to_quaternion()) for n in tgt.keys}
    h0 = tgt.rest_h["J_Bip_C_Hips"].copy()
    cam.data.type = "PERSP"; cam.data.lens = 50
    sc.render.resolution_x = sc.render.resolution_y = 520
    names = A.get("GEST").split(",") if A.get("GEST") not in ("1", "lib") else (list(mr.GESTURE) if A.get("GEST") == "lib" else list(G))
    for g in names:
        if g in mr.GESTURE and A.get("GEST") != "1":
            R = mr.gesture(tgt, R0, "L", g)
        else:
            curl = G.get(g, {})
            R = mr.finger_pose(tgt, R0, "L", curl, spread={"Index": 8, "Middle": -8} if g == "ya" else None) if curl else R0
        mr.apply_pose(arm, tgt, R, h0); bpy.context.view_layer.update()
        pb = arm.pose.bones["J_Bip_L_Hand"]; c = arm.matrix_world @ pb.head.lerp(pb.tail, 0.7)
        for name, d in (("back", Vector((0.0, -0.001, 1))), ("palm", Vector((0.0, -0.001, -1))), ("thumb", Vector((0.15, -1, 0.15)))):
            cam.location = c + d.normalized() * 0.28
            cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = os.path.join(OUT, f"g_{g}_{name}.png"); bpy.ops.render.render(write_still=True)
    raise SystemExit
clip = mr.retarget(mr.read_fbx(os.path.join(r"D:\render-work\mixamo\raw", A.get("CLIP", "female_idle.fbx"))), tgt)
f = int(A.get("F", "0"))
R, h = clip["R"][f], clip["hips"][f].copy(); h.x = h.y = 0
mr.apply_pose(arm, tgt, R, h); bpy.context.view_layer.update()
cam.data.type = "PERSP"; cam.data.lens = 50
sc.render.resolution_x = sc.render.resolution_y = 560
for s in ("L", "R"):
    pb = arm.pose.bones[f"J_Bip_{s}_Hand"]
    c = arm.matrix_world @ (pb.head.lerp(pb.tail, 0.6))
    for name, d in (("front", Vector((0, -1, 0))), ("out", Vector((1 if s == "L" else -1, 0, 0))),
                    ("in", Vector((-1 if s == "L" else 1, -0.3, 0))), ("below", Vector((0, -0.4, -1)))):
        cam.location = c + d.normalized() * 0.30
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, f"{TAG}_{s}_{name}.png"); bpy.ops.render.render(write_still=True)
