# ZEPETO 動畫共用：姿勢修正（2026-10-12 由 B1→B2 的 b12_r2 抽出通用的函式，內容沒改）
#   lift_head：低頭太深只抬掉一部分；palm_info／hand_frame：掌心位置與朝向；raise_hips／straighten_stance：起步不沉
import math
from mathutils import Vector, Quaternion, Matrix
import zanim_lib as L
import zanim_fix as F
mr = L.mr


def _fwd(tgt, R, n, v=(0, -1, 0)):
    return (R[n] @ tgt.rest_q[n].inverted()) @ Vector(v)


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


def _blend_mat(A, B, w):
    q = A.to_quaternion().slerp(B.to_quaternion(), w); M = q.to_matrix().to_4x4()
    M.translation = A.translation.lerp(B.translation, w); return M


def _avg_mat(Ms):
    q0 = Ms[0].to_quaternion(); qs = Quaternion((0, 0, 0, 0)); t = Vector()
    for M in Ms:
        q = M.to_quaternion()
        if q.dot(q0) < 0:
            q.negate()
        qs = Quaternion((qs.w + q.w, qs.x + q.x, qs.y + q.y, qs.z + q.z)); t += M.translation
    qs.normalize(); A = qs.to_matrix().to_4x4(); A.translation = t / len(Ms); return A
