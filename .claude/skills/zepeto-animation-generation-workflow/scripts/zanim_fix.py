# ZEPETO 動畫共用（2026-10-12 由 b12_fix 搬來，內容沒改）
# 接縫與腳底的修正（套用 Mixamo 之後的「微調」層，不改動作結構）：
#   match_phase：兩段之間找腿部姿勢最像的那一格當剪接點（走路 → 停下、起步 → 走路），接縫不再一腳在地、一腳在空中硬漸變
#   foot_lock：著地的那幾格把腳踝釘在同一點、用兩節腿 IK 補膝蓋（業界叫 foot locking / foot planting）；順便把陷進地板的腳抬回地面
import math
from mathutils import Vector, Quaternion, Matrix
import zanim_lib as L
mr = L.mr

LEG = ("UpperLeg", "LowerLeg", "Foot", "ToeBase")


def leg_sig(tgt, clip, f):
    """一格的腿部特徵：兩腳腳踝相對骨盆的位置（扣掉面向）＋腿各節相對父骨頭的旋轉"""
    R, h, y = clip["R"][f], clip["hips"][f], clip["yaw"][f]
    Hd = tgt.fk(R, h); Yi = Quaternion((0, 0, 1), -y)
    pos = [Yi @ (Hd[f"J_Bip_{s}_Foot"] - h) for s in "LR"]
    Lp, _z = mr.local_pose(tgt, R, h, y)
    rot = [Lp[f"J_Bip_{s}_{b}"] for s in "LR" for b in LEG[:3]]
    return pos, rot


def sig_dist(a, b):
    dp = sum((p - q).length for p, q in zip(a[0], b[0]))                 # m
    dr = sum(p.rotation_difference(q).angle for p, q in zip(a[1], b[1]))  # rad
    return dp + 0.05 * dr


def match_phase(tgt, A, a_frames, B, b_frames):
    """→ (A 的格, B 的格, 距離)：A 播到第 a 格接 B 的第 b 格最順"""
    sa = {f: leg_sig(tgt, A, f) for f in a_frames}
    sb = {f: leg_sig(tgt, B, f) for f in b_frames}
    best = min(((sig_dist(sa[a], sb[b]), a, b) for a in a_frames for b in b_frames))
    return best[1], best[2], round(best[0], 4)


# ── 兩節腿 IK ──
def leg_ik(tgt, R, hips, side, ankle, pole):
    """腳踝到 ankle、膝蓋往 pole 方向彎；腳掌、腳趾保持原本的世界轉向（鞋底不跟著翻）"""
    s = side
    U, Lo, F, T = (f"J_Bip_{s}_{b}" for b in LEG)
    keepF, keepT = R[F], R[T]
    Hd = tgt.fk(R, hips)
    S = Hd[U]; a = (tgt.rest_h[Lo] - tgt.rest_h[U]).length; b = (tgt.rest_h[F] - tgt.rest_h[Lo]).length
    v = ankle - S; d = max(1e-4, min(v.length, (a + b) * 0.9995)); dn = v.normalized()
    ca = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d)))
    p = pole - dn * pole.dot(dn)
    p = p.normalized() if p.length > 1e-6 else Vector((0, -1, 0))
    E = S + (dn * ca + p * math.sqrt(max(0.0, 1 - ca * ca))) * a
    R = mr.rotate_subtree(tgt, R, U, (Hd[Lo] - S).rotation_difference(E - S))
    Hd = tgt.fk(R, hips)
    R = mr.rotate_subtree(tgt, R, Lo, (Hd[F] - Hd[Lo]).rotation_difference(S + dn * d - Hd[Lo]))
    R = dict(R); R[F] = keepF; R[T] = keepT
    return R


