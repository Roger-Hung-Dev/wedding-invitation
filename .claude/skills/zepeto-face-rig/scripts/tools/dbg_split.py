# 除錯：Head 灰、Hair 藍、Ears 紅，正面／兩側／背面
import bpy, sys
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]
def mk(n, c):
    m = bpy.data.materials.new(n); b = next(x for x in m.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*c, 1); return m
C = {"Head": (0.8, 0.8, 0.8), "Hair": (0.1, 0.3, 1), "Ears": (1, 0.1, 0.1)}
for n, c in C.items():
    o = bpy.data.objects.get(n)
    if o:
        m = mk("D" + n, c)
        for s_ in o.material_slots: s_.material = m
rig = bpy.data.objects.get("Face_Rig")
if rig: rig.hide_render = True
sc = bpy.context.scene; cam = sc.camera
sc.render.resolution_x = sc.render.resolution_y = 400
for i, (loc, tgt) in enumerate([((0, -3.4, 0.0), (0, 0, -0.1)), ((3.4, 0, 0.0), (0, 0, -0.1)), ((-3.4, 0, 0.0), (0, 0, -0.1)), ((0, 3.4, 0.0), (0, 0, -0.1))]):
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + "_%d.png" % i; bpy.ops.render.render(write_still=True)
