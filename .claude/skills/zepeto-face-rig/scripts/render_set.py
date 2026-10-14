# 渲固定幾個代表表情（正面＋斜側），所有帶形態鍵的網格都照名字套值。不改 .blend。
# 用法：blender -b <blend> -P render_set.py -- <輸出資料夾> [hide=物件名,物件名]
import bpy, os, sys
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:]
out = args[0]; os.makedirs(out, exist_ok=True)
hide = set(args[1].split(",")) if len(args) > 1 and args[1] else set()
sc = bpy.context.scene; cam = sc.camera
for o in bpy.data.objects:
    if o.name in hide: o.hide_render = True
EXPR = [
    ("basis", {}),
    ("jawOpen", {"jawOpen": 0.7}),
    ("smile", {"mouthSmileLeft": 1, "mouthSmileRight": 1, "cheekSquintLeft": .7, "cheekSquintRight": .7, "eyeSquintLeft": .4, "eyeSquintRight": .4}),
    ("blink", {"eyeBlinkLeft": 1, "eyeBlinkRight": 1}),
    ("surprise", {"eyeWideLeft": 1, "eyeWideRight": 1, "browInnerUp": 1, "browOuterUpLeft": 1, "browOuterUpRight": 1, "jawOpen": .8, "mouthFunnel": .4}),
    ("lookSide", {"LOOK_L_X": 1, "LOOK_R_X": 1}),
    ("lookUp", {"LOOK_L_Z": 1, "LOOK_R_Z": 1}),
    ("angry", {"browDownLeft": 1, "browDownRight": 1, "mouthFrownLeft": .7, "mouthFrownRight": .7, "noseSneerLeft": .4, "noseSneerRight": .4}),
    ("sad", {"browInnerUp": 1, "mouthFrownLeft": 1, "mouthFrownRight": 1, "mouthLowerDownLeft": .3, "mouthLowerDownRight": .3}),
    ("pucker", {"mouthPucker": 1}),
    ("cheekPuff", {"cheekPuff": 1}),
    ("tongue", {"jawOpen": .45, "tongueOut": 1}),
    ("wink", {"eyeBlinkLeft": 1, "mouthSmileLeft": .6, "cheekSquintLeft": .5}),
    ("laugh", {"mouthSmileLeft": 1, "mouthSmileRight": 1, "jawOpen": .55, "cheekSquintLeft": .8, "cheekSquintRight": .8, "eyeSquintLeft": .5, "eyeSquintRight": .5}),
]
VIEWS = {"front": ((0.0, -3.0, 0.1), (0.0, -0.5, 0.08)), "34": ((1.9, -2.2, 0.1), (0.0, -0.4, 0.06))}
if len(args) > 2: VIEWS = {k: VIEWS[k] for k in args[2].split(",")}
objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys]
frames = [(v, e) for v in VIEWS for e in EXPR]
for f, (view, (name, vals)) in enumerate(frames):
    for o in objs:
        for kb in o.data.shape_keys.key_blocks[1:]:
            if kb.name == "jawOpen_smile_corr":
                kb.value = min(vals.get("jawOpen", 0), (vals.get("mouthSmileLeft", 0) + vals.get("mouthSmileRight", 0)) / 2)
            else:
                kb.value = vals.get(kb.name, 0.0)
            kb.keyframe_insert("value", frame=f)
    for m in bpy.data.materials:
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.name.startswith(("BLINK_", "LOOK_", "JAW_")):
                    n.outputs[0].default_value = vals.get("eyeBlink" + n.name[6:], 0.0) if n.name.startswith("BLINK_") else vals.get("jawOpen", 0.0) if n.name == "JAW_OPEN" else vals.get(n.name, 0.0)
                    n.outputs[0].keyframe_insert("default_value", frame=f)
    loc, tgt = VIEWS[view]
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
for o in objs + [cam]:
    ad = o.data.shape_keys.animation_data if o is not cam else o.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, "fcurves", []):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
sc.frame_start, sc.frame_end = 0, len(frames) - 1
sc.render.resolution_x = sc.render.resolution_y = 420
try: sc.eevee.taa_render_samples = 24
except Exception: pass
sc.render.filepath = os.path.join(out, "")
sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(animation=True)
open(os.path.join(out, "frames.txt"), "w").write("\n".join(f"{i:04d} {v} {e[0]}" for i, (v, e) in enumerate(frames)))
print("[render] frames", len(frames))
