# 四肢近照（目視用；2026-10-14 四肢強化時拿來做比較圖的三支暫存程式整理進來）。開 body.blend（唯讀，不存檔），左側：
#   bend：手肘彎 90°／130°（從上方看）、膝蓋彎 90°／130°（從外側看）——關節內側有沒有塌、有沒有凹口（研究 research-limb-deformation.md 第 5 節）
#   hip ：兩條大腿各扭 35°（左右反向）拍正面、背面、從下往上，＋左腿往前抬 70°——下腹、胯下有沒有皺出凹凸（權重清理，見 clean_weights）
#   shin：小腿正面、側面、背面——表面有沒有一條條直紋（Skin 細分次數，見 SKINSUB）
# 用法：blender -b <body.blend> -P limb_shots.py -- OUT=<資料夾> [ONLY=bend,hip,shin] [TAG=<檔名前綴>] [RES=480]
# 輸出：<OUT>/<TAG>_elbow90.png、_elbow130、_knee90、_knee130、_hip_front、_hip_back、_hip_low、_legup、_shin_front、_shin_side、_shin_back
#   （沒給 TAG 就沒有前綴：elbow90.png …）。兩副身體要並排比較時，同一個 OUT、不同 TAG。
# 相機用 body.blend 裡的攝影棚（body_build.studio）；位置都從骨頭算，不寫死，換頭身比也對得到。
import bpy, os, sys, math
from mathutils import Vector, Quaternion
sys.path.insert(0, r"D:\SideProject\wedding-invitation\.claude\skills\blender-motion-library\scripts")
import mixamo_retarget as mr

A = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:] if "=" in a) if "--" in sys.argv else {}
OUT = A["OUT"]; os.makedirs(OUT, exist_ok=True)
TAG = A.get("TAG", ""); PRE = TAG + "_" if TAG else ""
ONLY = A.get("ONLY", "bend,hip,shin").split(",")
RES = int(A.get("RES", "480"))
O = bpy.data.objects; arm = O["Body_Armature"]; B = arm.data.bones; PB = arm.pose.bones; AW = arm.matrix_world
sc = bpy.context.scene; cam = sc.camera
sc.render.resolution_x = sc.render.resolution_y = RES
cam.data.type = "PERSP"


def reset():
    for pb in PB:
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    bpy.context.view_layer.update()


def shoot(name, target, loc, lens=50):
    cam.location = loc; cam.data.lens = lens
    cam.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, PRE + name + ".png"); bpy.ops.render.render(write_still=True)
    print("SHOT", sc.render.filepath)


reset()
if "bend" in ONLY:
    tgt = mr.Target(arm)
    R0 = {n: (AW.to_quaternion() @ B[n].matrix_local.to_quaternion()) for n in tgt.keys}; H0 = tgt.rest_h["J_Bip_C_Hips"].copy()
    for nm, bone, axis, deg, look in (("elbow90", "J_Bip_L_LowerArm", (0, 0, 1), -90, (0, 0, 1)), ("elbow130", "J_Bip_L_LowerArm", (0, 0, 1), -130, (0, 0, 1)),
                                      ("knee90", "J_Bip_L_LowerLeg", (1, 0, 0), 90, (1, 0, 0)), ("knee130", "J_Bip_L_LowerLeg", (1, 0, 0), 130, (1, 0, 0))):
        R = mr.rotate_subtree(tgt, R0, bone, Quaternion(Vector(axis), math.radians(deg)))
        mr.apply_pose(arm, tgt, R, H0); bpy.context.view_layer.update()
        c = AW @ PB[bone].head
        shoot(nm, c, c + Vector(look) * 0.45 + Vector((0, -0.05, 0.05)))
    reset()

if "hip" in ONLY:
    # 胯下高度附近：大腿根往下 5 cm（4.5 頭身約 0.55 m）
    c = Vector((0, 0, (AW @ B["J_Bip_L_UpperLeg"].head_local).z - 0.05))
    PB["J_Bip_L_UpperLeg"].rotation_quaternion = Quaternion((0, 1, 0), math.radians(35))      # 骨頭本地 Y＝沿大腿：扭轉
    PB["J_Bip_R_UpperLeg"].rotation_quaternion = Quaternion((0, 1, 0), math.radians(-35))
    bpy.context.view_layer.update()
    for name, off in (("hip_front", (0, -0.9, 0.05)), ("hip_back", (0, 0.9, 0.05)), ("hip_low", (0, -0.6, -0.35))):
        shoot(name, c, c + Vector(off))
    reset()
    PB["J_Bip_L_UpperLeg"].rotation_quaternion = Quaternion((1, 0, 0), math.radians(-70))     # 往前抬
    bpy.context.view_layer.update()
    shoot("legup", c, c + Vector((0.6, -0.6, 0.0)))
    reset()

if "shin" in ONLY:
    kn, an = AW @ B["J_Bip_L_LowerLeg"].head_local, AW @ B["J_Bip_L_Foot"].head_local
    c = kn.lerp(an, 0.6); c.y = 0.0                     # 小腿肚下面一點（直紋最明顯的地方）
    for name, off in (("shin_front", (0.04, -0.40, 0.05)), ("shin_side", (0.40, 0.0, 0.05)), ("shin_back", (0.05, 0.40, 0.05))):
        shoot(name, c, c + Vector(off), lens=60)
