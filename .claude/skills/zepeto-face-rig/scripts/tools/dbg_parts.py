import bpy
def mk(n, c):
    m = bpy.data.materials.new(n); b = next(x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*c, 1); b.inputs['Roughness'].default_value = 0.8; return m
C = {"Cavity": (0.1, 0.2, 1), "upper_teeth": (1, 1, 1), "bottom_teeth": (0.9, 0.9, 0.6), "upper_gum": (1, 0.8, 0), "bottom_gum": (1, 0.5, 0), "Tongue": (1, 0, 1)}
for n, c in C.items():
    o = bpy.data.objects.get(n)
    if o:
        o.data.materials.clear(); o.data.materials.append(mk("D_" + n, c))
li = bpy.data.materials.get("LipInner")
b = next(x for x in li.node_tree.nodes if x.type == 'BSDF_PRINCIPLED'); b.inputs['Base Color'].default_value = (0, 1, 0.2, 1)
print("[dbg] ok")
