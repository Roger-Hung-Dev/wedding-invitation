# B1→B2 第 2 輪修正（使用者 2026-10-11 裁決）：都是套在 Mixamo 原樣之上的微調，不改動作結構。
#   lift_head：按手機時頭低太深 → 只把超過 PITCH0 的低頭角抬掉一部分（時間點照原樣）
#   phone：手機（先用 7×15×0.8 cm 方塊）黏在左手掌，螢幕朝臉；右手用 IK 把掌心貼到手機另一邊
#   raise_hips：起步一開始骨盆下沉（膝蓋一沉）→ 骨盆抬回、腿 IK 讓腳留在原地
import math
from mathutils import Vector, Quaternion, Matrix
import zanim_lib as L
import zanim_fix as F
mr = L.mr

PHONE = (0.078, 0.155, 0.014)        # 寬、長、厚（m）：素材庫 phone_mute 的機身（背面相機凸起另計）
# 手機座標（本檔）：x＝寬（角色右手方向）、y＝長邊（往頂端）、z＝螢幕法線（朝臉）、原點在機身中心。
# 素材庫道具：原點在底部中心、螢幕朝 −Y、長邊沿 +Z → 道具矩陣 ＝ Mp @ PROP_FROM_PHONE
PROP_FROM_PHONE = Matrix(((1, 0, 0, 0), (0, 0, 1, -PHONE[1] / 2), (0, -1, 0, 0), (0, 0, 0, 1)))


def _fwd(tgt, R, n, v=(0, -1, 0)):
    return (R[n] @ tgt.rest_q[n].inverted()) @ Vector(v)


# ════════ 1. 低頭調淺 ════════
def head_pitch(tgt, R):
    f = _fwd(tgt, R, "J_Bip_C_Head")
    return math.degrees(math.asin(max(-1, min(1, -f.z))))


def lift_head(tgt, R, keep=0.4, pitch0=10.0, split=(0.4, 0.6)):
    """低頭角超過 pitch0 的部分只留 keep 倍（例：44° → 10 + 34×0.4 ≈ 24°）；脖子、頭各分一部分，繞角色左右軸抬"""
    p = head_pitch(tgt, R)
    if p <= pitch0:
        return R
    lift = math.radians((p - pitch0) * (1 - keep))
    f = _fwd(tgt, R, "J_Bip_C_UpperChest"); f.z = 0
    if f.length < 1e-6:
        return R
    side = f.normalized().cross(Vector((0, 0, 1)))       # 角色右手方向；繞它轉負角＝抬頭
    for n, k in zip(("J_Bip_C_Neck", "J_Bip_C_Head"), split):
        R = mr.rotate_subtree(tgt, R, n, Quaternion(side, lift * k))
    return R


# ════════ 2. 手機 ════════
def hand_frame(tgt, R, Hd, s):
    """手的世界矩陣（骨架空間）"""
    n = f"J_Bip_{s}_Hand"
    return Matrix.Translation(Hd[n]) @ R[n].to_matrix().to_4x4()


def palm_info(tgt, R, Hd, s):
    n = f"J_Bip_{s}_Hand"
    q = R[n] @ tgt.rest_q[n].inverted()
    d = (tgt.tail(R, Hd, n) - Hd[n]).normalized()          # 手腕 → 指尖方向
    hl = (tgt.rest_t[n] - tgt.rest_h[n]).length
    nrm = q @ Vector((0, 0, -1))                            # rest 掌心朝下
    c = Hd[n] + d * (0.55 * hl) + nrm * 0.012              # 掌心表面中心（手掌厚約 2.4 cm）
    return c, nrm, d


def phone_frame_ideal(tgt, R, h):
    """理想手機姿勢：左手掌心外 1 cm＋半寬；螢幕朝眼睛；長邊沿身體前方（直拿、底部靠身體）"""
    Hd = tgt.fk(R, h)
    cL, nL, dL = palm_info(tgt, R, Hd, "L")
    c = cL + nL * (0.004 + PHONE[0] / 2)
    eye = Hd["J_Bip_C_Head"] + Vector((0, 0, 0.07)) + _fwd(tgt, R, "J_Bip_C_Head") * 0.10
    zN = (eye - c).normalized()                             # 螢幕法線
    fw = _fwd(tgt, R, "J_Bip_C_Hips"); fw.z = 0; fw.normalize()
    yL = (fw - zN * fw.dot(zN)).normalized()                # 長邊
    xW = yL.cross(zN)
    c = c + yL * 0.025                                      # 手握在下半段
    M = Matrix((xW, yL, zN)).transposed().to_4x4(); M.translation = c
    return M


