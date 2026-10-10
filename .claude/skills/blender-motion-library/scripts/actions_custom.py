# 擴充動作庫：由 blender-animation-append 新增。actions.py 載入後會把 CUSTOM_ACTIONS 併進 ACTIONS／ACT。
#
# 規則（細節見 references/adding-actions.md）：
#   - 一個動作＝一個函式 t∈[0,1) → 姿勢 dict，頭尾相接（t=0 和 t→1 的姿勢一樣）。
#   - 可直接用 actions.py 的工具：arms_down、legs、breathe、seg、bump、ease、s、bs、TUNE、SMILE。
#   - 手要碰到身體、臉、另一隻手時，用 ik=[(side, 手腕, 手肘方向, 指尖方向)]，座標用 bs(...) 包起來（會依體型縮放）。
#   - 代號用英文小寫、不可和既有 30 個重複；中文名稱是網頁上顯示的名字。
#   - 新增後一定要跑 run_analyse（穿模／腳底／轉速）並通過，才算入庫。
#
# ── 2026-10-06 新增（開場影片 V12）：walk_fwd 往前走、pull_walk 拉著東西往前走、toast 舉杯乾杯、taste 品嚐美食 ──
# 四個都是「工廠函式」：呼叫時給參數（方向、距離、步數、秒數…）回傳 fn(t)，CUSTOM_ACTIONS 登記的是預設參數的那一份。
# 情境要對時間就自己呼叫工廠，例：W = walk_fwd(dist=1.5, steps=4, dur=3.2, dirx=1, origin=(-2.0, 0.3))；
# 第 f 格（30fps）用 pose_frame(ARM, W(f / (3.2 * 30)))。
#
# ── 2026-10-06 新增（開場影片 V12 互動）：第 6 節 sneak_hand 偷牽手、bonked 被敲抱頭、mallet_bonk 玩具槌敲頭、feed 餵食、fed 被餵、
#    glass_pick 相視一笑拿酒杯、toast_sit 坐姿乾杯、sip 喝一口——劇情用的單次動作（不循環），手臂用 _arm_set 直接寫 FK（說明見第 6 節開頭）。
#    第 7 節（路人甲）：walk_in_photo 走進來舉手機拍照、oops_bow 尷尬抓頭鞠躬、turn_exit 轉身走出去——腿也直接寫 FK（_leg_set），
#    可以邊走邊轉、原地換步轉身不滑。
#
# ⚠️ 擺位置：
#   - walk_fwd／pull_walk 的位置與朝向一律用參數 origin／dirx（或 rz）給，不要事後改回傳的 root／rz（腳會滑）。
#   - toast／taste 的手 IK 目標跟著 Hips 走，事後改 root／rz 可以（腿沒有鎖，直接整個人搬過去）。
#   - 既有的 feet 動作（idle、bow…）要搬到別的位置用 place(P, x, y, rz)；直接改 root 腳會留在原點。
import math
from mathutils import Vector, Matrix


# ════════════════════════ 共用工具 ════════════════════════

def _kof(arm):
    """體型比例（和 actions.BODY_S 同算法，但可以給別的骨架）"""
    return arm.data.bones["J_Bip_C_Head"].head_local.z / 1.386


def _V(k, x, y, z):
    """新娘座標 × 體型比例 k（和 actions.bs 一樣，但體型取自工廠綁定的骨架）"""
    return Vector((x * k, y * k, z * k))


def _who(arm):
    return arm.name[:-len("_Armature")] if arm.name.endswith("_Armature") else WHO


def _rotm(axis, deg):
    if isinstance(axis, str):
        axis = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}[axis]
    return Matrix.Rotation(math.radians(deg), 4, Vector(axis).normalized())


def _fk(arm, P, key):
    """姿勢 dict 的身體旋轉 → 骨頭 key 的「rest → 姿勢」變換（骨架空間）。
    和 apply_pose 一樣：照 BODY_ORDER（父骨先）、世界軸、繞當下的骨頭頭部轉；只算 key 和它的祖先"""
    B = arm.data.bones; tgt = B[bn(key)]
    anc = {b.name for b in tgt.parent_recursive} | {tgt.name}
    M = Matrix.Identity(4)
    for k in BODY_ORDER:
        b = bn(k)
        if b not in anc:
            continue
        for axis, deg in P.get(k, []):
            pv = M @ B[b].head_local
            M = Matrix.Translation(pv) @ _rotm(axis, deg) @ Matrix.Translation(-pv) @ M
    return M


def _arm_sim(arm, P, side, W, pole, twist=0.0):
    """在骨架空間模擬 pose_lib.ik_arm（不給指尖方向，手掌順著前臂）＋ twist_forearm，回傳手骨的姿勢矩陣。
    算法和 pose_lib 一模一樣（最小旋轉對準），所以拿來預先算「手上的道具點會落在哪」"""
    B = arm.data.bones
    ua, la, hd = (f"J_Bip_{side}_{n}" for n in ("UpperArm", "LowerArm", "Hand"))
    Mu, Ml, Mh = _fk(arm, P, f"{side}_UpperArm"), _fk(arm, P, f"{side}_LowerArm"), _fk(arm, P, f"{side}_Hand")
    L1 = (B[la].head_local - B[ua].head_local).length; L2 = (B[hd].head_local - B[la].head_local).length
    S = Mu @ B[ua].head_local
    W = Vector(W); Pp = Vector(pole)
    v = W - S; d = max(1e-4, min(v.length, (L1 + L2) * 0.999)); dr = v.normalized()
    a = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    pp = Pp - S; pp = pp - dr * pp.dot(dr)
    if pp.length < 1e-6:
        pp = Vector((0, 0, -1)) - dr * dr.z
    pp.normalize()
    E = S + dr * math.cos(a) * L1 + pp * math.sin(a) * L1

    def aim(Ms, bone, tgt):
        h = Ms[0] @ B[bone].head_local; cur = (Ms[0] @ B[bone].tail_local) - h; want = Vector(tgt) - h
        if want.length < 1e-6:
            return Ms
        cur.normalize(); want.normalize()
        ang = cur.angle(want)
        if ang < 1e-5:
            return Ms
        ax = cur.cross(want)
        if ax.length < 1e-8:
            return Ms
        R = Matrix.Translation(h) @ Matrix.Rotation(ang, 4, ax.normalized()) @ Matrix.Translation(-h)
        return [R @ m for m in Ms]

    Mu, Ml, Mh = aim([Mu, Ml, Mh], ua, E)
    Ml, Mh = aim([Ml, Mh], la, S + dr * d)
    if abs(twist) > 1e-3:
        axis = (Mh.to_3x3() @ B[hd].matrix_local.to_3x3()).col[1].normalized()
        h = Ml @ B[la].head_local
        R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(twist * 0.5), 4, axis) @ Matrix.Translation(-h)
        Ml, Mh = R @ Ml, R @ Mh
        h = Mh @ B[hd].head_local
        Mh = Matrix.Translation(h) @ Matrix.Rotation(math.radians(twist * 0.5), 4, axis) @ Matrix.Translation(-h) @ Mh
    return Mh @ B[hd].matrix_local


def _twist_for(Hm, want):
    """要讓手骨局部 Z（拇指那側＝杯子往上）轉到 want 方向，前臂要扭幾度"""
    Y = Hm.col[1].xyz.normalized(); Z0 = Hm.col[2].xyz.normalized()
    w = Vector(want); w = w - Y * w.dot(Y)
    if w.length < 1e-6:
        return 0.0
    w.normalize()
    return math.degrees(math.atan2(Y.dot(Z0.cross(w)), Z0.dot(w)))


def _solve_hand(arm, P, side, prop, off, pole, thumb, iters=5):
    """手上的道具點（手骨局部 off）要到骨架空間的 prop、拇指朝 thumb → (手腕目標, twist 度數)"""
    prop = Vector(prop); W = prop.copy(); tw = 0.0
    for _ in range(iters):
        tw = _twist_for(_arm_sim(arm, P, side, W, pole, 0.0), thumb)
        pt = _arm_sim(arm, P, side, W, pole, tw) @ Vector(off)
        W = W + (prop - pt)
    return W, tw


# 擴充手勢（只加不改既有的）：捏東西前手指先半張開（taste 用：relax → pinch_open → pinch，兩兩內插頭尾相接）
HANDS.setdefault("pinch_open", dict(Thumb=(8, 10, 8), Index=(14, 18, 12), Middle=(14, 20, 14), Ring=(18, 24, 16), Little=(22, 28, 18), spread=2))

# 手上道具的掛點（新娘尺寸、右手骨局部座標；左手 x 取負；乘體型比例）。手骨局部：Y＝手指方向、Z＝拇指那側、右手 -X／左手 +X＝掌心
OFF_GRIP = (-0.025, 0.060, 0.000)      # grip 手勢握住的杯身中心（香檳杯，杯子往上＝局部 +Z）
OFF_PINCH = (-0.054, 0.072, 0.037)     # pinch 手勢拇指與食指之間（小點心的中心）
OFF_FIST = (-0.012, 0.048, 0.000)      # fist 手勢拳心（緞帶穿過，方向＝局部 Z）


def _off(kind, side, k):
    o = {"grip": OFF_GRIP, "pinch": OFF_PINCH, "fist": OFF_FIST}[kind]
    return Vector((o[0] * (1 if side == "R" else -1), o[1], o[2])) * k


def hand_point(kind, side="R", arm=None, upright=False):
    """道具掛點的世界矩陣（先 pose_frame 再呼叫）。kind：'grip' 香檳杯、'pinch' 點心、'fist' 緞帶。
    矩陣的 Z 軸＝杯子往上（拇指那側）、Y 軸＝手指方向；upright=True 時改成 Z 軸朝正上方（杯子保持直立，只跟手的水平方向轉）"""
    arm = arm or ARM
    bpy.context.view_layer.update()
    M = arm.matrix_world @ arm.pose.bones[f"J_Bip_{side}_Hand"].matrix
    p = M @ _off(kind, side, _kof(arm))
    R = M.to_3x3().normalized()
    if upright:
        y = R.col[1].copy(); y.z = 0
        y = y.normalized() if y.length > 1e-4 else Vector((0, 1, 0))
        z = Vector((0, 0, 1)); x = y.cross(z)
        R = Matrix((x, y, z)).transposed()
    return Matrix.Translation(p) @ R.to_4x4()


def place(P, x=0.0, y=0.0, rz=0.0, arm=None):
    """把「站在原點、面向 -Y」寫的姿勢搬到 (x, y) 並轉 rz 度（含 feet 腳底鎖定、沒有跟隨骨頭的 IK 目標）。
    plant_feet 的腳踝目標是世界座標，直接改 root／rz 會讓腳留在原點被拉長，所以要用這個換算。
    ⚠️ pose_lib 的膝蓋方向（FOOT_POLE）固定朝世界 -Y：rz 不是 0 時只適合膝蓋幾乎打直的動作（idle、bow、hips、bouquet）"""
    arm = arm or ARM
    Q = dict(P); r = math.radians(rz); c, sn = math.cos(r), math.sin(r)
    tr = lambda px, py: (x + c * px - sn * py, y + sn * px + c * py)
    rx, ry, rzz = P.get("root", (0, 0, 0))
    Q["root"] = tr(rx, ry) + (rzz,); Q["rz"] = P.get("rz", 0) + rz
    if P.get("feet"):
        B = arm.data.bones; F = {}
        for sd, spec in P["feet"].items():
            sp = list((tuple(spec) + (0.0,) * 6)[:6]); a0 = B[f"J_Bip_{sd}_Foot"].head_local
            wx, wy = tr(a0.x + sp[0], a0.y + sp[1]); sp[0], sp[1] = wx - a0.x, wy - a0.y
            F[sd] = tuple(sp)
        Q["feet"] = F
    if P.get("ik"):
        out = []
        for it in P["ik"]:
            if len(it) > 4:
                out.append(it); continue
            out.append((it[0],) + tuple(None if p is None else Vector(tr(p[0], p[1]) + (p[2],)) for p in it[1:4]))
        Q["ik"] = out
    return Q


# ════════════════════════ 走路引擎（腿：自己算的 IK，在骨架空間，所以朝哪個方向走都一樣） ════════════════════════
# 腿的三節骨頭在 rest 時都在同一個 x 平面上，只用繞 X 的轉動就能把腳踝放到任何 (y, z)：解析解、每格精確，
# 不靠 pose_lib.plant_feet（它的膝蓋方向固定朝世界 -Y，轉身朝 ±X 走時膝蓋會往側邊彎）。
_GEO = {}


def _leg_geo(arm, side):
    key = (arm.name, side)
    if key in _GEO:
        return _GEO[key]
    B = arm.data.bones
    hip, knee, ank, toe = (B[f"J_Bip_{side}_{n}"].head_local.copy() for n in ("UpperLeg", "LowerLeg", "Foot", "ToeBase"))
    pts = [B[b].matrix_local @ co for b, co in sole_points(arm, _who(arm)) if f"_{side}_" in b]
    zmin = min(p.z for p in pts)
    g = dict(hip=hip, ank=ank, toe=toe, heel=Vector((ank.x, max(p.y for p in pts), zmin)),
             tip=Vector((ank.x, min(p.y for p in pts), zmin)), zmin=zmin,
             l1=math.hypot(knee.y - hip.y, knee.z - hip.z), l2=math.hypot(ank.y - knee.y, ank.z - knee.z),
             p1=math.atan2(knee.z - hip.z, knee.y - hip.y), p2=math.atan2(ank.z - knee.z, ank.y - knee.y),
             hh=B["J_Bip_C_Hips"].head_local.copy())
    _GEO[key] = g
    return g


def _ankle(g, fy, th, lift, gz):
    """腳的狀態 → 腳踝在骨架空間的 (y, z)。fy：腳往前後的位移（往前＝負）；th：腳掌俯仰（>0 腳跟抬起，整隻鞋繞鞋尖著地點轉；
    <0 腳尖翹起，繞腳跟著地點轉）；lift：離地高度；gz：地面在骨架空間的高度（＝骨盆下沉量）。
    轉軸都放在地面上的著地點：腳趾關節離地 3.8 cm，繞它轉的話鞋底在關節正下方的點會往後刮（量到每格 3.5 mm 的滑步）"""
    a0 = g["ank"]; dz0 = gz + lift - g["zmin"]
    if abs(th) < 1e-9:
        return a0.y + fy, a0.z + dz0
    pv = g["tip"] if th > 0 else g["heel"]
    r = math.radians(th); c, sn = math.cos(r), math.sin(r)
    vy, vz = a0.y - pv.y, a0.z - pv.z
    return pv.y + fy + vy * c - vz * sn, pv.z + dz0 + vy * sn + vz * c


def _hip(g, hx):
    h = g["hip"]
    if not hx:
        return h.y, h.z
    c, sn = math.cos(math.radians(hx)), math.sin(math.radians(hx)); p = g["hh"]
    dy, dz = h.y - p.y, h.z - p.z
    return p.y + dy * c - dz * sn, p.z + dy * sn + dz * c


def _leg_ik(g, Ay, Az, hx=0.0):
    """腳踝到 (Ay, Az)、膝蓋朝前 → (大腿, 小腿) 繞 X 的角度（度），以及「需要的長度／腿長」"""
    hy, hz = _hip(g, hx)
    dy, dz = Ay - hy, Az - hz; l1, l2 = g["l1"], g["l2"]
    d = math.hypot(dy, dz); over = d / (l1 + l2)
    d = min(max(d, 1e-4), (l1 + l2) * 0.99999)
    al = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    t1 = math.atan2(dz, dy) - al
    ky, kz = hy + l1 * math.cos(t1), hz + l1 * math.sin(t1)
    t2 = math.atan2(Az - kz, Ay - ky)
    return math.degrees(t1 - g["p1"]) - hx, math.degrees(t2 - t1 - g["p2"] + g["p1"]), over


def _plan(seq, ta, tb, init, k, first_off=8.0, th_off=15.0, th_on=9.0, last_on=9.0, lift=0.035, last_lift=None):
    """換步表：seq＝[(左右, 落腳位置 u), ...] 依序在 [ta, tb] 之間排完。
    每一步：腳跟抬起 0.42T → 擺盪 0.78T（腳離地往前、落地時腳尖微翹）→ 腳掌放平 0.17T；T＝相鄰兩步的間隔
    （擺盪佔比大一點，快走時大腿、小腿的角速度與速度突變才壓得住）"""
    n = len(seq); T = (tb - ta) / (n - 1 + 1.37)
    out = []; pos = dict(init)
    for i, (sd, u1) in enumerate(seq):
        t0 = ta + 0.42 * T + i * T
        out.append(dict(side=sd, u0=pos[sd], u1=u1, t0=t0, t1=t0 + 0.78 * T, hoff=0.42 * T, hon=0.17 * T, T=T,
                        th_off=first_off if i == 0 else th_off, th_on=last_on if i == n - 1 else th_on,
                        lift=(lift if (i < n - 1 or last_lift is None) else last_lift) * k))
        pos[sd] = u1
    return out, T


class _Gait:
    """換步表 → 每個時間點的腿部角度、骨盆位置。u＝沿前進方向的距離（公尺）；hips_x(t)／extra_drop(t)／u_add(t) 可另外給。
    骨盆前後位置＝兩腳中點對時間取「一個步週期寬」的移動平均：穩定步行時剛好等速、而且永遠在兩腳中間，起步、停步、卡住時自然加減速
    （用加減速曲線硬排的話，中段會比步伐快、跑到兩腳前面，後腳構不到只好整個人蹲低）。
    骨盆高度：先算每個時間點「兩隻腳都構得到（腿長 × margin）」需要下沉多少，取 ±0.2 秒內的最大值再平均（平滑而且一定夠），
    再加上擺盪中段的上浮（bob）"""

    def __init__(self, arm, steps, dur, origin, rz, init=None, hips_x=None, extra_drop=None, u_add=None,
                 bob=0.006, margin=0.975):
        self.arm = arm; self.k = _kof(arm); self.steps = steps
        self.init = init or {"L": 0.0, "R": 0.0}
        self.ox, self.oy = origin; self.rz = rz
        r = math.radians(rz); self.fx, self.fy = math.sin(r), -math.cos(r)
        self.hips_x = hips_x or (lambda t: 0.0); self.extra = extra_drop or (lambda t: 0.0)
        self.u_add = u_add or (lambda t: 0.0)
        self.bobh = bob * self.k; self.soft = SOFT_KNEE * self.k
        self.geo = {sd: _leg_geo(arm, sd) for sd in "LR"}
        n = 721; self.n = n
        mid = [0.5 * (self.foot("L", i / (n - 1))[0] + self.foot("R", i / (n - 1))[0]) for i in range(n)]

        def t_loc(t):                                  # 離 t 最近那一步的週期
            return min(steps, key=lambda st: abs(t - 0.5 * (st["t0"] + st["t1"])))["T"]
        self.ugrid = []
        for i in range(n):
            w = max(1, int(round(0.5 * t_loc(i / (n - 1)) * (n - 1))))
            self.ugrid.append(sum(mid[min(max(j, 0), n - 1)] for j in range(i - w, i + w + 1)) / (2 * w + 1))
        need = []
        for i in range(n):
            t = i / (n - 1); up = self.u_p(t); hx = self.hips_x(t); req = self.soft
            for sd in "LR":
                g = self.geo[sd]; u, th, tau, lift = self.foot(sd, t)
                Ay, Az = _ankle(g, -(u - up), th, lift, 0.0)
                hy, hz = _hip(g, hx); R = (g["l1"] + g["l2"]) * margin; dy = Ay - hy
                if abs(dy) >= R * 0.97:
                    raise ValueError(f"步幅太大：t={t:.3f} 腳離骨盆水平 {abs(dy):.3f} m，腿長只有 {R:.3f} m；多走幾步或縮短距離")
                req = max(req, hz - Az - math.sqrt(R * R - dy * dy))
            need.append(req + self.bob(t) - self.extra(t))
        w = max(1, int(round(0.2 / dur * (n - 1))))
        mx = [max(need[max(0, i - w):i + w + 1]) for i in range(n)]
        self.base = [sum(mx[max(0, i - w):i + w + 1]) / len(mx[max(0, i - w):i + w + 1]) for i in range(n)]

    def _interp(self, grid, t):
        x = max(0.0, min(1.0, t)) * (self.n - 1); i = min(int(x), self.n - 2); f = x - i
        return grid[i] * (1 - f) + grid[i + 1] * f

    def u_p(self, t):
        return self._interp(self.ugrid, t) + self.u_add(t)

    def foot(self, side, t):
        """(u, 腳掌俯仰 th, 腳趾 tau, 離地高度)"""
        u = self.init[side]
        for st in self.steps:
            if st["side"] != side:
                continue
            t0, t1, ho, hn = st["t0"], st["t1"], st["hoff"], st["hon"]
            if t < t0 - ho:
                break
            if t < t0:                                   # 腳跟抬起（繞鞋尖轉，鞋尖不動）
                th = st["th_off"] * ease((t - (t0 - ho)) / ho)
                return st["u0"], th, 0.0, 0.0
            if t < t1:                                   # 擺盪：鞋尖離地 → 往前 → 腳跟著地
                q = (t - t0) / (t1 - t0); e = ease(q)
                th = st["th_off"] + (-st["th_on"] - st["th_off"]) * e
                return st["u0"] + (st["u1"] - st["u0"]) * e, th, 0.0, st["lift"] * math.sin(math.pi * q)
            if t < t1 + hn:                              # 腳掌放平（繞腳跟轉，不滑）
                return st["u1"], -st["th_on"] * (1 - ease((t - t1) / hn)), 0.0, 0.0
            u = st["u1"]
        return u, 0.0, 0.0, 0.0

    def bob(self, t):
        b = 0.0
        for st in self.steps:
            if st["t0"] < t < st["t1"]:
                b = max(b, math.sin(math.pi * (t - st["t0"]) / (st["t1"] - st["t0"])))
        return self.bobh * b

    def drop(self, t):
        return self._interp(self.base, t) - self.bob(t) + self.extra(t)

    def apply(self, P, t):
        """把兩條腿（和骨盆前傾）寫進 P，回傳 root"""
        up = self.u_p(t); hx = self.hips_x(t); dr = self.drop(t)
        if hx:
            P["Hips"] = [("X", hx)]
        for sd in "LR":
            g = self.geo[sd]; u, th, tau, lift = self.foot(sd, t)
            Ay, Az = _ankle(g, -(u - up), th, lift, dr)
            a, b, _ = _leg_ik(g, Ay, Az, hx)
            P[f"{sd}_UpperLeg"] = [("X", a)]; P[f"{sd}_LowerLeg"] = [("X", b)]
            P[f"{sd}_Foot"] = [("X", th - hx - a - b)]; P[f"{sd}_ToeBase"] = [("X", -tau)]
        return (self.ox + self.fx * up, self.oy + self.fy * up, -dr)


def _alt(lead):
    return "L" if lead == "R" else "R"


# ════════════════════════ 站姿骨盆修正（2026-10-08） ════════════════════════
# 使用者看 ② 新郎：「新郎還是骨盆前傾走路，走到定位也是骨盆前傾，很醜幫我調整」。
# 量測：站定的姿勢（walk_fwd 結尾、sneak_hand 開頭、idle）和 VRoid 的 rest 完全相同——rest 的骨盆骨頭（髖→腰椎）本來就往前斜 13.5°、
# 頭在骨盆後 3 cm，側面看屁股往後翹、腰往前凹。所以不是走路淡出或 sneak_hand 加的，是 rest 站姿本身（idle 在 actions.py，不改）。
# 修法：骨盆往後轉 POSTURE_TILT 度（Hips X −）、腰椎轉回同樣的量再多 POSTURE_SPINE 度（上身維持直立、頭回到骨盆上方）；
# 腿由 IK／規劃器重新對腳（不滑）。只套在男性（BOW_FEMALE＝False）：女性的骨盆微前傾是預期的站姿，新娘的動作不變。
# 套用：walk_fwd（proc 的 hips_x、mocap 的真人週期）、第 6 節站姿動作（_wrap standing=True：sneak_hand、bonked…）。
POSTURE_TILT = 11.0                                  # 第 1 輪 8°：站定改善、走路中段屁股仍往後；11°：骨盆骨頭從 13.5° 斜到約 2.5°
POSTURE_SPINE = 1.5
KNEE_FIX = False                                     # 走路膝蓋打直（mocap_retarget 的 KNEE_R_*）。2026-10-08 試做：V12 參數轉速 16.3、速度突變 7.6～9.0 未過，預設關
STAND_FIX = True                                     # 男性站姿統一修正（pose_lib.stand_fix：骨盆不前傾、站姿膝蓋打直），False＝關掉。排除：taste、turn、spin（no_stand_fix）
STAND_DROP = 0.0008                                  # 男性站姿動作（_wrap standing）骨盆下沉（公尺，新娘尺寸）
POSTURE_MOCAP_LEAN = -3.0                            # 真人週期走路時上身少前傾 3°（CMU 受試者走路上身前傾約 6°，加上 POSTURE_SPINE 看起來像彎腰、屁股往後）


def posture_fix():
    """(骨盆往後轉, 腰椎多往前) 度；女性 (0, 0)"""
    return (0.0, 0.0) if globals().get("BOW_FEMALE") else (POSTURE_TILT, POSTURE_SPINE)


def posture(P, w=1.0):
    """把站姿骨盆修正寫進姿勢 dict（腳要由 feet／IK 決定，否則骨盆一轉腳會被帶走）"""
    pt, pe = posture_fix()
    if pt:
        P["Hips"] = [("X", -pt * w)] + list(P.get("Hips", []))
        P["Spine"] = [("X", (pt + pe) * w)] + list(P.get("Spine", []))
    return P


# ════════════════════════ 1. 往前走 walk_fwd ════════════════════════

HANDS.setdefault("walk_relax", dict(Thumb=(18, 24, 18), Index=(30, 44, 24), Middle=(34, 50, 28), Ring=(40, 54, 30), Little=(44, 58, 32), spread=-3))


def _swing_curve(plan):
    """手臂前後擺的相位（−1～+1）：每一步腳跟著地那一刻到極值（左腳著地＝+1＝右手在前；最後併腳那步＝0），
    相鄰兩個極值之間用半個餘弦接起來 → 連續、極值處速度為 0，像鐘擺。
    （舊版直接用兩腳前後差：腳站著時不變、擺盪時才動，手臂一段一段停頓，看起來像機器人）"""
    pts = [(plan[0]["t0"] - plan[0]["hoff"], 0.0)]
    for i, st in enumerate(plan):
        pts.append((st["t1"], 0.0 if i == len(plan) - 1 else (1.0 if st["side"] == "L" else -1.0)))

    def f(t):
        if t <= pts[0][0] or t >= pts[-1][0]:
            return 0.0
        for (ta_, va), (tb_, vb) in zip(pts[:-1], pts[1:]):
            if ta_ <= t <= tb_:
                u = (t - ta_) / max(tb_ - ta_, 1e-6)
                return va + (vb - va) * (0.5 - 0.5 * math.cos(math.pi * u))
        return 0.0
    return f


def walk_fwd(dist=1.2, steps=4, dur=3.0, dirx=1, rz=None, origin=(0.0, 0.0), lead="R", start=0.25, end=0.3,
             arms="swing", arm_swing=16.0, smile=0.45, arm=None, style="mocap"):
    """真的往前移動的走路：站姿出發 → 換步 → 最後一步併腳、站姿結束（可以接 place(idle) 或其他站姿動作）。
    dist：走多遠（公尺）；steps：落腳次數（含最後併腳那一步，≥ 2；步幅＝dist／(steps−1)）；dur：總秒數；
    start／end：開頭／結尾站著不動的秒數；dirx：+1 朝 +X、−1 朝 −X（或直接給 rz 度數＝任意朝向）；origin：出發點 (x, y)；
    lead：先跨哪隻腳；arms：'swing' 自然擺手、'skirt' 雙手在身側提著裙子（穿蓬裙時用）。
    style（2026-10-08 加）：'mocap'（預設）＝混合式真人走路（mocap_retarget.walk_mocap）：腳印位置、著地時間、fn.pos、fn.landings
    和 'proc' 完全相同，姿態依步態相位取自 CMU 真人走路週期（腳掌滾地、膝蓋方向、骨盆扭轉／側傾／起伏、腰、頭、手臂），
    起步、停步兩步用權重和 'proc' 混合（頭尾站姿＝'proc'）；arms='skirt' 時手臂仍是 'proc' 的提裙，只有身體、腿用真人。
    第一次呼叫 fn(t) 才計算（約幾秒），所以只建工廠、不播放時不花時間。'proc'＝舊版程式步態（下面這段）。
    上半身（2026-10-06 改）：手臂照步伐連續擺（鐘擺式，和腳反向）、往前擺時手肘多彎、手指放鬆微握；
    肩膀和腰反向小扭轉、頭保持朝前；走路時上身整體前傾約 4°、上背微圓（VRoid 站姿頭在骨盆後面 2～3 cm，看起來像挺胸）"""
    if style == "mocap":
        proc = walk_fwd(dist=dist, steps=steps, dur=dur, dirx=dirx, rz=rz, origin=origin, lead=lead, start=start, end=end,
                        arms=arms, arm_swing=arm_swing, smile=smile, arm=arm, style="proc")
        rz_ = (90.0 if dirx >= 0 else -90.0) if rz is None else rz
        box = {}

        def fn(t):
            if "f" not in box:
                if "walk_mocap" not in globals():
                    use("mocap_retarget")
                box["f"] = walk_mocap(proc, arm or ARM, rz_, origin, arms=arms)
            return box["f"](t)
        fn.gait = proc.gait; fn.dur = proc.dur; fn.pos = proc.pos; fn.landings = proc.landings
        fn.style = "mocap"; fn.proc = proc
        return fn
    arm = arm or ARM; k = _kof(arm)
    rz = (90.0 if dirx >= 0 else -90.0) if rz is None else rz
    steps = max(2, int(steps)); L = dist / (steps - 1)
    seq = [((lead if i % 2 == 0 else _alt(lead)), min((i + 1) * L, dist)) for i in range(steps)]
    ta, tb = start / dur, 1.0 - end / dur
    plan, T = _plan(seq, ta, tb, {"L": 0.0, "R": 0.0}, k, last_on=4.0, last_lift=0.025)
    pt, pe = posture_fix()
    G = _Gait(arm, plan, dur, origin, rz, bob=0.009, hips_x=(lambda t: -pt) if pt else None)   # 骨盆往後轉 pt（腿照骨盆算，不滑）
    swc = _swing_curve(plan)

    def fn(t):
        P = {}
        root = G.apply(P, t)
        sw = swc(t)                                              # +1：左腳在前（右手往前擺）
        w = seg(t, ta, ta + 0.6 * T) * (1 - seg(t, tb - 0.6 * T, tb))   # 走路中＝1，頭尾站著＝0
        if arms == "skirt":
            arms_down(P, l_out=3, r_out=3)
            P["L_Hand"] = []; P["R_Hand"] = []
            # 提裙：手臂幾乎放直、往外約 20°，手輕捏在臀部高度的外層裙面（新娘禮服 z 0.83 處裙子半徑約 0.29 m），隨步伐輕微前後
            ik = [(sd, _V(k, sg * 0.245, -0.060 - 0.010 * sw * sg, 0.905), _V(k, sg * 0.50, 0.25, 1.00), None, "Hips")
                  for sd, sg in (("L", 1), ("R", -1))]
            hands = ("pinch", "pinch")
        else:
            fl, fr = max(0.0, -sw), max(0.0, sw)                  # 左手、右手往前擺的程度
            arms_down(P, l_fwd=-arm_swing * sw, r_fwd=arm_swing * sw,
                      l_el=16 + 18 * fl, r_el=16 + 18 * fr, l_out=4, r_out=4)
            P["L_Hand"] = [("X", -3.0)]; P["R_Hand"] = [("X", -3.0)]     # 手腕放鬆、幾乎打直（往上翹會露出整個手掌）
            ik = []; hands = ("walk_relax", "walk_relax")
        # 上身：前傾、上背微圓（w 淡入淡出，站著的頭尾和 idle 相同）；肩膀和腰反向扭轉、頭轉回來保持朝前
        P["Spine"] = [("X", 4.0 * w + pt + pe), ("Z", -1.5 * sw * w)]          # pt：轉回骨盆修正的量；pe：頭回到骨盆上方
        P["Chest"] = [("X", 1.5 * w), ("Z", 4.0 * sw * w)]
        P["UpperChest"] = [("X", 1.5 * w), ("Z", 1.5 * sw * w)]
        P["Neck"] = [("X", 1.5 * w), ("Z", -2.0 * sw * w)]
        P["Head"] = [("Z", -2.0 * sw * w), ("X", -5.5 * w)]
        blink = 1.0 if abs(t - 0.62) < 0.012 else 0.0
        out = dict(P, hands=hands, root=root, rz=rz, ground=False,
                   face={"Fcl_ALL_Fun": smile, "Fcl_EYE_Close": blink})
        if ik:
            out["ik"] = ik
        return out

    fn.gait = G; fn.dur = dur; fn.style = "proc"
    fn.pos = lambda t: (G.ox + G.fx * G.u_p(t), G.oy + G.fy * G.u_p(t))     # 骨盆的世界 (x, y)
    fn.landings = [(st["side"], st["t1"] * dur) for st in plan]               # 每一步腳跟著地的秒數
    return fn


