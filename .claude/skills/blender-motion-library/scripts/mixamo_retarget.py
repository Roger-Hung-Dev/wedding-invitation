# Mixamo（FBX，mixamorig 骨架）→ VRoid 骨架的重新對應（retarget）。2026-10-10 新增。
# 原則（使用者 2026-10-10 指定）：Mixamo 現成動作「原樣」套到角色上 —— 只做骨架對應，不鎖腳、不修手臂、不改速度、不加覆寫層。
# 微調（接觸點、穿模）由情境在這個結果上另外做，不寫在這裡。
#
# 用法（背景或 GUI Blender；FBX 用 Blender 內建匯入器讀，不執行檔案裡的任何東西）：
#     src = read_fbx(r"D:\render-work\mixamo\raw\waving_one_hand.fbx")       # 來源：每格每根骨頭的世界旋轉＋頭部位置
#     tgt = Target(bpy.data.objects["groom_Armature"])                       # 目標 rest 資料
#     clip = retarget(src, tgt)                                              # 每格 {VRoid 骨頭名: 世界旋轉}＋骨盆位置（角色本地座標，見下）
#     seq = Sequence(tgt, [Seg(clip, 0, 37), Seg(clip2, ...)], blend=0.3)   # 多段接起來（位置、朝向接續，接點漸變）
#     pose = seq.at(t)   →  apply_pose(arm, tgt, pose)                       # 寫進 pose bones（matrix_basis）
#
# 座標慣例（和 pose_lib 相同）：角色面向 −Y、左手 +X、Z 朝上，單位 m。yaw 角度：0＝面向 −Y（鏡頭），90＝面向 +X。
#
# 做法：
#   1. 來源 rest＝FBX 骨架的 rest（Mixamo 一律是 T 字、掌心朝下、面向 −Y），和 VRoid 的 rest 一樣是 T 字。
#   2. 每根骨頭：來源「rest → 這一格」的世界旋轉變化量 D 套到目標 rest 上；
#      四肢與手指另外做「方向對齊」A（把目標 rest 的骨頭方向轉到來源 rest 的方向），兩邊 T 字的手臂下垂角、手指角度不同也不會帶進來。
#      軀幹、頭、腳掌、腳趾只套變化量（兩邊 rest 都是直立、平踩）。
#   3. 骨盆位移 × 腿長比例（目標髖關節高 ÷ 來源髖關節高）。不鎖腳：腳會不會滑、會不會陷地，照 Mixamo 原樣。
import bpy, math
from mathutils import Vector, Quaternion, Matrix

_FING = (("Thumb", "Thumb"), ("Index", "Index"), ("Middle", "Middle"), ("Ring", "Ring"), ("Little", "Pinky"))
MAP = {"J_Bip_C_Hips": "Hips", "J_Bip_C_Spine": "Spine", "J_Bip_C_Chest": "Spine1", "J_Bip_C_UpperChest": "Spine2",
       "J_Bip_C_Neck": "Neck", "J_Bip_C_Head": "Head"}
for _s, _S in (("L", "Left"), ("R", "Right")):
    MAP.update({f"J_Bip_{_s}_Shoulder": f"{_S}Shoulder", f"J_Bip_{_s}_UpperArm": f"{_S}Arm",
                f"J_Bip_{_s}_LowerArm": f"{_S}ForeArm", f"J_Bip_{_s}_Hand": f"{_S}Hand",
                f"J_Bip_{_s}_UpperLeg": f"{_S}UpLeg", f"J_Bip_{_s}_LowerLeg": f"{_S}Leg",
                f"J_Bip_{_s}_Foot": f"{_S}Foot", f"J_Bip_{_s}_ToeBase": f"{_S}ToeBase"})
    for _v, _m in _FING:
        for _i in (1, 2, 3):
            MAP[f"J_Bip_{_s}_{_v}{_i}"] = f"{_S}Hand{_m}{_i}"
# 方向對齊：目標骨頭 → (目標方向的終點骨頭, 來源方向的終點骨頭)；終點 None＝用該骨頭自己的 tail
_ALIGN = {}
for _s, _S in (("L", "Left"), ("R", "Right")):
    _ALIGN.update({f"J_Bip_{_s}_Shoulder": (f"J_Bip_{_s}_UpperArm", f"{_S}Arm"),
                   f"J_Bip_{_s}_UpperArm": (f"J_Bip_{_s}_LowerArm", f"{_S}ForeArm"),
                   f"J_Bip_{_s}_LowerArm": (f"J_Bip_{_s}_Hand", f"{_S}Hand"),
                   f"J_Bip_{_s}_Hand": (f"J_Bip_{_s}_Middle1", f"{_S}HandMiddle1"),
                   f"J_Bip_{_s}_UpperLeg": (f"J_Bip_{_s}_LowerLeg", f"{_S}Leg"),
                   f"J_Bip_{_s}_LowerLeg": (f"J_Bip_{_s}_Foot", f"{_S}Foot")})
    for _v, _m in _FING:
        _ALIGN[f"J_Bip_{_s}_{_v}1"] = (f"J_Bip_{_s}_{_v}2", f"{_S}Hand{_m}2")
        _ALIGN[f"J_Bip_{_s}_{_v}2"] = (f"J_Bip_{_s}_{_v}3", f"{_S}Hand{_m}3")
        _ALIGN[f"J_Bip_{_s}_{_v}3"] = (None, f"{_S}Hand{_m}4")


def _qbetween(a, b):
    a = a.normalized(); b = b.normalized()
    return a.rotation_difference(b)


def _yaw_of(left_vec):
    """左手方向（水平）→ 面向的 yaw（0＝面向 −Y：左手朝 +X）"""
    return math.atan2(left_vec.y, left_vec.x)


