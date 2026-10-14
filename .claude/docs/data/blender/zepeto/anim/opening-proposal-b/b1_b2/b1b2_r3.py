# B1→B2 第 3 輪（身體 v8 出廠後，2026-10-12）：
#   手機換 phone_zp → phone_mute_zp（高 12.5 cm）；雙手拇指拿法：兩手從左右夾住機身側邊、四指繞到背面、拇指在螢幕上；
#   右手大拇指點螢幕下方的粉紅開關（點之前 phone_zp、碰到那一格換 phone_mute_zp）。
#   手指：往共用手勢（hold）混，每一指、每一節各自彎到碰到機身就停（不往靜止姿勢混，靜止姿勢現在是併攏伸直）；
#   左右張開角照手勢、不另外動。
import math
from mathutils import Vector, Quaternion, Matrix
import zanim_lib as L
mr = L.mr

S_ZP = 0.125 / 0.155
PHONE = (0.078 * S_ZP, 0.155 * S_ZP, 0.014 * S_ZP)      # 寬、長、厚（m）：build_props.phone_mb × PHONE_ZP
RR = PHONE[2] / 2                                          # 機身邊緣倒圓（厚度方向整個是圓的）
# 手機座標：x＝寬（角色右手方向）、y＝長邊（往頂端）、z＝螢幕法線（朝臉）、原點在機身中心；道具原點在底部中心、螢幕 −Y、長邊 +Z
PROP_FROM_PHONE = Matrix(((1, 0, 0, 0), (0, 0, 1, -PHONE[1] / 2), (0, -1, 0, 0), (0, 0, 0, 1)))


def from_prop(x, y, z):
    """道具座標（m，已縮放）→ 手機座標"""
    return Vector((x, z - PHONE[1] / 2, -y))


# 螢幕：0.066×0.004×0.138 在 y＝−0.007 → 表面 y＝−0.009（×S）；粉紅開關（膠囊）在 (0, −0.0095, 0.042)、厚 0.003 → 表面 y＝−0.011
SCREEN = (0.066 * S_ZP, 0.138 * S_ZP, 0.004 * S_ZP, from_prop(0, -0.007 * S_ZP, 0.0775 * S_ZP))
SCREEN_Z = 0.009 * S_ZP                                    # 螢幕表面在手機座標的 z
SWITCH = from_prop(0, -0.011 * S_ZP, 0.042 * S_ZP)        # 開關表面中心
SWITCH_HALF = ((0.0085 + 0.0065) * S_ZP, 0.0065 * S_ZP)   # 開關半長、半高
FINGERS = ("Index", "Middle", "Ring", "Little")


def _box(q, half, r):
    d = Vector((abs(q.x) - half[0] + r, abs(q.y) - half[1] + r, abs(q.z) - half[2] + r))
    return Vector((max(d.x, 0), max(d.y, 0), max(d.z, 0))).length + min(max(d.x, d.y, d.z), 0.0) - r


def sdf(q, switch=False):
    """點（手機座標）到機身（含螢幕面板）表面的距離，負＝在裡面"""
    d = _box(q, (PHONE[0] / 2, PHONE[1] / 2, PHONE[2] / 2), RR)
    c = SCREEN[3]
    d = min(d, _box(q - c, (SCREEN[0] / 2, SCREEN[1] / 2, SCREEN[2] / 2), 0.0008))
    if switch:
        sc = SWITCH - Vector((0, 0, 0.0015 * S_ZP))
        d = min(d, _box(q - sc, (SWITCH_HALF[0], SWITCH_HALF[1], 0.0015 * S_ZP), 0.0008))
    return d


# ════════ 手指粗細：從網格量（每節骨頭到皮膚的距離） ════════
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


# ════════ 手的目標姿勢 ════════
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


