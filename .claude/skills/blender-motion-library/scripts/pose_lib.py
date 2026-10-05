# 姿勢工具：exec 在 Blender 裡。
# 角度慣例（世界軸，rest 姿勢下）：角色面向 -Y，角色左手 = +X。
# 上臂 Y +90 = 左手垂下、-90 = 右手垂下；手臂垂下後再繞 X 負值 = 往前抬。
# 手指在 rest（T 姿勢）狀態下先轉（左手 Y 正值 = 往掌心彎），之後手臂再轉，手指會跟著走。
import bpy, math
from mathutils import Vector, Matrix

FINGERS = ["Thumb", "Index", "Middle", "Ring", "Little"]
BODY_ORDER = ["Hips", "Spine", "Chest", "UpperChest", "Neck", "Head",
              "L_Shoulder", "L_UpperArm", "L_LowerArm", "L_Hand", "R_Shoulder", "R_UpperArm", "R_LowerArm", "R_Hand",
              "L_UpperLeg", "L_LowerLeg", "L_Foot", "L_ToeBase", "R_UpperLeg", "R_LowerLeg", "R_Foot", "R_ToeBase"]


def bn(k):
    return ("J_Bip_C_" if "_" not in k else "J_Bip_") + k


def rot_world(arm, bone, axis, deg):
    pb = arm.pose.bones[bone]; bpy.context.view_layer.update()
    m = pb.matrix.copy(); h = m.to_translation()
    ax = Vector(axis).normalized() if not isinstance(axis, str) else axis
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, ax) @ Matrix.Translation(-h) @ m
    pb.scale = (1, 1, 1); pb.location = (0, 0, 0)      # 矩陣指定會漏出微小縮放，強制歸一避免累積
    pb.rotation_quaternion.normalize()   # 不在這裡 update：下一次 rot_world 開頭會 update，省一半時間


def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def check_scales(arm, allow=("Skirt_Sway",)):
    bad = [pb.name for pb in arm.pose.bones if pb.name not in allow and any(abs(x - 1) > 1e-3 for x in pb.scale)]
    if bad:
        raise RuntimeError("bones with abnormal scaling: " + ", ".join(bad[:5]))


# ── 手勢：每根手指 (第1節, 第2節, 第3節) 彎曲角度；拇指另有「往掌心收」 ──
HANDS = {
    "relax": dict(Thumb=(8, 12, 10), Index=(8, 14, 10), Middle=(12, 18, 12), Ring=(16, 22, 14), Little=(20, 26, 16), spread=-2),
    "open":  dict(Thumb=(0, 0, 0), Index=(0, 2, 2), Middle=(0, 2, 2), Ring=(0, 2, 2), Little=(0, 2, 2), spread=4),
    "fist":  dict(Thumb=(25, 35, 30), Index=(80, 95, 60), Middle=(85, 95, 60), Ring=(88, 95, 60), Little=(90, 95, 60), spread=-3),
    "point": dict(Thumb=(25, 35, 30), Index=(0, 2, 2), Middle=(85, 95, 60), Ring=(88, 95, 60), Little=(90, 95, 60), spread=-2),
    "grip":  dict(Thumb=(20, 25, 20), Index=(45, 55, 35), Middle=(50, 58, 38), Ring=(55, 60, 40), Little=(58, 62, 40), spread=-2),
    "pinch": dict(Thumb=(22, 28, 20), Index=(35, 45, 30), Middle=(20, 30, 20), Ring=(25, 35, 22), Little=(30, 40, 25), spread=0),
    "peace": dict(Thumb=(25, 35, 30), Index=(0, 2, 2), Middle=(0, 2, 2), Ring=(88, 95, 60), Little=(90, 95, 60), spread=9, spread_mid=-1.0),
    "flat":  dict(Thumb=(0, 0, 0), Index=(0, 0, 0), Middle=(0, 0, 0), Ring=(0, 0, 0), Little=(0, 0, 0), spread=0),
    "seam":  dict(Thumb=(0, 4, 4), Index=(0, 3, 2), Middle=(0, 3, 2), Ring=(0, 3, 2), Little=(0, 3, 2), spread=-5, thumb_in=30),   # 立正貼褲縫：四指併攏伸直、拇指在手掌平面內靠到食指旁
}


_HAND_CACHE = {}


