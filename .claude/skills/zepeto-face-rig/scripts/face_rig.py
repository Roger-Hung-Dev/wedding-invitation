# AI 網格路線 ⑥ 控制骨架：照舊路線（模板當成品，2026-10-14 停用、封存在 D:/render-work/archive/zepeto-face-rig-old-route-20261014）
#   的 face_rig.py（11 根控制骨頭、同名形態鍵一起推），差別：
#   - 推的是 AI_Driven（AI 網格本身）＋牙齒、牙齦、舌頭的形態鍵
#   - 眨眼、看方向是材質數值（AI 的眼睛畫在貼圖上）：CTRL_Blink_L/R → BLINK_Left/Right；CTRL_Eyes → LOOK_L/R_X、_Z
#     （同時也推 eyeLook* 形態鍵：眼周皮膚跟著動）
#   - JAW_OPEN（張嘴時淡化嘴角笑紋）跟著 AI_Driven 的 jawOpen 形態鍵值
#   - 模板留下來的眼球 Eye_L／Eye_R（材質眼睛用不到）刪掉
#   驅動器全部是簡單運算式（開檔不必允許自動執行腳本）。
# 用法：blender -b pack.blend -P face_rig.py -- <輸出 head_rig.blend> <landmarks.json>
import bpy, sys, math
from mathutils import Vector

_a = sys.argv[sys.argv.index("--") + 1:]
OUT = _a[0]
LMP = _a[1] if len(_a) > 1 else None
sc = bpy.context.scene
ai = bpy.data.objects.get("Head") or bpy.data.objects["AI_Driven"]  # 整理過交接格式（pack_head.py）的叫 Head
for n in ("Eye_L", "Eye_R"):
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
parts = [o for o in bpy.data.objects if o.type == 'MESH' and o.name in
         ("AI_Driven", "Head", "Hair", "Ears", "upper_teeth", "bottom_teeth", "upper_gum", "bottom_gum", "Tongue")]
keyed = [o for o in parts if o.data.shape_keys]
# 所有形態鍵先歸零：沒接控制骨頭的（瞇眼、睜大、鼓臉頰…留給表情捕捉）存檔時是什麼值就一直是什麼值
#   （transfer 後留在 1 → 骨架檔一打開所有表情全開、臉扭成一團）
for o in keyed:
    for k in o.data.shape_keys.key_blocks[1:]:
        k.value = 0.0
P = [ai.matrix_world @ v.co for v in ai.data.vertices]
xmax = max(p.x for p in P)
zmin, zmax = min(p.z for p in P), max(p.z for p in P)
L = 0.12  # 控制器的移動距離（拉到底＝1）
# 形態鍵（同舊路線）；"@材質數值" 開頭的是材質節點
CTRLS = [
    ("CTRL_Jaw",        (0.0, -1.0), ("x", -L, L), ("y", -L, 0), {"jawOpen": "max(0, -vy)", "jawLeft": "max(0, vx)", "jawRight": "max(0, -vx)"}),
    ("CTRL_Smile",      (0.0, -0.55), None, ("y", 0, L), {"mouthSmileLeft": "vy", "mouthSmileRight": "vy"}),
    ("CTRL_Mouth",      (0.45, -0.75), ("x", -L, L), ("y", -L, L),
     {"mouthLeft": "max(0, vx)", "mouthRight": "max(0, -vx)", "mouthSmileLeft": "max(0, vy)", "mouthSmileRight": "max(0, vy)",
      "mouthFrownLeft": "max(0, -vy)", "mouthFrownRight": "max(0, -vy)"}),
    ("CTRL_Blink_L",    (0.45, 0.15), None, ("y", -L, 0), {"@BLINK_Left": "max(0, -vy)"}),
    ("CTRL_Blink_R",    (0.0, 0.15), None, ("y", -L, 0), {"@BLINK_Right": "max(0, -vy)"}),
    ("CTRL_Eyes",       (0.22, -0.2), ("x", -L, L), ("y", -L, L),
     {"eyeLookUpLeft": "max(0, vy)", "eyeLookUpRight": "max(0, vy)", "eyeLookDownLeft": "max(0, -vy)", "eyeLookDownRight": "max(0, -vy)",
      # 從鏡頭看往右（+X）＝角色往自己的左邊看：左眼往外、右眼往內；材質虹膜往 +X 移
      "eyeLookOutLeft": "max(0, vx)", "eyeLookInRight": "max(0, vx)", "eyeLookInLeft": "max(0, -vx)", "eyeLookOutRight": "max(0, -vx)",
      "@LOOK_L_X": "vx", "@LOOK_R_X": "vx", "@LOOK_L_Z": "vy", "@LOOK_R_Z": "vy"}),
    ("CTRL_Brow_L",     (0.45, 0.55), None, ("y", -L, L), {"browOuterUpLeft": "max(0, vy)", "browDownLeft": "max(0, -vy)"}),
    ("CTRL_Brow_R",     (0.0, 0.55), None, ("y", -L, L), {"browOuterUpRight": "max(0, vy)", "browDownRight": "max(0, -vy)"}),
    ("CTRL_Brow_Inner", (0.22, 0.85), None, ("y", 0, L), {"browInnerUp": "vy"}),
    ("CTRL_Tongue",     (0.45, -1.0), None, ("y", -L, 0), {"tongueOut": "max(0, -vy)", "jawOpen": "max(0, -vy) * 0.45"}),
    ("CTRL_MouthClose", (0.22, -1.0), None, ("y", -L, 0), {"mouthClose": "max(0, -vy)", "jawOpen": "max(0, -vy)"}),
]