def foot_lock(tgt, poses, pts, z_on=0.010, v_on=0.30, ramp=3, fps=30, gap_max=12, step_h=0.012):
    """poses：[(R, hips)] → 新的 poses、每格的鎖定權重。
    著地＝鞋底最低點 ≤ z_on 且腳踝水平速度 ≤ v_on（m/s）的連續格；每段著地把腳踝 XY 釘在「這段裡最慢那一格」的位置，
    頭尾 ramp 格漸入漸出。所有格：鞋底低於地面就把腳踝抬回來（腳不陷地）。
    z_on、v_on 也可以給每格一個值的清單（2026-10-13 B1→B2 新娘：只在快轉身、起步那幾格放寬門檻；
    分兩次鎖的話兩次的釘點不同，交界那一格會跳 9～15 cm）"""
    n = len(poses)
    zz = list(z_on) if isinstance(z_on, (list, tuple)) else [z_on] * n
    vv = list(v_on) if isinstance(v_on, (list, tuple)) else [v_on] * n
    info = {"L": [], "R": []}
    for s in "LR":
        anc = []; low = []
        for R, h in poses:
            Hd = tgt.fk(R, h)
            anc.append(Hd[f"J_Bip_{s}_Foot"].copy())
            so = L.soles(tgt, R, h, [(b, c) for b, c in pts if f"_{s}_" in b])
            low.append(min(p.z for p in so[s]))
        spd = [((anc[min(i + 1, n - 1)] - anc[max(i - 1, 0)]).xy.length * fps / 2) for i in range(n)]
        on = [low[i] <= zz[i] and spd[i] <= vv[i] for i in range(n)]
        # 連續著地區間（太短的不算，1～2 格的雜訊）
        spans = []; i = 0
        while i < n:
            if on[i]:
                j = i
                while j + 1 < n and on[j + 1]:
                    j += 1
                if j - i >= 3:
                    spans.append((i, j))
                i = j + 1
            else:
                i += 1
        # 每段著地各自的權重；兩段的漸入漸出重疊時按權重混合（2026-10-12：以前直接換成權重大的那段，
        # 換段那一格腳踝目標瞬間跳到另一段的位置，起步時左腳一格滑 8 cm）
        parts = [[] for _ in range(n)]
        for a, b in spans:
            k = min(range(a, b + 1), key=lambda q: spd[q])
            xy = anc[k].xy.copy()
            for q in range(max(0, a - ramp), min(n, b + ramp + 1)):
                if q < a:
                    wq = (q - (a - ramp - 1)) / (ramp + 1)
                elif q > b:
                    wq = ((b + ramp + 1) - q) / (ramp + 1)
                else:
                    wq = 1.0
                parts[q].append((mr._smooth(wq), xy))
        # 兩段著地中間的短空檔（≤ gap_max 格）：Mixamo 在接縫常讓腳貼地拖過去，鎖腳會變成一格跳好幾公分
        # → 空檔裡整格鎖住、腳踝從前一段的位置平順移到下一段，同時抬起一點（像小碎步），不要貼地拖
        lift = [0.0] * n
        xys = []
        for a, b in spans:
            k = min(range(a, b + 1), key=lambda q: spd[q]); xys.append(anc[k].xy.copy())
        for (a1, b1), (a2, b2), xa, xb in zip(spans, spans[1:], xys, xys[1:]):
            if a2 - b1 - 1 <= gap_max:
                for q in range(b1 + 1, a2):
                    u = mr._smooth((q - b1) / (a2 - b1))
                    parts[q] = [(1.0, xa.lerp(xb, u))]
                    lift[q] = step_h * math.sin(math.pi * (q - b1) / (a2 - b1)) * min(1.0, (xb - xa).length / 0.02)
        w = [0.0] * n; tgt_xy = [None] * n
        for q in range(n):
            if parts[q]:
                full = [p for p in parts[q] if p[0] >= 0.999]        # 正在著地的那段優先，不被鄰段拉走
                if full:
                    parts[q] = full[:1]
                sw = sum(p[0] for p in parts[q])
                if sw > 1e-6:
                    tgt_xy[q] = sum((p[1] * p[0] for p in parts[q]), Vector((0, 0))) / sw
                    w[q] = min(1.0, sw)
        info[s] = dict(anc=anc, low=low, w=w, xy=tgt_xy, spans=spans, lift=lift)
    out = []
    for i, (R, h) in enumerate(poses):
        for s in "LR":
            I = info[s]
            a0 = I["anc"][i]
            t = a0.copy()
            if I["w"][i] > 0:
                t.x += (I["xy"][i].x - a0.x) * I["w"][i]; t.y += (I["xy"][i].y - a0.y) * I["w"][i]
            if I["low"][i] < 0:
                t.z -= I["low"][i]
            if I["lift"][i] > 0:                              # 小碎步抬腳（只往上補到 lift，原本就比較高就不動）
                t.z += max(0.0, I["lift"][i] - max(0.0, I["low"][i]))
            if (t - a0).length > 1e-5:
                Hd = tgt.fk(R, h)
                knee = Hd[f"J_Bip_{s}_LowerLeg"]
                mid = (Hd[f"J_Bip_{s}_UpperLeg"] + a0) / 2
                pole = (knee - mid)
                if pole.length < 1e-3:                       # 腿打直：膝蓋往角色前方彎
                    pole = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0))
                R = leg_ik(tgt, R, h, s, t, pole)
        out.append((R, h))
    return out, {s: dict(spans=info[s]["spans"]) for s in "LR"}


