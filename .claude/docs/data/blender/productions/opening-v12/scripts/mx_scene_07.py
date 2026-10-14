# ⑦ 燭光晚餐（12 秒）。2026-10-10 Mixamo 版第 1 關（骨骼）；2026-10-11 第 3 關第 2 輪回饋後第三次重做。
# 座位、道具、鏡頭照現行 v2_07（shots_v2.py 的 T07R5、set_v2.py）：圓桌心 (1.85, −1.25)、桌面高 0.734、落地桌巾半徑 0.485；
#   新郎座位 (1.45, −0.85) 面向 45°、新娘 (2.25, −0.85) 面向 −45°（都面向桌心）；鏡頭 (1.98, −3.95, 1.36) 看 (1.99, −1.05, 0.97)、38 mm。
# 劇情照舊：新郎（左手）叉一口餵新娘 → 兩人拿起酒杯、碰杯、舉杯向鏡頭、喝 → 拿著杯子笑。
#
# 2026-10-11 第 3 關第 2 輪回饋「太多動作行為都不是正常人類的動作，甚至比最原初的版本還差」→ 重想做法：
#   Mixamo 沒有坐著吃飯、乾杯的動畫。上一版拿「坐著聊天」「坐著指東西」「坐下喝飲料」三支當底，原片本身的大動作（比手勢、仰頭喝罐裝飲料、
#   手舉到頭頂）和我加的手部路線互相拉扯，手臂一下舉高握拳、一下甩開；新娘頭往下栽、身體轉開。
#   對照最早的版本（videos/preview-v2/s07_dinner_sheet.jpg）：看起來像人的關鍵是「兩人坐著幾乎不動，只有拿東西的那隻手在動」。
#   → 底換成「Seated Idle With Hands On A Table」（兩手平放桌上、身體穩，原片只有很小的晃動；原片低頭 26° 由看人的微調抬起來）＋呼吸；
#     只有拿叉子、拿杯子的那隻手照劇情動，路線用平順的曲線（經過每個點、中間不停），節奏照最早的版本。
#   道具：叉子、酒杯開場擺的位置改成照新動作算（mx_preview 在拿起的那一格量手上的道具），拿起來時不會瞬移。
import math
from mathutils import Quaternion, Matrix

SEAT = 0.675                                          # 骨盆高：Seated Idle 原片手在骨盆上 7 cm → 手剛好平放在桌面（0.734）
G07, B07 = (1.45, -0.85), (2.25, -0.85)
SEAT_G = SEAT_B = SEAT

FINAL = OPT.get("FINAL") == "1"
CAM = Vector((1.98, -3.95, 1.36))
TABLE_Z = 0.733
TABLE_C, TABLE_R = Vector((1.85, -1.25)), 0.485
PLATE_BITE = Vector((1.740, -1.098, 0.752))          # 牛排塊在盤上的位置（正式場景，scripts/mx_prop_probe.py）
GLASS_G, GLASS_B = Vector((1.6197, -1.0197, 0.775)), Vector((2.0803, -1.0197, 0.775))   # 酒杯握點（杯腳中段），同上
CLINK = Vector((1.85, -0.94, 0.89))                  # 碰杯點（兩個杯身相碰的地方）
TOAST_G, TOAST_B = Vector((1.610, -1.127, 0.937)), Vector((2.152, -1.122, 0.898))   # 舉杯向鏡頭停住的握點（現行）
HOLD_G, HOLD_B = Vector((1.640, -1.000, 0.865)), Vector((2.060, -1.000, 0.865))     # 喝完拿在胸前
GROOM_FACE = Vector((1.48, -0.89, 1.24))             # 新郎的臉（新娘先算，拿不到新郎的骨架，用坐好時的位置）
DRINK_LOOK = Vector((1.85, -1.25, 1.18))             # 喝的時候看前方（桌子中間上方），不轉頭喝
OFF_STEM = Vector((-0.022, 0.058, -0.004))           # 杯腳在手骨頭裡的位置（動作庫 actions_custom.OFF_STEM，右手；左手 x 取負）×體型
GL_BOWL, GL_RIM, GL_RIM_R = 0.085, 0.135, 0.042      # 從握點量：杯身中心、杯緣高、杯緣半徑（動作庫 GLASS）
FORK_BITE = Vector((0.0789, 0.165, 0.0518))          # 牛排塊相對新郎左手骨頭（骨頭座標，scripts/mx_fork_probe.py 量的正式場景叉子）
FORK_AX = Vector((0.3015, 0.9045, 0.3015)).normalized()   # 叉子方向（握點→叉尖），同上
T_FORK, T_SPEAR, T_PUT = 0.4, 1.0, 3.4                # 拿起叉子、叉起那一口、叉子放回桌上（mx_preview 的道具時間點）
T_GLASS_G, T_GLASS_B = 5.3, 5.4                       # 拿起酒杯
UP = Vector((0, 0, 1))


