# ⑦a 新娘右手的西餐握叉（2026-10-11，第 3 關第 13 輪回饋「手握叉的角度始終不正確，握法也不正確，手指也會穿模」）。
# 前幾輪的做法是「手指先擺固定彎度、再把叉子塞到手指附近」，手指和叉柄從來沒有對上，所以會穿模、角度怪。
# 這裡反過來：先在右手的 rest 空間（armature 座標；VRoid 右手手指往 −X、掌心朝 −Z、食指在 −Y 側）把叉子放好，
# 再讓每根手指從伸直慢慢彎，彎到剛好碰到叉柄就停：
#   食指：根部往掌心彎，第 2、3 節壓在叉柄上面
#   中指：彎起來，指尖那節的側面托在叉柄下
#   無名指、小指：彎進掌心，不碰叉柄
#   拇指：指尖夾在叉柄的食指側
#   叉柄尾端：壓在掌根靠小指那側
# 尺寸是 bride 右手量的（hand_probe：手指皮膚離骨頭中心 0.7～0.9 cm、掌心皮膚在手骨頭下 2.1～2.3 cm）。
# 用法：g = solve_grip(rest_h, rest_t, rest_q) → g["Fr"]（叉子在 rest 空間的矩陣）、g["acc"]（每節手指相對手掌的旋轉，rest 空間）；
#   apply_grip(tgt, R, g["acc"]) 套到姿勢上（同 finger_pose 最後一步）
import math
from mathutils import Vector, Quaternion, Matrix
from mathutils.geometry import intersect_point_line

SIDE = "R"
SG = -1.0                                   # 右手（finger_pose：左手 +1、右手 −1）
R_FINGER = {"Index": (0.0105, 0.0095, 0.0090), "Middle": (0.0089, 0.0087, 0.0074), "Ring": (0.0092, 0.0077, 0.0060),
            "Little": (0.0080, 0.0067, 0.0050), "Thumb": (0.0130, 0.0099, 0.0060)}   # 各節粗細（皮膚離骨頭中心的中位數）
HALF_T, HALF_W = 0.00175, 0.0045            # 叉柄半厚、半寬（set_v2.build_fork：柄 9 mm × 3.5 mm）
HANDLE = (-0.065, 0.035)                    # 叉柄在叉子 z 上的範圍（原點＝握點、+Z＝叉尖；柄尾 −6.5、叉頸從 +3.5）
NECK = (0.035, 0.075)
BITE_LOCAL = Vector((0.0, 0.0, 0.098))      # 叉上那一口的位置（叉齒中段）
GAP = 0.0006                                # 手指皮膚離叉柄的空隙


def _seg_dist(a, b, c, d):
    """兩條線段 ab、cd 的最近距離（取樣法，夠用）"""
    best = 1e9
    for i in range(21):
        p = a.lerp(b, i / 20)
        q, u = intersect_point_line(p, c, d)
        u = max(0.0, min(1.0, u)); q = c.lerp(d, u)
        best = min(best, (p - q).length)
    return best


def _chain(rest_h, rest_t, fn, acc_list):
    """手指彎好之後各節的頭、尾位置（rest 空間）"""
    names = ["J_Bip_%s_%s%d" % (SIDE, fn, i) for i in (1, 2, 3)]
    pts = [rest_h[names[0]].copy()]
    for k, n in enumerate(names):
        seg = (rest_t[n] - rest_h[n]) if k == 2 else (rest_h[names[k + 1]] - rest_h[n])
        pts.append(pts[-1] + acc_list[k] @ seg)
    return names, pts


def _acc(fn, degs, spread=0.0):
    axis_r = Vector((0, SG, 0)); axis_s = Vector((0, 0, -SG))
    acc = Quaternion(axis_s, math.radians(spread)); out = []
    for d in degs:
        acc = acc @ Quaternion(axis_r, math.radians(d)); out.append(acc.copy())
    return out