def _avg_mat(Ms):
    q0 = Ms[0].to_quaternion(); qs = Quaternion((0, 0, 0, 0)); t = Vector()
    for M in Ms:
        q = M.to_quaternion()
        if q.dot(q0) < 0:
            q.negate()
        qs = Quaternion((qs.w + q.w, qs.x + q.x, qs.y + q.y, qs.z + q.z)); t += M.translation
    qs.normalize(); A = qs.to_matrix().to_4x4(); A.translation = t / len(Ms); return A


def phone_rig(tgt, poses, t_text, fps=30):
    """→ off_L（手機在左手座標）、off_R（右手在手機座標，右掌心貼手機另一邊）；用按手機段中段（t_text=(a, b) 秒）的平均"""
    fr = range(int(t_text[0] * fps), int(t_text[1] * fps))
    oL, oR = [], []
    for i in fr:
        R, h = poses[i]; Hd = tgt.fk(R, h)
        Mp = phone_frame_ideal(tgt, R, h)
        oL.append(hand_frame(tgt, R, Hd, "L").inverted() @ Mp)
        oR.append(Mp.inverted() @ hand_frame(tgt, R, Hd, "R"))
    off_L = _avg_mat(oL); off_R = _avg_mat(oR)
    # 右手的位置改成「掌心貼手機右邊」：在手機座標裡，右掌心中心要在 x = −(半寬＋0.4 cm)、y 和左手同一段
    return off_L, off_R


def place_right(tgt, R, h, Mp, off_R, w):
    """右手照手機的位置擺：手腕 IK＋手掌朝向，w＝權重（0～1）；回傳新 R"""
    if w <= 1e-3:
        return R
    Hd = tgt.fk(R, h)
    MR0 = hand_frame(tgt, R, Hd, "R")
    MRt = Mp @ off_R
    # 掌心表面中心換到右手座標：先算目標手的掌心，再讓它落在手機右邊
    n = "J_Bip_R_Hand"; hl = (tgt.rest_t[n] - tgt.rest_h[n]).length
    qt = MRt.to_quaternion() @ tgt.rest_q[n].inverted()
    dT = qt @ ((tgt.rest_t[n] - tgt.rest_h[n]).normalized()); nT = qt @ Vector((0, 0, -1))
    xW = Mp.col[0].to_3d().normalized()
    nT = -xW                                                 # 掌心朝手機（右手在 +x 邊，掌心朝 −x）
    dT = (dT - xW * dT.dot(xW)).normalized()                 # 指尖方向：平均方向扣掉朝手機的分量
    # 掌心中心：沿長邊的位置照平均，左右貼手機右邊，厚度方向對齊手機中線
    rel = Mp.inverted() @ (MRt.translation + (qt @ ((tgt.rest_t[n] - tgt.rest_h[n]).normalized())) * (0.55 * hl))
    rel.x = PHONE[0] / 2 + 0.004 + 0.012; rel.z = 0.0          # xW＝長邊×螢幕法線＝角色右手方向，右手在 +x 邊
    palm_c = Mp @ rel                                        # 手掌中心（骨頭軸上）
    wrist_t = palm_c - dT * (0.55 * hl)
    wrist = MR0.translation.lerp(wrist_t, w)
    pole = Hd["J_Bip_R_LowerArm"] - (Hd["J_Bip_R_UpperArm"] + Hd[n]) / 2
    R = mr.arm_ik(tgt, R, h, "R", wrist, pole if pole.length > 1e-4 else Vector((0, 0, -1)))
    d0 = (tgt.tail(R, tgt.fk(R, h), n) - tgt.fk(R, h)[n]).normalized()
    R = mr.aim_hand(tgt, R, h, "R", d0.lerp(dT, w).normalized(), palm=nT, palm_w=w)
    return R