def read_fbx(path):
    """匯入 Mixamo FBX → dict(fps, n, rest_q, rest_h, Q[f], H[f])（骨頭名去掉 mixamorig: 前綴；位置單位 m），讀完刪掉匯入的物件"""
    before = set(bpy.data.objects); acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False, use_anim=True)
    new = [o for o in bpy.data.objects if o not in before]
    src = next(o for o in new if o.type == "ARMATURE")
    sc = bpy.context.scene; keep = sc.frame_current
    act = src.animation_data.action
    f0, f1 = (int(round(x)) for x in act.frame_range)
    names = [b.name for b in src.data.bones]
    short = {n: n.split(":", 1)[-1] for n in names}
    Mw = src.matrix_world.copy()
    rest_q = {short[n]: (Mw @ src.data.bones[n].matrix_local).to_3x3().normalized().to_quaternion() for n in names}
    rest_h = {short[n]: Mw @ src.data.bones[n].head_local for n in names}
    Q = []; H = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        q = {}; h = {}
        for n in names:
            M = Mw @ src.pose.bones[n].matrix
            q[short[n]] = M.to_3x3().normalized().to_quaternion(); h[short[n]] = M.to_translation()
        Q.append(q); H.append(h)
    sc.frame_set(keep)
    for o in new:
        data = o.data
        bpy.data.objects.remove(o)
        if data is not None and getattr(data, "users", 1) == 0:
            if isinstance(data, bpy.types.Armature):
                bpy.data.armatures.remove(data)
            elif isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
    for a in set(bpy.data.actions) - acts_before:
        bpy.data.actions.remove(a)
    fps = sc.render.fps / sc.render.fps_base
    return dict(path=path, fps=30.0, n=len(Q), rest_q=rest_q, rest_h=rest_h, Q=Q, H=H)


class Target:
    """目標骨架（VRoid）的 rest 資料：armature 空間"""
    def __init__(self, arm):
        self.arm = arm
        B = arm.data.bones
        self.keys = [b.name for b in B if b.name in MAP]          # 照骨架階層順序（父在前）
        self.rest = {n: B[n].matrix_local.copy() for n in self.keys}
        self.rest_q = {n: self.rest[n].to_quaternion() for n in self.keys}
        self.rest_h = {n: B[n].head_local.copy() for n in self.keys}
        self.rest_t = {n: B[n].tail_local.copy() for n in self.keys}
        self.parent = {}
        for n in self.keys:
            p = B[n].parent
            while p is not None and p.name not in MAP:
                p = p.parent
            self.parent[n] = p.name if p is not None else None
        self.hip_h = 0.5 * (self.rest_h["J_Bip_L_UpperLeg"].z + self.rest_h["J_Bip_R_UpperLeg"].z)
        # 拇指尖壓到手指時離那節骨頭多遠（m）。角色可在骨架物件上設自訂屬性 thumb_contact（2026-10-12 ZEPETO 身體：手指較粗，
        #   照 VRoid 的 12 mm 會壓進 2.5 mm）；沒設就是原本的 12 mm，VRoid 角色不受影響
        self.thumb_contact = float(arm.get("thumb_contact", 0.012))
        # 這副骨架專用的手勢微調（骨架物件自訂屬性 gesture_overrides＝JSON 字串，{手勢名: {curl/spread/thumb_to}}）：
        #   2026-10-12 ZEPETO 身體手指較粗，共用的 thumbs_up 指尖會壓進掌心 2.8 mm → 身體自己帶一組；沒設就照共用 GESTURE
        import json as _json
        try:
            self.gesture_overrides = _json.loads(arm.get("gesture_overrides", "{}"))
        except Exception:
            self.gesture_overrides = {}

    def fk(self, R, hips):
        """R：{骨頭: 世界旋轉}；hips：骨盆頭部位置 → {骨頭: 頭部位置}"""
        Hd = {}
        for n in self.keys:
            p = self.parent[n]
            Hd[n] = hips.copy() if p is None else Hd[p] + (R[p] @ self.rest_q[p].inverted()) @ (self.rest_h[n] - self.rest_h[p])
        return Hd

    def tail(self, R, Hd, n):
        return Hd[n] + (R[n] @ self.rest_q[n].inverted()) @ (self.rest_t[n] - self.rest_h[n])


def retarget(src, tgt):
    """→ clip：dict(n, fps, R[f]={骨頭: 世界旋轉}, hips[f]=骨盆位置, yaw[f]=面向角)。
    角色本地座標：來源原樣（Mixamo 第 0 格不一定在原點，Sequence 會再對齊）"""
    rq, rh = src["rest_q"], src["rest_h"]
    # 來源 rest 面向：左手方向（LeftUpLeg − RightUpLeg）轉到 +X
    lv = rh["LeftUpLeg"] - rh["RightUpLeg"]; lv.z = 0
    Rg = Quaternion((0, 0, 1), -_yaw_of(lv))
    A = {}
    for n in tgt.keys:
        if n in _ALIGN:
            tn, sn = _ALIGN[n]; s0 = MAP[n]
            if sn not in rh:
                A[n] = Quaternion(); continue
            sd = Rg @ (rh[sn] - rh[s0])
            td = (tgt.rest_h[tn] if tn else tgt.rest_t[n]) - tgt.rest_h[n]
            A[n] = _qbetween(td, sd)
        else:
            A[n] = Quaternion()
    leg_s = 0.5 * ((rh["LeftUpLeg"]).z + (rh["RightUpLeg"]).z) - min(rh["LeftToeBase"].z, rh["RightToeBase"].z, rh["LeftFoot"].z, rh["RightFoot"].z)
    leg_t = tgt.hip_h
    s = leg_t / leg_s
    h0 = rh["Hips"]
    Rs = []; hips = []; yaw = []
    for f in range(src["n"]):
        Qf, Hf = src["Q"][f], src["H"][f]
        R = {}
        for n in tgt.keys:
            sn = MAP[n]
            D = (Rg @ Qf[sn]) @ (Rg @ rq[sn]).inverted()
            # A＝把目標 rest 骨頭方向轉到來源 rest 方向，所以是先 A 再套來源的變化量 D。
            # 2026-10-11 修正：之前寫成 A⁻¹，會把兩副骨架的 rest 方向差多加一次（不是抵消）——
            #   VRoid 角色拇指每格多轉約 26°、肩胛 13°、手腕 6.6°；ZEPETO 身體手指張成扇形（小指往旁邊 15° 變 62°）。
            #   改後手指角度和 Mixamo 原樣一致（D:\render-work\zepeto-body\scripts\finger_compare.py 驗證）。
            R[n] = D @ A[n] @ tgt.rest_q[n]
        Rs.append(R)
        hp = Rg @ (Hf["Hips"] - h0) * s
        hips.append(tgt.rest_h["J_Bip_C_Hips"] + hp)
        l = Rg @ (Hf["LeftUpLeg"] - Hf["RightUpLeg"]); l.z = 0
        yaw.append(_yaw_of(l))
    return dict(n=src["n"], fps=src["fps"], R=Rs, hips=hips, yaw=yaw, scale=s, path=src.get("path"))


