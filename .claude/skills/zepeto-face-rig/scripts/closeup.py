# 五官近照：每個表情 × 每個部位（嘴、左眼、右眼、眉）。不改 .blend。
# 用法：blender -b <blend> -P gloss.py -P closeup.py -- <輸出資料夾> <landmarks.json> [表情,表情] [部位,部位] [FLAT]
import bpy, os, sys, json
import os as _o
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; os.makedirs(out, exist_ok=True)
LM = json.load(open(a[1], encoding="utf-8"))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-face-rig/scripts", "expr_list.py"), encoding="utf-8").read())
want_e = a[2].split(",") if len(a) > 2 and a[2] else [n for n, _ in EXPR]
want_p = a[3].split(",") if len(a) > 3 and a[3] else ["mouth", "eyeL", "eyeR", "brow"]
sc = bpy.context.scene; cam = sc.camera
eL, eR = Vector(LM["eyes"]["L"]["c"]), Vector(LM["eyes"]["R"]["c"])
mc = Vector(LM["mouth"]["center"])
PARTS = {"mouth": (mc + Vector((0, -0.75, 0.02)), mc, ),
         "mouth34": (mc + Vector((0.5, -0.6, 0.03)), mc),
         "mouth34R": (mc + Vector((-0.5, -0.6, 0.03)), mc),
         "mouthside": (mc + Vector((0.75, -0.25, 0.03)), mc + Vector((0, 0.05, 0))),
         "lips": (mc + Vector((0, -0.42, 0.0)), mc),
         "teethtop": (mc + Vector((0, -0.05, 0.6)), mc + Vector((0, 0.05, 0))),
         "wide34": (mc + Vector((0.9, -1.0, 0.1)), mc + Vector((0, 0.0, 0.05))),
         "wide34R": (mc + Vector((-0.9, -1.0, 0.1)), mc + Vector((0, 0.0, 0.05))),
         "m34": (mc + Vector((0.33, -0.68, 0.04)), mc + Vector((0.02, 0, 0))),
         "m34R": (mc + Vector((-0.33, -0.68, 0.04)), mc + Vector((-0.02, 0, 0))),
         "eyeL": (eL + Vector((0, -0.6, 0)), eL), "eyeR": (eR + Vector((0, -0.6, 0)), eR),
         "brow": ((eL + eR) / 2 + Vector((0, -0.95, 0.1)), (eL + eR) / 2 + Vector((0, 0, 0.1)))}
objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys]
E = dict(EXPR)
frames = [(e, p) for e in want_e for p in want_p]
for f, (en, pn) in enumerate(frames):
    vals = E[en]
    for o in objs:
        for kb in o.data.shape_keys.key_blocks[1:]:
            kb.value = min(vals.get("jawOpen", 0), (vals.get("mouthSmileLeft", 0) + vals.get("mouthSmileRight", 0)) / 2) if kb.name == "jawOpen_smile_corr" else vals.get(kb.name, 0.0)
            kb.keyframe_insert("value", frame=f)
    for m in bpy.data.materials:
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.name.startswith(("BLINK_", "LOOK_", "JAW_")):
                    n.outputs[0].default_value = vals.get("eyeBlink" + n.name[6:], 0.0) if n.name.startswith("BLINK_") else vals.get("jawOpen", 0.0) if n.name == "JAW_OPEN" else vals.get(n.name, 0.0)
                    n.outputs[0].keyframe_insert("default_value", frame=f)
    loc, tgt = PARTS[pn]
    cam.location = loc; cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
for o in objs + [cam]:
    ad = o.data.shape_keys.animation_data if o is not cam else o.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, "fcurves", []):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
if _o.environ.get("CU_BG"):  # 背景換成跟膚色差很多的顏色：近照裡背景不會被誤認成嘴角破洞
    w_ = sc.world or bpy.data.worlds.new("W"); sc.world = w_; w_.use_nodes = True
    bg_ = next(n for n in w_.node_tree.nodes if n.type == 'BACKGROUND')
    bg_.inputs[0].default_value = tuple(float(c) for c in _o.environ["CU_BG"].split(",")) + (1,)
    sc.render.film_transparent = False
sc.frame_start, sc.frame_end = 0, len(frames) - 1
sc.render.resolution_x = sc.render.resolution_y = int(_o.environ.get('CU_RES', 360))
sc.render.filepath = os.path.join(out, ""); sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(animation=True)
open(os.path.join(out, "frames.txt"), "w").write("\n".join(f"{e} {p}" for e, p in frames))
print("[closeup] frames", len(frames))