# ════════ 3. 起步不下沉 ════════
def raise_hips(tgt, poses, a, b, ramp=6, margin_deg=4.0):
    """第 a～b 格：骨盆高度不低於「a 格高度 → b 格高度」的平滑過渡線；腳用腿 IK 留在原來的世界位置。
    腿伸不到（膝蓋會打直）就少抬一點：膝蓋至少留 margin_deg 度彎"""
    out = list(poses)
    za = poses[a][1].z; zb = poses[b][1].z
    lim = math.cos(math.radians(margin_deg) / 2)
    lifted = []
    for i in range(max(0, a - ramp), min(len(poses), b + ramp + 1)):
        R, h = poses[i]
        s = mr._smooth((i - a) / max(1, b - a))
        zd = za + (zb - za) * s
        w = 1.0 if a <= i <= b else mr._smooth(1 - (a - i) / ramp if i < a else 1 - (i - b) / ramp)
        dz = max(0.0, zd - h.z) * w
        if dz < 1e-4:
            lifted.append(0.0); continue
        Hd = tgt.fk(R, h)
        ank = {s_: Hd[f"J_Bip_{s_}_Foot"].copy() for s_ in "LR"}
        # 可抬的上限：兩腳 髖→腳踝 距離不超過腿長 × lim
        for s_ in "LR":
            U = Hd[f"J_Bip_{s_}_UpperLeg"]
            Lt = (tgt.rest_h[f"J_Bip_{s_}_LowerLeg"] - tgt.rest_h[f"J_Bip_{s_}_UpperLeg"]).length + \
                 (tgt.rest_h[f"J_Bip_{s_}_Foot"] - tgt.rest_h[f"J_Bip_{s_}_LowerLeg"]).length
            v = ank[s_] - U; horiz = v.xy.length
            zmax = math.sqrt(max(0.0, (Lt * lim) ** 2 - horiz ** 2)) - (U.z - ank[s_].z)
            dz = min(dz, max(0.0, zmax))
        h2 = h.copy(); h2.z += dz
        R2 = R
        for s_ in "LR":
            Hd2 = tgt.fk(R2, h2)
            knee = Hd2[f"J_Bip_{s_}_LowerLeg"]; mid = (Hd2[f"J_Bip_{s_}_UpperLeg"] + Hd2[f"J_Bip_{s_}_Foot"]) / 2
            R2 = F.leg_ik(tgt, R2, h2, s_, ank[s_], knee - mid)
        out[i] = (R2, h2); lifted.append(dz)
    return out, max(lifted) if lifted else 0.0


def straighten_stance(tgt, poses, pts, a, b, kmax=10.0, ramp=8, smooth=4, z_on=0.012, zcap=None):
    """起步不下沉（第 2 版）：第 a～b 格，踩地那隻腳的膝蓋彎超過 kmax 度時，把骨盆抬到膝蓋剛好 kmax 度；
    陷地的腳先抬回地面；腳（含騰空那隻）用腿 IK 留在原位置。抬的量前後 smooth 格平均、頭尾 ramp 格漸入漸出"""
    n = len(poses)
    lo_i, hi_i = max(0, a - ramp), min(n - 1, b + ramp)
    need = {}; tgt_ank = {}
    for i in range(lo_i, hi_i + 1):
        R, h = poses[i]; Hd = tgt.fk(R, h)
        so = L.soles(tgt, R, h, pts)
        dz_i = 0.0; ank = {}
        for s_ in "LR":
            low = min(p.z for p in so[s_])
            A = Hd[f"J_Bip_{s_}_Foot"].copy()
            if low < 0:
                A.z -= low
            ank[s_] = A
            if low > z_on:
                continue
            U = Hd[f"J_Bip_{s_}_UpperLeg"]
            la = (tgt.rest_h[f"J_Bip_{s_}_LowerLeg"] - tgt.rest_h[f"J_Bip_{s_}_UpperLeg"]).length
            lb = (tgt.rest_h[f"J_Bip_{s_}_Foot"] - tgt.rest_h[f"J_Bip_{s_}_LowerLeg"]).length
            dK = math.sqrt(la * la + lb * lb + 2 * la * lb * math.cos(math.radians(kmax)))
            horiz = (U - A).xy.length
            if horiz >= dK:
                continue
            dz_i = max(dz_i, math.sqrt(dK * dK - horiz * horiz) - (U.z - A.z))
        if zcap is not None:                                  # 不高過站立時的骨盆（不然像往上彈）
            dz_i = min(dz_i, max(0.0, zcap - h.z))
        need[i] = dz_i; tgt_ank[i] = ank
    # 只抬不壓：踩地兩腳各自要求的抬量取大，但不能超過「另一隻踩地腳伸直」的上限 → 用 leg_ik 時自然夾住
    sm = {}
    for i in need:
        win = [need[j] for j in range(max(lo_i, i - smooth), min(hi_i, i + smooth) + 1)]
        sm[i] = sum(win) / len(win)
    out = list(poses); lifted = 0.0
    for i in need:
        w = 1.0 if a <= i <= b else mr._smooth(1 - ((a - i) if i < a else (i - b)) / (ramp + 1))
        dz = sm[i] * w
        R, h = poses[i]; h2 = h.copy(); h2.z += dz; R2 = R
        for s_ in "LR":
            Hd2 = tgt.fk(R2, h2)
            knee = Hd2[f"J_Bip_{s_}_LowerLeg"]; mid = (Hd2[f"J_Bip_{s_}_UpperLeg"] + Hd2[f"J_Bip_{s_}_Foot"]) / 2
            pole = knee - mid
            if pole.length < 1e-3:
                pole = _fwd(tgt, R2, "J_Bip_C_Hips")
            R2 = F.leg_ik(tgt, R2, h2, s_, tgt_ank[i][s_], pole)
        out[i] = (R2, h2); lifted = max(lifted, dz)
    return out, lifted