# ════════ 套用後的微調（使用者 2026-10-10 同意：接觸點、手勢可以微調，但不破壞動作結構）════════
# R 是每根骨頭各自的世界旋轉（不會自動跟著父骨頭轉），所以轉一根骨頭時要連它底下整串一起轉（rotate_subtree）。
def _children(tgt):
    if not hasattr(tgt, "_kids"):
        tgt._kids = {n: [m for m in tgt.keys if tgt.parent[m] == n] for n in tgt.keys}
    return tgt._kids


def subtree(tgt, n):
    out = [n]; k = 0
    while k < len(out):
        out += _children(tgt)[out[k]]; k += 1
    return out


def rotate_subtree(tgt, R, n, q):
    """骨頭 n 和它底下所有骨頭的世界旋轉都左乘 q（繞 n 的頭部轉；位置由 fk 重算）"""
    R = dict(R)
    for m in subtree(tgt, n):
        R[m] = q @ R[m]
    return R


def _dir(tgt, R, Hd, n, child=None):
    return ((Hd[child] if child else tgt.tail(R, Hd, n)) - Hd[n]).normalized()


def arm_ik(tgt, R, hips, side, wrist, pole):
    """兩節手臂 IK：手腕到 wrist（世界座標），手肘往 pole 方向彎；手掌、手指跟著前臂一起轉（相對前臂不變）"""
    s = side
    U, L, H = f"J_Bip_{s}_UpperArm", f"J_Bip_{s}_LowerArm", f"J_Bip_{s}_Hand"
    Hd = tgt.fk(R, hips)
    S = Hd[U]; a = (tgt.rest_h[L] - tgt.rest_h[U]).length; b = (tgt.rest_h[H] - tgt.rest_h[L]).length
    v = wrist - S; d = max(1e-4, min(v.length, (a + b) * 0.999)); dn = v.normalized()
    ca = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d)))
    p = pole - dn * pole.dot(dn)
    # 2026-10-11 第 3 關自我審查：手經過肩膀附近時 pole 幾乎和手臂同方向，p 很小、方向一格就翻面（⑤ 路人甲手肘一格跳 37 cm）
    #   → p 不夠明確時，加上目前手肘所在的方向當依據（和上一個姿勢連續）
    ce = Hd[L] - S; ce = ce - dn * ce.dot(dn)
    lim = 0.35 * max(1e-6, pole.length)
    if p.length < lim and ce.length > 1e-6:
        p = p + ce.normalized() * (lim - p.length)
    p = p.normalized() if p.length > 1e-6 else Vector((0, 0, 1))
    E = S + (dn * ca + p * math.sqrt(max(0.0, 1 - ca * ca))) * a
    R = rotate_subtree(tgt, R, U, (Hd[L] - S).rotation_difference(E - S))
    Hd = tgt.fk(R, hips)
    T = S + dn * d
    R = rotate_subtree(tgt, R, L, (Hd[H] - Hd[L]).rotation_difference(T - Hd[L]))
    return fix_arm_twist(tgt, R, hips, s)


def _twist_about(tgt, R, parent, child, ax=None):
    """child 相對 parent 的扭轉角（度）：兩根骨頭各自「相對 rest 的轉動」相除，拆成擺動＋繞 child rest 骨頭方向的扭轉，取扭轉
    （swing-twist 拆法；手臂舉到垂直時也穩定。ax 參數保留相容，不用）"""
    dp = R[parent] @ tgt.rest_q[parent].inverted(); dc = R[child] @ tgt.rest_q[child].inverted()
    q = dp.inverted() @ dc
    kids = [n for n, p in tgt.parent.items() if p == child] if hasattr(tgt, "parent") else []
    tip = tgt.rest_t.get(child) if hasattr(tgt, "rest_t") and tgt.rest_t.get(child) is not None else None
    if tip is None and kids:
        tip = tgt.rest_h[kids[0]]
    a = (tip - tgt.rest_h[child]).normalized() if tip is not None else Vector((1, 0, 0))
    v = Vector((q.x, q.y, q.z)); pr = a * v.dot(a)
    tw = Quaternion((q.w, pr.x, pr.y, pr.z))
    if tw.magnitude < 1e-9:
        return 0.0
    tw.normalize()
    ang = 2.0 * math.atan2(Vector((tw.x, tw.y, tw.z)).dot(a), tw.w)
    return (math.degrees(ang) + 180.0) % 360.0 - 180.0


def fix_arm_twist(tgt, R, hips, side):
    """手臂扭轉校正（2026-10-11 第 3 關自我審查：IK 用最小轉動擺上臂，上臂繞自己的軸轉多少沒管，⑧ 新娘右手肘相對上臂變成往後折）：
    1) 上臂繞自己的軸轉，讓上臂的「正前方」（rest −Y）對準手肘彎的方向——手肘才是正常往前折（手肘幾乎打直時不動）；
    2) 前臂繞自己的軸轉，把「手肘處」和「手腕處」的扭轉平均分掉，不會某一處扭成麻花。
    兩步都只轉那一根骨頭、繞它自己的軸，所以手肘、手腕、手的位置和手掌方向都不變"""
    U, L, H = f"J_Bip_{side}_UpperArm", f"J_Bip_{side}_LowerArm", f"J_Bip_{side}_Hand"
    Hd = tgt.fk(R, hips)
    u = (Hd[L] - Hd[U]); fa = (Hd[H] - Hd[L])
    if u.length < 1e-6 or fa.length < 1e-6:
        return R
    u.normalize(); fa.normalize()
    R = dict(R)
    bend = u.angle(fa)
    if bend > math.radians(12):
        front = (R[U] @ tgt.rest_q[U].inverted()) @ Vector((0, -1, 0))
        fr = front - u * front.dot(u); fp = fa - u * fa.dot(u)
        if fr.length > 1e-6 and fp.length > 1e-6:
            fr.normalize(); fp.normalize()
            th = math.atan2(u.dot(fr.cross(fp)), fr.dot(fp))
            R[U] = Quaternion(u, th) @ R[U]
    te = _twist_about(tgt, R, U, L, fa); tw = _twist_about(tgt, R, L, H, fa)
    tot = (te + tw + 180.0) % 360.0 - 180.0             # 上臂到手掌的總扭轉（繞一圈的要折回來，不然會分成兩個 ±136°）
    d = (tot * 0.5 - te + 180.0) % 360.0 - 180.0
    if abs(d) > 0.5:
        R[L] = Quaternion(fa, math.radians(d)) @ R[L]
    return R


