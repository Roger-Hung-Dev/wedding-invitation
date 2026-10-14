# 除錯：AI 網格依口腔袋圈數上色（0 皮膚＝灰、1 圈＝綠、2 圈＝黃、3 圈＝橘、4 圈以後＝藍）；背面洋紅
import bpy
ai = bpy.data.objects["AI_Driven"]; me = ai.data
pk = [d.value for d in me.attributes["pocket_k"].data]
ca = me.color_attributes.new("pkc", 'FLOAT_COLOR', 'POINT')
C = {0: (0.75, 0.75, 0.75, 1), 1: (0, 0.9, 0.2, 1), 2: (1, 0.9, 0, 1), 3: (1, 0.45, 0, 1)}
for i, k in enumerate(pk):
    ca.data[i].color = C.get(k, (0.1, 0.3, 1, 1))
m = bpy.data.materials.new("PKD"); nt = m.node_tree
bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = "pkc"
g = nt.nodes.new('ShaderNodeNewGeometry'); mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
mx.inputs['B'].default_value = (1, 0, 1, 1)
nt.links.new(g.outputs['Backfacing'], mx.inputs['Factor']); nt.links.new(vc.outputs['Color'], mx.inputs['A']); nt.links.new(mx.outputs[2], bs.inputs['Base Color'])
for s_ in ai.material_slots:
    s_.material = m
print("[dbg_pocket] ok")