def grip_local(tgt, side, P):
    """握法 → 手骨在手機座標裡的矩陣。P：dy／dz＝手指方向（手機面內往上、往背面的分量），
    tilt＝掌心從「朝機身中線」往螢幕方向轉幾度，c＝掌心皮膚中心（手機座標）"""
    sx = 1.0 if side == "L" else -1.0                        # 左手在 −x 邊，掌心朝 +x
    d = Vector((sx * P.get("dx", 0.0), P["dy"], -P["dz"])).normalized()
    palm = Vector((sx * math.cos(math.radians(P["tilt"])), 0, math.sin(math.radians(P["tilt"]))))
    q = hand_quat(tgt, side, d, palm)
    n = f"J_Bip_{side}_Hand"
    hl = (tgt.rest_h[f"J_Bip_{side}_Middle1"] - tgt.rest_h[n]).length
    pq = q @ tgt.rest_q[n].inverted()
    dW = pq @ (tgt.rest_h[f"J_Bip_{side}_Middle1"] - tgt.rest_h[n]).normalized(); nW = pq @ Vector((0, 0, -1))
    c = Vector(P["c"])
    wrist = c - nW * 0.012 - dW * (0.55 * hl)               # 掌心皮膚 → 骨頭軸（手掌厚約 2.4 cm）→ 手腕
    M = q.to_matrix().to_4x4(); M.translation = wrist
    return M


# ════════ 每指每節碰到就停 ════════
def _seg_pts(tgt, R, Hd, n, k):
    a = Hd[n]; b = tgt.tail(R, Hd, n)
    ss = (0.15, 0.4, 0.65, 0.9, 1.0) if k == 3 else (0.15, 0.4, 0.65, 0.9)
    return [a.lerp(b, s) for s in ss]


def finger_clear(tgt, R, Hd, side, fn, Mi, rad, ks=(1, 2, 3), switch=False):
    """這根手指第 ks 節離機身的最小間隙（m，已扣掉手指半徑；負＝穿進去）"""
    g = 9.9
    for k in ks:
        n = f"J_Bip_{side}_{fn}{k}"
        for p in _seg_pts(tgt, R, Hd, n, k):
            g = min(g, sdf(Mi @ p, switch) - rad[n])
    return g


def close_fingers(tgt, R, h, side, Mp, rad, target, lo, spread, gap=0.0005, step=2.0, fingers=FINGERS):
    """每根手指從 lo 往 target（共用手勢的度數）一節一節彎：第 1 節先彎（後面兩節留在 lo），
    碰到機身（間隙 ≤ gap）就停在前一步；再換第 2 節、第 3 節。回傳 (每指每節的度數, 每節停下來的原因)"""
    Mi = Mp.inverted(); out = {}; why = {}
    for fn in fingers:
        cur = list(lo[fn]); why[fn] = []
        sp = {fn: spread[fn]} if spread and fn in spread else None
        for j in range(3):
            a0, a1 = cur[j], target[fn][j]
            nstep = max(1, int(abs(a1 - a0) / step)); stop = "到手勢"
            for s in range(1, nstep + 1):
                trial = list(cur); trial[j] = a0 + (a1 - a0) * s / nstep
                Rt = mr.finger_pose(tgt, R, side, {fn: tuple(trial)}, sp)
                if finger_clear(tgt, Rt, tgt.fk(Rt, h), side, fn, Mi, rad, ks=range(j + 1, 4)) <= gap:
                    stop = "碰到機身"; break
                cur = trial
            why[fn].append(stop)
        out[fn] = tuple(round(x, 1) for x in cur)
    return out, why


def thumb_pad(tgt, R, Hd, side, Mi, rad, switch=True):
    """拇指最末節離螢幕（或開關）最近的點：(間隙 m, 那一點的手機座標)"""
    n = f"J_Bip_{side}_Thumb3"; best = (9.9, None)
    for p in _seg_pts(tgt, R, Hd, n, 3) + [Hd[n].lerp(tgt.tail(R, Hd, n), s) for s in (0.5, 0.75)]:
        q = Mi @ p; g = sdf(q, switch) - rad[n]
        if g < best[0]:
            best = (g, q)
    return best


