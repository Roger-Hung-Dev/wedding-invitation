# 動作小片段自我檢驗（第 7.5 步）：背景 Blender 從樣張（已烤關鍵影格）渲一段「固定機位」的近距離小片段。
#   blender -b <樣張>.blend -P close_clip.py -- <輸出資料夾> <起秒> <迄秒> <誰> <角度> [每幾格一張] BODY=<人,人>
#   誰：groom｜bride｜photographer（穿 Suit_＝groom、Gown_＝bride、Photog_＝photographer）
#   角度：side（側面全身）｜front（斜前方全身）｜feet（腳部特寫）｜hands（手部特寫）｜face（臉部特寫：看嘴型、表情）
#   機位照起秒那格這個人的面向擺（side＝從他右手邊看、front＝他前方偏右、feet＝腳的前側方）。
#   秒數是鏡內秒（樣張頭尾各多做 1 秒）。機位在起秒那格對準這個人的骨盆後就固定不動——看腳有沒有碎步、身體有沒有抖，鏡頭一定要固定。
#   其他人先藏起來（只在這次檢查，不影響樣張）。
# 2026-10-13 使用者：改完動作後先用小短片自己檢驗再交（B3 新郎轉身雙腳小碎步那次起）。
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
out, t0, t1, who, view = argv[0], float(argv[1]), float(argv[2]), argv[3], argv[4]
step = int(argv[5]) if len(argv) > 5 and argv[5].isdigit() else 1
HANDLES = 1.0
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
arms = [o for o in sc.objects if o.type == "ARMATURE" and o.name.startswith("Body_Armature")]
groom = next((a for a in arms if any(c.name.startswith("Suit_") for c in a.children)), arms[0])
def _wears(a, pre):
    return any(o.name.startswith(pre) for o in sc.objects if o.type == "MESH" and any(m.type == "ARMATURE" and m.object == a for m in o.modifiers))
others = [a for a in arms if a is not groom]
pick = {"groom": groom,                                  # 照衣服認人：禮服 Gown_＝新娘、Photog_＝攝影師；認不到才照順序
        "bride": next((a for a in others if _wears(a, "Gown_")), others[0] if others else groom),
        "photographer": next((a for a in others if _wears(a, "Photog_")), others[-1] if others else groom)}
arm = pick.get(who, groom)
cam = bpy.data.objects.new("CHK_Cam", bpy.data.cameras.new("CHK_Cam")); sc.collection.objects.link(cam)
cam.data.lens = 40; sc.camera = cam
sc.render.resolution_x = sc.render.resolution_y = 480
sc.render.image_settings.file_format = "JPEG"
f0 = sc.frame_start + int(round((t0 + HANDLES) * 30)); f1 = sc.frame_start + int(round((t1 + HANDLES) * 30))
sc.frame_set(f0)
h0 = arm.matrix_world @ arm.pose.bones["J_Bip_C_Hips"].head
OFF = {"side": Vector((0.0, -2.0, 0.1)), "front": Vector((1.6, -1.6, 0.15)), "feet": Vector((-0.7, -0.9, 0.35)), "hands": Vector((0.5, -1.0, 0.45)), "face": Vector((0.75, -0.25, 0.05))}[view]
AIM_Z = {"side": 0.55, "front": 0.55, "feet": 0.08, "hands": 0.75, "face": 1.12}[view]
for a in arms:                                          # 其他人藏起來（不擋視線）
    if a is arm:
        continue
    for o in sc.objects:
        if o.type == "MESH" and (o in a.children_recursive or any(m.type == "ARMATURE" and m.object == a for m in o.modifiers)):
            o.hide_render = True
import math
from mathutils import Quaternion
fw = (arm.matrix_world.to_3x3() @ (arm.pose.bones["J_Bip_C_Hips"].matrix.to_3x3() @ arm.data.bones["J_Bip_C_Hips"].matrix_local.to_3x3().inverted()) @ Vector((0, -1, 0)))   # 骨盆朝向（rest 面向 −Y）
fw.z = 0; fw.normalize()
yaw = math.atan2(fw.y, fw.x) - math.atan2(0.0, 1.0)        # 機位偏移是照「面向 +X 走路」定的 → 轉到這個人當下的面向
OFF = Quaternion((0, 0, 1), yaw) @ OFF
tgt = Vector((h0.x, h0.y, AIM_Z))
cam.location = tgt + OFF
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
for f in range(f0, f1 + 1, step):
    sc.frame_set(f)
    sc.render.filepath = f"{out}/{view}_{f:04d}.jpg"
    bpy.ops.render.render(write_still=True)
print("CLOSE_DONE", out)
