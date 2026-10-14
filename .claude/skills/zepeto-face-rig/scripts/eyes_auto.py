# AI 網格路線 ② 眼睛自動偵測（第 1 段：渲圖）：AI 頭正面正交、只有貼圖顏色（不打光），存 png＋換算參數 json。
#   第 2 段（找眼珠）在 eyes_find.py（run_face_rig.py 的 eyes 步驟呼叫）：系統 Python＋PIL。
#   為什麼不用網格頂點找：ZEPETO 畫風眼線粗、眼白少，頂點顏色會抓到眼線或臉旁細髮絲（新娘：眼珠中心抓到 x=±0.44 的髮絲）
# 用法：blender -b <AI 頭 .blend> -P eyes_auto.py -- <輸出 png> <輸出 json> [解析度]
import bpy, sys, json
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
OUT_PNG, OUT_JSON = a[0], a[1]
RES = int(a[2]) if len(a) > 2 else 1400
sc = bpy.context.scene
ob = next(o for o in bpy.data.objects if o.name in ("ZEPETO_Head", "Base_Head"))
for m_ in list(ob.modifiers):
    if m_.type == 'SUBSURF':
        ob.modifiers.remove(m_)
for s_ in ob.material_slots:  # 貼圖接自發光：看到的就是貼圖原色
    nt = s_.material.node_tree
    tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
    em = nt.nodes.new("ShaderNodeEmission")
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        o.hide_render = True
w = sc.world or bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0, 0, 0, 1)
P = [ob.matrix_world @ v.co for v in ob.data.vertices]
x0, x1 = min(p.x for p in P), max(p.x for p in P)
z0, z1 = min(p.z for p in P), max(p.z for p in P)
cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
size = max(x1 - x0, z1 - z0) * 1.02
cam = sc.camera or bpy.data.objects.new("C", bpy.data.cameras.new("C"))
if cam.name not in sc.collection.objects and cam.users_collection == ():
    sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
cam.location = Vector((cx, min(p.y for p in P) - 3.0, cz)); cam.rotation_euler = (1.5708, 0, 0)
sc.render.resolution_x = sc.render.resolution_y = RES
sc.render.film_transparent = False
try:
    sc.view_settings.view_transform = 'Standard'
except Exception:
    pass
sc.render.filepath = OUT_PNG
bpy.ops.render.render(write_still=True)
json.dump(dict(cx=cx, cz=cz, size=size, res=RES, z_top=z1, z_bot=z0), open(OUT_JSON, "w"))
print("[eyes_auto] 渲好 %s（中心 x=%.3f z=%.3f、寬 %.3f）" % (OUT_PNG, cx, cz, size))
