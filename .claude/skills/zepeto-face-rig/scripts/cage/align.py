# 乙路線第 1 步之二：把模板頭等比例縮放、對齊到 AI 頭的兩眼位置，渲正面／側面／斜側疊圖比對。
#   只做「縮放＋平移」（相似變換），還沒有變形；目的是看兩顆頭還差多少。
#   輸出：preview/align_<視角>_ai.png、_tmpl.png（之後在系統 Python 疊成一張），aligned.blend（模板已對齊＋AI 頭）
# 用法：blender.exe -b template_clean.blend --python align.py -- <AI 頭 .blend> <AI 五官 landmarks.json>
import bpy, os, sys, json
import numpy as np
from mathutils import Vector, Matrix

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
# 每張臉的輸出資料夾（環境變數 ZEPETO_RIG_WORK）與模板資料夾（ZEPETO_RIG_TEMPLATE）；run_face_rig.py 會設好
WORK = os.environ.get("ZEPETO_RIG_WORK") or os.getcwd()
TEMPLATE = os.environ.get("ZEPETO_RIG_TEMPLATE") or os.path.normpath(
    os.path.join(_SCRIPTS, "..", "..", "..", "..", "docs", "data", "blender", "zepeto", "templates", "cartoon-head-lucadrech"))
HERE = WORK
ai_blend, ai_lm_path = sys.argv[sys.argv.index("--") + 1:][:2]
T = json.load(open(os.path.join(TEMPLATE, "template_landmarks.json"), encoding="utf-8"))
A = json.load(open(ai_lm_path, encoding="utf-8"))
sc = bpy.context.scene

# ── 相似變換：兩眼距離一樣、兩眼中點重合 ──
t_mid = (np.array(T["eyes"]["L"]["c"]) + np.array(T["eyes"]["R"]["c"])) / 2
a_mid = (np.array(A["eyes"]["L"]["c"]) + np.array(A["eyes"]["R"]["c"])) / 2
s = A["U"] / T["U"]
M = Matrix.Translation(Vector(a_mid)) @ Matrix.Scale(s, 4) @ Matrix.Translation(Vector(-t_mid))
tmpl_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in tmpl_objs:
    o.matrix_world = M @ o.matrix_world
for o in tmpl_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = tmpl_objs[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ── 載入 AI 頭（只要網格物件） ──
with bpy.data.libraries.load(ai_blend, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in ("ZEPETO_Head", "Base_Head")]
ai = dst.objects[0]
sc.collection.objects.link(ai)
ai.name = "AI_Head"
ai.modifiers.clear()

# ── 疊圖用：Workbench 純色，各渲一張 ──
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'OBJECT'
sc.display.shading.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 800
sc.render.film_transparent = True
ai.color = (0.95, 0.55, 0.45, 1)
for o in tmpl_objs:
    o.color = (0.45, 0.7, 1.0, 1)
cam_d = bpy.data.cameras.new("cam")
cam_d.type = 'ORTHO'
cam_d.ortho_scale = 2.2
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
target = Vector((0.0, -0.3, -0.1))
out = os.path.join(HERE, "preview")
os.makedirs(out, exist_ok=True)
for name, d in (("front", (0, 1, 0)), ("side", (-1, 0, 0)), ("34", (-0.7, 1, 0))):
    dv = Vector(d).normalized()
    cam.location = target - dv * 6
    cam.rotation_euler = dv.to_track_quat('-Z', 'Y').to_euler()
    for which, show in (("ai", [ai]), ("tmpl", tmpl_objs)):
        for o in [ai] + tmpl_objs:
            o.hide_render = o not in show
        sc.render.filepath = os.path.join(out, f"align_{name}_{which}.png")
        bpy.ops.render.render(write_still=True)
for o in [ai] + tmpl_objs:
    o.hide_render = False

# 對齊後兩邊的五官（給下一步變形用）
tm = {k: (np.array(v) - t_mid) * s + a_mid for k, v in (("nose", T["nose"]), ("chin", T["chin"]), ("mouth_L", T["mouth"]["L"]), ("mouth_R", T["mouth"]["R"]))}
print("[align] scale %.4f；對齊後模板 鼻尖 %s 嘴角 L%s R%s 下巴 %s" % (s, np.round(tm["nose"], 3), np.round(tm["mouth_L"], 3), np.round(tm["mouth_R"], 3), np.round(tm["chin"], 3)))
print("[align] AI 頭       鼻 z %.3f 嘴角 L%s R%s 下巴 z %.3f" % (A["nose"][2], np.round(A["mouth"]["L"], 3), np.round(A["mouth"]["R"], 3), A["chin_z"]))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "aligned.blend"))
