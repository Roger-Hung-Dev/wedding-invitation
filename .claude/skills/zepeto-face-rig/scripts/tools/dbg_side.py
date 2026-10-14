import bpy
ai = bpy.data.objects["AI_Driven"]; me = ai.data
ca = me.color_attributes.new("dbgc", 'FLOAT_COLOR', 'POINT')
sv = [d.value for d in me.attributes["lip_side"].data]
for i, s in enumerate(sv):
    ca.data[i].color = ((0.2, 0.4, 1, 1), (0.2, 0.4, 1, 1), (1, 0.2, 0.2, 1))[s] if s else (0.9, 0.9, 0.9, 1)
m = bpy.data.materials.new("DBG"); nt = m.node_tree
bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); vc = nt.nodes.new('ShaderNodeVertexColor'); vc.layer_name = "dbgc"
nt.links.new(vc.outputs['Color'], bs.inputs['Base Color'])
for i in range(len(ai.material_slots)): ai.material_slots[i].material = m
w = ai.modifiers.new("wf", 'WIREFRAME'); w.thickness = 0.002; w.use_replace = False; w.material_offset = 0
