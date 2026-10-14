# 預覽：原本的 AI 頭 vs 包覆後的新頭（正面／側面／斜側），以及新頭的佈線、眼睛嘴巴特寫。
# 用法：blender.exe -b wrapped.blend --python preview_wrap.py -- <輸出資料夾>
#   輸出 <資料夾>/cmp_<視角>_ai.png、cmp_<視角>_new.png、wire_<視角>.png（之後在系統 Python 拼成一張）
import bpy, os, sys
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
ai = bpy.data.objects["AI_Head"]
new = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != "AI_Head"]
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'OBJECT'
sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 700
COL = {"Head": (0.93, 0.8, 0.72), "Hair": (0.18, 0.18, 0.2), "Eyes": (0.95, 0.95, 0.95),
       "upper_teeth": (1, 1, 1), "bottom_teeth": (1, 1, 1), "upper_gum": (0.85, 0.45, 0.5), "bottom_gum": (0.85, 0.45, 0.5)}
for o in new:
    o.color = (*COL.get(o.name, (0.7, 0.7, 0.7)), 1)
ai.color = (0.93, 0.8, 0.72, 1)
for o in new + [ai]:
    o.hide_set(False)

wire_mat = bpy.data.materials.new("WIRE")
head = bpy.data.objects["Head"]
w = head.copy()
w.data = head.data.copy()
w.name = "Head_wire"
sc.collection.objects.link(w)
m = w.modifiers.new("wf", 'WIREFRAME')
m.thickness = 0.003
w.color = (0.1, 0.1, 0.15, 1)

cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 70
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam


def shot(path, d, target, dist, show):
    dv = Vector(d).normalized()
    cam.location = Vector(target) - dv * dist
    cam.rotation_euler = dv.to_track_quat('-Z', 'Y').to_euler()
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.hide_render = o not in show
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


views = {"front": (0, 1, 0), "side": (-1, 0, 0), "34": (-0.7, 1, 0.05)}
for name, d in views.items():
    shot(os.path.join(out, f"cmp_{name}_ai.png"), d, (0, -0.2, -0.05), 5.0, [ai])
    shot(os.path.join(out, f"cmp_{name}_new.png"), d, (0, -0.2, -0.05), 5.0, new)
shot(os.path.join(out, "wire_front.png"), (0, 1, 0), (0, -0.4, -0.15), 2.6, [w, bpy.data.objects["Eyes"], bpy.data.objects["Hair"]])
shot(os.path.join(out, "wire_34.png"), (-0.7, 1, 0.05), (0, -0.4, -0.15), 2.6, [w, bpy.data.objects["Eyes"], bpy.data.objects["Hair"]])
print("[preview] ok")