# ════════════════════════ 2. 拉著東西往前走 pull_walk ════════════════════════
# 緞帶扛在肩上往後拖：面向前進方向、身體前傾；近側拳頭在（預設右）肩前、約肩膀高度，另一手橫過胸前握在它前下方，
# 緞帶從兩個拳頭經過肩膀上方往後拖。
# 走 walk1 秒 → 卡住 stuck 秒（停步、更往前傾、膝蓋多彎、雙手往前一扯）→ 再走 walk2 秒到終點併腳。

# 握緞帶的位置（新娘座標、緞帶扛右肩；跟著 UpperChest 走，所以身體前傾時拳頭跟著肩膀）
PULL_R = (-0.155, -0.150, 1.310); PULL_R_POLE = (-0.42, -0.30, 1.00)
PULL_L = (-0.070, -0.215, 1.215); PULL_L_POLE = (0.30, -0.42, 0.97)
PULL_SHOULDER = (-0.105, 0.020, 1.330)          # 肩上緞帶經過的點
PULL_YANK = (0.15, -0.75, -0.64)                # 往前一扯的方向（沿著緞帶往前下）


def pull_walk(dist1=1.4, steps1=4, walk1=2.0, stuck=0.8, dist2=None, steps2=2, walk2=0.8, start=0.15, end=0.35,
              dirx=1, rz=None, origin=(0.0, 0.0), lead="R", shoulder="R", lean=12.0, stuck_lean=12.0,
              yank=0.10, yank_at=0.45, arm=None):
    """dist1／steps1／walk1：卡住前走多遠、幾步、幾秒（最後停在前後腳的拉扯站姿，步幅＝dist1／(steps1−0.5)）；
    stuck：卡住幾秒；yank_at：卡住段的第幾成往前扯（0~1）；yank：扯多遠（公尺）；
    dist2／steps2／walk2：卡住後再走多遠、幾步（含最後併腳）、幾秒（dist2 預設＝0.5＋0.8 個步幅）；
    start／end：開頭／結尾站著的秒數；shoulder：緞帶扛哪一邊肩膀；lean：走路前傾角；stuck_lean：卡住時再多傾的角度。
    總秒數＝start＋walk1＋stuck＋walk2＋end（fn.dur）；各段起訖秒數在 fn.times"""
    arm = arm or ARM; k = _kof(arm)
    rz = (90.0 if dirx >= 0 else -90.0) if rz is None else rz
    dur = start + walk1 + stuck + walk2 + end
    steps1 = max(2, int(steps1)); steps2 = max(1, int(steps2))
    L1 = dist1 / (steps1 - 0.5)
    seq1 = [((lead if i % 2 == 0 else _alt(lead)), (i + 1) * L1) for i in range(steps1)]
    back = seq1[-2][0]; F0 = steps1 * L1
    if steps2 == 1:
        dist2 = 0.5 * L1; seq2 = [(back, F0)]
    else:
        if dist2 is None:
            dist2 = 0.5 * L1 + 0.8 * L1 * (steps2 - 1)
        L2 = (dist2 - 0.5 * L1) / (steps2 - 1)
        if L2 <= 0:
            raise ValueError("dist2 太短：至少要大於半個步幅 %.2f m（或 steps2=1）" % (0.5 * L1))
        seq2 = [((back if j % 2 == 0 else _alt(back)), F0 + min(j + 1, steps2 - 1) * L2) for j in range(steps2)]
    ta1, tb1 = start / dur, (start + walk1) / dur
    ta2, tb2 = (start + walk1 + stuck) / dur, (start + walk1 + stuck + walk2) / dur
    p1, T1 = _plan(seq1, ta1, tb1, {"L": 0.0, "R": 0.0}, k, lift=0.04)
    end1 = {"L": 0.0, "R": 0.0}
    for sd, u in seq1:
        end1[sd] = u
    p2, T2 = _plan(seq2, ta2, tb2, end1, k, first_off=15.0, last_on=4.0, lift=0.04, last_lift=0.025)
    sg = 1 if shoulder == "R" else -1                 # 扛左肩：x 鏡射、左右手對調

    def stuck_s(t):
        return (t - tb1) / max(ta2 - tb1, 1e-6)

    def brace(t):
        q = stuck_s(t); return seg(q, 0.0, 0.35) * (1 - seg(q, 0.72, 1.0))

    def yk(t):                                        # 往前扯：約 0.25 秒扯到底、停一下、再慢慢放回走路的位置
        q = stuck_s(t); return bump(q, yank_at - 0.26, yank_at + 0.05, 0.62, 0.98)

    def walkw(t):
        return seg(t, ta1, ta1 + 0.5 * T1) * (1 - seg(t, tb2 - 0.5 * T2, tb2))

    def total_lean(t):
        return lean * walkw(t) + stuck_lean * brace(t) + 4.0 * yk(t)

    G = _Gait(arm, p1 + p2, dur, origin, rz, hips_x=lambda t: 0.35 * total_lean(t),
              extra_drop=lambda t: 0.025 * k * brace(t), u_add=lambda t: 0.04 * k * yk(t), bob=0.008)
    near, far = ("R", "L") if sg == 1 else ("L", "R")

    def mir(p):
        return (p[0] * sg, p[1], p[2])

    def fn(t):
        P = {}
        root = G.apply(P, t)
        lt = total_lean(t)
        P["Spine"] = [("X", 0.40 * lt)]; P["Chest"] = [("X", 0.25 * lt)]
        P["Neck"] = [("X", -0.20 * lt)]; P["Head"] = [("X", -0.45 * lt)]
        arms_down(P); P["L_Hand"] = []; P["R_Hand"] = []
        d = Vector(mir(PULL_YANK)).normalized() * yank * yk(t)
        ik = [(near, _V(k, *mir(PULL_R)) + d, _V(k, *mir(PULL_R_POLE)), None, "UpperChest"),
              (far, _V(k, *mir(PULL_L)) + d, _V(k, *mir(PULL_L_POLE)), None, "UpperChest")]
        b = brace(t)
        face = {"Fcl_ALL_Fun": 0.45 * (1 - b), "Fcl_EYE_Close": 0.55 * b, "Fcl_MTH_E": 0.15 + 0.45 * b}
        return dict(P, hands=("fist", "fist"), ik=ik, root=root, rz=rz, ground=False, face=face)

    fn.gait = G; fn.dur = dur; fn.shoulder = shoulder
    fn.pos = lambda t: (G.ox + G.fx * G.u_p(t), G.oy + G.fy * G.u_p(t))
    fn.times = dict(walk1=(start, start + walk1), stuck=(start + walk1, start + walk1 + stuck),
                    yank=start + walk1 + stuck * (yank_at + 0.05), walk2=(start + walk1 + stuck, start + walk1 + stuck + walk2),
                    dur=dur, dist1=dist1, dist2=dist2)
    fn.landings = [(st["side"], st["t1"] * dur) for st in p1 + p2]
    return fn


def ribbon_points(shoulder="R", arm=None):
    """拉緞帶的路徑點（世界座標，先 pose_frame 再呼叫）：[前面那隻手的拳心, 肩前那隻手的拳心, 肩上的點]；
    緞帶從第一點經過第二點、跨過肩上的點往後拖到道具"""
    arm = arm or ARM; k = _kof(arm); sg = 1 if shoulder == "R" else -1
    near, far = ("R", "L") if sg == 1 else ("L", "R")
    bpy.context.view_layer.update()
    pb = arm.pose.bones["J_Bip_C_UpperChest"]
    M = arm.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted()
    sh = M @ Vector((PULL_SHOULDER[0] * sg * k, PULL_SHOULDER[1] * k, PULL_SHOULDER[2] * k))
    return [hand_point("fist", far, arm).to_translation(), hand_point("fist", near, arm).to_translation(), sh]


# ════════════════════════ 3. 舉杯乾杯 toast ════════════════════════
# 單手拿香檳杯（grip 手勢；杯子由情境掛在手骨上，見 hand_point('grip')）。前臂扭轉讓拇指盡量朝上，杯子跟著手骨時
# 最多斜 28°（致意後放下那幾格）；要完全直立用 hand_point('grip', side, upright=True)。
# 胸前拿著 → 舉起、往側前方伸出碰杯（輕敲一下）→ 收回、往前舉到下巴高度致意（點頭微笑）→ 回到胸前拿著。

def toast(hand="R", aim=0.0, reach=0.40, height=1.22, dur=2.5, arm=None):
    """hand：拿杯的手；aim：碰杯方向（度，0＝正前方、正值＝往角色左邊、負值＝往右邊）；
    reach：碰杯時杯子離肩膀多遠（公尺，新娘尺寸，會乘體型）；height：碰杯時杯子高度（新娘尺寸）。
    時間（fn.times，秒）：舉起 0.15～0.8、碰杯 0.9、收回舉杯致意 1.0～1.4、停住到 1.95、放回 2.4"""
    arm = arm or ARM; k = _kof(arm)
    sg = -1 if hand == "R" else 1                       # 拿杯那一側的 x 符號
    off = _off("grip", hand, k)
    ar = math.radians(aim); dv = Vector((math.sin(ar), -math.cos(ar), 0.0))
    H = _V(k, sg * 0.150, -0.270, 1.050)                    # 胸前（腰上）拿著
    C1 = _V(k, sg * 0.125, -0.270, 1.180)                   # 舉到胸口
    C = _V(k, sg * 0.110, 0.0, 0.0) + dv * reach * k + Vector((0, 0, height * k))
    U = _V(k, sg * 0.160, -0.340, 1.320)                    # 舉杯致意：往前舉到下巴高度（離臉夠遠、前臂比較平，杯子才直）
    PH, PC, PU = _V(k, sg * 0.45, 0.15, 0.95), _V(k, sg * 0.42, -0.05, 0.98), _V(k, sg * 0.44, -0.06, 1.02)
    up = Vector((0, 0, 1))

    def fn(t):
        a, b = seg(t, 0.05, 0.22), seg(t, 0.14, 0.32)
        tap = bump(t, 0.33, 0.36, 0.36, 0.40)
        c, d = seg(t, 0.40, 0.56), seg(t, 0.78, 0.96)
        G = H.lerp(C1, a).lerp(C, b) + dv * 0.025 * k * tap
        G = G.lerp(U, c).lerp(H, d)
        pole = PH.lerp(PC, b).lerp(PU, c).lerp(PH, d)
        cw = b * (1 - c)                                 # 碰杯段
        sw = c * (1 - d)                                 # 致意段
        nod = bump(t, 0.58, 0.64, 0.66, 0.74)
        P = {}
        arms_down(P, l_fwd=4, r_fwd=4)
        P[f"{hand}_Hand"] = []
        P["Spine"] = [("X", 3.0 * cw + 1.0 * sw), ("Z", 0.15 * aim * cw)]
        P["Head"] = [("Z", 0.35 * aim * cw), ("X", 9.0 * nod - 3.0 * sw), ("Y", -sg * 4.0 * sw)]
        W, tw = _solve_hand(arm, P, hand, G, off, pole, up)
        face = {"Fcl_ALL_Fun": 0.55 * (1 - cw) * (1 - sw) + 0.35 * sw, "Fcl_ALL_Joy": 0.85 * cw + 0.55 * sw}
        return dict(P, hands=("relax", "grip") if hand == "R" else ("grip", "relax"),
                    ik=[(hand, W, pole, None, "Hips")], twist=[(hand, tw)], face=face)

    fn.dur = dur; fn.hand = hand
    fn.times = dict(raise_=(0.05 * dur, 0.32 * dur), clink=0.36 * dur, salute=(0.40 * dur, 0.78 * dur), lower=(0.78 * dur, 0.96 * dur))
    return fn


# ════════════════════════ 4. 品嚐美食 taste ════════════════════════
# 一手從腰高前方（桌上、點心架）捏起一小塊點心 → 送到嘴邊、張嘴咬一口 → 拿開、嚼、滿足地笑著點頭 → 手放下。
_LIPS = {}


def lips_rest(arm=None):
    """嘴巴（閉嘴時的唇線、臉的表面）在 rest 骨架空間的位置：用 Fcl_MTH_A 會往下動的頂點找高度，再取那個高度臉中線最前面的點"""
    arm = arm or ARM
    if arm.name in _LIPS:
        return _LIPS[arm.name]
    import numpy as np
    F = bpy.data.objects[f"{_who(arm)}_Face"]; kb = F.data.shape_keys.key_blocks; n = len(F.data.vertices)
    b = np.empty(n * 3); kb["Basis"].data.foreach_get("co", b); a = np.empty(n * 3); kb["Fcl_MTH_A"].data.foreach_get("co", a)
    M = np.array(arm.matrix_world.inverted() @ F.matrix_world)
    b = b.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]; a = a.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    dz = b[:, 2] - a[:, 2]; idx = np.argsort(dz)[-30:]
    zm = float((b[idx, 2] * dz[idx]).sum() / dz[idx].sum()) - 0.003
    mid = b[(np.abs(b[:, 0]) < 0.004) & (np.abs(b[:, 2] - zm) < 0.003)]
    _LIPS[arm.name] = Vector((0.0, float(mid[:, 1].min()), zm))
    return _LIPS[arm.name]


def taste(hand="R", pick=(-0.16, -0.31, 0.97), dur=2.5, arm=None):
    """hand：拿點心的手；pick：點心原本的位置（新娘尺寸、角色座標：x 右手側為負、y 往前為負、z 高度；會乘體型）。
    點心中心＝pinch 手勢拇指和食指之間（hand_point('pinch')）。時間點見 fn.times（秒）"""
    arm = arm or ARM; k = _kof(arm)
    sg = -1 if hand == "R" else 1
    off = _off("pinch", hand, k)
    Pk = Vector((pick[0] if hand == "R" else -pick[0], pick[1], pick[2])) * k
    CH = _V(k, sg * 0.120, -0.250, 1.150)                   # 拿開後停在胸前（嚼）
    MID = _V(k, sg * 0.130, -0.310, 1.150)                  # 送到嘴邊途中先經過胸前（轉速平均、前臂不貼胸）
    RP = _V(k, sg * 0.40, 0.15, 0.85); KP = _V(k, sg * 0.45, 0.05, 0.88); MP = _V(k, sg * 0.44, -0.10, 0.98); HP = _V(k, sg * 0.42, 0.0, 0.92)
    MDP = _V(k, sg * 0.46, -0.02, 0.92)
    fwd = Vector((0, -1, 0)); up = Vector((0, 0, 1))
    cache = {}
    # 時間軸（0~1）：伸手 → 捏起 → 送到嘴邊 → 咬 → 拿開到胸前 → 嚼＋點頭 → 手放下
    T_REACH, T_GRAB, T_LIFT, T_AWAY, T_LOWER = (0.03, 0.20), (0.17, 0.27), (0.26, 0.54), (0.575, 0.78), (0.80, 0.995)
    T_BITE = 0.565

    def rest_pt():
        if "rest" not in cache:                          # 起始：手垂在身側、手肘彎 35°（手臂不要接近打直，IK 才不會在出發時甩一下）
            Q = {}; arms_down(Q, l_el=35, r_el=35); Q[f"{hand}_Hand"] = []
            Hm = _fk(arm, Q, f"{hand}_Hand") @ arm.data.bones[f"J_Bip_{hand}_Hand"].matrix_local
            cache["rest"] = Hm @ off
        return cache["rest"]

    def fn(t):
        a = seg(t, *T_REACH); c = seg(t, *T_AWAY); d = seg(t, *T_LOWER)
        b1 = seg(t, T_LIFT[0], T_LIFT[0] + 0.62 * (T_LIFT[1] - T_LIFT[0]))      # 兩段重疊：先往胸前抬、再靠向嘴
        b = seg(t, T_LIFT[0] + 0.30 * (T_LIFT[1] - T_LIFT[0]), T_LIFT[1])
        pk = a * (1 - b1)                                # 彎腰看桌子
        P = {}
        arms_down(P)
        P[f"{hand}_Hand"] = []
        P["Spine"] = [("X", 9.0 * pk + 2.0 * b * (1 - c))]; P["Chest"] = [("X", 3.0 * pk)]
        chew = seg(t, 0.60, 0.64) * (1 - seg(t, 0.85, 0.89))
        nod = bump(t, 0.65, 0.70, 0.71, 0.76) + bump(t, 0.76, 0.81, 0.82, 0.87)
        P["Neck"] = [("X", 2.0 * b * (1 - c))]
        P["Head"] = [("X", 14.0 * pk + 5.0 * b * (1 - c) + 7.0 * nod), ("Y", -sg * 5.0 * chew)]
        mouth = _fk(arm, P, "Head") @ lips_rest(arm) + Vector((0, -0.019 * k, -0.002 * k))
        S = rest_pt().lerp(Pk, a).lerp(MID, b1).lerp(mouth, b).lerp(CH, c).lerp(rest_pt(), d)
        pole = RP.lerp(KP, a).lerp(MDP, b1).lerp(MP, b).lerp(HP, c).lerp(RP, d)
        thumb = fwd.lerp(up, a * (1 - d)).normalized()
        W, tw = _solve_hand(arm, P, hand, S, off, pole, thumb)
        if t < 0.17:                                     # 伸手時半張 → 捏住 → 一直捏著，手放下時才慢慢放鬆
            hs = ("relax", "pinch_open", round(seg(t, 0.04, 0.17), 2))
        elif t < 0.30:
            hs = ("pinch_open", "pinch", round(seg(t, 0.17, 0.27), 2))
        else:
            hs = ("relax", "pinch", round(1 - seg(t, 0.84, 0.99), 2))
        mopen = bump(t, 0.46, 0.53, 0.54, 0.575)
        mchew = chew * 0.22 * abs(math.sin(math.pi * 3 * (t - 0.62) / 0.24))
        joy = seg(t, 0.62, 0.69) * (1 - seg(t, 0.88, 0.99))
        face = {"Fcl_MTH_A": 0.65 * mopen + mchew, "Fcl_ALL_Fun": 0.35 * (1 - joy), "Fcl_ALL_Joy": 0.8 * joy}
        hands = ("relax", hs) if hand == "R" else (hs, "relax")
        # no_stand_fix：手的 IK 跟著 Hips 走，男性站姿統一層（pose_lib.stand_fix）把骨盆往後轉 11° 時手會偏進臉（量到穿模 19 mm）
        return dict(P, hands=hands, ik=[(hand, W, pole, None, "Hips")], twist=[(hand, tw)], face=face, no_stand_fix=True)

    fn.dur = dur; fn.hand = hand
    fn.times = dict(reach=(T_REACH[0] * dur, T_REACH[1] * dur), grab=0.24 * dur, to_mouth=(T_LIFT[0] * dur, T_LIFT[1] * dur),
                    mouth_open=0.46 * dur, bite=T_BITE * dur, away=(T_AWAY[0] * dur, T_AWAY[1] * dur),
                    chew=(0.60 * dur, 0.89 * dur), lower=(T_LOWER[0] * dur, T_LOWER[1] * dur), release=0.90 * dur)
    return fn


# ════════════════════════ 5. 原地拉繩 pull_rope ════════════════════════
# 繩子從背後（拉的反方向）過來、扛在靠鏡頭那側的肩膀上，雙手一前一後在胸前握住（grip_rope：grip 的四指包住繩子、拇指沿繩子朝肩膀）。
# 前後弓箭步站穩（腳底鎖定、不滑步）、身體往拉的方向前傾、膝蓋微蹲，一下一下用力拉：
#   蓄力（重心後移、上身稍微抬起、雙手沿繩往上握）→ 用力一扯（骨盆往前下沉、更前傾、後腳跟離地、雙手往前下扯、咬牙）→ 撐住 → 放鬆回來。
# 方向以「鏡頭在角色正前方（-Y 那側）」時的畫面為準：dirx=+1 往畫面右邊（+X）拉、繩子從畫面左邊過來；dirx=-1 左右鏡像。
# 身體面向拉的方向轉 turn 度（預設 75°），頭和胸口轉回來看鏡頭（共約 25°）→ 正面鏡頭看到的臉約 3/4。
# 原地拉、腳踩穩：兩腳鎖在地上（和 walk_fwd 同一套腿 IK），骨盆用 root 前後移、上下沉，所以站的位置與朝向一律用參數 origin／dirx／turn（或 rz）給，
# 不要事後改回傳的 root／rz（腳會滑）。
# 繩子的路徑點（畫繩子用）：先 pose_frame 再呼叫 rope_points(fn)；穿西裝外套這類有墊肩的衣服時用 rope_points(fn, fit=True)。

# 擴充手勢（只加不改既有的）：握繩＝grip 的四指（手掌面和彎起的四指內側之間約 2.1 cm，包住 2.3～2.5 cm 粗的繩子），
# 拇指少彎一點、沿著繩子貼著（grip 的拇指尖離繩子約 1.6 cm，近看像比讚）
HANDS.setdefault("grip_rope", dict(HANDS["grip"], Thumb=(17, 22, 18)))
ROPE_HAND = "grip_rope"
# 繩子穿過的點（新娘尺寸、右手骨局部座標，左手 x 取負）：手掌面（x −0.017）和四指內側（x −0.038）的中點；
# 繩子方向＝手骨局部 Z（拇指那側）。2026-10-06 在新郎骨架上量的（手指關節擬合圓＋手掌網格厚度）
OFF_ROPE = (-0.0270, 0.0595, -0.0040)


def _rope_off(side, k):
    return Vector((OFF_ROPE[0] * (1 if side == "R" else -1), OFF_ROPE[1], OFF_ROPE[2])) * k


def pull_rope(dirx=1, tugs=2, dur=3.0, turn=75.0, look=20.0, rz=None, origin=(0.0, 0.0), shoulder=None,
              front=0.19, rear=0.21, drop=0.075, lean=24.0, load=(2.2, 0.35), pad=0.0, arm=None):
    """dirx：+1 往 +X（畫面右）拉、-1 往 -X（畫面左）拉；tugs：一輪拉幾下；dur：一輪幾秒（頭尾相接可循環）；
    turn：身體往拉的方向轉幾度（0＝面對鏡頭、90＝完全側身）；look：頭轉回來看鏡頭的角度；rz：直接指定身體朝向（度，會蓋掉 turn）；
    origin：站的位置 (x, y)；shoulder：繩子扛哪一邊肩膀（預設靠鏡頭那側：往右拉＝右肩、往左拉＝左肩）；
    front／rear：前腳往前、後腳往後幾公尺（新娘尺寸，會乘體型）；drop：骨盆平常下沉多少（微蹲）；lean：平常的前傾角；
    load：繩子另一端（拉的東西）在身後多遠、多高（公尺，新娘尺寸），只給 rope_points 畫繩子用；
    pad：繩子繞過肩膀那段再往外抬多少（公尺，新娘尺寸）。預設 0＝貼著新郎的 T 恤（量過整段不會穿過衣服）；
    穿西裝外套（墊肩比 T 恤高約 2 cm）時改用 rope_points(fit=True) 逐格貼著衣服算，不要只靠 pad（pad 0.02 墊肩前緣才不陷，但肩頂會浮 2 cm）。
    時間（秒）在 fn.times：每一下的蓄力、一扯、撐住、放鬆"""
    arm = arm or ARM; k = _kof(arm)
    dirx = 1 if dirx >= 0 else -1
    rz = dirx * turn if rz is None else rz
    near = shoulder or ("R" if dirx > 0 else "L"); far = _alt(near)
    sg = -1 if near == "R" else 1                     # 扛繩那側肩膀的 x 符號（角色座標）
    B = arm.data.bones
    geo = {sd: _leg_geo(arm, sd) for sd in "LR"}
    r = math.radians(rz); fx, fy = math.sin(r), -math.cos(r)
    UF, UR = front * k, -rear * k                     # 前腳（遠側）、後腳（扛繩那側）沿面向方向的位置
    foot_u = {far: UF, near: UR}
    Jn = B[f"J_Bip_{near}_UpperArm"].head_local.copy(); Jf = B[f"J_Bip_{far}_UpperArm"].head_local.copy()
    # 繩子的點（rest 骨架座標，跟著 UpperChest 走）：繞過肩膀的弧（肩頂 S0 → 肩頂後側 B1 → 肩胛骨上緣 B2，之後才往身後拉的東西去；
    # 直接從肩頂連到身後的話，身體前傾時繩子會穿過肩胛骨）、近手握點、遠手握點；手的極向（手肘方向）
    S0 = Vector((0.85 * Jn.x, Jn.y - 0.007 * k, Jn.z + (0.060 + pad) * k))
    B10 = Vector((0.85 * Jn.x, Jn.y + (0.034 + 0.4 * pad) * k, Jn.z + (0.050 + pad) * k))
    B20 = Vector((0.85 * Jn.x, Jn.y + (0.065 + pad) * k, Jn.z + (0.017 + 0.4 * pad) * k))
    N0 = Jn + Vector((sg * -0.010, -0.215, -0.060)) * k
    F0 = Vector((sg * 0.030 * k, Jn.y - 0.245 * k, Jn.z - 0.160 * k))
    PN = Jn + Vector((sg * 0.26, 0.06, -0.30)) * k
    PF = Jf + Vector((-sg * 0.14, -0.20, -0.30)) * k
    YANK = Vector((0.0, -0.40, -0.92)); REACH = Vector((0.0, 0.35, 0.94))
    offN, offF = _rope_off(near, k), _rope_off(far, k)

    def env(t):
        q = (t * tugs) % 1.0
        g = bump(q, 0.0, 0.26, 0.27, 0.48)            # 蓄力
        h = bump(q, 0.30, 0.50, 0.66, 1.0)            # 一扯＋撐住＋放鬆
        return g, h

    def body(t):
        g, h = env(t)
        up = (-0.030 * g + 0.045 * h) * k             # 骨盆沿面向方向的位置
        dr = (drop - 0.012 * g + 0.035 * h) * k       # 骨盆下沉
        L = lean - 8.0 * g + 12.0 * h                 # 上身總前傾
        return g, h, up, dr, L

    def legs_into(P, t, up, dr, hx, h):
        over = 0.0
        for sd in "LR":
            gg = geo[sd]
            th = 7.0 * h if sd == near else 0.0       # 一扯時後腳跟離地（繞鞋尖轉，鞋尖不動）
            Ay, Az = _ankle(gg, -(foot_u[sd] - up), th, 0.0, dr)
            a, b, ov = _leg_ik(gg, Ay, Az, hx)
            over = max(over, ov)
            P[f"{sd}_UpperLeg"] = [("X", a)]; P[f"{sd}_LowerLeg"] = [("X", b)]
            P[f"{sd}_Foot"] = [("X", th - hx - a - b)]; P[f"{sd}_ToeBase"] = []
        return over

    # 先掃一輪：腿一定要構得到（伸直會讓膝蓋一格彈直）
    worst = max(legs_into({}, i / 240, body(i / 240)[2], body(i / 240)[3], 0.35 * body(i / 240)[4], body(i / 240)[1])
                for i in range(240))
    if worst > 0.975:
        raise ValueError(f"pull_rope：腿伸到 {worst:.3f} 倍腿長，前後腳放太開或骨盆下沉太少（front／rear 縮小或 drop 加大）")

    def fn(t):
        g, h, up, dr, L = body(t)
        P = {}
        hx = 0.35 * L
        legs_into(P, t, up, dr, hx, h)
        P["Hips"] = [("X", hx)]
        P["Spine"] = [("X", 0.40 * L), ("Z", 2.0 * sg)]
        P["Chest"] = [("X", 0.25 * L), ("Z", 3.0 * sg)]
        P["Neck"] = [("X", -0.25 * L)]
        P["Head"] = [("X", -0.50 * L + 2.0 * h), ("Z", look * sg)]
        arms_down(P); P["L_Hand"] = []; P["R_Hand"] = []
        Mc = _fk(arm, P, "UpperChest")
        dN = YANK * (0.050 * k * h) + REACH * (0.025 * k * g)
        dF = YANK * (0.060 * k * h) + REACH * (0.030 * k * g)
        S, N, F = Mc @ S0, Mc @ (N0 + dN), Mc @ (F0 + dF)
        thumbN = ((S - N).normalized() + (N - F).normalized()).normalized()
        thumbF = (N - F).normalized()
        WN, twN = _solve_hand(arm, P, near, N, offN, Mc @ PN, thumbN)
        WF, twF = _solve_hand(arm, P, far, F, offF, Mc @ PF, thumbF)
        root = (origin[0] + fx * up, origin[1] + fy * up, -dr)
        Mo = Matrix.Translation(Vector(root)) @ Matrix.Rotation(r, 4, "Z")
        # 表情：平常咬牙皺眉（下定決心）；蓄力時吸一口氣（嘴微張）；一扯時瞇眼、咬緊牙、眉頭往下壓（用力）
        face = {"Fcl_ALL_Angry": 0.50 + 0.05 * h - 0.10 * g, "Fcl_ALL_Sorrow": 0.25 * h, "Fcl_MTH_I": 0.35 + 0.25 * h - 0.25 * g,
                "Fcl_EYE_Close": 0.08 + 0.27 * h, "Fcl_MTH_A": 0.10 * g}
        return dict(P, hands=(ROPE_HAND, ROPE_HAND), ik=[(near, Mo @ WN, Mo @ (Mc @ PN)), (far, Mo @ WF, Mo @ (Mc @ PF))],
                    twist=[(near, twN), (far, twF)], root=root, rz=rz, ground=False, face=face)

    T = dur / tugs
    fn.dur = dur; fn.tugs = tugs; fn.near = near; fn.far = far; fn.dirx = dirx; fn.rz = rz
    fn.times = dict(period=T, gather=(0.0, 0.26 * T), heave=(0.30 * T, 0.50 * T), hold=(0.50 * T, 0.66 * T), release=(0.66 * T, T))
    back = Vector((-fx, -fy, 0.0))
    fn.rope = dict(near=near, far=far, shoulder=[S0, B10, B20], anchor=Vector((origin[0], origin[1], load[1] * k)) + back * load[0] * k,
                   tail=0.15 * k)
    return fn


def rope_points(fn, arm=None, fit=False, radius=0.012, margin=0.002):
    """拉繩的路徑點（世界座標，先 pose_frame(ARM, fn(t)) 再呼叫），依序連起來就是整條繩子：
    [繩尾（遠手下方垂下的一段）, 遠手握點, 近手握點, 肩頂, 肩頂後側, 肩胛骨上緣, 繩子另一端（拉的東西，固定在身後 load 的位置）]。
    握點＝握繩手勢手指圍出的洞的中心（OFF_ROPE），繩子從這裡穿過。
    fit=False：肩上的弧是固定的點（照新郎 T 恤量的：貼著 T 恤、整段不穿過；穿西裝外套會陷進墊肩約 1 cm）。
    fit=True：近手到肩胛骨上緣這段改成每 2 cm 一點，照角色身上「現在看得到的衣服／皮膚」逐點往外推到表面外 radius＋margin（公尺），
    繩子才會蓋在西裝墊肩這類比較厚的衣服上、不陷進去（點數會變多；每格打幾百條射線，情境逐格畫繩子時用）"""
    arm = arm or ARM; R = fn.rope; k = _kof(arm)
    bpy.context.view_layer.update()
    pb = arm.pose.bones["J_Bip_C_UpperChest"]
    Mf = arm.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted()
    F, N = (arm.matrix_world @ arm.pose.bones[f"J_Bip_{sd}_Hand"].matrix @ _rope_off(sd, k) for sd in (R["far"], R["near"]))
    arc = [Mf @ p for p in R["shoulder"]]
    if fit:
        Jn = arm.data.bones[f"J_Bip_{R['near']}_UpperArm"].head_local
        C = Mf @ Vector((0.85 * Jn.x, Jn.y + 0.03 * k, Jn.z - 0.03 * k))          # 肩膀裡面的一點：從這裡往外看哪裡是表面
        dg = bpy.context.evaluated_depsgraph_get(); who = _who(arm)
        obs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(who + "_") and "Hair" not in o.name
               and not o.hide_render and o.visible_get()]

        def push(p):
            nrm = (p - C).normalized(); o = p + nrm * 0.15; best = None
            for ob in obs:
                M = ob.matrix_world; inv = M.inverted(); oo = inv @ o; dl = (inv.to_3x3() @ -nrm).normalized()
                ok, loc, nor, idx = ob.evaluated_get(dg).ray_cast(oo + dl * 0.11, dl, distance=0.09)
                if ok:                                   # 只看點外 4 cm～點內 5 cm 的表面（更外面的是手臂、袖子，不是繩子靠著的地方）
                    dd = ((M @ loc) - o).length
                    best = dd if best is None else min(best, dd)
            if best is None:
                return p
            need = 0.15 - best + radius + margin                 # 表面在點外面多少（＋繩子半徑＋間隙）
            return p + nrm * max(0.0, need)
        chain = [N] + arc; dense = []                    # 近手 → 肩頂 → 肩胛骨上緣，每 2 cm 一點，各自推到表面外
        for a, b in zip(chain[:-1], chain[1:]):
            m = max(1, int((b - a).length / 0.02))
            dense += [a.lerp(b, j / m) for j in range(1, m)] + [b]
        arc = [push(p) for p in dense if (p - N).length > 0.07]
    return [F + Vector((0.0, 0.0, -R["tail"])), F, N] + arc + [R["anchor"].copy()]