def hand_pose(arm, side, spec):
    """rest 狀態下彎手指（結果是相對父骨的局部旋轉，所以算一次就快取起來直接套用）"""
    key = (arm.name, side, spec if not isinstance(spec, tuple) else (spec[0], spec[1], round(spec[2], 2)))
    if key in _HAND_CACHE:
        for name, q in _HAND_CACHE[key].items():
            arm.pose.bones[name].rotation_quaternion = q
        return
    _hand_pose(arm, side, spec if not isinstance(spec, tuple) else (spec[0], spec[1], round(spec[2], 2)))
    bpy.context.view_layer.update()
    _HAND_CACHE[key] = {pb.name: pb.rotation_quaternion.copy() for pb in arm.pose.bones
                        if pb.name.startswith(f"J_Bip_{side}_") and any(f in pb.name for f in FINGERS)}


def _hand_pose(arm, side, spec):
    """rest 狀態下彎手指。spec 可以是 HANDS 的名字或 dict；可用 ('relax','fist',t) 做兩種手勢的內插"""
    if isinstance(spec, str):
        spec = HANDS[spec]
    elif isinstance(spec, tuple):
        a, b, t = HANDS[spec[0]], HANDS[spec[1]], spec[2]
        def mix(k):
            x, y = a.get(k, 0), b.get(k, 0)
            return tuple(p + (q - p) * t for p, q in zip(x, y)) if isinstance(x, tuple) else x + (y - x) * t
        spec = {k: mix(k) for k in set(a) | set(b)}
    sg = 1 if side == "L" else -1
    B = arm.data.bones
    for f in FINGERS:
        for j, deg in enumerate(spec[f]):
            name = f"J_Bip_{side}_{f}{j + 1}"
            if name not in B or abs(deg) < 1e-3:
                continue
            if f == "Thumb":
                d = (B[name].tail_local - B[name].head_local).normalized()
                axis = d.cross(Vector((0, 0, -1))).normalized()   # 正角度：拇指尖往掌心（下方）收，左右手同號
                rot_world(arm, name, axis, deg)
            else:
                rot_world(arm, name, "Y", deg * sg)
    ti = spec.get("thumb_in", 0)         # 拇指在手掌平面內往食指靠（繞 rest 時的掌心法線轉）；舊手勢沒有這欄，不受影響
    if ti and f"J_Bip_{side}_Thumb1" in B:
        rot_world(arm, f"J_Bip_{side}_Thumb1", "Z", ti * sg)
    sp = spec.get("spread", 0)
    if sp:
        for f, k in (("Index", 1), ("Middle", spec.get("spread_mid", 0)), ("Ring", -0.6), ("Little", -1.2)):
            if not k:
                continue
            rot_world(arm, f"J_Bip_{side}_{f}1", "Z", sp * k * sg)


def apply_pose(arm, P):
    """P：{骨頭 key: [(軸, 角度), ...], 'hands': (左手勢, 右手勢)}"""
    reset_pose(arm)
    hl, hr = P.get("hands", ("relax", "relax"))
    hand_pose(arm, "L", hl); hand_pose(arm, "R", hr)
    for k in BODY_ORDER:
        for axis, deg in P.get(k, []):
            rot_world(arm, bn(k), axis, deg)


FACE_KEYS = ["Fcl_ALL_Fun", "Fcl_ALL_Joy", "Fcl_ALL_Angry", "Fcl_ALL_Sorrow", "Fcl_ALL_Surprised",
             "Fcl_EYE_Close", "Fcl_EYE_Close_L", "Fcl_EYE_Close_R", "Fcl_MTH_A", "Fcl_MTH_I", "Fcl_MTH_U", "Fcl_MTH_E", "Fcl_MTH_O"]


def set_face(vals, who=None):
    who = who or WHO
    kb = bpy.data.objects[f"{who}_Face"].data.shape_keys.key_blocks
    for k in FACE_KEYS:
        if k in kb:
            kb[k].value = vals.get(k, 0.0)


def s(t, n=1, ph=0.0):
    return math.sin(2 * math.pi * (t * n + ph))


