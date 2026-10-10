# 情境版 ③ v2_03「愛情里程碑」與 ⑧ v2_08 中段（拱門下 wave2／heart）（2026-10-09 快速預覽）。
# 依據：規劃表 plan-2 V12-03／V12-08、opening-v12-production.md「第二版修改」；③ 的時間以主控端轉達的使用者定案為準：
#   全長 7.74 秒；0～2.0 新郎扛緞帶快走（0→99%）、2.0～3.05 卡在 99%（停步、更往前傾、用力扯，把手在「婚禮」前顫動）、
#   3.05 到 100%（「婚禮」亮起擴散光環、花瓣雨）→ 新郎走到新娘身邊，兩人並肩對鏡頭（新郎 wave2；新娘 0～3.05 cheer、3.05～5.05 clap、之後 cheer）。
# 載入：在 run_prod（MODE 給不認識的值＝只載入）之後 use("shots_v2_s0308")；要用 shots_v2 的 Actor2、postured、_posture_R、_runs。
#
# 新郎的身體動作＝真人動作捕捉接起來（fast-iteration.md §0「先套成熟的骨骼動作」）：
#   ① CMU 35_01「walk」正常走路（快走）→ ② CMU 16_33「slow walk, stop」最後一步（右腳支撐期接進來，急停、併腳；和 ② 幕同一份資料）
#   → 站著卡住（停在 16_33 最後一格；上身加前傾、膝蓋多彎、雙手往前下一扯＝情境加的拉扯姿勢）
#   → ③ CMU 82_08「stand still; casual walk forward」從站著起步 → ④ 再接 16_33 的最後一步，停在新娘身邊。
#   走路 ↔ 停步在「同一隻腳剛踩下」的支撐期對齊那隻腳的腳踝、交叉淡入 0.2 秒（做法同 shots_v2.mocap_walk_stop）；
#   站著 ↔ 站著（② 的結尾 ↔ ③ 的開頭）對齊兩腳中點、淡入 0.3 秒。接好的整段一起鎖腳貼地、男性骨盆修正、最後站定時膝蓋拉直。
#   試過沒用的來源：CMU 81_07／81_08「pull／drag heavy object」是面向重物倒退走（方向相反）；18_03「A pulls B」身體側對前進方向、
#   回頭看被拉的人（接進來時每格轉到 53°，扭正又會變成橫著走）。
#   手臂不用真人資料：雙手換成動作庫 pull_walk 扛緞帶的 IK（緞帶扛左肩、拳頭跟著 UpperChest）；上身另外加前傾（拉東西的必要姿勢，
#   35_01 本身是直立走路）。真人資料的時間不拉長不壓縮：情境配合它——片段從走路中途開始（t=0 時已經在走）、停下那一刻＝99%、
#   進度條長度＝新郎 0～2.0 秒實際走的距離、站著卡住的長度＝等到 3.05 秒扯完再起步。
import bpy, math, os, random
from mathutils import Vector, Matrix, Quaternion

use("set_v2_milestone")

S03 = dict(dur=7.74, t99=2.0, t100=3.05, bx=-0.30, by=-0.98, gy=-1.08, side_gap=0.80, tow=0.55,
           cam_y=-7.0, cam_z=1.30, aim_z=1.02, margin_l=0.40, margin_r=0.95)
S03_MOCAP = dict(walk=dict(bvh="35_01", frames=(2, 358)), stop=dict(bvh="16_33", frames=(2, 236)), start=dict(bvh="82_08", frames=(900, 1250)))
# stop_side／stop_at：16_33 從哪隻腳、第幾格附近的支撐期接進來（第 148 格右腳＝最後一步，剩約 0.45 m 就停）；
# walk_after：100% 之後幾秒起步；go_step：起步後第幾個同一隻腳的支撐期接 16_33 的最後一步
S03_JOIN = dict(blend=0.20, lead=4, stand_blend=0.30, stop_side="R", stop_at=148, walk_after=0.08, go_step=1,
                straight_from=0.75, straight_reach=0.9997, brace_drop=0.025)
# 上身前傾（度；Spine 0.40、Chest 以上 0.65、Neck 0.45、Head 0＝頭保持平視）：走路、卡住加多少、扯的那一下、走到新娘身邊後淡掉
S03_LEAN = dict(walk=14.0, stuck=18.0, yank=6.0, after=4.0)
S03_FIST_DROP = (0.06, 0.12)         # 肩前那隻（左）、橫過胸前那隻（右）拳頭往下移（公尺，× 體型）
S03_YANK = dict(dist=0.10, t=(2.80, 2.97, 3.05, 3.35))     # 雙手往前下扯（bump 的四個時間點，100% 在 3.05）


def _flag(F, s, i):
    return any(a <= i <= b for a, b in F.contact_src[s])