def aim_hand(tgt, R, hips, side, direction, palm=None, palm_w=1.0, max_bend=85.0):
    """手掌（手腕→中指根）轉到 direction；palm 給的話再繞手掌軸轉，讓掌心朝 palm（VRoid rest 掌心朝 −Z）。
    2026-10-11 第 3 關自我審查加的兩個保護：
      palm_w＝掌心轉過去的權重（0～1，平順轉；以前各幕寫「權重過一半才給 palm」，掌心會在那一格突然翻過去）；
      max_bend＝手腕最多彎幾度（手掌方向和前臂方向的夾角；⑤ 舉手機時手掌被硬轉朝上、手腕往後折 133°）"""
    H, M, L = f"J_Bip_{side}_Hand", f"J_Bip_{side}_Middle1", f"J_Bip_{side}_LowerArm"
    Hd = tgt.fk(R, hips)
    cur = (Hd[M] - Hd[H]).normalized(); want = direction.normalized()
    fa = (Hd[H] - Hd[L]).normalized()
    if max_bend is not None and fa.angle(want) > math.radians(max_bend):
        ax = fa.cross(want)
        if ax.length > 1e-6:
            want = Quaternion(ax.normalized(), math.radians(max_bend)) @ fa
    R = rotate_subtree(tgt, R, H, cur.rotation_difference(want))
    if palm is not None and palm_w > 1e-3:
        n = (R[H] @ tgt.rest_q[H].inverted()) @ Vector((0, 0, -1))
        n = n - want * n.dot(want); w = palm - want * palm.dot(want)
        if n.length > 1e-6 and w.length > 1e-6:
            q = n.normalized().rotation_difference(w.normalized())
            R = rotate_subtree(tgt, R, H, Quaternion().slerp(q, max(0.0, min(1.0, palm_w))))
    return fix_arm_twist(tgt, R, hips, side)


def breathe(tgt, R, hips, t, w=1.0, period=3.6, deg=1.6, phase=0.0):
    """呼吸（2026-10-11 第 3 關自我審查「⑤ 新郎擺拍 1.5 秒全身完全不動，像定格」）：胸口每 period 秒起伏一次——
    脊椎繞身體左右軸往後仰 deg°（吸氣）再回來，脖子反向轉 60% 讓頭大致保持水平。手臂跟著胸口一起動（很小）"""
    if w <= 0:
        return R
    Hd = tgt.fk(R, hips)
    lft = Hd["J_Bip_L_UpperLeg"] - Hd["J_Bip_R_UpperLeg"]; lft.z = 0
    if lft.length < 1e-6:
        return R
    lft.normalize()
    a = math.radians(deg) * w * 0.5 * (1 - math.cos(2 * math.pi * (t / period + phase)))
    R = rotate_subtree(tgt, R, "J_Bip_C_Spine", Quaternion(lft, a))
    return rotate_subtree(tgt, R, "J_Bip_C_Neck", Quaternion(lft, -a * 0.6))


def lift_shoulder(tgt, R, side, deg):
    """肩胛（Shoulder）往上抬 deg 度（整隻手臂跟著）：手舉過頭時肩膀要跟著抬，不然肩膀會塌下去（⑧ 第 3 輪的教訓）"""
    n = f"J_Bip_{side}_Shoulder"
    axis = Vector((0, -1, 0)) if side == "L" else Vector((0, 1, 0))        # 左肩（朝 +X）繞 −Y 往上、右肩繞 +Y
    return rotate_subtree(tgt, R, n, Quaternion(axis, math.radians(deg)))


def _yaw_axis_angle(a, b):
    """水平面上從 a 轉到 b 的角度（弧度，繞 +Z，逆時針為正）"""
    return math.atan2(a.x * b.y - a.y * b.x, a.x * b.x + a.y * b.y)


def look_at(tgt, R, hips, target, w=1.0, split=(0.15, 0.25, 0.60), max_yaw=75.0, pitch=0.7):
    """頭轉向 target（世界座標）：水平轉角分給腰（Spine）、上胸（UpperChest）、脖子（Neck）＝ split；
    上下（pitch）只給脖子和頭。w＝權重 0～1（漸入漸出用）。VRoid 頭 rest 面向 −Y"""
    if w <= 0:
        return R
    Hd = tgt.fk(R, hips)
    hn = "J_Bip_C_Head"
    eye = Hd[hn] + Vector((0, 0, 0.08))
    fwd = (R[hn] @ tgt.rest_q[hn].inverted()) @ Vector((0, -1, 0))
    want = target - eye
    f2 = Vector((fwd.x, fwd.y, 0)); w2 = Vector((want.x, want.y, 0))
    if f2.length < 1e-6 or w2.length < 1e-6:
        return R
    d = max(-math.radians(max_yaw), min(math.radians(max_yaw), _yaw_axis_angle(f2, w2))) * w
    for n, k in zip(("J_Bip_C_Spine", "J_Bip_C_UpperChest", "J_Bip_C_Neck"), split):
        if n in R:
            R = rotate_subtree(tgt, R, n, Quaternion((0, 0, 1), d * k))
    if pitch:
        Hd = tgt.fk(R, hips)
        fwd = (R[hn] @ tgt.rest_q[hn].inverted()) @ Vector((0, -1, 0))
        want = target - (Hd[hn] + Vector((0, 0, 0.08)))
        e_now = math.atan2(fwd.z, Vector((fwd.x, fwd.y)).length); e_want = math.atan2(want.z, Vector((want.x, want.y)).length)
        side = Vector((fwd.y, -fwd.x, 0)).normalized()            # 頭的右手邊（水平）；繞它轉正角度＝抬頭
        dp = (e_want - e_now) * w * pitch
        # 2026-10-11 修正：之前正負號反了（要往下看反而抬頭，⑤⑦ 第 3 關回饋「頭的位置異常」）。lookat_test.py 驗證
        R = rotate_subtree(tgt, R, "J_Bip_C_Neck", Quaternion(side, dp * 0.4))
        R = rotate_subtree(tgt, R, hn, Quaternion(side, dp * 0.6))
    return R


_FINGERS = ("Thumb", "Index", "Middle", "Ring", "Little")
THUMB_SIGN = -1.0