def ease(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


STAND = {"L_UpperArm": [("Y", 72)], "R_UpperArm": [("Y", -72)],
         "L_LowerArm": [("Y", 8), ("X", -18)], "R_LowerArm": [("Y", -8), ("X", -18)],
         "L_Hand": [("X", -6)], "R_Hand": [("X", -6)]}


# ── 掌心朝向：繞前臂軸轉，一半給前臂、一半給手腕 ──
PALM_REST = Vector((0, 0, -1))   # VRoid T 姿勢：掌心朝下


def palm_normal(arm, side):
    pb = arm.pose.bones[f"J_Bip_{side}_Hand"]
    rot = pb.matrix.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()
    return (rot @ PALM_REST).normalized(), pb.matrix.to_3x3().col[1].normalized()


_PALM_LAST = {}


def face_palm(arm, side, target=(0, -1, 0), split=0.5, w=1.0):
    """w：轉動量的比例（0~1，用來平滑淡入淡出）；接近 180 度時沿用上一格的旋轉方向，避免左右翻轉"""
    target = Vector(target)
    bpy.context.view_layer.update()
    n, axis = palm_normal(arm, side)
    def proj(v): return v - axis * v.dot(axis)
    a, b = proj(n), proj(target)
    if a.length < 1e-4 or b.length < 1e-4:
        return 0.0
    a.normalize(); b.normalize()
    ang = math.atan2(axis.dot(a.cross(b)), a.dot(b))
    last = _PALM_LAST.get((arm.name, side))
    if last is not None and abs(ang) > math.radians(120) and (ang > 0) != (last > 0):
        ang -= math.copysign(2 * math.pi, ang)
    _PALM_LAST[(arm.name, side)] = ang
    ang *= w
    for bone, part in ((f"J_Bip_{side}_LowerArm", split), (f"J_Bip_{side}_Hand", 1 - split)):
        pb = arm.pose.bones[bone]
        m = pb.matrix.copy(); h = m.to_translation()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(ang * part, 4, axis) @ Matrix.Translation(-h) @ m
        pb.scale = (1, 1, 1); pb.location = (0, 0, 0); pb.rotation_quaternion.normalize()
        bpy.context.view_layer.update()
    return math.degrees(ang)


def _leg_geom(arm):
    B = arm.data.bones
    hip, knee, ank = (B[f"J_Bip_L_{n}"].head_local for n in ("UpperLeg", "LowerLeg", "Foot"))
    return (knee - hip).length, (ank - knee).length, (ank - hip).length


def leg_bend(arm, drop):
    """骨盆下降 drop（公尺）時，腳掌平貼地面需要的 (大腿, 小腿, 腳踝) 角度"""
    L1, L2, D0 = _leg_geom(arm)
    def ang(D):
        D = max(0.2, min(L1 + L2 - 1e-6, D))
        a = math.acos((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D)); b = math.acos((L2 * L2 + D * D - L1 * L1) / (2 * L2 * D))
        return a, b
    a0, b0 = ang(D0); a, b = ang(D0 - drop)
    da, db = math.degrees(a - a0), math.degrees(b - b0)
    return -da, da + db, -db


_SOLE = {}


def sole_points(arm, who=None):
    """鞋底取樣點：rest 時 z<1.2cm 的鞋子頂點，記成所屬腳骨的局部座標（之後每格用骨頭矩陣換算，不必算網格）"""
    if arm.name in _SOLE:
        return _SOLE[arm.name]
    who = who or WHO
    sh = bpy.data.objects[f"{who}_Shoes"]; names = {g.index: g.name for g in sh.vertex_groups}
    pts = []
    for v in sh.data.vertices:
        if v.co.z > 0.012 or not v.groups:
            continue
        g = max(v.groups, key=lambda g: g.weight); bname = names[g.group]
        if bname not in arm.data.bones:
            continue
        pts.append((bname, arm.data.bones[bname].matrix_local.inverted() @ v.co))
    _SOLE[arm.name] = pts[::3]
    return _SOLE[arm.name]


def sole_min_z(arm):
    bpy.context.view_layer.update()
    mw = arm.matrix_world
    return min((mw @ arm.pose.bones[b].matrix @ co).z for b, co in sole_points(arm))


def foot_sole_min(arm, side):
    """單腳鞋底最低點的世界高度"""
    bpy.context.view_layer.update()
    mw = arm.matrix_world
    return min((mw @ arm.pose.bones[b].matrix @ co).z for b, co in sole_points(arm) if f"_{side}_" in b)


def _aim_child(arm, bone, child, target):
    """繞 bone 的頭部做最小旋轉，讓子骨頭 child 的頭部對準 target（骨架空間）。
    用子骨頭的頭部而不是 bone 的尾端：VRoid 的小腿尾端和腳踝差了幾毫米"""
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone]; h = pb.head.copy()
    cur = arm.pose.bones[child].head - h; want = Vector(target) - h
    if cur.length < 1e-6 or want.length < 1e-6:
        return
    ang = cur.angle(want); ax = cur.cross(want)
    if ang < 1e-7 or ax.length < 1e-9:
        return
    rot_world(arm, bone, ax.normalized(), math.degrees(ang))