# ════════ 單格試做：手機位置 → 兩手握上去 → 手指碰到就停 ════════
# 握法定案值（2026-10-12 第 3 輪定案，由 search_grip 網格搜尋＋近照確認）：c＝掌心皮膚中心（手機座標 m）、tilt＝掌心往螢幕方向轉幾度、
# dy／dz＝手指方向（往手機頂端、往背面的分量）
GRIP_L = dict(c=(-0.034, 0.010, -0.004), tilt=10.0, dy=1.0, dz=0.6)
GRIP_R = dict(c=(0.031, -0.050, -0.004), tilt=20.0, dy=1.0, dz=0.6, dx=0.0)


def phone_pose(tgt, R, h, up=0.08, fwd_d=0.02):
    """手機中心＝兩手掌心中點往上 up、往前 fwd_d；螢幕朝眼睛、長邊沿身體前方"""
    import b1b2_r2 as R2
    Hd = tgt.fk(R, h)
    c = (R2.palm_info(tgt, R, Hd, "L")[0] + R2.palm_info(tgt, R, Hd, "R")[0]) / 2
    fw = R2._fwd(tgt, R, "J_Bip_C_Hips"); fw.z = 0; fw.normalize()
    return R2.reorient_phone(tgt, R, h, c + Vector((0, 0, up)) + fw * fwd_d)


def grip_once(tgt, R, h, Mp, rad, GL=None, GR=None, gest="hold"):
    """這一格：兩手照握法放上去、四指和左手拇指碰到就停。回傳 (R, 報告)"""
    GL = GL or GRIP_L; GR = GR or GRIP_R
    rep = {}
    for side, G in (("L", GL), ("R", GR)):
        M = Mp @ grip_local(tgt, side, G)
        R = put_hand(tgt, R, h, side, M)
        Hd = tgt.fk(R, h)
        rep[side + "_wrist_err_mm"] = round(1000 * (Hd[f"J_Bip_{side}_Hand"] - M.translation).length, 1)
    g = mr.GESTURE[gest]; lo = {f: (0.0, 0.0, 0.0) for f in FINGERS + ("Thumb",)}
    for side in "LR":
        fs = FINGERS + (("Thumb",) if side == "L" else ())
        tgt_c = dict(g["curl"]); tgt_c["Thumb"] = mr.GESTURE["grip"]["curl"]["Thumb"]
        curls, why = close_fingers(tgt, R, h, side, Mp, rad[side], tgt_c, lo, g.get("spread"), fingers=fs)
        R = mr.finger_pose(tgt, R, side, curls, g.get("spread"))
        rep[side + "_curl"] = curls; rep[side + "_why"] = {k: "".join("碰" if s == "碰到機身" else "滿" for s in v) for k, v in why.items()}
    return R, rep


def report_hand(tgt, R, h, Mp, rad):
    Mi = Mp.inverted(); Hd = tgt.fk(R, h); out = {}
    for side in "LR":
        out[side] = {fn: round(1000 * finger_clear(tgt, R, Hd, side, fn, Mi, rad[side], switch=True), 1) for fn in FINGERS + ("Thumb",)}
        import b1b2_r2 as R2
        c, nrm, _d = R2.palm_info(tgt, R, Hd, side)
        out[side]["palm"] = round(1000 * sdf(Mi @ c), 1)
    g, q = thumb_pad(tgt, R, Hd, "R", Mi, rad["R"])
    out["R_thumb_pad"] = (round(1000 * g, 1), tuple(round(1000 * x, 1) for x in q))
    out["switch"] = tuple(round(1000 * x, 1) for x in SWITCH)
    return out


def tilt_up(Mp, deg):
    """手機繞自己的寬度軸把頂端抬起 deg 度（螢幕更朝臉）"""
    xW = Mp.col[0].to_3d().normalized()
    q = Quaternion(xW, math.radians(deg))
    M = (q.to_matrix() @ Mp.to_3x3()).to_4x4(); M.translation = Mp.translation
    return M


THUMB_FULL = (35.0, 45.0, 35.0)