def mocap_pull_chain(ns, heading, t99, t100, fps=120.0):
    """35_01 → 16_33（停）→ 站著 → 82_08（起步）→ 16_33（停）。回傳 fn(u)（u＝0～1）＋ fn.dur、fn.shift（片段秒數＝場景秒數＋shift）、
    fn.pos、fn.settle（最後站定的場景秒數）、fn.t_go（起步的場景秒數）、fn.joins（各接點）"""
    lib = os.path.join(LIB, "mocap"); J = S03_JOIN
    FW, FS, FC = (ns["mocap_action"](os.path.join(lib, S03_MOCAP[k]["bvh"] + ".bvh"), frames=S03_MOCAP[k]["frames"], heading=heading,
                                     origin=(0.0, 0.0), foot_fix=False, fix_arm_offset=False) for k in ("walk", "stop", "start"))
    rig = FW.rig; slerp = ns["_slerp"]
    NW, NS, NC = len(FW.R_fk), len(FS.R_fk), len(FC.R_fk)
    K = int(round(J["blend"] * fps)); K2 = int(round(J["stand_blend"] * fps)); lead = J["lead"]; need = K + lead + 2
    sd1 = J["stop_side"]
    rs = min([r for r in FS.contact_src[sd1] if r[1] - r[0] >= need], key=lambda r: abs(r[0] - J["stop_at"]))
    jS = rs[0] + lead
    s_set = max(FS.contact_src[s][-1][0] for s in "LR")          # 16_33 兩腳都踩定的第一格（停下）
    # 停下＝t99：往前推 35_01 要從哪一個同一隻腳的支撐期接（前面要夠長，t=0 時已經在走）
    t_join = t99 - (s_set - jS) / fps                            # 接點（淡入開始）的場景秒數
    rw = [r for r in FW.contact_src[sd1] if r[0] + lead >= int(round(t_join * fps)) + 1 and r[0] + lead + K <= NW - 1][0]
    jW = rw[0] + lead
    shift = jW / fps - t_join
    R_c, r_c, src = list(FW.R_fk[:jW]), list(FW.roots[:jW]), [(FW, i) for i in range(jW)]

    def fade(Fa, ia, oa, Fb, ib, ob, n, hold_a=False):
        for i in range(n + 1):
            u = i / n; w = u * u * (3 - 2 * u)
            xa = ia if hold_a else ia + i
            Ra, Rb = Fa.R_fk[xa], Fb.R_fk[ib + i]
            R_c.append({k: slerp(Ra[k], Rb[k], w) for k in rig.keys}); r_c.append((Fa.roots[xa] + oa).lerp(Fb.roots[ib + i] + ob, w))
            src.append((Fa, xa) if w < 0.5 else (Fb, ib + i))

    def foot(F, i, s, o=Vector()):
        return rig.fk(F.R_fk[i], F.roots[i] + o)[f"{s}_Foot"]
    off1 = foot(FW, jW, sd1) - foot(FS, jS, sd1); off1.z = 0.0
    fade(FW, jW, Vector(), FS, jS, off1, K)
    for i in range(jS + K + 1, NS):
        R_c.append(FS.R_fk[i]); r_c.append(FS.roots[i] + off1); src.append((FS, i))
    # 站著卡住：停在 16_33 最後一格，等到 t100＋walk_after 起步。82_08 從「第一隻腳剛要離地」前 0.1 秒淡入 0.2 秒，
    # 對齊不離地那隻腳（支撐腳）：16_33 停下時兩腳只隔 8 cm、82_08 站著隔 27 cm，兩腳都踩著時淡入的話腿會被拉著交叉（第 2 輪實測腿互穿 19 mm）；
    # 改成在抬腳那一刻接，抬起的腳在空中自己移到 82_08 的位置
    ends = {s: next(r[1] for r in FC.contact_src[s] if r[1] > 60) for s in "LR"}
    s_lift = min("LR", key=lambda s: ends[s]); s_sup = "R" if s_lift == "L" else "L"
    c_go = ends[s_lift]                                          # 82_08 第一隻腳離地
    c0 = c_go - K // 2
    t_go = t100 + J["walk_after"]
    n_hold = max(0, int(round((t_go + shift) * fps)) - K // 2 - len(R_c))
    for _ in range(n_hold):
        R_c.append(FS.R_fk[NS - 1]); r_c.append(FS.roots[NS - 1] + off1); src.append((FS, NS - 1))
    off3 = foot(FS, NS - 1, s_sup, off1) - foot(FC, c0, s_sup); off3.z = 0.0
    nf = K
    fade(FS, NS - 1, off1, FC, c0, off3, nf, hold_a=True)
    # 起步後第 go_step 個支撐期（和 16_33 最後一步同一隻腳）接 16_33 的最後一步
    st = sorted(r[0] for r in FC.contact_src[sd1] if r[0] > c_go and r[1] - r[0] >= need)
    jC = st[min(len(st) - 1, J["go_step"] - 1)] + lead
    for i in range(c0 + nf + 1, jC):
        R_c.append(FC.R_fk[i]); r_c.append(FC.roots[i] + off3); src.append((FC, i))
    i_j4 = len(R_c)
    off4 = foot(FC, jC, sd1, off3) - foot(FS, jS, sd1); off4.z = 0.0
    fade(FC, jC, off3, FS, jS, off4, K)
    for i in range(jS + K + 1, NS):
        R_c.append(FS.R_fk[i]); r_c.append(FS.roots[i] + off4); src.append((FS, i))
    N = len(R_c)
    # 卡住時膝蓋多彎（骨盆下沉 brace_drop，鎖腳 IK 會把腳留在地上）
    k = ns["BODY_S"]
    for i in range(N):
        t = i / fps - shift
        dz = J["brace_drop"] * k * seg01(t, t99, t99 + 0.35) * (1 - seg01(t, t100 + 0.05, t_go + 0.2))
        if dz:
            r_c[i] = r_c[i] - Vector((0, 0, dz))
    contact = {s: _runs([_flag(F, s, i) for F, i in src]) for s in "LR"}
    pf = _posture_R(ns, heading)
    if pf:
        R_c = pf(R_c)
    sole = {"L": [], "R": []}
    for b, co in ns["sole_points"](ns["ARM"]):
        s = "L" if "_L_" in b else "R"
        key = next((kk for kk in rig.keys if ns["bn"](kk) == b), None)
        if key:
            sole[s].append((key, co))

    def sole_pts(R, Hd, s, o=Vector()):
        return [(Matrix.Translation(Hd[key] + o) @ R[key].to_matrix().to_4x4()) @ co for key, co in sole[s]]
    R_out, roots, contacts, extra = ns["_fix_feet"](rig, R_c, r_c, sole, sole_pts, contact, 0.995, fps)
    extra["knee_straight"] = _knee_straighten(ns, rig, R_out, roots, contacts, fps)
    last = max(contacts[s][-1][0] for s in "LR")
    t_settle = last / fps - shift
    # 上身前傾：拉東西的姿勢。頭的世界旋轉不動＝頭保持平視
    ax = Quaternion(Vector((0, 0, 1)), math.radians(heading)) @ Vector((1, 0, 0))
    for i in range(N):
        L = lean_at(i / fps - shift, t99, t100, t_settle)
        if abs(L) < 1e-4:
            continue
        R = dict(R_out[i])
        for kk in R:
            if kk == "Hips" or kk == "Head" or "Leg" in kk or "Foot" in kk or "ToeBase" in kk:
                continue
            f = 0.40 if kk == "Spine" else (0.45 if kk == "Neck" else 0.65)
            R[kk] = Quaternion(ax, math.radians(L * f)) @ R[kk]
        R_out[i] = R
    dur = (N - 1) / fps

    def fn(u):
        x = max(0.0, min(1.0, u)) * (N - 1); i = min(int(x), N - 2); f = x - i
        R = {kk: slerp(R_out[i][kk], R_out[i + 1][kk], f) for kk in rig.keys}
        root = roots[i].lerp(roots[i + 1], f)
        return dict(rig.to_dict(R), hands=("fist", "fist"), root=(root.x, root.y, root.z), rz=0.0, ground=False, face={"Fcl_ALL_Fun": 0.45})
    fn.dur = dur; fn.shift = shift; fn.rig = rig; fn.R = R_out; fn.roots = roots; fn.contacts = contacts; fn.info = extra
    fn.pos = lambda u: tuple(roots[int(round(max(0, min(1, u)) * (N - 1)))].xy + rig.rest_h["Hips"].xy)
    fn.settle = round(t_settle, 3); fn.t_go = round(t_go, 3)
    fn.joins = dict(walk_stop=dict(side=sd1, walk_frame=S03_MOCAP["walk"]["frames"][0] + jW, stop_frame=S03_MOCAP["stop"]["frames"][0] + jS,
                                   t=round(t_join, 3)),
                    hold=dict(frames=n_hold, sec=round(n_hold / fps, 3)),
                    start=dict(fade_from_frame=S03_MOCAP["start"]["frames"][0] + c0, lift_frame=S03_MOCAP["start"]["frames"][0] + c_go, lift=s_lift,
                               t_go=round(t_go, 3)),
                    start_stop=dict(start_frame=S03_MOCAP["start"]["frames"][0] + jC, stop_frame=S03_MOCAP["stop"]["frames"][0] + jS,
                                    t=round(i_j4 / fps - shift, 3)),
                    start_t=round(-shift, 3), end_t=round(dur - shift, 3))
    return fn


def lean_at(t, t99, t100, t_settle):
    Lw = S03_LEAN["walk"] * seg01(t, -0.5, 0.3)
    Ls = S03_LEAN["stuck"] * seg01(t, t99 - 0.05, t99 + 0.35) * (1 - seg01(t, t100 + 0.05, t100 + 0.45))
    Ly = S03_LEAN["yank"] * bump(t, *S03_YANK["t"])
    tail = 1 - seg01(t, t100 + 0.2, t_settle)                    # 100% 之後慢慢站直（剩 after 度），站定時歸零
    return (Lw * tail + S03_LEAN["after"] * (1 - tail) * (1 - seg01(t, t_settle - 0.3, t_settle))) + Ls + Ly


def _knee_straighten(ns, rig, R_out, roots, contacts, fps, max_shift=None):
    """站定前膝蓋打直（同 shots_v2.mocap_walk_stop 的做法與理由：CMU 站著膝蓋就彎約 30°）：骨盆最小移動量 D 讓兩腿伸到 straight_reach，
    片段結束前 straight_from 秒起漸進套用（單腳支撐時只到支撐腿構得到為止），腳踝目標不變、腳底不滑"""
    N = len(R_out); st_from = S03_JOIN["straight_from"]; Rch = S03_JOIN["straight_reach"]
    i0 = max(1, N - 1 - int(round(st_from * fps)))
    last = max(contacts[s][-1][0] for s in "LR")
    i1 = max(i0 + 1, last)
    Hn = rig.fk(R_out[-1], roots[-1]); D = Vector((0.0, 0.0, 0.0)); LEG = {}
    for s in "LR":
        L1 = (rig.rest_h[f"{s}_LowerLeg"] - rig.rest_h[f"{s}_UpperLeg"]).length; L2 = (rig.rest_h[f"{s}_Foot"] - rig.rest_h[f"{s}_LowerLeg"]).length
        LEG[s] = (Hn[f"{s}_UpperLeg"], Hn[f"{s}_Foot"], (L1 + L2) * Rch)
    for _ in range(2000):
        c = Vector((0.0, 0.0, 0.0))
        for s in "LR":
            h, a_, Rm = LEG[s]; v = (h + D) - a_
            c += v.normalized() * (Rm - v.length)
        D = D + c * 0.5
        if c.length < 1e-7:
            break
    if max_shift is not None and D.length > max_shift:          # 站定那格兩腳離太遠（或還在跨步）：骨盆最多只挪 max_shift，避免整個人被拉下去
        D = D * (max_shift / D.length)
    qb = ns["_qbetween"]
    LL = {s: LEG[s][2] for s in "LR"}
    lam = [0.0] * N; cap = [1.0] * N
    for i in range(i0, N):
        u = max(0.0, min(1.0, (i - i0) / (i1 - i0))); w = u * u * (3 - 2 * u)
        Hd1 = rig.fk(R_out[i], roots[i]); hi = 1.0
        for s in "LR":
            h, a_ = Hd1[f"{s}_UpperLeg"], Hd1[f"{s}_Foot"]
            if (h - a_).length >= LL[s]:
                hi = 0.0; break
            if (h + D - a_).length > LL[s]:
                l0, l1 = 0.0, 1.0
                for _ in range(30):
                    m = 0.5 * (l0 + l1)
                    if (h + D * m - a_).length > LL[s]:
                        l1 = m
                    else:
                        l0 = m
                hi = min(hi, l0)
        cap[i] = hi; lam[i] = min(w, hi)
    for sig in (0.04, 0.02):
        sm = ns["_gauss"](lam, sig * fps)
        lam = [min(sm[i], cap[i]) if i >= i0 else 0.0 for i in range(N)]
    for i in range(i0, N):
        w = lam[i]
        if w <= 0.0:
            continue
        Hd1 = rig.fk(R_out[i], roots[i]); R = dict(R_out[i]); r_new = roots[i] + D * w
        Hn2 = rig.fk(R, r_new)
        for s in "LR":
            ul, ll, ft = f"{s}_UpperLeg", f"{s}_LowerLeg", f"{s}_Foot"
            L1 = (rig.rest_h[ll] - rig.rest_h[ul]).length; L2 = (rig.rest_h[ft] - rig.rest_h[ll]).length
            S_ = Hn2[ul]; W_ = Hd1[ft]; v = W_ - S_; d = max(1e-4, min(v.length, (L1 + L2) * 0.9999)); dr = v.normalized()
            ca = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
            pp = Hd1[ll] - S_; pp = pp - dr * pp.dot(dr)
            pp = pp.normalized() if pp.length > 1e-6 else Vector((0, -1, 0))
            E = S_ + dr * math.cos(ca) * L1 + pp * math.sin(ca) * L1
            cur_t = (R[ul] @ rig.rest_q[ul].inverted()) @ (rig.rest_h[ll] - rig.rest_h[ul]); R[ul] = qb(cur_t, E - S_) @ R[ul]
            cur_s = (R[ll] @ rig.rest_q[ll].inverted()) @ (rig.rest_h[ft] - rig.rest_h[ll]); R[ll] = qb(cur_s, (S_ + dr * d) - E) @ R[ll]
        R_out[i] = R; roots[i] = r_new
    return dict(from_frame=i0, full_frame=i1, shift_mm=[round(x * 1000, 1) for x in D])


def v2_03_setup():
    if V2S.get("03"):
        return V2S["03"]
    c = S03; t99, t100 = c["t99"], c["t100"]
    if "mocap_action" not in GR:
        GR["use"]("mocap_retarget")
    F = mocap_pull_chain(GR, 90.0, t99, t100)
    g_end = (c["bx"] - c["side_gap"], c["gy"])
    off = Vector(g_end) - Vector(F.pos(1.0))
    k = GR["BODY_S"]; sg = -1                                     # 緞帶扛左肩（pull_walk 的座標鏡射）
    near, far = "L", "R"

    def mir(p):
        return (p[0] * sg, p[1], p[2])

    def u_of(t):
        return (t + F.shift) / F.dur

    def gx(t):
        return F.pos(u_of(t))[0] + off.x

    def brace(t):
        return seg01(t, t99 - 0.05, t99 + 0.3) * (1 - seg01(t, t100 + 0.05, t100 + 0.5))

    yd = Vector(mir(GR["PULL_YANK"])).normalized()

    def pull_pose(tl):                                           # 時間軸 spec（tl＝場景秒數，這段從 0 開始）
        P = dict(F(u_of(tl)))
        r = P["root"]; P["root"] = (r[0] + off.x, r[1] + off.y, r[2])
        GR["arms_down"](P); P["L_Hand"] = []; P["R_Hand"] = []
        d = yd * S03_YANK["dist"] * bump(tl, *S03_YANK["t"])
        # 拳頭比動作庫 pull_walk 低一點（S03_FIST_DROP）：側面看，橫過胸前那隻拳頭在動作庫的高度剛好擋在嘴前
        P["ik"] = [(near, GR["_V"](k, *mir(GR["PULL_R"])) + d - Vector((0, 0, S03_FIST_DROP[0] * k)), GR["_V"](k, *mir(GR["PULL_R_POLE"])), None, "UpperChest"),
                   (far, GR["_V"](k, *mir(GR["PULL_L"])) + d - Vector((0, 0, S03_FIST_DROP[1] * k)), GR["_V"](k, *mir(GR["PULL_L_POLE"])), None, "UpperChest")]
        b = brace(tl)
        P["face"] = {"Fcl_ALL_Fun": 0.45 * (1 - b), "Fcl_EYE_Close": 0.55 * b, "Fcl_MTH_E": 0.15 + 0.45 * b}
        P["abs"] = True
        return P
    # 進度條：0%＝t=0 時把手的位置（新郎身後 tow）；99%＝t99 時把手的位置；把手停在「婚禮」前 gap
    gap = MS["wed_r"] + MS["handle_r"] + 0.012
    x0 = gx(0.0) - c["tow"]; x99 = gx(t99) - c["tow"]
    L = (x99 - x0) + gap
    ts = F.settle; t_rel = ts                                     # 站定＝放下緞帶、轉向鏡頭
    turn_t = (ts, ts + 0.45)
    b_turn = (ts + 0.15, ts + 0.75)
    print("V2_03_SETUP", "joins", F.joins, "settle", ts, "bar x0", round(x0, 3), "L", round(L, 3), "groom end", [round(v, 3) for v in g_end],
          "start x", round(gx(0.0), 3), "dur", round(F.dur, 3), "info", F.info, flush=True)

    def place_g(t):
        return (g_end[0], g_end[1], turn(t, turn_t[0], turn_t[1], 90.0, 25.0))

    def place_b(t):
        return (c["bx"], c["by"], turn(t, b_turn[0], b_turn[1], -58.0, -15.0))     # 新郎到身邊後轉向鏡頭

    def act(ns, key):
        return lambda tl: act_pose(ns, key, tl)
    # 換動作的淡入：舉手的動作（wave2、cheer↔clap）0.8～0.9 秒（0.3 秒時手臂每格轉 35～41°、0.5～0.6 秒時 25°）
    AG = Actor2(GR, [(0.0, ts, pull_pose, 0.0),
                     (ts, turn_t[1], postured(GR, act(GR, "idle")), 0.50),
                     (turn_t[1], 10.0, postured(GR, act(GR, "wave2")), 0.90)], place_g)
    AB = Actor2(B, [(0.0, t100, act(B, "cheer"), 0.0), (t100, 5.05, act(B, "clap"), 0.80), (5.05, 10.0, act(B, "cheer"), 0.80)], place_b)
    st = dict(F=F, off=off, gx=gx, x0=x0, L=L, gap=gap, t_rel=t_rel, turn=turn_t, b_turn=b_turn, AG=AG, AB=AB, g_end=g_end)
    V2S["03"] = st
    SHOTS["v2_03"]["actors"] = [AG, AB]
    SHOTS["v2_03"]["qa_skip"] = [turn_t, b_turn]
    return st


def v2_03_build():
    need_garden()
    st = v2_03_setup()
    col = coll_new("V2_Milestone", v2_coll())
    if "MS_Track" not in bpy.data.objects:
        ms_build(col, st["x0"], st["L"], st["gap"])


def v2_03_progress(t):
    st = V2S["03"]; t99, t100 = S03["t99"], S03["t100"]
    if t < t99:
        d0 = st["gx"](0.0); d = (st["gx"](max(0.0, t)) - d0) / max(1e-6, st["gx"](t99) - d0)
        return 0.99 * max(0.0, min(1.0, d))
    return 0.99 + 0.01 * seg01(t, t100 - 0.05, t100)


def v2_03_petals(i, rnd):
    st = V2S["03"]; t100 = S03["t100"]
    if i < 70:                                                   # 「婚禮」節點迸出的花瓣
        c = Vector((st["x0"] + st["L"], MS["y"] - 0.05, MS["z"]))
        a = rnd.uniform(0, 2 * math.pi); s_ = rnd.uniform(0.6, 1.6)
        return (t100 + rnd.uniform(0, 0.12), c, (math.cos(a) * s_ * 0.8, -abs(math.sin(a)) * 0.6 - 0.2, rnd.uniform(0.6, 2.0)))
    t0 = t100 + rnd.uniform(0.05, 1.6)                           # 整個畫面的花瓣雨
    return (t0, (rnd.uniform(st["x0"] - 0.4, S03["bx"] + 0.8), rnd.uniform(-1.6, 0.2), rnd.uniform(2.6, 3.4)), (0, 0, 0))


def v2_03_cam():
    st = V2S["03"]; c = S03
    xl = st["x0"] - c["margin_l"]; xr = c["bx"] + c["margin_r"]
    cx = (xl + xr) / 2; d = (c["gy"] + c["by"]) / 2 - c["cam_y"]
    return (cx, c["cam_y"], c["cam_z"]), (cx, (c["gy"] + c["by"]) / 2, c["aim_z"]), 36.0 * d / (xr - xl)


def v2_03_frame(t, props=True, cast=True, cam=True):
    st = v2_03_setup(); t99, t100 = S03["t99"], S03["t100"]
    if props:
        garden_parts(()); v2_parts(("V2_Milestone",))
        p = v2_03_progress(t)
        # 卡在 99%：把手在「婚禮」前顫動（越接近扯的那一下越用力）
        shake = 0.0
        if t99 <= t < t100:
            shake = (0.003 + 0.004 * seg01(t, t99, t100 - 0.1)) * math.sin(2 * math.pi * 9 * t) * seg01(t, t99, t99 + 0.1)
        hx0 = ms_handle_x(p)
        lit = []
        for i, (e, o, r) in enumerate(MS_OBJ["nodes"]):
            if i == 0:
                lit.append(seg01(t, 0.2, 0.38))
            elif i == 3:
                lit.append(seg01(t, t100, t100 + 0.16))
            else:
                lit.append(max(0.0, min(1.0, (hx0 - (e.location.x - r)) / (2 * r))))
        halos = (lin01(t, t100, t100 + 0.75), lin01(t, t100 + 0.22, t100 + 0.97))
        head = ms_update(p, lit, shake, halos)
        petals_update(t, v2_03_petals)
    if cast:
        st["AG"].pose(t); st["AB"].pose(t); b08_face_keys(t)
    if props:
        # 緞帶（同第一版 ③）：把手 → 垂下 → 肩上 → 肩前的拳頭 → 前面的拳頭；100% 時尾端從把手脫開、拖在身後草地；站定放手、整條落地
        bpy.context.view_layer.update()
        far_fist, near_fist, sh = GR["ribbon_points"]("L", GR["ARM"])
        gxw = GR["ARM"].location.x
        loose = seg01(t, t100, t100 + 0.45)
        tail = head.lerp(Vector((gxw - 0.75, S03["gy"] + 0.28, 0.012)), loose)
        drop = seg01(t, st["t_rel"], st["t_rel"] + 0.45)
        if drop > 0:
            def gnd(v, dx):
                return v.lerp(Vector((v.x + dx, v.y + 0.12, 0.012)), drop)
            sh, near_fist, far_fist = gnd(sh, -0.25), gnd(near_fist, -0.1), gnd(far_fist, 0.0)
        span = (sh - tail).length
        sag = 0.10 * max(0.0, min(1.0, (0.95 - span) / 0.35))          # 卡住時新郎往前挪、緞帶拉緊：下垂變小
        mid = tail.lerp(sh, 0.45); mid.z = max(0.012, min(tail.z, sh.z) - sag * (1 - drop))
        ms_tow([tail, mid, sh, near_fist, far_fist])
    if cam:
        loc, aim_, lens = v2_03_cam()
        look(loc, aim_, lens)


SHOTS["v2_03"] = dict(set="Set_Garden", cast=True, t0=0.0, dur=S03["dur"], tail=0.0, build=v2_03_build, frame=v2_03_frame,
                      actors=[], qa_skip=[], stills=[0.5, 1.5, 2.4, 2.97, 3.3, 4.3, 5.5, 7.0])


# ══════════ ⑧ 中段 6.0～9.5：穿過拱門小畫回到 3D 花園，新人在拱門下置中（構圖同 ② 拱門下：全身、約佔畫面高度 3/4） ══════════
# 鏡頭照 ② 的拱門下構圖（V2_02：(0,−5.95,0.95) 看 (0,0.96,1.13)、58 mm，兩人在 y≈0.9）移到兩人站的 y＝ARCH_Y，再退 0.6 m：
#   新郎揮手、新娘比愛心時手舉過頭，要留字幕條的位置（手最高點約在 16%、腳在 93%）；
# 6.0～6.9 從後面一點慢出推進（接「穿過小畫」的動勢），之後固定。角色 6.4 秒淡入 0.5 秒是合成做（set／cast 分層，同第一版 ⑧）
S08 = dict(gx=-0.42, bx=0.40, rz=8.0, cam0=(0.0, -8.4, 1.05), cam1=(0.0, -7.15, 0.95), aim=(0.0, ARCH_Y, 1.15), lens=58.0,
           push=(6.0, 6.9), act=6.4, act_start=5.6, wave_out=15.0,
           wave=os.environ.get("V2_08_WAVE", "wave_arc"), wave_kw=__import__("json").loads(os.environ.get("V2_08_WAVE_KW", "{}")))   # V2_08_WAVE_KW＝試參數用        # V2_08_WAVE=wave_r＝第 2 版（真人 143_25＋外張 15°）對照


# ── ⑧ 新娘表情覆寫（2026-10-10 第 4 輪回饋「新娘微笑笑開：嘴巴用大笑Joy 改前（參考圖第 5 格）、眼睛張開像微笑改後（第 4 格）」）──
#   Fcl_ALL_Joy 會連眼睛一起閉（笑瞇眼），所以拆成分部位鍵：嘴＝Fcl_MTH_Joy（張嘴笑、露上排牙，和 ALL_Joy 的嘴型相同）、
#   眉＝Fcl_BRW_Joy，眼睛不加任何笑眼鍵（全開）。5.6～9.5 秒全程維持（5.4～5.6 從動作庫的臉淡過來，6.0 鏡頭才開始），只留眨眼。
#   動作庫（heart_head 的 face、project.json 的 face）不動。MTH_Joy／BRW_Joy 不在 pose_lib.FACE_KEYS 裡（set_face 不會管它們），
#   所以 v2_08_frame 每格自己寫進形狀鍵、範圍外寫 0。V2_08_FACE_LEGACY=1（環境變數）＝改前對照（第 3 版的臉）
F08 = dict(t=(5.4, 5.6), mth_joy=1.0, brw_joy=1.0, blink=(7.25, 8.75), blink_hw=0.08)
F08_LEGACY = bool(int(os.environ.get("V2_08_FACE_LEGACY", "0") or 0))


def f08_weight(t):
    a, b = F08["t"]
    return 0.0 if t <= a else (1.0 if t >= b else ease((t - a) / (b - a)))


def f08_blink(t):
    return max([0.0] + [max(0.0, 1.0 - abs(t - tb) / F08["blink_hw"]) for tb in F08["blink"]])


def b08_face_mod(t, P):
    w = f08_weight(t)
    if w <= 0:
        return P
    f0 = P.get("face") or {}
    f1 = {"Fcl_EYE_Close": f08_blink(t)}                       # 不放 Fcl_ALL_Fun／Joy：嘴眉由 b08_face_keys 直接寫
    P["face"] = {k: f0.get(k, 0.0) * (1 - w) + f1.get(k, 0.0) * w for k in set(f0) | set(f1)}
    return P


def b08_face_keys(t):
    kb = bpy.data.objects[B["WHO"] + "_Face"].data.shape_keys.key_blocks
    w = 0.0 if F08_LEGACY else f08_weight(t)
    kb["Fcl_MTH_Joy"].value = F08["mth_joy"] * w
    kb["Fcl_BRW_Joy"].value = F08["brw_joy"] * w


def v2_08_setup():
    if V2S.get("08"):
        return V2S["08"]
    c = S08

    def act(ns, key):
        return lambda tl: act_pose(ns, key, tl)
    # 動作 5.6 秒就開始（淡入 0.8 秒）：6.4 秒角色淡入時已經在揮手／比愛心，看不到 idle → 揮手的過渡（過渡中雙手會平舉、新郎的手伸到她手臂前）。
    # 2026-10-09 使用者回饋：新郎改右手單手揮（wave_r，CMU 143_25 真人，大臂跟著擺、左手放下），新娘改 heart_head（指尖在頭頂相碰、掌心朝下）
    s0 = c["act_start"]
    # 揮手的右臂整條繞前後軸往外張 wave_out 度（2026-10-09 使用者：手擺到耳邊）：手到頭頂中心最近 33.4 → 約 41 cm（wave2_mocap 的 both_out 同做法）。
    # postured 保留：wave_r 的骨盆照抄真人、沒有男性骨盆修正（不包時 −6.7°、idle 不包 −3.8°），包了是 −17.7°（idle 包了 −14.8°），只修一次
    def wave_out(spec, deg):
        def fn(tl):
            P = dict(spec(tl)); P["R_UpperArm"] = list(P.get("R_UpperArm", [])) + [("Y", -deg)]
            return P
        return fn
    # 2026-10-09 第 3 輪：「肩膀消失、破圖」「不是水平橫移劃小弧形的揮手」→ 改用動作庫 wave_arc（IK 水平弧形、肩胛跟著抬 14～18°）。
    # 根本原因：wave_r（CMU 143_25）轉位後右肩胛骨往下壓 43～46°（v2_s08_shoulder.py 量的），外套肩頂塌、脖子露出變長 15～24%；
    # 再加上 wave_out 外張 15° 讓上臂近水平外展（85～95°）。wave_arc 不吃真人肩胛，也不再外張（wave_out 不用）。
    # hold＝True：起手 0.55 秒（5.6～6.15，角色 6.4 才淡入）後一直揮到鏡頭結束、不收手；淡入 0.3（起手本身從垂手開始）
    if S08.get("wave") == "wave_r":                                                   # 第 2 版對照
        g_wave, g_bl = postured(GR, wave_out(act(GR, "wave_r"), c["wave_out"])), 0.80
    else:
        FW = GR["wave_arc"]("R", hold=True, cycles=10, **S08.get("wave_kw", {}))
        g_wave, g_bl = postured(GR, lambda tl: FW(min(0.9999, tl / FW.dur))), 0.30
    AG = Actor2(GR, [(5.5, s0, postured(GR, act(GR, "idle")), 0.0), (s0, 12.0, g_wave, g_bl)],
                lambda t: (c["gx"], ARCH_Y, c["rz"]))
    AB = Actor2(B, [(5.5, s0, act(B, "idle"), 0.0), (s0, 12.0, act(B, "heart_head"), 0.80)],
                lambda t: (c["bx"], ARCH_Y, -c["rz"]), None if F08_LEGACY else b08_face_mod)
    V2S["08"] = dict(AG=AG, AB=AB)
    SHOTS["v2_08"]["actors"] = [AG, AB]
    return V2S["08"]


def v2_08_petals(i, rnd):
    t0 = rnd.uniform(5.8, 9.4)
    return (t0, (rnd.uniform(-1.2, 1.2), rnd.uniform(0.2, 0.8), rnd.uniform(1.0, 2.6)), (rnd.uniform(-0.4, 0.4), rnd.uniform(-3.0, -1.8), rnd.uniform(-0.2, 0.4)))


def v2_08_build():
    need_garden(); v2_08_setup()


def v2_08_frame(t, props=True, cast=True, cam=True):
    st = v2_08_setup(); c = S08
    if props:
        garden_parts(()); v2_parts(()); petals_update(t, v2_08_petals)
    if cast:
        st["AG"].pose(t); st["AB"].pose(t); b08_face_keys(t)
    if cam:
        u = seg01(t, *c["push"])
        look(lerpv(c["cam0"], c["cam1"], 1 - (1 - u) ** 2), Vector(c["aim"]), c["lens"])


SHOTS["v2_08"] = dict(set="Set_Garden", cast=True, t0=6.0, dur=3.5, tail=0.0, build=v2_08_build, frame=v2_08_frame,
                      actors=[], stills=[6.3, 6.9, 7.6, 8.4, 9.2])