def finger_pose(tgt, R, side, curl, spread=None, w=1.0, thumb_to=None):
    """手指擺成指定彎度（相對手掌，取代原本的手指動作）：curl＝{手指: (第1節, 第2節, 第3節) 度}，彎向掌心；
    spread＝{手指: 度}，往拇指側張開為正；thumb_to＝拇指尖要壓到的位置（例 "Ring2"＝無名指第 2 節），
    拇指先照 curl 彎、再整串轉過去對準（拇指要橫過掌心，單純彎曲到不了）。沒列的手指保持原樣。w＝和原本手指姿勢之間的權重。
    VRoid rest：手指沿 ±X、掌心朝 −Z"""
    sg = 1.0 if side == "L" else -1.0
    H = f"J_Bip_{side}_Hand"
    Mh = R[H] @ tgt.rest_q[H].inverted()
    out = dict(R)
    palm_n = Vector((0, 0, -1))
    acc_all = {}                                          # 每節相對手掌的旋轉（rest 空間）
    for fn in _FINGERS:
        if fn not in curl:
            continue
        names = [f"J_Bip_{side}_{fn}{i}" for i in (1, 2, 3)]
        if fn == "Thumb":
            d = (tgt.rest_h[names[1]] - tgt.rest_h[names[0]]).normalized()
            axis_r = d.cross(palm_n).normalized() * THUMB_SIGN
            axis_s = palm_n
        else:
            axis_r = Vector((0, sg, 0))                      # 左手繞 +Y、右手繞 −Y：指尖往 −Z（掌心）彎
            axis_s = Vector((0, 0, -sg))                     # 張開（往拇指側為正）：食指在中指的 −Y 側（rest 掌心朝下時）
        acc = Quaternion()
        if spread and fn in spread:
            acc = Quaternion(axis_s, math.radians(spread[fn]))
        for n, deg in zip(names, curl[fn]):
            acc = acc @ Quaternion(axis_r, math.radians(deg))
            acc_all[n] = acc.copy()

    def rest_pos(n):                                      # 彎好之後這一節頭部的位置（rest 空間，相對手掌）
        f_, i = n.rsplit("_", 1)[1][:-1], int(n[-1])
        base = f"J_Bip_{side}_{f_}1"
        p = tgt.rest_h[base].copy()
        for k in range(1, i):
            a_, b_ = f"J_Bip_{side}_{f_}{k}", f"J_Bip_{side}_{f_}{k + 1}"
            p += acc_all.get(a_, Quaternion()) @ (tgt.rest_h[b_] - tgt.rest_h[a_])
        return p

    if thumb_to and f"J_Bip_{side}_Thumb1" in acc_all:
        t1, t3 = f"J_Bip_{side}_Thumb1", f"J_Bip_{side}_Thumb3"
        tip = rest_pos(t3) + acc_all[t3] @ (tgt.rest_t[t3] - tgt.rest_h[t3])
        goal = rest_pos(f"J_Bip_{side}_{thumb_to}") + Vector((0, 0, -getattr(tgt, "thumb_contact", 0.012)))   # 壓在那節的手背側上方一點（掌心朝下時是 −Z 側）
        q = (tip - tgt.rest_h[t1]).rotation_difference(goal - tgt.rest_h[t1])
        for n in (t1, f"J_Bip_{side}_Thumb2", t3):
            acc_all[n] = q @ acc_all[n]
    for n, acc in acc_all.items():
        q = Mh @ acc @ tgt.rest_q[n]
        out[n] = R[n].slerp(q, w) if w < 1 else q
    return out


# 比讚的拇指（第 1、2、3 節彎度＋張開）。2026-10-11 /fix-animation「大拇指變得纖細又長，不像大拇指」：原本 (−15, −5, 0) 張 25°，
#   整根（連手掌裡的第 1 節）往外撐又反扳 15°，拇指高出拳頭 5.7 cm、根部皮膚被拉細 → 根部貼著拳頭側面、只有前兩節豎起、指尖微彎
THUMB_UP_T = (30.0, -2.0, 18.0, 6.0)

# 常用手勢（度數；第 1、2、3 節）
GESTURE = {
    "peace": dict(curl={"Index": (0, 0, 0), "Middle": (0, 0, 0), "Ring": (80, 95, 60), "Little": (80, 95, 60), "Thumb": (0, 20, 20)},
                  spread={"Index": 9, "Middle": -9}, thumb_to="Ring2"),
    "fist": dict(curl={f: (80, 95, 60) for f in ("Index", "Middle", "Ring", "Little")} | {"Thumb": (30, 35, 30)}),
    "grip": dict(curl={f: (45, 60, 40) for f in ("Index", "Middle", "Ring", "Little")} | {"Thumb": (20, 25, 15)}),
    "flat": dict(curl={f: (0, 5, 5) for f in ("Index", "Middle", "Ring", "Little")} | {"Thumb": (0, 5, 5)}),
    # 自然下垂的手（2026-10-11，⑤ 第 3 關回饋「新郎的手變異常」：Mixamo 原片的手指套到 VRoid 上變成食指往前伸、拇指翹開）：
    # 四指由食指到小指越來越彎、拇指輕靠食指側
    "relaxed": dict(curl={"Index": (12, 22, 14), "Middle": (18, 28, 18), "Ring": (24, 34, 22), "Little": (30, 40, 26),
                          "Thumb": (8, 14, 10)}, spread={"Index": 2, "Middle": 0, "Ring": -2, "Little": -4}, thumb_to="Index2"),
    # 拿細的東西（叉子柄、酒杯腳）（2026-10-11，⑦ 第 3 關第 2 輪自我審查：用 grip 拿叉子、杯子時拇指直直翹起來，像在比讚）：
    # 四指由食指到小指越來越彎，拇指彎過來靠在食指第 2 節旁
    "hold": dict(curl={"Index": (30, 40, 25), "Middle": (45, 55, 35), "Ring": (55, 65, 40), "Little": (60, 70, 45), "Thumb": (12, 22, 16)},
                 spread={"Index": 2, "Middle": 0, "Ring": -2, "Little": -4}, thumb_to="Index2"),
    # 手掌貼著圓的東西（2026-10-11，⑤ 第 3 關第 2 輪回饋「摸頭的手居然還會比 1，應該是手掌摸頭」）：四指併攏、平均微彎，貼著頭髮的弧度
    "cup": dict(curl={"Index": (18, 22, 12), "Middle": (20, 24, 12), "Ring": (22, 26, 14), "Little": (24, 28, 16), "Thumb": (6, 10, 8)},
                spread={"Index": 1, "Middle": 0, "Ring": -1, "Little": -2}),
    # 比讚（2026-10-11，⑦a「新娘吃得很開心」：Mixamo「Sitting Thumbs Up」的手指套到 VRoid 會跑掉，手指改用這組）：
    # 四指握緊成拳、拇指伸直往外翹（不壓在食指上）
    # 2026-10-11 /fix-animation「其餘四指彎曲不多，要類似握拳」：(85,100,60) 指尖沒收進掌心 → 握緊、指尖壓進掌心
    "thumbs_up": dict(curl={"Index": (95, 112, 78), "Middle": (98, 112, 78), "Ring": (98, 112, 78), "Little": (95, 112, 78),
                            "Thumb": (THUMB_UP_T[0], THUMB_UP_T[1], THUMB_UP_T[2])},
                      spread={"Index": 0, "Middle": 0, "Ring": -2, "Little": -4, "Thumb": THUMB_UP_T[3]}),
    # 握叉子（西餐握法）（2026-10-11，⑦a 第 3 關第 12 輪回饋「手沒有握著叉子，叉子穿過手像是手指的一部分」：hold 只是鬆鬆微彎，
    # 叉子從指縫穿過去）：食指幾乎伸直壓在叉柄上、拇指靠在食指第 2 節旁夾住側面、中指到小指彎起來包住叉柄
    "fork_grip": dict(curl={"Index": (10, 14, 8), "Middle": (55, 70, 45), "Ring": (68, 82, 52), "Little": (74, 88, 58), "Thumb": (12, 22, 16)},
                      spread={"Index": 0, "Middle": -2, "Ring": -4, "Little": -6}, thumb_to="Index2"),
}