def eval_grip(tgt, R, h, Mp, rad, side, G, gest="fist", free="hold"):
    """一組握法的結果：手放上去 → 四指、拇指碰到就停 → (R, 分數用的數字)"""
    M = Mp @ grip_local(tgt, side, G)
    R = put_hand(tgt, R, h, side, M)
    g = mr.GESTURE[gest]; lo = {f: (0.0, 0.0, 0.0) for f in FINGERS + ("Thumb",)}
    tc = dict(g["curl"]); tc["Thumb"] = G.get("thumb_full", THUMB_FULL)
    curls, why = close_fingers(tgt, R, h, side, Mp, rad, tc, lo, g.get("spread"), fingers=FINGERS + ("Thumb",))
    if free:                                                 # 一路彎到 gest 都沒碰到機身的手指（懸空）改用 free 手勢，不要在空中握拳
        for fn in FINGERS:
            if "碰到機身" not in why[fn]:
                curls[fn] = mr.GESTURE[free]["curl"][fn]; why[fn] = ["懸空"] * 3
    R = mr.finger_pose(tgt, R, side, curls, g.get("spread"))
    Hd = tgt.fk(R, h); Mi = Mp.inverted()
    import b1b2_r2 as R2
    c, _n, _d = R2.palm_info(tgt, R, Hd, side)
    pad_g, pad_q = thumb_pad(tgt, R, Hd, side, Mi, rad, switch=False)
    clear = {fn: finger_clear(tgt, R, Hd, side, fn, Mi, rad) for fn in FINGERS + ("Thumb",)}
    hand_pen = 9.9                                           # 手掌（手骨軸）離機身
    for s in (0.2, 0.5, 0.8):
        p = Hd[f"J_Bip_{side}_Hand"].lerp(Hd[f"J_Bip_{side}_Middle1"], s)
        hand_pen = min(hand_pen, sdf(Mi @ p) - 0.012)
    return R, dict(curls=curls, why=why, palm_gap=sdf(Mi @ c), pad_gap=pad_g, pad=pad_q, clear=clear, hand_gap=hand_pen,
                   touching=sum(1 for fn in FINGERS if "碰到機身" in why[fn]))


def search_grip(tgt, R, h, Mp, rad, side, base, grid, score):
    """在 grid（{參數: [值…]}）裡找分數最低的握法"""
    import itertools
    keys = list(grid); best = None
    for vals in itertools.product(*[grid[k] for k in keys]):
        G = dict(base); G.update(dict(zip(keys, vals)))
        if "cx" in G or "cy" in G or "cz" in G:
            c = list(G["c"]); c[0] = G.get("cx", c[0]); c[1] = G.get("cy", c[1]); c[2] = G.get("cz", c[2]); G["c"] = tuple(c)
        _R, r = eval_grip(tgt, R, h, Mp, rad, side, G)
        s = score(r)
        if best is None or s < best[0]:
            best = (s, G, r)
    return best


THUMB_BEND = (10.0, 45.0, 40.0)                            # 拇指彎到底的度數（第 1、2、3 節），用比例 s 混


def thumb_reach(tgt, R, h, side, Mp, rad, goal, lift=0.0, iters=4):
    """拇指指腹點到 goal（手機座標，例如開關表面中心）上方 lift 公尺：
    先調彎度讓「拇指根→指腹」的距離對上，再把整根拇指（從第 1 節）轉過去對準。回傳 (R, 指腹間隙 m, 指腹位置, 拇指整根轉了幾度)"""
    Mi = Mp.inverted(); n1 = f"J_Bip_{side}_Thumb1"; n3 = f"J_Bip_{side}_Thumb3"
    zW = Mp.col[2].to_3d().normalized()
    want = Mp @ goal + zW * (rad[n3] + lift)                # 指腹骨頭軸要到的位置（世界）

    def pad_axis(Rx):
        Hd = tgt.fk(Rx, h); a = Hd[n3]; b = tgt.tail(Rx, Hd, n3)
        return a.lerp(b, 0.7), Hd
    lo, hi = 0.0, 1.0
    Rb = R
    for _ in range(12):                                     # 彎度：拇指根到指腹的距離 = 拇指根到目標的距離
        s = (lo + hi) / 2
        Rt = mr.finger_pose(tgt, R, side, {"Thumb": tuple(x * s for x in THUMB_BEND)})
        p, Hd = pad_axis(Rt)
        if (p - Hd[n1]).length > (want - Hd[n1]).length:
            lo = s
        else:
            hi = s
        Rb = Rt
    ang = 0.0
    for _ in range(iters):
        p, Hd = pad_axis(Rb)
        q = (p - Hd[n1]).rotation_difference(want - Hd[n1])
        ang += math.degrees(q.angle)
        Rb = mr.rotate_subtree(tgt, Rb, n1, q)
    Hd = tgt.fk(Rb, h)
    g, qp = thumb_pad(tgt, Rb, Hd, side, Mi, rad, switch=True)
    return Rb, g, qp, ang