# ════════════════════════ 6. V12 互動動作：第 2 幕（玩具槌）、第 7 幕（圓桌餵食、紅酒） ════════════════════════
# 2026-10-06 由 blender-animation-append 新增。這一節的動作是「劇情用的單次動作」，不循環：
#   t∈[0,1) 對應 fn.dur 秒；t=0 是開頭姿勢、t→1 是結尾姿勢（最後幾格已經停在結尾姿勢上）。
# 接續的動作「開頭＝前一個的結尾」（同一組參數時逐骨頭相同，情境淡入淡出 0.3～0.4 秒就順）：
#   第 2 幕：sneak_hand 偷牽手（新郎）→ bonked 被敲抱頭（新郎）；mallet_bonk 玩具槌敲頭（新娘）在 0.5 秒敲中新郎頭頂。
#   第 7 幕：feed 餵食（新郎）／fed 被餵（新娘）→ glass_pick 相視一笑拿酒杯（兩人）→ toast_sit 坐姿乾杯（兩人）→ sip 喝一口（兩人）。
# 站位：工廠的 me=(x, y, rz) 是這個角色在場景裡的位置與朝向（和 scene_lib.pose_frame_at 的 x, y, rz 相同，rz=0 面向 -Y）。
#   target／clink／partner 這類「對到另一個人」的點一律給世界座標，工廠自己換算成角色座標。
#   回傳的姿勢 dict 照慣例寫成「角色在原點、面向 -Y」：情境用 pose_frame_at(ARM, fn(t), *me)；預覽、檢查用 pose_frame（站在原點）。
#   不要事後改回傳的 root／rz（站姿兩腳鎖地、坐姿骨盆高度照椅面算）：要換位置就改 me 重新呼叫工廠。
# 手臂不經過 pose_lib.ik_arm：直接照「肩膀、手腕、手肘方向、手骨方向」算出上臂、前臂、手骨的 FK 寫進姿勢（_arm_set，見下面「手臂」一節）。
#   ik_arm 從垂手出發做最小旋轉，手舉過頭時會一格翻面；palms 的目標在 face_palm 是骨架空間、pose_frame_at 卻會再乘站位旋轉，坐姿 ±45° 時掌心會偏。
#   這一節的姿勢 dict 沒有 ik／twist／palms 欄，pose_frame 與 pose_frame_at 套用結果相同，換站位也不會偏。
# 道具（玩具槌、叉子、紅酒杯）不在動作裡：held_prop(kind, side) 在 pose_frame 之後給道具的世界矩陣（握點＋道具軸）。
# 工廠建一次要 0.5～2 秒（要先量路徑），CUSTOM_ACTIONS 登記的是「第一次用到才建」的包裝（fn.real() 拿到工廠結果）。
from mathutils import Quaternion

# 預設站位／座位（照分鏡估的；情境要傳實際值）
V12_STAGE = {"groom": (-0.42, 0.0, 0.0), "bride": (0.42, 0.0, 0.0)}          # 第 2 幕：並排面向鏡頭，新郎在畫面左（-X）
V12_SEAT = {"groom": (-0.40, 0.40, 45.0), "bride": (0.40, 0.40, -45.0)}       # 第 7 幕：圓桌後兩張相鄰椅子，約 90°、各自 3/4 對鏡頭
V12_TABLE = dict(center=(0.0, 0.0), radius=0.40, top=0.73)                    # 圓桌（桌面高 0.73 m）
V12_CAM = (0.0, -2.6)                                                          # 第 7 幕鏡頭的 (x, y)：桌前
SEAT_H = 0.46                    # 椅面高（公尺，真實尺寸，不乘體型）
SIT_BUTT = 0.078                 # 坐下時髖關節比大腿／臀部最低點高多少（新娘尺寸 × 體型；兩個角色量過：新娘 0.076、新郎 0.074）
_ROLE = "bride" if BOW_FEMALE else "groom"
_NEAR = {"groom": "L", "bride": "R"}       # 第 7 幕靠對方的那隻手


def _to_local(p, me):
    """世界座標 → 站在 me=(x, y, rz) 的角色座標（原點在兩腳中間的地上、面向 -Y）"""
    x, y, rz = me; r = math.radians(-rz); c, s_ = math.cos(r), math.sin(r)
    dx, dy = p[0] - x, p[1] - y
    return Vector((c * dx - s_ * dy, s_ * dx + c * dy, p[2]))


def _to_world(p, me):
    x, y, rz = me; r = math.radians(rz); c, s_ = math.cos(r), math.sin(r)
    return Vector((x + c * p[0] - s_ * p[1], y + s_ * p[0] + c * p[1], p[2]))


def _aim_deg(me, pt):
    """世界座標的點在角色的哪個方向（度，0＝正前方、正值＝角色左邊）"""
    p = _to_local(pt, me)
    return math.degrees(math.atan2(p.x, -p.y))


_ANC = {}


def _chain(arm, key):
    """骨頭 key 和它的祖先（照 BODY_ORDER）＋各自 rest 頭部位置：快取起來（bpy 屬性存取很慢）"""
    ck = (arm.name, key)
    if ck not in _ANC:
        B = arm.data.bones; tgt = B[bn(key)]
        names = {b.name for b in tgt.parent_recursive} | {tgt.name}
        _ANC[ck] = [(kk, B[bn(kk)].head_local.copy()) for kk in BODY_ORDER if bn(kk) in names]
    return _ANC[ck]


def _fkc(arm, P, key):
    """_fk 的快版（結果相同）：祖先清單快取、跳過 0 度"""
    M = Matrix.Identity(4)
    for kk, h in _chain(arm, key):
        for axis, deg in P.get(kk, ()):
            if deg:
                pv = M @ h
                M = Matrix.Translation(pv) @ _rotm(axis, deg) @ Matrix.Translation(-pv) @ M
    return M


_BD = {}


def _bd(arm, name):
    """骨頭 rest 資料 (head, tail, matrix_local) 快取"""
    ck = (arm.name, name)
    if ck not in _BD:
        b = arm.data.bones[name]; _BD[ck] = (b.head_local.copy(), b.tail_local.copy(), b.matrix_local.copy())
    return _BD[ck]


def _len_arm(arm, side):
    ua, la, hd = (_bd(arm, f"J_Bip_{side}_{n}")[0] for n in ("UpperArm", "LowerArm", "Hand"))
    return (la - ua).length, (hd - la).length


def _shoulder(arm, P, side):
    return _fkc(arm, P, f"{side}_UpperArm") @ _bd(arm, f"J_Bip_{side}_UpperArm")[0]


_PALM_LOC = {"L": Vector((1.0, 0.0, 0.0)), "R": Vector((-1.0, 0.0, 0.0))}     # 掌心＝手骨局部 ±X（左 +X、右 -X）；拇指那側＝局部 +Z


def _frame(e1, e2):
    """兩個方向 → 正交基底（e1 不變、e2 取垂直分量）"""
    a = Vector(e1).normalized(); b = Vector(e2) - a * a.dot(Vector(e2))
    if b.length < 1e-6:
        b = Vector((0, 0, 1)) - a * a.z
        if b.length < 1e-6:
            b = Vector((0, 1, 0)) - a * a.y
    b.normalize()
    return a, b, a.cross(b)


def _rot_map(src1, src2, dst1, dst2):
    """把手骨局部的兩個方向 (src1, src2) 對到骨架空間的 (dst1, dst2)：回傳 3x3（＝手骨姿勢矩陣的旋轉部分）"""
    a = Matrix(_frame(src1, src2)).transposed(); b = Matrix(_frame(dst1, dst2)).transposed()
    return b @ a.transposed()


def _arm_fk(arm, P, side):
    """一次算出上臂、前臂、手骨的「rest→姿勢」變換（和 _fk 分三次算結果相同）"""
    Mu = _fkc(arm, P, f"{side}_UpperArm"); out = [Mu]; M = Mu
    for n in ("LowerArm", "Hand"):
        h = _bd(arm, f"J_Bip_{side}_{n}")[0]
        for axis, deg in P.get(f"{side}_{n}", ()):
            if deg:
                pv = M @ h
                M = Matrix.Translation(pv) @ _rotm(axis, deg) @ Matrix.Translation(-pv) @ M
        out.append(M)
    return out


def _plerp(a, b, w, out):
    """手肘方向點的內插：直線內插會穿過手臂的軸（手肘一格翻到另一邊），中段往外推 out"""
    return Vector(a).lerp(Vector(b), w) + Vector(out) * (4.0 * w * (1.0 - w))


def _slerp_dir(a, b, w):
    a = Vector(a).normalized(); b = Vector(b).normalized()
    if w <= 0:
        return a
    if w >= 1:
        return b
    q = a.rotation_difference(b)
    return (Quaternion().slerp(q, w) @ a).normalized()


def _ease_in(u, p=1.7):
    u = max(0.0, min(1.0, u)); return u ** p


def _ease_out(u, p=1.7):
    u = max(0.0, min(1.0, u)); return 1 - (1 - u) ** p


# 擴充手勢（只加不改既有的）
# stem：握紅酒杯腳——四指比 grip 收緊（杯腳粗 7～8 mm），拇指從側面扣住
HANDS.setdefault("stem", dict(Thumb=(22, 30, 24), Index=(58, 66, 42), Middle=(64, 70, 44), Ring=(68, 72, 44), Little=(70, 72, 44), spread=-2))
# fork：拿叉子（像拿筆）——拇指和食指捏住叉柄、中指在下面托著、無名指和小指彎進掌心
HANDS.setdefault("fork", dict(Thumb=(20, 26, 18), Index=(30, 38, 26), Middle=(38, 48, 30), Ring=(70, 80, 50), Little=(74, 82, 50), spread=-1))
# cup：抱頭、托臉頰——手指併攏微彎，手掌貼著圓的頭、臉
HANDS.setdefault("cup", dict(Thumb=(6, 8, 6), Index=(12, 16, 10), Middle=(12, 16, 10), Ring=(14, 18, 12), Little=(16, 20, 12), spread=1))

# 道具握點與道具軸（手骨局部座標，新娘尺寸 × 體型；右手 x 取負、左手取正）。手骨局部：Y＝手指方向、Z＝拇指那側、±X＝掌心（左 +X、右 -X）
OFF_MALLET = (-0.025, 0.060, 0.000)     # 玩具槌柄穿過 grip 拳心
AX_MALLET = (0.0, 0.64, 0.77)           # 槌柄方向（往槌頭）：斜穿過掌心，從拇指那側出來、和手指方向差 50°（真的握槌就是斜的）；槌面朝 (0, 0.77, -0.64)
OFF_STEM = (-0.022, 0.058, -0.004)      # 紅酒杯腳穿過 stem 拳心；杯子往上＝局部 +Z
OFF_FORK = (-0.040, 0.066, 0.030)       # 叉柄在拇指與食指之間
AX_FORK = (-0.30, 0.90, 0.30)           # 叉子方向（往叉尖）：順著手指、往掌心和拇指那側微斜（右手；左手 x 取負）
# 道具本身的尺寸（真實尺寸，不乘體型）
MALLET = dict(handle=0.38, end=0.04, head_r=0.06, head_len=0.20)   # 槌柄 38 cm（握在末端、拳心離柄尾 4 cm）、槌頭直徑 12 cm 長 20 cm
FORK = dict(tip=0.115, back=0.065)      # 握點到叉尖 11.5 cm、到柄尾 6.5 cm
GLASS = dict(bowl=0.085, rim=0.135, rim_r=0.042, base=-0.042)     # 從握點（杯腳中段）量：杯身中心 +8.5、杯緣 +13.5（半徑 4.2）、杯底 -4.2 cm


def _mir(o, side):
    return Vector((o[0] * (1 if side == "R" else -1), o[1], o[2]))


def _offk(o, side, k):
    return _mir(o, side) * k


_PROP = {"mallet": (OFF_MALLET, AX_MALLET), "glass": (OFF_STEM, (0, 0, 1)), "fork": (OFF_FORK, AX_FORK)}


def held_prop(kind, side, arm=None):
    """手上道具的世界矩陣（先 pose_frame／pose_frame_at 再呼叫）：位置＝握點；Z 軸＝道具軸
    （'mallet' 從拳頭往槌頭、'glass' 杯子往上、'fork' 往叉尖）；Y 軸＝垂直於道具軸、最接近手指方向（槌：槌面朝的方向，槌頭圓柱的軸）。
    道具上的點：槌頭中心＝握點 + (handle − end + head_r)·Z；叉尖＝握點 + tip·Z；杯身中心＝握點 + bowl·Z"""
    arm = arm or ARM
    bpy.context.view_layer.update()
    k = _kof(arm)
    M = arm.matrix_world @ arm.pose.bones[f"J_Bip_{side}_Hand"].matrix
    off, ax = _PROP[kind]
    p = M @ _offk(off, side, k)
    R3 = M.to_3x3().normalized()
    z, y, x = _frame(R3 @ _mir(ax, side), R3.col[1])
    return Matrix.Translation(p) @ Matrix((y.cross(z), y, z)).transposed().to_4x4()


# ──────── 坐姿底 ────────
def sit_legs(P, seat=SEAT_H, arm=None, knee_out=0.03, fwd=0.03):
    """坐姿底：骨盆降到「椅面 seat＋臀部厚度」、兩腳踩地（腳底鎖定 feet，膝蓋自動彎、腳掌平貼地面）。
    寫進 P["feet"]，回傳 root 的 z（骨盆下降量，負值）。knee_out／fwd：腳踝往外、往前多少（新娘尺寸）。
    上身前傾、轉身只用 Spine 以上的骨頭（不要轉 Hips，腿會跟著動）"""
    arm = arm or ARM; k = _kof(arm); B = arm.data.bones
    hip0 = B["J_Bip_L_UpperLeg"].head_local
    L1 = (B["J_Bip_L_LowerLeg"].head_local - hip0).length
    hip_z = seat + SIT_BUTT * k
    P["feet"] = {"L": (knee_out * k, -(L1 + fwd * k), 0.0), "R": (-knee_out * k, -(L1 + fwd * k), 0.0)}
    return hip_z - hip0.z


def _body(P, st):
    """上半身角度（度）寫進 P：s*＝Spine、c*＝Chest、n*＝Neck、h*＝Head（各自先轉 Z 再 X 再 Y）、shl／shr＝左右聳肩"""
    g = lambda n: st.get(n, 0.0)
    P["Spine"] = [("Z", g("sz")), ("X", g("sx")), ("Y", g("sy"))]
    P["Chest"] = [("Z", g("cz")), ("X", g("cx")), ("Y", g("cy"))]
    P["Neck"] = [("Z", g("nz")), ("X", g("nx")), ("Y", g("ny"))]
    P["Head"] = [("Z", g("hz")), ("X", g("hx")), ("Y", g("hy"))]
    if g("shl"):
        P["L_Shoulder"] = [("Y", -g("shl"))]
    if g("shr"):
        P["R_Shoulder"] = [("Y", g("shr"))]
    return P


def _mixd(a, b, w):
    return {n: a.get(n, 0.0) + (b.get(n, 0.0) - a.get(n, 0.0)) * w for n in set(a) | set(b)}


def _look(deg, neck=0.22):
    """頭轉 deg 度（正值＝往角色左邊）：分給 Neck、Head"""
    return {"nz": neck * deg, "hz": (1 - neck) * deg}


_SURF = {}


def _surf_bvh(arm, parts):
    """角色網格（rest 姿勢、骨架空間）的 BVH：量頭頂、臉頰表面用"""
    key = (arm.name, parts)
    if key in _SURF:
        return _SURF[key]
    from mathutils.bvhtree import BVHTree
    who = _who(arm); V, Fc = [], []
    for n in parts:
        ob = bpy.data.objects.get(who + n)
        if ob is None:
            continue
        M = arm.matrix_world.inverted() @ ob.matrix_world; b = len(V)
        V += [M @ v.co for v in ob.data.vertices]; Fc += [tuple(i + b for i in p.vertices) for p in ob.data.polygons]
    _SURF[key] = BVHTree.FromPolygons(V, Fc)
    return _SURF[key]


def _surface(arm, parts, origin, direction):
    """從 origin 沿 direction 打一條射線到 rest 姿勢的網格表面 → (點, 朝外的法線)"""
    loc, nor, i, d = _surf_bvh(arm, parts).ray_cast(Vector(origin), Vector(direction).normalized())
    if loc is None:
        return None, None
    nor = nor.normalized()
    return loc, (nor if nor.dot(Vector(direction)) < 0 else -nor)


def _palm_pt(arm, side, k, gap=0.0):
    """手骨局部座標的「掌心表面中心」（手掌中段、掌心表面再往外 gap）"""
    po = _palm_off() if arm is ARM else 0.022 * k
    return Vector((0.0, 0.050 * k, 0.0)) + _PALM_LOC[side] * (po + gap)




# ──────── 手臂：直接算三根骨頭的方向寫進 FK（不經過 pose_lib.ik_arm） ────────
# 為什麼：ik_arm 是從 FK（垂手）出發做「最小旋轉」對準；手要舉過頭時前臂得轉 150～180°，最小旋轉的軸在接近 180° 時不穩，
# 會一格翻到另一邊（量到每格 80～180°）。這裡改成照「肩膀、手腕、手肘方向點、手骨方向 R」直接算出上臂、前臂、手骨的姿勢，
# 換成 P 裡的世界軸旋轉（rot_world 的寫法），pose_frame 照常套用。好處：
#   1. 不會翻：每根骨頭的方向都由連續的幾何量決定（手肘平面、前臂扭轉照 swing-twist 分一半給前臂、一半給手腕）。
#   2. 和站位無關：寫的是骨架空間的 FK，scene_lib.pose_frame_at 怎麼搬、怎麼轉都正確（不必再管 ik 目標要不要加 root）。
# 手臂狀態一律寫成 (W, pole, R)：骨架空間的手腕位置、手肘方向點、手骨的姿勢旋轉（3x3，欄＝手骨局部 X/Y/Z 在骨架空間的方向；
# 局部 Y＝手指方向、Z＝拇指那側、±X＝掌心：左 +X、右 -X）。R 給 None＝手掌順著前臂。

_PALM_LOC = {"L": Vector((1.0, 0.0, 0.0)), "R": Vector((-1.0, 0.0, 0.0))}


def _elbow(arm, side, S, W, pole):
    """和 pose_lib.ik_arm 同一套算法：(手肘位置, 手腕實際到的位置, 肩→腕方向, 手肘偏向的單位向量, 肩膀處的夾角)"""
    L1, L2 = _len_arm(arm, side)
    v = Vector(W) - S; d = max(1e-4, min(v.length, (L1 + L2) * 0.999)); dr = v.normalized()
    a = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    pp = Vector(pole) - S; pp = pp - dr * pp.dot(dr)
    if pp.length < 1e-6:
        pp = Vector((0, 0, -1)) - dr * dr.z
    pp.normalize()
    return S + dr * math.cos(a) * L1 + pp * math.sin(a) * L1, S + dr * d, dr, pp, a


def _arm_frames(arm, side, S, W, pole):
    """上臂、前臂（不含扭轉）的骨頭方向（3x3，欄＝骨頭局部 X/Y/Z）。VRoid 手臂：局部 Y＝骨頭方向、X＝手肘轉軸（彎曲＝繞 +X 轉、前臂往 +Z 那側彎）。
    手肘偏向 pp（ik_arm 的手肘方向點）時，上臂的 +Z＝dr·sin(a) − pp·cos(a)：手臂打直也有定義，不會跳"""
    E, Wr, dr, pp, a = _elbow(arm, side, S, W, pole)
    yu = (E - S).normalized()
    zu = (dr * math.sin(a) - pp * math.cos(a)).normalized()
    xu = yu.cross(zu).normalized(); zu = xu.cross(yu)
    yf = (Wr - E).normalized(); zf = xu.cross(yf).normalized()
    return E, Wr, Matrix((xu, yu, zu)).transposed(), Matrix((xu, yf, zf)).transposed()


def _delta(M_want, M_cur):
    """「rest→姿勢」變換的旋轉部分要從 M_cur 變成 M_want：差的那個旋轉 → (世界軸, 度數) 或 None"""
    D = M_want @ M_cur.transposed()
    q = D.to_quaternion()
    ang = 2 * math.acos(max(-1.0, min(1.0, q.w)))
    if ang < 1e-5:
        return None
    ax = Vector((q.x, q.y, q.z))
    if ax.length < 1e-9:
        return None
    return (tuple(ax.normalized()), math.degrees(ang))


def _arm_set(arm, P, side, W, pole, R=None, split=0.5, hand_extra=None):
    """把這隻手臂的 FK 寫進 P（蓋掉 P 裡這隻手原本的 UpperArm／LowerArm／Hand）：手腕到 W、手肘朝 pole、手骨方向＝R（骨架空間）。
    split：手腕要轉的扭轉角有多少比例由前臂負擔（twist_forearm 也是一半一半）。回傳 (手肘位置, 手腕彎的角度)"""
    names = [f"{side}_{n}" for n in ("UpperArm", "LowerArm", "Hand")]
    for n in names:
        P[n] = []
    ua, la, hd = (_bd(arm, "J_Bip_" + n) for n in names)
    Mu = _fkc(arm, P, names[0])
    S = Mu @ ua[0]
    E, Wr, Fu, F0 = _arm_frames(arm, side, S, W, pole)
    if R is None:
        R = F0
    R = Matrix(R)
    # 手相對前臂的扭轉（繞前臂軸）：swing-twist 分解
    rel = (F0.transposed() @ R).to_quaternion()
    tw = 2 * math.atan2(rel.y, rel.w)
    if tw > math.pi:
        tw -= 2 * math.pi
    if tw < -math.pi:
        tw += 2 * math.pi
    Ff = F0 @ Matrix.Rotation(tw * split, 3, "Y")
    d = _delta(Fu @ ua[2].to_3x3().transposed(), Mu.to_3x3())
    P[names[0]] = [d] if d else []
    Ml = _arm_fk(arm, P, side)[1]
    d = _delta(Ff @ la[2].to_3x3().transposed(), Ml.to_3x3())
    P[names[1]] = [d] if d else []
    Mh = _arm_fk(arm, P, side)[2]
    d = _delta(R @ hd[2].to_3x3().transposed(), Mh.to_3x3())
    P[names[2]] = [d] if d else []
    bend = math.degrees(Ff.col[1].angle(R.col[1]))
    return E, bend


def _rest_state(arm, P, side):
    """P 目前的 FK（arms_down 垂著）換成 (W, pole, R)：從這裡內插出去，開頭那格不會跳"""
    ua, la, hd = (_bd(arm, f"J_Bip_{side}_{n}") for n in ("UpperArm", "LowerArm", "Hand"))
    Mu, Ml, Mh = _arm_fk(arm, P, side)
    S = Mu @ ua[0]; E = Ml @ la[0]; W = Mh @ hd[0]
    # 手肘方向點：取「手肘偏離肩→腕連線」的方向，_elbow 會算回同一個手肘位置
    dr = (W - S).normalized()
    pp = (E - S) - dr * (E - S).dot(dr)
    if pp.length < 1e-6:
        pp = Vector((0, 0.1, -0.1))
    pole = S + dr * 0.15 + pp.normalized() * 0.4
    return (W, pole, (Mh.to_3x3() @ hd[2].to_3x3()))


def _elbow_dir(arm, P, side, st):
    """手臂狀態 (W, pole, R) 的手肘在肩膀的哪個方向（單位向量，骨架空間）"""
    S = _shoulder(arm, P, side)
    return (_elbow(arm, side, S, st[0], st[1])[0] - S).normalized()


def _mix_arm(A, B, w, bulge=None, pbulge=None, arm=None, P=None, side=None, elbow="bend"):
    """兩個手臂狀態 (W, pole, R) 內插；bulge：手腕在中段往外繞多少。
    給了 arm／P／side 時，手肘方向在肩膀周圍的球面上內插（slerp）：手肘方向點直線內插會在中途剛好落到「肩→腕」那條線上，
    手肘一格從上面翻到下面；球面內插的手肘一直離那條線有一段距離。pbulge：手肘方向往這邊偏（中段最多）"""
    if w <= 0:
        return A
    if w >= 1:
        return B
    W = Vector(A[0]).lerp(Vector(B[0]), w)
    h = 4.0 * w * (1.0 - w)
    if bulge is not None:
        W = W + Vector(bulge) * h
    if arm is not None:
        S = _shoulder(arm, P, side)
        # elbow="bend"（預設）：內插「手肘往哪邊彎」（垂直於肩→腕軸的那個方向，_elbow 的 pp），再投影到目前的軸上——
        # 手臂打直時手肘本來就貼著軸，內插手肘位置會在打直附近亂跳；彎的方向永遠和軸垂直，不會
        if elbow == "bend":
            pa = _elbow(arm, side, S, A[0], A[1])[3]; pb = _elbow(arm, side, S, B[0], B[1])[3]
            dd = _slerp_dir(pa, pb, w)
            if pbulge is not None:
                dd = (dd + Vector(pbulge).normalized() * 0.6 * h).normalized()
            ax = (W - S).normalized()
            dd2 = dd - ax * dd.dot(ax)
            if dd2.length < 0.2:                               # 剛好轉到軸上（很少見）：改用兩端彎向的平均
                dd2 = (pa + pb) - ax * (pa + pb).dot(ax)
            pole = S + dd2.normalized() * 0.5 + ax * 0.1
        else:                                                  # elbow="dir"：手肘位置（從肩膀看的方向）球面內插——手臂一直彎著時路徑最短
            dd = _slerp_dir(_elbow_dir(arm, P, side, A), _elbow_dir(arm, P, side, B), w)
            if pbulge is not None:
                dd = (dd + Vector(pbulge).normalized() * 0.6 * h).normalized()
            pole = S + dd * 0.5
        # 手的方向「相對前臂」內插：世界空間直接 slerp 的話，中途手和前臂脫節，前臂扭轉會衝到 ±180° 翻面
        Fa = _arm_frames(arm, side, S, A[0], A[1])[3]; Fb = _arm_frames(arm, side, S, B[0], B[1])[3]
        Fc = _arm_frames(arm, side, S, W, pole)[3]
        ra = (Fa.transposed() @ Matrix(A[2])).to_quaternion(); rb = (Fb.transposed() @ Matrix(B[2])).to_quaternion()
        if ra.dot(rb) < 0:
            rb.negate()
        return (W, pole, Fc @ ra.slerp(rb, w).to_matrix())
    pole = Vector(A[1]).lerp(Vector(B[1]), w)
    if pbulge is not None:
        pole = pole + Vector(pbulge) * h
    qa = Matrix(A[2]).to_quaternion(); qb = Matrix(B[2]).to_quaternion()
    if qa.dot(qb) < 0:
        qb.negate()
    return (W, pole, qa.slerp(qb, w).to_matrix())


def _hold(arm, P, side, G, d, d_loc, off, pole, iters=4, palm=None):
    """手上的道具：握點（手骨局部 off）放到 G、道具軸（手骨局部 d_loc）朝 d（都是骨架空間）→ 手臂狀態 (W, pole, R) 和手腕彎的角度。
    繞道具軸的那個自由度：palm 給了就讓掌心盡量朝 palm；沒給就讓手指方向最接近前臂（手腕彎得最少）"""
    S = _shoulder(arm, P, side); d = Vector(d).normalized(); dl = Vector(d_loc).normalized()
    yl = Vector((0, 1, 0)); c = yl.dot(dl); W = Vector(G)
    if palm is not None:
        R = _rot_map(dl, _PALM_LOC[side], d, Vector(palm))
        W = Vector(G) - R @ Vector(off)
    else:
        for _ in range(iters):
            E, Wr, dr, pp, a = _elbow(arm, side, S, W, pole)
            f = (Wr - E).normalized()
            p = f - d * f.dot(d)
            if p.length < 1e-6:
                p = Vector((0, 0, 1)) - d * d.z
            p.normalize()
            R = _rot_map(dl, yl, d, d * c + p * math.sqrt(max(0.0, 1 - c * c)))
            W = Vector(G) - R @ Vector(off)
    E, Wr, dr, pp, a = _elbow(arm, side, S, W, pole)
    return (W, Vector(pole), R), math.degrees((Wr - E).angle(R.col[1]))


def _place_hand(R, pt_loc, pt):
    """手骨方向 R、手骨局部的點 pt_loc 要落在 pt → 手腕位置"""
    return Vector(pt) - Matrix(R) @ Vector(pt_loc)


def _elbow_behind(arm, P, side, W, R, push=None):
    """手肘方向點取在「手指方向的正後方」（前臂和手掌接近一直線）；push：再往這個方向推（避開身體）"""
    L1, L2 = _len_arm(arm, side)
    S = _shoulder(arm, P, side)
    E = Vector(W) - Matrix(R).col[1] * L2
    p = E + (E - (S + Vector(W)) * 0.5) * 2.0
    return p + Vector(push) if push is not None else p


def _bone_quats(arm, P, side, st_):
    """手臂狀態套進去之後，上臂、前臂（含扭轉）、手骨在骨架空間的方向（四元數）"""
    Sh = _shoulder(arm, P, side); E, Wr, Fu, F0 = _arm_frames(arm, side, Sh, st_[0], st_[1])
    R = Matrix(st_[2]); rel = (F0.transposed() @ R).to_quaternion()
    tw = 2 * math.atan2(rel.y, rel.w)
    tw = (tw + math.pi) % (2 * math.pi) - math.pi
    return [Fu.to_quaternion(), (F0 @ Matrix.Rotation(tw * 0.5, 3, "Y")).to_quaternion(), R.to_quaternion()]


def _arc_table(arm, P, sample, n=60):
    """重新參數化：sample(w)（w 0~1）→ {side: 手臂狀態}。內插參數均勻走時骨頭轉速並不均勻（中段快）；
    先沿路徑量手臂各骨頭的累計轉角（每一步取最大的那根），回傳 x→w 的反查：x 均勻走時，最快的骨頭也接近等速"""
    ws, cum, prev = [], [0.0], None
    for i in range(n + 1):
        w = i / n
        q = []
        for sd, st_ in sample(w).items():
            q += _bone_quats(arm, P, sd, st_)
        if prev is not None:
            cum.append(cum[-1] + max(math.degrees(min(a.rotation_difference(b).angle, 2 * math.pi - a.rotation_difference(b).angle))
                                     for a, b in zip(q, prev)))
        prev = q; ws.append(w)
    tot = cum[-1] or 1.0

    def inv(x):
        x = max(0.0, min(1.0, x)); tgt = x * tot
        for i in range(1, len(cum)):
            if cum[i] >= tgt:
                f = (tgt - cum[i - 1]) / max(1e-9, cum[i] - cum[i - 1])
                return ws[i - 1] + (ws[i] - ws[i - 1]) * f
        return 1.0
    inv.total = tot
    return inv


# 伸手偷牽時手指半張（relax 和 open 之間 45%），抱頭時從這裡收成 cup
HANDS.setdefault("reach", dict(Thumb=(4.4, 6.6, 5.5), Index=(4.4, 8.6, 6.4), Middle=(6.6, 10.8, 7.5), Ring=(8.8, 13.0, 8.6), Little=(11.0, 15.2, 9.7), spread=0.7))


def _tr(s, a, b, r=0.3):
    """梯形速度的 0→1（前 r 加速、中段等速、後 r 減速）：最高速＝平均的 1/(1−r) 倍，比 smoothstep 的 1.5 倍低"""
    return _trap((s - a) / (b - a), r)


def _mixf(a, b, w):
    """兩組表情內插"""
    return {n: a.get(n, 0.0) * (1 - w) + b.get(n, 0.0) * w for n in set(a) | set(b)}


def _hands(hand, near, far="relax"):
    return (near, far) if hand == "L" else (far, near)


def _wrap(state, dur, standing, arm):
    """state(秒) → 動作函式 fn(t)：把每隻手臂的 (W, pole, R) 換成 FK 寫進姿勢"""
    def fn(t):
        S = state(t * dur)
        P = dict(S["P"])
        if standing:
            posture(P); P["_posture_done"] = True        # 男性站姿骨盆修正（手臂 FK 在這之後算，手的位置不變）；膝蓋由 pose_lib.stand_fix 統一處理
        for sd in ("L", "R"):
            W, pole, R = S["arms"][sd]
            _arm_set(arm, P, sd, W, pole, R)
        out = dict(P, hands=S["hands"], root=S["root"], face=S["face"])
        if standing:
            out["feet"] = PLANT
        else:
            out["ground"] = False
        return out
    fn.dur = dur; fn.state = state
    return fn


# ════════ 第 2 幕：偷牽手（新郎） ════════
V12_HAND_B = (0.222, -0.062, 0.812)  # 新娘右手（idle 垂在身側）掌心的世界座標：新娘站在 x=+0.42 時（2026-10-06 在新娘骨架上量的）


