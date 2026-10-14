# 臉旁細髮絲近照：正面、左右斜面（頭檔，不含身體）；最後一個參數 dbg＝零件分色（同 dbg_body_parts.py）。不存檔。
# 用法：blender -b rig.blend -P shot_face_strands.py -- <輸出檔名前綴> [dbg]
import bpy, sys
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; dbg = sys.argv[-1] == "dbg"
if dbg:
    exec(open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "dbg_body_parts.py"), encoding="utf-8").read())
rig = bpy.data.objects.get("Face_Rig")
if rig: rig.hide_render = True
sc = bpy.context.scene; cam = sc.camera
sc.render.resolution_x = sc.render.resolution_y = 500
for i, (loc, tgt) in enumerate([((0, -2.4, 0.0), (0, -0.4, -0.05)), ((1.6, -1.7, 0.0), (0.2, -0.3, -0.05)), ((-1.6, -1.7, 0.0), (-0.2, -0.3, -0.05))]):
    cam.location = Vector(loc); cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = out + ("d" if dbg else "n") + "_%d.png" % i; bpy.ops.render.render(write_still=True)
