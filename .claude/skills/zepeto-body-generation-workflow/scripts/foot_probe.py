# 腳部近照診斷（手腳研究第 6 步；2026-10-14 腳模板試做時加）：開 body.blend（只讀不存），T 字靜止姿勢下左腳擺幾個角度，拍外側、前方、正下方。
# 用法：blender -b body.blend -P foot_probe.py -- OUT=<資料夾> [POSES=rest,ankle_up30,ankle_down50,toes_up70]
# 角度：ankle_up＝腳踝往上翹（腳背靠向小腿）、ankle_down＝往下壓（踮腳）、toes_up＝腳趾往上翹（走路蹬地那一下）
import bpy, sys, os, math
from mathutils import Vector, Quaternion
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr
A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
OUT = A.get("OUT", r"D:\render-work\zepeto-body\build\foot"); os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; O = bpy.data.objects
arm = O["Body_Armature"]; cam = O["Camera"]; tgt = mr.Target(arm); B = arm.data.bones
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0)
bpy.context.view_layer.update()
R0 = {n: (arm.matrix_world.to_quaternion() @ B[n].matrix_local.to_quaternion()) for n in tgt.keys}
h0 = tgt.rest_h["J_Bip_C_Hips"].copy()
P = {"rest": (0, 0), "ankle_up30": (-30, 0), "ankle_down50": (50, 0), "toes_up70": (0, -70), "toes_up40": (0, -40)}
cam.data.type = "PERSP"; cam.data.lens = 60
sc.render.resolution_x = sc.render.resolution_y = 520
an = arm.matrix_world @ B["J_Bip_L_Foot"].head_local
_body = O["Body"]
_fv = [_body.matrix_world @ v.co for v in _body.data.vertices if v.co.x > 0 and v.co.z < 0.04]
_fy0, _fy1 = min(p.y for p in _fv), max(p.y for p in _fv)              # 腳尖、腳跟（靜止）
FL_ = _fy1 - _fy0
FC = Vector((an.x, (_fy0 + _fy1) / 2, 0.035))                          # 對準腳的中間，不是腳踝（2026-10-14 腳模板 v2 腳變長、腳踝抬高，舊對法拍到小腿）
DIST = max(0.34, 1.75 * FL_)
for name in A.get("POSES", "rest,ankle_up30,ankle_down50,toes_up70").split(","):
    af, at = P[name]
    R = dict(R0)
    qf = Quaternion((1, 0, 0), math.radians(af)); qt = Quaternion((1, 0, 0), math.radians(at))
    for s in "LR":
        R[f"J_Bip_{s}_Foot"] = qf @ R0[f"J_Bip_{s}_Foot"]; R[f"J_Bip_{s}_ToeBase"] = qt @ qf @ R0[f"J_Bip_{s}_ToeBase"]
    mr.apply_pose(arm, tgt, R, h0); bpy.context.view_layer.update()
    c = FC
    for view, d in (("out", Vector((1, 0, 0.12))), ("front", Vector((0.25, -1, 0.35))), ("in", Vector((-1, 0.0, 0.12)))):
        cam.location = c + d.normalized() * DIST
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, f"f_{name}_{view}.png"); bpy.ops.render.render(write_still=True)
    if name == "rest":                                           # 正下方看腳底（地板先藏起來）
        fl = O.get("Floor")
        if fl:
            fl.hide_render = True
        cam.location = c + Vector((0, 0.001, -DIST))
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(OUT, "f_rest_sole.png"); bpy.ops.render.render(write_still=True)
        if fl:
            fl.hide_render = False
print("FOOTPROBE done", OUT)