def sneak_hand(target=V12_HAND_B, me=V12_STAGE["groom"], gap=0.12, look=34.0, dur=1.3, hand="L", arm=None):
    """站姿面向鏡頭 → 頭轉向她（新郎在畫面左、她在畫面右＝新郎的左邊）偷看、上身往她那邊微探 →
    左手從身側慢慢伸向她的手，約 0.8 秒停在她手前 gap 公尺（不碰到）→ 停住到結束（手指微微猶豫）。
    target：她那隻手的世界座標；me：自己的站位；gap：手掌中心停在離她的手多遠；look：轉頭角度（度，正值＝往左）；hand：伸哪隻手。
    構不到時手停在手臂伸到 9 成的地方（fn.gap＝實際離她的手多遠）。預設站位兩人相距 0.84 m、她的手垂在 0.81 m 高（比新郎自己垂手還低）：
    新郎實測只伸得到 0.27 m 前；要停在 10～15 cm 前，兩人要站近到約 0.65 m，或她的手抬高 / 往他那邊伸一點"""
    arm = arm or ARM; k = _kof(arm)
    sg = 1 if hand == "L" else -1
    T = _to_local(target, me)
    L1, L2 = _len_arm(arm, hand)

    def st(s):
        h = seg(s, 0.0, 0.45); l = seg(s, 0.10, 0.80)
        b = {"sx": 2.0 * l, "sy": sg * 4.0 * l, "cy": sg * 2.5 * l, "cz": sg * 4.0 * l,
             "nz": 0.22 * sg * look * h, "hz": 0.78 * sg * look * h, "hx": 5.0 * h, "hy": sg * 2.0 * h}
        return b, (sg * 0.022 * k * l, 0.0, -SOFT_KNEE * k)

    b1, r1 = st(dur)
    P1 = _body(arms_down({}), b1)
    S1 = _shoulder(arm, P1, hand)                    # 骨架空間（身體探過去之後）
    Tl = T - Vector(r1)
    u = (Tl - S1); u.z *= 0.6; u.normalize()
    W = Tl - u * (gap + 0.055 * k)
    lim = 0.90 * (L1 + L2)
    if (W - S1).length > lim:
        W = S1 + (W - S1).normalized() * lim
    pole_reach = S1 + Vector((sg * 0.30, 0.22, -0.18)) * k
    E, Wr, Fu, F0 = _arm_frames(arm, hand, S1, W, pole_reach)
    gap_real = (Tl - (Wr + F0.col[1] * 0.055 * k)).length
    Wc = W + Vector(r1)                              # 伸到的位置固定在角色座標（世界不動）

    def state(s):
        s = max(0.0, min(dur, s))
        b, root = st(s)
        P = _body(arms_down({}), b)
        r = seg(s, 0.15, 0.85)
        hes = seg(s, 0.80, 0.95) * 0.007 * k * math.sin(2 * math.pi * max(0.0, s - 0.8) / 0.5)
        reach = (Wc + u * hes - Vector(root), pole_reach + Vector(r1) - Vector(root), F0)
        arms = {hand: _mix_arm(_rest_state(arm, P, hand), reach, r, arm=arm, P=P, side=hand),
                _alt(hand): _rest_state(arm, P, _alt(hand))}
        face = {"Fcl_ALL_Fun": 0.35 + 0.25 * seg(s, 0.1, 0.5), "Fcl_EYE_Close": 0.12 * seg(s, 0.1, 0.5)}
        return dict(P=P, root=root, arms=arms, hands=_hands(hand, ("relax", "reach", round(r, 2))), face=face, body=b)

    fn = _wrap(state, dur, True, arm)
    fn.hand = hand; fn.gap = gap_real; fn.target_local = T; fn.me = me
    fn.times = dict(look=(0.0, 0.45), lean=(0.10, 0.80), reach=(0.15, 0.85))
    return fn


# ════════ 第 2 幕：被敲抱頭（新郎） ════════
def bonked(target=V12_HAND_B, me=V12_STAGE["groom"], gap=0.12, look=34.0, sneak_dur=1.3, dur=1.3, hand="L", arm=None):
    """從 sneak_hand（同一組 target／me／gap／look／hand）的結尾開始：
    0～0.2 秒頭一縮、縮脖子、閉眼 → 雙手抱頭（0.95 秒按到頭兩側斜上方的頭髮上、手指往後腦勺）、表情委屈 →
    0.84 秒起另一隻手放到胸前、伸出去的那隻手揉頭頂、轉頭對她傻笑。手跟著頭算（頭縮、轉時手不會離開頭頂）。
    分鏡寫「0.15～0.5 秒雙手抱頭」：0.35 秒把雙手從腰邊舉到頭頂，最快的骨頭每格約 30°，超過檢查門檻（每格 15°），所以雙手 0.95 秒才到頭上；另一隻手也只放到胸前（完全垂下要每格 30°），接下一個動作（鞠躬）時淡入就會垂下"""
    arm = arm or ARM; k = _kof(arm)
    sg = 1 if hand == "L" else -1
    pre = sneak_hand(target, me, gap, look, sneak_dur, hand, arm)
    S0 = pre.state(sneak_dur)
    b0, r0, face0 = S0["body"], S0["root"], S0["face"]
    # 手按在頭頂兩側（rest 骨架空間，之後跟著 Head 轉）：掌心貼著頭頂斜上方的頭髮（離頭髮 4 mm）、手指往後腦勺、手肘往外偏前。
    # 不用「手指朝內、掌心朝下」：從垂手轉到那樣手掌要翻 180°；手指朝後只要轉約 100°
    hc = _bd(arm, "J_Bip_C_Head")[0] + Vector((0.0, 0.015 * k, 0.105 * k))           # 頭的中心（rest）
    on = {}
    for sd, sgn in (("L", 1), ("R", -1)):
        dv = Vector((sgn * math.cos(math.radians(40)), -0.12, math.sin(math.radians(40)))).normalized()
        c, n = _surface(arm, ("_Hair", "_HairBack", "_Face"), hc + dv * 0.4, -dv)
        if c is None:
            c, n = hc + dv * 0.11 * k, dv
        fdir = Vector((0.0, 1.0, 0.25)); fdir = fdir - n * fdir.dot(n)
        on[sd] = (_rot_map(Vector((0, 1, 0)), _PALM_LOC[sd], fdir, -n), c + n * 0.004 * k)
    # 揉頭頂：伸出去的那隻手 0.8～1.15 秒從頭側滑到頭頂（斜上 70°），0.98 秒起揉
    sgh = 1 if hand == "L" else -1
    dv = Vector((sgh * math.cos(math.radians(70)), -0.05, math.sin(math.radians(70)))).normalized()
    c, n = _surface(arm, ("_Hair", "_HairBack", "_Face"), hc + dv * 0.4, -dv)
    if c is None:
        c, n = hc + dv * 0.11 * k, dv
    fdir = Vector((-sgh * 0.3, 1.0, 0.1)); fdir = fdir - n * fdir.dot(n)
    on_top = (_rot_map(Vector((0, 1, 0)), _PALM_LOC[hand], fdir, -n), c + n * 0.004 * k)
    BUL = {"L": Vector((0.02, -0.16, 0.0)) * k, "R": Vector((-0.02, -0.16, 0.0)) * k}     # 手往頭上移時從身體前面繞上去（從外側繞會經過「手肘方向和手臂同一直線」的地方）
    PUSH = {"L": Vector((0.10, -0.05, 0.0)) * k, "R": Vector((-0.10, -0.05, 0.0)) * k}
    # 手肘方向：一開始舉手就轉向「往外」（抱頭時手肘本來就往兩側張開）。手肘方向若用兩端姿勢內插，
    # 途中會和「肩→腕」那條線幾乎重合（量到只差 6～12°），手肘解會亂跳、上臂多繞將近一倍的路
    ELB = {"L": Vector((0.9, -0.25, 0.1)).normalized(), "R": Vector((-0.9, -0.25, 0.1)).normalized()}
    ELB_D = {"L": Vector((0.8, 0.1, -0.6)).normalized(), "R": Vector((-0.8, 0.1, -0.6)).normalized()}

    def body_at(s):
        f = seg(s, 0.0, 0.22)                        # 縮
        back = seg(s, 0.0, 0.45)                     # 上身收回
        g = seg(s, 0.88, 1.25)                       # 轉頭傻笑
        flin = f * (1 - 0.45 * seg(s, 0.35, 0.9))
        b = _mixd(b0, {}, back)
        b["hx"] = b0["hx"] * (1 - f) + 12.0 * flin + 2.0 * g
        b["nx"] = 7.0 * flin
        b["hz"] = b0["hz"] * (1 - 0.7 * f) * (1 - g) + 0.70 * sg * look * g
        b["nz"] = b0["nz"] * (1 - 0.7 * f) * (1 - g) + 0.20 * sg * look * g
        b["hy"] = b0["hy"] * (1 - f) + sg * 7.0 * g
        b["shl"] = b["shr"] = 10.0 * flin
        return b, (r0[0] * (1 - back), 0.0, -(SOFT_KNEE + 0.012 * flin) * k), f, g

    def arms_at(P, hold, down, ph=0.0, amp=0.0, top=0.0):
        Mh = _fkc(arm, P, "Head")
        o = _alt(hand); so = 1 if o == "L" else -1
        Rw = _rot_map(Vector((0, 1, 0)), _PALM_LOC[o], Vector((-so * 0.5, -0.3, 0.8)), Vector((-so * 0.6, 0.7, 0.0)))
        Ww = Vector((so * 0.19, -0.13, 1.30)) * k
        waist = (Ww, _shoulder(arm, P, o) + ELB_D[o] * 0.5, Rw)      # 另一隻手放到胸前（手肘彎、手掌朝內，接下一個動作再垂下）
        arms = {}
        for sd in ("L", "R"):
            rub = Vector((math.sin(ph), 0.6 * (1 - math.cos(ph)), 0.0)) * amp if sd == hand else Vector((0, 0, 0))
            R0, pc = on[sd]
            if sd == hand and top > 0:                                 # 滑到頭頂
                qa = R0.to_quaternion(); qb = on_top[0].to_quaternion()
                if qa.dot(qb) < 0:
                    qb.negate()
                R0 = qa.slerp(qb, top).to_matrix(); pc = pc.lerp(on_top[1], top)
            R = Mh.to_3x3() @ R0
            Wt = _place_hand(R, _palm_pt(arm, sd, k), Mh @ (pc + rub))
            Sh = _shoulder(arm, P, sd)
            on_head = (Wt, Sh + ELB[sd] * 0.5, R)
            st0 = S0["arms"][sd] if sd == hand else _rest_state(arm, P, sd)
            up_ = _mix_arm(st0, on_head, hold, BUL[sd], None, arm=arm, P=P, side=sd, elbow="dir")
            if 0 < hold < 1:                                           # 手肘方向：前 35% 就轉到往外
                up_ = (up_[0], Sh + _slerp_dir(_elbow_dir(arm, P, sd, st0), ELB[sd], min(1.0, hold / 0.35)) * 0.5, up_[2])
            if sd != hand and down > 0:
                dn = _mix_arm(up_, waist, down, BUL[sd] * 0.5, None, arm=arm, P=P, side=sd, elbow="dir")
                arms[sd] = (dn[0], Sh + _slerp_dir(ELB[sd], ELB_D[sd], down) * 0.5, dn[2])
            else:
                arms[sd] = up_
        return arms

    def state(s):
        s = max(0.0, min(dur, s))
        b, root, f, g = body_at(s)
        hold = _tr(s, 0.0, 0.95, 0.38)      # 雙手上頭（0.5 秒內舉到頭頂要每格 30°，超過檢查門檻 15°，所以拉到 0.95 秒）
        down = _tr(s, 0.84, 1.30, 0.40)              # 另一隻手放到胸前
        sr = seg(s, 0.10, 0.60) * (1 - seg(s, 0.85, 1.20))     # 委屈
        P = _body(arms_down({}), b)
        ph = 2 * math.pi * 1.25 * seg(s, 0.98, 1.27); amp = 0.010 * k * bump(s, 0.98, 1.06, 1.18, 1.27)
        arms = arms_at(P, hold, down, ph, amp, seg(s, 0.80, 1.15))
        face = _mixf(face0, {}, f)
        face.update({"Fcl_EYE_Close": max(face.get("Fcl_EYE_Close", 0.0), f * (1 - g), 0.25 * g), "Fcl_MTH_I": 0.55 * f * (1 - sr),
                     "Fcl_ALL_Sorrow": 0.85 * sr, "Fcl_MTH_U": 0.25 * sr, "Fcl_ALL_Joy": 0.85 * g, "Fcl_MTH_A": 0.15 * g})
        hh = ("reach", "cup", round(hold, 2)); ho = ("relax", "cup", round(hold * (1 - down), 2))
        return dict(P=P, root=root, arms=arms, hands=_hands(hand, hh, ho), face=face, body=b)

    fn = _wrap(state, dur, True, arm)
    fn.hand = hand; fn.me = me
    fn.times = dict(flinch=(0.0, 0.20), hands_up=(0.0, 0.95), other_down=(0.84, 1.30), rub=(0.98, 1.27), grin=(0.88, 1.25))
    return fn


# ════════ 第 2 幕：玩具槌敲頭（新娘） ════════
V12_HEAD_G = (-0.236, 0.021, 1.673)  # 新郎頭被敲的點（世界座標）：新郎站 x=-0.42、sneak_hand 結尾往她那邊探時，頭髮表面朝她那側斜上 15°（在新郎骨架上量的）


# 握拳斜握槌柄（2026-10-06 改）：槌柄從小指根斜到食指根穿過拳心、和手指方向差 50°（AX_MALLET），四指包住、拇指壓在前面（hammer 手勢：
# 食指彎得少、小指彎得多，才貼得住斜的槌柄）。舊版用 grip 手勢（拿香檳杯的圓弧手型），手指沒有包住槌柄、槌柄離掌心 1 cm，看起來像手腕折到。
# 握點＝拳心（手骨局部，新娘手上量的：半徑 1.3 cm 的槌柄，皮膚最深穿進 0.5 mm、四周手指離槌柄 1～6 mm）
HANDS.setdefault("hammer", dict(Thumb=(40, 50, 40), Index=(34, 48, 32), Middle=(45, 56, 34), Ring=(55, 62, 36), Little=(64, 67, 36),
                                spread=-3, thumb_in=20.0))
OFF_HAMMER = (-0.035, 0.052, 0.000)
_PROP["mallet"] = (OFF_HAMMER, AX_MALLET)


V12_HEADC_G = (-0.341, 0.021, 1.645)   # 新郎頭的中心（世界座標，sneak_hand 結尾；頭頂頭髮在它正上方 10 cm，在新郎骨架上量的）


def _tw_of(arm, P, side, st_):
    """手相對前臂（_arm_frames 的不扭轉前臂）的扭轉角（度，−180～180）"""
    S = _shoulder(arm, P, side); E, Wr, Fu, F0 = _arm_frames(arm, side, S, st_[0], st_[1])
    rel = (F0.transposed() @ Matrix(st_[2])).to_quaternion()
    return (math.degrees(2 * math.atan2(rel.y, rel.w)) + 180.0) % 360.0 - 180.0


def mallet_bonk(target=V12_HEAD_G, me=V12_STAGE["bride"], hit_el=15.0, dur=1.8, hand="R", head_c=V12_HEADC_G, arm=None):
    """站姿；開頭右手已經在背後握著槌（手在右後腰、前臂往後平放、槌頭朝後上方藏在背後）→ 0～0.5 秒一口氣從背後抽出來、
    由右側往上再往他那邊劃弧（上身同時轉向他＝畫面左），0.5 秒槌面敲中他的頭 → 0.5～0.8 秒回彈（往回 11 cm、往上 7 cm）→
    1.38 秒把槌扛在右肩（槌柄往後上方、槌頭在肩膀後面）、下巴微抬、得意。手不高過自己的頭。
    握法（2026-10-06 改）：拳頭握住槌柄（hammer 手勢，槌柄斜穿過拳心，握點／槌柄方向見 held_prop('mallet')），
    手腕只往小指那側偏（敲中前後最多約 29°），不往掌心折。
    head_c：他頭的中心（世界座標）。給了（預設）就在他頭上往她那側的半圈找「槌面正對頭髮、手腕最不彎」的敲擊點與槌柄角度，
    target／hit_el 不用；fn.hit_point（角色座標）＝實際敲中的頭髮表面點，fn.hit_choice＝選到的仰角、手腕彎、扭轉。
    head_c=None 時照舊：target＝槌面打到的點、hit_el＝打下去的角度（舊版槌面沒有正對頭，離頭髮約 4 cm）。
    分鏡寫「0～0.25 秒抽出、0.25～0.5 秒劃弧」：分兩段（中間停在舉起的姿勢）時最快的骨頭每格 20～60°，超過門檻，所以合成一段連續的弧。
    前一段接 idle 時，淡入那 0.3～0.4 秒就是「手伸到背後」"""
    arm = arm or ARM; k = _kof(arm)
    sg = 1 if hand == "L" else -1                    # 拿槌那一側的 x 符號
    T = _to_local(target, me)
    hdir = Vector((T.x, T.y, 0.0)).normalized()      # 往他的水平方向
    tsg = 1 if hdir.x > 0 else -1                    # 轉向他：繞 Z 的正負號（他在 +X＝左邊 → 正）
    be = math.radians(hit_el)
    face_n = hdir * math.cos(be) + Vector((0, 0, -math.sin(be)))     # 槌面打進去的方向
    u_hit = hdir * math.sin(be) + Vector((0, 0, math.cos(be)))       # 敲中時槌柄方向（拳頭 → 槌頭）
    Lg = MALLET["handle"] - MALLET["end"] + MALLET["head_r"]
    C = T - face_n * (MALLET["head_len"] / 2)                        # 敲中時槌頭中心
    G_hit = C - u_hit * Lg
    off = _offk(OFF_HAMMER, hand, k); dl = Vector(AX_MALLET)
    sgp = 1 if hand == "R" else -1                   # 掌心＝槌柄 × 槌面方向（右手；左手反號）：用它把槌面轉到正對他的頭
    look_t = max(-55.0, min(55.0, math.degrees(math.atan2(T.x, -T.y))))
    # 關鍵姿勢。敲中、回彈：照目標精確算槌的位置與方向（_hold）；藏槌、扛肩：「中性握法」——手和前臂不扭不彎
    # （手骨方向＝前臂方向），槌的方向就是握在手裡自然的方向。關鍵之間「相對前臂」內插（_mix_arm），手腕不會被硬擰。
    # 藏槌姿勢：手在右後腰、前臂往後平放、拇指朝上（槌頭朝後上方，藏在背後）——揮出去主要只是前臂繞垂直軸擺過來，
    # 不必同時自轉；試過「手垂在臀後、掌心朝後」，揮出去要邊擺邊自轉，最快的骨頭每格 30～60°
    W0, E0 = Vector((sg * 0.14, 0.14, 1.04)) * k, Vector((sg * 0.22, -0.18, 0.98)) * k                # 藏在背後
    W4, E4 = Vector((sg * 0.20, -0.13, 1.28)) * k, Vector((sg * 0.23, -0.21, 1.04)) * k               # 扛在肩上：拳頭在右肩前、前臂往後上方斜（槌柄往後靠在肩上、槌頭在背後）
    want4 = Vector((sg * 0.20, 0.75, 0.63)).normalized()                                               # 扛肩時槌柄的方向（往後上方，槌頭在肩膀後面、離他遠）
    pole_hit = Vector((sg * 0.30, 0.10, 0.95)) * k
    up_w = Vector((sg * 0.10, 0.77, 0.64))
    hit_s = 0.50

    def keys(P, root):
        rt = Vector(root); S_ = _shoulder(arm, P, hand)
        def neutral(W, E, want=None):
            Wa = W - rt; pl = E - rt
            R = _arm_frames(arm, hand, S_, Wa, pl)[3]
            if want is not None:                     # 手連前臂一起繞前臂軸轉，讓槌柄最接近 want（手腕不彎）
                best = None
                for th in range(-180, 180, 5):
                    Rt = R @ Matrix.Rotation(math.radians(th), 3, "Y"); sc_ = (Rt @ dl).dot(want)
                    if best is None or sc_ > best[0]:
                        best = (sc_, Rt)
                R = best[1]
            return (Wa, pl, R)
        k2, _ = _hold(arm, P, hand, G_hit - rt, u_hit, dl, off, pole_hit - rt, palm=sgp * u_hit.cross(face_n))     # 槌面正對他的頭
        u3 = _slerp_dir(u_hit, up_w, 0.25); n3 = (face_n - u3 * face_n.dot(u3)).normalized()
        k3, _ = _hold(arm, P, hand, G_hit - hdir * 0.11 * k + Vector((0, 0, 0.07 * k)) - rt, u3, dl, off, pole_hit - rt)   # 回彈：往回 11 cm、往上 7 cm（手腕回到最不彎）
        return [neutral(W0, E0), k2, k3, neutral(W4, E4, want4)]

    def body_at(s):
        tw = seg(s, 0.12, hit_s) * (1 - 0.65 * seg(s, 0.65, 1.30))
        lk = seg(s, 0.10, 0.45) * (1 - seg(s, 0.70, 1.30))
        end = seg(s, 0.9, 1.45)
        b = {"sz": tsg * 8.0 * tw, "cz": tsg * 6.0 * tw, "sy": tsg * 4.0 * tw, "sx": 2.0 * tw,
             "nz": 0.22 * look_t * lk + tsg * 3.0 * end, "hz": 0.78 * look_t * lk + tsg * 5.0 * end,
             "hx": -8.0 * lk - 7.0 * end, "hy": -tsg * 5.0 * end}
        return b, (hdir.x * 0.02 * k * tw, 0.0, -SOFT_KNEE * k)

    # 敲哪裡、槌柄朝哪（head_c 給了才找；None＝照 target／hit_el 舊算法）：他頭上往她那側的半圈（仰角 10～70°、左右 ±30°），
    # 每一點的槌面都正對頭的表面（槌面法線＝往頭中心），槌柄繞法線轉一圈；取手腕彎最少、前臂扭轉在 ±80° 內、手臂不必打直、仰角高一點的組合。
    # 固定 target＋hit_el 時槌面要正對頭，手腕得彎 50～70°（像折到）；舊版沒對正，槌面離頭髮 4 cm
    if head_c is not None:
        Hc = _to_local(head_c, me); rr = 0.105 * k; La = sum(_len_arm(arm, hand))
        b_h, root_h = body_at(hit_s); P_h = _body(arms_down({}), b_h); rt_h = Vector(root_h)
        S_h = _shoulder(arm, P_h, hand) + rt_h
        tow = Vector((S_h.x - Hc.x, S_h.y - Hc.y, 0.0)).normalized(); side_ax = Vector((0, 0, 1)).cross(tow); upv = Vector((0, 0, 1))
        best = None
        for el in range(10, 71, 10):
            for az in (-30, -15, 0, 15, 30):
                e_, a_ = math.radians(el), math.radians(az)
                dv = (tow * math.cos(a_) + side_ax * math.sin(a_)) * math.cos(e_) + upv * math.sin(e_)
                Pi = Hc + dv * rr; fn_ = -dv
                e1 = (upv - fn_ * upv.dot(fn_)).normalized(); e2 = fn_.cross(e1)
                for j in range(16):
                    ph = 2 * math.pi * j / 16; u_ = e1 * math.cos(ph) + e2 * math.sin(ph)
                    C_ = Pi - fn_ * (MALLET["head_len"] / 2); G_ = C_ - u_ * Lg
                    st_, bend_ = _hold(arm, P_h, hand, G_ - rt_h, u_, dl, off, pole_hit - rt_h, palm=sgp * u_.cross(fn_))
                    reach = (Vector(st_[0]) - (S_h - rt_h)).length / La
                    tw_ = _tw_of(arm, P_h, hand, st_)
                    sc = bend_ + 1.5 * max(0.0, abs(tw_) - 80.0) + 300.0 * max(0.0, reach - 0.95) - 0.25 * el
                    if best is None or sc < best[0]:
                        best = (sc, fn_, u_, C_, G_, Pi, el, az, bend_, tw_)
        _, face_n, u_hit, C, G_hit, T, hit_el_used, hit_az, hit_bend, hit_tw = best
    else:
        hit_el_used, hit_az, hit_bend, hit_tw = hit_el, 0.0, None, None

    # 揮擊段重新參數化：骨頭轉角對時間照 swing() 的速度曲線走（內插參數均勻走時中段轉得最快）
    _bm, _rm = body_at(0.3); _Pm = _body(arms_down({}), _bm); _Km = keys(_Pm, _rm)
    _bb_of = _arc_table(arm, _Pm, lambda w: {hand: _mix_arm(_Km[0], _Km[1], w, arm=arm, P=_Pm, side=hand)})

    def swing(x, r=0.3):
        """0→1，先加速、之後等速一路到敲中（不減速，敲中後靠回彈反向）：最高速只有平均的 1/(1−r/2) 倍"""
        x = max(0.0, min(1.0, x))
        return (x * x / (2 * r) if x < r else x - r / 2) / (1 - r / 2)

    def state(s):
        s = max(0.0, min(dur, s))
        bb = _bb_of(swing(s / hit_s)) if s < hit_s else 1.0
        c = _ease_out((s - hit_s) / 0.30, 2.0) if s > hit_s else 0.0        # 回彈 0.3 秒（退得比較遠，太快手會每格超過 15°）
        d = seg(s, 0.62, 1.38)
        b, root = body_at(s)
        end = seg(s, 0.9, 1.45)
        P = _body(arms_down({}), b)
        K = keys(P, root)
        st_ = K[0]
        for kk, w in zip(K[1:], (bb, c, d)):
            st_ = _mix_arm(st_, kk, w, arm=arm, P=P, side=hand)
        sway = 0.004 * k * math.sin(2 * math.pi * max(0.0, s - 1.35) / 0.9) * seg(s, 1.35, 1.5)
        st_ = (Vector(st_[0]) + Vector((0, 0, sway)), Vector(st_[1]) + Vector((0, 0, sway)), st_[2])
        Sh = _shoulder(arm, P, hand); E_, Wr, Fu, F0 = _arm_frames(arm, hand, Sh, st_[0], st_[1])
        bend = math.degrees(F0.col[1].angle(Matrix(st_[2]).col[1]))
        hit = bump(s, 0.46, 0.52, 0.56, 0.75)
        a = seg(s, 0.0, 0.3)
        face = {"Fcl_ALL_Fun": 0.5 * (1 - a) + 0.75 * end, "Fcl_EYE_Close": 0.12 * (1 - a) + 0.45 * hit + 0.35 * end * (1 - hit),
                "Fcl_ALL_Angry": 0.25 * a * (1 - end), "Fcl_MTH_E": 0.25 * a * (1 - hit) * (1 - end), "Fcl_ALL_Joy": 0.7 * hit}
        return dict(P=P, root=root, arms={hand: st_, _alt(hand): _rest_state(arm, P, _alt(hand))},
                    hands=_hands(hand, "hammer"), face=face, body=b, bend=bend)

    fn = _wrap(state, dur, True, arm)
    fn.hand = hand; fn.me = me; fn.target_local = T
    fn.times = dict(pull_and_swing=(0.0, hit_s), hit=hit_s, rebound=(hit_s, hit_s + 0.30), shoulder=(0.62, 1.38))
    fn.hit_head = C                                   # 敲中時槌頭中心（角色座標）
    fn.hit_point = T; fn.hit_dir = face_n; fn.hit_choice = dict(el=hit_el_used, az=hit_az, bend=hit_bend, tw=hit_tw)
    return fn


# ════════ 第 2 幕：抽槌上肩（mallet_draw）→ 跳起來從斜上方敲頭（mallet_jump_bonk）（新娘，2026-10-07） ════════
_MALLET_REST = ((0.20, -0.13, 1.28), (0.23, -0.21, 1.04), (0.20, 0.75, 0.63))   # 扛在右肩：拳頭、手肘（rest 座標，跟著 UpperChest）、槌柄方向（胸口座標；往後上方，槌頭在肩膀後面）


def _neutral_arm(arm, P, side, Wl, El, k, want=None, M=None, twist=None):
    """手腕不彎（手骨＝前臂方向）的手臂狀態：拳頭 Wl、手肘方向點 El（rest 座標，M＝跟著哪個框架，預設 UpperChest）；
    want 給了就讓手連前臂一起繞前臂軸轉，讓槌柄（AX_MALLET）最接近 want（M 的座標）；twist（度）給了就直接繞前臂軸轉這麼多（不看 want）"""
    sg = 1 if side == "L" else -1
    M = M if M is not None else _fkc(arm, P, "UpperChest")
    W = M @ (Vector((sg * Wl[0], Wl[1], Wl[2])) * k); E = M @ (Vector((sg * El[0], El[1], El[2])) * k)
    S = _shoulder(arm, P, side); R = _arm_frames(arm, side, S, W, E)[3]
    if twist is not None:
        R = R @ Matrix.Rotation(math.radians(twist), 3, "Y")
    elif want is not None:
        wv = (M.to_3x3() @ Vector((sg * want[0], want[1], want[2]))).normalized(); dl = Vector(_mir(AX_MALLET, side)); best = None
        for th in range(-75, 76, 3):                                 # 前臂＋手腕大約只能扭 ±75°
            Rt = R @ Matrix.Rotation(math.radians(th), 3, "Y"); sc_ = (Rt @ dl).dot(wv)
            if best is None or sc_ > best[0]:
                best = (sc_, Rt)
        R = best[1]
    return (W, E, R)


def _mallet_rest(arm, P, side, k):
    return _neutral_arm(arm, P, side, _MALLET_REST[0], _MALLET_REST[1], k, _MALLET_REST[2])


def _stand_legs(arm, P, root, rz, feet):
    """站著／跳躍的腿：feet＝{side: (腳踝目標（角色座標）, 腳尖朝向 rz)} → 寫進 P"""
    for sd in ("L", "R"):
        Aw, fy = feet[sd]
        Aa = _world_to_arm(Aw, root, rz); rel = fy - rz
        _leg_set(arm, P, sd, Aa, Aa + _foot_dir(rel) * 0.5 + Vector((0, 0, 0.35)), rel)


def mallet_draw(dur=0.7, hand="R", arm=None):
    """從背後抽出槌、扛上右肩（新娘）：開頭右手繞到背後（手肘在身體右側、拳頭在右肩胛骨下方）、槌柄橫在背後往左、槌頭在左肩後面——
    從正面看槌大部分被身體擋住，只有槌頭從左肩後露出一點（和 mallet_bonk 的開頭不同）→ 0～dur 秒手從身體右側往外繞到右胸前、前臂立起來，
    槌柄往後上方靠在右肩上（槌頭在肩膀後面）；
    上身跟著微微一轉、嘴角上揚。結尾＝mallet_jump_bonk 的開頭（站姿、槌扛右肩）。
    握法 hammer（拳頭握、手腕不彎）。站在原點、面向 -Y（情境用 pose_frame_at(ARM, fn(t), *me)）。
    2026-10-07：開頭姿勢重找過（舊版開頭槌其實橫在右腰側、從正面看得到）；最短約 0.6 秒（每格 13.9°、速度突變 6.0 剛好在門檻上），預設 0.7 秒"""
    arm = arm or ARM; k = _kof(arm); B = arm.data.bones
    sg = 1 if hand == "L" else -1
    a0 = {sd: B[f"J_Bip_{sd}_Foot"].head_local.copy() for sd in ("L", "R")}
    feet = {sd: (a0[sd].copy(), 0.0) for sd in ("L", "R")}
    root = (0.0, 0.0, -SOFT_KNEE * k)
    REF = {}

    def state(s, W_=None):
        s = max(0.0, min(dur, s))
        tw = bump(s, 0.0, 0.25 * dur, 0.55 * dur, dur)
        b = {"sz": -sg * 6.0 * tw, "cz": -sg * 4.0 * tw, "nz": sg * 2.0 * tw, "hz": sg * 5.0 * tw}
        P = _body(arms_down({}), b)
        Rt = Vector(root)
        # 藏在背後：手肘在身體右側、拳頭在右肩胛骨下方、前臂扭 75°，槌柄橫在背後往左（離線搜尋：手骨轉到扛肩只要 111°（越少越不超速）、
        # 穿模 0、槌離身體 9 cm；槌頭比肩寬長，從正面看會從左肩後露出一點。要完全藏住大概得把槌朝下藏到腰下——沒試：穿蓬裙時那裡在裙子裡面，抽出來會穿過裙面）
        K0 = _neutral_arm(arm, P, hand, (0.17, 0.21, 1.16), (0.26, 0.10, 0.90), k, twist=75.0)
        K1 = _mallet_rest(arm, P, hand, k)
        w = W_ if W_ is not None else _tr(s, 0.0, dur, 0.35)
        st_ = _mix_arm_fk(K0, K1, w, arm, P, hand, ref=REF, roll=(0.0, 1.0))
        Sh = _shoulder(arm, P, hand); bul = Vector((sg * 0.09, 0.0, 0.0)) * k * math.sin(math.pi * w)   # 中段手往外繞（直線經過身體右側會擦到）
        st_ = (Vector(st_[0]) + bul, Vector(st_[1]) + bul * 1.5, st_[2])
        face = {"Fcl_ALL_Fun": 0.5 + 0.2 * seg(s, 0.2 * dur, dur), "Fcl_MTH_E": 0.15 * tw}
        return dict(P=P, root=root, rz=0.0, feet=feet, arms={hand: st_, _alt(hand): _rest_state(arm, P, _alt(hand))},
                    hands=_hands(hand, "hammer"), face=face, body=b)

    state(0.5 * dur, 0.5)

    def fn(t):
        st_ = state(t * dur)
        P = dict(st_["P"]); _stand_legs(arm, P, st_["root"], st_["rz"], st_["feet"])
        for sd in ("L", "R"):
            W, pl, R = st_["arms"][sd]
            _arm_set(arm, P, sd, W, pl, R)
        return dict(P, hands=st_["hands"], root=st_["root"], rz=st_["rz"], ground=False, face=st_["face"])

    fn.dur = dur; fn.state = state; fn.hand = hand
    fn.times = dict(draw=(0.0, dur))
    return fn