def ground(tgt, poses, pts, win=8, smooth=6, skin=0.0015):
    """整個人貼地（2026-10-12 換 v8 身體後走路兩腳一直離地 1.5 cm）：每格取兩腳鞋底較低的那個，
    前後 win 格取最小（走路時一定有一隻腳踩地），再平滑 smooth 格，骨盆往下放到最低的腳離地 skin。→ (poses, 每格位移)"""
    n = len(poses); m = []
    for R, h in poses:
        so = L.soles(tgt, R, h, pts)
        m.append(min(min(p.z for p in so["L"]), min(p.z for p in so["R"])))
    rm = [min(m[max(0, i - win):i + win + 1]) for i in range(n)]
    off = []
    for i in range(n):
        ws = rm[max(0, i - smooth):i + smooth + 1]
        off.append(skin - sum(ws) / len(ws))
    out = []
    for (R, h), o in zip(poses, off):
        h2 = h.copy(); h2.z += o; out.append((R, h2))
    return out, off


# ════════ 片段加工（2026-10-13，B1→B2、B0 正式版） ════════
def retime(c, k):
    """動畫放慢／加快：k＜1 變慢（格數變多）。每格照原片內插（骨頭 slerp、骨盆 lerp）。
    例：女生走路每秒 0.815 m、新郎 0.70 m → 新娘的走路 k＝0.854 才能和新郎並排走"""
    n0 = c["n"]; n = int(round((n0 - 1) / k)) + 1
    R, H, Y = [], [], []
    for j in range(n):
        x = min(j * k, n0 - 1); i = min(int(x), n0 - 2); f = x - i
        R.append({b: c["R"][i][b].slerp(c["R"][i + 1][b], f) for b in c["R"][i]})
        H.append(c["hips"][i].lerp(c["hips"][i + 1], f)); Y.append(c["yaw"][i] + (c["yaw"][i + 1] - c["yaw"][i]) * f)
    return dict(c, n=n, R=R, hips=H, yaw=Y)


def amp_turn(tgt, c, total=90.0, a=0, b=None):
    """邊走邊轉的片段，把轉向放大到 total 度（路線跟著彎）。
    Mixamo 的 Walking Turn 90 Left 套上來骨盆只轉 36°、路線幾乎是直的（2026-10-13 量）：
    每格多轉 e＝(total／原本轉的角度 − 1)×(到這格為止轉的角度)，骨頭整體繞 Z 轉 e、骨盆每格的位移也轉 e 再累加。
    a～b：只取這幾格（含）"""
    b = c["n"] - 1 if b is None else b
    def hy(R):
        v = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0))
        return math.atan2(v.x, -v.y)
    ys = [hy(c["R"][i]) for i in range(a, b + 1)]
    turn = ys[-1] - ys[0]
    g = (math.radians(total) / turn - 1.0) if abs(turn) > 1e-3 else 0.0
    R, H, Y = [], [], []
    for j, i in enumerate(range(a, b + 1)):
        e = g * (ys[j] - ys[0]); q = Quaternion((0, 0, 1), e)
        R.append({k: q @ r for k, r in c["R"][i].items()})
        if j == 0:
            H.append(c["hips"][i].copy())
        else:
            d = c["hips"][i] - c["hips"][i - 1]; em = g * ((ys[j] + ys[j - 1]) / 2 - ys[0])
            dd = Quaternion((0, 0, 1), em) @ Vector((d.x, d.y, 0))
            H.append(Vector((H[-1].x + dd.x, H[-1].y + dd.y, c["hips"][i].z)))
        Y.append(c["yaw"][i] + e)
    return dict(c, n=len(R), R=R, hips=H, yaw=Y), dict(turn_deg=round(math.degrees(turn), 1), gain=round(g + 1, 2))


