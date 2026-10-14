# 除錯：只看頭（沒有身體）——Hair 灰、細髮絲紅（pack_head.py 的 strand 屬性）、Head／Ears 粉；正面／側面／背面正交。不存檔。
# 用法：blender -b rig.blend -P dbg_hair_split.py -- <輸出檔名前綴>
#   看細髮絲、衣領、髮尾有沒有分對（2026-10-14：細髮絲範圍太廣，髮尾和衣領邊也被當細髮絲往前推進胸口）
import bpy, sys, numpy as np
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
h = bpy.data.objects["Hair"]; me = h.data
st = [d.value for d in me.attributes["strand"].data] if "strand" in me.attributes else [0] * len(me.vertices)
ca = me.color_attributes.new("sp", 'FLOAT_COLOR', 'POINT')
for i, s_ in enumerate(st): ca.data[i].color = (1, 0.1, 0.1, 1) if s_ else (0.55, 0.55, 0.55, 1)
m = bpy.data.materials.new("SP"); nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = "sp"; nt.links.new(vc.outputs['Color'], b.inputs['Base Color'])
for s_ in h.material_slots: s_.material = m
mh = bpy.data.materials.new("HD"); next(n for n in mh.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (1, 0.7, 0.7, 1)
for n in ("Head", "Ears"):
    o = bpy.data.objects.get(n)
    if o:
        for s_ in o.material_slots: s_.material = mh
rig = bpy.data.objects.get("Face_Rig")
if rig: rig.hide_render = True
sc = bpy.context.scene; cam = sc.camera; sc.render.resolution_x = sc.render.resolution_y = 500
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.3
for i, (loc, tgt) in enumerate([((0, -5, -0.1), (0, 0, -0.1)), ((5, 0, -0.1), (0, 0, -0.1)), ((0, 5, -0.1), (0, 0, -0.1))]):
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + "_%d.png" % i; bpy.ops.render.render(write_still=True)