def mallet_jump_bonk(head_c=V12_HEADC_G, me=V12_STAGE["bride"], jump=0.15, t_hit=1.00, land_yaw=-25.0, el=(30, 55), dur=2.25, hand="R", arm=None):
    """跳起來從斜上方敲頭（新娘）：開頭＝mallet_draw 的結尾（站姿、槌扛右肩）→ 0～0.58 秒把槌舉過頭（槌頭在頭頂後上方）、
    0.25～0.62 秒下蹲蓄力、上身轉向他 → 0.62 秒起跳（騰空約 jump 公尺，空中整個人轉 land_yaw 度）→ 0.55～t_hit 秒由上往下揮，
    t_hit 秒槌面從斜上方（仰角 el 度之間自動選）敲在他頭頂靠她那側 → t_hit～t_hit+0.45 秒回彈 → 1.22 秒落地、1.22～1.65 秒膝蓋緩衝 →
    1.40～2.05 秒槌扛回右肩、上身轉回正對骨盆、下巴微抬，站著結束（整個人朝 land_yaw、槌扛右肩，可以接快速鞠躬）。
    握法 hammer（拳頭握），手腕只准往小指那側偏、不往掌心折；敲中點在 head_c（他頭的中心，世界座標）往她那側的上半圈找。
    回傳的 root／rz 是角色座標（情境用 pose_frame_at(ARM, fn(t), *me)）；fn.hit_point（角色座標）＝敲中的頭髮表面點、fn.hit_head＝敲中時槌頭中心"""
    arm = arm or ARM; k = _kof(arm); B = arm.data.bones
    sg = 1 if hand == "L" else -1; sgp = 1 if hand == "R" else -1
    Hc = _to_local(head_c, me); rr = 0.105 * k
    hd = Vector((Hc.x, Hc.y, 0.0)).normalized()
    psi_face = math.degrees(math.atan2(hd.x, -hd.y))
    t_off, t_land = 0.62, 1.22
    a0 = {sd: B[f"J_Bip_{sd}_Foot"].head_local.copy() for sd in ("L", "R")}
    Lg = MALLET["handle"] - MALLET["end"] + MALLET["head_r"]; HL = MALLET["head_len"]
    off = _offk(OFF_HAMMER, hand, k); dl = Vector(_mir(AX_MALLET, hand)); La = sum(_len_arm(arm, hand))
    D = [0.0]
    mid0 = (a0["L"] + a0["R"]) * 0.5

    def flight(s):
        return max(0.0, min(1.0, (s - t_off) / (t_land - t_off)))

    def hop(s):
        u = flight(s)
        return jump * k * (0.5 - 0.5 * math.cos(2 * math.pi * u)) if 0 < u < 1 else 0.0

    def drop(s):
        return (0.08 * bump(s, 0.25, 0.52, 0.52, 0.72) + 0.02 * bump(s, 0.72, 0.85, 0.95, 1.12)
                + 0.07 * bump(s, 1.12, 1.32, 1.32, 1.65)) * k

    def yaw_p(s):
        return 0.30 * land_yaw * seg(s, 0.05, 0.55) + 0.70 * land_yaw * ease(flight(s))

    def yaw_f(s):
        return land_yaw * ease((flight(s) - 0.15) / 0.7)

    def body(s):
        rz = yaw_p(s)
        crouch = bump(s, 0.25, 0.52, 0.52, 0.72); landc = bump(s, 1.12, 1.32, 1.32, 1.65)
        chop = bump(s, 0.62, 0.95, 1.05, 1.40)
        tw = (0.80 * psi_face - rz) * seg(s, 0.05, 0.60) * (1 - seg(s, 1.30, 2.05))      # 胸口比骨盆多轉向他（最後轉回來）
        look = (psi_face - rz - tw) * seg(s, 0.05, 0.50) * (1 - seg(s, 1.30, 2.05))
        end = seg(s, 1.50, 2.10)
        b = {"sz": 0.45 * tw, "cz": 0.55 * tw, "nz": 0.25 * look, "hz": 0.75 * look,
             "shl": 4.0 * crouch, "shr": 4.0 * crouch}
        lean = 10.0 * crouch + 10.0 * chop + 8.0 * landc
        up = -14.0 * seg(s, 0.20, 0.60) * (1 - seg(s, 1.10, 1.40)) - 7.0 * end           # 抬頭看他頭頂；最後下巴微抬
        return b, rz, lean, up, end

    def feet_at(s):
        out = {}
        r1 = math.radians(yaw_f(s)); mv = hd * D[0] * ease(flight(s))
        for sd in ("L", "R"):
            p = a0[sd]; c, sn = math.cos(r1), math.sin(r1)
            out[sd] = (Vector((p.x * c - p.y * sn + mv.x, p.x * sn + p.y * c + mv.y, p.z + hop(s))), yaw_f(s))
        return out

    def body_P(s):
        b, rz, lean, up, end = body(s)
        feet = feet_at(s)
        mid = (feet["L"][0] + feet["R"][0]) * 0.5
        root = (mid.x - mid0.x, mid.y - mid0.y, hop(s) - drop(s) - SOFT_KNEE * k)
        armL = 40.0 * bump(s, 0.45, 0.75, 1.05, 1.45)
        P = _body(arms_down({}, l_fwd=armL, l_out=10.0 * armL / 40.0, l_el=18 + 17 * armL / 40.0), b)
        yc = b["sz"] + b["cz"]; yh = yc + b["nz"] + b["hz"]
        axc = (math.cos(math.radians(yc)), math.sin(math.radians(yc)), 0.0); axh = (math.cos(math.radians(yh)), math.sin(math.radians(yh)), 0.0)
        P["Spine"] = list(P.get("Spine", [])) + [(axc, 0.6 * lean)]; P["Chest"] = list(P.get("Chest", [])) + [(axc, 0.4 * lean)]
        P["Head"] = list(P.get("Head", [])) + [(axh, up - 0.5 * lean)]
        return P, root, rz, feet, b, end

    def hit_search(P, root, rz):
        """敲中那格：他頭上往她那側的上半圈（仰角 el、左右 ±30°）× 槌柄繞槌面法線一圈；槌面正對頭髮，手肘放在讓前臂和手背一直線的方向。
        取手腕最不彎、前臂扭轉 ±80° 內、手臂不必打直、仰角高一點的組合 → (分數, 敲中點, 槌面方向, 槌柄方向, 槌頭中心, 握點, 手臂狀態, 細節)"""
        S_ = _shoulder(arm, P, hand); Ha = _world_to_arm(Hc, root, rz)
        tow = Vector((S_.x - Ha.x, S_.y - Ha.y, 0.0)).normalized(); side_ax = Vector((0, 0, 1)).cross(tow); upv = Vector((0, 0, 1))
        best = None
        for e_ in range(el[0], el[1] + 1, 5):
            for az in (-30, -15, 0, 15, 30):
                er, ar = math.radians(e_), math.radians(az)
                dv = (tow * math.cos(ar) + side_ax * math.sin(ar)) * math.cos(er) + upv * math.sin(er)
                Pi = Ha + dv * rr; fn_ = -dv
                e1 = (upv - fn_ * upv.dot(fn_)).normalized(); e2 = fn_.cross(e1)
                for j in range(24):
                    ph = 2 * math.pi * j / 24; u_ = e1 * math.cos(ph) + e2 * math.sin(ph)
                    C_ = Pi - fn_ * (HL / 2); G_ = C_ - u_ * Lg
                    R = _rot_map(dl, _PALM_LOC[hand], u_, sgp * u_.cross(fn_))
                    W = G_ - R @ off; reach = (W - S_).length / La
                    if reach > 0.97 or reach < 0.35:
                        continue
                    dr = (W - S_).normalized(); yh = R.col[1]; pp = -(yh - dr * yh.dot(dr))
                    if pp.length < 1e-4:
                        continue
                    pole = S_ + dr * 0.15 * k + pp.normalized() * 0.4 * k
                    E, Wr, dr2, pp2, a = _elbow(arm, hand, S_, W, pole)
                    bend = math.degrees((Wr - E).angle(yh))
                    st_ = (W, pole, R); tw_ = _tw_of(arm, P, hand, st_)
                    elb_in = max(0.0, (E.x - S_.x) * (-sg))                   # 手肘跑到肩膀內側（往身體中線）扣分
                    sc = bend + 1.5 * max(0.0, abs(tw_) - 80.0) + 300.0 * max(0.0, reach - 0.92) + 200.0 * elb_in - 0.25 * e_
                    if best is None or sc < best[0]:
                        best = (sc, Pi, fn_, u_, C_, G_, st_, dict(el=e_, az=az, bend=round(bend, 1), tw=round(tw_, 1), reach=round(reach, 2)))
        return best

    # 往他那邊跳多遠：0～25 cm 裡找分數最好的
    bestD = None
    for dd in (0.0, 0.05, 0.10, 0.15, 0.20, 0.25):
        D[0] = dd * k
        P_, root_, rz_, *_ = body_P(t_hit); hs_ = hit_search(P_, root_, rz_)
        if hs_ is not None and (bestD is None or hs_[0] < bestD[0]):
            bestD = (hs_[0], dd * k)
    D[0] = bestD[1]
    P_h, root_h, rz_h, *_ = body_P(t_hit)
    HS = hit_search(P_h, root_h, rz_h)
    _, Pi_a, fn_a, u_a, C_a, G_a, _st, choice = HS
    # 敲中點、方向換成角色座標存起來（每格再換回當時的骨架空間）
    def a2l(v, root, rz, vec=False):
        r = math.radians(rz); c, s_ = math.cos(r), math.sin(r)
        x, y = v.x * c - v.y * s_, v.x * s_ + v.y * c
        return Vector((x, y, v.z)) if vec else Vector((x + root[0], y + root[1], v.z + root[2]))
    Pi_l = a2l(Pi_a, root_h, rz_h); fn_l = a2l(fn_a, root_h, rz_h, True); u_l = a2l(u_a, root_h, rz_h, True)
    C_l = a2l(C_a, root_h, rz_h); G_l = a2l(G_a, root_h, rz_h)
    KH = {}

    def keys(P, root, rz, s=None):
        K0 = _mallet_rest(arm, P, hand, k)
        K1 = _neutral_arm(arm, P, hand, (0.12, 0.04, 1.62), (0.20, -0.10, 1.40), k, (0.05, 0.62, 0.78))    # 舉過頭：拳頭在頭頂右上、前臂直立、槌頭在頭頂後上方
        # 敲中：照敲中點、槌面方向、槌柄方向換到這一格的骨架空間；手肘照「前臂和手背一直線」
        u_ = _world_to_arm(u_l + Vector(root), root, rz) - _world_to_arm(Vector(root), root, rz)
        fn_ = _world_to_arm(fn_l + Vector(root), root, rz) - _world_to_arm(Vector(root), root, rz)
        G_ = _world_to_arm(G_l, root, rz)
        R = _rot_map(dl, _PALM_LOC[hand], u_, sgp * u_.cross(fn_)); W = G_ - R @ off
        S_ = _shoulder(arm, P, hand); dr = (W - S_).normalized(); yh = R.col[1]; pp = -(yh - dr * yh.dot(dr)).normalized()
        K2 = (W, S_ + dr * 0.15 * k + pp * 0.4 * k, R)
        Mc = _fkc(arm, P, "UpperChest")
        if "c" in KH and s is not None and s > t_hit:                 # 敲中之後：手臂跟著胸口（用敲中那一格量的、胸口座標）
            Wc, pc, Rc = KH["c"]; K2 = (Mc @ Wc, Mc @ pc, Mc.to_3x3() @ Rc)
            S_ = _shoulder(arm, P, hand); dr = (K2[0] - S_).normalized()
        # 回彈：從敲中往「舉過頭」那個姿勢彈回去 65%（槌往上、往她自己這邊收，離開他正要抬起來抱頭的手臂；
        # 只跟著胸口往下的話，她落地時槌會掉到他手臂的高度，量到撞在一起）
        K3 = _mix_arm_fk(K2, K1, 0.65, arm, P, hand, ref=REF_K3, roll=(0.0, 1.0))
        return [K0, K1, K2, K3, K0]

    REF = [{}, {}, {}, {}]; REF_K3 = {}

    def swing(x, r=0.3):
        x = max(0.0, min(1.0, x))
        return (x * x / (2 * r) if x < r else x - r / 2) / (1 - r / 2)

    def weights(s):
        return (_tr(s, 0.0, 0.58, 0.3), swing((s - 0.55) / (t_hit - 0.55)),
                _ease_out((s - t_hit) / 0.45, 2.0) if s > t_hit else 0.0, _tr(s, 1.40, 2.05, 0.3))     # 回彈一開始就帶著揮下來的速度（從 0 起步的話，敲中那格速度一頓，突變 8）

    def state(s, W_=None):
        s = max(0.0, min(dur, s))
        P, root, rz, feet, b, end = body_P(s)
        K = keys(P, root, rz, s)
        w = W_ if W_ is not None else weights(s)
        st_ = K[0]
        for i, wi in enumerate(w):
            st_ = _mix_arm_fk(st_, K[i + 1], wi, arm, P, hand, ref=REF[i], roll=(0.0, 1.0))
        hit = bump(s, t_hit - 0.06, t_hit, t_hit + 0.04, t_hit + 0.30)
        a = seg(s, 0.0, 0.40)
        face = {"Fcl_ALL_Fun": 0.4 * (1 - a) + 0.75 * end, "Fcl_ALL_Angry": 0.35 * a * (1 - end), "Fcl_MTH_E": 0.3 * a * (1 - hit) * (1 - end),
                "Fcl_EYE_Close": 0.5 * hit + 0.3 * end * (1 - hit), "Fcl_ALL_Joy": 0.8 * hit}
        return dict(P=P, root=root, rz=rz, feet=feet, arms={hand: st_, _alt(hand): _rest_state(arm, P, _alt(hand))},
                    hands=_hands(hand, "hammer"), face=face, body=b)

    P_h, root_h, rz_h, *_ = body_P(t_hit); K_h = keys(P_h, root_h, rz_h)[2]; Mh_ = _fkc(arm, P_h, "UpperChest"); Mi = Mh_.inverted()
    KH["c"] = (Mi @ K_h[0], Mi @ K_h[1], Mi.to_3x3() @ Matrix(K_h[2]))
    for i, sm in enumerate((0.30, 0.78, t_hit + 0.15, 1.70)):          # 每一段的參考姿勢（上臂自轉角選哪一邊）
        state(sm, [1.0 if j < i else (0.5 if j == i else 0.0) for j in range(4)])

    def fn(t):
        st_ = state(t * dur)
        P = dict(st_["P"]); _stand_legs(arm, P, st_["root"], st_["rz"], st_["feet"])
        for sd in ("L", "R"):
            W, pl, R = st_["arms"][sd]
            _arm_set(arm, P, sd, W, pl, R)
        return dict(P, hands=st_["hands"], root=st_["root"], rz=st_["rz"], ground=False, face=st_["face"])

    fn.dur = dur; fn.state = state; fn.hand = hand; fn.me = me; fn.t_hit = t_hit
    fn.hit_point = Pi_l; fn.hit_dir = fn_l; fn.hit_head = C_l; fn.hit_choice = dict(choice, hop_fwd=round(D[0], 3))
    fn.times = dict(raise_=(0.0, 0.58), crouch=(0.25, 0.62), takeoff=t_off, swing=(0.55, t_hit), hit=t_hit, rebound=(t_hit, t_hit + 0.45),
                    land=t_land, cushion=(t_land, 1.65), shoulder=(1.40, 2.05))
    return fn


# ════════ 第 7 幕：坐姿共用 ════════
V12_MOUTH_B = (0.248, 0.399, 1.024)  # 新娘被餵時（fed 第 2.6 秒）嘴巴的世界座標（預設座位，在新娘骨架上量的）；情境用 fed 的 fn.mouth_world(t) 算實際值
V12_PLATE = (0.03, -0.38)            # 盤子（角色座標 x, y；x 正值＝往拿叉子那隻手那側），盤面高＝桌面 + 1.2 cm
V12_FORK_AT = (0.17, -0.30)          # 叉子一開始平放在桌上的位置（握點）
V12_GLASS_AT = (0.17, -0.27)         # 酒杯在桌上的位置（杯腳中心；x 正值＝往靠對方那隻手那側）
V12_CLINK = (0.0, 0.31, 0.89)        # 碰杯時兩個杯身相碰的點（世界座標，預設座位）
_HOLD_BODY = {"sx": 2.0}


def _seat_P(arm, b, seat):
    P = _body(arms_down({}), b)
    dz = sit_legs(P, seat, arm)
    return P, (0.0, 0.0, dz)


def _table_hand(arm, P, side, root, table, k, x=0.12, y=-0.29):
    """沒事做的那隻手平放在桌上（掌心朝下、手指朝前偏內側，掌心離桌面 3 mm）→ 手臂狀態（骨架空間）"""
    sg = 1 if side == "L" else -1
    fdir = Vector((-sg * 0.30, -1.0, -0.04)).normalized()
    R = _rot_map(Vector((0, 1, 0)), _PALM_LOC[side], fdir, Vector((0, 0, -1)))
    W = _place_hand(R, _palm_pt(arm, side, k), Vector((sg * x * k, y * k, table + 0.003)) - Vector(root))
    return (W, _shoulder(arm, P, side) + Vector((sg * 0.30, 0.25, -0.30)) * k, R)


def _glass_hold_G(k, side, table):
    """胸前拿酒杯時的握點（角色座標）：杯底比桌面高 3 cm"""
    sg = 1 if side == "L" else -1
    return Vector((sg * 0.075 * k, -0.245 * k, table + 0.072))


def _glass(arm, P, side, root, k, G, d=(0, 0, 1), pole_off=None):
    """拿著酒杯（握杯腳）：握點 G（角色座標）、杯子軸 d → 手臂狀態"""
    sg = 1 if side == "L" else -1
    pole = _shoulder(arm, P, side) + (Vector(pole_off) if pole_off is not None else Vector((sg * 0.32, 0.05, -0.32))) * k
    st_, bend = _hold(arm, P, side, Vector(G) - Vector(root), Vector(d), Vector((0, 0, 1)), _offk(OFF_STEM, side, k), pole)
    return st_


def _pick_pole(arm, P, side, G, d, d_loc, off, k, M3, score_extra=None, prev=None):
    """拿道具的手肘方向：在肩→腕連線四周找一圈，取手腕彎最少（手繞道具軸取最不彎的轉向）、前臂扭轉 ±80° 內、
    手肘不跑到身體內側、不抬得比肩膀低 8 cm 還高（舉起手肘去湊手腕不彎，看起來比手腕彎還怪）的方向；
    prev（上一個關鍵的方向）給了就偏好離它近的（相鄰關鍵手肘不換邊，中間內插才不會翻）→ 回傳胸口座標的方向（之後每格照它內插）"""
    S = _shoulder(arm, P, side)
    st0, _ = _hold(arm, P, side, G, d, d_loc, off, S + Vector((0.3 if side == "L" else -0.3, 0.1, -0.3)) * k)
    dr = (Vector(st0[0]) - S).normalized()
    a0 = Vector((0, 0, -1)) - dr * (-dr.z)
    if a0.length < 1e-4:
        a0 = Vector((0, -1, 0)) - dr * (-dr.y)
    a0.normalize(); b0 = dr.cross(a0); sg = 1 if side == "L" else -1
    best = None
    for i in range(36):
        th = 2 * math.pi * i / 36
        pl = S + dr * 0.15 * k + (a0 * math.cos(th) + b0 * math.sin(th)) * 0.4 * k
        st_, bend = _hold(arm, P, side, G, d, d_loc, off, pl)
        E = _elbow(arm, side, S, st_[0], pl)[0]
        tw = _tw_of(arm, P, side, st_)
        sc = bend + 1.5 * max(0.0, abs(tw) - 80.0) + 300.0 * max(0.0, (S.x - E.x) * sg - 0.02)     # 手肘往身體內側跑扣分
        sc += 400.0 * max(0.0, E.z - (S.z - 0.08 * k)) + 200.0 * max(0.0, E.y - (S.y + 0.15 * k))   # 手肘抬太高、跑到背後扣分
        for f_ in (0.25, 0.5, 0.75):                                   # 前臂穿過軀幹（半徑 14 cm 的直立圓柱）扣分
            q_ = E.lerp(Vector(st_[0]), f_); rq = math.hypot(q_.x, q_.y - 0.02 * k)
            if q_.z < S.z and rq < 0.15 * k:
                sc += 2000.0 * (0.15 * k - rq)
        if prev is not None:
            sc += 0.3 * math.degrees((M3.transposed() @ (pl - S)).normalized().angle(prev))
        if score_extra is not None:
            sc += score_extra(E, st_)
        if best is None or sc < best[0]:
            best = (sc, pl, bend, tw)
    return (M3.transposed() @ (best[1] - S)).normalized(), best[2], best[3], best[0]


def _pole_track(keys_):
    """[(秒, 胸口座標方向), …] → s 時的方向（相鄰兩個關鍵之間 smoothstep 球面內插）"""
    def f(s):
        if s <= keys_[0][0]:
            return keys_[0][1]
        for (ta, va), (tb, vb) in zip(keys_[:-1], keys_[1:]):
            if s <= tb:
                return _slerp_dir(va, vb, ease((s - ta) / max(tb - ta, 1e-6)))
        return keys_[-1][1]
    return f


# ════════ 第 7 幕：餵食（新郎） ════════
def feed(target=V12_MOUTH_B, me=V12_SEAT["groom"], plate=V12_PLATE, fork_at=V12_FORK_AT, table=V12_TABLE["top"], seat=SEAT_H,
         dur=4.5, hand="L", arm=None):
    """坐著 → 0.05～0.7 秒拿起叉子 → 0.55～1.3 秒在盤子上叉一小口（1.0 秒叉下去）→ 1.3～2.4 秒慢慢送到她嘴邊（上身轉向她、微傾）→
    2.6 秒她咬下（叉尖停在嘴唇上）→ 2.7～3.3 秒叉子收回盤子上方 → 看著她微笑到 4.5 秒。另一隻手平放在桌上。
    target：她的嘴（世界座標，咬下那一刻；用 fed(...).mouth_world(2.6 / 4.5) 算）；me：自己的座位；
    plate／fork_at：盤子中心、叉子平放的握點（角色座標的 x, y，x 正值＝拿叉那手那側）；table：桌面高；seat：椅面高。
    叉子握法、叉尖位置見 held_prop('fork')（叉尖＝握點 + 11.5 cm × 道具軸）。
    手腕（2026-10-07 改）：手繞叉子軸取「手腕最不彎」的轉向；平放、叉、送到嘴邊、收回四個時間點的叉子方向在原本方向附近（±48°）
    重新找過（叉尖仍往下叉、仍對著她的嘴），手肘方向在 8 個時間點各自找（不往身體內側、不抬過肩、前臂不穿過軀幹）、中間內插。
    舊版照固定的掌心方向擺手，手腕整段彎 50～98°。fn.pole_end：結尾的手肘方向（glass_pick 從這裡接）；fn.opt_bend：四個時間點的手腕彎角"""
    arm = arm or ARM; k = _kof(arm)
    sg = 1 if hand == "L" else -1
    T = _to_local(target, me)
    la = _aim_deg(me, target)                                          # 她在哪個方向
    tsg = 1 if la > 0 else -1
    off = _offk(OFF_FORK, hand, k); dl = _mir(AX_FORK, hand).normalized(); tip = FORK["tip"]
    F = Vector((sg * plate[0], plate[1], table + 0.022))              # 盤子上那一口
    G_lie = Vector((sg * fork_at[0], fork_at[1], table + 0.006)); d_lie = Vector((sg * 0.25, -1.0, 0.0)).normalized()
    Pr, rt = _seat_P(arm, dict(_HOLD_BODY), seat)
    S = _shoulder(arm, Pr, hand) + Vector(rt)
    hp = Vector((F.x - S.x, F.y - S.y, 0.0)).normalized()
    d_sp = (hp * math.cos(math.radians(50)) + Vector((0, 0, -math.sin(math.radians(50))))).normalized()
    G_above = F - d_sp * tip + Vector((0, 0, 0.05))
    G_up = G_lie + Vector((0.0, -0.02, 0.07))
    hm = Vector((T.x - S.x, T.y - S.y, 0.0)).normalized()
    d_m = (hm + Vector((0, 0, 0.08))).normalized()                   # 叉尖略朝上
    G_mouth = T - d_m * (tip - 0.004)
    d_bk = (hp * math.cos(math.radians(35)) + Vector((0, 0, -math.sin(math.radians(35))))).normalized()
    G_back = F - d_bk * tip + Vector((0.0, 0.02, 0.07))
    ph_lie = Vector((0, 0, -1)); ph_sp = Vector((-sg * 0.4, 0.0, -1.0)).normalized(); ph_m = Vector((-sg * 0.3, 0.0, -1.0)).normalized()
    pl_rest = Vector((sg * 0.30, 0.25, -0.30)); pl_sp = Vector((sg * 0.35, 0.15, -0.28)); pl_m = Vector((sg * 0.38, 0.10, -0.25))

    def keys(s):
        a = seg(s, 0.05, 0.70); b = seg(s, 0.55, 0.92); c = bump(s, 0.92, 1.02, 1.06, 1.20); e = seg(s, 1.17, 1.32)   # 拿起叉子慢一點（0.45 秒拿完時手每格轉 24°）
        m = seg(s, 1.30, 2.40); n_ = bump(s, 2.40, 2.52, 2.56, 2.66); r = seg(s, 2.70, 3.30)
        G = G_lie.lerp(G_up, a).lerp(G_above, b) + Vector((0, 0, -0.05)) * c + Vector((0, 0, 0.03)) * e
        G = G.lerp(G_mouth, m) + d_m * 0.006 * n_
        G = G.lerp(G_back, r)
        d = _slerp_dir(_slerp_dir(_slerp_dir(d_lie, d_sp, a), d_m, m), d_bk, r)
        ph = ph_lie.lerp(ph_sp, a).lerp(ph_m, m).lerp(ph_sp, r)
        pl = pl_rest.lerp(pl_sp, a).lerp(pl_m, m).lerp(pl_sp, r)
        return G, d, ph, pl, m, r

    def body_feed(s):
        G, d, ph, pl, m, r = keys(s)
        tr = m * (1 - 0.65 * r)                                       # 上身轉向她
        lp = seg(s, 0.0, 0.6) * (1 - seg(s, 1.2, 1.6))                # 看盤子
        look = la - tsg * 14.0 * tr
        b = {"sx": 2.0 + 3.0 * lp + 3.0 * tr, "sz": tsg * 8.0 * tr, "cz": tsg * 6.0 * tr, "sy": tsg * 4.0 * tr}
        lw = seg(s, 1.1, 1.7)
        b.update(_look(look * lw + (sg * 10.0) * lp * (1 - lw)))
        b["hx"] = 14.0 * lp + 5.0 * seg(s, 1.3, 2.2)
        b["hy"] = tsg * 4.0 * seg(s, 2.8, 3.4)
        P, root = _seat_P(arm, b, seat)
        return P, root, b, G, d, m, r, lp

    TP = None

    def state(s):
        s = max(0.0, min(dur, s))
        P, root, b, G, d, m, r, lp = body_feed(s)
        M3 = _fkc(arm, P, "UpperChest").to_3x3(); S_ = _shoulder(arm, P, hand)
        st_h, bend_h = _hold(arm, P, hand, G - Vector(root), d, dl, off, S_ + M3 @ TP(s) * 0.4 * k)
        blink = 1.0 if min(abs(s - 0.75), abs(s - 3.9)) < 0.05 else 0.0
        face = {"Fcl_ALL_Fun": 0.45 * (1 - seg(s, 2.6, 3.0)), "Fcl_MTH_A": 0.30 * bump(s, 1.7, 2.1, 2.5, 2.75),
                "Fcl_ALL_Joy": 0.75 * seg(s, 2.6, 3.0), "Fcl_EYE_Close": max(blink, 0.2 * seg(s, 2.7, 3.1))}
        g = seg(s, 0.0, 0.40)                                         # 手指慢慢收成拿叉子（太快的話手指每格轉 40° 以上）
        hs = ("relax", "fork", round(g, 2)) if g < 1 else "fork"
        o = _alt(hand)
        return dict(P=P, root=root, arms={hand: st_h, o: _table_hand(arm, P, o, root, table, k)},
                    hands=_hands(hand, hs), face=face, body=b, G=G, d=d, bend=bend_h)

    def _under_table(E, st_):                                         # 手肘鑽到桌面底下扣分
        return 300.0 * max(0.0, table + 0.03 - E.z) if E.y < -0.05 else 0.0
    def _cands(d0, mode):
        out = []
        if mode == "lie":                                             # 平放在桌上：只能在桌面上轉
            for yaw in range(-60, 61, 10):
                out.append(Matrix.Rotation(math.radians(yaw), 3, "Z") @ d0)
            return out
        e1 = d0.cross(Vector((0, 0, 1))).normalized(); e2 = e1.cross(d0).normalized()
        for a_ in (0, 12, 24, 36, 48):
            for ph_ in range(0, 360, 30 if a_ else 360):
                ar, pr = math.radians(a_), math.radians(ph_)
                out.append((d0 * math.cos(ar) + (e1 * math.cos(pr) + e2 * math.sin(pr)) * math.sin(ar)).normalized())
        return out

    def _grip_of(mode, d_):
        if mode == "lie":
            return G_lie
        if mode == "spear":
            return F - d_ * tip + Vector((0, 0, 0.05))
        if mode == "mouth":
            return T - d_ * (tip - 0.004)
        return F - d_ * tip + Vector((0.0, 0.02, 0.07))

    def _ok(mode, d_):
        if mode == "spear":
            return d_.z < -0.45                                       # 叉尖要往下叉
        if mode == "back":
            return d_.z < -0.15
        if mode == "mouth":
            return abs(d_.z) < 0.55 and d_.angle(hm) < math.radians(50)   # 叉尖朝她的嘴、不要太斜
        return True

    def _opt(tk, d0, mode, prev):
        P_, root_, *_ = body_feed(tk); M3_ = _fkc(arm, P_, "UpperChest").to_3x3(); rt_ = Vector(root_)
        best = None
        for d_ in _cands(d0, mode):
            if not _ok(mode, d_):
                continue
            G_ = _grip_of(mode, d_)
            dirc, bd, tw_, sc = _pick_pole(arm, P_, hand, G_ - rt_, d_, dl, off, k, M3_, _under_table, prev)
            sc += 0.25 * math.degrees(d_.angle(d0))
            if best is None or sc < best[0]:
                best = (sc, d_, dirc, bd)
        return best

    o_lie = _opt(0.05, d_lie, "lie", None); d_lie = o_lie[1]
    G_up = G_lie + Vector((0.0, -0.02, 0.07))
    o_sp = _opt(1.00, d_sp, "spear", o_lie[2]); d_sp = o_sp[1]; G_above = F - d_sp * tip + Vector((0, 0, 0.05))
    o_m = _opt(2.40, d_m, "mouth", o_sp[2]); d_m = o_m[1]; G_mouth = T - d_m * (tip - 0.004)
    o_bk = _opt(3.30, d_bk, "back", o_m[2]); d_bk = o_bk[1]; G_back = F - d_bk * tip + Vector((0.0, 0.02, 0.07))
    FEED_OPT = dict(lie=round(o_lie[3], 1), spear=round(o_sp[3], 1), mouth=round(o_m[3], 1), back=round(o_bk[3], 1))
    kp = []; prev_ = None
    for tk in (0.05, 0.70, 1.00, 1.30, 2.40, 2.60, 3.30, 4.50):
        P_, root_, b_, G_, d_, *_ = body_feed(tk)
        dirc, bd, tw_, _ = _pick_pole(arm, P_, hand, G_ - Vector(root_), d_, dl, off, k, _fkc(arm, P_, "UpperChest").to_3x3(), _under_table, prev_)
        kp.append((tk, dirc)); prev_ = dirc
    TP = _pole_track(kp)

    fn = _wrap(state, dur, False, arm)
    fn.hand = hand; fn.me = me; fn.target_local = T
    fn.plate = F; fn.fork_at = (G_lie, d_lie); fn.pole_end = TP(dur); fn.opt_bend = FEED_OPT
    fn.times = dict(pick=(0.05, 0.70), spear=(0.92, 1.20), to_mouth=(1.30, 2.40), bite=2.60, back=(2.70, 3.30))
    return fn