def bend(c, deg, a, b):
    """讓一段移動中的動畫（例：Stop Walking）在第 a～b 格之間平順轉彎 deg 度（正＝左轉），之後維持新方向；
    骨頭整體繞 Z 轉、骨盆每格的位移跟著轉再累加（腳步不變）。
    2026-10-13 B2：新郎減速時要等新娘從他和餐檯之間超過去，才往餐檯斜過去 → 只在停下動作的後半段轉"""
    g = math.radians(deg)
    def e(i):
        if i <= a:
            return 0.0
        if i >= b:
            return g
        x = (i - a) / (b - a)
        return g * x * x * (3 - 2 * x)
    R, H, Y = [], [], []
    for i in range(c["n"]):
        q = Quaternion((0, 0, 1), e(i))
        R.append({k: q @ r for k, r in c["R"][i].items()})
        if i == 0:
            H.append(c["hips"][0].copy())
        else:
            d = c["hips"][i] - c["hips"][i - 1]
            dd = Quaternion((0, 0, 1), (e(i) + e(i - 1)) / 2) @ Vector((d.x, d.y, 0))
            H.append(Vector((H[-1].x + dd.x, H[-1].y + dd.y, c["hips"][i].z)))
        Y.append(c["yaw"][i] + e(i))
    return dict(c, R=R, hips=H, yaw=Y)


# ════════ 蓬裙（2026-10-13 新娘禮服 bride-blush-ballgown） ════════
# 裙子（含外層紗）離地 z 高度 → 離骨盆垂直軸最遠多少 m（站姿量的，背景 Blender 實測 Gown_Skirt／Gown_Overskirt）
GOWN_PROF = ((0.0, 0.335), (0.1, 0.335), (0.2, 0.329), (0.3, 0.318), (0.4, 0.318), (0.5, 0.31), (0.6, 0.289), (0.7, 0.241), (0.8, 0.157), (0.86, 0.0))


def prof_r(z, prof=GOWN_PROF):
    """高度 z 的裙子半徑（線性內插；裙子上緣以上＝0）"""
    if z <= prof[0][0]:
        return prof[0][1]
    for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
        if z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 0.0


def _chain(tgt, root):
    out = []
    for n in tgt.keys:
        p = n
        while p is not None and p != root:
            p = tgt.parent[p]
        if p == root:
            out.append(n)
    return out


def _arm_pts(tgt, R, Hd, s):
    pts = [Hd[f"J_Bip_{s}_Hand"], (Hd[f"J_Bip_{s}_LowerArm"] + Hd[f"J_Bip_{s}_Hand"]) / 2]
    for f in ("Thumb3", "Index3", "Middle3", "Little3", "Index1", "Little1"):
        n = f"J_Bip_{s}_{f}"
        pts.append(tgt.tail(R, Hd, n) if f.endswith("3") else Hd[n])
    return pts