THUMBS = ("Thumb1", "Thumb2", "Thumb3")


def thumb_local(tgt, R, side):
    """拇指三節相對手骨的旋轉（手相對手機不動，所以這組在每一格都一樣）"""
    H = f"J_Bip_{side}_Hand"
    return {t: R[H].inverted() @ R[f"J_Bip_{side}_{t}"] for t in THUMBS}


def set_thumb(R, side, loc, w=1.0):
    H = f"J_Bip_{side}_Hand"; out = dict(R)
    for t in THUMBS:
        n = f"J_Bip_{side}_{t}"; q = R[H] @ loc[t]
        out[n] = R[n].slerp(q, w) if w < 1 else q
    return out


def thumb_press_poses(tgt, R, h, side, Mp, rad, goal, hover=0.008, fix_iters=3, touch_gap=-0.0007):
    """點開關的兩個拇指姿勢（相對手骨）：touch＝指腹貼在開關中心（間隙約 0.4 mm），hover＝整根拇指從根部抬起、指腹離開關 hover。
    touch 的落點會再修正幾次（指腹落點和開關中心的差，反向補到目標上）。回傳 (touch, hover, 報告)"""
    # touch_gap：骨頭估的指腹間隙目標。皮膚網格實量比骨頭估的多約 1.1 mm（2026-10-12 mesh_checks），
    # 所以骨頭估 −0.7 mm ≈ 皮膚離開關 0.4 mm
    g_ = goal.copy(); lift = touch_gap
    for _ in range(fix_iters + 3):
        Rt, g, qp, ang = thumb_reach(tgt, R, h, side, Mp, rad, g_, lift)
        err = Vector((goal.x - qp.x, goal.y - qp.y, 0))
        g_ = g_ + err
        lift += touch_gap - g
    touch = thumb_local(tgt, Rt, side)
    Hd = tgt.fk(Rt, h); n1 = f"J_Bip_{side}_Thumb1"
    zW = Mp.col[2].to_3d().normalized()
    pad = Mp @ qp
    ax = (pad - Hd[n1]).cross(zW).normalized()
    a = 0.0; Rh = Rt
    for _ in range(3):                                          # 抬到指腹間隙 ≈ hover
        a += (hover + touch_gap - thumb_pad(tgt, Rh, tgt.fk(Rh, h), side, Mp.inverted(), rad, True)[0]) / max(0.02, (pad - Hd[n1]).length)
        Rh = mr.rotate_subtree(tgt, Rt, n1, Quaternion(ax, a))
        if thumb_pad(tgt, Rh, tgt.fk(Rh, h), side, Mp.inverted(), rad, True)[0] < 0:
            ax = -ax; a = -a; Rh = mr.rotate_subtree(tgt, Rt, n1, Quaternion(ax, a))
    hov = thumb_local(tgt, Rh, side)
    gh, qh = thumb_pad(tgt, Rh, tgt.fk(Rh, h), side, Mp.inverted(), rad, True)
    return touch, hov, dict(touch_gap_mm=round(1000 * g, 2), touch_pad_mm=tuple(round(1000 * x, 1) for x in qp),
                            hover_gap_mm=round(1000 * gh, 1), lift_deg=round(math.degrees(abs(a)), 1), thumb_rot_deg=round(ang, 1))
