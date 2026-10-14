# 張嘴程度序列：jawOpen 0／0.3／0.6／1.0 × （單色正面、正中剖面）
#   剖面：側面正交相機放在 x=+2、clip_start=2 → 只看得到 x≤0 那一半（從正中切開）
import bpy, os, sys, json
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; os.makedirs(out, exist_ok=True)
LM = json.load(open(a[1], encoding="utf-8")); mc = Vector(LM["mouth"]["center"])
KEY = os.environ.get("KEY", "jawOpen")
LV = [float(v) for v in os.environ.get("LEVELS", "0,0.3,0.6,1.0").split(",")]
sc = bpy.context.scene
flat = bpy.data.materials.new("FLATS"); b = next(n for n in flat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
b.inputs['Base Color'].default_value = (0.8, 0.62, 0.55, 1); b.inputs['Roughness'].default_value = 0.6
ai = bpy.data.objects["AI_Driven"]
if os.environ.get("FLAT"):
    for s_ in ai.material_slots:
        if s_.material and s_.material.name.startswith("ZEPETO"): s_.material = flat
objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys]
cam_p = bpy.data.objects.new("CP", bpy.data.cameras.new("CP")); sc.collection.objects.link(cam_p)
cam_s = bpy.data.objects.new("CS", bpy.data.cameras.new("CS")); sc.collection.objects.link(cam_s)
cam_p.location = mc + Vector((0, -0.5, 0.0)); cam_p.rotation_euler = (mc - cam_p.location).to_track_quat('-Z', 'Y').to_euler()
cam_s.data.type = 'ORTHO'; cam_s.data.ortho_scale = 0.42; cam_s.data.clip_start = 2.0; cam_s.data.clip_end = float(os.environ.get('CLIP_END', 6))
cam_s.location = Vector((2.0, mc.y + 0.08, mc.z - 0.03)); cam_s.rotation_euler = (1.5708, 0, 1.5708)
sc.render.resolution_x = sc.render.resolution_y = 420
for i, lv in enumerate(LV):
    for o in objs:
        for kb in o.data.shape_keys.key_blocks[1:]:
            kb.value = lv if kb.name == KEY else 0.0
    for m in bpy.data.materials:
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.name == "JAW_OPEN": n.outputs[0].default_value = lv if KEY == "jawOpen" else 0
    for tag, cam in (("p", cam_p), ("s", cam_s)):
        sc.camera = cam
        sc.render.filepath = os.path.join(out, "%s_%d.png" % (tag, i))
        bpy.ops.render.render(write_still=True)
print("[series] done", LV)
