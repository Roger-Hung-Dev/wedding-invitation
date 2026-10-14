# 除錯分色（頭接身體後也能用）：Head 紅、Body 藍、Hair 灰（背面洋紅）、Ears 綠。不存檔。
# 用法：blender -b <rig.blend 或 body.blend> -P dbg_body_parts.py -P <拍照的工具，例：身體端 neck_probe.py> -- ...
#   例：找出頭髮哪裡露出背面（洋紅）、哪些皮膚被誤分到頭髮（灰）
import bpy
def mk(n, c, back=None):
    m = bpy.data.materials.new(n); nt = m.node_tree; b = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
    if back is None:
        b.inputs['Base Color'].default_value = (*c, 1); return m
    g = nt.nodes.new('ShaderNodeNewGeometry'); mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    mx.inputs['A'].default_value = (*c, 1); mx.inputs['B'].default_value = (*back, 1)
    nt.links.new(g.outputs['Backfacing'], mx.inputs['Factor']); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    return m
for n, m in (("Head", mk("DH", (1, 0.25, 0.25))), ("Body", mk("DB", (0.3, 0.6, 1))), ("Hair", mk("DR", (0.5, 0.5, 0.5), (1, 0, 1))), ("Ears", mk("DE", (0.2, 0.9, 0.2)))):
    o = bpy.data.objects.get(n)
    if o:
        for s_ in o.material_slots: s_.material = m
