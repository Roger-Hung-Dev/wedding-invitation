# ZEPETO 動畫共用：手和道具的互動（2026-10-12 由 B1→B2 的 b12_r3、坐餐桌喝紅酒的 t_sit 抽出，內容沒改）
#   finger_radius：從皮膚網格量每節手指的粗細；put_hand／put_hand_pole：手放到指定矩陣（後者可指定手肘方向）
#   close_fingers：每一指、每一節往目標手勢彎，碰到道具（距離場 sdf）就停；thumb_to：拇指整根轉到目標點
#   道具的形狀用距離場 sdf(q)→ 距離（m，負＝在裡面），q 是道具座標；Mi／Mo 是世界 → 道具座標的矩陣
import math
from mathutils import Vector, Quaternion, Matrix
import zanim_lib as L
mr = L.mr

FINGERS = ("Index", "Middle", "Ring", "Little")
THUMB_FULL = (35.0, 45.0, 35.0)          # 拇指三節「完全彎」的角度（b12_r3 定的）


def finger_radius(arm, body, side):
    """每節手指的半徑（m）：權重 > 0.6 的頂點到骨頭軸的距離取 70 百分位（指節背側凸起也算進去）"""
    B = arm.data.bones; gi = {g.name: g.index for g in body.vertex_groups}
    M = arm.matrix_world.inverted() @ body.matrix_world
    names = [f"J_Bip_{side}_{f}{k}" for f in FINGERS + ("Thumb",) for k in (1, 2, 3)]
    want = {gi[n]: n for n in names if n in gi}
    ds = {n: [] for n in names}
    for v in body.data.vertices:
        for g in v.groups:
            n = want.get(g.group)
            if n and g.weight > 0.6:
                a, b = B[n].head_local, B[n].tail_local; p = M @ v.co
                t = max(0.0, min(1.0, (p - a).dot(b - a) / (b - a).length_squared))
                ds[n].append((p - (a + (b - a) * t)).length)
    out = {}
    for n, d in ds.items():
        d.sort()
        out[n] = d[int(0.7 * (len(d) - 1))] if d else 0.008
    return out


def hand_quat(tgt, side, d, palm):
    """手骨的世界旋轉：手腕→中指根朝 d、掌心朝 palm（VRoid rest：手指沿 ±X、掌心 −Z）"""
    n = f"J_Bip_{side}_Hand"
    d0 = (tgt.rest_h[f"J_Bip_{side}_Middle1"] - tgt.rest_h[n]).normalized(); p0 = Vector((0, 0, -1))
    p0 = (p0 - d0 * p0.dot(d0)).normalized()
    d = d.normalized(); palm = (palm - d * palm.dot(d)).normalized()
    A = Matrix((d0, p0, d0.cross(p0))).transposed()
    Bm = Matrix((d, palm, d.cross(palm))).transposed()
    return (Bm @ A.inverted()).to_quaternion() @ tgt.rest_q[n]


def hand_mat(tgt, R, Hd, side):
    n = f"J_Bip_{side}_Hand"
    return Matrix.Translation(Hd[n]) @ R[n].to_matrix().to_4x4()


def put_hand(tgt, R, h, side, M, w=1.0):
    """手骨移到世界矩陣 M（位置＝手腕、旋轉＝手骨世界旋轉）：手臂 IK＋轉手掌；w＝和原本之間的權重"""
    if w <= 1e-3:
        return R
    n = f"J_Bip_{side}_Hand"; Hd = tgt.fk(R, h)
    q = M.to_quaternion() @ tgt.rest_q[n].inverted()
    d = q @ (tgt.rest_h[f"J_Bip_{side}_Middle1"] - tgt.rest_h[n]).normalized(); palm = q @ Vector((0, 0, -1))
    d0 = (Hd[f"J_Bip_{side}_Middle1"] - Hd[n]).normalized()
    pole = Hd[f"J_Bip_{side}_LowerArm"] - (Hd[f"J_Bip_{side}_UpperArm"] + Hd[n]) / 2
    R = mr.arm_ik(tgt, R, h, side, Hd[n].lerp(M.translation, w), pole if pole.length > 1e-4 else Vector((0, 0, -1)))
    R = mr.aim_hand(tgt, R, h, side, d0.lerp(d, w).normalized(), palm=palm, palm_w=w, max_bend=None)
    return R


def _seg_pts(tgt, R, Hd, n, k):
    a = Hd[n]; b = tgt.tail(R, Hd, n)
    ss = (0.15, 0.4, 0.65, 0.9, 1.0) if k == 3 else (0.15, 0.4, 0.65, 0.9)
    return [a.lerp(b, s) for s in ss]


