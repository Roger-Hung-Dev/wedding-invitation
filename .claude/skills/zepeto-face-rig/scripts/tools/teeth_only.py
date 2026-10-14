import bpy
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name not in ("upper_teeth", "bottom_teeth", "upper_gum", "bottom_gum", "Tongue"):
        o.hide_render = True