def gesture(tgt, R, side, name, w=1.0):
    g = dict(GESTURE[name])
    g.update(getattr(tgt, "gesture_overrides", {}).get(name, {}))
    return finger_pose(tgt, R, side, g["curl"], g.get("spread"), w, g.get("thumb_to"))


def _mirror_name(n):
    return n.replace("_L_", "_#_").replace("_R_", "_L_").replace("_#_", "_R_")


def mirror_clip(clip, tgt):
    """左右鏡射（等同 Mixamo 下載選項的 Mirror）：例如右手拿杯子的動畫改成左手拿。動作本身不變。
    做法：每根骨頭相對 rest 的世界變化量 W＝R·rest⁻¹ 對 X＝0 平面鏡射（四元數 (w,x,y,z)→(w,x,−y,−z)），
    換到左右對稱的那根骨頭上，再乘回那根骨頭的 rest；骨盆 x 取負、面向取負。VRoid 骨架左右對稱，所以關節位置剛好鏡射"""
    Rs = []; hips = []
    cx = tgt.rest_h["J_Bip_C_Hips"].x
    for f in range(clip["n"]):
        R = clip["R"][f]; out = {}
        for n in tgt.keys:
            W = R[n] @ tgt.rest_q[n].inverted()
            Wm = Quaternion((W.w, W.x, -W.y, -W.z))
            m = _mirror_name(n)
            out[m] = Wm @ tgt.rest_q[m]
        Rs.append(out)
        h = clip["hips"][f]
        hips.append(Vector((2 * cx - h.x, h.y, h.z)))
    return dict(clip, R=Rs, hips=hips, yaw=[-y for y in clip["yaw"]], mirrored=True)


def splice_clip(clip, spans, xfade=0.3, pin=False):
    """把同一支動畫的幾段依序接成一支新的動畫（剪掉不要的段落、把剩下的接成循環）。
    spans＝[(a 秒, b 秒[, 這段接進來的漸變秒數]), …]：每段的頭和前一段的尾巴重疊漸變（預設 xfade 秒）；
    後一段整段繞 Z 轉＋水平平移，讓重疊開始那格的骨盆水平位置、面向和前一段對齊（原地的動作才不會一段一段跳位）。
    剪接點要挑兩邊姿勢像的格子（tools/loop_probe.py），漸變的中點放在剪接點上：前一段多播 xfade/2、後一段提早 xfade/2。
    原片本來就接得起來的地方（循環動畫的最後一格＝第一格）漸變給 1 格：前一段播到最後一格、下一段從第 0 格起；
    漸變給長了會把前後兩段的動作疊在一起、等於壓快（② 第一版給 0.1 秒，手速從 2.3 衝到 5 m/s）。
    pin＝True：扣掉整支從頭到尾累積的水平位移（平均分攤到每一格），原地的舞步接成循環後才不會每圈往同一邊漂（腳會跟著滑，每秒幾公分）。
    2026-10-11 第 3 關第 3 輪回饋 ②「移除最後敬禮，轉場進來就跳舞到下一次轉場」：Booty Hip Hop 剪掉 2.4～4.4 秒
    手放胸前、往前走 1.3 m 那段，剩下的原地舞步接成循環"""
    fps = clip["fps"]
    R, H, Y = [], [], []
    for sp in spans:
        a, b = sp[0], sp[1]
        X = max(1, int(round((sp[2] if len(sp) > 2 else xfade) * fps)))
        fa = int(round(a * fps)); fb = min(clip["n"] - 1, int(round(b * fps)))
        idx = list(range(fa, fb + 1))
        if not R:
            R = [clip["R"][i] for i in idx]; H = [clip["hips"][i].copy() for i in idx]; Y = [clip["yaw"][i] for i in idx]
            continue
        X = min(X, len(idx) - 1, len(R) - 1)
        k0 = len(R) - X                                           # 重疊從輸出的第 k0 格開始
        dy = _wrap(Y[k0] - clip["yaw"][idx[0]])
        q = Quaternion((0, 0, 1), dy)
        off = H[k0] - q @ clip["hips"][idx[0]]; off.z = 0.0
        sR = [{n: q @ r for n, r in clip["R"][i].items()} for i in idx]
        sH = [q @ clip["hips"][i] + off for i in idx]
        sY = [clip["yaw"][i] + dy for i in idx]
        for j in range(X):
            w = _smooth((j + 1) / (X + 1)); k = k0 + j
            R[k] = {n: R[k][n].slerp(sR[j][n], w) for n in R[k]}
            H[k] = H[k].lerp(sH[j], w)
            Y[k] = Y[k] + _wrap(sY[j] - Y[k]) * w
        R += sR[X:]; H += sH[X:]; Y += sY[X:]
    if pin and len(H) > 1:
        d = H[-1] - H[0]; d.z = 0.0
        H = [h - d * (k / (len(H) - 1)) for k, h in enumerate(H)]
    return dict(clip, n=len(R), R=R, hips=H, yaw=Y, spliced=[tuple(s) for s in spans])


