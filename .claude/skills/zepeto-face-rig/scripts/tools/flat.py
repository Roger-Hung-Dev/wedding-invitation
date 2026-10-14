import bpy
ai = bpy.data.objects["AI_Driven"]
m = bpy.data.materials.new("FLAT"); b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
b.inputs['Base Color'].default_value = (0.8, 0.6, 0.5, 1)
ai.material_slots[0].material = m