for n in ("Face_Rig",):
    o = bpy.data.objects.get(n)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)
for o in keyed:
    ad = o.data.shape_keys.animation_data
    if ad:
        for fc in list(ad.drivers):
            ad.drivers.remove(fc)

wgt_col = bpy.data.collections.get("WGT") or bpy.data.collections.new("WGT")
if wgt_col.name not in sc.collection.children:
    sc.collection.children.link(wgt_col)
wgt_col.hide_viewport = wgt_col.hide_render = True
circle = bpy.data.objects.get("WGT_circle")
if circle is None:
    cm = bpy.data.meshes.new("WGT_circle")
    n = 24
    cm.from_pydata([(math.cos(2 * math.pi * i / n) * 0.5, 0, math.sin(2 * math.pi * i / n) * 0.5) for i in range(n)],
                   [(i, (i + 1) % n) for i in range(n)], [])
    circle = bpy.data.objects.new("WGT_circle", cm)
    wgt_col.objects.link(circle)

arm = bpy.data.armatures.new("Face_Rig")
rig = bpy.data.objects.new("Face_Rig", arm)
sc.collection.objects.link(rig)
rig.show_in_front = True
for o in bpy.context.view_layer.objects:
    o.select_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones.new("head")
# 轉軸：下巴往上 3.5% 頭高、頭的中線後方 0.1（照舊產線新娘頭量出來的位置：chin −0.282、pivot −0.24、top 0.95）
#   用整顆頭的最低點算的話，長髮垂到背後、轉軸跑到下巴下面 0.35（身體端的頭骨會在胸口轉）
if LMP:
    import json as _j
    _ch = _j.load(open(LMP, encoding="utf-8"))["chin_z"]
    _top = max((o.matrix_world @ Vector(c)).z for o in parts for c in o.bound_box)
    pz = _ch + 0.035 * (_top - _ch)
else:
    pz = zmin + 0.25 * (zmax - zmin)
eb.head = (0.0, 0.1, pz)
eb.tail = (0.0, 0.1, zmax)
eb.use_deform = False
origin = Vector((xmax + 0.35, -0.6, 0.0))
for name, (cx, cz), ax, ay, _ in CTRLS:
    b = arm.edit_bones.new(name)
    b.head = origin + Vector((cx, 0.0, cz))
    b.tail = b.head + Vector((0, 0, 0.08))
    b.roll = 0.0
    b.parent = arm.edit_bones["head"]
    b.use_deform = False
bpy.ops.object.mode_set(mode='POSE')
for name, _, ax, ay, _ in CTRLS:
    pb = rig.pose.bones[name]
    pb.custom_shape = circle
    pb.custom_shape_scale_xyz = (0.9, 0.9, 0.9)
    pb.lock_rotation = (True, True, True)
    pb.lock_rotation_w = True
    pb.lock_scale = (True, True, True)
    pb.lock_location = (ax is None, ay is None, True)
    c = pb.constraints.new('LIMIT_LOCATION')
    c.owner_space = 'LOCAL'
    c.use_transform_limit = True
    c.use_min_x = c.use_max_x = c.use_min_y = c.use_max_y = c.use_min_z = c.use_max_z = True
    c.min_x, c.max_x = (ax[1], ax[2]) if ax else (0, 0)
    c.min_y, c.max_y = (ay[1], ay[2]) if ay else (0, 0)
    c.min_z = c.max_z = 0.0
bpy.ops.object.mode_set(mode='OBJECT')

bpy.context.view_layer.update()
for o in parts:
    mw = o.matrix_world.copy()
    o.parent = rig
    o.parent_type = 'BONE'
    o.parent_bone = "head"
    bpy.context.view_layer.update()
    o.matrix_world = mw

# 材質數值節點所在的材質（eyes_shader.py 建在 AI 皮膚材質裡）
mat_nodes = {}  # 名稱 → [(node_tree, 節點)]：皮膚材質複製給頭髮、耳朵、嘴唇後，同名節點有好幾份，全部都接
for m in bpy.data.materials:
    if m.node_tree and m.users:
        for nd in m.node_tree.nodes:
            if nd.type == 'VALUE' and nd.name.startswith(("BLINK_", "LOOK_", "JAW_OPEN")):
                mat_nodes.setdefault(nd.name, []).append((m.node_tree, nd))


