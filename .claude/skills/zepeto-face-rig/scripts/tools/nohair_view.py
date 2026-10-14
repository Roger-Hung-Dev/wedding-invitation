# 藏起頭髮看 Head 哪裡沒有皮（開 pack.blend／ring.blend／head_rig.blend；不存檔）：Head 粉、Ears 綠；
#   有補後頸墊底皮的頭，墊底皮（nape_underlay 屬性）另塗黃色。正交三張：正後、右後斜、正右。
# 用法：blender -b <檔> -P nohair_view.py -- <輸出前綴>
#   2026-10-14：新娘整片後頸、後腦都不在 Head 上（AI 畫成髮色、切頭髮時跟著進 Hair），從後面直接看到臉的內側——
#   近照只看到「深色鋸齒」，這張才看得出是整片缺皮。之前用「正後方 ±60°」數開放邊，剛好把缺口邊界算成側面，誤判成沒有洞
import bpy, sys
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
O = bpy.data.objects
for o in O:
    if o.name == "Hair" or o.type == 'ARMATURE' or o.name.startswith("WGT_"):
        o.hide_render = True


def mk(c):
    m = bpy.data.materials.new("C"); b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*c, 1); return m


hd = O["Head"]
for s in hd.material_slots:
    s.material = mk((1, 0.6, 0.6))
ua = hd.data.attributes.get("nape_underlay")
if ua:
    hd.data.materials.append(mk((1, 0.85, 0.2))); yi = len(hd.data.materials) - 1
    n = 0
    for p in hd.data.polygons:
        if all(ua.data[v].value for v in p.vertices):
            p.material_index = yi; n += 1
    print("[nohair] 墊底皮 %d 面（黃）" % n)
ea = O.get("Ears")
if ea:
    for s in ea.material_slots:
        s.material = mk((0.3, 0.9, 0.3))
sc = bpy.context.scene; cam = sc.camera; sc.render.resolution_x = sc.render.resolution_y = 500
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.6
tgt = Vector((0, -0.1, -0.15))
for i, d in enumerate([Vector((0, 1, 0)), Vector((-0.7, 0.7, 0)), Vector((-1, 0, 0))]):
    cam.location = tgt + d * 5
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + "_%d.png" % i
    bpy.ops.render.render(write_still=True)
