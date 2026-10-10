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
            R[n] = D @ A[n].inverted() @ tgt.rest_q[n]
        Rs.append(R)
        hp = Rg @ (Hf["Hips"] - h0) * s
        hips.append(tgt.rest_h["J_Bip_C_Hips"] + hp)
        l = Rg @ (Hf["LeftUpLeg"] - Hf["RightUpLeg"]); l.z = 0
        yaw.append(_yaw_of(l))
    return dict(n=src["n"], fps=src["fps"], R=Rs, hips=hips, yaw=yaw, scale=s, path=src.get("path"))


class Seg:
    """一段：clip 的第 a～b 格（含頭尾）。hold＝b 之後停在最後一格的秒數；
    at＝這段在場景裡的開始秒數（None＝接在前一段結束前 blend 秒；比那個晚的話，前一段停在最後一格等）"""
    def __init__(self, clip, a=0, b=None, hold=0.0, name="", at=None, loops=None, face=None):
        """loops：循環動作（走路）重複幾次（可以是小數）：每圈骨盆往前接上一圈的位移，圈與圈之間不漸變（循環動作頭尾本來就接得起來）；
        face：這段開頭的面向（度，場景座標；0＝面向鏡頭），None＝接前一段的面向"""
        self.clip = clip; self.a = a; self.b = clip["n"] - 1 if b is None else b; self.hold = hold; self.name = name; self.at = at
        self.loops = loops; self.face = face

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
        """t：段內秒數 → (R, hips, yaw)，格與格之間 slerp"""
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
                self.T.append((t0, Quaternion(), Vector()))
                t = t0 + s.dur
                continue
            tb = s.at if s.at is not None else t - self.blend    # 這段從前一段結束前 blend 秒開始（或指定的秒數）
            pR, ph, py = self._raw(i - 1, tb)                    # 前一段在接點的狀態（已含前一段的擺放）
            R0, h0, y0 = s.frame(0)
            face = getattr(s, "face", None)
            dy = _wrap((math.radians(face) - gyaw if face is not None else py) - y0)
            Ry = Quaternion((0, 0, 1), dy)
            off = ph - Ry @ h0; off.z = 0
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
