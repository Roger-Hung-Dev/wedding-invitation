import bpy, os
for n in os.environ.get("HIDE", "").split(","):
    o = bpy.data.objects.get(n)
    if o: o.hide_render = True