def ik_leg(arm, side, ankle_w, pole_w, pitch=0.0, yaw=0.0, toe=0.0):
    """雙骨骼腿 IK（世界座標）：腳踝（Foot 頭部）到 ankle_w、膝蓋朝 pole_w 那一側。
    腳掌維持 rest 的朝向（平貼地面），再加 pitch（腳尖往下為正）、yaw（腳尖往角色左邊轉為正）；toe：腳趾往上翹的角度"""
    bpy.context.view_layer.update()
    inv = arm.matrix_world.inverted()
    W = inv @ Vector(ankle_w); Pp = inv @ Vector(pole_w)
    B = arm.data.bones
    ul, ll, ft, tb = (f"J_Bip_{side}_{n}" for n in ("UpperLeg", "LowerLeg", "Foot", "ToeBase"))
    L1 = (B[ll].head_local - B[ul].head_local).length; L2 = (B[ft].head_local - B[ll].head_local).length
    S = arm.pose.bones[ul].head.copy()
    v = W - S; d = max(1e-4, min(v.length, (L1 + L2) * 0.9999)); dr = v.normalized()
    a = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    pp = Pp - S; pp = pp - dr * pp.dot(dr)
    if pp.length < 1e-6:
        pp = Vector((0, -1, 0)) - dr * dr.y
    pp.normalize()
    E = S + dr * math.cos(a) * L1 + pp * math.sin(a) * L1
    _aim_child(arm, ul, ll, E)
    _aim_child(arm, ll, ft, S + dr * d)
    bpy.context.view_layer.update()
    pb = arm.pose.bones[ft]; h = pb.head.copy()
    R = Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(pitch), 3, "X") @ pb.bone.matrix_local.to_3x3()
    pb.matrix = Matrix.Translation(h) @ R.to_4x4()
    pb.scale = (1, 1, 1); pb.location = (0, 0, 0); pb.rotation_quaternion.normalize()
    if abs(toe) > 1e-3:
        rot_world(arm, tb, "X", -toe)


FOOT_POLE = (0.1, -0.6, 0.35)      # 膝蓋朝向：腳踝目標往前 60 cm、往外 10 cm、往上 35 cm


def plant_feet(arm, feet):
    """腳底鎖定。feet = {"L": (dx, dy, lift, pitch, yaw, toe), "R": ...}，後面的值可省略（預設 0）。
    腳踝鎖在世界座標「rest 站姿的腳踝位置 + (dx, dy)」；lift＝這隻腳鞋底最低點離地多高（0＝踩在地上）。
    在 apply_pose 與整體位移（root）之後做：骨盆怎麼移、怎麼轉，踩著的腳都留在原地；要換位置就抬腳（lift > 0）再放下。"""
    B = arm.data.bones
    for side, spec in feet.items():
        dx, dy, lift, pitch, yaw, toe = (tuple(spec) + (0.0,) * 6)[:6]
        a0 = B[f"J_Bip_{side}_Foot"].head_local
        sg = 1 if side == "L" else -1
        tgt = Vector((a0.x + dx, a0.y + dy, a0.z + lift))
        for _ in range(3):               # 依實際鞋底高度修正腳踝高度（腳尖往下時，最低點從腳跟換到腳尖）
            ik_leg(arm, side, tgt, tgt + Vector((sg * FOOT_POLE[0], FOOT_POLE[1], FOOT_POLE[2])), pitch, yaw, toe)
            err = lift - foot_sole_min(arm, side)
            if abs(err) < 2e-5:
                break
            tgt.z += err


def follow_matrix(arm, key):
    """rest 時的世界座標 → 跟著骨頭 key 目前姿勢移動後的世界座標（給 ik 第 5 欄用）"""
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bn(key)]
    return arm.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted()


