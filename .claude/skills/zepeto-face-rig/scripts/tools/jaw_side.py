# 張嘴時的喉嚨、後頸（開 head_rig.blend；不存檔）：jawOpen 0／0.5／1.0，頭髮藏起來，驅動器靜音後直接設形態鍵。
# 用法：blender -b head_rig.blend -P jaw_side.py -- <輸出前綴> [side|back]
#   side（預設）：正右側，看喉嚨的輪廓——接口環附近的表情位移漸變太短，張到全開喉嚨會折一個角（新娘 FALL 0.06 時）
#   back：右後斜，看後頸墊底皮會不會被張嘴的下顎戳破、表面有沒有一條一條橫紋
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; mode = a[1] if len(a) > 1 else "side"
for idb in list(bpy.data.shape_keys) + [m.node_tree for m in bpy.data.materials if m.node_tree]:
    ad = idb.animation_data
    if ad:
        for fc in ad.drivers:
            fc.mute = True
for o in bpy.data.objects:
    if o.name == "Hair" or o.type == 'ARMATURE' or o.name.startswith("WGT_"):
        o.hide_render = True
sc = bpy.context.scene; cam = sc.camera; sc.render.resolution_x = sc.render.resolution_y = 420
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.9
if mode == "back":
    tgt = Vector((0, 0.05, -0.12)); cam.location = tgt + Vector((-3.5, 3.5, 0))
else:
    tgt = Vector((0, -0.1, -0.2)); cam.location = tgt + Vector((5, 0, 0))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys]
for i, v in enumerate((0.0, 0.5, 1.0)):
    for o in objs:
        kb = o.data.shape_keys.key_blocks.get("jawOpen")
        if kb:
            kb.value = v
    sc.render.filepath = out + "_%d.png" % i
    bpy.ops.render.render(write_still=True)
