# 成品預覽圖（身體端的頭清單、可動臉端驗收、使用者看）。不改 .blend。
# 用法：
#   blender -b head_rig.blend -P previews.py -- mat <輸出資料夾> <AI 頭 .blend>
#       → mat_front_new.png、mat_34_new.png（成品）、mat_front_ai.png、mat_34_ai.png（AI 原頭：同一組鏡頭、燈光，才比得出像不像）
#   blender -b head_rig.blend -P previews.py -- keys <影格資料夾>
#       → 52 個 ARKit 單一表情各一格＋frames.txt（run_face_rig.py 拼成 preview/sheet_keys.png）
#   head_rig.blend 的形態鍵、材質數值由驅動器推，直接設值會被蓋掉 → 這裡先把驅動器全部靜音（不存檔，所以不影響成品）
import bpy, sys, os, math
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
MODE, OUT = a[0], a[1]
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
cam = sc.camera
if cam is None:
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'PERSP'; cam.data.lens = 85; cam.data.sensor_width = 36
sc.render.image_settings.file_format = 'PNG'
try:
    sc.eevee.taa_render_samples = 32
except Exception:
    pass
for o in bpy.data.objects:  # 控制骨架、骨頭外形不入鏡
    if o.type == 'ARMATURE' or o.name.startswith("WGT_"):
        o.hide_render = True
for idb in list(bpy.data.shape_keys) + [m.node_tree for m in bpy.data.materials if m.node_tree]:
    ad = idb.animation_data
    if ad:
        for fc in ad.drivers:
            fc.mute = True
HEADS = [o for o in bpy.data.objects if o.type == 'MESH' and o.visible_get() and not o.hide_render]


def look(loc, tgt):
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()