class Seg:
    """一段：clip 的第 a～b 格（含頭尾）。hold＝b 之後停在最後一格的秒數；
    at＝這段在場景裡的開始秒數（None＝接在前一段結束前 blend 秒；比那個晚的話，前一段停在最後一格等）"""
    def __init__(self, clip, a=0, b=None, hold=0.0, name="", at=None, loops=None, face=None, dz=0.0, mod=None, add=False):
        """loops：循環動作（走路）重複幾次（可以是小數）：每圈骨盆往前接上一圈的位移，圈與圈之間不漸變（循環動作頭尾本來就接得起來）；
        face：這段開頭的面向（度，場景座標；0＝面向鏡頭），None＝接前一段的面向；
        dz：這段整條上下平移（公尺）。只用來配合場景的椅面、台階高度（Mixamo 各支坐姿動畫的原椅高不同），動作本身不變；
        mod：套用後的微調 fn(段內秒數, R, hips) → R（例：手臂 IK 比愛心）。在這段自己的座標裡算，之後才接到場景；
        add：只取這段「相對自己第一格的變化」（轉向、腳步、身體晃動），疊到前後兩段的姿勢上（加法動作，見 _additive）。
          2026-10-11 第 3 關第 2 輪回饋：Mixamo 的轉身（Quick 90 Degree Right Turn）整段是運動員的預備站姿——膝蓋一直彎 27～39°、
          手肘彎著垂在兩側，接在站直、揮手之間會先「微蹲、雙手垂下」再轉。add=True 時身體和手臂沿用前一段的結尾、慢慢換成下一段的開頭，
          轉身只留腳步和轉向"""
        self.clip = clip; self.a = a; self.b = clip["n"] - 1 if b is None else b; self.hold = hold; self.name = name; self.at = at
        self.loops = loops; self.face = face; self.dz = dz; self.mod = mod; self.add = add
        self._base = None                     # add=True 時由 Sequence 填：(前一段結尾的姿勢, 下一段開頭的姿勢, 骨架)

    @property
    def cycle(self):
        return (self.b - self.a) / self.clip["fps"]

    @property
    def dur(self):
        return self.cycle * (self.loops or 1.0) + self.hold

    def _frame1(self, t):
        x = self.a + max(0.0, min(t, self.cycle)) * self.clip["fps"]
        i = min(int(x), self.b - 1) if self.b > self.a else self.a; f = x - i if self.b > self.a else 0.0
        j = min(i + 1, self.b)
        c = self.clip
        R = {k: c["R"][i][k].slerp(c["R"][j][k], f) for k in c["R"][i]}
        h = c["hips"][i].lerp(c["hips"][j], f)
        y = c["yaw"][i] + _wrap(c["yaw"][j] - c["yaw"][i]) * f
        return R, h, y

    def frame(self, t):
        """t：段內秒數 → (R, hips, yaw)，格與格之間 slerp；add 的段疊到前後段的姿勢上；有 mod 的話套上微調"""
        R, h, y = self._frame0(t)
        if getattr(self, "add", False) and self._base is not None:
            R, h = _additive(self, t, R, h, y)
        if getattr(self, "mod", None) is not None:
            R = self.mod(t, R, h)
        return R, h, y

    def _frame0(self, t):
        if not self.loops:
            return self._frame1(t)
        t = max(0.0, min(t, self.cycle * self.loops))
        k = min(int(t / self.cycle), max(0, math.ceil(self.loops) - 1)) if self.cycle > 0 else 0
        R, h, y = self._frame1(t - k * self.cycle)
        step = self.clip["hips"][self.b] - self.clip["hips"][self.a]; step.z = 0
        return R, h + step * k, y


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def _smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


_LEGS = ("UpperLeg", "LowerLeg", "Foot", "ToeBase")


def local_pose(tgt, R, h, y):
    """世界姿勢 → 和站位、面向無關的姿勢：每根骨頭相對父骨頭的旋轉；骨盆是「扣掉面向 y 之後的傾斜」；再加骨盆高度"""
    Yi = Quaternion((0, 0, 1), -y)
    L = {n: (Yi @ R[n]) if tgt.parent[n] is None else (R[tgt.parent[n]].inverted() @ R[n]) for n in tgt.keys}
    return L, h.z


def _additive(seg, t, Rt, ht, yt):
    """加法動作（Seg.add）：輸出＝底姿勢 ×（這段第 t 秒相對第 0 格的變化）。
    底姿勢：整段從前一段結尾慢慢換成下一段開頭（不會先垂手再舉手；下一段是蹲低的舞步時，膝蓋也是轉到最後才彎下去）。
    骨盆水平位置、面向照這段原樣（轉向、腳步就是要的部分）；高度＝底姿勢高度＋這段的起伏，再把較低那隻腳對到這段原本的高度（不陷地、不懸空）"""
    (L0, z0), (L1, z1), tgt = seg._base
    Lr, zr = seg._ref
    Lt, zt = local_pose(tgt, Rt, ht, yt)
    s_up = s_leg = _smooth(t / max(1e-6, seg.dur))
    legs = {f"J_Bip_{s}_{b}" for s in "LR" for b in _LEGS}
    arms = {n for n in tgt.keys if "_L_" in n or "_R_" in n} - legs
    R = {}
    for n in tgt.keys:
        p = tgt.parent[n]
        s = s_leg if (p is None or n in legs) else s_up
        Lb = L0[n].slerp(L1[n], s)
        # 變化量在父骨頭的座標裡套（「上臂往前擺 30°」套到垂下的手臂上還是往前擺；套在自己座標裡，彎著的手臂的擺動會變成往側邊甩高）；
        # 轉身時上身、手臂只是跟著晃，取一部分：腿和骨盆 100%、脊椎頭 50%、手臂 30%
        d = Lt[n] @ Lr[n].inverted()
        k = 0.3 if n in arms else (1.0 if (p is None or n in legs) else 0.5)
        if k < 1.0:
            d = Quaternion().slerp(d, k)
        R[n] = (Quaternion((0, 0, 1), yt) @ d @ Lb) if p is None else (R[p] @ d @ Lb)
    h = Vector((ht.x, ht.y, z0 + (z1 - z0) * s_leg + (zt - zr)))

    def low(R_, h_):
        Hd = tgt.fk(R_, h_)
        return min(Hd[f"J_Bip_{s}_{b}"].z for s in "LR" for b in ("Foot", "ToeBase"))
    h.z += low(Rt, ht) - low(R, h)
    return R, h