def finger_clear(tgt, R, Hd, side, fn, Mi, rad, sdf, ks=(1, 2, 3)):
    g = 9.9
    for k in ks:
        n = f"J_Bip_{side}_{fn}{k}"
        for p in _seg_pts(tgt, R, Hd, n, k):
            g = min(g, sdf(Mi @ p) - rad[n])
    return g


def close_fingers(tgt, R, h, side, Mo, rad, target, sdf, fingers, gap=0.0005, step=2.0):
    Mi = Mo.inverted(); out = {}; why = {}
    for fn in fingers:
        cur = [0.0, 0.0, 0.0]; why[fn] = []
        for j in range(3):
            a0, a1 = cur[j], target[fn][j]
            nstep = max(1, int(abs(a1 - a0) / step)); stop = "到手勢"
            for s in range(1, nstep + 1):
                trial = list(cur); trial[j] = a0 + (a1 - a0) * s / nstep
                Rt = mr.finger_pose(tgt, R, side, {fn: tuple(trial)})
                if finger_clear(tgt, Rt, tgt.fk(Rt, h), side, fn, Mi, rad, sdf, ks=range(j + 1, 4)) <= gap:
                    stop = "碰到"; break
                cur = trial
            why[fn].append(stop)
        out[fn] = tuple(round(x, 1) for x in cur)
    return out, why


def thumb_to(tgt, R, h, side, Mo, rad, goal, sdf, gap=0.0004, iters=4, bend=(10.0, 45.0, 40.0)):
    """拇指指腹點到 goal（物件座標）：先調彎度讓根部到指腹的距離對上，再整根轉過去對準；回傳 (R, 指腹間隙, 拇指整根轉了幾度)"""
    n1, n3 = f"J_Bip_{side}_Thumb1", f"J_Bip_{side}_Thumb3"
    Mi = Mo.inverted()

    def pad(Rx):
        Hd = tgt.fk(Rx, h); a = Hd[n3]; b = tgt.tail(Rx, Hd, n3)
        return a.lerp(b, 0.7), Hd
    # 目標：指腹的骨頭軸要在 goal 往外（離開杯腳軸）拇指半徑＋gap 的地方
    out_dir = Vector((goal.x, goal.y, 0)).normalized()
    want = Mo @ (goal + out_dir * (rad[n3] + gap))
    lo, hi = 0.0, 1.0; Rb = R
    for _ in range(12):
        s = (lo + hi) / 2
        Rt = mr.finger_pose(tgt, R, side, {"Thumb": tuple(x * s for x in bend)})
        p, Hd = pad(Rt)
        if (p - Hd[n1]).length > (want - Hd[n1]).length:
            lo = s
        else:
            hi = s
        Rb = Rt
    ang = 0.0
    for _ in range(iters):
        p, Hd = pad(Rb)
        q = (p - Hd[n1]).rotation_difference(want - Hd[n1]); ang += math.degrees(q.angle)
        Rb = mr.rotate_subtree(tgt, Rb, n1, q)
    Hd = tgt.fk(Rb, h)
    g = min(sdf(Mi @ p_) - rad[n3] for p_ in _seg_pts(tgt, Rb, Hd, n3, 3))
    return Rb, g, ang


def put_hand_pole(tgt, R, h, side, M, w, pole_dir, pw):
    """同 b12_r3.put_hand，但手肘方向（pole）可以往 pole_dir 混 pw"""
    if w <= 1e-3:
        return R
    n = f"J_Bip_{side}_Hand"; Hd = tgt.fk(R, h)
    q = M.to_quaternion() @ tgt.rest_q[n].inverted()
    d = q @ (tgt.rest_h[f"J_Bip_{side}_Middle1"] - tgt.rest_h[n]).normalized(); palm = q @ Vector((0, 0, -1))
    d0 = (Hd[f"J_Bip_{side}_Middle1"] - Hd[n]).normalized()
    pole = Hd[f"J_Bip_{side}_LowerArm"] - (Hd[f"J_Bip_{side}_UpperArm"] + Hd[n]) / 2
    if pole.length < 1e-4:
        pole = Vector((0, 0, -1))
    pole = pole.normalized().lerp(pole_dir, pw)
    R = mr.arm_ik(tgt, R, h, side, Hd[n].lerp(M.translation, w), pole)
    R = mr.aim_hand(tgt, R, h, side, d0.lerp(d, w).normalized(), palm=palm, palm_w=w, max_bend=None)
    return R