# ════════ 第 7 幕：被餵（新娘） ════════
def fed(partner=None, me=V12_SEAT["bride"], table=V12_TABLE["top"], seat=SEAT_H, dur=4.5, hand="R", arm=None):
    """坐著看他 → 1.3～2.4 秒轉向他、上身前傾約 10°、張嘴 → 2.6 秒咬下 → 坐回來嚼 → 2.95～4.3 秒雙手輕放在桌上、肩膀開心地輕輕晃兩下
    （左右肩輪流聳起、上身跟著微微左右擺、頭往反方向歪一點），閉眼笑著嚼到 4.5 秒。
    partner：他的頭（世界座標，看他用；預設照座位）；hand：靠他那隻手（整段平放在桌上；glass_pick 用這隻手拿杯）。
    fn.mouth_world(t)：第 t（0~1）時嘴巴的世界座標——給 feed 的 target 用（咬下那一刻 t＝2.6／dur）。
    2026-10-07 改：舊版 2.95～3.95 秒右手托上臉頰（手腕彎 92°）。改成手肘撐在桌上托腮試了 6 輪：托好的姿勢手腕可以 0°、穿模 1 mm，
    但手往臉上移、從臉上放下那幾格，前臂都會擦過胸口或手指掃過下巴（逐格量 12～20 mm），依組長決定改成不托臉頰"""
    arm = arm or ARM; k = _kof(arm)
    partner = partner or (V12_SEAT["groom"][0], V12_SEAT["groom"][1], 1.13)
    la = _aim_deg(me, partner); tsg = 1 if la > 0 else -1
    sg = 1 if hand == "L" else -1
    lips = lips_rest(arm)

    def body(s):
        nb = bump(s, 2.40, 2.52, 2.56, 2.66)
        lean = seg(s, 1.3, 2.4) * (1 - 0.7 * seg(s, 2.65, 3.2)) + 0.15 * nb
        trn = seg(s, 1.3, 2.4) * (1 - 0.6 * seg(s, 2.65, 3.2))
        look = la - tsg * 14.0 * trn
        lk = 1 - 0.45 * seg(s, 2.8, 3.4)                              # 嚼的時候臉轉回來一點（3/4 對鏡頭）
        cw = seg(s, 2.95, 3.6)                                        # 坐回來後上身再往桌子那邊靠一點
        wg = seg(s, 2.95, 3.2) * (1 - seg(s, 4.0, 4.3))               # 晃肩的包絡：2.95 秒起、4.3 秒停
        sw = math.sin(2 * math.pi * (s - 2.95) / 0.55) * wg            # 一下 0.55 秒，晃兩下多
        b = {"sx": 2.0 + 5.0 * lean + 2.0 * cw, "sy": tsg * 4.0 * lean, "cx": 2.0 * lean + 1.5 * cw, "cy": tsg * 2.0 * lean + 3.0 * sw,
             "sz": tsg * 9.0 * trn + 2.0 * sw, "cz": tsg * 5.0 * trn, "shl": 6.0 * wg * (0.5 + 0.5 * math.sin(2 * math.pi * (s - 2.95) / 0.55)),
             "shr": 6.0 * wg * (0.5 - 0.5 * math.sin(2 * math.pi * (s - 2.95) / 0.55))}
        b.update(_look(look * lk))
        b["hx"] = 4.0 * seg(s, 1.5, 2.3) * (1 - seg(s, 2.7, 3.2)) + 2.0 * nb
        b["nx"] = 2.0 * nb
        b["hy"] = tsg * 4.0 * seg(s, 3.0, 3.6) - 3.5 * sw              # 頭微歪向他、晃肩時往反方向擺一點
        return b

    def state(s):
        s = max(0.0, min(dur, s))
        b = body(s)
        P, root = _seat_P(arm, b, seat)
        hk = _table_hand(arm, P, hand, root, table, k)                # 兩隻手都平放在桌上（手的位置釘在桌面上，肩膀晃的時候手不動）
        chew = seg(s, 2.75, 2.85) * 0.17 * abs(math.sin(math.pi * 2.6 * (s - 2.75)))
        mo = 0.75 * seg(s, 1.85, 2.30) * (1 - seg(s, 2.57, 2.66))
        joy = seg(s, 2.6, 3.0)
        face = {"Fcl_ALL_Fun": 0.55 * (1 - joy), "Fcl_ALL_Joy": 0.85 * joy, "Fcl_MTH_A": mo + chew,
                "Fcl_EYE_Close": 0.65 * seg(s, 2.62, 3.0) * (1 - 0.3 * bump(s, 3.9, 4.0, 4.1, 4.3))}
        o = _alt(hand)
        return dict(P=P, root=root, arms={hand: hk, o: _table_hand(arm, P, o, root, table, k)},
                    hands=_hands(hand, "relax"), face=face, body=b)

    fn = _wrap(state, dur, False, arm)

    def mouth_local(t):
        P, root = _seat_P(arm, body(t * dur), seat)
        return _fkc(arm, P, "Head") @ lips + Vector(root)

    fn.hand = hand; fn.me = me
    fn.mouth_local = mouth_local
    fn.mouth_world = lambda t: _to_world(mouth_local(t), me)
    fn.times = dict(turn=(1.3, 2.4), open=(1.85, 2.30), bite=2.6, chew=(2.75, dur), wiggle=(2.95, 4.3))
    return fn


# ════════ 第 7 幕：相視一笑拿酒杯（兩人） ════════
def glass_pick(role=None, me=None, partner=None, glass_at=V12_GLASS_AT, table=V12_TABLE["top"], seat=SEAT_H, dur=1.8,
               feed_kw=None, fed_kw=None, arm=None):
    """接在 feed（新郎）／fed（新娘）結尾：新郎 0～0.5 秒把叉子放回盤上；新娘同時把平放在桌上的手移到杯子旁（0～0.9 秒）→
    0.5～1.0 秒對看一笑 → 1.0～1.8 秒靠對方那隻手（新郎左手、新娘右手）慢慢拿起面前的酒杯（握杯腳），舉到胸前。
    role：'groom'／'bride'（預設看角色性別）；me：座位；partner：對方的頭（世界座標）；glass_at：酒杯在桌上的位置（角色座標，x 正值＝往拿杯那手那側）。
    feed_kw／fed_kw：前一個動作用的參數（同一組才會接得剛好）。結尾＝toast_sit／sip 的開頭（胸前拿杯、看著對方）。
    手腕（2026-10-07 改，只改新郎）：放叉子時手繞叉子軸取最不彎的轉向、叉子放下的角度與手肘方向重新找過（舊版放好那格手腕彎 85°）"""
    arm = arm or ARM; k = _kof(arm)
    role = role or _ROLE
    hand = _NEAR[role]; sg = 1 if hand == "L" else -1
    me = me or V12_SEAT[role]
    other = "bride" if role == "groom" else "groom"
    partner = partner or (V12_SEAT[other][0], V12_SEAT[other][1], 1.13 if other == "groom" else 1.05)
    la = _aim_deg(me, partner); tsg = 1 if la > 0 else -1
    if role == "groom":
        pre = feed(**dict(dict(me=me, table=table, seat=seat, hand=hand, arm=arm), **(feed_kw or {})))
    else:
        pre = fed(**dict(dict(partner=partner, me=me, table=table, seat=seat, hand=hand, arm=arm), **(fed_kw or {})))
    S0 = pre.state(pre.dur)
    b0, face0 = S0["body"], S0["face"]
    Gg = Vector((sg * glass_at[0], glass_at[1], table + 0.045))       # 杯腳握點（杯底在桌上）
    pre_g = Gg + Vector((sg * 0.035, 0.05, 0.03))
    if role == "groom":
        F = pre.plate
        d_put = Vector((sg * 0.2, -1.0, -0.12)).normalized()           # 叉子斜放在盤緣：叉尖在盤子上
        G_put = F + Vector((sg * 0.05, 0.02, -0.010)) - d_put * FORK["tip"] + Vector((0, 0, 0.015))
        off_f = _offk(OFF_FORK, hand, k); dl_f = _mir(AX_FORK, hand).normalized()
    b_end = dict(_HOLD_BODY); b_end.update(_look(la))
    PB = Vector((sg * 0.20, 0.0, 0.0)) * k
    if role == "groom":                                               # 放叉子：手肘方向從 feed 結尾的方向內插到放好那格找到的方向
        PD0 = pre.pole_end
        b_p = _mixd(b0, b_end, seg(0.5, 0.0, 1.0)); b_p["hx"] = b_p.get("hx", 0.0); P_p, root_p = _seat_P(arm, b_p, seat)
        M3p = _fkc(arm, P_p, "UpperChest").to_3x3(); tip_pt = G_put + d_put * FORK["tip"]; bestp = None
        e1 = d_put.cross(Vector((0, 0, 1))).normalized(); e2 = e1.cross(d_put).normalized()
        for a_ in (0, 12, 24, 36):
            for ph_ in range(0, 360, 30 if a_ else 360):
                ar, pr = math.radians(a_), math.radians(ph_)
                dd = (d_put * math.cos(ar) + (e1 * math.cos(pr) + e2 * math.sin(pr)) * math.sin(ar)).normalized()
                if dd.z > -0.05:                                      # 叉尖要比握點低（斜放在盤緣）
                    continue
                Gp = tip_pt - dd * FORK["tip"]
                dirc, bd, tw_, sc = _pick_pole(arm, P_p, hand, Gp - Vector(root_p), dd, dl_f, off_f, k, M3p, None, PD0)
                sc += 0.25 * math.degrees(dd.angle(d_put))
                if bestp is None or sc < bestp[0]:
                    bestp = (sc, dd, Gp, dirc)
        d_put, G_put, PD1 = bestp[1], bestp[2], bestp[3]

    def state(s):
        s = max(0.0, min(dur, s))
        x1 = seg(s, 0.0, 0.50)                                        # 放下叉子
        sm = seg(s, 0.45, 1.0)                                        # 看對方、笑
        gr = seg(s, 0.50, 1.0)                                        # 手移到杯子旁邊
        cl = seg(s, 1.0, 1.3)                                         # 握住杯腳
        up = seg(s, 1.3, 1.8)                                         # 舉到胸前
        b = _mixd(b0, b_end, seg(s, 0.0, 1.0))
        if role == "groom":
            b["hx"] = b.get("hx", 0.0) + 7.0 * bump(s, 0.05, 0.22, 0.32, 0.5)      # 放叉子時瞄一下盤子
        b["hy"] = b.get("hy", 0.0) + tsg * 3.0 * bump(s, 0.55, 0.8, 1.2, 1.6)
        P, root = _seat_P(arm, b, seat)
        rt = Vector(root)
        G = pre_g.lerp(Gg, cl) if up <= 0 else Gg.lerp(_glass_hold_G(k, hand, table), up)
        gl = _glass(arm, P, hand, root, k, G)
        if role == "groom":
            Gf, df = S0["G"], S0["d"]
            M3 = _fkc(arm, P, "UpperChest").to_3x3(); Sh = _shoulder(arm, P, hand)
            pdir = _slerp_dir(PD0, PD1, ease(x1))
            first, _ = _hold(arm, P, hand, Gf.lerp(G_put, x1) - rt, _slerp_dir(df, d_put, x1), dl_f, off_f, Sh + M3 @ pdir * 0.4 * k)
            hk = _mix_arm(first, gl, gr, arm=arm, P=P, side=hand)
        else:                                                         # 新娘：平放在桌上的手移到杯子旁邊（0～0.9 秒）
            hk = _mix_arm(S0["arms"][hand], gl, seg(s, 0.0, 0.9), Vector((sg * 0.05, -0.05, 0.0)) * k, PB, arm=arm, P=P, side=hand)
        face = _mixf(face0, {"Fcl_ALL_Joy": 0.9 * (1 - 0.35 * up), "Fcl_ALL_Fun": 0.3 * up, "Fcl_EYE_Close": 0.25 * (1 - up)}, sm)
        face["Fcl_MTH_A"] = face.get("Fcl_MTH_A", 0.0) * (1 - seg(s, 0.0, 0.3))
        if role == "groom":
            hs = "fork" if s < 0.36 else (("fork", "relax", round(seg(s, 0.36, 0.70), 2)) if s < 1.0 else ("relax", "stem", round(cl, 2)))
        else:
            hs = "relax" if s < 1.0 else ("relax", "stem", round(cl, 2))           # fed 結尾兩手平放在桌上（relax）
        o = _alt(hand)
        return dict(P=P, root=root, arms={hand: hk, o: _table_hand(arm, P, o, root, table, k)},
                    hands=_hands(hand, hs), face=face, body=b)

    fn = _wrap(state, dur, False, arm)
    fn.hand = hand; fn.me = me; fn.role = role; fn.glass_at = Gg
    fn.times = dict(put_fork=(0.0, 0.50), release=0.45, smile=(0.45, 1.0), grasp=(1.0, 1.3), lift=(1.3, 1.8))
    if role == "groom":
        fn.fork_put = (G_put, d_put)
    return fn


# ════════ 第 7 幕：坐姿乾杯（兩人） ════════
def toast_sit(role=None, me=None, partner=None, clink=V12_CLINK, cam=V12_CAM, table=V12_TABLE["top"], seat=SEAT_H, dur=2.2,
              t_clink=0.9, arm=None):
    """坐姿版的舉杯乾杯（紅酒杯、握杯腳）：胸前拿杯、看著對方 → 舉起往對方伸出，t_clink 秒兩個杯身輕碰 →
    收回、舉到下巴高度朝鏡頭致意（轉頭看鏡頭、點頭）→ 放回胸前，看著鏡頭結束（＝sip 的開頭）。
    clink：兩個杯身相碰的點（世界座標，兩人要給同一點）；partner：對方的頭；cam：鏡頭的 (x, y)"""
    arm = arm or ARM; k = _kof(arm)
    role = role or _ROLE
    hand = _NEAR[role]; sg = 1 if hand == "L" else -1
    me = me or V12_SEAT[role]
    other = "bride" if role == "groom" else "groom"
    partner = partner or (V12_SEAT[other][0], V12_SEAT[other][1], 1.13 if other == "groom" else 1.05)
    la = _aim_deg(me, partner); tsg = 1 if la > 0 else -1
    lc = _aim_deg(me, (cam[0], cam[1], 1.0))
    Cl = _to_local(clink, me)
    pl = _to_local(partner, me); nd = Vector((pl.x, pl.y, 0.0)).normalized()
    Bm = Cl - nd * (GLASS["rim_r"] + 0.006)                           # 碰之前兩個杯身各差 6 mm
    G_c = Bm - Vector((0, 0, GLASS["bowl"]))
    H = _glass_hold_G(k, hand, table)
    Pr, rt = _seat_P(arm, dict(_HOLD_BODY), seat)
    chin = (_fkc(arm, Pr, "Head") @ lips_rest(arm)).z + rt[2] - 0.03 * k
    cd = Vector((math.sin(math.radians(lc)), -math.cos(math.radians(lc)), 0.0))
    U = Vector((sg * 0.05 * k, -0.25 * k, 0.0)) + cd * 0.05; U.z = chin - GLASS["bowl"] - 0.02
    a0, a1 = 0.05, t_clink - 0.15

    def state(s):
        s = max(0.0, min(dur, s))
        a = seg(s, a0, a1)
        tap = bump(s, t_clink - 0.10, t_clink - 0.01, t_clink + 0.01, t_clink + 0.09)
        c = seg(s, t_clink + 0.08, t_clink + 0.48)
        d = seg(s, t_clink + 0.72, t_clink + 1.20)
        nod = bump(s, t_clink + 0.55, t_clink + 0.65, t_clink + 0.69, t_clink + 0.83)
        cw = a * (1 - c)
        G = H.lerp(G_c, a) + nd * 0.006 * tap
        G = G.lerp(U, c).lerp(H, d)
        lk = la + (lc - la) * seg(s, t_clink + 0.02, t_clink + 0.70)
        b = {"sx": 2.0 + 2.0 * cw, "sz": tsg * 5.0 * cw, "cz": tsg * 3.0 * cw}
        b.update(_look(lk - tsg * 8.0 * cw))
        b["hx"] = 7.0 * nod - 2.0 * c * (1 - d)
        P, root = _seat_P(arm, b, seat)
        face = {"Fcl_ALL_Fun": 0.3 * (1 - cw) + 0.35 * c, "Fcl_ALL_Joy": 0.9 * cw * (1 - c) + 0.5 * c * (1 - 0.4 * d),
                "Fcl_EYE_Close": 0.3 * bump(s, t_clink - 0.1, t_clink, t_clink + 0.15, t_clink + 0.3)}
        o = _alt(hand)
        return dict(P=P, root=root, arms={hand: _glass(arm, P, hand, root, k, G), o: _table_hand(arm, P, o, root, table, k)},
                    hands=_hands(hand, "stem"), face=face, body=b)

    fn = _wrap(state, dur, False, arm)
    fn.hand = hand; fn.me = me; fn.role = role; fn.clink_local = Cl
    fn.times = dict(raise_=(a0, a1), clink=t_clink, salute=(t_clink + 0.08, t_clink + 0.83), lower=(t_clink + 0.72, t_clink + 1.20))
    return fn


# ════════ 第 7 幕：喝一口（兩人） ════════
def sip(role=None, me=None, cam=V12_CAM, table=V12_TABLE["top"], seat=SEAT_H, dur=3.5, tilt=(34.0, 46.0), arm=None):
    """從胸前拿杯（看著鏡頭）→ 0～0.8 秒杯子舉到唇邊（杯緣碰下唇、杯子往臉傾 tilt[0] 度）→ 0.8～1.4 秒輕啜一口（傾到 tilt[1]、頭微仰、閉眼）→
    1.4～2.0 秒放回胸前 → 拿著杯子對鏡頭微笑到結束。杯緣碰嘴是設計上的接觸（杯子不在穿模檢查範圍）"""
    arm = arm or ARM; k = _kof(arm)
    role = role or _ROLE
    hand = _NEAR[role]; sg = 1 if hand == "L" else -1
    me = me or V12_SEAT[role]
    lc = _aim_deg(me, (cam[0], cam[1], 1.0))
    H = _glass_hold_G(k, hand, table)
    lips = lips_rest(arm)
    up = Vector((0, 0, 1))

    def state(s):
        s = max(0.0, min(dur, s))
        r = seg(s, 0.0, 0.8); sp = seg(s, 0.8, 1.25) * (1 - seg(s, 1.25, 1.45)); lo = seg(s, 1.4, 2.0)
        cam_w = max(0.0, min(1.0, 1 - seg(s, 0.0, 0.55) + seg(s, 1.7, 2.4)))
        b = dict(_HOLD_BODY)
        b.update(_look(lc * cam_w))
        b["hx"] = 3.0 * r * (1 - lo) - 6.0 * sp
        b["nx"] = -2.0 * sp
        b["hy"] = 3.0 * seg(s, 2.2, 2.8) * (1 if lc > 0 else -1)
        P, root = _seat_P(arm, b, seat)
        Lp = _fkc(arm, P, "Head") @ lips + Vector(root)
        q = Vector((Lp.x - H.x, Lp.y - H.y, 0.0)).normalized()
        th = math.radians(tilt[0] + (tilt[1] - tilt[0]) * sp)
        d = up * math.cos(th) + q * math.sin(th); m = q * math.cos(th) - up * math.sin(th)
        tgt = Lp + Vector((0, 0, -0.008 * k)) - q * 0.002
        G_l = tgt - d * GLASS["rim"] - m * GLASS["rim_r"]
        w = r * (1 - lo)
        G = H.lerp(G_l, w); dd = _slerp_dir(up, d, w)
        face = {"Fcl_ALL_Fun": 0.4 * (1 - w) * (1 - seg(s, 2.0, 2.6)), "Fcl_EYE_Close": 0.55 * sp + 0.15 * w * (1 - sp),
                "Fcl_MTH_U": 0.25 * w * (1 - lo), "Fcl_ALL_Joy": 0.7 * seg(s, 2.0, 2.6)}
        o = _alt(hand)
        po = Vector((sg * 0.32, 0.05, -0.32)).lerp(Vector((sg * 0.45, -0.12, -0.22)), w)      # 舉到嘴邊時手肘往外前方，前臂才不會貼到胸側
        return dict(P=P, root=root, arms={hand: _glass(arm, P, hand, root, k, G, dd, po), o: _table_hand(arm, P, o, root, table, k)},
                    hands=_hands(hand, "stem"), face=face, body=b, lips=Lp)

    fn = _wrap(state, dur, False, arm)
    fn.hand = hand; fn.me = me; fn.role = role
    fn.times = dict(to_lips=(0.0, 0.8), sip=(0.8, 1.45), lower=(1.4, 2.0), smile=(2.0, dur))
    return fn


# ════════ 登記（預覽／檢查用預設參數） ════════
def _lazy(make):
    """第一次用到才建，載入動作庫不會變慢；fn.real() 拿到真正的工廠結果（有 dur、times…）"""
    box = {}

    def real():
        if "f" not in box:
            box["f"] = make()
        return box["f"]

    def fn(t):
        return real()(t)
    fn.real = real
    return fn


V12_ACTIONS = [("sneak_hand", "偷牽手", _lazy(lambda: sneak_hand()), 31), ("bonked", "被敲抱頭", _lazy(lambda: bonked()), 31),
               ("mallet_bonk", "玩具槌敲頭", _lazy(lambda: mallet_bonk()), 43), ("feed", "餵食", _lazy(lambda: feed()), 108),
               ("fed", "被餵", _lazy(lambda: fed()), 108), ("glass_pick", "相視一笑拿酒杯", _lazy(lambda: glass_pick()), 43),
               ("toast_sit", "坐姿乾杯", _lazy(lambda: toast_sit()), 53), ("sip", "喝一口", _lazy(lambda: sip()), 84),
               ("mallet_draw", "抽槌上肩", _lazy(lambda: mallet_draw()), 17),("mallet_jump_bonk", "跳起來敲頭", _lazy(lambda: mallet_jump_bonk()), 54)]



# ════════════════════════ 7. V12 第 5 幕：路人甲（走進來舉手機拍照 → 尷尬抓頭鞠躬 → 轉身走出去） ════════════════════════
# 2026-10-06 新增，單次動作。腳：自己的換步表＋腿部直接寫 FK（_leg_set，和第 6 節手臂同一套算法），所以可以邊走邊轉向、
# 原地換兩步轉身，腳都是「抬起、移過去、放下」，踩著的腳不滑。
#   pose_lib.plant_feet 的膝蓋方向固定朝世界 -Y、walk_fwd 的步態只能直線走，都做不了轉身；舊的 walk／turn 在三個角色上都滑步超標。
# 位置一律是世界座標（和 walk_fwd 一樣）：工廠參數給 origin、dist、dirx（或 face），回傳的 root／rz 已經是世界座標，
#   情境用 pose_frame（或 pose_frame_at(…, 0, 0, 0)）直接套，不要再搬。

def _two_bone(S, W, pole, L1, L2):
    """兩節骨頭的 IK 幾何（和 pose_lib 同算法）→ (中間關節位置, 末端實際位置, 起→末方向, 中間關節偏向的單位向量, 起點的夾角)"""
    v = Vector(W) - S; d = max(1e-4, min(v.length, (L1 + L2) * 0.999)); dr = v.normalized()
    a = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    pp = Vector(pole) - S; pp = pp - dr * pp.dot(dr)
    if pp.length < 1e-6:
        pp = Vector((0, -1, 0)) - dr * dr.y
    pp.normalize()
    return S + dr * math.cos(a) * L1 + pp * math.sin(a) * L1, S + dr * d, dr, pp, a


def _len_leg(arm, side):
    hp, kn, an = (_bd(arm, f"J_Bip_{side}_{n}")[0] for n in ("UpperLeg", "LowerLeg", "Foot"))
    return (kn - hp).length, (an - kn).length


def _leg_set(arm, P, side, A, pole, yaw=0.0):
    """把這條腿的 FK 寫進 P（蓋掉 UpperLeg／LowerLeg／Foot／ToeBase）：腳踝到 A、膝蓋朝 pole、腳掌平放並繞 Z 轉 yaw 度（骨架空間）。
    VRoid 腿：局部 Y＝骨頭方向、X＝膝蓋轉軸、局部 Z 朝前；膝蓋彎的時候小腿往局部 -Z（後面）走（和手臂相反）"""
    names = [f"{side}_{n}" for n in ("UpperLeg", "LowerLeg", "Foot")]
    for n in names + [f"{side}_ToeBase"]:
        P[n] = []
    hp, kn, ft = (_bd(arm, "J_Bip_" + n) for n in names)
    L1, L2 = _len_leg(arm, side)
    Mu = _fkc(arm, P, names[0]); S = Mu @ hp[0]
    E, Wr, dr, pp, a = _two_bone(S, A, pole, L1, L2)
    yu = (E - S).normalized()
    zu = -(dr * math.sin(a) - pp * math.cos(a)).normalized()          # 局部 Z＝小腿彎的方向的反面（朝前）
    xu = yu.cross(zu).normalized(); zu = xu.cross(yu)
    yf = (Wr - E).normalized(); zf = xu.cross(yf).normalized()
    Fu = Matrix((xu, yu, zu)).transposed(); Ff = Matrix((xu, yf, zf)).transposed()
    d = _delta(Fu @ hp[2].to_3x3().transposed(), Mu.to_3x3())
    P[names[0]] = [d] if d else []
    M = _fkc(arm, P, names[1])
    d = _delta(Ff @ kn[2].to_3x3().transposed(), M.to_3x3())
    P[names[1]] = [d] if d else []
    M = _fkc(arm, P, names[2])
    Rf = Matrix.Rotation(math.radians(yaw), 3, "Z") @ ft[2].to_3x3()
    d = _delta(Rf @ ft[2].to_3x3().transposed(), M.to_3x3())
    P[names[2]] = [d] if d else []
    return E


def _wrap_angle(a):
    return (a + 180.0) % 360.0 - 180.0


class _Steps:
    """換步表（世界座標）：feet0＝{'L': (x, y, yaw), 'R': …} 一開始的腳位（yaw＝腳尖朝向的 rz，度）；
    steps＝[(side, t0, t1, (x, y, yaw), lift[, (ya, yb)]), …]：t0～t1 秒這隻腳抬起（最高 lift 公尺）、移到新位置與朝向、放下；
    (ya, yb)＝腳尖轉向在這一步的哪一段（0～1）做完，預設 (0.15, 0.85)。
    水平移動只在腳離地 1 cm 以上的中段發生（和 actions 的 _step 一樣），所以不會在地上拖。
    前後兩步時間重疊時，兩隻腳的抬高都減掉比較低的那隻 → 任何時刻至少一隻腳踩在地上（不會變成小跳步）"""

    def __init__(self, feet0, steps):
        self.f0 = {k: tuple(v) for k, v in feet0.items()}; self.steps = steps

    def foot(self, side, t):
        x, y, yaw, lift = self._raw(side, t)
        other = self._raw("R" if side == "L" else "L", t)[3]
        return (x, y, yaw, lift - min(lift, other))

    def _raw(self, side, t):
        cur = self.f0[side]
        for st_ in self.steps:
            sd, t0, t1, to, lift = st_[:5]
            ya, yb = st_[5] if len(st_) > 5 else (0.15, 0.85)       # 第 6 欄（選填）：腳尖轉向在這一步的哪一段做
            if sd != side:
                continue
            if t <= t0:
                break
            if t < t1:
                u = (t - t0) / (t1 - t0)
                up = 0.5 - 0.5 * math.cos(2 * math.pi * u)
                m = ease((u - 0.2) / 0.6)
                my = ease((u - ya) / (yb - ya))                      # 腳尖轉向：預設離地 5 mm 以上的整段（約 15%～85%）都在轉
                yaw = cur[2] + _wrap_angle(to[2] - cur[2]) * my
                return (cur[0] + (to[0] - cur[0]) * m, cur[1] + (to[1] - cur[1]) * m, yaw, lift * up)
            cur = tuple(to)
        return (cur[0], cur[1], cur[2], 0.0)


def _foot_dir(yaw):
    r = math.radians(yaw)
    return Vector((math.sin(r), -math.cos(r), 0.0))


# 手機（代用道具的尺寸，真實尺寸）
PHONE = dict(w=0.074, h=0.152, t=0.008)


def _phone_hands(arm, P, k, C, up, fwd):
    """雙手拿手機（直拿、螢幕朝自己）：手機中心 C、手機上方向 up、螢幕法線（朝自己）＝-fwd（骨架空間）→ 兩隻手的狀態。
    兩手捏著手機左右兩邊的下半段：掌心朝手機側邊、手指繞到手機背面、拇指在螢幕這面"""
    st = {}
    side_ax = up.cross(fwd).normalized()                     # 角色的左邊（+X 那側）
    for sd, sg in (("L", 1), ("R", -1)):
        lat = side_ax * sg                                    # 往這隻手那側
        g = C + lat * (PHONE["w"] / 2 + 0.006) - up * 0.035   # 手掌中心：手機側邊外 6 mm、下半段
        Y = (fwd * 0.75 + up * 0.45 - lat * 0.2).normalized() # 手指往前上方（繞到手機背面）
        R = _rot_map(Vector((0, 1, 0)), _PALM_LOC[sd], Y, -lat)
        W = _place_hand(R, _palm_pt(arm, sd, k), g)
        Sh = _shoulder(arm, P, sd)
        st[sd] = (W, Sh + Vector((sg * 0.35, 0.05, -0.30)) * k, R)
    return st


def _world_to_arm(p, root, rz):
    r = math.radians(-rz); c, s_ = math.cos(r), math.sin(r)
    dx, dy = p[0] - root[0], p[1] - root[1]
    return Vector((c * dx - s_ * dy, s_ * dx + c * dy, p[2] - root[2]))


