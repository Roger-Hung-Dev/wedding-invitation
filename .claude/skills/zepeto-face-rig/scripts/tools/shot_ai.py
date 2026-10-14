# AI 原頭同機位近拍（對照用）：blender -b stylized_face_zepeto.blend -P shot_ai.py -- <landmarks> <out.png> <x,y,z 相機偏移> <解析度>
import bpy, json, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
sc = bpy.context.scene
LM = json.load(open(a[0], encoding="utf-8")); mc = Vector(LM["mouth"]["center"])
off = Vector([float(v) for v in a[2].split(",")])
cam = sc.camera; cam.location = mc + off; cam.rotation_euler = (mc - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x = sc.render.resolution_y = int(a[3]); sc.render.filepath = a[1]
bpy.ops.render.render(write_still=True)