def skirt_arms(tgt, poses, margin=0.03, max_deg=35.0, smooth=5, prof=GOWN_PROF, skip=(), elbow_k=0.0):
    """手垂下時手掌會沒入蓬裙兩側（服裝端提醒）→ 每格把整隻手臂繞肩膀往外擺（外展），擺到手掌、手指離裙面 margin m 為止。
    參考：穿禮服時手臂稍微離開身體、手肘微彎（fstoppers.com/education/tips-model-bride-be-41925）。
    elbow_k：外展每 1 度、手肘再往前彎幾度（手抬高到裙子較窄的地方，外展就不用那麼大）。
    角度先逐格算、再取前後 smooth 格的最大值並平均（不會一格一格跳）。skip：不處理的格子範圍 [(a, b)]（手握著東西那幾段；IK 做完再跑一次時用）。
    回傳 (poses, {L/R: 最大外展角})"""
    chains = {s: _chain(tgt, f"J_Bip_{s}_UpperArm") for s in "LR"}
    fore = {s: _chain(tgt, f"J_Bip_{s}_LowerArm") for s in "LR"}

    def turn(R, h, s, deg, k, fwd):
        """外展 deg 度（繞肩、軸 k）＋手肘往前彎 elbow_k×deg 度（繞手肘、軸 down×fwd）→ 新的 R"""
        R = dict(R)
        if elbow_k > 0:
            Hd = tgt.fk(R, h); qe = Quaternion(down.cross(fwd).normalized(), math.radians(elbow_k * deg))
            for b in fore[s]:
                R[b] = qe @ R[b]
        q = Quaternion(k, math.radians(deg))
        for b in chains[s]:
            R[b] = q @ R[b]
        return R
    down = Vector((0, 0, -1)); n = len(poses)
    ang = {s: [0.0] * n for s in "LR"}; axes = {s: [None] * n for s in "LR"}; fws = {s: [None] * n for s in "LR"}
    skipped = lambda i: any(a <= i <= b for a, b in skip)
    for i, (R, h) in enumerate(poses):
        Hd = tgt.fk(R, h); c = Vector((h.x, h.y, 0))
        Rh = R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()
        for s, sg in (("L", 1), ("R", -1)):
            side = Rh @ Vector((sg, 0, 0)); side.z = 0; side.normalize()
            k = down.cross(side).normalized(); axes[s][i] = k
            if skipped(i):
                continue
            fw = Rh @ Vector((0, -1, 0)); fw.z = 0; fw.normalize(); fws[s][i] = fw
            for deg in range(0, int(max_deg) + 1):
                R2 = turn(R, h, s, deg, k, fw); H2 = tgt.fk(R2, h)
                P = [p for p in _arm_pts(tgt, R2, H2, s) if prof_r(p.z, prof) > 0]
                if not P or max(prof_r(p.z, prof) + margin - (Vector((p.x, p.y, 0)) - c).length for p in P) <= 0:
                    break
            ang[s][i] = float(deg)
    out = [dict(R) for R, _h in poses]
    mx = {}
    for s in "LR":
        a = ang[s]
        m = [max(a[max(0, i - smooth):i + smooth + 1]) for i in range(n)]
        m = [sum(m[max(0, i - smooth):i + smooth + 1]) / len(m[max(0, i - smooth):i + smooth + 1]) for i in range(n)]
        if skip:                                           # 指定不動的格子（手握著東西）歸零，前後再平均一次 → 進出那幾格漸變
            m = [0.0 if skipped(i) else v for i, v in enumerate(m)]
            m = [sum(m[max(0, i - smooth):i + smooth + 1]) / len(m[max(0, i - smooth):i + smooth + 1]) if not skipped(i) else 0.0 for i in range(n)]
        mx[s] = round(max(m), 1); skirt_arms.last[s] = m
        for i in range(n):
            if m[i] < 0.05:
                continue
            if fws[s][i] is None:
                Rh = out[i]["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted(); f_ = Rh @ Vector((0, -1, 0)); f_.z = 0; fws[s][i] = f_.normalized()
            out[i] = turn(out[i], poses[i][1], s, m[i], axes[s][i], fws[s][i])
    return [(R, h) for R, (_r, h) in zip(out, poses)], mx


skirt_arms.last = {}                                       # 上一次每格的外展角（看分布用）


def skirt_gap(tgt_g, poses_g, poses_b, prof=GOWN_PROF, limb=0.06):
    """新郎（骨頭中心＋肢體半徑 limb）離新娘裙面最近多少 m（負＝穿進裙子）。只用骨架算，很快，調站位用；最後仍以網格實量為準。
    回傳 (最近, 第幾格)"""
    best = (9.0, 0)
    for i, ((R, h), (_Rb, hb)) in enumerate(zip(poses_g, poses_b)):
        Hd = tgt_g.fk(R, h); c = Vector((hb.x, hb.y, 0))
        pts = list(Hd.values()) + [tgt_g.tail(R, Hd, f"J_Bip_{s}_{b}") for s in "LR" for b in ("ToeBase", "Middle3")]
        for p in pts:
            r = prof_r(p.z, prof)
            if r <= 0:
                continue
            d = (Vector((p.x, p.y, 0)) - c).length - r - limb
            if d < best[0]:
                best = (d, i)
    return round(best[0], 3), best[1]


def _hyaw(tgt, R):
    v = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0))
    return math.atan2(v.x, -v.y)