def walk_in_photo(origin=(0.45, 0.0), dist=0.50, dirx=-1, face=180.0, feet_turn=0.65, phone_dist=0.25, dur=1.3, t_shot=1.0, arm=None,
                  steps=2, stop=None):
    """路人甲：從畫面右側往左快走 2 步（真的往前移）→ 原地換兩步轉身、上身再扭過去面向新人 → 雙手把手機舉到臉前 phone_dist 公尺（不舉過頭）→
    t_shot 秒按快門（手機往前一點點、頭微點）→ 拿著不動到結束。
    origin：出發點 (x, y)（世界）；dist：走多遠；dirx：-1＝往 -X（畫面左）走；face：轉身後面向的 rz（度；180＝面向 +Y，背對鏡頭拍新人）；
    feet_turn：轉身角度裡腳換步轉的比例（其餘由骨盆以上扭過去；1.3 秒內腳要轉滿 90° 會超過每格 15°，預設腳轉 65%）。
    steps：走幾步（預設 2＝原本的 0.5 m／2 步，結果和舊版完全相同）；3 步以上時每一步的擺盪時間照步幅拉長（擺盪的腳每秒走 1.6 m；再快腿的骨頭每格超過 15°、步與步之間速度突變超過 6），
    走完之後的轉身、舉手機、按快門整段往後延，fn.dur 會跟著變長（dur、t_shot 照舊是「走 2 步時」的秒數，多走的時間自動加上去）。
    stop：停下時兩腳中點的位置 (x, y)（世界）；給了就不看 dist／dirx，從 origin 直線走到 stop（可以斜著走）。走完兩腳一前一後差約 22 cm，
    dist 是「最後一步落腳點」的距離，兩腳中點比它少約 11 cm；實際停下的位置看 fn.stop。
    回傳的 root／rz 是世界座標。fn.stop＝停下的位置，fn.end_face＝結尾面向，fn.t_phone＝雙手拿好手機的秒數（之前手機跟著右手），fn.walk_end＝走完的秒數"""
    arm = arm or ARM; k = _kof(arm)
    B = arm.data.bones
    if stop is not None:                                        # 起點 → 終點（停下時兩腳中點）：走多遠、朝哪走
        dx, dy = stop[0] - origin[0], stop[1] - origin[1]
        D_ = math.hypot(dx, dy); rz0 = math.degrees(math.atan2(dx, -dy))
        dist = D_ / 0.775 if int(steps) <= 2 else D_ + 0.5 * min(0.225 * k, (D_ + 0.11 * k) / max(3, int(steps)))
    else:
        rz0 = 90.0 if dirx > 0 else -90.0
    fw = _foot_dir(rz0); lat = Vector((-fw.y, fw.x, 0))          # lat＝角色的左邊
    a0L = B["J_Bip_L_Foot"].head_local; hw = abs(a0L.x)
    O = Vector((origin[0], origin[1], 0)); X1 = O + fw * dist
    def at(c, sd):                                              # 以 c 為中心、站姿寬度的腳位（世界）
        return c + lat * (hw if sd == "L" else -hw)
    L0, R0 = at(O, "L"), at(O, "R")
    steps = max(2, int(steps))
    if steps == 2:                                              # 原本的 2 步（時間、位置都不動）
        stp = [("L", 0.06, 0.33, tuple(at(O + fw * dist * 0.55, "L").xy) + (rz0,), 0.040 * k),
               ("R", 0.27, 0.54, tuple(at(X1, "R").xy) + (rz0,), 0.035 * k)]
        sw_per = 0.54
    else:                                                       # n 步：落腳點平均分配、最後一步停在 dist，擺盪時間照這隻腳要走多遠拉長
        st2 = min(0.225 * k, dist / steps)                         # 最後一步只比前一步多 22.5 cm（和 2 步版一樣），兩腳停下來不會一前一後拉太開
        al = [(dist - st2) * (i + 1) / (steps - 1) for i in range(steps - 1)] + [dist]
        stp = []; prev = {"L": 0.0, "R": 0.0}; t0 = 0.06
        for i in range(steps):
            sd = "L" if i % 2 == 0 else "R"
            ts = max(0.40, (al[i] - prev[sd]) / 1.3) if i == 0 else max(0.30, (al[i] - prev[sd]) / 1.60)   # 第一步慢一點起步
            stp.append((sd, t0, t0 + ts, tuple(at(O + fw * al[i], sd).xy) + (rz0,), (0.040 if i == 0 else 0.035) * k))
            prev[sd] = al[i]; t0 = t0 + ts - 0.12                 # 前後兩步重疊 0.12 秒：一隻腳落地前另一隻就起步，速度才不會一步一頓
        sw_per = 2 * (stp[-1][1] - stp[0][1]) / (steps - 1)
    walk_end = stp[-1][2]; DT = walk_end - 0.54                 # 走完之後的所有事件往後延 DT 秒
    dur = dur + DT; t_shot = t_shot + DT
    lastp = {}
    for st_ in stp:
        lastp[st_[0]] = Vector(st_[3][:2]).to_3d()
    X1 = (lastp["L"] - lat * hw + lastp["R"] + lat * hw) * 0.5
    # 原地轉身：先動要轉過去那一側的腳（往右轉先抬右腳）
    dturn = _wrap_angle(face - rz0)
    fface = rz0 + dturn * feet_turn                              # 腳最後朝向
    fw2 = _foot_dir(fface); lat2 = Vector((-fw2.y, fw2.x, 0))
    first = "R" if dturn < 0 else "L"; second = "L" if first == "R" else "R"
    mid = rz0 + dturn * feet_turn * 0.5
    fwm = _foot_dir(mid); latm = Vector((-fwm.y, fwm.x, 0))
    # 轉身換三步。多步版重疊少一點（各 0.08 秒）：重疊太多時，前一步的腳在 80% 之後就被「減掉比較低的那隻」壓回地面，腳尖還在轉就會滑
    tt_ = ((0.48, 0.78), (0.66, 1.02), (0.94, 1.22)) if steps == 2 else ((0.48, 0.80), (0.72, 1.08), (1.00, 1.28))
    stp += [(first, tt_[0][0] + DT, tt_[0][1] + DT, tuple((X1 + latm * (hw if first == "L" else -hw)).xy) + (mid,), 0.025 * k),
            (second, tt_[1][0] + DT, tt_[1][1] + DT, tuple((X1 + lat2 * (hw if second == "L" else -hw)).xy) + (fface,), 0.025 * k),
            (first, tt_[2][0] + DT, tt_[2][1] + DT, tuple((X1 + lat2 * (hw if first == "L" else -hw)).xy) + (fface,), 0.020 * k)]
    S = _Steps({"L": tuple(L0.xy) + (rz0,), "R": tuple(R0.xy) + (rz0,)}, stp)
    L1, L2 = _len_leg(arm, "L")
    hip0 = B["J_Bip_L_UpperLeg"].head_local

    # 骨盆高度：每個時間點兩隻腳都要構得到（腿長 × 0.993 → 腳最遠時膝蓋還留約 14° 彎），取前後 0.03 秒內的最大值再平滑（和 walk_fwd 的 _Gait 同做法）；
    # 腿接近打直時，構得到的長度差 2.5% 膝蓋就彎 25°，看起來像半蹲，所以這裡不能抓太寬
    def _need(s):
        p, yaw = _pxy(s); req = (SOFT_KNEE + 0.006 * seg(s, 0.04, 0.14) * (1 - seg(s, 0.50 + DT, 0.70 + DT))) * k
        for sd in ("L", "R"):
            fx, fy, fyaw, lift = S.foot(sd, s)
            a0 = B[f"J_Bip_{sd}_Foot"].head_local
            A = _world_to_arm(Vector((fx, fy, a0.z + lift)), (p.x, p.y, 0.0), yaw)
            h = B[f"J_Bip_{sd}_UpperLeg"].head_local; Rl = (L1 + L2) * 0.993
            dxy = (Vector((A.x, A.y)) - Vector((h.x, h.y))).length
            if dxy < Rl:
                req = max(req, h.z - A.z - math.sqrt(Rl * Rl - dxy * dxy))
        return req

    def _pxy(s):
        acc = Vector((0, 0, 0)); yaws = []
        for i in range(-4, 5):
            tt = max(0.0, min(dur, s + i * 0.03))
            fl, fr = S.foot("L", tt), S.foot("R", tt)
            acc += Vector(((fl[0] + fr[0]) * 0.5, (fl[1] + fr[1]) * 0.5, 0))
            yaws.append(fl[2] + _wrap_angle(fr[2] - fl[2]) * 0.5)
        y0 = yaws[0]
        return acc / 9.0, y0 + sum(_wrap_angle(y - y0) for y in yaws) / len(yaws)

    _N = 131; _req = [_need(dur * i / (_N - 1)) for i in range(_N)]
    _w = 3; _mx = [max(_req[max(0, i - _w):i + _w + 1]) for i in range(_N)]
    _base = [sum(_mx[max(0, i - _w):i + _w + 1]) / len(_mx[max(0, i - _w):i + _w + 1]) for i in range(_N)]

    def pelvis(s):
        """骨盆：兩腳中點（照時間取 ±0.12 秒平均，起步、停步自然加減速）、朝向＝兩腳朝向的平均，高度＝兩腳都構得到的微蹲"""
        p, yaw = _pxy(s)
        x = max(0.0, min(1.0, s / dur)) * (_N - 1); i = min(int(x), _N - 2); f = x - i
        return p, yaw, _base[i] * (1 - f) + _base[i + 1] * f

    lead = 12.0 * (1 if dturn > 0 else -1)                       # 轉身時上身先轉一點
    twist = dturn * (1 - feet_turn)                               # 腳沒轉到的那部分由上身扭過去

    def body(s):
        p, yaw, drop = pelvis(s)
        sl = s - DT                                              # 走完之後的事件（轉身、舉手機）照原本 2 步的時間表、整段往後延
        turn_lead = lead * bump(sl, 0.45, 0.65, 0.80, 1.05)
        tw = twist * seg(sl, 0.50, 1.00)
        walk = seg(s, 0.04, 0.30) * (1 - seg(sl, 0.42, 0.62))
        sw = math.sin(2 * math.pi * (s - 0.06) / sw_per) * walk   # 走路時的擺手、扭腰（從 0 慢慢加大，起步那格才不會突然一甩）
        b = {"sx": 4.0 * walk, "sz": 3.0 * sw + 0.35 * (turn_lead + tw), "cz": -2.0 * sw + 0.35 * (turn_lead + tw)}
        shot = seg(sl, 0.16, 0.92)
        b.update(_look((turn_lead + tw) * 0.3))
        b["hx"] = 4.0 * shot - 3.0 * walk                           # 看手機螢幕
        b["hx"] += 2.0 * bump(s, t_shot - 0.04, t_shot, t_shot + 0.02, t_shot + 0.12)
        return b, p, yaw, drop, sw, walk, shot

    def state(s, arc_w=None):
        s = max(0.0, min(dur, s))
        b, p, yaw, drop, sw, walk, shot = body(s)
        root = (p.x, p.y, -drop); rz = yaw
        P = _body(arms_down({}, l_fwd=-14 * sw, r_fwd=14 * sw, l_el=45, r_el=45), b)       # 快走：手肘彎 45°
        legs = {}
        for sd in ("L", "R"):
            fx, fy, fyaw, lift = S.foot(sd, s)
            a0 = B[f"J_Bip_{sd}_Foot"].head_local
            Aw = Vector((fx, fy, a0.z + lift))
            A = _world_to_arm(Aw, root, rz)
            rel = _wrap_angle(fyaw - rz)
            pole = A + _foot_dir(rel) * 0.5 + Vector((0, 0, 0.35))
            legs[sd] = (A, pole, rel)
        # 手機：頭前方 phone_dist、略低於眼睛；螢幕朝自己
        Ph = _fkc(arm, P, "Head")
        eye = Ph @ (lips_rest(arm) + Vector((0, 0, 0.06 * k)))
        fwd = (Ph.to_3x3() @ Vector((0, -1, 0))); fwd.z = 0; fwd.normalize()
        click = 0.010 * bump(s, t_shot - 0.04, t_shot, t_shot + 0.02, t_shot + 0.12)
        C = eye + fwd * (phone_dist + click) + Vector((0, 0, -0.03 * k))
        up = Vector((0, 0, 1)).lerp(-fwd, 0.15).normalized()
        ph = _phone_hands(arm, P, k, C, up, fwd)
        w = arc_w if arc_w is not None else (arc(_tr(s - DT, 0.16, 0.92, 0.22)) if s - DT > 0.16 else 0.0)
        arms = {sd: _mix_arm(_rest_state(arm, P, sd), ph[sd], w, arm=arm, P=P, side=sd) for sd in ("L", "R")}
        face = {"Fcl_ALL_Fun": 0.35 + 0.15 * shot, "Fcl_EYE_Close_R": 0.4 * bump(s, t_shot - 0.10, t_shot - 0.02, t_shot + 0.04, t_shot + 0.15),
                "Fcl_MTH_U": 0.2 * shot}
        hs = ("relax", "pinch", round(shot, 2))
        return dict(P=P, root=root, rz=rz, legs=legs, arms=arms, hands=(hs, hs), face=face, body=b, phone=(C, up, fwd))

    # 舉手機重新參數化（骨頭轉角照梯形速度走）：用 0.6 秒時的身體量
    def _arms_w(w):
        st0 = state(0.6 + DT, arc_w=w)
        return st0["arms"]
    arc = lambda x: x
    _b6 = state(0.6 + DT)
    arc = _arc_table(arm, _b6["P"], _arms_w)

    def fn(t):
        st_ = state(t * dur)
        P = dict(st_["P"])
        for sd in ("L", "R"):
            A, pole, rel = st_["legs"][sd]
            _leg_set(arm, P, sd, A, pole, rel)
            W, pl, R = st_["arms"][sd]
            _arm_set(arm, P, sd, W, pl, R)
        return dict(P, hands=st_["hands"], root=st_["root"], rz=st_["rz"], ground=False, face=st_["face"])

    fn.dur = dur; fn.state = state; fn.steps = S; fn.stop = tuple(X1.xy); fn.end_face = face; fn.rz0 = rz0
    fn.times = dict(walk=(0.06, walk_end), turn=(0.48 + DT, tt_[2][1] + DT), raise_phone=(0.16 + DT, 0.92 + DT), shot=t_shot)
    fn.t_phone = 0.92 + DT; fn.walk_end = walk_end; fn.steps_n = steps
    fn.feet_face = fface
    return fn


def oops_bow(origin=(0.45, 0.0), dist=0.50, dirx=-1, face=180.0, feet_turn=0.65, phone_dist=0.25, photo_dur=1.3, cam=None,
             look=-100.0, bow=30.0, dur=0.8, arm=None, steps=2, stop=None):
    """接在 walk_in_photo（同一組 origin／dist／dirx／face／feet_turn／phone_dist）的結尾：
    0～0.6 秒右手離開手機、左手把手機放到胸前 → 上身往右扭、回頭看老相機（look：從原本面向再轉幾度，負值＝往右；腳不動）→
    0～0.7 秒右手從右外側繞到後腦（之後搓一下）、苦笑 → 0.42～0.8 秒朝老相機的方向快速小鞠躬 bow 度、縮肩。
    往右回頭（往畫面右邊、出口那側）：結尾上身已經朝向出口，接 walk_fwd(dirx=+1) 往右走出去只差一點。cam 給了就照老相機方向算 look"""
    arm = arm or ARM; k = _kof(arm)
    A = walk_in_photo(origin, dist, dirx, face, feet_turn, phone_dist, photo_dur, arm=arm, steps=steps, stop=stop)
    S0 = A.state(A.dur)                              # walk_in_photo 的結尾（多走幾步時比 photo_dur 長）
    b0, root0, rz0 = S0["body"], S0["root"], S0["rz"]
    if cam is not None:
        tgt = math.degrees(math.atan2(cam[0] - root0[0], -(cam[1] - root0[1])))
        look = _wrap_angle(tgt - (rz0 + b0.get("sz", 0) + b0.get("cz", 0) + b0.get("nz", 0) + b0.get("hz", 0)))
    sgn = 1 if look > 0 else -1
    hip_t = 0.20 * look; up_t = 0.30 * look; head_t = 0.50 * look   # 骨盆（腳不動）／胸腰／脖子頭 各分多少
    legs0 = S0["legs"]
    # 抓後腦：右手掌貼後腦勺偏右的頭髮（rest 骨架空間，跟著頭轉）
    hc = _bd(arm, "J_Bip_C_Head")[0] + Vector((0.0, 0.015 * k, 0.105 * k))
    dv = Vector((-0.75, 0.50, 0.42)).normalized()
    c, n = _surface(arm, ("_Hair", "_HairBack", "_Face"), hc + dv * 0.4, -dv)
    if c is None:
        c, n = hc + dv * 0.11 * k, dv
    fy = Vector((0.25, 0.15, 1.0)); fy = (fy - n * fy.dot(n)).normalized()
    R_sc = _rot_map(Vector((0, 1, 0)), _PALM_LOC["R"], fy, -n)
    pc = c + n * 0.006 * k
    AROUND = Vector((-0.20, 0.0, 0.06)) * k          # 右手從臉前移到後腦：往右外側繞過去（直線過去會穿過頭）

    def sc_state(P, scr):
        Mh = _fkc(arm, P, "Head"); Rh = Mh.to_3x3() @ R_sc
        Wsc = _place_hand(Rh, _palm_pt(arm, "R", k), Mh @ (pc + Vector((0, 0, scr))))
        return (Wsc, _shoulder(arm, P, "R") + Vector((-0.45, 0.05, 0.30)) * k, Rh)     # 手肘往右側上方張開，前臂走在頭外側

    def body(s):
        tw = seg(s, 0.02, 0.52)
        bw = bump(s, 0.42, 0.60, 0.62, 0.80)
        sh = seg(s, 0.35, 0.70)
        b = dict(b0)
        b["sz"] = b0.get("sz", 0) + 0.55 * up_t * tw; b["cz"] = b0.get("cz", 0) + 0.45 * up_t * tw
        b["nz"] = b0.get("nz", 0) * (1 - tw) + 0.25 * head_t * tw; b["hz"] = b0.get("hz", 0) * (1 - tw) + 0.75 * head_t * tw
        b["hx"] = b0.get("hx", 0) * (1 - tw) + 6.0 * bw + 2.0 * tw
        b["shl"] = b["shr"] = 8.0 * sh                              # 縮肩
        return b, tw, bw, sh

    def state(s):
        s = max(0.0, min(dur, s))
        b, tw, bw, sh = body(s)
        hy = hip_t * tw
        rz = rz0 + hy
        P = _body(arms_down({}, l_el=45, r_el=45), b)
        # 鞠躬：往現在胸口朝的方向前彎（軸＝胸口的左右方向，骨架空間；骨盆已經用 rz 轉了）
        yaw_c = b.get("sz", 0) + b.get("cz", 0)
        ax = (math.cos(math.radians(yaw_c)), math.sin(math.radians(yaw_c)), 0.0)
        P["Spine"] = P["Spine"] + [(ax, 0.55 * bow * bw)]; P["Chest"] = P["Chest"] + [(ax, 0.30 * bow * bw)]
        root = (root0[0], root0[1], root0[2] - 0.010 * k * bw)
        legs = {}
        for sd in ("L", "R"):
            Aa, pole, rel = legs0[sd]
            Aw = _to_world(Aa, (root0[0], root0[1], rz0))          # 腳踝在世界不動
            Aw = Vector((Aw.x, Aw.y, Aa.z + root0[2]))
            An = _world_to_arm(Aw, root, rz)
            reln = rel - hy                                          # 腳在世界不動 → 相對骨盆反轉
            legs[sd] = (An, An + _foot_dir(rel - 0.5 * hy) * 0.5 + Vector((0, 0, 0.35)), reln)   # 膝蓋朝腳尖和骨盆中間（開頭＝walk_in_photo 結尾）
        # 右手：手機 → 後腦（抓頭時手上下小幅搓動）
        scr = 0.008 * k * math.sin(2 * math.pi * 3.0 * max(0.0, s - 0.66)) * seg(s, 0.66, 0.70)
        wr = arc_r(_tr(s, 0.0, 0.70, 0.25))
        armR = _mix_arm(S0["arms"]["R"], sc_state(P, scr), wr, AROUND, None, arm=arm, P=P, side="R")
        # 途中手腕離頭中心太近就沿半徑往外推（最後抓頭的位置不受影響）：手繞過去時不會擦進頭髮
        hcen = _fkc(arm, P, "Head") @ hc; dvec = Vector(armR[0]) - hcen; rmin = 0.15 * k
        if dvec.length < rmin:
            Wn = hcen + dvec.normalized() * rmin; dW = Wn - Vector(armR[0])
            armR = (Wn, Vector(armR[1]) + dW, armR[2])
        # 左手：拿著手機放到胸前（手機螢幕朝上斜向自己）
        Mc = _fkc(arm, P, "UpperChest")                               # 跟著胸口（鞠躬、扭身時手機跟著身體）
        Rl = Mc.to_3x3() @ _rot_map(Vector((0, 1, 0)), _PALM_LOC["L"], Vector((-0.35, -0.85, 0.20)), Vector((-0.55, 0.0, 0.83)))
        Wl = _place_hand(Rl, _palm_pt(arm, "L", k), Mc @ (Vector((0.07, -0.22, 1.12)) * k))
        st_l = (Wl, _shoulder(arm, P, "L") + Mc.to_3x3() @ Vector((0.35, 0.05, -0.30)) * k, Rl)
        armL = _mix_arm(S0["arms"]["L"], st_l, seg(s, 0.02, 0.62), arm=arm, P=P, side="L", elbow="dir")
        face = _mixf(S0["face"], {"Fcl_ALL_Fun": 0.6, "Fcl_ALL_Sorrow": 0.35, "Fcl_EYE_Close": 0.25, "Fcl_MTH_E": 0.25}, tw)
        face["Fcl_EYE_Close"] = face.get("Fcl_EYE_Close", 0.0) + 0.3 * bw
        hs_r = ("pinch", "cup", round(seg(s, 0.05, 0.30), 2))
        return dict(P=P, root=root, rz=rz, legs=legs, arms={"L": armL, "R": armR}, hands=("pinch", hs_r), face=face, body=b)

    arc_r = lambda x: x
    _P3 = state(0.3)["P"]
    arc_r = _arc_table(arm, _P3, lambda w: {"R": _mix_arm(S0["arms"]["R"], sc_state(_P3, 0.0), w, AROUND, None, arm=arm, P=_P3, side="R")})

    def fn(t):
        st_ = state(t * dur)
        P = dict(st_["P"])
        for sd in ("L", "R"):
            A_, pole, rel = st_["legs"][sd]
            _leg_set(arm, P, sd, A_, pole, rel)
            W, pl, R = st_["arms"][sd]
            _arm_set(arm, P, sd, W, pl, R)
        return dict(P, hands=st_["hands"], root=st_["root"], rz=st_["rz"], ground=False, face=st_["face"])

    fn.dur = dur; fn.state = state; fn.photo = A; fn.look = look; fn.phone0 = S0["phone"]
    fn.scratch = sc_state; fn.head_c = hc                # 給 turn_exit 接續用：抓頭的手臂狀態（跟著頭算）、頭的中心（rest）
    fn.times = dict(lower_phone=(0.02, 0.62), look_back=(0.02, 0.52), hand_to_head=(0.0, 0.70), scratch=(0.66, 0.8), bow=(0.42, 0.80))
    return fn


# ──────── 轉身走出去（接 oops_bow）────────
def _qslerp(a, b, w):
    """四元數球面內插，不自動換成最短路徑（正負號由呼叫端決定，路徑才不會在兩端轉動時突然換邊）"""
    d = max(-1.0, min(1.0, a.dot(b)))
    if d > 0.9995:
        q = Quaternion([x + (y - x) * w for x, y in zip(a, b)]); q.normalize(); return q
    th = math.acos(d); s_ = math.sin(th)
    if s_ < 1e-6:
        return a.copy()
    fa, fb = math.sin((1 - w) * th) / s_, math.sin(w * th) / s_
    q = Quaternion([fa * x + fb * y for x, y in zip(a, b)]); q.normalize(); return q


def _mix_arm_fk(A, B, w, arm, P, side, ref=None, fold=0.0, late_roll=False, roll=None):
    """兩個手臂狀態 (W, pole, R) 用「關節角」內插：上臂方向（含手肘轉軸）球面內插、手肘彎角線性內插、
    手相對前臂拆成「繞前臂軸的扭轉（線性內插）」＋「其餘擺動（球面內插）」。
    _mix_arm 是手腕走直線（加 bulge）；手從頭上放到身側這種大動作，手腕走直線會擦過頭和肩膀、手肘翻面，關節角內插的手會自然往外劃弧。
    ref：給一個 dict（同一個動作共用）時，第一次呼叫記下兩端的正負號，之後每格照它選邊——兩端差將近 180° 時，
    「每格各取最短路徑」會在某一格突然換到另一邊（量到一格 140°）。fold：中段手肘多彎幾度。
    late_roll：上臂先擺方向（最小旋轉）、繞上臂自轉放到後半段（w 0.45～1）、手肘在前 7 成就伸到目標角度——
    前臂留在原本那個平面裡往下甩，不會先往前平伸（手從側上方放下來用）。
    roll=(a, b)：上臂「先擺方向、再繞自己轉」，自轉在 w a～b 之間做完（手肘照 w 線性）；兩端上臂差將近 180° 時用它（四元數兩條路一樣遠，
    兩端稍微一動就會換邊），方向的球面內插只有在兩端方向正好相反時才不定"""
    if w <= 0:
        return A
    if w >= 1:
        return B
    S = _shoulder(arm, P, side)
    L1, L2 = _len_arm(arm, side)
    fr = []
    for W_, pl, R_ in (A, B):
        E, Wr, Fu, F0 = _arm_frames(arm, side, S, W_, pl)
        yu, zu = Fu.col[1], Fu.col[2]; yf = F0.col[1]
        fr.append((Fu.to_quaternion(), math.atan2(yf.dot(zu), yf.dot(yu)), (F0.transposed() @ Matrix(R_)).to_quaternion()))
    (q0, b0, r0), (q1, b1, r1) = fr
    if roll is not None:
        pass                                                      # 方向＋自轉模式不用四元數正負號
    elif ref is not None and "q0" not in ref:                     # 第一次（參考姿勢）：取最短路徑，記下兩端的正負號
        if q0.dot(q1) < 0:
            q1 = -q1
        ref["q0"], ref["q1"] = q0.copy(), q1.copy()
    elif ref is not None:                                         # 之後每格：兩端各自跟參考同號 → 走同一條路，不會換邊
        if q0.dot(ref["q0"]) < 0:
            q0 = -q0
        if q1.dot(ref["q1"]) < 0:
            q1 = -q1
    elif q0.dot(q1) < 0:
        q1 = -q1
    # 手相對前臂：拆成「繞前臂軸的扭轉」＋「其餘的擺動」，扭轉角線性內插（不會在中途越過 ±180° 讓 _arm_set 的前臂分攤翻面）
    def _st(r):
        t = 2 * math.atan2(r.y, r.w)
        t = (t + math.pi) % (2 * math.pi) - math.pi
        return r @ Quaternion((0, 1, 0), t).inverted(), t
    s0, t0 = _st(r0); s1, t1 = _st(r1)
    if s0.dot(s1) < 0:
        s1 = -s1                                                   # 手的擺動部分不到 180°，取最短路徑
    tt = t0 + (t1 - t0) * w
    if late_roll or roll is not None:
        ra, rb = roll if roll is not None else (0.45, 1.0)
        F0m, F1m = q0.to_matrix(), q1.to_matrix(); y0, y1 = F0m.col[1], F1m.col[1]
        Fs1 = y0.rotation_difference(y1).to_matrix() @ F0m
        tau = math.atan2(Fs1.col[0].cross(F1m.col[0]).dot(y1), Fs1.col[0].dot(F1m.col[0]))
        if roll is not None and ref is not None:                  # 自轉角接近 ±180° 時，照參考那格選同一邊（每格各取 atan2 會在某一格從 +179 跳到 −179）
            if "tau" in ref:
                tau += 2 * math.pi * round((ref["tau"] - tau) / (2 * math.pi))
            else:
                ref["tau"] = tau
        yw = _slerp_dir(y0, y1, w)
        Mu = Matrix.Rotation(tau * (seg(w, ra, rb) if rb - ra < 0.999 else w), 3, yw) @ y0.rotation_difference(yw).to_matrix() @ F0m
        bt = b0 + (b1 - b0) * (ease(min(1.0, w / 0.7)) if late_roll else w) + math.radians(fold) * math.sin(math.pi * w)
    else:
        Mu = _qslerp(q0, q1, w).to_matrix(); bt = b0 + (b1 - b0) * w + math.radians(fold) * math.sin(math.pi * w)
    xu, yu, zu = Mu.col[0], Mu.col[1], Mu.col[2]
    E = S + yu * L1
    yf = (yu * math.cos(bt) + zu * math.sin(bt)).normalized()
    W = E + yf * L2
    zf = xu.cross(yf).normalized()
    Ff = Matrix((xu, yf, zf)).transposed()
    R = Ff @ (_qslerp(s0, s1, w) @ Quaternion((0, 1, 0), tt)).to_matrix()
    dr = (W - S).normalized(); pp = (E - S) - dr * (E - S).dot(dr)
    if pp.length < 1e-6:
        pp = zu
    return (W, S + dr * 0.15 + pp.normalized() * 0.4, R)


def turn_exit(origin=(0.45, 0.0), dist=0.50, dirx=-1, face=180.0, feet_turn=0.65, phone_dist=0.25, photo_dur=1.3, cam=None,
              look=-100.0, bow=30.0, bow_dur=0.8, exit_dirx=1, out=0.65, stride=0.24, settle=False, arm=None, steps=2, stop=None):
    """路人甲：接在 oops_bow（同一組 origin／dist／dirx／face／feet_turn／phone_dist／photo_dur／cam／look／bow，bow_dur＝oops_bow 的 dur）的結尾：
    0～1.4 秒右手離開後腦、往外劃開再放下（前半段整隻手臂往外下方轉、後半段關節角內插），之後跟著走路前後擺；左手拿著手機留在胸前（跟著胸口）→
    腳一步一步轉向出口：前四步（0～1.28 秒）外側腳兩步各轉一半、內側腳兩步各轉一半（最後留 12° 外八），腳離地才轉、任何時刻至少一腳踩地 →
    同時縮肩 10°、低頭 10°、上身微前傾，第三步起快步往 exit_dirx（+1＝世界 +X，畫面右）走（每步 stride×體型、0.26 秒一步）。
    骨盆跟著兩腳的平均朝向轉（開頭比腳多扭的 20° 照比例收掉），頭從開頭就看著出口方向。
    out：骨盆從 oops_bow 結尾的位置沿出口方向總共走多遠（公尺，湊成整步）；轉身那四步本身就會走約 0.43×體型 m、1.28 秒，給更小也一樣。
    settle=False：最後一步落地就結束（走出鏡頭用）；True：後腳跟上併腳、兩腳轉正、站 0.25 秒（之後可接 walk_fwd(dirx=+1)）。
    秒數 fn.dur 由 out／settle 決定（預設 out=0.65 → 1.5 秒）。回傳的 root／rz 是世界座標（和 walk_in_photo 一樣，不要事後改）。
    fn.stop＝結尾骨盆的 (x, y)，fn.end_face＝出口朝向，fn.times＝各段秒數與每一步的起訖"""
    arm = arm or ARM; k = _kof(arm); B = arm.data.bones
    O = oops_bow(origin, dist, dirx, face, feet_turn, phone_dist, photo_dur, cam, look, bow, bow_dur, arm=arm, steps=steps, stop=stop)
    S0 = O.state(bow_dur)
    b_end, f_end = dict(S0["body"]), dict(S0["face"])
    root0, rz0 = S0["root"], S0["rz"]
    Sw = O.photo.steps
    f0 = {sd: Sw.foot(sd, 1e3) for sd in ("L", "R")}
    fy0 = f0["L"][2]
    he = 90.0 if exit_dirx > 0 else -90.0
    dturn = _wrap_angle(he - fy0); hfin = fy0 + dturn
    sg = 1.0 if dturn > 0 else -1.0
    first = "R" if dturn < 0 else "L"; second = "L" if first == "R" else "R"
    # 腳尖朝向：外側那隻腳（往右轉＝右腳）兩步各轉一半；內側那隻腳最後留 12° 外八（自然站姿），兩步各轉剩下的一半
    toe = -sg * 12.0
    hf = {first: hfin, second: hfin + toe}
    h1 = {first: fy0 + dturn * 0.5, second: fy0 + (dturn + toe) * 0.5}
    rz0u = fy0 + _wrap_angle(rz0 - fy0)
    rzw = O.photo.state(O.photo.dur)["rz"]; q0 = 0.5 * _wrap_angle(rz0 - rzw)       # oops_bow 結尾膝蓋方向的偏移（骨盆扭過去一半）
    avg_end = hfin if settle else hfin + toe * 0.5                    # 兩腳最後的平均朝向（settle 時最後兩腳都轉正）
    ratio = (hfin - rz0u) / (avg_end - fy0) if abs(avg_end - fy0) > 1e-6 else 1.0   # 骨盆最後正對出口
    e = Vector((1.0 if exit_dirx > 0 else -1.0, 0.0, 0.0))
    hw = abs(B["J_Bip_L_Foot"].head_local.x)
    c0 = Vector(((f0["L"][0] + f0["R"][0]) / 2, (f0["L"][1] + f0["R"][1]) / 2, 0.0))

    def place(sd, along, h):
        r = math.radians(h); lat = Vector((math.cos(r), math.sin(r), 0.0))
        q = c0 + e * along + lat * (hw if sd == "L" else -hw)
        return (q.x, q.y, h)
    S_ = stride * k
    # 換步表：前兩步原地往出口側挪、腳尖各轉一半；第三、四步轉完並開始往前走；之後照步幅走到 out
    a_1, a_2 = 0.10 * k, 0.20 * k
    a_3 = a_2 + 0.7 * S_; a_4 = a_3 + 0.6 * S_
    stp = [(first, 0.00, 0.40, place(first, a_1, h1[first]), 0.030 * k),
           (second, 0.28, 0.68, place(second, a_2, h1[second]), 0.035 * k),
           (first, 0.56, 0.98, place(first, a_3, hf[first]), 0.040 * k),
           (second, 0.84, 1.28, place(second, a_4, hf[second]), 0.045 * k)]
    al = {first: a_3, second: a_4}; sd = first; t0 = 1.14; t_end = 1.28
    while (al["L"] + al["R"]) / 2 < out:
        a_n = al["L" if sd == "R" else "R"] + S_
        stp.append((sd, t0, t0 + 0.36, place(sd, a_n, hf[sd]), 0.045 * k)); al[sd] = a_n
        t_end = t0 + 0.36; t0 += 0.26
        sd = "L" if sd == "R" else "R"
    if settle:                                                        # 後面那隻腳跟上來、併腳站好
        a_n = al["L" if sd == "R" else "R"]
        stp.append((sd, t0, t0 + 0.30, place(sd, a_n, hfin), 0.030 * k)); al[sd] = a_n
        t_end = t0 + 0.30
        other = "L" if sd == "R" else "R"
        if abs(hf[other] - hfin) > 1e-6:                             # 另一隻腳還外八：原地抬一下轉正（接 walk_fwd 時兩腳都正對出口）
            stp.append((other, t0 + 0.24, t0 + 0.50, place(other, al[other], hfin), 0.020 * k))
            t_end = t0 + 0.50
    dur = round(t_end + (0.25 if settle else 0.0), 3)
    St = _Steps({sd_: f0[sd_][:3] for sd_ in ("L", "R")}, stp)
    L1, L2 = _len_leg(arm, "L")

    def _pxy(s):
        w = max(0.0, min(0.12, s, dur - s)); acc = Vector((0, 0, 0)); ys = []
        for i in range(-4, 5):
            tt = s + i * w / 4
            fl, fr = St.foot("L", tt), St.foot("R", tt)
            acc += Vector(((fl[0] + fr[0]) * 0.5, (fl[1] + fr[1]) * 0.5, 0))
            ys.append(fl[2] + _wrap_angle(fr[2] - fl[2]) * 0.5)
        y_ = ys[0]
        return acc / 9.0, y_ + sum(_wrap_angle(y - y_) for y in ys) / 9.0

    def _rz(ya):
        return rz0u + ratio * (ya - fy0)                              # 骨盆跟著腳轉（開頭比腳多扭的那段照比例收掉）

    def _need(s):
        p, ya = _pxy(s); rz = _rz(ya)
        req = (SOFT_KNEE + 0.006 * seg(s, 0.30, 0.60) * (1 - (seg(s, dur - 0.45, dur - 0.15) if settle else 0.0))) * k
        for sd_ in ("L", "R"):
            fx, fy, fyaw, lift = St.foot(sd_, s)
            a0 = B[f"J_Bip_{sd_}_Foot"].head_local
            Aa = _world_to_arm(Vector((fx, fy, a0.z + lift)), (p.x, p.y, 0.0), rz)
            h = B[f"J_Bip_{sd_}_UpperLeg"].head_local; Rl = (L1 + L2) * 0.993
            dxy = (Vector((Aa.x, Aa.y)) - Vector((h.x, h.y))).length
            if dxy < Rl:
                req = max(req, h.z - Aa.z - math.sqrt(Rl * Rl - dxy * dxy))
        return req

    _N = int(round(dur * 100)) + 1; _req = [_need(dur * i / (_N - 1)) for i in range(_N)]
    _w = 3; _mx = [max(_req[max(0, i - _w):i + _w + 1]) for i in range(_N)]
    _base = [sum(_mx[max(0, i - _w):i + _w + 1]) / len(_mx[max(0, i - _w):i + _w + 1]) for i in range(_N)]
    d0 = -root0[2]

    def _drop(s):
        x = max(0.0, min(1.0, s / dur)) * (_N - 1); i = min(int(x), _N - 2); f = x - i
        b_ = _base[i] * (1 - f) + _base[i + 1] * f
        return b_ + (d0 - _base[0]) * (1 - seg(s, 0.0, 0.25))       # 開頭＝oops_bow 結尾的高度

    up0 = b_end.get("sz", 0.0) + b_end.get("cz", 0.0)
    rs = b_end.get("sz", 0.0) / up0 if abs(up0) > 1e-6 else 0.55
    hd0 = b_end.get("nz", 0.0) + b_end.get("hz", 0.0)
    rn = b_end.get("nz", 0.0) / hd0 if abs(hd0) > 1e-6 else 0.25
    head_w0 = rz0u + up0 + hd0
    dhead = _wrap_angle(hfin - head_w0)
    sh0 = b_end.get("shl", 0.0); sx0 = b_end.get("sx", 0.0); hx0 = b_end.get("hx", 0.0)

    def body(s):
        p, ya = _pxy(s); rz = _rz(ya)
        endw = seg(s, dur - 0.45, dur - 0.10) if settle else 0.0
        walk = seg(s, 0.50, 0.85) * (1 - endw)
        fl, fr = St.foot("L", s), St.foot("R", s)
        sw = max(-1.0, min(1.0, ((Vector(fr[:2]) - Vector(fl[:2])).dot(e.xy)) / S_)) * walk   # 右腳在前＝正
        up = up0 * (1 - seg(s, 0.15, 1.05))
        head_w = head_w0 + dhead * seg(s, 0.05, 0.60)
        hd = head_w - rz - up
        b = dict(b_end)
        b["sz"] = up * rs - 2.0 * sw; b["cz"] = up * (1 - rs) + 1.5 * sw
        b["nz"] = hd * rn; b["hz"] = hd * (1 - rn)
        b["sx"] = sx0 + (5.0 - sx0) * seg(s, 0.20, 0.70) * (1 - endw)
        b["shl"] = b["shr"] = sh0 + (10.0 - sh0) * seg(s, 0.0, 0.40)
        b["hx"] = hx0 * (1 - seg(s, 0.0, 0.40))
        dn = 10.0 * seg(s, 0.10, 0.60)                                # 低頭（沿頭的朝向算前彎軸）
        return b, p, rz, walk, sw, dn

    scr_end = 0.008 * k * math.sin(2 * math.pi * 3.0 * max(0.0, bow_dur - 0.66)) * seg(bow_dur, 0.66, 0.70)
    VIA = -70.0                                                       # 右手放下前半段：繞胸口前後軸往外下方轉幾度
    hc = O.head_c; rmin = 0.15 * k

    def state(s, arc_w=None):
        s = max(0.0, min(dur, s))
        b, p, rz, walk, sw, dn = body(s)
        root = (p.x, p.y, -_drop(s))
        P = _body(arms_down({}, l_el=45, r_el=45, r_fwd=-14.0 * sw), b)
        yh = b["sz"] + b["cz"] + b["nz"] + b["hz"]
        axh = (math.cos(math.radians(yh)), math.sin(math.radians(yh)), 0.0)
        P["Neck"] = list(P.get("Neck", [])) + [(axh, 0.4 * dn)]; P["Head"] = list(P.get("Head", [])) + [(axh, 0.6 * dn)]
        legs = {}
        for sd_ in ("L", "R"):
            fx, fy, fyaw, lift = St.foot(sd_, s)
            a0 = B[f"J_Bip_{sd_}_Foot"].head_local
            Aa = _world_to_arm(Vector((fx, fy, a0.z + lift)), root, rz)
            rel = fyaw - rz
            q = q0 * (1 - seg(s, 0.0, 0.35))
            legs[sd_] = (Aa, Aa + _foot_dir(rel + q) * 0.5 + Vector((0, 0, 0.35)), rel)
        # 左手：手機留在胸前（和 oops_bow 結尾同一個拿法，跟著 UpperChest）
        Mc = _fkc(arm, P, "UpperChest")
        Rl = Mc.to_3x3() @ _rot_map(Vector((0, 1, 0)), _PALM_LOC["L"], Vector((-0.35, -0.85, 0.20)), Vector((-0.55, 0.0, 0.83)))
        Wl = _place_hand(Rl, _palm_pt(arm, "L", k), Mc @ (Vector((0.07, -0.22, 1.12)) * k))
        armL = (Wl, _shoulder(arm, P, "L") + Mc.to_3x3() @ Vector((0.35, 0.05, -0.30)) * k, Rl)
        # 右手：從後腦放下到身側，之後跟著走路前後擺（0～1.4 秒；前半段整隻手臂繞胸口前後軸往外下方轉 70°＝手離開頭往外劃開，
        # 後半段關節角內插到走路的垂手、上臂自轉放後面（late_roll）。直接內插的話手會整隻往前伸直劃過臉前；
        # 再快的話前臂每格超過 15°）
        wd = arc_w if arc_w is not None else arc_d(_tr(s, 0.0, 1.40, 0.30))
        st0 = O.scratch(P, scr_end * (1 - seg(s, 0.0, 0.15)))
        # 走路時垂下的右手：在「上身沒扭」的姿勢裡用 arms_down 擺好，再整隻跟著胸口搬到現在的姿勢
        #（arms_down 的角度是骨架軸，上身扭 50° 時直接用，手會垂到身體後面）
        P_ref = _body(arms_down({}, l_el=45, r_el=25, r_fwd=-10.0 * sw), {"sx": b["sx"], "shl": b["shl"], "shr": b["shr"]})   # 手肘微彎 25°、前後擺 ±10°
        Mr = _fkc(arm, P_ref, "UpperChest"); Tm = _fkc(arm, P, "UpperChest") @ Mr.inverted()
        Wt, plt, Rt = _rest_state(arm, P_ref, "R")
        tgt = (Tm @ Wt, Tm @ plt, Tm.to_3x3() @ Rt)
        Sh = _shoulder(arm, P, "R"); ax = (Mc.to_3x3() @ Vector((0, 1, 0))).normalized()
        Rv = Matrix.Rotation(math.radians(VIA * min(1.0, wd / 0.5)), 3, ax)
        via = (Sh + Rv @ (Vector(st0[0]) - Sh), Sh + Rv @ (Vector(st0[1]) - Sh), Rv @ Matrix(st0[2]))
        armR = via if wd <= 0.5 else _mix_arm_fk(via, tgt, (wd - 0.5) / 0.5, arm, P, "R", ref=REF, late_roll=True)
        hcen = _fkc(arm, P, "Head") @ hc; dvec = Vector(armR[0]) - hcen
        if dvec.length < rmin:
            Wn = hcen + dvec.normalized() * rmin; dW = Wn - Vector(armR[0])
            armR = (Wn, Vector(armR[1]) + dW, armR[2])
        face = _mixf(f_end, {"Fcl_ALL_Fun": 0.45, "Fcl_ALL_Sorrow": 0.40, "Fcl_EYE_Close": 0.20, "Fcl_MTH_E": 0.20}, seg(s, 0.0, 0.50))
        hs_r = ("cup", "relax", round(seg(s, 0.10, 0.45), 2))
        return dict(P=P, root=root, rz=rz, legs=legs, arms={"L": armL, "R": armR}, hands=("pinch", hs_r), face=face, body=b)

    REF = {}                                                          # late_roll 不用正負號參考（留著給 _mix_arm_fk 的預設路徑）
    arc_d = lambda x: x
    _P3 = state(0.25)["P"]
    arc_d = _arc_table(arm, _P3, lambda w: {"R": state(0.25, arc_w=w)["arms"]["R"]})

    def fn(t):
        st_ = state(t * dur)
        P = dict(st_["P"])
        for sd_ in ("L", "R"):
            A_, pole, rel = st_["legs"][sd_]
            _leg_set(arm, P, sd_, A_, pole, rel)
            W, pl, R = st_["arms"][sd_]
            _arm_set(arm, P, sd_, W, pl, R)
        return dict(P, hands=st_["hands"], root=st_["root"], rz=st_["rz"], ground=False, face=st_["face"])

    pe, _ = _pxy(dur)
    fn.dur = dur; fn.state = state; fn.steps = St; fn.prev = O; fn.stop = (pe.x, pe.y); fn.end_face = he
    fn.times = dict(lower_hand=(0.0, 1.4), turn=(0.0, 1.28), walk=(0.56, dur), steps=[(x[0], x[1], x[2]) for x in stp])
    return fn


