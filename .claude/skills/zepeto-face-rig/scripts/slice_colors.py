# 切片用顏色：AI 皮正面膚色／背面洋紅、唇內壁綠、口腔袋藍、牙白、牙齦黃、舌頭粉紅
import bpy
def mk(n, c, emit=False):
    m = bpy.data.materials.new(n); nt = m.node_tree; b = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*c, 1); b.inputs['Roughness'].default_value = 0.8
    b.inputs['Emission Color'].default_value = (*c, 1); b.inputs['Emission Strength'].default_value = 0.6
    return m
C = {"Cavity": (0.1, 0.25, 1), "upper_teeth": (1, 1, 1), "bottom_teeth": (1, 1, 1), "upper_gum": (1, 0.8, 0), "bottom_gum": (1, 0.8, 0), "Tongue": (1, 0.35, 0.6)}
for n, c in C.items():
    o = bpy.data.objects.get(n)
    if o: o.data.materials.clear(); o.data.materials.append(mk("S_" + n, c))
ai = bpy.data.objects["AI_Driven"]
skin = mk("S_skin", (0.85, 0.7, 0.6)); nt = skin.node_tree
b = next(x for x in nt.nodes if x.type == 'BSDF_PRINCIPLED'); g = nt.nodes.new('ShaderNodeNewGeometry')
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.85, 0.7, 0.6, 1); mx.inputs['B'].default_value = (1, 0, 1, 1)
nt.links.new(g.outputs['Backfacing'], mx.inputs['Factor']); nt.links.new(mx.outputs[2], b.inputs['Base Color']); nt.links.new(mx.outputs[2], b.inputs['Emission Color'])
for s_ in ai.material_slots:
    s_.material = mk("S_wall", (0, 0.8, 0.2)) if s_.material and s_.material.name.startswith("LipInner") else skin