def pivot_turn(tgt, poses, ia, ib, first="R", lift=0.035, phase_a=(0.0, 0.5), phase_b=(0.52, 1.0), sign=0):
    """站著小角度轉身（取代 Mixamo 的轉身動作：那幾支整段是運動員預備站姿，套到 30° 左右的小轉身會變成雙腳小碎步／微蹲）。
    第 ia 格的姿勢 → 第 ib 格的姿勢（兩格都是站穩的；中間原本可能是兩段的漸變）之間：
      身體（全部骨頭）照 smoothstep 從 ia 的面向轉到 ib 的面向，骨盆水平位置跟著內插；
      先跨的那隻腳（first，往右轉就是右腳）在 phase_a 時段抬起 lift m、移到 ib 的位置與朝向，另一隻腳在 phase_b 時段跟上；
      任何時候最多一隻腳離地，腿用兩節 IK 對到腳踝。
    sign：+1 往左轉、−1 往右轉、0 走近的那邊。
    參考：站著轉向旁邊的人，是先把轉向那一側的腳打開一小步、再把另一隻腳帶過來（pivot step）。回傳新的 poses"""
    out = list(poses)
    Ra, ha = poses[ia]; Rb, hb = poses[ib]
    Ha, Hb = tgt.fk(Ra, ha), tgt.fk(Rb, hb)
    ya, yb = _hyaw(tgt, Ra), _hyaw(tgt, Rb); dy = (yb - ya + math.pi) % (2 * math.pi) - math.pi
    if sign and dy * sign < 0:                            # 指定往哪邊轉（+1 左、−1 右）：接近 180° 時兩邊一樣近，要明確指定
        dy += sign * 2 * math.pi
    other = "L" if first == "R" else "R"
    sched = {first: phase_a, other: phase_b}
    feet = {s: dict(pa=Ha[f"J_Bip_{s}_Foot"].copy(), pb=Hb[f"J_Bip_{s}_Foot"].copy(),
                    fa=Ra[f"J_Bip_{s}_Foot"], fb=Rb[f"J_Bip_{s}_Foot"], ta=Ra[f"J_Bip_{s}_ToeBase"], tb=Rb[f"J_Bip_{s}_ToeBase"]) for s in "LR"}
    sm = lambda x: (lambda y: y * y * (3 - 2 * y))(max(0.0, min(1.0, x)))
    n = max(1, ib - ia)
    for i in range(ia, ib + 1):
        x = (i - ia) / n; k = sm(x)
        R, h = poses[i]
        q = Quaternion((0, 0, 1), ya + dy * k - _hyaw(tgt, R))
        R = {b: q @ r for b, r in R.items()}
        hx = ha.lerp(hb, k); h2 = Vector((hx.x, hx.y, h.z))
        fw = Vector((math.sin(ya + dy * k), -math.cos(ya + dy * k), 0))
        for s in "LR":
            p0, p1 = sched[s]; ks = sm((x - p0) / (p1 - p0)); f = feet[s]
            tgt_p = f["pa"].lerp(f["pb"], ks)
            tgt_p.z = f["pa"].z + (f["pb"].z - f["pa"].z) * sm((ks - 0.75) / 0.25)     # 高度到最後 1/4 才接到終點（終點那格可能已經是起步、腳抬起來：太早接會落地後浮著）
            tgt_p += Vector((0, 0, lift * math.sin(math.pi * ks) ** 0.5))             # 開根號：起落兩端也離地（跨步長時腳快落地還在水平移動，會被量成滑步）   # 開根號：起落兩端也離地（跨步長時腳快落地還在水平移動，會被量成滑步）
            R = leg_ik(tgt, R, h2, s, tgt_p, fw)
            R[f"J_Bip_{s}_Foot"] = f["fa"].slerp(f["fb"], ks); R[f"J_Bip_{s}_ToeBase"] = f["ta"].slerp(f["tb"], ks)
        out[i] = (R, h2)
    return out


def level_head(tgt, poses, max_up=5.0, split=0.4):
    """頭往上仰超過 max_up 度的部分壓回來（脖子分 split、頭分其餘），往下看不動。
    2026-10-13 使用者：新娘一般走路時頭往斜上方看（Mixamo Female Walk／Stop Walking 原片頭仰 13～18°，新郎的 Walking 只有 1～6°）→ 新娘全片套用。
    回傳 (poses, 原本最大仰角)"""
    out = []; worst = -90.0
    for R, h in poses:
        q = R["J_Bip_C_Head"] @ tgt.rest_q["J_Bip_C_Head"].inverted()
        f = q @ Vector((0, -1, 0)); p = math.degrees(math.asin(max(-1.0, min(1.0, f.z)))); worst = max(worst, p)
        if p <= max_up:
            out.append((R, h)); continue
        fh = Vector((f.x, f.y, 0)); fh = fh.normalized() if fh.length > 1e-6 else Vector((0, -1, 0))
        axis = fh.cross(Vector((0, 0, 1))).normalized()                    # 頭的右手方向：繞它轉負角＝低頭
        d = math.radians(p - max_up)
        R = dict(R)
        R["J_Bip_C_Neck"] = Quaternion(axis, -d * split) @ R["J_Bip_C_Neck"]
        R["J_Bip_C_Head"] = Quaternion(axis, -d) @ R["J_Bip_C_Head"]
        out.append((R, h))
    return out, round(worst, 1)
