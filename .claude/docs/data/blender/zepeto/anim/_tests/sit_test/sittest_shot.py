# 測試情境（單獨使用，不屬於任何片）：新郎坐在花園餐桌前，右手拿起紅酒杯喝一口、放回桌上（2026-10-12，使用者「抓一幕可以做測試動畫的情境」）。
# 要測的：屁股坐在椅墊上（不浮不陷）、手握細的杯子（每指每節碰到就停）、大頭角色把杯子送到嘴邊（杯緣碰嘴唇、不穿頭）。
# 動作：Mixamo「Sitting Drinking」原樣的 4.5～14.7 秒（坐好之後；前面那段「往前走直接坐下」會從椅背穿過去，不用）。
# 用法（MCP）：
#   # BODY=groom   ← 身體出廠閘門只核對新郎（2026-10-12 起閘門改成只擋點名的身體）
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("_tests", "sit_test"); import sittest_shot as T; print(T.run())   ← 穿西裝版（第 4 版）一次重建
import math, json
import bpy
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree
import zanim_lib as L
import zanim_fix as F
import zanim_hand as R3
import zanim as B
mr = L.mr

CLIP = "sitting_drinking"
T0, T1 = 4.5, 14.7                 # 用原片的這一段（秒）
GLASS_S = 0.806                    # 杯子縮放（和手機一樣，配 ZEPETO 手長 11.4 cm）
# 杯子外形（素材庫 wineglass 的 lathe 剖面，外側輪廓；z 往上、原點在杯底中心）
GLASS_PROF = [(0.0, 0.038), (0.006, 0.040), (0.012, 0.006), (0.090, 0.006), (0.105, 0.030), (0.140, 0.045), (0.190, 0.040)]
CHAIR_SEAT = 0.51                  # 素材庫椅子：椅墊頂（m）
CHAIR_KEY, CHAIR_ZP_SEAT = "chair_zp", 0.19    # 2026-10-12 使用者要 ZEPETO 比例的椅子：chair_zp 椅墊頂 0.19 m，原尺寸用（不縮放）
TABLE_TOP = 0.75                   # 素材庫餐桌：桌面高（m）
TABLE_R = (0.38, 0.465, 0.52)      # 桌面平的半徑、桌緣最外、桌巾落地最外（m，縮放前）
STATE = B.STATE


# ════════ 杯子距離場 ════════
def _r_out(z):
    P = [(z_ * GLASS_S, r_ * GLASS_S) for z_, r_ in GLASS_PROF]
    if z <= P[0][0]:
        return P[0][1]
    for (za, ra), (zb, rb) in zip(P, P[1:]):
        if za <= z <= zb:
            return ra + (rb - ra) * (z - za) / max(1e-9, zb - za)
    return P[-1][1]


def glass_sdf(q):
    """點（杯子座標）到杯子外側的近似距離，負＝在裡面"""
    H = GLASS_PROF[-1][0] * GLASS_S
    rho = Vector((q.x, q.y)).length
    if q.z < 0:
        return math.hypot(max(0.0, rho - _r_out(0)), q.z)
    if q.z > H:
        return math.hypot(max(0.0, rho - _r_out(H)), q.z - H)
    d = rho - _r_out(q.z)
    return max(d, -min(q.z, H - q.z)) if d < 0 else d


# ════════ 通用：手指碰到就停（距離場當參數） ════════
def finger_clear(tgt, R, Hd, side, fn, Mi, rad, sdf, ks=(1, 2, 3)):
    g = 9.9
    for k in ks:
        n = f"J_Bip_{side}_{fn}{k}"
        for p in R3._seg_pts(tgt, R, Hd, n, k):
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


# ════════ 握杯：手骨在杯子座標裡的矩陣 ════════
def grip_local(tgt, P):
    """右手從杯子的 a 方向（水平角 az 度）握杯身：掌心朝杯軸、手指沿杯身水平往前繞（往下傾 tilt 度）、繞手指軸滾 roll 度。
    P：az、zc（握的高度，m，杯子座標）、tilt、roll、gap（掌心皮膚離杯身）"""
    az = math.radians(P["az"])
    a = Vector((math.cos(az), math.sin(az), 0))                     # 杯軸 → 手
    up = Vector((0, 0, 1))
    d = up.cross(a).normalized()                                     # 水平切線（右手：手指繞杯子往前）
    d = (Quaternion(a, math.radians(P.get("tilt", 0.0))) @ d).normalized()
    palm = Quaternion(d, math.radians(P.get("roll", 0.0))) @ (-a)
    q = R3.hand_quat(tgt, "R", d, palm)
    n = "J_Bip_R_Hand"
    hl = (tgt.rest_h["J_Bip_R_Middle1"] - tgt.rest_h[n]).length
    pq = q @ tgt.rest_q[n].inverted()
    dW = pq @ (tgt.rest_h["J_Bip_R_Middle1"] - tgt.rest_h[n]).normalized(); nW = pq @ Vector((0, 0, -1))
    zc = P["zc"]
    c = Vector((0, 0, zc)) + a * (_r_out(zc) + P.get("gap", 0.002))   # 掌心皮膚中心
    wrist = c - nW * 0.012 - dW * (0.55 * hl) + d * P.get("slide", 0.0)
    M = q.to_matrix().to_4x4(); M.translation = wrist
    return M


