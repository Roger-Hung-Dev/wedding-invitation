import bpy, os, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; os.makedirs(out, exist_ok=True)
LM = json.load(open(a[1], encoding="utf-8")); mc = Vector(LM["mouth"]["center"])
sc = bpy.context.scene; cam = sc.camera
ai = bpy.data.objects["AI_Driven"]
flat = bpy.data.materials.new("F"); b = next(n for n in flat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); b.inputs['Base Color'].default_value = (0.8, 0.62, 0.55, 1)
for s_ in ai.material_slots:
    if s_.material and s_.material.name.startswith("ZEPETO"): s_.material = flat
if os.environ.get("WIRE"):
    w = ai.modifiers.new("w", 'WIREFRAME'); w.thickness = 0.0008; w.use_replace = False
    wm = bpy.data.materials.new("WM"); bb = next(n for n in wm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); bb.inputs['Base Color'].default_value = (0.05, 0.05, 0.3, 1)
    ai.data.materials.append(wm); w.material_offset = len(ai.data.materials) - 1
for kb in ai.data.shape_keys.key_blocks[1:]:
    kb.value = 1.0 if kb.name == "jawOpen" else 0.0
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.shape_keys and o != ai:
        for kb in o.data.shape_keys.key_blocks[1:]: kb.value = 1.0 if kb.name == "jawOpen" else 0.0
sc.render.resolution_x = sc.render.resolution_y = 600
tgt = mc + Vector((0, 0, -0.07))
for i, off in enumerate([Vector((0, -0.35, 0.0)), Vector((0, -0.3, -0.12)), Vector((0.25, -0.3, -0.05))]):
    cam.location = tgt + off; cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, "%d.png" % i); bpy.ops.render.render(write_still=True)