def setup(drv, srcs):
    terms = []
    for i, (bone, expr) in enumerate(srcs):
        for axis in ("x", "y"):
            if f"v{axis}" not in expr:
                continue
            v = drv.variables.new()
            v.name = f"v{axis}{i}"
            v.type = 'TRANSFORMS'
            t = v.targets[0]
            t.id = rig
            t.bone_target = bone
            t.transform_type = 'LOC_X' if axis == "x" else 'LOC_Y'
            t.transform_space = 'LOCAL_SPACE'
        terms.append(expr.replace("vx", f"(vx{i}/{L})").replace("vy", f"(vy{i}/{L})"))
    drv.type = 'SCRIPTED'
    drv.expression = terms[0] if len(terms) == 1 else "max(" + ", ".join(terms) + ")"


targets = {}
for name, _, ax, ay, keys in CTRLS:
    for key, expr in keys.items():
        targets.setdefault(key, []).append((name, expr))
n_drv, simple, missing = 0, [], []
for key, srcs in targets.items():
    if key.startswith("@"):
        nn = key[1:]
        if nn not in mat_nodes:
            missing.append(nn); continue
        for nt, nd in mat_nodes[nn]:
            fc = nt.driver_add(f'nodes["{nn}"].outputs[0].default_value')
            setup(fc.driver, srcs)
            for m_ in list(fc.modifiers):
                fc.modifiers.remove(m_)
            n_drv += 1; simple.append(fc.driver.is_simple_expression)
        continue
    for o in keyed:
        if key not in o.data.shape_keys.key_blocks:
            continue
        fc = o.data.shape_keys.driver_add(f'key_blocks["{key}"].value')
        setup(fc.driver, srcs)
        for m_ in list(fc.modifiers):
            fc.modifiers.remove(m_)
        n_drv += 1; simple.append(fc.driver.is_simple_expression)
# 大笑修正鍵（AI_Driven 若有轉移到）
kb_c = ai.data.shape_keys.key_blocks.get("jawOpen_smile_corr")
if kb_c:
    fc = ai.data.shape_keys.driver_add('key_blocks["jawOpen_smile_corr"].value')
    drv = fc.driver; drv.type = 'SCRIPTED'
    for vn, bone in (("j", "CTRL_Jaw"), ("s", "CTRL_Smile"), ("m", "CTRL_Mouth")):
        v = drv.variables.new(); v.name = vn; v.type = 'TRANSFORMS'
        t = v.targets[0]; t.id = rig; t.bone_target = bone; t.transform_type = 'LOC_Y'; t.transform_space = 'LOCAL_SPACE'
    drv.expression = f"min(max(0, -j/{L}), max(s/{L}, max(0, m/{L})))"
    for m_ in list(fc.modifiers):
        fc.modifiers.remove(m_)
    n_drv += 1; simple.append(drv.is_simple_expression)
# JAW_OPEN：讀 AI_Driven 的 jawOpen 形態鍵值（張嘴、吐舌頭、閉嘴控制器都會推到它）
for nt, nd in mat_nodes.get("JAW_OPEN", []):
    fc = nt.driver_add('nodes["JAW_OPEN"].outputs[0].default_value')
    drv = fc.driver; drv.type = 'SCRIPTED'
    v = drv.variables.new(); v.name = "j"; v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'KEY'; v.targets[0].id = ai.data.shape_keys
    v.targets[0].data_path = 'key_blocks["jawOpen"].value'
    drv.expression = "j"
    for m_ in list(fc.modifiers):
        fc.modifiers.remove(m_)
    n_drv += 1; simple.append(drv.is_simple_expression)
# 打開就是姿勢模式、沒選任何骨頭：使用者直接點圓圈按 G 就能拉（物件模式時按 G 會整副骨架一起移動）
for o in bpy.context.view_layer.objects:
    o.select_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')
for pb in rig.pose.bones:
    pb.select = False  # Blender 5 的選取在 PoseBone 上（Bone.select 已拿掉）
arm.bones["head"].hide = True  # head 骨頭（接身體用、不用拉）藏起來：骨架顯示在最前面，它是穿過臉中間的一根灰柱子；要用時 Alt+H
for scr in bpy.data.screens:
    for area in scr.areas:
        for sp in area.spaces:
            if sp.type == 'VIEW_3D':
                sp.shading.type = 'MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("[rig] 控制骨頭 %d 根、驅動器 %d 個（材質數值 %d）、全部是簡單運算式：%s%s" % (
    len(CTRLS), n_drv, sum(1 for k in targets if k.startswith("@") and k[1:] in mat_nodes) + ("JAW_OPEN" in mat_nodes),
    all(simple), "；找不到材質數值 %s" % missing if missing else ""))