V12_PASSERBY = [("walk_in_photo", "走進來舉手機拍照", _lazy(lambda: walk_in_photo()), 31),
                ("oops_bow", "尷尬抓頭鞠躬", _lazy(lambda: oops_bow()), 19),
                ("turn_exit", "轉身走出去", _lazy(lambda: turn_exit()), 36)]


# ════════════════════════ 8. 真人揮手（CMU 動作捕捉，循環） ════════════════════════
# 2026-10-09 新增（V12 第 2 輪回饋：「雙手舉高之後只有前臂在左右甩、大臂固定住超奇怪」「新郎右手揮、左手放下打直」）。
# 上半身（骨盆、腰、胸、頸、頭、肩、手臂）照抄真人資料（mocap_retarget.mocap_action，heading=None＝原地、面向 −Y）；
# 腿不抄，用站姿腳鎖（feet=PLANT），腳底不滑；骨盆只跟著真人左右晃（限 ±2 cm）。
# 資料照 60 fps 播（cgspeed 版檔頭寫 120，但 141／143 照 120 播是每秒揮 5 下，照 60 播約 2.6 下／秒才像真人），見 library/mocap/README.md。
# 循環：從揮動中段取整數個揮動週期（自動量週期），結尾 fade 秒和開頭前 fade 秒交叉淡入，頭尾相接；播放長度固定成 dur。
# 來源（src）：
#   "143"：143_25「Waving」第 175～380 格，左手揮（手臂往側前方舉、前臂直立，大臂擺約 40°）——預設
#   "141"：141_16「Wave Hello」第 34～200 格，右手揮（手肘約與肩同高、手在耳朵旁，大臂擺約 30°）
# hand：要揮哪一隻手（"R"／"L"）；和來源不同側時整段左右鏡射。另一隻手放下打直（arms_down，手肘 down_el 度）。
# hand="both"：兩手都揮（CMU 沒有雙手左右揮的乾淨片段：143_25 的雙手段是在頭前交叉開合、會擋臉）——
#   主手照來源，另一隻手用鏡射後晚半個週期的同一段資料，兩手同方向擺（像雨刷）；軀幹照來源但左右扭轉、側彎減半。
import os as _os
from mathutils import Quaternion as _Quat
MOCAP_WAVE = {"143": ("143_25.bvh", (255, 385), "L"), "141": ("141_16.bvh", (34, 200), "R")}
WAVE_KEYS = ("Hips", "Spine", "Chest", "UpperChest", "Neck", "Head",
             "L_Shoulder", "L_UpperArm", "L_LowerArm", "L_Hand", "R_Shoulder", "R_UpperArm", "R_LowerArm", "R_Hand")
_SIDE_SW = lambda k: k.replace("L_", "#").replace("R_", "L_").replace("#", "R_")


def _mirror_q(q):
    """世界旋轉的左右鏡射（對 YZ 平面）：(w, x, y, z) → (w, x, −y, −z)"""
    return _Quat((q.w, q.x, -q.y, -q.z))


def _wave_period(R, side, lo=12, hi=110):
    """揮動週期（格）：揮的那隻手（上臂、前臂、手）在 lag 格後回到最像的姿勢——取第一個明顯的谷底"""
    keys = (f"{side}_UpperArm", f"{side}_LowerArm", f"{side}_Hand"); n = len(R)
    def d(lag):
        idx = range(0, n - lag, 2)
        return sum(sum(R[i][k].rotation_difference(R[i + lag][k]).angle for k in keys) for i in idx) / max(1, len(idx))
    ds = {lag: d(lag) for lag in range(lo, min(hi, n // 2))}
    lags = sorted(ds)
    for lg in lags[1:-1]:
        if ds[lg] <= ds[lg - 1] and ds[lg] <= ds[lg + 1] and ds[lg] < 0.6 * max(ds.values()):
            return lg
    return min(ds, key=ds.get)


def wave_mocap(hand="R", src="143", cycles=None, fade=0.25, src_fps=60.0, smile=0.6, down_el=6.0, both_out=20.0, arm=None):
    arm = arm or ARM
    if "mocap_action" not in globals():
        use("mocap_retarget")
    fname, (fa, fb), sside = MOCAP_WAVE[src]
    W = mocap_action(_os.path.join(LIB, "mocap", fname), frames=(fa, fb), heading=None, origin=(0.0, 0.0), src_fps=src_fps,
                     arm=arm, foot_fix=False, fix_arm_offset=False)
    rig = W.rig; rq = rig.rest_q; roots = W.roots; N = len(W.R)
    main = sside if hand == "both" else hand
    if main != sside:                                             # 鏡射「rest → 姿勢」的變化量，再套回自己這一側的 rest
        R = [{k: _mirror_q(Rf[_SIDE_SW(k)] @ rq[_SIDE_SW(k)].inverted()) @ rq[k] for k in rig.keys} for Rf in W.R]
        roots = [Vector((-r.x, r.y, r.z)) for r in roots]
    else:
        R = W.R
    per = _wave_period(R, main)
    F = int(round(fade * src_fps)); i0 = F
    room = N - 1 - i0 - (per // 2 if hand == "both" else 0)
    n_cyc = cycles or max(1, (room - per // 3) // per)
    # 一圈的實際長度：在 n_cyc 個週期附近（±1/3 週期）找「結尾最像開頭」的那一格，接縫的交叉淡入才不會把兩個不同相位混在一起
    keys_m = (f"{main}_UpperArm", f"{main}_LowerArm")
    sim = lambda j: sum(R[i0][k].rotation_difference(R[j][k]).angle for k in keys_m)
    L = min(range(max(per, n_cyc * per - per // 3), min(room, n_cyc * per + per // 3) + 1), key=lambda Lc: sim(i0 + Lc))
    if hand == "both":                                            # 另一隻手：鏡射主手、晚半個週期
        oth = _SIDE_SW(main + "_"); oth = oth[0]; half = per / 2.0
        Rm = [{k: _mirror_q(Rf[_SIDE_SW(k)] @ rq[_SIDE_SW(k)].inverted()) @ rq[k] for k in rig.keys} for Rf in R]
    dur = L / src_fps
    mean = sum((roots[i] for i in range(i0, i0 + L)), Vector()) / L
    k_ = _kof(arm)

    def Rat(RR, x):
        x = max(0.0, min(N - 1.001, x)); i = int(x); f = x - i
        return {k: _slerp(RR[i][k], RR[i + 1][k], f) for k in rig.keys}

    def loop(RR, x):
        """循環取樣：x 是從 i0 起的格數（可以超過 L）"""
        u = x % L
        Ra = Rat(RR, i0 + u)
        if u > L - F:
            w = ease((u - (L - F)) / F); Rb = Rat(RR, i0 + u - L)
            Ra = {k: _slerp(Ra[k], Rb[k], w) for k in rig.keys}
        return Ra

    def fn(t):
        x = (t % 1.0) * L
        Ra = loop(R, x)
        if hand == "both":
            Rb = loop(Rm, x + half)
            for kk in ("Shoulder", "UpperArm", "LowerArm", "Hand"):
                Ra[f"{oth}_{kk}"] = Rb[f"{oth}_{kk}"]
            for kk in ("Hips", "Spine", "Chest", "UpperChest", "Neck", "Head"):      # 軀幹：和鏡射版平均（左右扭轉、側彎抵掉一半）
                Ra[kk] = _slerp(Ra[kk], Rb[kk], 0.5)
            # 兩手整條手臂繞肩膀往外張 both_out 度（繞世界前後軸）：VRoid 的頭比真人大，往內擺的那隻手會貼到臉旁（25° 斜角看像摸頭）
            for sd, sg in (("L", 1), ("R", -1)):
                q = _Quat((0, 1, 0), math.radians(sg * both_out))
                for kk in ("UpperArm", "LowerArm", "Hand"):
                    Ra[f"{sd}_{kk}"] = q @ Ra[f"{sd}_{kk}"]
        full = rig.to_dict(Ra)
        # 揮的手：手腕不抄真人（CMU 的手骨只有一節、手腕方向雜訊大，套上去手掌往下垂），手掌順著前臂、掌心轉向前方（palms）
        P = {k: full[k] for k in WAVE_KEYS if k in full and not (k.endswith("_Hand") and (hand == "both" or k[0] == hand))}
        if hand == "both":
            hands = ("open", "open"); palms = [("L", (0, -1, 0)), ("R", (0, -1, 0))]
        else:
            dn = "R" if hand == "L" else "L"
            for kk in ("Shoulder", "UpperArm", "LowerArm", "Hand"):
                P.pop(f"{dn}_{kk}", None)
            Q = arms_down({}, l_el=down_el, r_el=down_el)
            for kk in ("UpperArm", "LowerArm", "Hand"):
                P[f"{dn}_{kk}"] = Q[f"{dn}_{kk}"]
            hands = ("relax", "open") if hand == "R" else ("open", "relax")
            palms = [(hand, (0, -1, 0))]
        r = roots[i0 + int(x) % L] - mean
        sx = max(-0.02, min(0.02, r.x)); sy = max(-0.02, min(0.02, r.y))
        blink = 1.0 if 0.40 < (t % 1.0) < 0.43 else 0.0
        return dict(P, hands=hands, palms=palms, root=(sx * k_, sy * k_, -SOFT_KNEE * BODY_S), feet=PLANT,
                    face={"Fcl_ALL_Fun": smile, "Fcl_EYE_Close": blink})
    fn.dur = dur
    fn.info = dict(W.info, src=fname, loop_src_frames=(fa + i0, fa + i0 + L), period_frames=per, seam_deg=round(math.degrees(sim(i0 + L)), 1), cycles=n_cyc,
                   wave_hz=round(src_fps / per, 2), dur=round(dur, 3), mirrored=main != sside)
    return fn


# 格數＝真人一圈的長度 × 24（播放速度和真人一樣）：143_25 第 270～370 格＝週期 30 格（60 fps，每秒 2 下）× 約 3.3 下＝1.667 秒＝40 格。
# 改了 MOCAP_WAVE 的格號範圍要重量（fn.real().info["dur"]）再改這裡
V12_WAVES = [("wave_r", "真人單手揮手（右手，左手放下）", _lazy(lambda: wave_mocap("R")), 40),
             ("wave_l", "真人單手揮手（左手，右手放下）", _lazy(lambda: wave_mocap("L")), 40),
             ("wave2_mocap", "真人雙手揮手", _lazy(lambda: wave_mocap("both")), 40)]


# ════════════════════════ 9. 頭上比愛心（指尖在頭頂相碰） ════════════════════════
# 2026-10-09 新增（V12 第 8 幕回饋：「新娘不像是比愛心，手掌方向也不正確」）。actions.py 的 heart 是兩手直直舉高、掌心朝前、
# 手沒有碰在一起，看起來像投降。這裡用 IK：兩手指尖在頭頂正上方相碰（指尖往內下方斜），手腕在兩側、掌心朝下，
# 手肘往外撐開——上臂、前臂從肩膀往外再往內彎回頭頂，和頭一起圍成愛心（頭是愛心的尖端）。
# 頭頂高度每個角色自己量（頭髮網格在頭頂正中附近的最高點），所以換角色、換髮型都會貼在頭髮上方 gap 公尺。
HANDS.setdefault("heart_top", dict(Thumb=(0, 10, 8), Index=(8, 14, 10), Middle=(8, 14, 10), Ring=(10, 16, 12), Little=(12, 18, 14),
                                   spread=3, thumb_in=25))
_CROWN = {}


def _crown(arm):
    """rest 時頭頂（頭髮、臉）在中線附近的最高點 (y, z)，骨架空間"""
    if arm.name not in _CROWN:
        who = _who(arm); best = None
        for nm in (f"{who}_Hair", f"{who}_Face"):
            o = bpy.data.objects.get(nm)
            if o is None or o.type != "MESH":
                continue
            M = arm.matrix_world.inverted() @ o.matrix_world        # 物件可能跟著骨架搬到場景裡，換回骨架空間
            for v in o.data.vertices:
                p = M @ v.co
                if abs(p.x) < 0.03 and (best is None or p.z > best.z):
                    best = p.copy()
        _CROWN[arm.name] = (best.y, best.z)
    return _CROWN[arm.name]


def _hand_len(arm, side):
    """手腕到中指指尖的長度（rest）"""
    B = arm.data.bones
    tip = B.get(f"J_Bip_{side}_Middle3")
    return (tip.tail_local - B[f"J_Bip_{side}_Hand"].head_local).length if tip else 0.16 * _kof(arm)


def heart_head(gap=0.0, slope=0.25, fwd=0.0, elbow_out=0.55, sway=1.0, arm=None):
    """gap：指尖相碰的點離頭頂多高（m）；slope：指尖往下斜的程度（手的方向＝(∓1, 0, −slope)）；
    fwd：相碰點往前（−Y）多少；elbow_out：手肘往外的 pole 距離（m，新娘尺寸）；sway：身體左右輕晃的倍率"""
    arm = arm or ARM; k = _kof(arm)
    cy, cz = _crown(arm)
    C = Vector((0.0, cy - fwd * k, cz + gap * k))
    ik = []
    for sd, sg in (("L", 1), ("R", -1)):
        d = Vector((-sg, 0.0, -slope)).normalized()                    # 手腕 → 指尖（往中線、往下）
        hl = _hand_len(arm, sd)
        Wr = C - d * hl + Vector((sg * 0.004 * k, 0, 0))               # 兩手指尖各留 4 mm，碰到但不互穿
        pole = Vector((sg * elbow_out * k, cy + 0.05 * k, cz - 0.05 * k))
        ik.append((sd, Wr, pole, Wr + d, "UpperChest"))

    def fn(t):
        P = arms_down({})
        P["Spine"] = [("Y", 2.5 * sway * s(t))]; P["Head"] = [("Y", -1.5 * sway * s(t)), ("X", -2)]
        return dict(P, hands=("heart_top", "heart_top"), ik=ik, palms=[("L", (0, 0, -1), 1.0, 0.0), ("R", (0, 0, -1), 1.0, 0.0)],
                    root=(0, 0, -SOFT_KNEE * BODY_S), feet=PLANT, face={"Fcl_ALL_Fun": 0.6})
    fn.crown = (cy, cz); fn.ik = ik
    return fn


V12_HEART = [("heart_head", "頭上比愛心（指尖相碰）", _lazy(lambda: heart_head()), 48)]


# ════════════════════════ 10. 水平弧形揮手（IK，肩胛跟著抬） ════════════════════════
# 2026-10-09 新增（V12 第 3 輪：⑧「新郎揮手動作看起來還是很奇怪，不是水平橫移劃小弧形的那種揮手」「新郎肩膀消失，突然有破圖」；
# ③「肩膀變低、脖子變長、雙手變很細」）。
# 為什麼不用真人資料：wave_mocap（CMU 143_25）的肩胛骨（Shoulder）轉位後往下壓 43～46°（量 ⑧ 新郎 6.4～8.0 秒），
# 外套的肩頂掉 1.3 cm、脖子露出變長 15～24%、肩膀輪廓不見；而且 143_25 是前臂直立左右甩，不是使用者要的「水平橫移」。
# CMU 沒有「整隻手臂水平劃弧」的乾淨片段，所以這裡用 IK 做，只寫手腕要走的軌跡，其他交給 IK：
#   - 手腕目標在臉旁、比肩關節高 height，左右水平來回 amp（全幅），軌跡是往下凹的小弧（兩端高 sag、中間低）；
#   - 肘的方向（pole）往外下方 → 大臂繞肩擺、手肘跟著左右移，不是只有前臂在動；
#   - 肩胛骨（Shoulder）跟著上抬 sh_up 度（外端多抬 sh_swing），肩部網格不被壓扁；
#   - 手掌立起、掌心朝前（palms），手腕只跟前臂差 ≤ wrist_max 度（往動作反方向輕微落後）；
#   - 起手、收手 raise／lower 秒，緩入緩出（手從垂下沿弧線抬到起點）。
# hand：'R'／'L'／'both'（both：兩手各在自己那一側，sync='mirror'（預設）＝一起往外再一起往內；'same'＝同方向擺（雨刷），錯開半拍那個來回左手轉速會到 23°/格）。
# 座標寫在 rest 骨架空間、跟著 UpperChest 走（ik 第 5 欄），所以軀幹的呼吸、男性骨盆修正都不會把手甩開。
def wave_arc(hand="R", amp=0.26, height=0.12, out=0.16, fwd=0.15, sag=0.035, hz=1.5, cycles=3, raise_t=1.0, lower_t=1.0,
             sh_up=14.0, sh_swing=4.0, wrist_max=20.0, pole_out=0.40, pole_down=0.30, sync="mirror", hold=False, smile=0.6, arm=None):
    """amp：左右全幅（公尺，新娘尺寸 × 體型）；height：手腕比肩關節（UpperArm 頭）高多少；out：弧線中心往外多少；fwd：往前多少；
    sag：弧線兩端比中間高多少；hz：每秒幾個來回；cycles：揮幾個來回；raise_t／lower_t：起手／收手秒數；
    sh_up：肩胛上抬（度）；sh_swing：手到外端時肩胛多抬；wrist_max：手掌最多偏離前臂幾度；hold＝True：不收手（情境裡揮到鏡頭結束）"""
    arm = arm or ARM; k = _kof(arm); B_ = arm.data.bones
    sides = ("L", "R") if hand == "both" else (hand,)
    per = 1.0 / hz; wave_d = cycles * per
    dur = raise_t + wave_d + (0.0 if hold else lower_t)
    geo = {}
    for sd in sides:
        sg = 1.0 if sd == "L" else -1.0                                   # 角色左手在 +X
        Sh = B_[f"J_Bip_{sd}_Shoulder"].head_local; UA = B_[f"J_Bip_{sd}_UpperArm"].head_local
        L1 = (B_[f"J_Bip_{sd}_LowerArm"].head_local - UA).length; L2 = (B_[f"J_Bip_{sd}_Hand"].head_local - B_[f"J_Bip_{sd}_LowerArm"].head_local).length
        geo[sd] = (sg, Sh.copy(), UA.copy(), L1, L2)

    def shoulder_pt(sd, deg):
        sg, Sh, UA, L1, L2 = geo[sd]
        return Sh + Matrix.Rotation(math.radians(-sg * deg), 3, "Y") @ (UA - Sh)   # 和 P["<sd>_Shoulder"]＝("Y", −sg×deg) 同一個旋轉

    def elbow(S, W, Pp, L1, L2):
        v = W - S; d_ = max(1e-4, min(v.length, (L1 + L2) * 0.999)); dr = v.normalized()
        a = math.acos(max(-1.0, min(1.0, (L1 * L1 + d_ * d_ - L2 * L2) / (2 * L1 * d_))))
        pp = Pp - S; pp = pp - dr * pp.dot(dr)
        pp = pp.normalized() if pp.length > 1e-6 else Vector((0, 0, -1))
        return S + dr * math.cos(a) * L1 + pp * math.sin(a) * L1

    def phase(tt, sd):
        """揮動相位：u∈[−1,1]（+1＝外端）、du＝速度方向；淡入淡出用的權重 a（0＝垂手、1＝在弧上）"""
        w0 = tt - raise_t
        if tt < raise_t:
            a = ease(tt / raise_t); x = 0.0
        elif hold or w0 < wave_d:
            a = 1.0; x = w0
        else:
            a = 1.0 - ease(min(1.0, (w0 - wave_d) / lower_t)); x = wave_d
        th = 2 * math.pi * hz * x
        if hand == "both" and sync == "same" and sd == "L":
            # 同方向擺：左手相位差半圈（一手往外時另一手往內）。起手、收手時兩手都在外端（從內端起手，掌心要轉將近 180°、會翻面），
            # 相位差在第一個來回內慢慢拉開、最後一個來回內收回（hold 時不收）
            ramp = min(1.0, x / per)
            if not hold:
                ramp = min(ramp, max(0.0, (wave_d - x) / per))
            th += math.pi * ease(ramp)
        # 起手時從弧線外端開始（u＝+1，cos 起點），速度連續
        return math.cos(th), -math.sin(th), a

    def wrist_target(sd, u, a):
        sg, Sh, UA, L1, L2 = geo[sd]
        deg = (sh_up + sh_swing * max(0.0, u)) * a
        S = shoulder_pt(sd, deg)
        lat = out + 0.5 * amp * u
        Wa = S + Vector((sg * lat * k, -(fwd + 0.02 * u * u) * k, (height + sag * u * u) * k))
        Wd = S + Vector((sg * 0.07 * k, -0.06 * k, -(L1 + L2) * 0.93))           # 垂手（手腕在肩下、略往前）
        mid = (Wa + Wd) / 2 + Vector((sg * 0.12 * k, -0.06 * k, 0.0))           # 起手走往外的弧，不從身體前面穿過
        W = (1 - a) ** 2 * Wd + 2 * (1 - a) * a * mid + a * a * Wa
        return S, W, deg

    def fn(t):
        tt = (t % 1.0) * dur
        P = arms_down({})
        P["Spine"] = []; P["Head"] = []
        ik = []; palms = []; hs = {}
        for sd in ("L", "R"):
            hs[sd] = "relax"
        sway = 0.0
        for sd in sides:
            sg, Sh, UA, L1, L2 = geo[sd]
            u, du, a = phase(tt, sd)
            S, W, deg = wrist_target(sd, u, a)
            P[f"{sd}_Shoulder"] = [("Y", -sg * deg)]
            # IK 之前的底稿（FK）：從垂手（arms_down）漸變到「上臂外展、前臂立起、掌心朝前」。IK 的 aim 是最小旋轉，
            # 底稿已經掌心朝前，palms 只剩小修正；底稿若停在垂手，手掌要扭將近 180° 才朝前，起手中段會一格翻面
            # 號誌照 arms_down（L_UpperArm Y +72＝垂下、R −72；R_LowerArm Y +＝前臂往上）：sg＝+1（左）／−1（右）
            P[f"{sd}_UpperArm"] = [("X", -90.0 * a), ("Y", sg * (72.0 * (1 - a) + 10.0 * a))]
            P[f"{sd}_LowerArm"] = [("Y", sg * (8.0 * (1 - a) - 100.0 * a)), ("X", -18.0 * (1 - a))]
            P[f"{sd}_Hand"] = [("X", -6.0 * (1 - a))]
            # 手肘方向點：在弧上＝往外下方；垂手時改往外後方（垂手的 pole 若也往下，會和手臂同方向、IK 的手肘方向不穩，一格甩 30°）
            Pup = Vector((sg * pole_out * k, 0.02 * k, -pole_down * k)); Pdn = Vector((sg * 0.20 * k, 0.35 * k, -0.10 * k))
            Pp = S + Pdn.lerp(Pup, a)
            E = elbow(S, W, Pp, L1, L2)
            fa = (W - E).normalized()
            # 手掌方向：立起（往上、微往外），往動作反方向輕微落後；和前臂最多差 wrist_max 度
            want = Vector((sg * (0.12 - 0.22 * du * a), 0.0, 1.0)).normalized()
            want = fa.slerp(want, a) if a < 1.0 else want
            ang_ = fa.angle(want) if fa.length > 0 else 0.0
            lim = math.radians(wrist_max)
            hd = fa.slerp(want, min(1.0, lim / ang_)) if ang_ > lim else want
            ik.append((sd, W, Pp, W + hd * 0.1, "UpperChest"))
            palms.append((sd, (0, -1, 0), a))
            hs[sd] = ("relax", "open", round(a, 3))
            sway += sg * u * a
        if hand != "both":
            P["Spine"].append(("Y", 1.2 * sway)); P["Head"].append(("Y", -0.8 * sway))
        P["Head"].append(("X", -2.0))
        blink = 1.0 if 0.40 < ((tt * 0.6) % 1.0) < 0.43 else 0.0
        return dict(P, hands=(hs["L"], hs["R"]), ik=ik, palms=palms, root=(0, 0, -SOFT_KNEE * BODY_S), feet=PLANT,
                    face={"Fcl_ALL_Fun": smile, "Fcl_EYE_Close": blink})
    fn.dur = dur; fn.period = per; fn.times = dict(raise_=(0.0, raise_t), wave=(raise_t, raise_t + wave_d), lower=None if hold else (raise_t + wave_d, dur))
    fn.wrist = lambda tt, sd=sides[0]: wrist_target(sd, *[phase(tt, sd)[i] for i in (0, 2)])[1]
    return fn


# 格數＝dur × 24：起手 1.0 ＋ 3 個來回 2.0 ＋ 收手 1.0＝4.0 秒＝96 格（循環時從垂手接回垂手）
V12_WAVE_ARC = [("wave_arc", "水平弧形揮手（右手，IK，肩胛跟著抬）", _lazy(lambda: wave_arc("R")), 96),
                ("wave_arc_l", "水平弧形揮手（左手）", _lazy(lambda: wave_arc("L")), 96),
                ("wave_arc2", "水平弧形揮手（雙手）", _lazy(lambda: wave_arc("both")), 96)]


CUSTOM_ACTIONS = [
    # 登記版的出發點偏 −X：預覽鏡頭在 +X 側斜 25°、固定看原點，往 +X 走的人會越走越靠近畫面右緣
    # 預覽畫面只看得到約 1.3 m 寬，所以登記版走得比較短（情境用自己的參數）
    ("walk_fwd", "往前走", walk_fwd(dist=0.9, steps=4, dur=3.0, dirx=1, origin=(-0.55, 0.0)), 72),
    ("pull_walk", "拉著東西往前走", pull_walk(dist1=0.6, steps1=2, walk1=1.2, stuck=0.8, dist2=0.36, steps2=2, walk2=1.0,
                                         start=0.2, end=0.4, dirx=1, origin=(-0.62, 0.0)), 86),
    ("toast", "舉杯乾杯", toast(), 60),
    ("taste", "品嚐美食", taste(), 60),
    # 原地拉繩：往右／往左各一個（同一個工廠，dirx 鏡像）。預覽：往右拉用預設鏡頭（YAW 25），往左拉用鏡像鏡頭（YAW -25）
    ("pull_rope_r", "原地拉繩（往右）", pull_rope(dirx=1), 72),
    ("pull_rope_l", "原地拉繩（往左）", pull_rope(dirx=-1), 72),
]
CUSTOM_ACTIONS += V12_ACTIONS    # 第 6 節：V12 互動動作（第一次用到才建）
CUSTOM_ACTIONS += V12_PASSERBY   # 第 7 節：V12 第 5 幕路人甲（第一次用到才建）
CUSTOM_ACTIONS += V12_WAVES      # 第 8 節：真人揮手（第一次用到才建）
CUSTOM_ACTIONS += V12_HEART      # 第 9 節：頭上比愛心（第一次用到才建）
CUSTOM_ACTIONS += V12_WAVE_ARC   # 第 10 節：水平弧形揮手（第一次用到才建）