def solve_grip(rest_h, rest_t, rest_q):
    H = "J_Bip_%s_Hand" % SIDE
    hh = rest_h[H]
    P = lambda f, i=1: rest_h["J_Bip_%s_%s%d" % (SIDE, f, i)]
    palm_z = hh.z - 0.0225                                          # 掌心皮膚
    # 叉柄：尾端壓在掌根靠小指側，往前斜過食指根部下方（掌心皮膚外 1 柄厚），叉尖伸出食指外
    #   斜度約 20°（第一版 36°，叉齒偏到食指外側 6 cm）
    T = Vector((hh.x - 0.022, P("Little").y - 0.020, palm_z - HALF_T - GAP))
    P2 = Vector((P("Index").x + 0.004, P("Index").y + 0.010, palm_z - HALF_T - GAP - 0.001))
    z = (P2 - T).normalized()
    y = Vector((0, 0, -1)); y = (y - z * y.dot(z)).normalized()     # 叉子的平面朝掌心
    x = y.cross(z)
    O = T + z * (-HANDLE[0])                                        # 原點使柄尾剛好在 T
    Fr = Matrix((x, y, z)).transposed().to_4x4(); Fr.translation = O
    h0, h1 = O + z * HANDLE[0], O + z * NECK[1]                    # 叉柄＋叉頸（手指可能碰到的範圍）
    acc_all = {}; report = {}

    def dist_to_fork(fn, pts, k0=0):
        rr = R_FINGER[fn]
        return min(_seg_dist(pts[k], pts[k + 1], h0, h1) - rr[k] - HALF_T for k in range(k0, 3))

    # 食指：根部往掌心彎（第 2、3 節跟著微彎），彎到第 2、3 節碰到叉柄上面
    best = None
    for k in range(0, 91):
        a = float(k)
        acc = _acc("Index", (a, a * 0.25, a * 0.15))
        _n, pts = _chain(rest_h, rest_t, "Index", acc)
        dmin = dist_to_fork("Index", pts)
        if dmin <= GAP:
            best = (a, acc, dmin); break
        best = (a, acc, dmin)
    a, acc, dmin = best
    a -= 2.0                                                          # 再退 2°：骨頭距離算剛好碰到時，皮膚最粗的點還會陷進 0.1 mm（FORKCLIP）
    acc = _acc("Index", (a, a * 0.25, a * 0.15))
    for n, q in zip(["J_Bip_%s_Index%d" % (SIDE, i) for i in (1, 2, 3)], acc):
        acc_all[n] = q
    report["Index"] = round(a, 1)

    # 中指：整根彎（1 : 1.1 : 0.75），彎到指尖那兩節碰到叉柄
    # 上限＝真人拿叉子時自然微彎的程度（整根約 130°）。第一版沒有上限、一路彎到碰掌心才停（整根 170°），
    #   手指捲成拳頭、指尖勾回叉柄下面，側面看手指背面壓在桌上（第 3 關近照頁回饋「側面的手都很奇怪，例如有一些是手背折餐桌」）
    for fn, ratio, k_from, stop_touch, max_a in (("Middle", (1.0, 1.1, 0.75), 1, True, 46),
                                                 ("Ring", (1.0, 1.1, 0.75), 0, False, 44),
                                                 ("Little", (1.0, 1.1, 0.75), 0, False, 46)):
        last = (0.0, _acc(fn, (0, 0, 0)))
        for k in range(0, max_a + 1):
            a = float(k)
            acc = _acc(fn, tuple(a * r for r in ratio), spread={"Middle": -2, "Ring": -5, "Little": -9}[fn])
            _n, pts = _chain(rest_h, rest_t, fn, acc)
            d = dist_to_fork(fn, pts, k_from)
            tip_below_palm = pts[3].z < palm_z - 0.002 and (pts[3] - hh).length < 0.075   # 指尖跑到掌心皮膚裡
            if d < 0 or tip_below_palm:
                break                                                 # 再彎就穿進叉柄／掌心 → 停在上一格
            last = (a, acc)
            if stop_touch and d <= GAP:
                break
        a, acc = last
        for n, q in zip(["J_Bip_%s_%s%d" % (SIDE, fn, i) for i in (1, 2, 3)], acc):
            acc_all[n] = q
        report[fn] = round(a, 1)

    # 拇指：先微彎，再整串繞拇指根轉過去，讓指尖碰在叉柄的食指側（離叉柄中心＝指尖粗細＋柄半寬）
    th_degs = (12.0, 22.0, 16.0)
    d0 = (rest_h["J_Bip_%s_Thumb2" % SIDE] - rest_h["J_Bip_%s_Thumb1" % SIDE]).normalized()
    axis_r = d0.cross(Vector((0, 0, -1))).normalized() * -1.0       # finger_pose 的 THUMB_SIGN 方向（右手）
    acc = Quaternion(); th = []
    for dg in th_degs:
        acc = acc @ Quaternion(axis_r, math.radians(dg)); th.append(acc.copy())
    names, pts = _chain(rest_h, rest_t, "Thumb", th)
    contact = O + z * 0.012                                          # 叉柄上、食指第 1 節下方一點
    goal = contact + Vector((0, -1, 0)) * (R_FINGER["Thumb"][2] + HALF_W + GAP + 0.0015) + Vector((0, 0, 0.002))   # +1.5 mm：0 時穿進叉柄 2.3 mm、+3 mm 時離 3.5 mm
    q = (pts[3] - pts[0]).rotation_difference(goal - pts[0])
    for n, a_ in zip(names, th):
        acc_all[n] = q @ a_
    _n, pts_t = _chain(rest_h, rest_t, "Thumb", [q @ a_ for a_ in th])
    report["Thumb_tip_to_handle_mm"] = round((_seg_dist(pts_t[2], pts_t[3], h0, h1) - R_FINGER["Thumb"][2] - HALF_W) * 1000, 1)
    report["Index_to_handle_mm"] = round(dist_to_fork("Index", _chain(rest_h, rest_t, "Index", [acc_all["J_Bip_R_Index%d" % i] for i in (1, 2, 3)])[1]) * 1000, 1)
    return dict(Fr=Fr, acc=acc_all, report=report, hand=H)


def fork_in_hand(g, rest_h, rest_q):
    """叉子 → 手骨頭空間：FB_R（那一口）、FA_R（叉子方向），給 fork_to_r 用；rel＝叉子矩陣（給 mx_preview 的 fork_rel）"""
    H = g["hand"]; Fr = g["Fr"]
    qi = rest_q[H].inverted()
    fb = qi @ ((Fr @ BITE_LOCAL) - rest_h[H])
    fa = (qi @ (Fr.to_3x3() @ Vector((0, 0, 1)))).normalized()
    return fb, fa


def apply_grip(tgt, R, acc_all, w=1.0):
    """套到姿勢上（同 mixamo_retarget.finger_pose 的最後一步）"""
    H = "J_Bip_%s_Hand" % SIDE
    Mh = R[H] @ tgt.rest_q[H].inverted()
    out = dict(R)
    for n, acc in acc_all.items():
        q = Mh @ acc @ tgt.rest_q[n]
        out[n] = R[n].slerp(q, w) if w < 1 else q
    return out