def pose_frame(arm, P, who=None):
    """套用一格：姿勢 → 整體位移/旋轉 → 腳底鎖定（feet）→ 貼地（ground，最低的鞋底剛好貼地，再加 hop）→ IK → 前臂扭轉 → 掌心 → 表情。
    貼地要在 IK 之前算，IK 的世界座標目標才不會被之後的整體平移帶走。
    有 feet 時腳的高度由 feet 決定，預設不再貼地（root 的 z＝骨盆下降量，膝蓋由腿 IK 自動彎）"""
    apply_pose(arm, P)
    x, y, z = P.get("root", (0, 0, 0))
    arm.location = (x, y, z); arm.rotation_euler = (0, 0, math.radians(P.get("rz", 0)))
    feet = P.get("feet")
    if feet:
        plant_feet(arm, feet)
    if P.get("ground", not feet):
        arm.location.z = z - sole_min_z(arm) + P.get("hop", 0.0)
    for item in P.get("ik", []):
        if len(item) > 4:                # 第 5 欄：座標寫的是 rest 時的位置，跟著這根骨頭走（例：手貼小腹，彎腰時跟著骨盆）
            M = follow_matrix(arm, item[4])
            item = (item[0],) + tuple(None if p is None else M @ Vector(p) for p in item[1:4])
        ik_arm(arm, *item)
    for side, deg in P.get("twist", []):
        twist_forearm(arm, side, deg)
    for item in P.get("palms", []):
        side, tgt = item[0], item[1]; w = item[2] if len(item) > 2 else 1.0
        if len(item) > 3:                # 第 4 欄 split：前臂分到的比例（0＝只轉手腕，IK 對好的手腕位置不會被甩開）
            face_palm(arm, side, tgt, split=item[3], w=w)
        else:
            face_palm(arm, side, tgt, w=w)
    set_face(P.get("face", {}), who)


def mesh_eval(on, arm_name=None):
    """擺姿勢時關掉網格的骨架變形（只在視窗評估），每轉一根骨頭就不會重算整個網格；渲染用的是 show_render，不受影響"""
    A = bpy.data.objects[arm_name or f"{WHO}_Armature"]
    for o in bpy.data.objects:
        if o.type == "MESH" and o.parent == A:
            for m in o.modifiers:
                if m.type == "ARMATURE":
                    m.show_viewport = on


def twist_forearm(arm, side, deg, split=0.5):
    """繞前臂軸固定轉 deg 度（前臂、手腕各分一半）：比 face_palm 穩定，不會在接近 180 度時翻面"""
    if abs(deg) < 1e-3:
        return
    bpy.context.view_layer.update()
    axis = arm.pose.bones[f"J_Bip_{side}_Hand"].matrix.to_3x3().col[1].normalized()
    for bone, part in ((f"J_Bip_{side}_LowerArm", split), (f"J_Bip_{side}_Hand", 1 - split)):
        pb = arm.pose.bones[bone]
        m = pb.matrix.copy(); h = m.to_translation()
        pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg * part), 4, axis) @ Matrix.Translation(-h) @ m
        pb.scale = (1, 1, 1); pb.location = (0, 0, 0); pb.rotation_quaternion.normalize()
        bpy.context.view_layer.update()


def aim_bone(arm, bone, target_arm):
    """把骨頭（頭→尾）轉向 target（骨架空間座標），用最小旋轉"""
    bpy.context.view_layer.update()
    pb = arm.pose.bones[bone]
    cur = (pb.tail - pb.head).normalized(); want = (Vector(target_arm) - pb.head)
    if want.length < 1e-6:
        return
    want.normalize()
    ang = cur.angle(want)
    if ang < 1e-5:
        return
    ax = cur.cross(want)
    if ax.length < 1e-8:
        return
    rot_world(arm, bone, ax.normalized(), math.degrees(ang))


def ik_arm(arm, side, wrist_w, pole_w, hand_tip_w=None):
    """雙骨骼 IK（世界座標目標）：手腕到 wrist_w，手肘朝 pole_w 那一側；hand_tip_w：手掌（中指方向）指向的點"""
    bpy.context.view_layer.update()
    inv = arm.matrix_world.inverted()
    W = inv @ Vector(wrist_w); Pp = inv @ Vector(pole_w)
    B = arm.data.bones
    ua, la, hd = (f"J_Bip_{side}_{n}" for n in ("UpperArm", "LowerArm", "Hand"))
    L1 = (B[la].head_local - B[ua].head_local).length; L2 = (B[hd].head_local - B[la].head_local).length
    S = arm.pose.bones[ua].head.copy()
    v = W - S; d = max(1e-4, min(v.length, (L1 + L2) * 0.999)); dr = v.normalized()
    a = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    pp = (Pp - S); pp = pp - dr * pp.dot(dr)
    if pp.length < 1e-6:
        pp = Vector((0, 0, -1)) - dr * dr.z
    pp.normalize()
    E = S + dr * math.cos(a) * L1 + pp * math.sin(a) * L1
    aim_bone(arm, ua, E)
    aim_bone(arm, la, S + dr * d)
    if hand_tip_w is not None:
        aim_bone(arm, hd, inv @ Vector(hand_tip_w))