def sm(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def win(t, a, b, c, d):
    if t <= a or t >= d:
        return 0.0
    if t < b:
        return sm((t - a) / max(1e-6, b - a))
    if t <= c:
        return 1.0
    return 1.0 - sm((t - c) / max(1e-6, d - c))


def spline(t, keys):
    """[(秒, 點或 fn(t))…] 平順曲線：經過每個點、中間不停（Catmull-Rom 切線＋Hermite）；頭尾和「相鄰兩點一樣」（停住）切線為 0。
    點給函式時用目前的秒數算（例：新娘的嘴會動，叉子跟著她的嘴）"""
    P = [(tk, (p(t) if callable(p) else p)) for tk, p in keys]
    if t <= P[0][0]:
        return P[0][1].copy()
    if t >= P[-1][0]:
        return P[-1][1].copy()
    n = len(P)

    def tan(i):
        if i == 0 or i == n - 1:
            return Vector((0, 0, 0))
        (ta, pa), (tb, pb), (tc, pc) = P[i - 1], P[i], P[i + 1]
        if (pb - pa).length < 1e-6 or (pc - pb).length < 1e-6:
            return Vector((0, 0, 0))
        return (pc - pa) / (tc - ta)
    for i in range(n - 1):
        (t0, p0), (t1, p1) = P[i], P[i + 1]
        if t0 <= t <= t1:
            dt = max(1e-6, t1 - t0); u = (t - t0) / dt
            h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
            return p0 * h00 + tan(i) * (h10 * dt) + p1 * h01 + tan(i + 1) * (h11 * dt)
    return P[-1][1].copy()


def ramp(t, spans, r=0.4):
    """[(a, b, 點或 fn(t))…] → (目標點, 權重)：各段前後 r 秒漸入漸出，重疊時照權重混合（第 2 輪後 0.25 → 0.4 秒：轉頭太快像點頭）"""
    pts = []; ws = []
    for a_, b_, pt in spans:
        if t < a_ - r or t > b_ + r:
            continue
        x = (t - (a_ - r)) / r if t < a_ else (1.0 if t <= b_ else 1.0 - (t - b_) / r)
        x = sm(x)
        if x > 0:
            pts.append(pt(t) if callable(pt) else Vector(pt)); ws.append(x)
    if not ws:
        return None, 0.0
    tot = sum(ws)
    return sum((p_ * w_ for p_, w_ in zip(pts, ws)), Vector()) / tot, min(1.0, tot)


def head_axes(T_, R):
    q = R["J_Bip_C_Head"] @ T_.rest_q["J_Bip_C_Head"].inverted()
    return q @ Vector((0, -1, 0)), q @ Vector((0, 0, 1)), q @ Vector((1, 0, 0))


def mouth_of(T_, R, H):
    """嘴（頭骨往臉前 8.5 cm、往上 2 cm，跟著頭的方向）"""
    f, u, _l = head_axes(T_, R)
    return H["J_Bip_C_Head"] + f * 0.085 + u * 0.02


def bride_face(t, fwd_cm=0.0, up_m=0.02):
    """新娘的嘴（用她算好的骨架：轉頭、湊過去都算進去）＋往臉前 fwd_cm"""
    f_ = min(len(BUILT["bride"]) - 1, int(round(t * 30)))
    H = BUILT["bride"][f_]; R = BUILT_R["bride"][f_]; B = tgt("bride")
    f, u, _l = head_axes(B, R)
    return H["J_Bip_C_Head"] + f * (0.085 + fwd_cm) + u * up_m


def body_axes(Hd):
    lft = Hd["J_Bip_L_UpperLeg"] - Hd["J_Bip_R_UpperLeg"]; lft.z = 0; lft.normalize()
    return lft, Vector((lft.y, -lft.x, 0))


def palm_of(H, s_):
    return (H[f"J_Bip_{s_}_Hand"] + H[f"J_Bip_{s_}_Middle1"]) * 0.5


def hand_to(T_, R, h, s_, goal_palm, pole, w, iters=3):
    """掌心中點到 goal_palm（手腕目標反覆修正）；w＝權重"""
    H = T_.fk(R, h); start = H[f"J_Bip_{s_}_Hand"]; p0 = palm_of(H, s_)
    want = p0.lerp(goal_palm, w); target = start + (want - p0); R0 = R
    for _ in range(iters):
        R = arm_ik(T_, R0, h, s_, target, pole)
        target = target + (want - palm_of(T_.fk(R, h), s_))
    return R


def stem_off(T_, s_):
    k = T_.rest_h["J_Bip_C_Head"].z / 1.386
    return Vector((OFF_STEM.x * (1 if s_ == "R" else -1), OFF_STEM.y, OFF_STEM.z)) * k


def grip_of(T_, R, Hd, s_):
    return Hd[f"J_Bip_{s_}_Hand"] + R[f"J_Bip_{s_}_Hand"] @ stem_off(T_, s_)


def hold_glass(T_, R, h, s_, grip, axis, w, pole, iters=4):
    """握杯腳：握點到 grip、杯子直立方向＝axis（手骨頭的 +Z，同動作庫 held_prop("glass")）；手指方向順著前臂
    （最早那版看起來像人的握法：mx_prop_probe 量的，手骨頭 Y 軸≈前臂方向、Z 軸朝上）。w＝權重（從原片的手漸漸接過來）"""
    H, L = f"J_Bip_{s_}_Hand", f"J_Bip_{s_}_LowerArm"
    off = stem_off(T_, s_); a = axis.normalized()
    Hd = T_.fk(R, h); g0 = Hd[H] + R[H] @ off
    want = g0.lerp(grip, w); target = Hd[H] + (want - g0); R0 = R
    for _ in range(iters):
        R = arm_ik(T_, R0, h, s_, target, pole)
        Hd = T_.fk(R, h)
        fa = (Hd[H] - Hd[L]).normalized()
        b = fa - a * fa.dot(a)
        if b.length < 1e-4:
            b = Vector((0, -1, 0)) - a * a.y
        b.normalize()
        Rh = Matrix((b.cross(a), b, a)).transposed().to_quaternion()
        R = rotate_subtree(T_, R, H, R[H].slerp(Rh, w) @ R[H].inverted())
        R = fix_arm_twist(T_, R, h, s_)
        Hd = T_.fk(R, h)
        target = target + (want - (Hd[H] + R[H] @ off))
    return R


def drink_grip(T_, R, H, theta):
    """喝：杯緣靠在下唇、杯子往臉的方向傾 theta → (握點, 杯子軸)"""
    f, u, _l = head_axes(T_, R)
    fh = Vector((f.x, f.y, 0)).normalized()
    m = mouth_of(T_, R, H)
    rim = m + fh * (GL_RIM_R + 0.004) - UP * 0.014
    a = (UP * math.cos(theta) - fh * math.sin(theta)).normalized()
    return rim - a * GL_RIM, a


def glass_plan(own, clink, toast, hold, dt=0.0):
    """握點路線：手伸過去 → 拿起 → 胸前 → 往桌子中間碰杯 → 舉向鏡頭停 1.2 秒 → 拿到嘴邊喝 → 拿在胸前（dt＝整條延後，兩人不會完全同步）"""
    chest = own + Vector((0.0, 0.03, 0.10))
    return [(4.45 + dt, None), (4.95 + dt, own + UP * 0.05), (5.3 + dt, own), (5.36 + dt, own),
            (5.85 + dt, chest), (6.45, clink), (6.62, clink), (6.85, clink + (own - clink).normalized() * 0.02 + UP * 0.01),
            (7.3 + dt, toast), (8.5 + dt, toast), (8.95 + dt, "drink"), (9.95 + dt, "drink"), (10.5 + dt, hold), (12.5, hold)]


def glass_hand(T_, R, h, s_, plan, w, pole, t, dt=0.0):
    """照 glass_plan 擺拿杯子的手（喝的那段用頭的位置算握點、杯子傾斜 30→44°）"""
    Hd = T_.fk(R, h)
    cur = grip_of(T_, R, Hd, s_)
    th = math.radians(30.0 + 14.0 * sm((t - (9.0 + dt)) / 0.9))
    dg, da = drink_grip(T_, R, Hd, th)
    keys = [(tk, cur if p is None else (dg if isinstance(p, str) else p)) for tk, p in plan]
    goal = spline(t, keys)
    wd = win(t, 8.5 + dt, 8.95 + dt, 9.95 + dt, 10.5 + dt)
    axis = UP.lerp(da, wd).normalized()
    return hold_glass(T_, R, h, s_, goal, axis, w, pole)


def table_guard(T_, R, h, skip=()):
    """桌面護手：手（手腕、中指根）在桌面範圍內又低於桌面上 1.5 cm 時，掌心往上抬到剛好放在桌上（不足多少抬多少，平順）"""
    for s_, sg in (("L", 1.0), ("R", -1.0)):
        if s_ in skip:
            continue
        Hd = T_.fk(R, h)
        pts = [Hd[f"J_Bip_{s_}_Hand"], Hd[f"J_Bip_{s_}_Middle1"]]
        on = [p_ for p_ in pts if (Vector((p_.x, p_.y)) - TABLE_C).length < TABLE_R - 0.01]
        if not on:
            continue
        lack = TABLE_Z + 0.015 - min(p_.z for p_ in on)
        if lack <= 0:
            continue
        lft, _f = body_axes(Hd)
        R = hand_to(T_, R, h, s_, palm_of(Hd, s_) + UP * lack, lft * sg + UP * (-0.8), 1.0)
    return R


def fork_to(G, R, h, goal, d, w, iters=4):
    """新郎左手的叉子：牛排塊到 goal、叉子方向轉向 d（權重 w）；手腕目標照牛排塊的誤差修幾次"""
    H = "J_Bip_L_Hand"
    Hd = G.fk(R, h); R0 = R
    bite0 = Hd[H] + R[H] @ FORK_BITE
    want = bite0.lerp(goal, w); target = Hd[H] + (want - bite0)
    for _ in range(iters):
        R = arm_ik(G, R0, h, "L", target, Vector((0.35, 0.35, -1)))
        ax = R[H] @ FORK_AX
        R = rotate_subtree(G, R, H, ax.rotation_difference(ax.lerp(d, w).normalized()))
        R = fix_arm_twist(G, R, h, "L")
        Hd2 = G.fk(R, h)
        target = target + (want - (Hd2[H] + R[H] @ FORK_BITE))
    return R


def lean(T_, R, Hd, toward, deg):
    """上身往 toward 那邊傾 deg 度（繞腰）"""
    tb = toward - Hd["J_Bip_C_Hips"]; tb.z = 0
    if tb.length < 1e-6 or abs(deg) < 1e-3:
        return R
    tb.normalize()
    return rotate_subtree(T_, R, "J_Bip_C_Spine", Quaternion(UP.cross(tb).normalized(), math.radians(deg)))


def rest_hands(T_, R, h):
    """雙手平放桌上、收在身前（2026-10-11：原片兩手相距 53 cm、手肘張很開，兩人坐成直角時靠內側的手在桌子中間碰在一起）：
    掌心在骨盆往前 30 cm、往左右各 15 cm、桌面上 2 cm，手指朝前偏內，掌心朝下"""
    Hd = T_.fk(R, h)
    lft, fwd = body_axes(Hd)
    hp = Hd["J_Bip_C_Hips"]
    for s_, sg in (("L", 1.0), ("R", -1.0)):
        spot = Vector((hp.x, hp.y, 0)) + fwd * 0.30 + lft * (sg * 0.15); spot.z = TABLE_Z + 0.02
        for _ in range(2):                                                    # 轉手掌朝下會讓掌心移 2～3 cm，擺位置→轉手掌做兩次才收斂
            R = hand_to(T_, R, h, s_, spot, lft * (sg * 0.8) - UP * 0.6, 1.0)
            H2 = T_.fk(R, h)
            cur = (H2[f"J_Bip_{s_}_Middle1"] - H2[f"J_Bip_{s_}_Hand"]).normalized()
            R = aim_hand(T_, R, h, s_, (fwd * 0.92 - lft * (sg * 0.3) - UP * 0.12).normalized(), palm=-UP, palm_w=1.0)
        R = gesture(T_, R, s_, "relaxed", w=1.0)
    return R


def bride_mod():
    B = tgt("bride")
    plan = glass_plan(GLASS_B, CLINK + Vector((0.046, 0, -GL_BOWL)), TOAST_B, HOLD_B, dt=0.08)

    def mod(t, R, h):
        R = breathe(B, R, h, t, deg=1.2, phase=0.45)
        Hd = B.fk(R, h)
        lft, fwd = body_axes(Hd)
        mouth = Hd["J_Bip_C_Head"] + fwd * 0.09 + UP * 0.025
        fork_in = mouth + fwd * 0.12 - lft * 0.12                            # 叉子從她右前方（新郎那側）過來
        R = lean(B, R, Hd, fork_in, 7.0 * win(t, 1.55, 1.95, 2.2, 2.7))      # 湊過去咬（2.1 秒咬下）
        # 頭：看新郎 → 叉子過來時看叉子 → 咬完看回新郎笑 → 拿杯看自己的杯子 → 碰杯看新郎 → 舉杯看鏡頭 → 喝的時候看前方 → 結尾看著新郎
        pt, w = ramp(t, [(-1, 1.05, GROOM_FACE), (1.3, 2.2, fork_in), (2.45, 4.35, GROOM_FACE), (4.6, 5.35, GLASS_B + UP * 0.45),
                         (5.6, 6.85, GROOM_FACE), (7.15, 8.55, CAM), (8.85, 10.4, DRINK_LOOK), (10.65, 99, GROOM_FACE)])
        if pt is not None:
            R = look_at(B, R, h, pt, w=w, split=(0.1, 0.2, 0.7), pitch=0.85)
        R = rest_hands(B, R, h)
        wg = win(t, 4.45, 4.8, 12.5, 13.0)
        if wg > 0:
            R = glass_hand(B, R, h, "R", plan, wg, -lft * 0.7 - UP * 0.7, t, dt=0.08)
        R = gesture(B, R, "R", "hold", w=win(t, 5.2, 5.4, 12.5, 13.0))
        return table_guard(B, R, h, skip=("R",) if wg > 0.5 else ())
    return mod


def groom_mod():
    G = tgt("groom")
    plan = glass_plan(GLASS_G, CLINK + Vector((-0.046, 0, -GL_BOWL)), TOAST_G, HOLD_G)

    def mod(t, R, h):
        # 順序：會轉動上身的（呼吸、探身、轉頭）先做，最後才擺手（第 3 關第 1 輪：先送叉子再轉頭，叉子被帶偏 17 cm 插進新娘頭）
        R = breathe(G, R, h, t, deg=1.2)
        R = lean(G, R, G.fk(R, h), bride_face(t), 10.0 * win(t, 1.25, 1.85, 2.3, 2.9))   # 餵的時候上身往她那邊傾
        # 頭：看新娘 → 低頭看盤子叉一口 → 餵的時候看她的嘴 → 看著她笑 → 拿杯看杯子 → 碰杯看她 → 舉杯看鏡頭 → 喝的時候看前方 → 結尾看鏡頭
        pt, wl = ramp(t, [(-1, 0.25, lambda t_: bride_face(t_)), (0.5, 1.1, PLATE_BITE + UP * 0.22), (1.4, 4.35, lambda t_: bride_face(t_)),
                          (4.6, 5.3, GLASS_G + UP * 0.45), (5.55, 6.85, lambda t_: bride_face(t_)), (7.15, 8.55, CAM),
                          (8.85, 10.4, DRINK_LOOK), (10.65, 99, CAM)])
        if pt is not None:
            R = look_at(G, R, h, pt, w=wl, split=(0.1, 0.2, 0.7), pitch=0.85)
        R = rest_hands(G, R, h)
        # 左手：叉子（0.4 秒拿起 → 盤上叉一口 → 送到她嘴前 2.5 cm 停 0.4 秒 → 收回、3.4 秒放回桌上）
        # 叉子平躺在桌上（第 2 輪自我審查：手平放時叉子的握點在手掌下面 3 cm，叉子插進桌子）→ 0.15～0.4 秒手抬到叉子平躺在桌面上的高度才拿起，
        #   3.1～3.4 秒放回同一個地方、平躺，3.4～3.7 秒手才放回桌上
        wf = win(t, 0.15, 0.4, 3.4, 3.7)
        if wf > 0:
            Hd = G.fk(R, h)
            rb = Hd["J_Bip_L_Hand"] + R["J_Bip_L_Hand"] @ FORK_BITE
            rest = Vector((rb.x, rb.y, TABLE_Z + 0.008))
            # 牛排塊停在嘴前 2.5 cm、嘴的高度（第 2 輪近照：以前高 1.5 cm，碰到上唇和鼻尖）
            mouth = lambda t_: bride_face(t_, 0.025, 0.005)
            mid = lambda t_: PLATE_BITE.lerp(bride_face(t_, 0.025, 0.005), 0.5) + UP * 0.10
            back = lambda t_: PLATE_BITE.lerp(bride_face(t_, 0.025, 0.005), 0.45) + UP * 0.06
            keys = [(0.4, rest), (0.75, PLATE_BITE + UP * 0.07), (1.0, PLATE_BITE), (1.2, PLATE_BITE + UP * 0.09),
                    (1.55, mid), (1.9, mouth), (2.3, mouth), (2.65, back), (3.05, rest + UP * 0.04), (3.4, rest)]
            goal = spline(t, keys)
            sh = Hd["J_Bip_L_UpperArm"]
            d = goal - sh; d.z = 0; d.normalize()
            stab = win(t, 0.75, 0.92, 1.05, 1.2)                               # 叉的時候叉尖往下
            lie = 1.0 - win(t, 0.4, 0.6, 3.0, 3.35)                            # 放在桌上時叉子平躺
            d = (d + UP * (0.12 * (1 - stab) * (1 - lie) - 0.9 * stab)).normalized()
            R = fork_to(G, R, h, goal, d, wf)
        R = gesture(G, R, "L", "hold", w=win(t, 0.25, 0.4, T_PUT - 0.05, T_PUT + 0.15))
        # 左手：酒杯
        wg = win(t, 4.45, 4.8, 12.5, 13.0)
        if wg > 0:
            Hd = G.fk(R, h)
            lft, _f = body_axes(Hd)
            R = glass_hand(G, R, h, "L", plan, wg, lft * 0.7 - UP * 0.7, t)
        R = gesture(G, R, "L", "hold", w=win(t, 5.1, 5.3, 12.5, 13.0))
        return table_guard(G, R, h, skip=("L",) if (wg > 0.5 or t < 0.45 or 3.0 < t < 3.75) else ())
    return mod


def post(out):
    """第 2 關網頁：酒杯跟著手（拿起後杯腳在握點）；椅子調高到坐姿骨盆下方"""
    if not FINAL:
        return
    for who, side, own, tg, nm in (("groom", "L", GLASS_G, T_GLASS_G, "新郎酒杯"), ("bride", "R", GLASS_B, T_GLASS_B, "新娘酒杯")):
        c = out["chars"][who]; I = {n: i for i, n in enumerate(c["bones"])}
        path = []
        for i in range(0, len(c["frames"]), 2):
            t = i / out["fps"]
            if t < tg:
                continue
            p = c["frames"][i]["p"]; Hh, M = p[I[f"J_Bip_{side}_Hand"]], p[I[f"J_Bip_{side}_Middle1"]]
            palm = [(Hh[k] + M[k]) / 2 for k in range(3)]
            path.append([round(t, 3), round(palm[0], 3), round(palm[1], 3), round(palm[2] + 0.046, 3)])
        g = next(p for p in out["props"] if p.get("name") == nm)
        z0 = TABLE_Z + 0.088
        g.update(c=[own[0], own[1], z0], z0=TABLE_Z, z1=TABLE_Z + 0.177, path=[[0.0, own[0], own[1], z0], [tg, own[0], own[1], z0]] + path)
    for p in out["props"]:
        if p.get("name", "").startswith("新郎椅") or p.get("name", "").startswith("新娘椅"):
            p["max"][2] = SEAT - 0.08; p["name"] = p["name"][:3] + "（椅面調高到 %.2f）" % (SEAT - 0.08)


def scene():
    # 底：兩人都是「Seated Idle With Hands On A Table」（新娘左右鏡射，兩人才不會一模一樣），循環 3 次蓋滿 12 秒
    groom = dict(segs=[
        S("groom", "seated_table_idle", 0, None, loops=3.0, seat=SEAT, label="坐著、雙手放桌上（Seated Idle With Hands On A Table）"),
    ], anchor=(0.0, G07, 45.0), mod=groom_mod() if FINAL else None)
    bride = dict(segs=[
        S("bride", "seated_table_idle", 0, None, loops=3.0, seat=SEAT, mirror=True, label="坐著、雙手放桌上（Seated Idle With Hands On A Table，鏡射）"),
    ], anchor=(0.0, B07, -45.0), mod=bride_mod() if FINAL else None)
    props = [
        dict(kind="cyl", name="圓桌＋落地桌巾", c=[1.85, -1.25], r=0.485, z0=0.0, z1=0.734, color="#FBF6EE", opacity=0.4),
        dict(kind="box", name="新郎椅（椅面 0.46）", min=[1.205, -1.025, 0.0], max=[1.625, -0.605, 0.46], color="#ECB0AC", opacity=0.5),
        dict(kind="box", name="新娘椅（椅面 0.46）", min=[2.075, -1.025, 0.0], max=[2.495, -0.605, 0.46], color="#ECB0AC", opacity=0.5),
        dict(kind="cyl", name="主餐大盤", c=[1.81, -1.16], r=0.15, z0=0.734, z1=0.752, color="#FFFDF8", opacity=0.8),
        dict(kind="cyl", name="新郎酒杯", c=[1.62, -1.02], r=0.046, z0=0.733, z1=0.91, color="#6E1424", opacity=0.7),
        dict(kind="cyl", name="新娘酒杯", c=[2.08, -1.02], r=0.046, z0=0.733, z1=0.91, color="#6E1424", opacity=0.7),
        dict(kind="cyl", name="紅酒瓶", c=[1.56, -1.47], r=0.037, z0=0.734, z1=1.041, color="#24331F", opacity=0.8),
        dict(kind="box", name="畫架＋小黑板", min=[2.35, -1.44, 0.0], max=[2.94, -0.86, 1.24], color="#2F3D35", opacity=0.35),
    ]
    cam = dict(pos=[1.98, -3.95, 1.36], aim=[1.99, -1.05, 0.97], lens=38.0, sensor=36.0, aspect=16 / 9)
    return dict(id="07", title="⑦ 燭光晚餐", dur=12.0, chars=dict(bride=bride, groom=groom), props=props, cam=cam, skirt=None, post=post,
                note="兩人坐在圓桌後面（白色圓柱是落地桌巾），腿和椅子大多被桌巾擋住。底是「雙手放桌上靜坐」，只有拿叉子、拿杯子的手照劇情動。",
                decide=DECIDE_FINAL if FINAL else DECIDE_G1R6)


DECIDE_G1R6 = [
    "【第 1 關第三次換底（第 3 關第 2 輪回饋「太多動作不是正常人類的動作，比最原初的版本還差」）】",
    "兩人都改用「Seated Idle With Hands On A Table」：雙手平放桌上、身體穩，原片只有很小的晃動（新娘左右鏡射）。上一版的「坐著聊天」「坐著指東西」「坐下喝飲料」"
    "原片本身就有比手勢、仰頭喝罐裝飲料的大動作，和劇情要的手部動作互相拉扯，所以拿掉。",
    "原片兩人低頭看桌子 26°，第 2 關由看人的微調抬起來；拿叉子、拿杯子都在第 2 關做（只動那一隻手）。",
]

DECIDE_FINAL = [
    "【第 2 關（第三次重做），灰線是 Mixamo 原樣「雙手放桌上靜坐」】做法照最早那版看起來像人的地方：兩人坐著幾乎不動，只有拿東西的那隻手在動，"
    "手的路線是平順的曲線（經過每個點、中間不停），不再一段一段地停頓。兩人都有呼吸。",
    "新郎餵食（左手）：0.4 秒拿起叉子 → 0.75～1.2 秒在盤上叉一口（叉尖往下）→ 1.9 秒送到新娘嘴前 2.5 cm、停到 2.3 秒（新娘 2.1 秒湊過去咬）→ 3.1 秒收回、3.4 秒把叉子放回桌上。"
    "餵的時候上身往她那邊傾 10°，新娘往叉子傾 7°。右手一直平放在桌上。",
    "酒杯（新郎左手、新娘右手，新娘晚 0.08 秒）：4.45 秒伸手 → 5.3 秒拿起自己面前的杯子 → 5.85 秒到胸前 → 6.45～6.62 秒在桌子中間碰杯 → 7.3～8.5 秒舉向鏡頭 → "
    "8.95～9.95 秒拿到嘴邊喝（杯緣靠下唇，杯子傾 30→44°）→ 10.5 秒拿在胸前到結尾。杯子一直直立（喝的時候除外）。",
    "頭：新郎 看新娘 → 看盤子 → 餵的時候看她的嘴 → 看著她 → 拿杯看杯子 → 碰杯看她 → 舉杯看鏡頭 → 喝的時候看前方 → 結尾看鏡頭；"
    "新娘 看新郎 → 看叉子 → 看回新郎 → 看自己的杯子 → 碰杯看新郎 → 舉杯看鏡頭 → 喝的時候看前方 → 結尾看著新郎。",
    "上一版有的「新娘咬完右手遮嘴笑」拿掉了（看起來像手扶著額頭），改成咬完坐回去笑。",
]