FINGERS = ("Index", "Middle", "Ring", "Little")


def open_fingers(tgt, R, side, u):
    """四指每一節「相對上一節」的彎曲只留 (1−u)：u＝0 原樣、1 全伸直（rest 的張開角）；拇指不動"""
    if u <= 1e-4:
        return R
    for f in FINGERS:
        for k in (1, 2, 3):
            n = f"J_Bip_{side}_{f}{k}"
            p = tgt.parent[n]
            loc = R[p].inverted() @ R[n]                       # 這一節相對父骨頭
            loc0 = tgt.rest_q[p].inverted() @ tgt.rest_q[n]     # rest 時的相對
            want = loc0.slerp(loc, 1 - u)
            q = (R[p] @ want) @ R[n].inverted()
            R = mr.rotate_subtree(tgt, R, n, q)
    return R


def reorient_phone(tgt, R, h, c):
    """手機中心在 c 時的姿勢：螢幕朝眼睛、長邊沿身體前方"""
    Hd = tgt.fk(R, h)
    eye = Hd["J_Bip_C_Head"] + Vector((0, 0, 0.07)) + _fwd(tgt, R, "J_Bip_C_Head") * 0.10
    zN = (eye - c).normalized()
    fw = _fwd(tgt, R, "J_Bip_C_Hips"); fw.z = 0; fw.normalize()
    yL = (fw - zN * fw.dot(zN)).normalized(); xW = yL.cross(zN)
    M = Matrix((xW, yL, zN)).transposed().to_4x4(); M.translation = c
    return M


def lift_left(tgt, R, h, off_L, up, fwd_d, w):
    """手機（連左手）往上 up、往前 fwd_d 公尺，螢幕重新朝臉；左手用 IK 跟過去。回傳 (R, 實際手機姿勢)"""
    Hd = tgt.fk(R, h)
    Mp0 = hand_frame(tgt, R, Hd, "L") @ off_L
    fw = _fwd(tgt, R, "J_Bip_C_Hips"); fw.z = 0; fw.normalize()
    c = Mp0.translation + (Vector((0, 0, up)) + fw * fwd_d) * w
    Mp = reorient_phone(tgt, R, h, c)
    Mp = Matrix.lerp(Mp0, Mp, w) if False else _blend_mat(Mp0, Mp, w)
    MLt = Mp @ off_L.inverted()
    n = "J_Bip_L_Hand"
    qt = MLt.to_quaternion() @ tgt.rest_q[n].inverted()
    d = qt @ (tgt.rest_t[n] - tgt.rest_h[n]).normalized(); palm = qt @ Vector((0, 0, -1))
    pole = Hd["J_Bip_L_LowerArm"] - (Hd["J_Bip_L_UpperArm"] + Hd[n]) / 2
    R = mr.arm_ik(tgt, R, h, "L", MLt.translation, pole if pole.length > 1e-4 else Vector((0, 0, -1)))
    R = mr.aim_hand(tgt, R, h, "L", d, palm=palm, palm_w=1.0)
    Hd = tgt.fk(R, h)
    return R, hand_frame(tgt, R, Hd, "L") @ off_L


def _blend_mat(A, B, w):
    q = A.to_quaternion().slerp(B.to_quaternion(), w); M = q.to_matrix().to_4x4()
    M.translation = A.translation.lerp(B.translation, w); return M