def eval_grip(tgt, R, h, Mg, rad, P):
    M = Mg @ grip_local(tgt, P)
    R = R3.put_hand(tgt, R, h, "R", M)
    g = mr.GESTURE["fist"]; tc = dict(g["curl"]); tc["Thumb"] = R3.THUMB_FULL
    curls, why = close_fingers(tgt, R, h, "R", Mg, rad, tc, glass_sdf, R3.FINGERS + ("Thumb",))
    for fn in R3.FINGERS:                          # 彎到底都沒碰到的手指用 hold（不要在空中握拳）
        if "碰到" not in why[fn]:
            curls[fn] = mr.GESTURE["hold"]["curl"][fn]; why[fn] = ["懸空"] * 3
    R = mr.finger_pose(tgt, R, "R", curls)
    Hd = tgt.fk(R, h); Mi = Mg.inverted()
    clear = {fn: finger_clear(tgt, R, Hd, "R", fn, Mi, rad, glass_sdf) for fn in R3.FINGERS + ("Thumb",)}
    hand_gap = min(glass_sdf(Mi @ Hd["J_Bip_R_Hand"].lerp(Hd["J_Bip_R_Middle1"], s)) - 0.012 for s in (0.2, 0.5, 0.8))
    return R, dict(curls=curls, why=why, clear=clear, hand_gap=hand_gap,
                   touching=sum(1 for fn in R3.FINGERS if "碰到" in why[fn]), thumb=("碰到" in why["Thumb"]))


def search_grip(tgt, R, h, Mg, rad, grid, base):
    import itertools
    keys = list(grid); best = None
    for vals in itertools.product(*[grid[k] for k in keys]):
        P = dict(base); P.update(dict(zip(keys, vals)))
        _R, r = eval_grip(tgt, R, h, Mg, rad, P)
        mm = lambda v: v * 1000
        s = (4 - r["touching"]) * 6 + (0 if r["thumb"] else 8) + max(0, -mm(r["hand_gap"])) * 5 + max(0, mm(r["hand_gap"]) - 4)
        s += sum(max(0, -mm(c)) for c in r["clear"].values()) * 5
        if best is None or s < best[0]:
            best = (s, P, r)
    return best


# ════════ 嘴巴（頭骨座標） ════════
def mouth_local():
    """嘴唇前緣（頭骨 rest 局部座標）：牙齒外框的前方中心，往前打到頭網格的表面；回傳 (上下唇中間點, 頭骨局部的「前方」)"""
    # 2026-10-12：牙齒的 matrix_world 是「目前姿勢」的，要用頭骨「目前姿勢」的矩陣換算（以前用 rest 的 matrix_local，嘴巴被算到腰）。
    # head_mat()（骨頭世界旋轉＋頭骨位置）和 pose_bone.matrix 是同一套，所以這裡量出來的局部座標每一格都能用
    arm = STATE["arm"]; STATE["sc"].view_layers[0].update()
    Mi = (arm.matrix_world @ arm.pose.bones["J_Bip_C_Head"].matrix).inverted()
    pts = []
    for nm in ("upper_teeth", "bottom_teeth"):
        o = next((c for c in arm.children_recursive if c.name.split(".")[0] == nm), None)
        if o is not None:
            pts += [Mi @ (o.matrix_world @ Vector(c)) for c in o.bound_box]
    c = sum(pts, Vector()) / len(pts)
    tgt = STATE["tgt"]
    fwd = tgt.rest_q["J_Bip_C_Head"].inverted() @ Vector((0, -1, 0)); fwd.normalize()   # 頭骨局部的「前方」（rest 面向 −Y）
    bvh = B._head_bvh()                                                   # 頭網格在頭骨 rest 局部座標（和這裡同一套）
    # 往前一路打到最外層（2026-10-12：只取第一個交點會打到口腔內側，外唇其實還在前面約 1.6 cm）
    lip = None; o = c.copy()
    for _ in range(8):
        hit = bvh.ray_cast(o, fwd)
        if hit[0] is None:
            break
        lip = hit[0]; o = hit[0] + fwd * 0.0005
    lip = lip if lip is not None else c + fwd * 0.02
    return lip, fwd


def head_mat(tgt, R, Hd):
    return Matrix.Translation(Hd["J_Bip_C_Head"]) @ R["J_Bip_C_Head"].to_matrix().to_4x4()


