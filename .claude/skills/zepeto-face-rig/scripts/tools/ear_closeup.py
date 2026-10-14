# 耳朵附近近照（開 head_rig.blend，只有頭；不存檔）：鬢角、耳朵前面、耳垂下方的髮際線鋸齒。
# 用法：blender -b head_rig.blend -P ear_closeup.py -- <輸出前綴> [R|L] [DBG]
#   R＝角色右耳（−X，預設）、L＝左耳；DBG＝分色（Head 紅、Hair 灰／背面洋紅、Ears 綠），分辨鋸齒是哪個零件
#   三張：斜前、正側、斜下往上。鬢角那排深色三角從斜前最明顯（2026-10-14 使用者圈出來的就是這個角度）
#   驅動器先靜音（不存檔），表情都在 0
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]
side = a[1] if len(a) > 1 and a[1] in ("R", "L") else "R"
dbg = "DBG" in a
O = bpy.data.objects
for idb in list(bpy.data.shape_keys) + [m.node_tree for m in bpy.data.materials if m.node_tree]:
    ad = idb.animation_data
    if ad:
        for fc in ad.drivers:
            fc.mute = True
for o in O:
    if o.type == 'ARMATURE' or o.name.startswith("WGT_"):
        o.hide_render = True
if dbg:
    def mk(n, c, back=None):
        m = bpy.data.materials.new(n); nt = m.node_tree; b = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
        if back is None:
            b.inputs['Base Color'].default_value = (*c, 1); return m
        g = nt.nodes.new('ShaderNodeNewGeometry'); mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        mx.inputs['A'].default_value = (*c, 1); mx.inputs['B'].default_value = (*back, 1)
        nt.links.new(g.outputs['Backfacing'], mx.inputs['Factor']); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
        return m
    for n, m in (("Head", mk("H", (1, 0.3, 0.3))), ("Hair", mk("R", (0.55, 0.55, 0.55), (1, 0, 1))), ("Ears", mk("E", (0.2, 0.9, 0.2)))):
        o = O.get(n)
        if o:
            for s in o.material_slots:
                s.material = m
ears = O["Ears"]
sg = -1 if side == "R" else 1
P = [ears.matrix_world @ v.co for v in ears.data.vertices]
S = [p for p in P if p.x * sg > 0] or P
c = sum(S, Vector()) / len(S)
sc = bpy.context.scene; cam = sc.camera; sc.render.resolution_x = sc.render.resolution_y = 500
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.55
tgt = c + Vector((0, -0.05, -0.05))
for i, d in enumerate([Vector((sg, -0.7, 0)), Vector((sg, 0, 0)), Vector((sg, -0.4, -0.8))]):
    cam.location = tgt + d.normalized() * 5
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + "_%d.png" % i
    bpy.ops.render.render(write_still=True)
print("[ear] %s 耳近照 3 張 → %s_*.png" % (side, out))