class Sequence:
    """多段接成一條：每段的開頭對齊前一段「接點」的骨盆水平位置與面向（只繞 Z 轉＋水平平移，動作本身不變），
    接點前後 blend 秒漸變（前一段的尾巴和後一段的開頭重疊 blend 秒）。
    place(t, xy, yaw_deg)：整條平移／轉向，讓第 t 秒的骨盆水平位置＝xy、面向＝yaw_deg"""
    def __init__(self, tgt, segs, blend=0.3, start=0.0):
        self.tgt = tgt; self.segs = segs; self.blend = blend; self.start = start
        self.G = (Quaternion(), Vector())                     # 整條的擺放
        self._build(0.0)

    def _build(self, gyaw):
        """排每段的開始秒數與擺放。Seg.face（度，場景最終座標）有給的段：開頭面向固定成 face（例：跳舞一律面向鏡頭），
        不接前一段的面向；骨盆水平位置照樣接續。gyaw＝整條擺放的轉角（place 算出來的）"""
        self.T = []                     # 每段 (開始秒數, Yaw 四元數, 平移)
        t = self.start
        for i, s in enumerate(self.segs):
            if i == 0:
                t0 = s.at if s.at is not None else self.start
                self.T.append((t0, Quaternion(), Vector((0.0, 0.0, getattr(s, "dz", 0.0)))))
                t = t0 + s.dur
                continue
            tb = s.at if s.at is not None else t - self.blend    # 這段從前一段結束前 blend 秒開始（或指定的秒數）
            pR, ph, py = self._raw(i - 1, tb)                    # 前一段在接點的狀態（已含前一段的擺放）
            if getattr(s, "add", False):                          # 加法段：底姿勢＝前一段在接點的姿勢 → 下一段第一格（和站位無關）
                s._base = None
                s._ref = local_pose(self.tgt, *s._frame0(0))
                b0 = local_pose(self.tgt, pR, ph, py)
                b1 = local_pose(self.tgt, *self.segs[i + 1].frame(0)) if i + 1 < len(self.segs) else b0
                s._base = (b0, b1, self.tgt)
            R0, h0, y0 = s.frame(0)
            face = getattr(s, "face", None)
            dy = _wrap((math.radians(face) - gyaw if face is not None else py) - y0)
            Ry = Quaternion((0, 0, 1), dy)
            off = ph - Ry @ h0; off.z = getattr(s, "dz", 0.0)
            self.T.append((tb, Ry, off))
            t = tb + s.dur
        self.dur = t - self.start

    def _raw(self, i, t):
        t0, Ry, off = self.T[i]
        R, h, y = self.segs[i].frame(t - t0)
        R = {k: Ry @ q for k, q in R.items()}
        h = Ry @ h + off
        return R, h, y + Ry.to_euler().z

    def place(self, t, xy, yaw_deg):
        """t 要在所有 face 段之前（擺放先由前面的段決定，再把 face 段轉到指定面向）"""
        for _ in range(2):
            R, h, y = self.at(t, raw=True)
            dy = _wrap(math.radians(yaw_deg) - y)
            Gq = Quaternion((0, 0, 1), dy)
            g = Vector((xy[0], xy[1], 0)) - Gq @ Vector((h.x, h.y, 0))
            self.G = (Gq, g)
            self._build(dy)

    def at(self, t, raw=False):
        """場景第 t 秒 → (R, hips, yaw)。t 超出範圍就停在頭尾"""
        t = max(self.start, min(t, self.start + self.dur - 1e-6))
        idx = 0
        for i, (t0, _r, _o) in enumerate(self.T):
            if t >= t0:
                idx = i
        R, h, y = self._raw(idx, t)
        if idx + 1 < len(self.T):
            pass
        if idx > 0:
            t0 = self.T[idx][0]
            if t < t0 + self.blend:                           # 漸變：前一段的尾巴 → 這一段
                w = _smooth((t - t0) / self.blend)
                pR, ph, py = self._raw(idx - 1, t)
                R = {k: pR[k].slerp(R[k], w) for k in R}
                h = ph.lerp(h, w); y = py + _wrap(y - py) * w
        if not raw:
            Gq, g = self.G
            R = {k: Gq @ q for k, q in R.items()}; h = Gq @ h + g; y = y + Gq.to_euler().z
        return R, h, y

    def which(self, t):
        idx = 0
        for i, (t0, _r, _o) in enumerate(self.T):
            if t >= t0:
                idx = i
        return self.segs[idx].name


def basis_from_world(tgt, R, hips):
    """世界旋轉＋骨盆位置 → 每根骨頭的 matrix_basis（armature 空間計算，不用 view_layer.update）"""
    Hd = tgt.fk(R, hips)
    M = {n: Matrix.Translation(Hd[n]) @ R[n].to_matrix().to_4x4() for n in tgt.keys}
    out = {}
    B = tgt.arm.data.bones
    for n in tgt.keys:
        bone = B[n]
        p = bone.parent
        if p is None:
            parent_pose = Matrix(); parent_rest = Matrix()
        elif p.name in M:
            parent_pose = M[p.name]; parent_rest = p.matrix_local
        else:                                           # 中間有沒對應的骨頭（例：Root）：視為不動
            chain = p; parent_pose = None
            while chain is not None and chain.name not in M:
                chain = chain.parent
            if chain is None:
                parent_pose = p.matrix_local; parent_rest = p.matrix_local
            else:
                parent_pose = M[chain.name] @ chain.matrix_local.inverted() @ p.matrix_local; parent_rest = p.matrix_local
        out[n] = (parent_pose @ parent_rest.inverted() @ bone.matrix_local).inverted() @ M[n]
    return out, Hd


def apply_pose(arm, tgt, R, hips, reset=True):
    if reset:
        for pb in arm.pose.bones:
            pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    arm.location = (0, 0, 0); arm.rotation_euler = (0, 0, 0)
    basis, _ = basis_from_world(tgt, R, hips)
    for n, Bm in basis.items():
        pb = arm.pose.bones[n]
        loc, q, _s = Bm.decompose()
        pb.rotation_mode = "QUATERNION"; pb.rotation_quaternion = q; pb.location = loc


def summarize(clip):
    """clip 的簡要數字：秒數、骨盆水平位移、面向變化、最後 0.5 秒是否靜止"""
    n = clip["n"]; fps = clip["fps"]
    d = clip["hips"][-1] - clip["hips"][0]
    dyaw = sum(_wrap(clip["yaw"][i + 1] - clip["yaw"][i]) for i in range(n - 1))
    sp = [((clip["hips"][i + 1] - clip["hips"][i]).xy.length * fps) for i in range(n - 1)]
    return dict(dur=round((n - 1) / fps, 2), frames=n, travel_xy=(round(d.x, 3), round(d.y, 3)), travel=round(d.xy.length, 3),
                yaw_start=round(math.degrees(clip["yaw"][0]), 1), dyaw=round(math.degrees(dyaw), 1),
                max_speed=round(max(sp) if sp else 0, 2), scale=round(clip["scale"], 4))
