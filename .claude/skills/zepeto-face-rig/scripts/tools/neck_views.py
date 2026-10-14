# 脖子前後對照用的固定機位（開 pack.blend／slim.blend／ring.blend／head_rig.blend；不存檔）：正面、斜前、正右側、右後斜，正交。
#   修細脖子（neck_slim.py）前後各跑一次，機位一樣、可以直接並排比。nohair＝藏起頭髮（看脖子本身的輪廓）。
# 用法：blender -b <檔> -P neck_views.py -- <輸出前綴> [nohair]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; nohair = len(a) > 1 and a[1] == "nohair"
O = bpy.data.objects
for o in O:
    if o.type == 'ARMATURE' or o.name.startswith("WGT_") or (nohair and o.name == "Hair"):
        o.hide_render = True
sc = bpy.context.scene; cam = sc.camera; sc.render.resolution_x = sc.render.resolution_y = 480
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.5
tgt = Vector((0, -0.05, -0.12))
for i, d in enumerate([Vector((0, -1, 0)), Vector((0.7, -0.7, 0)), Vector((1, 0, 0)), Vector((0.7, 0.7, 0))]):
    cam.location = tgt + d * 5
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + "_%d.png" % i
    bpy.ops.render.render(write_still=True)
print("[neck_views] %s（%s）" % (out, "不含頭髮" if nohair else "含頭髮"))