# ════════ 主流程 ════════
def build(P_grip=None, pinch=False, table_h=0.50, table_fwd=0.67, seat_fwd=0.03, t_grab=7.1, t_rel=12.0, sip=(8.3, 10.9), tilt_max=35.0,
          ramp=12, glass_at=None, sip_gap=0.010, elbow=(0.55, -0.8, -0.15), arc_h=0.08, lip_up=0.004):
    tgt = STATE["tgt"]; arm = STATE["arm"]
    C = L._CL[CLIP]; f0, f1 = int(T0 * 30), int(T1 * 30)
    P = [(dict(C["R"][f]), C["hips"][f].copy()) for f in range(f0, f1 + 1)]
    n = len(P)
    # 1. 放到原點：坐好那一格的骨盆水平位置 → (0, 0)
    h0 = P[int(2.0 * 30)][1].copy(); sh = Vector((h0.x, h0.y, 0))
    P = [(R, h - sh) for R, h in P]
    pts = L.sole_points(arm)
    P, off = F.ground(tgt, P, pts)
    # 手指：一律 relaxed（Mixamo 原片的手指套到這副身體會伸直）
    P = [((lambda R: mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"))(R), h) for R, h in P]
    # 腳步修正（防滑）要在手擱大腿之前做：它會挪腿，之後做的話大腿移走、手還留在原地（2026-10-12 穿西裝檢查：手離大腿差到 4 cm）
    P, _li = F.foot_lock(tgt, P, pts, v_on=0.3, ramp=9)
    STATE["sit"] = dict(table=None)
    Rm, hm = P[int(2.0 * 30)]
    fw = (Rm["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0)); fw.z = 0; fw.normalize()
    yaw = math.atan2(fw.y, fw.x) - math.atan2(-1, 0)                # 道具面向 −Y → 轉到角色面向
    # 2. 屁股高度（皮膚網格）→ 椅子縮放
    butt = _butt_low(Rm, hm)
    s_chair = 1.0 if CHAIR_KEY == "chair_zp" else butt / CHAIR_SEAT
    if CHAIR_KEY == "chair_zp":
        butt_seat0 = butt - CHAIR_ZP_SEAT                              # 屁股和椅墊的差（正＝浮）
    s_table = table_h / TABLE_TOP
    hips_xy = Vector((hm.x, hm.y, 0))
    chair = Matrix.LocRotScale(hips_xy + fw * seat_fwd, Quaternion((0, 0, 1), yaw), (s_chair,) * 3)
    table = Matrix.LocRotScale(hips_xy + fw * table_fwd, Quaternion((0, 0, 1), yaw), (s_table,) * 3)
    STATE["sit"] = dict(chair=chair, table=table, s_chair=s_chair, s_table=s_table, fw=fw, butt=butt, table_h=table_h, yaw=yaw)
    # 兩手沒拿東西時擱在大腿上（2026-10-12：原片的手擱在一張比較低、比較近的桌子上，套過來會插進桌巾；
    # 我們的桌子為了讓開高膝蓋只能放遠，短手搆不到桌面）。右手拿杯子那段由下面的 IK 蓋過去
    P_raw = list(P)                                                   # 杯子的搬運路徑照原片的右手（拿起、舉到嘴邊、放下）
    P, li_L = left_hand_fix(tgt, P, rest_z=0.0, side="L")
    P, li_R = left_hand_fix(tgt, P, rest_z=0.0, side="R")
    STATE["left_fix"] = dict(L=li_L, R=li_R)
    # 3. 杯子：握法在拿起那一格解；杯子放的位置＝那一格 Mixamo 手的前方、桌面上（離桌緣至少 4 cm）
    ig, ir = int((t_grab - T0) * 30), int((t_rel - T0) * 30)
    rad = R3.finger_radius(arm, L.body_mesh(arm), "R")
    P_grip = P_grip or dict(az=-150.0, zc=0.105, tilt=0.0, roll=0.0, gap=0.002)

    def table_spot(hand_pt, extra=0.0):
        tc = table.translation.copy(); tr = TABLE_R[0] * s_table - 0.045 - extra
        v = Vector((hand_pt.x - tc.x, hand_pt.y - tc.y, 0))
        if v.length > tr:
            v = v.normalized() * tr
        return Matrix.LocRotScale(Vector((tc.x + v.x, tc.y + v.y, table_h)), Quaternion((0, 0, 1), yaw), (1, 1, 1))

    Rg, hg = P_raw[ig]; Hd = tgt.fk(Rg, hg)
    G1 = glass_at or table_spot(Hd["J_Bip_R_Middle1"])
    Rr, hr = P_raw[ir]; Hd = tgt.fk(Rr, hr)
    G2 = table_spot(Hd["J_Bip_R_Middle1"] - fw * 0.03)
    if pinch:
        Rgr, rep = eval_pinch(tgt, P[ig][0], P[ig][1], G1, rad, P_grip)
    else:
        Rgr, rep = eval_grip(tgt, Rg, hg, G1, rad, P_grip)
    curls = rep["curls"]
    # 手指（含拇指）相對手骨的旋轉：手相對杯子不動，所以拿起那一格解出來的每一格都能用
    Hn = "J_Bip_R_Hand"
    floc = {n: Rgr[Hn].inverted() @ Rgr[n] for n in Rgr if n.startswith("J_Bip_R_") and any(f in n for f in R3.FINGERS + ("Thumb",))}
    offG = grip_local(tgt, P_grip)                                    # 手骨在杯子座標（杯子 = 手 @ offG⁻¹）
    # 4. 喝：杯緣碰下唇、杯子往臉傾
    lip_l, fwd_l = mouth_local()
    up_l = tgt.rest_q["J_Bip_C_Head"].inverted() @ Vector((0, 0, 1))    # 頭骨局部的「上方」
    a0, a1 = int((sip[0] - T0) * 30), int((sip[1] - T0) * 30)
    H = GLASS_PROF[-1][0] * GLASS_S; rim = GLASS_PROF[-1][1] * GLASS_S

    def standoff_at(th):
        return 0.065 * (1 - th / math.radians(tilt_max)) if tilt_max > 0 else 0.0

    def sip_glass(R, h, th):
        Hd = tgt.fk(R, h); Mh = head_mat(tgt, R, Hd)
        # 杯緣對準嘴縫往上 lip_up（2026-10-12：對下唇時杯緣下緣會碰到大頭角色凸出的下巴）；頭骨局部的 z 不是上方
        lip = Mh @ lip_l + (Mh.to_3x3() @ up_l) * lip_up
        f = Mh.to_3x3() @ fwd_l; f.z = 0; f.normalize()                # 臉的前方（水平）
        to_face = -f
        zax = (Vector((0, 0, 1)) * math.cos(th) + to_face * math.sin(th)).normalized()
        xax = to_face.cross(Vector((0, 0, 1))).normalized()            # 傾斜軸
        yax = zax.cross(xax).normalized()
        towards = (to_face - zax * to_face.dot(zax)).normalized()      # 杯口平面裡朝臉的方向
        # 杯緣只在喝的中段貼嘴唇；開始和結束時離嘴 standoff（杯子直立貼嘴時杯身會頂到大頭的下巴，2026-10-12 量到穿 13 mm）
        contact = lip + f * (sip_gap + standoff_at(th))
        origin = contact - towards * rim - zax * H
        M = Matrix((xax, yax, zax)).transposed().to_4x4(); M.translation = origin
        return M

    def sm(x):
        return mr._smooth(max(0.0, min(1.0, x)))
    out = []; glass = []; info_w = []
    right_v = fw.cross(Vector((0, 0, 1))).normalized()
    Graw = [None] * n
    for i in range(n):
        R, h = P_raw[i]; Hd = tgt.fk(R, h)
        Graw[i] = R3.hand_mat(tgt, R, Hd, "R") @ offG.inverted()
    # 搬運段的修正：拿起那格對齊 G1、放下那格對齊 G2，中間平滑過渡（位置＋旋轉）
    q1 = G1.to_quaternion() @ Graw[ig].to_quaternion().inverted(); t1 = G1.translation - Graw[ig].translation
    q2 = G2.to_quaternion() @ Graw[ir].to_quaternion().inverted(); t2 = G2.translation - Graw[ir].translation
    for i in range(n):
        R, h = P[i]
        if i < ig - ramp or i > ir + ramp:
            w = 0.0
        elif i < ig:
            w = sm((i - (ig - ramp)) / ramp)
        elif i > ir:
            w = sm(1 - (i - ir) / ramp)
        else:
            w = 1.0
        if i <= ig:
            Gi = G1
        elif i >= ir:
            Gi = G2
        else:
            u = sm((i - ig) / (ir - ig))
            q = q1.slerp(q2, u); t = t1.lerp(t2, u)
            gr = Graw[i]
            Gi = Matrix.LocRotScale(gr.translation + t, q @ gr.to_quaternion(), (1, 1, 1))
            ws = 0.0
            if a0 - ramp <= i <= a1 + ramp:
                ws = sm((i - (a0 - ramp)) / ramp) if i < a0 else (sm(1 - (i - a1) / ramp) if i > a1 else 1.0)
            if ws > 0:
                k = (i - a0) / max(1, a1 - a0)
                th = math.radians(tilt_max) * (math.sin(math.pi * max(0.0, min(1.0, k))) if 0 <= k <= 1 else 0.0)
                Gs = sip_glass(R, h, th)
                Gi = Matrix.LocRotScale(Gi.translation.lerp(Gs.translation, ws), Gi.to_quaternion().slerp(Gs.to_quaternion(), ws), (1, 1, 1))
        # 手：照杯子放（拿起前、放下後漸入漸出）
        if w > 0:
            # 喝的那段手肘往下、往外（使用者 2026-10-12：照原片手肘抬很高「不太自然」）。elbow＝(往右, 往上, 往前) 的 pole 方向
            pw = 0.0
            if a0 - ramp <= i <= a1 + ramp:
                pw = sm((i - (a0 - ramp)) / ramp) if i < a0 else (sm(1 - (i - a1) / ramp) if i > a1 else 1.0)
            pole_sip = (right_v * elbow[0] + Vector((0, 0, elbow[1])) + fw * elbow[2]).normalized()
            # 從大腿伸到桌上（或收回）時手往上繞一個弧，越過桌緣（直線過去會讓無名指、小指擦進桌巾）
            Mt = Gi @ offG
            if 0 < w < 1:
                Mt = Matrix.Translation(Vector((0, 0, arc_h * math.sin(math.pi * w)))) @ Mt
            R = put_hand_pole(tgt, R, h, "R", Mt, w, pole_sip, pw)
            R = dict(R)
            for n_, lq in floc.items():
                R[n_] = R[n_].slerp(R[Hn] @ lq, w) if w < 1 else R[Hn] @ lq
        out.append((R, h)); glass.append(Gi); info_w.append(w)
    linfo = STATE.get("left_fix")
    STATE["left_fix"] = linfo
    STATE.update(poses=out, glass=glass, sit_w=info_w, sit_grip=rep, sit_P=P_grip, sit_idx=(ig, ir, a0, a1), offG=offG)
    return dict(n=n, chair_scale=round(s_chair, 3), table_scale=round(s_table, 3), butt_mm=round(1000 * butt, 1),
                grip=dict(curls=curls, why=rep["why"], clear_mm={k: round(1000 * v, 1) for k, v in rep["clear"].items()},
                          hand_gap_mm=round(1000 * rep["hand_gap"], 1)),
                ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)))


def thigh_spot(tgt, R, h, at=0.7, side="L"):
    """左大腿上面（皮膚表面）靠膝蓋那一點：大腿骨 at 處，往上找皮膚（大腿半徑在第一次呼叫時從網格量）"""
    Hd = tgt.fk(R, h)
    p = Hd[f"J_Bip_{side}_UpperLeg"].lerp(Hd[f"J_Bip_{side}_LowerLeg"], at)
    if ("thigh_r", side) not in STATE:
        arm = STATE["arm"]; body = L.body_mesh(arm); vl = STATE["sc"].view_layers[0]
        mr.apply_pose(arm, tgt, R, h); vl.update()
        oe = body.evaluated_get(vl.depsgraph); me = oe.to_mesh(); M = body.matrix_world
        gi = {g.name: g.index for g in body.vertex_groups}; ul = gi[f"J_Bip_{side}_UpperLeg"]
        zs = [q.z for v, q in ((v, M @ me.vertices[v.index].co) for v in body.data.vertices)
              if any(g.group == ul and g.weight > 0.5 for g in v.groups) and Vector((q.x - p.x, q.y - p.y)).length < 0.015 and q.z > p.z]
        oe.to_mesh_clear()
        r = (max(zs) - p.z) if zs else 0.05
        pants = STATE["sc"].objects.get("Suit_Pants")             # 穿了西裝：手擱在褲子上面，不是皮膚上（2026-10-12 穿西裝檢查，右手整隻陷進褲子）
        if pants is not None:
            oe = pants.evaluated_get(vl.depsgraph); me = oe.to_mesh(); M = pants.matrix_world
            zs = [q.z for q in (M @ v.co for v in me.vertices) if Vector((q.x - p.x, q.y - p.y)).length < 0.015 and q.z > p.z]
            oe.to_mesh_clear()
            if zs:
                r = max(r, max(zs) - p.z)
        STATE[("thigh_r", side)] = r
    return p + Vector((0, 0, STATE[("thigh_r", side)] + 0.002))


def left_hand_fix(tgt, P, rest_z=0.40, inset=0.04, margin=0.006, smooth=8, side="L"):
    """左手不穿進桌巾（2026-10-12：Mixamo 原片的左手擱在一張比較低、比較近的桌子上，套過來整隻插進桌巾 13 cm）。
    原片左手掌心高於 rest_z 的格子＝擱在桌上 → 抬到我們的桌面（掌心皮膚貼桌面、離桌緣至少 inset）；
    其他格子 → 只往外推到離桌巾 margin。位移前後 smooth 格平均，手臂 IK、手掌朝向照原片；擱桌的格子手指往 relaxed 彎、碰到桌面就停"""
    import zanim_pose as R2
    S_ = STATE["sit"]; tc = S_["table"].translation; top = S_["table_h"]; r_top = TABLE_R[0] * S_["s_table"] - inset
    n = len(P); offs = []; resting = []; cs = []; spots = []
    for R, h in P:
        Hd = tgt.fk(R, h); c, nrm, d = R2.palm_info(tgt, R, Hd, side)
        cs.append(c); spots.append(thigh_spot(tgt, R, h, side=side))
        pts = [Hd[f"J_Bip_{side}_Hand"], c] + [tgt.tail(R, Hd, f"J_Bip_{side}_{f}3") for f in ("Index", "Middle", "Ring", "Little", "Thumb")] + [Hd[f"J_Bip_{side}_LowerArm"].lerp(Hd[f"J_Bip_{side}_Hand"], 0.6)]
        if c.z > rest_z:
            # 2026-10-12：擱桌面搆不到（桌子為了讓開高膝蓋只能放遠，左臂要完全打直 48 cm 才到）→ 改擱在左大腿上、靠膝蓋那一段
            offs.append(Vector()); resting.append(1.0)
        else:
            need = 0.0; out_dir = None
            for p in pts:
                dd = table_sdf(p) - 0.012 - margin
                if dd < need:
                    need = dd; out_dir = Vector((p.x - tc.x, p.y - tc.y, 0)).normalized()
            offs.append(out_dir * (-need) if out_dir is not None else Vector()); resting.append(0.0)
    so = []; sr = []
    for i in range(n):
        js = range(max(0, i - smooth), min(n, i + smooth + 1))
        sr_i = sum(resting[j] for j in js) / len(js)
        # 擱大腿：平滑的是「大腿上那一點」，手直接放過去（2026-10-12 穿西裝檢查：原本平滑的是位移量，
        # 原片的手在桌上比劃，殘差讓擱在大腿上的手前後滑最多 4.7 cm／2 格，還會插進大腿）
        rest_off = spots[i] - cs[i]                           # 大腿上那一點本來就跟著腿連續動，不用平滑（平滑會落後腿）
        tab_off = sum((offs[j] for j in js), Vector()) / len(js)
        so.append(rest_off * sr_i + tab_off * (1 - sr_i)); sr.append(sr_i)
    out = []; plane = lambda q: q.z - top                      # 桌面（世界座標）的距離場
    rad = R3.finger_radius(STATE["arm"], L.body_mesh(STATE["arm"]), side)
    for i, (R, h) in enumerate(P):
        if so[i].length < 1e-4:
            out.append((R, h)); continue
        Hd = tgt.fk(R, h); n_ = f"J_Bip_{side}_Hand"
        q = R[n_] @ tgt.rest_q[n_].inverted()
        d = (Hd[f"J_Bip_{side}_Middle1"] - Hd[n_]).normalized(); palm = q @ Vector((0, 0, -1))
        if sr[i] > 0:                                           # 擱大腿：掌心朝下、手指沿大腿往膝蓋
            th = (Hd[f"J_Bip_{side}_LowerLeg"] - Hd[f"J_Bip_{side}_UpperLeg"]); th.z = 0; th.normalize()
            palm = palm.lerp(Vector((0, 0, -1)), sr[i]).normalized(); d = d.lerp(th, sr[i]).normalized()
        pole = Hd[f"J_Bip_{side}_LowerArm"] - (Hd[f"J_Bip_{side}_UpperArm"] + Hd[n_]) / 2
        pole = pole if pole.length > 1e-4 else Vector((0, 0, -1))
        R0 = R; wrist = Hd[n_] + so[i]; goal = cs[i] + so[i]       # goal＝掌心該到的點
        for _k in range(3 if sr[i] > 0 else 1):
            # 手掌轉向是繞手腕轉，掌心會跟著跑掉（2026-10-12 量到差 3～5 cm）→ 量掌心實際位置，把手腕補過去再解一次
            R = mr.arm_ik(tgt, R0, h, side, wrist, pole)
            R = mr.aim_hand(tgt, R, h, side, d, palm=palm, palm_w=1.0, max_bend=None)
            if sr[i] > 0:
                R = mr.gesture(tgt, R, side, "cup", sr[i])        # 手掌貼著大腿的弧度（共用手勢 cup）
                c2 = R2.palm_info(tgt, R, tgt.fk(R, h), side)[0]
                wrist = wrist + (goal - c2) * sr[i]
        out.append((R, h))
    return out, dict(resting_s=round(sum(1 for r in resting if r > 0) / 30, 2), max_shift_mm=round(1000 * max(o.length for o in so), 1))


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


def _butt_low(R, h):
    """坐姿時屁股最低點（皮膚網格，骨盆正下方 12 cm 內）"""
    arm = STATE["arm"]; tgt = STATE["tgt"]; body = L.body_mesh(arm)
    mr.apply_pose(arm, tgt, R, h); vl = STATE["sc"].view_layers[0]; vl.update()
    Hd = tgt.fk(R, h); hw = arm.matrix_world @ Hd["J_Bip_C_Hips"]
    oe = body.evaluated_get(vl.depsgraph); me = oe.to_mesh(); M = body.matrix_world
    zs = [p.z for p in (M @ v.co for v in me.vertices) if Vector((p.x - hw.x, p.y - hw.y)).length < 0.12 and p.z < hw.z]
    oe.to_mesh_clear()
    return min(zs)


# ════════ 場景物件 ════════
def props():
    g = {"__file__": r"D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/props-zepeto/use_props.py"}
    exec(open(g["__file__"], encoding="utf8").read(), g)
    col = bpy.data.collections["B12_studio"]
    for key, name in ((CHAIR_KEY, "SIT_Chair"), ("table", "SIT_Table"), ("wineglass", "SIT_Glass")):
        if name not in bpy.data.objects:
            g["place_prop"](key, name=name, parent=col)
    S = STATE["sit"]; arm = STATE["arm"]
    bpy.data.objects["SIT_Chair"].matrix_world = arm.matrix_world @ S["chair"]
    bpy.data.objects["SIT_Table"].matrix_world = arm.matrix_world @ S["table"]


def pose_at(t):
    i = max(0, min(len(STATE["poses"]) - 1, int(round(t * 30))))
    R, h = STATE["poses"][i]
    mr.apply_pose(STATE["arm"], STATE["tgt"], R, h)
    o = bpy.data.objects.get("SIT_Glass")
    if o is not None:
        o.matrix_world = STATE["arm"].matrix_world @ STATE["glass"][i] @ Matrix.Diagonal((GLASS_S, GLASS_S, GLASS_S, 1.0))
    STATE["sc"].view_layers[0].update()
    return i


def shots(times, focus="J_Bip_C_Chest", dist=1.2, out=r"D:/render-work/zepeto-anim/sit/close", views=None, dz=0.0, lens=50, at=None):
    """at＝對準的世界座標（給了就不用 focus 骨頭）"""
    import os
    sc = STATE["sc"]; cam = sc.camera
    views = views or [("main", 0), ("front", 90), ("side", 35)]
    os.makedirs(out, exist_ok=True); sc.render.image_settings.file_format = "JPEG"
    done = []
    for t in times:
        i = pose_at(t)
        c = (at(i) if callable(at) else B.bone_world(focus)) + Vector((0, 0, dz))
        for name, az in views:
            if isinstance(az, tuple):
                loc = c + Vector(az)
            else:
                r = math.radians(az); loc = c + Vector((math.sin(r) * dist, -math.cos(r) * dist, 0.25 * dist))
            B._aim(cam, loc, c, lens)
            sc.render.filepath = os.path.join(out, "%05.2f_%s.jpg" % (t, name))
            with bpy.context.temp_override(**B._ctx(sc)):
                bpy.ops.render.render(write_still=True, scene=sc.name)
            done.append(sc.render.filepath)
    return len(done)


# ════════ 檢查數字 ════════
TABLE_PROF = [(0.0, 0.75), (0.38, 0.75), (0.43, 0.742), (0.455, 0.715), (0.465, 0.66), (0.48, 0.4), (0.5, 0.12), (0.52, 0.02), (0.51, 0.0)]


def table_sdf(p):
    """點（世界）到餐桌（含落地桌巾）的近似距離：只看水平方向（桌巾外側），負＝在桌子裡面"""
    S_ = STATE["sit"]; Mi = S_["table"].inverted(); q = Mi @ p; s = S_["s_table"]
    z = q.z
    if z < 0 or z > 0.75:
        return 9.9
    prof = sorted(TABLE_PROF[1:], key=lambda a: a[1])
    r = prof[-1][0]
    for (ra, za), (rb, zb) in zip(prof, prof[1:]):
        if za <= z <= zb:
            r = ra + (rb - ra) * (z - za) / max(1e-9, zb - za); break
    rho = Vector((q.x, q.y)).length
    if rho >= r:
        return (rho - r) * s
    return -min(r - rho, 0.75 - z) * s                    # 在裡面：離側面或離桌面，取近的那個（擱在桌面上的手只算陷進桌面多深）


def checks(step=3):
    """皮膚網格逐格量（每 step 格）：手指／手掌離杯子、身體離桌巾、屁股離椅墊；杯子（取樣點）離頭、杯緣離下唇；滑步"""
    import time
    t0 = time.time()
    arm = STATE["arm"]; tgt = STATE["tgt"]; body = L.body_mesh(arm); vl = STATE["sc"].view_layers[0]
    if "hand_vids" not in STATE:
        gi = {g.index: g.name for g in body.vertex_groups}; vids = {}
        for v in body.data.vertices:
            for g in v.groups:
                nm = gi.get(g.group, "")
                if g.weight > 0.3 and nm.startswith("J_Bip_") and ("Hand" in nm or any(f in nm for f in R3.FINGERS + ("Thumb",))):
                    side = nm.split("_")[2]; part = "palm" if nm.endswith("Hand") else ("thumb" if "Thumb" in nm else "finger")
                    vids.setdefault((side, part), set()).add(v.index)
        STATE["hand_vids"] = {k: sorted(s) for k, s in vids.items()}
    vids = STATE["hand_vids"]
    S_ = STATE["sit"]; seat_top = CHAIR_ZP_SEAT if CHAIR_KEY == "chair_zp" else S_["butt"]
    ig, ir, a0, a1 = STATE["sit_idx"]
    bvh = B._head_bvh(); lip_l, fwd_l = mouth_local()
    up_l = tgt.rest_q["J_Bip_C_Head"].inverted() @ Vector((0, 0, 1))
    H = GLASS_PROF[-1][0] * GLASS_S
    ring = []
    for z_, r_ in GLASS_PROF[1:]:
        for k in range(16):
            a = 2 * math.pi * k / 16
            ring.append(Vector((r_ * GLASS_S * math.cos(a), r_ * GLASS_S * math.sin(a), z_ * GLASS_S)))
    worst = {}; rows = {}
    n = len(STATE["poses"])
    frames = sorted(set(list(range(0, n, step)) + list(range(a0, a1 + 1)) + [ig, ir]))
    for i in frames:
        R, h = STATE["poses"][i]; Hd = tgt.fk(R, h); G = STATE["glass"][i]; Gi = G.inverted()
        row = {}
        # 杯子離頭（頭網格在頭骨局部）
        Mh = head_mat(tgt, R, Hd); Mhi = Mh.inverted(); dmin = 9.9
        for p in ring:
            ins, d = B._inside(bvh, Mhi @ (G @ p))
            dmin = min(dmin, -d if ins else d)
        row["glass_head"] = dmin
        if a0 <= i <= a1:
            # 杯緣離下唇：下唇到「杯口那一圈」最近的距離
            lip = Mh @ lip_l - (Mh.to_3x3() @ up_l) * 0.006
            rim = [G @ p for p in ring if abs(p.z - H) < 1e-6]
            row["rim_lip"] = min((q - lip).length for q in rim)
        if i % step == 0 or i in (ig, ir):
            pose_at(i / 30)
            oe = body.evaluated_get(vl.depsgraph); me = oe.to_mesh(); M = body.matrix_world
            V = [M @ v.co for v in me.vertices]
            oe.to_mesh_clear()
            if ig <= i <= ir:
                for part in ("finger", "thumb", "palm"):
                    row["R_" + part + "_glass"] = min(glass_sdf(Gi @ V[k]) for k in vids[("R", part)])
            row["body_table"] = min(table_sdf(V[k]) for k in range(0, len(V), 3))
            hw = Hd["J_Bip_C_Hips"]
            seat = [V[k].z for k in range(0, len(V), 2) if Vector((V[k].x - hw.x, V[k].y - hw.y)).length < 0.12 and V[k].z < hw.z]
            row["butt_seat"] = min(seat) - seat_top
        rows[i] = row
        for k_, v_ in row.items():
            if k_ not in worst or v_ < worst[k_][0]:
                worst[k_] = (v_, i)
    STATE["sit_rows"] = rows
    pts = L.sole_points(arm); cs = L.contact_stats(STATE["poses"], tgt, pts)
    sl = [(r_["slide" + s], r_["i"]) for r_ in cs for s in "LR" if r_["slide" + s] is not None]
    lows = [min(r_["lowL"], r_["lowR"]) for r_ in cs]
    out = {k_: (round(1000 * v_, 1), round(i_ / 30, 2)) for k_, (v_, i_) in worst.items()}
    out["slide_max_mm"] = round(max(sl)[0], 1) if sl else 0.0
    out["sole_low_mm"] = (round(1000 * min(lows), 1), round(1000 * max(lows), 1))
    # 屁股離椅墊：最大值也要看（浮起來）
    bs = [r_["butt_seat"] for r_ in rows.values() if "butt_seat" in r_]
    out["butt_seat_range_mm"] = (round(1000 * min(bs), 1), round(1000 * max(bs), 1))
    out["sec"] = round(time.time() - t0, 1)
    return out


# ════════ 捏杯腳（使用者 2026-10-12 選的握法） ════════
# 網路上的標準拿法：拇指和食指捏住杯腳下半段，中指從後面扶著，無名指、小指輕輕彎著（不碰杯身，保持杯身乾淨、不讓手溫熱到酒）。
# 第 1、2 版是握杯身：拇指翹在杯口上方 6.7 mm、往外伸 6.7 cm（使用者「大拇指位置不正確」）
STEM_R = 0.006 * GLASS_S
STEM_Z = (0.012 * GLASS_S, 0.090 * GLASS_S)


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
    g = min(sdf(Mi @ p_) - rad[n3] for p_ in R3._seg_pts(tgt, Rb, Hd, n3, 3))
    return Rb, g, ang


def eval_pinch(tgt, R, h, Mg, rad, P):
    """捏杯腳：手照 P 放（P 同 grip_local，zc＝捏的高度、gap＝掌心離杯腳）→ 食指、中指往 fist 彎、碰到就停 →
    無名指、小指用 relaxed（碰到杯底就停）→ 拇指指腹點到杯腳另一側（和食指指腹相對）"""
    M = Mg @ grip_local(tgt, P)
    R = R3.put_hand(tgt, R, h, "R", M)
    fist = mr.GESTURE["fist"]["curl"]; relaxed = mr.GESTURE["relaxed"]["curl"]
    hold = mr.GESTURE["hold"]["curl"]
    # 參考（網路標準拿法）：無名指、小指收起來、輕靠在杯底座 → 往 hold 彎、碰到杯底座就停（第 3 版用 relaxed 會往外張開）
    tc = {"Index": fist["Index"], "Middle": fist["Middle"], "Ring": hold["Ring"], "Little": hold["Little"]}
    curls, why = close_fingers(tgt, R, h, "R", Mg, rad, tc, glass_sdf, R3.FINGERS)
    R = mr.finger_pose(tgt, R, "R", curls)
    Hd = tgt.fk(R, h); Mi = Mg.inverted()
    # 食指指腹（第 3 節）在杯腳哪一邊、哪個高度 → 拇指放對面
    ip = Mi @ Hd["J_Bip_R_Index3"].lerp(tgt.tail(R, Hd, "J_Bip_R_Index3"), 0.5)
    side_v = Vector((ip.x, ip.y, 0))
    if side_v.length < 1e-6:
        side_v = Vector((1, 0, 0))
    goal = -side_v.normalized() * STEM_R + Vector((0, 0, min(max(ip.z, STEM_Z[0] + 0.004), STEM_Z[1] - 0.004)))
    R, tg, ang = thumb_to(tgt, R, h, "R", Mg, rad, goal, glass_sdf)
    Hd = tgt.fk(R, h)
    clear = {fn: finger_clear(tgt, R, Hd, "R", fn, Mi, rad, glass_sdf) for fn in R3.FINGERS + ("Thumb",)}
    hand_gap = min(glass_sdf(Mi @ Hd["J_Bip_R_Hand"].lerp(Hd["J_Bip_R_Middle1"], s)) - 0.012 for s in (0.2, 0.5, 0.8))
    ip2 = Mi @ Hd["J_Bip_R_Index3"].lerp(tgt.tail(R, Hd, "J_Bip_R_Index3"), 0.5)
    tp = Mi @ Hd["J_Bip_R_Thumb3"].lerp(tgt.tail(R, Hd, "J_Bip_R_Thumb3"), 0.7)
    oppose = math.degrees(Vector((ip2.x, ip2.y, 0)).angle(Vector((tp.x, tp.y, 0)), 0.0)) if Vector((tp.x, tp.y)).length > 1e-6 else 0.0
    return R, dict(curls=curls, why=why, clear=clear, hand_gap=hand_gap, thumb_gap=tg, thumb_rot=ang,
                   index_z=ip2.z, thumb_z=tp.z, oppose_deg=oppose,
                   idx_touch="碰到" in why["Index"], mid_touch="碰到" in why["Middle"])


def search_pinch(tgt, R, h, Mg, rad, grid, base, z_pref=0.035):
    import itertools
    keys = list(grid); best = None; mm = lambda v: v * 1000
    for vals in itertools.product(*[grid[k] for k in keys]):
        P = dict(base); P.update(dict(zip(keys, vals)))
        _R, r = eval_pinch(tgt, R, h, Mg, rad, P)
        s = (0 if r["idx_touch"] else 20) + (0 if r["mid_touch"] else 4)
        s += abs(mm(r["thumb_gap"])) * 2 + max(0, 160 - r["oppose_deg"]) * 0.2           # 拇指要和食指隔著杯腳相對（接近 180°）
        s += abs(mm(r["thumb_z"] - r["index_z"])) * 0.3                                  # 同高度
        s += sum(max(0, -mm(c)) for c in r["clear"].values()) * 5 + max(0, -mm(r["hand_gap"])) * 5
        s += max(0, r["thumb_rot"] - 40) * 0.2                                           # 拇指整根不要轉太多
        s += abs(mm(r["index_z"] - z_pref)) * 0.15                                        # 捏在杯腳下半段（網路標準拿法）
        if best is None or s < best[0]:
            best = (s, P, r)
    return best


# ════════ 穿西裝版（第 4 版，2026-10-12）＋工作流入口 ════════
# 由 t_sit_suit 搬來：衣服改用共用的 zanim_dress（一開始就穿）；椅子往後挪 7.2 cm（seat_fwd 0.03 → −0.042）：
# 原片一開始人往後靠，背會穿過椅背（沒穿西裝也穿 10～25 mm）
import zanim_dress as DR
import zanim_sample as SP
OUTFIT = "groom-beige-3piece"
BUILD = dict(pinch=True, sip=(7.6, 11.0), tilt_max=25.0, arc_h=0.16, seat_fwd=-0.042)
PINCH_P3 = dict(az=160.0, zc=0.04, gap=0.03, tilt=10.0, roll=0.0)
SCENE, PREFIX = "SIT_WORK", "B12_"     # 攝影棚名稱沿用搬家前（props() 認 B12_studio）


def _glass_hook(i):
    """zanim.pose_at 的 hook：杯子跟著這一格"""
    o = bpy.data.objects.get("SIT_Glass")
    if o is not None and "glass" in STATE:
        o.matrix_world = STATE["arm"].matrix_world @ STATE["glass"][i] @ Matrix.Diagonal((GLASS_S, GLASS_S, GLASS_S, 1.0))


def run(dress=True):
    """一次重建：場景＋角色 → 讀 Mixamo → 穿西裝 → build → 道具。約 15～30 秒"""
    import time
    t0 = time.time()
    B.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = B.use_shot("_tests", "sit_test")[1]
    B.load_clips((CLIP,))
    if dress:
        DR.dress(OUTFIT)
    for s in "LR":
        STATE.pop(("thigh_r", s), None)
    with DR.no_mask():
        r = build(P_grip=dict(PINCH_P3), **BUILD)
    props()
    B.POSE_HOOKS.append(_glass_hook)
    return dict(sec=round(time.time() - t0, 1), ground_mm=r["ground_mm"], grip_clear_mm=r["grip"]["clear_mm"])


def body_checks(step=3):
    """皮膚網格的檢查（手指離杯、杯緣離嘴、身體離桌巾、屁股離椅墊、滑步）"""
    with DR.no_mask():
        return checks(step)


def outfit_checks(step=6):
    """衣服穿進椅子多深（正＝穿進去；椅墊被屁股壓住的那一角幾 mm 算正常）、離桌巾多遠（正＝在外面）。
    桌巾是下面開口的筒子，用法線判斷會把桌巾下的鞋子誤判成在裡面 → 桌子改用這一鏡的距離場 table_sdf"""
    out = DR.outfit_vs_props({"chair": bpy.data.objects["SIT_Chair"]}, step=step)
    sc = STATE["sc"]; dg = sc.view_layers[0].depsgraph; worst = {}
    for i in range(0, len(STATE["poses"]), step):
        B.pose_at(i / 30)
        for n in ("Suit_Jacket", "Suit_Pants", "Suit_Shoes"):
            V, _ = DR.world_verts(sc.objects[n], dg)
            d = min(table_sdf(p) for p in V[::3])
            if n not in worst or d < worst[n][0]:
                worst[n] = (d, i)
    out.update({f"{n}↔桌巾": (round(1000 * d, 1), round(i / 30, 2)) for n, (d, i) in worst.items()})
    return out


def sample():
    """存樣張、登記總表（樣張鏡頭：斜前方 113°，看得到臉、拿杯的手、桌面、椅子）"""
    arm = STATE["arm"]
    SP.new_camera("SAMPLE_Cam", 35.0)
    pose_at(4.0)
    c = arm.matrix_world @ arm.pose.bones["J_Bip_C_Hips"].head + Vector((0, 0, 0.34))
    r = math.radians(113); loc = c + Vector((math.sin(r) * 1.95, -math.cos(r) * 1.95, 0.25 * 1.95))
    out = SP.bake(objects=[bpy.data.objects["SIT_Glass"]], camera_fn=lambda i: (loc, c))
    STATE["sc"]["sample_focus_dist"] = (c + Vector((0, 0, 0.35)) - loc).length
    path = SP.save("sit_test")
    reg = SP.register("sit_test", "坐餐桌喝紅酒（測試）", None, path,
                      [(2.6, "拿起杯子"), (5.1, "喝（臉、杯子）"), (7.7, "手快速收回（動得快，看動態模糊）"), (9.5, "手擱大腿（靜態）")],
                      note="測試情境，不是正式分鏡；新郎穿米色三件式", kind="test")
    return dict(out, path=path, reg=reg)


def cleanup():
    return B.cleanup(SCENE)