def render(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


if MODE == "mat":
    # 取景：成品（頭＋頭髮＋耳朵）的外框，鏡頭距離至少照舊路線的 5.6（85mm）
    pts = [o.matrix_world @ Vector(c) for o in HEADS if o.name in ("Head", "Hair", "Ears") for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2
    d = max(5.6, max(hi.z - lo.z, hi.x - lo.x) * 1.1 / 2 / (18 / 85))
    VIEWS = {"front": ((c.x, c.y - d, c.z), (c.x, c.y, c.z)),
             "34": ((c.x + d * 0.7, c.y - d * 0.7, c.z + 0.2), (c.x, c.y, c.z))}
    sc.render.resolution_x = sc.render.resolution_y = 600
    for v, (loc, tgt) in VIEWS.items():
        look(loc, tgt); render(os.path.join(OUT, "mat_%s_new.png" % v))
    # AI 原頭：append 進同一個場景（同鏡頭燈光），成品藏起來
    ai_path = a[2]
    with bpy.data.libraries.load(ai_path) as (src, dst):
        dst.objects = [n for n in src.objects if n == "ZEPETO_Head"]
    if not dst.objects:
        raise SystemExit("[previews] AI 頭檔裡沒有 ZEPETO_Head：%s" % ai_path)
    ai = dst.objects[0]
    sc.collection.objects.link(ai)
    for img in bpy.data.images:  # AI 頭的貼圖是相對於 AI 頭檔的 //…，append 進來後要換成絕對路徑
        if img.source == 'FILE' and not img.packed_file and img.filepath.startswith("//") and not os.path.exists(bpy.path.abspath(img.filepath)):
            p = os.path.join(os.path.dirname(os.path.abspath(ai_path)), img.filepath[2:])
            if os.path.exists(p):
                img.filepath = p; img.reload()
    for o in HEADS:
        o.hide_render = True
    for v, (loc, tgt) in VIEWS.items():
        look(loc, tgt); render(os.path.join(OUT, "mat_%s_ai.png" % v))
    print("[previews] mat：鏡頭距離 %.2f、中心 %s" % (d, tuple(round(x, 3) for x in c)))

elif MODE == "keys":
    ARKIT_52 = [
        "eyeBlinkLeft", "eyeLookDownLeft", "eyeLookInLeft", "eyeLookOutLeft", "eyeLookUpLeft", "eyeSquintLeft", "eyeWideLeft",
        "eyeBlinkRight", "eyeLookDownRight", "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight", "eyeSquintRight", "eyeWideRight",
        "jawForward", "jawLeft", "jawRight", "jawOpen",
        "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
        "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
        "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight",
        "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper",
        "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight",
        "mouthUpperUpLeft", "mouthUpperUpRight",
        "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
        "cheekPuff", "cheekSquintLeft", "cheekSquintRight",
        "noseSneerLeft", "noseSneerRight",
        "tongueOut",
    ]
    # ARKit 規格要跟張嘴一起用的（單獨開會穿過嘴唇）：照控制骨架帶的量（face_rig.py：CTRL_Tongue 帶 0.45、CTRL_MouthClose 帶一樣大）
    #   mouthClose 不能大於 jawOpen：試過 jawOpen 0.5＋mouthClose 1，上下唇交叉、嘴角像被撕開
    WITH = {"tongueOut": {"jawOpen": 0.45}, "mouthClose": {"jawOpen": 1.0}}
    # 眨眼、看方向在材質上（AI 的眼睛畫在貼圖上）：角色的左＝+X；LOOK_*_X 正＝虹膜往 +X
    MATV = {"eyeBlinkLeft": {"BLINK_Left": 1}, "eyeBlinkRight": {"BLINK_Right": 1},
            "eyeLookOutLeft": {"LOOK_L_X": 1}, "eyeLookInLeft": {"LOOK_L_X": -1},
            "eyeLookOutRight": {"LOOK_R_X": -1}, "eyeLookInRight": {"LOOK_R_X": 1},
            "eyeLookUpLeft": {"LOOK_L_Z": 1}, "eyeLookDownLeft": {"LOOK_L_Z": -1},
            "eyeLookUpRight": {"LOOK_R_Z": 1}, "eyeLookDownRight": {"LOOK_R_Z": -1}}
    objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys]
    nodes = [n for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes
             if n.type == 'VALUE' and n.name.startswith(("BLINK_", "LOOK_", "JAW_OPEN"))]
    look((0.0, -3.0, 0.1), (0.0, -0.5, 0.08))  # 同 render_set.py 的正面（臉部特寫）
    labels = []
    for f, k in enumerate(ARKIT_52):
        vals = dict(WITH.get(k, {}), **{k: 1.0})
        for o in objs:
            for kb in o.data.shape_keys.key_blocks[1:]:
                kb.value = vals.get(kb.name, 0.0)  # eyeBlink*_geo、jawOpen_smile_corr 都歸 0
                kb.keyframe_insert("value", frame=f)
        mv = dict(MATV.get(k, {}), JAW_OPEN=vals.get("jawOpen", 0.0))
        for n in nodes:
            n.outputs[0].default_value = mv.get(n.name, 0.0)
            n.outputs[0].keyframe_insert("default_value", frame=f)
        labels.append(k + ("（＋張嘴 %.2g）" % WITH[k]["jawOpen"] if k in WITH else ""))
    for idb in [o.data.shape_keys for o in objs] + [m.node_tree for m in bpy.data.materials if m.node_tree]:
        ad = idb.animation_data
        if ad and ad.action:
            for fc in getattr(ad.action, "fcurves", []):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'CONSTANT'
    sc.frame_start, sc.frame_end = 0, len(ARKIT_52) - 1
    sc.render.resolution_x = sc.render.resolution_y = 300
    sc.render.filepath = os.path.join(OUT, "")
    bpy.ops.render.render(animation=True)
    open(os.path.join(OUT, "frames.txt"), "w", encoding="utf-8").write("\n".join(labels))
    print("[previews] keys：%d 格（形態鍵物件 %d、材質數值 %d）" % (len(ARKIT_52), len(objs), len(nodes)))
else:
    raise SystemExit("[previews] 不認得的模式：%s" % MODE)
