import bpy, json, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
LM = json.load(open(a[0], encoding="utf-8")); mc = Vector(LM["mouth"]["center"])
sc = bpy.context.scene; cam = sc.camera
cam.location = mc + Vector((0, -0.42, 0)); cam.rotation_euler = (mc - cam.location).to_track_quat('-Z', 'Y').to_euler()
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.shape_keys:
        for kb in o.data.shape_keys.key_blocks[1:]: kb.value = {"jawOpen": 0.7}.get(kb.name, 0.0)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
fr = [cam.matrix_world @ v for v in cam.data.view_frame(scene=sc)]
for px, py in [(300, 430), (300, 445), (300, 460), (200, 450), (420, 450)]:
    u, v = px / 600, py / 600
    p = fr[3].lerp(fr[0], u).lerp(fr[2].lerp(fr[1], u), v)
    d = (p - cam.location).normalized()
    hit, loc, nor, idx, ob, _ = sc.ray_cast(dg, cam.location, d)
    info = ""
    if hit:
        me = ob.data
        rest = [tuple(round(c, 3) for c in (ob.matrix_world @ me.vertices[i].co)) for i in me.polygons[idx].vertices] if idx < len(me.polygons) else []
        mat = me.materials[me.polygons[idx].material_index].name if idx < len(me.polygons) and me.materials else ""
        info = "面%d 材質 %s 靜止頂點 %s" % (idx, mat, rest[:2])
    print("[pick] (%d,%d) → %s %s %s" % (px, py, ob.name if ob else None, tuple(round(c, 3) for c in loc) if hit else "", info))
