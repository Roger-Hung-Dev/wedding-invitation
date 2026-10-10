# 情境版 ③ v2_03c「推紅毯」（2026-10-09 第 3 幕改版，取代 v2_03 拉緞帶的進度條；v2_03 保留）。
# 依據：主控端轉達的使用者回饋＋時間軸：全長 7.74 秒、3.05 秒到 100%（對齊配樂）。
# 載入：在 run_prod 之後 use("shots_v2_s03carpet")（要用 shots_v2 的 Actor2、postured、_posture_R、_runs 與 shots_v2_s0308 的 _knee_straighten）。
#
# 2026-10-10 第 4 輪（使用者回饋 9 條；第 3 輪的程式備份在 D:\render-work\opening-v12\backup_r5\）：
#   1. 毯上平貼字 → 立體文字牆 ×4（set_v2_carpet.cp_wall）：「相遇」「交往」「求婚」立在紅毯遠側（離鏡頭遠的那一邊，不擋人），
#      「婚禮」在拱門左柱內側、下方一行「2026.12.12」；紅毯卷滾到那一面時 0.25 秒亮燈、之後一直亮。
#   2. 拿掉石頭：紅毯卷一路跟著新郎的手（越鋪越小、越來越難推），卡住那段（82_06 頂住）新郎身體再多前傾 8°，新娘來推一把才推動。
#   3. 起步步幅太大：真人推重物（81_05／82_06）兩腳前後距離 0.6～0.9 m，整段沿行進方向縮成 0.7 倍（腳與骨盆一起縮、腿用 IK 重新對腳、
#      骨盆補高保持原本的膝蓋彎曲），前 0.9 秒時間軸緩入（起步速度從 0.45 倍慢慢回到 1 倍）。
#   4. 新娘煞車：跑來急停時站位往後挪（蓬裙和新郎量網格最近距離 > 0），急停前 0.35 秒上身微後仰。
#   5. 新娘推一把：雙手掌心貼在新郎外套背上（掌心中心落在外套表面、掌心朝他、手指順著前臂方向），
#      2.75～3.05 身體再前傾、骨盆往前 5 cm；他往前衝時她的手肘自然打直，構不到才放開。
#   6. 結尾揮手 wave2_mocap → 動作庫 wave_arc2 的工廠 wave_arc('both')（雙手同時往外／往內；肩胛不被往下壓）；新娘 hz 1.3。
#   7. 新郎推的手：雙手掌心貼紅毯卷（掌心中心在卷的表面、掌心朝卷），接觸點沿卷的弧面挑「前臂和表面夾 40°」的位置（＝手腕往上翹約 40°）。
#   8. 推完那一下（3.05 推動 → 往前衝）手一直貼著卷，衝到最快時才放開，卷自己再滾一小段停在拱門前。
#   9. 轉身：原地腳掌轉 → 往右邊踏步轉身（3～4 步：一腳踏出去、重心移過去、另一腳跟上，著地腳不滑），新娘轉完站到新郎左邊約 0.75 m。
import bpy, math, os, random
from mathutils import Vector, Matrix, Quaternion

use("set_v2_carpet")

C3 = dict(dur=7.74, t100=3.05, heading=180.0, cam=(6.3, -3.3, 1.75), aim=(0.0, -1.35, 0.72), lens=34.0,
          arch_y=ARCH_Y, r0=0.30, r1=0.20, carpet_back=1.0, k_stride=0.60, warp=(0.25, 0.9), g_lean=8.0,
          wall_x=-2.4, wall_gap=0.68, wall_lift=1.50, wed_pos=(-0.80, 0.24), roll_end_y=0.02, roll_x=0.17, ext_want=40.0,
          b_back=-0.06, b_depth=-0.80, b_heading=105.0, b_step_in=0.17, b_run_yaw=65.0, b_final=0.90, b_turn_t=4.30, g_sh_up=20.0, g_sh_swing=1.0, skirt_squash=0.60, step_dur=0.30, turn_blend=0.50)
C3_MOCAP = dict(push=dict(bvh="81_05", frames=(2, 1365)), strain=dict(bvh="82_06", frames=(2, 1092)), run=dict(bvh="16_57", frames=(2, 269)),
                start=dict(bvh="82_08", frames=(900, 1250)), stop=dict(bvh="16_33", frames=(2, 236)))
# 對齊點：82_06 第 burst 秒（推動了、身體開始往前衝）＝場景 t100；82_06 接進來的支撐期（右腳跨成弓箭步，第 strain_at 秒）；
# 推動後 after_at 秒附近的支撐期接到 82_06 的 stop_at 秒（最後停步、站直；淡入 blend2 秒，另一隻腳這段跨一步）；
# 新娘：16_57 急停、兩腳踩定的那一刻＝bride_stop 秒，之後上身前傾 bride_lean 度
C3_JOIN = dict(blend=0.20, blend1=0.35, blend2=0.35, lead=4, stance_v=0.25, burst=2.60, strain_at=1.63, strain_side="R", push_from=4.2,
               after_at=3.59, stop_at=7.88, stop_side="R", bride_stop=2.45, bride_lean=55.0, bride_go=7.50, stop_side16="R", stop16_at=1.23)
C3_MOCAP_DIR = os.path.join(LIB, "mocap")


class _Chain:
    """真人片段接成一段：R（每格骨頭世界旋轉）、r（骨盆位移）、src（每格的來源 (片段, 格) → 著地判斷）"""

    def __init__(self, rig, slerp):
        self.rig, self.slerp = rig, slerp; self.R, self.r, self.src = [], [], []; self.free = set()

    def add(self, F, i0, i1, off):
        for i in range(i0, i1):
            self.R.append(F.R_fk[i]); self.r.append(F.roots[i] + off); self.src.append((F, i))

    def fade(self, Fa, ia, oa, Fb, ib, ob, n, free=None):
        """free＝不對齊的那隻腳：淡入期間（前後再各多 pad 格）不算著地，鎖腳時它會平滑移到新片段的位置"""
        if free:
            i0 = len(self.R); pad = min(n // 2, 12)
            self.free.update((j, free) for j in range(max(0, i0 - pad), i0 + n + 1 + pad))
        for i in range(n + 1):
            u = i / n; w = u * u * (3 - 2 * u)
            Ra, Rb = Fa.R_fk[ia + i], Fb.R_fk[ib + i]
            self.R.append({k: self.slerp(Ra[k], Rb[k], w) for k in self.rig.keys})
            self.r.append((Fa.roots[ia + i] + oa).lerp(Fb.roots[ib + i] + ob, w)); self.src.append((Fa, ia + i) if w < 0.5 else (Fb, ib + i))

    def foot(self, F, i, s, o=Vector()):
        v = self.rig.fk(F.R_fk[i], F.roots[i] + o)[f"{s}_Foot"]; return Vector((v.x, v.y, 0.0))


def _other(s):
    return "L" if s == "R" else "R"


def _load(ns, key, heading, stance_v=None):
    p = C3_MOCAP[key]
    return ns["mocap_action"](os.path.join(C3_MOCAP_DIR, p["bvh"] + ".bvh"), frames=p["frames"], heading=heading, origin=(0.0, 0.0),
                              foot_fix=False, fix_arm_offset=False, stance_v=stance_v or C3_JOIN["stance_v"])


def _stance_at(F, side, t_local, fps, need):
    """side 這隻腳、開始時間最接近 t_local 秒、長度夠淡入的支撐期 → 起點格"""
    runs = [r for r in F.contact_src[side] if r[1] - r[0] >= need]
    return min(runs, key=lambda r: abs(r[0] - t_local * fps))[0]


def _stride_scale(ns, ch, k, fps, ns_heading=180.0):
    """沿行進方向（+Y）把整段的骨盆與腳一起縮成 k 倍（以第一格為中心），腿用兩骨 IK 重新對到縮過的腳踝；
    骨盆補高 dz（兩腳各自「保持原本髖到腳踝距離」需要的高度取小的那個、0.1 秒平滑），膝蓋彎曲維持真人的樣子。腳掌世界旋轉不動。"""
    rig = ch.rig; N = len(ch.R); yc = ch.r[0].y
    qb = ns["_qbetween"]
    L = {sd: ((rig.rest_h[f"{sd}_LowerLeg"] - rig.rest_h[f"{sd}_UpperLeg"]).length,
              (rig.rest_h[f"{sd}_Foot"] - rig.rest_h[f"{sd}_LowerLeg"]).length) for sd in "LR"}
    Hs = [rig.fk(ch.R[i], ch.r[i]) for i in range(N)]
    dzs = []
    for i in range(N):
        H = Hs[i]; r = ch.r[i]; dy = (yc + k * (r.y - yc)) - r.y; need = []
        for sd in "LR":
            hip = H[f"{sd}_UpperLeg"]; ft = H[f"{sd}_Foot"]
            d0 = min((ft - hip).length, (L[sd][0] + L[sd][1]) * 0.995)
            fy = yc + k * (ft.y - yc)
            h2 = math.hypot(ft.x - hip.x, fy - (hip.y + dy))
            need.append(math.sqrt(max(d0 * d0 - h2 * h2, 0.0)) - (hip.z - ft.z))
        dzs.append(max(-0.02, min(0.06, min(need))))
    dzs = ns["_gauss"](dzs, 0.1 * fps)
    for i in range(N):
        H = Hs[i]; r = ch.r[i]
        nr = Vector((r.x, yc + k * (r.y - yc), r.z + dzs[i])); dlt = nr - r
        R = dict(ch.R[i])
        for sd in "LR":
            ul, ll, ft = f"{sd}_UpperLeg", f"{sd}_LowerLeg", f"{sd}_Foot"
            L1, L2 = L[sd]
            S = H[ul] + dlt; Wt = Vector((H[ft].x, yc + k * (H[ft].y - yc), H[ft].z))
            v = Wt - S; d = max(1e-4, min(v.length, (L1 + L2) * 0.9999)); dr = v.normalized()
            a = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
            fwd = Vector((math.sin(math.radians(ns_heading)), -math.cos(math.radians(ns_heading)), 0.0))
            pp = ((H[ll] + dlt) - S) + fwd * 0.08                     # 膝蓋往前偏一點：腿快打直時 FK 膝蓋方向不穩、一格會翻（第 4 輪量到大腿一格 74°）
            pp = pp - dr * pp.dot(dr)
            if pp.length < 1e-6:
                pp = fwd
            pp.normalize()
            E = S + dr * math.cos(a) * L1 + pp * math.sin(a) * L1
            cur_t = (R[ul] @ rig.rest_q[ul].inverted()) @ (rig.rest_h[ll] - rig.rest_h[ul])
            R[ul] = qb(cur_t, E - S) @ R[ul]
            cur_s = (R[ll] @ rig.rest_q[ll].inverted()) @ (rig.rest_h[ft] - rig.rest_h[ll])
            R[ll] = qb(cur_s, (S + dr * d) - E) @ R[ll]
        ch.R[i] = R; ch.r[i] = nr
    return dict(k=k, dz_cm=(round(min(dzs) * 100, 1), round(max(dzs) * 100, 1)))


def _finish(ns, ch, heading, fps, posture=True):
    """接好的片段 → 鎖腳貼地、男性骨盆修正、最後站定時膝蓋拉直（同 shots_v2_s0308.mocap_pull_chain）"""
    rig = ch.rig
    contact = {s: _runs([any(a <= i <= b for a, b in F.contact_src[s]) and (j, s) not in ch.free for j, (F, i) in enumerate(ch.src)]) for s in "LR"}
    R_c = ch.R
    pf = _posture_R(ns, heading) if posture else None
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
    R_out, roots, contacts, extra = ns["_fix_feet"](rig, R_c, ch.r, sole, sole_pts, contact, 0.995, fps)
    extra["knee_straight"] = _knee_straighten(ns, rig, R_out, roots, contacts, fps, max_shift=0.08)
    return R_out, roots, contacts, extra


def _make_fn(ns, rig, R_out, roots, shift, fps, lean=None, heading=180.0, warp=None, yaw=None, pivot=None):
    """lean(t)→度：上身往前傾（Spine 0.40、Chest 以上 0.65、Neck 0.45、頭的世界旋轉不動＝保持平視），片段結束後停住的那幾秒也套得上。
    warp(t)→片段時間（場景開頭緩入用；None＝不變）。fk(t) 也套 lean，手的位置和實際擺出來的一樣"""
    N = len(R_out); slerp = ns["_slerp"]
    ax = Quaternion(Vector((0, 0, 1)), math.radians(heading)) @ Vector((1, 0, 0))

    def Rt(t):
        tw = warp(t) if warp else t
        x = max(0.0, min(N - 1.0, (tw + shift) * fps)); i = min(int(x), N - 2); f = x - i
        R = {kk: slerp(R_out[i][kk], R_out[i + 1][kk], f) for kk in rig.keys}
        L = lean(t) if lean else 0.0
        if abs(L) > 1e-4:
            for kk in R:
                if kk == "Hips" or kk == "Head" or "Leg" in kk or "Foot" in kk or "ToeBase" in kk:
                    continue
                R[kk] = Quaternion(ax, math.radians(L * (0.40 if kk == "Spine" else (0.45 if kk == "Neck" else 0.65)))) @ R[kk]
        root = roots[i].lerp(roots[i + 1], f)
        y_ = yaw(t) if yaw else 0.0
        if abs(y_) > 1e-4:                                           # 整個人繞 pivot（片段座標）水平轉 y_ 度：跑來的路線彎過來
            qz = Quaternion(Vector((0, 0, 1)), math.radians(y_))
            R = {kk: qz @ q for kk, q in R.items()}
            v = root - pivot; v2 = qz @ Vector((v.x, v.y, 0)); root = Vector((pivot.x + v2.x, pivot.y + v2.y, root.z))
        return R, root

    def fn(t):                                                   # t＝場景秒數（片段頭尾之外停在頭尾那一格）
        R, root = Rt(t)
        P = rig.to_dict(R)
        return dict(P, hands=("relax", "relax"), root=(root.x, root.y, root.z), rz=0.0, ground=False, face={"Fcl_ALL_Fun": 0.45})

    def fk(t):                                                   # 這一格的 FK 關節位置（片段座標）
        R, root = Rt(t)
        return rig.fk(R, root)
    fn.fk = fk; fn.Rt = Rt; fn.dur = (N - 1) / fps; fn.shift = shift; fn.N = N; fn.R = R_out; fn.roots = roots
    return fn


def _warp_fn():
    d, T = C3["warp"]
    return lambda t: t + d * (1 - t / T) ** 2 if t < T else t     # t=0 → 片段時間 +d、速度 1−2d/T，T 秒後回到 1 倍


def groom_chain(ns, heading, fps=120.0):
    J = C3_JOIN; t100 = C3["t100"]
    FP, FS = _load(ns, "push", heading), _load(ns, "strain", heading)
    rig = FP.rig; ch = _Chain(rig, ns["_slerp"])
    K = int(round(J["blend"] * fps)); K2 = int(round(J["blend2"] * fps)); lead = J["lead"]; need = K + lead + 2
    s1 = J["strain_side"]
    jS = _stance_at(FS, s1, J["strain_at"], fps, need) + lead
    sh82 = J["burst"] - t100                                     # 82_06 片段秒數＝場景秒數＋sh82
    t_join = jS / fps - sh82                                     # 接進 82_06 的場景秒數
    runs = [r for r in FP.contact_src[s1] if r[1] - r[0] >= need and r[0] >= J["push_from"] * fps - 1]
    jP = runs[0][0] + lead
    if jP - t_join * fps < 0:
        raise ValueError("81_05 前面不夠長")
    shift = jP / fps - t_join                                    # 整段片段秒數＝場景秒數＋shift
    ch.add(FP, 0, jP, Vector())
    off1 = ch.foot(FP, jP, s1) - ch.foot(FS, jS, s1)
    K1 = int(round(J["blend1"] * fps))                           # 第 4 輪：0.2 → 0.35 秒（兩段真人的頭部朝向差很多，0.2 秒內轉完頭一格 30°）
    ch.fade(FP, jP, Vector(), FS, jS, off1, K1, free=_other(s1))
    # 推動後往前衝一步，再接 82_06 最後的停步、站直（淡入 blend2：另一隻腳在這段跨上來）
    s2 = J["stop_side"]
    jA = _stance_at(FS, s2, J["after_at"], fps, need) + lead
    jB = _stance_at(FS, s2, J["stop_at"], fps, need) + lead
    ch.add(FS, jS + K1 + 1, jA, off1)
    off2 = ch.foot(FS, jA, s2, off1) - ch.foot(FS, jB, s2)
    ch.fade(FS, jA, off1, FS, jB, off2, K2, free=_other(s2))
    ch.add(FS, jB + K2 + 1, len(FS.R_fk), off2)
    sinfo = _stride_scale(ns, ch, C3["k_stride"], fps, heading)
    R_out, roots, contacts, extra = _finish(ns, ch, heading, fps)
    extra["stride"] = sinfo
    t_st = t_join

    def lean(t):                                                  # 卡住那段（82_06 頂住）上身再多前傾 g_lean 度
        return C3["g_lean"] * seg01(t, t_st - 0.25, t_st + 0.25) * (1 - seg01(t, t100 + 0.05, t100 + 0.45))
    fn = _make_fn(ns, rig, R_out, roots, shift, fps, lean=lean, heading=heading, warp=_warp_fn())
    last = max(contacts[s][-1][0] for s in "LR")
    fn.settle = round(last / fps - shift, 3); fn.contacts = contacts; fn.info = extra
    fn.joins = dict(push_strain=dict(side=s1, push_frame=C3_MOCAP["push"]["frames"][0] + jP, strain_frame=C3_MOCAP["strain"]["frames"][0] + jS,
                                     t=round(t_join, 3)),
                    burst_stop=dict(side=s2, from_frame=C3_MOCAP["strain"]["frames"][0] + jA, to_frame=C3_MOCAP["strain"]["frames"][0] + jB,
                                    t=round(jA / fps - sh82, 3)),
                    start_t=round(-shift, 3), end_t=round(fn.dur - shift, 3))
    fn.t_strain = t_join; fn.sh82 = sh82
    return fn


def bride_chain(ns, heading, fps=120.0):
    """16_57 跑來急停（停住）＋情境加的上身前傾（雙手推新郎背那段）→ 3.05 之後從站姿起步（82_08）、走一兩步接 16_33 最後一步，停到新郎身邊
    （做法同 shots_v2_s0308.mocap_pull_chain 的後半：在 82_08 第一隻腳剛要離地時淡入、對齊不離地的腳）。
    第一版讓新娘接 82_06 的弓箭步：上身整個趴平、蓬裙跟著骨盆斜成水平，像飛起來 → 改成站著前傾"""
    J = C3_JOIN; t100 = C3["t100"]
    FR = _load(ns, "run", heading)
    FC, FS = _load(ns, "start", heading, 0.5), _load(ns, "stop", heading, 0.5)
    rig = FR.rig; ch = _Chain(rig, ns["_slerp"])
    K = int(round(J["blend"] * fps)); lead = J["lead"]; need = K + lead + 2
    NR = len(FR.R_fk)
    stop_r = max(FR.contact_src[s][-1][0] for s in "LR")          # 急停後兩腳都踩定
    shift = stop_r / fps - J["bride_stop"]
    ch.add(FR, 0, NR, Vector())
    # 站著等到 bride_go 起步
    ends = {s: next(r[1] for r in FC.contact_src[s] if r[1] > 60) for s in "LR"}
    s_lift = min("LR", key=lambda s: ends[s]); s_sup = _other(s_lift)
    c_go = ends[s_lift]; c0 = c_go - K // 2
    n_hold = max(0, int(round((J["bride_go"] + shift) * fps)) - K // 2 - len(ch.R))
    for _ in range(n_hold):
        ch.R.append(FR.R_fk[NR - 1]); ch.r.append(FR.roots[NR - 1]); ch.src.append((FR, NR - 1))
    off3 = ch.foot(FR, NR - 1, s_sup) - ch.foot(FC, c0, s_sup)
    i0 = len(ch.R); pad = K // 2
    ch.free.update((j, s_lift) for j in range(i0 - pad, i0 + K + 1 + pad))
    for i in range(K + 1):                                         # 停住的最後一格 ↔ 82_08 起步
        u = i / K; w = u * u * (3 - 2 * u)
        ch.R.append({k: ch.slerp(FR.R_fk[NR - 1][k], FC.R_fk[c0 + i][k], w) for k in rig.keys})
        ch.r.append(FR.roots[NR - 1].lerp(FC.roots[c0 + i] + off3, w)); ch.src.append((FR, NR - 1) if w < 0.5 else (FC, c0 + i))
    sd = J["stop_side16"]
    jS = _stance_at(FS, sd, J["stop16_at"], fps, need) + lead
    st = sorted(r[0] for r in FC.contact_src[sd] if r[0] > c_go and r[1] - r[0] >= need)
    jC = st[0] + lead
    ch.add(FC, c0 + K + 1, jC, off3)
    off4 = ch.foot(FC, jC, sd, off3) - ch.foot(FS, jS, sd)
    ch.fade(FC, jC, off3, FS, jS, off4, K, free=_other(sd))
    ch.add(FS, jS + K + 1, len(FS.R_fk), off4)
    R_out, roots, contacts, extra = _finish(ns, ch, heading, fps)
    last = max(contacts[s][-1][0] for s in "LR")
    bs = J["bride_stop"]

    def lean(t):
        return (J["bride_lean"] * seg01(t, bs - 0.05, bs + 0.25) * (1 - seg01(t, t100 + 0.1, t100 + 0.6))
                + 8.0 * bump(t, t100 - 0.30, t100 - 0.05, t100 + 0.05, t100 + 0.3)           # 2.75～3.05 一起用力推
                - 6.0 * bump(t, bs - 0.40, bs - 0.15, bs - 0.10, bs + 0.05))                  # 煞車：急停前上身微後仰
    pv = roots[stop_r].copy()
    yw = C3.get("b_run_yaw", 0.0)

    def yaw(t):                                                   # 跑來時面向 heading＋yw（從他背後跑來），急停前 0.55 秒轉向 heading（面向他）
        return yw * (1 - seg01(t, bs - 0.55, bs))
    fn = _make_fn(ns, rig, R_out, roots, shift, fps, lean=lean, heading=heading, yaw=yaw, pivot=pv)
    fn.settle = round(last / fps - shift, 3); fn.contacts = contacts; fn.info = extra
    fn.joins = dict(run_stop=dict(stop_frame=C3_MOCAP["run"]["frames"][0] + stop_r, t=J["bride_stop"]),
                    start=dict(lift_frame=C3_MOCAP["start"]["frames"][0] + c_go, lift=s_lift, t_go=J["bride_go"]),
                    start_stop=dict(start_frame=C3_MOCAP["start"]["frames"][0] + jC, stop_frame=C3_MOCAP["stop"]["frames"][0] + jS),
                    start_t=round(-shift, 3))
    return fn


def _hip(fn, t, off):
    h = fn.fk(t)["Hips"]; return Vector((h.x + off.x, h.y + off.y, h.z))


def _rz_of(v):
    return math.degrees(math.atan2(v.x, -v.y))


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


# ───────────── 手掌貼表面（掌心中心落在表面、掌心朝表面、手指方向在切平面上） ─────────────
PALM = {}


def palm_geo(ns, side):
    """手掌取樣點（rest 時權重以 Hand 為主、在掌心那一側、手腕到指根之間的皮膚頂點）→ Hand 骨頭局部座標；中心、掌心法線（局部）"""
    key = (ns["WHO"], side)
    if key in PALM:
        return PALM[key]
    A = ns["ARM"]; body = bpy.data.objects[ns["WHO"] + "_Body"]; Bh = A.data.bones[f"J_Bip_{side}_Hand"]
    gi = body.vertex_groups[f"J_Bip_{side}_Hand"].index
    Mb = A.matrix_world.inverted() @ body.matrix_world
    h0 = Bh.head_local; ax = (Bh.tail_local - h0).normalized()
    mid1 = A.data.bones[f"J_Bip_{side}_Middle1"].head_local; Lp = (mid1 - h0).dot(ax)
    inv = Bh.matrix_local.inverted()
    pts, idx = [], []
    for v in body.data.vertices:
        w = next((g.weight for g in v.groups if g.group == gi), 0.0)
        if w < 0.5:
            continue
        p = Mb @ v.co; u = (p - h0).dot(ax)
        if 0.15 * Lp <= u <= 0.95 * Lp and p.z < h0.z - 0.004:          # T 姿勢掌心朝下（−Z）
            pts.append(inv @ p); idx.append(v.index)
    c = sum(pts, Vector()) / len(pts)
    n_l = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
    core = [i for i, p in enumerate(pts) if (p - c).length < 0.025]
    PALM[key] = dict(pts=pts, idx=idx, c=c, n=n_l, core=core)
    return PALM[key]


def palm_world(ns, side, which="c"):
    A = ns["ARM"]; pb = A.pose.bones[f"J_Bip_{side}_Hand"]; G = palm_geo(ns, side)
    M = A.matrix_world @ pb.matrix
    if which == "c":
        return M @ G["c"]
    return [M @ p for p in G["pts"]]


def _frame(y, n):
    """骨頭局部框架：Y＝骨頭方向、Z≈掌心法線（正交化）→ 3×3"""
    y = y.normalized(); z = (n - y * n.dot(y)).normalized(); x = y.cross(z)
    return Matrix((x, y, z)).transposed()


def _pole(S0, E0, W0, C0):
    """手肘方向點：原姿勢的手肘彎向（手臂快打直時這個方向不穩、一格會翻）＋往外（肩膀離胸口的水平方向）＋往下，三者合成，穩定"""
    lat = S0 - C0; lat.z = 0
    lat = lat.normalized() if lat.length > 1e-6 else Vector((1, 0, 0))
    v = (E0 - (S0 + W0) / 2) * 3.0 + lat * 0.5 + Vector((0, 0, -0.5))
    return E0 + v.normalized() * 0.3


def palm_place(ns, side, P, N, w, gap=0.003, iters=3):
    """把手掌放到表面點 P（外法線 N）：掌心中心＝P＋N×gap、掌心朝 −N、手指方向＝前臂方向投影到切平面。
    w＝權重（0＝原姿勢、1＝貼上）；手腕目標用 IK（手肘方向沿用原姿勢），再只轉手掌（face_palm split=0，手腕位置不動）"""
    if w <= 1e-3:
        return None
    A = ns["ARM"]; mw = A.matrix_world; G = palm_geo(ns, side)
    bpy.context.view_layer.update()
    pbu, pbl, pbh = (A.pose.bones[f"J_Bip_{side}_{n}"] for n in ("UpperArm", "LowerArm", "Hand"))
    if w < 0.999:
        # 貼上／放開的過渡：先完整貼上（w=1），再把三根骨頭的局部旋轉在原姿勢和貼上之間 slerp（逐格穩定；
        # 之前直接內插手腕目標＋face_palm 的轉動量，放開時手掌一格甩 90°）
        q0 = [pb.rotation_quaternion.copy() for pb in (pbu, pbl, pbh)]
        palm_place(ns, side, P, N, 1.0, gap, iters)
        for pb, qa in zip((pbu, pbl, pbh), q0):
            qb = pb.rotation_quaternion.copy()
            if qa.dot(qb) < 0:
                qb.negate()
            pb.rotation_quaternion = qa.slerp(qb, ease(w))
        bpy.context.view_layer.update()
        return (P + N * gap - palm_world(ns, side)).length
    S0 = mw @ pbu.head; E0 = mw @ pbl.head; W0 = mw @ pbh.head; d0 = (mw @ pbh.tail - W0).normalized()
    pole = _pole(S0, E0, W0, mw @ A.pose.bones["J_Bip_C_Chest"].head)
    Pc = P + N * gap; corr = Vector()
    n_bone = G["n"]
    for it in range(iters):
        E = mw @ pbl.head
        f = (Pc - E).normalized()
        d = f - N * f.dot(N)
        d = d.normalized() if d.length > 1e-4 else Vector((0, 0, 1))
        Rw = _frame(d, -N); Rl = _frame(Vector((0, 1, 0)), n_bone)
        c_off = Rw @ Rl.transposed() @ G["c"]
        Wc = Pc - c_off + corr
        W = W0.lerp(Wc, w); dd = d0.slerp(d, w) if d0.dot(d) > -0.99 else d
        ns["ik_arm"](A, side, W, pole, W + dd * 0.1)
        ns["face_palm"](A, side, mw.inverted().to_3x3() @ (-N), split=0.0, w=w)
        bpy.context.view_layer.update()
        if w < 0.999:
            break
        err = Pc - palm_world(ns, side)
        corr += err
        if err.length < 0.0015 and it >= 1:                       # 至少兩輪：手指方向要用 IK 之後的手肘重算
            break
    return (Pc - palm_world(ns, side)).length


# ───────────── 往右踏步轉身（重心移到支撐腳、另一腳踏出去；著地腳不動） ─────────────
def step_turn(ns, F, off, t0, c_to, rz_cam, blend, step_dur):
    """F＝真人片段（結尾站定）；off＝片段座標→場景；t0＝開始換姿勢（之後 blend 秒才踏第一步）；c_to＝轉完的站位中心；rz_cam＝最後面向。
    一律往右轉（順時針、rz 變小）。回傳 place(t)→(x, y, rz)、feet(t, place)→P['feet']、結束秒數、資訊"""
    A = ns["ARM"]; B = A.data.bones
    a0 = {s: B[f"J_Bip_{s}_Foot"].head_local.copy() for s in "LR"}
    r0 = {s: _rz_of(B[f"J_Bip_{s}_ToeBase"].head_local - B[f"J_Bip_{s}_Foot"].head_local) for s in "LR"}
    H = F.fk(t0); feet0 = {}
    for s in "LR":
        a = H[f"{s}_Foot"] + off; tv = (H[f"{s}_ToeBase"] + off) - a; tv.z = 0
        feet0[s] = (Vector((a.x, a.y, 0.0)), _rz_of(tv))
    yaws = [feet0[s][1] - r0[s] for s in "LR"]
    rz0 = math.degrees(math.atan2(sum(math.sin(math.radians(y)) for y in yaws), sum(math.cos(math.radians(y)) for y in yaws)))
    am = (a0["L"] + a0["R"]) / 2
    c0 = (feet0["L"][0] + feet0["R"][0]) / 2 - Matrix.Rotation(math.radians(rz0), 3, "Z") @ Vector((am.x, am.y, 0))
    c0.z = 0
    dl = -((rz0 - rz_cam) % 360.0)                                    # 順時針（往右）
    n = 2 if abs(dl) <= 45 else (3 if abs(dl) <= 125 else 4)
    th = [rz0 + dl * j / n for j in range(n + 1)]
    cs = [c0.lerp(Vector((c_to.x, c_to.y, 0)), j / n) for j in range(n + 1)]

    def foot_at(j, s):
        R = Matrix.Rotation(math.radians(th[j]), 3, "Z")
        return cs[j] + R @ Vector((a0[s].x, a0[s].y, 0)), th[j] + r0[s]
    moves = []; cur = {s: feet0[s] for s in "LR"}; ts = t0 + blend
    for j in range(1, n + 1):
        s = "R" if j % 2 == 1 else "L"
        moves.append((ts, ts + step_dur, s, cur[s], foot_at(j, s), j)); cur[s] = foot_at(j, s); ts += step_dur
    s_last = "L" if n % 2 == 1 else "R"
    moves.append((ts, ts + step_dur * 0.85, s_last, cur[s_last], foot_at(n, s_last), n)); ts += step_dur * 0.85
    t_end = ts

    def state(t):
        feet = dict(feet0); body_rz = rz0; c = c0.copy(); shift = Vector(); lift = {"L": 0.0, "R": 0.0}
        for (a, b, s, fa, fb, j) in moves:
            if t >= b:
                feet[s] = fb; body_rz = th[j]; c = cs[j].copy()
                continue
            if t <= a:
                break
            u = (t - a) / (b - a); e = u * u * (3 - 2 * u)
            pos = fa[0].lerp(fb[0], e); yw = fa[1] + _wrap(fb[1] - fa[1]) * e
            feet[s] = (pos, yw); lift[s] = 0.035 * math.sin(math.pi * u)
            body_rz = th[j - 1] + (th[j] - th[j - 1]) * e; c = cs[j - 1].lerp(cs[j], e)
            sup = feet[_other(s)][0]
            shift = (sup - (c + Matrix.Rotation(math.radians(body_rz), 3, "Z") @ Vector((am.x, am.y, 0)))) * (0.30 * math.sin(math.pi * min(1.0, u * 1.15)))
            shift.z = 0
            break
        return feet, body_rz, c + shift, lift

    def place(t):
        _, rz, c, _ = state(t); return (c.x, c.y, rz)

    def feet_spec(t, rz_arm=None):
        feet, rz, c, lift = state(t)
        if rz_arm is not None:                                          # 換姿勢淡入時骨架的朝向還在兩個姿勢之間：照實際朝向換算
            rz = rz_arm
        M = place_matrix(c.x, c.y, rz).inverted()
        out = {}
        for s in "LR":
            p = M @ Vector((feet[s][0].x, feet[s][0].y, 0.0))
            out[s] = (p.x - a0[s].x, p.y - a0[s].y, lift[s], 0.0, _wrap(feet[s][1] - rz - r0[s]), 0.0)
        return out
    info = dict(rz0=round(rz0, 1), turn_deg=round(dl, 1), steps=len(moves), t=(round(t0, 2), round(t_end, 2)),
                c0=[round(v, 3) for v in c0[:2]], c1=[round(v, 3) for v in cs[-1][:2]])
    return place, feet_spec, t_end, info


def v2_03c_setup():
    if V2S.get("03c"):
        return V2S["03c"]
    c = C3; t100 = c["t100"]; hd = c["heading"]; fps = 120.0
    for ns in (GR, B):
        if "mocap_action" not in ns:
            ns["use"]("mocap_retarget")
    FG = groom_chain(GR, hd)
    FB = bride_chain(B, c["b_heading"])
    kg = GR["BODY_S"]
    # ── 紅毯卷：推的時候跟著新郎雙手（手腕中點、0.1 秒平滑、只往前不往後）；推動後衝到最快時放手（t_rel），卷自己減速滾到 roll_end_y 停住
    hz = 60.0; ts = [i / hz for i in range(int(c["dur"] * hz) + 1)]
    FKs = [FG.fk(t) for t in ts]
    wy = GR["_gauss"]([0.5 * (H["L_Hand"].y + H["R_Hand"].y) for H in FKs], 0.1 * hz)
    wz = GR["_gauss"]([0.5 * (H["L_Hand"].z + H["R_Hand"].z) for H in FKs], 0.1 * hz)
    for i in range(1, len(wy)):
        wy[i] = max(wy[i], wy[i - 1])
    vel = [0.0] + [(wy[i] - wy[i - 1]) * hz for i in range(1, len(wy))]
    i_a, i_b = int((t100 + 0.4) * hz), int((t100 + 1.5) * hz)
    i_rel = max(range(i_a, i_b), key=lambda i: vel[i])
    t_rel = ts[i_rel]; v_rel = max(0.4, vel[i_rel])
    D_free = max(0.25, min(0.6, v_rel * 0.45)); T_free = 2 * D_free / v_rel
    a_nom = math.radians(50.0)

    def rr_of(yrel):                                               # 半徑（yrel＝離起點多遠）；先粗估，下面再用實際長度
        return c["r0"] - (c["r0"] - c["r1"]) * max(0.0, min(1.0, yrel / max(0.3, wy[i_rel] - wy[0] + D_free)))
    base = [wy[i] + rr_of(wy[i] - wy[0]) * math.cos(a_nom) + 0.03 for i in range(len(ts))]
    # 校準（片段座標、解析式，不擺姿勢）：每個時間點在「接觸點的弧面角度 a × 卷往前後挪 δ」裡挑：
    #   手腕往上翹（前臂和手掌方向的夾角）接近 ext_want、手臂伸展 ≤ 0.93（手肘保持微彎）、δ 越小越好
    x_off = CP["x"] - FG.fk(FG.t_strain)["Hips"].x
    Lr = {sd: ((GR["ARM"].data.bones[f"J_Bip_{sd}_LowerArm"].head_local - GR["ARM"].data.bones[f"J_Bip_{sd}_UpperArm"].head_local).length,
               (GR["ARM"].data.bones[f"J_Bip_{sd}_Hand"].head_local - GR["ARM"].data.bones[f"J_Bip_{sd}_LowerArm"].head_local).length) for sd in "LR"}
    PG = {sd: palm_geo(GR, sd) for sd in "LR"}
    Rl = {sd: _frame(Vector((0, 1, 0)), PG[sd]["n"]) for sd in "LR"}

    def arm_eval(sd, H, Pc, N):
        S = H[f"{sd}_UpperArm"]; E0 = H[f"{sd}_LowerArm"]; W0 = H[f"{sd}_Hand"]
        pole = _pole(S, E0, W0, H["Chest"])
        L1, L2 = Lr[sd]; E = E0; W = W0; dh = Vector((0, 0, 1))
        for _ in range(3):
            f = (Pc - E).normalized(); dh = f - N * f.dot(N)
            dh = dh.normalized() if dh.length > 1e-4 else Vector((0, 0, 1))
            W = Pc - (_frame(dh, -N) @ Rl[sd].transposed()) @ PG[sd]["c"]
            v = W - S; dd = max(1e-4, min(v.length, (L1 + L2) * 0.999)); dr = v.normalized()
            aa = math.acos(max(-1.0, min(1.0, (L1 * L1 + dd * dd - L2 * L2) / (2 * L1 * dd))))
            pp = (pole - S); pp = pp - dr * pp.dot(dr); pp = pp.normalized() if pp.length > 1e-6 else Vector((0, 0, -1))
            E = S + dr * math.cos(aa) * L1 + pp * math.sin(aa) * L1
        fa = (W - E).normalized()
        return math.degrees(fa.angle(dh)), (W - S).length / (L1 + L2)

    # 每個取樣時間點算每個 (a, δ) 的代價，再用動態規劃挑一條連續的路徑（相鄰兩點 a、δ 變化要付代價）：
    # 單點各自挑最小值時 a 會在 35°／80° 兩個解之間跳，平滑後落在中間、手腕反而彎 80～90°
    A_GRID = [15 + 5 * j for j in range(12)]; D_GRID = [-0.20 + 0.025 * j for j in range(11)]
    SS = [(a_deg, dl) for dl in D_GRID for a_deg in A_GRID]
    samp = [i for i in range(0, len(ts), 2) if ts[i] <= t_rel + 0.1]
    costs = []; infos = []
    for i in samp:
        H = FKs[i]; row = []; inf = []
        for a_deg, dl in SS:
            yc = base[i] + dl; r = rr_of(yc - base[0]); zc = CP["z0"] + r
            a = math.radians(a_deg); N = Vector((0, -math.cos(a), math.sin(a))); cost = (dl / 0.04) ** 2 * 0.5; info = []
            for sd in "LR":
                sx = -1 if sd == "L" else 1
                Pc = Vector((CP["x"] + sx * c["roll_x"] * kg - x_off, yc, zc)) + N * (r + 0.003)
                ext, stch = arm_eval(sd, H, Pc, N)
                cost += ((ext - c["ext_want"]) / 5.0) ** 2 + (max(0.0, stch - 0.93) / 0.01) ** 2; info.append((round(ext, 1), round(stch, 3)))
            row.append(cost); inf.append(info)
        costs.append(row); infos.append(inf)
    nS = len(SS); acc = list(costs[0]); back = []
    for k in range(1, len(samp)):
        nb = []; na = []
        for j, (aj, dj) in enumerate(SS):
            best = None
            for q, (aq, dq) in enumerate(SS):
                v = acc[q] + ((aj - aq) / 5.0) ** 2 * 2.0 + ((dj - dq) / 0.025) ** 2 * 2.0
                if best is None or v < best[0]:
                    best = (v, q)
            na.append(best[0] + costs[k][j]); nb.append(best[1])
        acc = na; back.append(nb)
    j = min(range(nS), key=lambda q: acc[q]); path = [j]
    for nb in reversed(back):
        j = nb[j]; path.append(j)
    path.reverse()
    a_raw = [SS[j][0] for j in path]; d_raw = [SS[j][1] for j in path]
    cal = [(round(ts[samp[k]], 2), a_raw[k], d_raw[k], infos[k][path[k]]) for k in range(len(samp))]
    while len(a_raw) * 2 < len(ts) + 2:
        a_raw.append(a_raw[-1]); d_raw.append(d_raw[-1])
    a_tab = GR["_gauss"]([a_raw[min(len(a_raw) - 1, i // 2)] for i in range(len(ts))], 0.15 * hz)
    d_tab = GR["_gauss"]([d_raw[min(len(d_raw) - 1, i // 2)] for i in range(len(ts))], 0.15 * hz)
    yc_ch = [base[i] + d_tab[i] for i in range(len(ts))]
    for i in range(1, len(yc_ch)):
        yc_ch[i] = max(yc_ch[i], yc_ch[i - 1])
    print("V2_03C_CAL", [x for x in cal[::6]], flush=True)
    y_end = c["roll_end_y"]
    dy = y_end - (yc_ch[i_rel] + D_free)
    offG = Vector((CP["x"] - FG.fk(FG.t_strain)["Hips"].x, dy, 0.0))
    y_start = yc_ch[0] + dy - c["carpet_back"]
    L_tot = y_end - y_start
    thick = math.pi * (c["r0"] ** 2 - c["r1"] ** 2) / max(1e-6, L_tot - c["carpet_back"])   # 開場時（已鋪 carpet_back）半徑＝r0

    def roll_r(y):
        Ld = y - (y_start + c["carpet_back"])
        return math.sqrt(max(c["r1"] ** 2, c["r0"] ** 2 - thick * Ld / math.pi))

    def roll_y(t):
        if t <= t_rel:
            x = max(0.0, min(len(ts) - 1.001, t * hz)); i = int(x); f = x - i
            return (yc_ch[i] * (1 - f) + yc_ch[i + 1] * f) + dy
        tau = min(t - t_rel, T_free); a_ = v_rel / T_free
        return yc_ch[i_rel] + dy + v_rel * tau - 0.5 * a_ * tau * tau

    ang = {}

    def roll_angle(t):                                             # 滾過的角度（往 +Y 滾＝繞 −X）
        k_ = int(round(t * 60))
        if k_ not in ang:
            a = 0.0; yp = roll_y(0.0)
            for j in range(1, k_ + 1):
                y = roll_y(j / 60.0); a -= (y - yp) / roll_r(y); yp = y
            ang[k_] = a
        return ang[k_]

    def roll_contact(t, sd):
        t = min(t, t_rel)                                          # 放手之後（權重淡出中）接觸點停在放手那一刻：卷滾走時手不去追、IK 不會一格翻
        y = roll_y(t)
        r = roll_r(y); x = max(0.0, min(len(ts) - 1.001, t * hz)); i = int(x)
        a = math.radians(a_tab[i]); Nn = Vector((0, -math.cos(a), math.sin(a)))
        sx = -1 if sd == "L" else 1
        C = Vector((CP["x"] + sx * c["roll_x"] * kg, y, CP["z0"] + r))
        return C + Nn * r, Nn

    def w_g(t):
        return 1.0 - seg01(t, t_rel, t_rel + 0.50)

    # ── 新娘的站位：t_b 時（兩人一起頂）在新郎骨盆正後方 b_back、往離鏡頭遠的一側挪 |b_depth|
    t_b = 2.80
    hg = _hip(FG, t_b, offG); hb = FB.fk(t_b)["Hips"]
    offB = Vector((hg.x + c["b_depth"] - hb.x, hg.y - c["b_back"] - hb.y, 0.0))

    def face_cam(p):
        v = Vector(c["cam"]) - Vector((p.x, p.y, 0)); return _rz_of(v)
    # ── 結尾：踏步轉向鏡頭（往右轉）；新娘轉完站在新郎左邊（從鏡頭看）b_final
    g_end = _hip(FG, 99.0, offG)
    Hg = FG.fk(99.0); g_c = (Hg["L_Foot"] + Hg["R_Foot"]) / 2 + offG; g_c.z = 0
    rz_g = face_cam(g_c)
    dcam = (Vector(c["cam"]) - g_c); dcam.z = 0; dcam.normalize()
    left = Vector((-dcam.y, dcam.x, 0)) * -1                       # 從鏡頭看的左邊（面向鏡頭的人的右手邊）
    b_c = g_c + left * c["b_final"]
    rz_b = face_cam(b_c)
    tg0 = FG.joins["end_t"] + 0.02; tb0 = c["b_turn_t"]                      # 新娘推完退一步、站著等他衝過去，b_turn_t 秒起踏步轉身、移到他左邊
    place_g, feet_g, tg1, ig = step_turn(GR, FG, offG, tg0, g_c, rz_g, c["turn_blend"], c["step_dur"])
    place_b, feet_b, tb1, ib = step_turn(B, FB, offB, tb0, b_c, rz_b, c["turn_blend"], c["step_dur"])
    # 揮手：轉身最後一步開始舉手（wave_arc 起手 1.0 秒）
    FWg = GR["wave_arc"]("both", hold=True, cycles=14, sh_up=c["g_sh_up"], sh_swing=c["g_sh_swing"])             # 肩胛多抬一點：第 4 輪量到脖子露出比待機長 7%（14° 時）
    FWb = B["wave_arc"]("both", hold=True, cycles=14, hz=1.3)
    tw_g = tg0 + c["turn_blend"] + 0.10; tw_b = tb0 + c["turn_blend"] + 0.30      # 第一步踏出去就開始舉手（只動手臂，和腳步同時）

    def g_pose(t):
        P = dict(FG(t)); r_ = P["root"]; P["root"] = (r_[0] + offG.x, r_[1] + offG.y, r_[2])
        if w_g(t) > 0.5:
            P["hands"] = ("open", "open")
        st_ = seg01(t, FG.t_strain - 0.2, FG.t_strain + 0.3) * (1 - seg01(t, t100 + 0.1, t100 + 0.6))
        P["face"] = {"Fcl_ALL_Fun": 0.45 * (1 - st_), "Fcl_EYE_Close": 0.5 * st_, "Fcl_MTH_E": 0.15 + 0.45 * st_}
        P["abs"] = True
        return P

    kb = B["BODY_S"]
    b_in = FB.joins["start_t"]
    hb2 = FB.fk(t_b)["Hips"] + offB; step_dir = hg - hb2; step_dir.z = 0; step_dir.normalize()
    face_dir = Vector((math.sin(math.radians(c["b_heading"])), -math.cos(math.radians(c["b_heading"])), 0))

    def b_push(t):
        return 0.05 * bump(t, t100 - 0.30, t100 - 0.05, t100 + 0.05, t100 + 0.35)

    def b_si(t):
        return c["b_step_in"] * (seg01(t, 2.45, 2.75) - seg01(t, 3.35, 3.75))
    # 靠近／退開用兩小步（先靠近他那隻腳、另一隻跟上；退開反過來），腳在蓬裙裡也照實踩：每隻腳的位移 f(t)，和骨盆位移的差用腿 IK 補
    Hb = FB.fk(2.45); lead = min("LR", key=lambda sd_: ((Hb[f"{sd_}_Foot"] + offB) - hg).xy.length); trail = _other(lead)

    def b_feet_corr(t):
        f = {lead: c["b_step_in"] * (seg01(t, 2.45, 2.62) - seg01(t, 3.55, 3.75)),
             trail: c["b_step_in"] * (seg01(t, 2.58, 2.75) - seg01(t, 3.35, 3.55))}
        lift = {lead: 0.03 * (bump(t, 2.45, 2.52, 2.55, 2.62) + bump(t, 3.55, 3.62, 3.68, 3.75)),
                trail: 0.03 * (bump(t, 2.58, 2.65, 2.68, 2.75) + bump(t, 3.35, 3.42, 3.48, 3.55))}
        out = {}
        for sd_ in "LR":
            v = step_dir * (f[sd_] - b_si(t)) - face_dir * b_push(t); v.z = lift[sd_]
            out[sd_] = v
        return out

    def w_b_on(t):                                                   # 她的手在他背上：2.45～2.97 貼上、3.25～3.75 他衝出去時放開（時間固定，不再用「構不構得到」逐格切換：那樣一格會甩 100°）
        return seg01(t, 2.45, 2.97) * (1 - seg01(t, C3["t100"] + 0.20, C3["t100"] + 0.70))

    def b_pose(t):
        P = dict(FB(t)); r_ = P["root"]
        push = b_push(t)                                              # 用力推：骨盆往前 5 cm（腳不動、上身壓過去）
        # 站定後往他靠近 b_step_in（2.45～2.75，推完 3.35～3.75 退回；腳在蓬裙裡看不到）＋用力推時骨盆往前（推的方向＝面向）
        si = b_si(t)
        P["root"] = (r_[0] + offB.x + step_dir.x * si + face_dir.x * push, r_[1] + offB.y + step_dir.y * si + face_dir.y * push, r_[2])
        if t < b_in:                                                 # 開始跑之前還在畫面外（往後挪到鏡頭看不到的地方）
            P["root"] = (P["root"][0], P["root"][1] - 30.0, P["root"][2])
        if w_b_on(t) > 0.5 and t < t100 + 0.6:
            P["hands"] = ("open", "open")
        st_ = seg01(t, 2.45, 2.7) * (1 - seg01(t, t100 + 0.1, t100 + 0.6))
        P["face"] = {"Fcl_ALL_Fun": 0.55 * (1 - st_), "Fcl_EYE_Close": 0.45 * st_, "Fcl_MTH_E": 0.15 + 0.4 * st_}
        P["abs"] = True
        return P

    def turn_wave(ns, place, feet, FW, t_w, t_seg0, male):
        def spec(tl):
            t = t_seg0 + tl
            P = dict(FW(max(0.0, min(0.9999, (t - t_w) / FW.dur))))
            P["feet"] = feet(t)
            return ns["posture"](P) if male else P
        return spec

    AG = Actor2(GR, [(0.0, tg0, g_pose, 0.0), (tg0, 12.0, turn_wave(GR, place_g, feet_g, FWg, tw_g, tg0, True), c["turn_blend"])], place_g)
    AB = Actor2(B, [(0.0, tb0, b_pose, 0.0), (tb0, 12.0, turn_wave(B, place_b, feet_b, FWb, tw_b, tb0, False), c["turn_blend"])], place_b)
    # ── 文字牆：前三面在紅毯遠側，位置＝紅毯卷在 trig 秒時的位置；第三面在卡住前；「婚禮」在拱門左柱內側
    # 推的那 2 秒紅毯卷只前進約 0.5 m（小步推），三面牆左右只能隔約 0.2 m → 一面比一面高（墊高 lift），從鏡頭看是往右上的階梯，字不互相擋
    y1 = roll_y(0.15); y3 = roll_y(FG.t_strain + 0.05); y2 = 0.5 * (y1 + y3)
    walls = []
    # 推的那 2 秒紅毯卷只前進約 0.4 m（小步推），三面牆若照卷的位置排，左右只隔 0.2 m、字擠在一起看不清 →
    # 改成紅毯遠側一排（x=wall_x），左右隔 wall_gap、架高到新娘頭頂以上（推的那段她站在遠側），從鏡頭看由左到右＝相遇→交往→求婚，
    # 紅毯卷推到 lit_at 的時間（0.15、1.65、2.17 秒：卷經過三個等分點）依序亮；中間那面對齊卷在 1.65 秒的位置
    y1 = roll_y(0.15); y3 = roll_y(FG.t_strain + 0.05); y2 = 0.5 * (y1 + y3)
    walls = []
    for txt, y in (("相遇", y2 - c["wall_gap"]), ("交往", y2), ("求婚", y2 + c["wall_gap"])):
        p = Vector((c["wall_x"], y, 0)); walls.append(dict(text=txt, pos=(p.x, p.y), rz=face_cam(p), kind="small", lift=c["wall_lift"]))
    pw = Vector((c["wed_pos"][0], c["wed_pos"][1], 0))
    walls.append(dict(text="婚禮", sub="2026.12.12", pos=(pw.x, pw.y), rz=face_cam(pw), kind="big"))

    def t_reach(y):
        for i in range(int(c["dur"] * 60) + 1):
            if roll_y(i / 60.0) >= y - 1e-4:
                return i / 60.0
        return 99.0
    lit_t = [t_reach(y) for y in (y1, y2, y3)] + [t_rel + T_free - 0.05]
    st = dict(b_feet_corr=b_feet_corr, feet_g=feet_g, feet_b=feet_b, FG=FG, FB=FB, offG=offG, offB=offB, roll_y=roll_y, roll_r=roll_r, roll_angle=roll_angle, roll_contact=roll_contact, w_g=w_g,
              w_b_on=w_b_on, y_start=y_start, y_end=y_end, walls=walls, lit_t=lit_t, AG=AG, AB=AB, turn_g=(tg0, tg1), turn_b=(tb0, tb1),
              t_rel=t_rel, T_free=T_free, g_c=g_c, b_c=b_c, a_tab=a_tab, tw=(tw_g, tw_b), place_g=place_g, place_b=place_b)
    print("V2_03C_SETUP groom", FG.joins, "settle", FG.settle, "stride", FG.info.get("stride"), "bride", FB.joins, "settle", FB.settle,
          "carpet", round(y_start, 3), "→", round(y_end, 3), "t_rel", round(t_rel, 3), "v_rel", round(v_rel, 2), "D_free", round(D_free, 2),
          "T_free", round(T_free, 2), "r", [round(roll_r(roll_y(t)), 3) for t in (0, 2.0, 3.05, 5.0)],
          "a_deg", [round(a_tab[int(t * hz)], 1) for t in (0, 1, 2, 2.5, 3, 3.5, 4)],
          "groom start", [round(v, 3) for v in _hip(FG, 0.0, offG)], "end", [round(v, 3) for v in g_end], "turn", ig,
          "bride start", [round(v, 3) for v in _hip(FB, 0.0, offB)], "end", [round(v, 3) for v in _hip(FB, 99.0, offB)], "turn", ib,
          "walls", [(w["text"], [round(v, 2) for v in w["pos"]], round(w["rz"], 1)) for w in walls], "lit", [round(x, 2) for x in lit_t],
          "wave_t", (round(tw_g, 2), round(tw_b, 2)), "info", FG.info.get("knee_straight"), FB.info.get("knee_straight"), flush=True)
    V2S["03c"] = st
    SHOTS["v2_03c"]["actors"] = [AG, AB]
    SHOTS["v2_03c"]["qa_skip"] = [(0.0, b_in + 0.1)]
    return st


def v2_03c_build():
    need_garden()
    st = v2_03c_setup()
    col = coll_new("V2_Carpet", v2_coll())
    if "CP_Flat" not in bpy.data.objects or "CP_Wall0" not in bpy.data.objects:
        cp_build(col, st["y_start"], st["walls"])


def v2_03c_petals(i, rnd):
    st = V2S["03c"]; y_end = st["y_end"]; t_stop = st["t_rel"] + st["T_free"]
    if i < 60:                                                   # 紅毯卷停在拱門下時迸出的花瓣
        cc = Vector((CP["x"], y_end, 0.4))
        a = rnd.uniform(0, 2 * math.pi); s_ = rnd.uniform(0.5, 1.4)
        return (t_stop - 0.15 + rnd.uniform(0, 0.12), cc, (math.cos(a) * s_ * 0.6, math.sin(a) * s_ * 0.6, rnd.uniform(0.8, 2.0)))
    t0 = C3["t100"] + rnd.uniform(0.1, 1.8)
    return (t0, (rnd.uniform(-1.2, 1.4), rnd.uniform(st["y_start"] + 0.8, y_end + 0.6), rnd.uniform(2.6, 3.4)), (0, 0, 0))


def v2_03c_hands(t):
    """擺完兩人之後：新郎雙手貼紅毯卷、新娘雙手貼新郎背（每格；回傳掌心中心誤差 m）"""
    st = V2S["03c"]; out = {}
    w = st["w_g"](t)
    if w > 1e-3:
        for sd in "LR":
            P, N = st["roll_contact"](t, sd)
            out["g" + sd] = palm_place(GR, sd, P, N, w)
    out["skirt_squash"] = skirt_squash(t)
    # 新娘靠近／推／退開（2.45～3.75）：腳照小步走，不跟著骨盆滑
    if 2.44 <= t <= 3.76:
        corr = st["b_feet_corr"](t)
        if any(v.length > 1e-5 for v in corr.values()):
            leg_shift(B, corr)
    # 轉身開頭換姿勢的那 turn_blend 秒：兩個姿勢的腳位置相同，但淡入時骨盆在兩個姿勢之間內插，腳會滑 → 腳鎖回踏步轉身算好的位置
    for ns_, (t0_, _), feet_, place_ in ((GR, st["turn_g"], st["feet_g"], st["place_g"]), (B, st["turn_b"], st["feet_b"], st["place_b"])):
        if t0_ <= t <= t0_ + C3["turn_blend"]:
            pl = place_(t); rz_a = math.degrees(ns_["ARM"].rotation_euler.z)
            ns_["plant_feet_at"](ns_["ARM"], feet_(t, rz_a), place_matrix(pl[0], pl[1], rz_a))
    wb = st["w_b_on"](t)
    if wb > 1e-3 and t < C3["t100"] + 0.70:                         # 推完放開後不再碰他（她之後走到他旁邊時手會再構得到）
        A = GR["ARM"]; bpy.context.view_layer.update()
        BA = B["ARM"]
        for sd in "LR":
            P, N = back_point(sd)
            S_ = BA.matrix_world @ BA.pose.bones[f"J_Bip_{sd}_UpperArm"].head
            Lr = arm_len(B, sd)
            reach = (P - S_).length / Lr
            wr = wb
            out["b" + sd] = palm_place(B, sd, P, N, wr, gap=0.006)
            out["b" + sd + "_reach"] = round(reach, 3)
    return out


def leg_shift(ns, corr):
    """每隻腳的腳踝目標＝目前的位置＋corr[side]（世界向量）；腳掌朝向不變（平貼）、膝蓋朝腳尖前上方"""
    A = ns["ARM"]; mw = A.matrix_world; bpy.context.view_layer.update(); Bn = A.data.bones
    for sd, v in corr.items():
        pb = A.pose.bones[f"J_Bip_{sd}_Foot"]; an = mw @ pb.head; toe = mw @ A.pose.bones[f"J_Bip_{sd}_ToeBase"].head
        fw = toe - an; fw.z = 0; fw = fw.normalized() if fw.length > 1e-6 else Vector((0, 1, 0))
        r0 = _rz_of(Bn[f"J_Bip_{sd}_ToeBase"].head_local - Bn[f"J_Bip_{sd}_Foot"].head_local)
        yaw = _wrap(_rz_of(fw) - math.degrees(A.rotation_euler.z) - r0)
        tg = an + v
        ns["ik_leg"](A, sd, tg, tg + fw * 0.6 + Vector((0, 0, 0.35)), 0.0, yaw, 0.0)


def skirt_squash(t):
    """新娘靠到新郎旁邊推他時，蓬裙下擺朝他那一側被壓扁（裙擺骨頭 Skirt_Sway 在她的左右／前後兩軸縮放；下擺權重 0.99、腰部 0）：
    快速預覽不跑裙擺物理，不壓的話下擺（半徑約 0.6～0.7 m）一定穿過他的腳和褲管。2.30～2.55 壓；離他 1.25 m 以上不壓；5.2～5.7 放回"""
    BA = B["ARM"]; pb = BA.pose.bones["Skirt_Sway"]
    w = seg01(t, 2.30, 2.55) * (1 - seg01(t, 5.2, 5.7))
    if w <= 1e-3:
        pb.scale = (1, 1, 1); return 0.0
    bpy.context.view_layer.update()
    A = GR["ARM"]; mw = A.matrix_world
    g = mw @ A.pose.bones["J_Bip_C_Hips"].head; h = BA.matrix_world @ BA.pose.bones["J_Bip_C_Hips"].head
    d = g - h; d.z = 0; dist = d.length; d.normalize()
    w *= max(0.0, min(1.0, (0.88 - dist) / 0.15))                  # 骨盆相距 0.88 m 以上就不壓（推的時候約 0.6 m；最後並排 0.9 m 不壓）
    if w <= 1e-3:
        pb.scale = (1, 1, 1); return 0.0
    Mw = (BA.matrix_world @ pb.matrix).to_3x3()
    cx = abs(d.dot(Mw.col[0].normalized())); cz = abs(d.dot(Mw.col[2].normalized()))
    s_ = 1 - (1 - C3["skirt_squash"]) * w
    pb.scale = (1 - (1 - s_) * cx * cx, 1, 1 - (1 - s_) * cz * cz)
    return round(s_, 3)


_ARML = {}


def arm_len(ns, sd):
    k = (ns["WHO"], sd)
    if k not in _ARML:
        Bn = ns["ARM"].data.bones
        _ARML[k] = (Bn[f"J_Bip_{sd}_LowerArm"].head_local - Bn[f"J_Bip_{sd}_UpperArm"].head_local).length + \
                   (Bn[f"J_Bip_{sd}_Hand"].head_local - Bn[f"J_Bip_{sd}_LowerArm"].head_local).length + 0.06
    return _ARML[k]


_BACK = {}


def back_points():
    """新郎外套背後腰上方的兩個貼點（rest：脊椎骨頭往上 0.05、左右 ±0.085×體型、外套最後面的頂點）→ Spine 骨頭局部座標＋法線"""
    if _BACK:
        return _BACK
    A = GR["ARM"]; jk = bpy.data.objects[GR["WHO"] + "_Cos_Jacket"]; kg = GR["BODY_S"]
    Mb = A.matrix_world.inverted() @ jk.matrix_world; Bs = A.data.bones["J_Bip_C_Spine"]; inv = Bs.matrix_local.inverted()
    sp = Bs.head_local; ch = A.data.bones["J_Bip_C_Chest"].head_local
    z0 = sp.z + 0.35 * (ch.z - sp.z)
    vs = [(Mb @ v.co, (Mb.to_3x3() @ v.normal).normalized()) for v in jk.data.vertices]
    # 新娘站在他左邊（蓬裙不碰他的腳和腿）推：她的左手貼他左後側偏上、右手貼他左後腰；rest：新郎左手在 +X、背在 +Y
    for sd, (px, dz_, dv) in (("L", (0.17, 0.16, Vector((1.0, 0.2, 0)))), ("R", (0.16, 0.03, Vector((0.95, 0.35, 0))))):
        cand = [(p, n) for p, n in vs if abs(p.x - px * kg) < 0.02 and abs(p.z - (z0 + dz_)) < 0.02 and n.dot(dv) > 0.3]
        p, n = max(cand, key=lambda q: q[0].dot(dv))
        _BACK[sd] = (inv @ p, (inv.to_3x3() @ n).normalized())
    return _BACK


def back_point(sd):
    A = GR["ARM"]; pb = A.pose.bones["J_Bip_C_Spine"]; M = A.matrix_world @ pb.matrix
    p, n = back_points()[sd]
    return M @ p, (M.to_3x3() @ n).normalized()


def v2_03c_frame(t, props=True, cast=True, cam=True):
    st = v2_03c_setup(); c = C3
    if cast:
        st["AG"].pose(t); st["AB"].pose(t)
        st["last_hands"] = v2_03c_hands(t)
    if props:
        garden_parts(()); v2_parts(("V2_Carpet",))
        y = st["roll_y"](t)
        cp_update(y, st["roll_r"](y), st["roll_angle"](t), 0.0)
        for i, tl in enumerate(st["lit_t"]):
            cp_light(i, seg01(t, tl, tl + 0.25))
        petals_update(t, v2_03c_petals)
    if cam:
        look(Vector(c["cam"]), Vector(c["aim"]), c["lens"])


SHOTS["v2_03c"] = dict(set="Set_Garden", cast=True, t0=0.0, dur=C3["dur"], tail=0.0, build=v2_03c_build, frame=v2_03c_frame,
                       actors=[], qa_skip=[], stills=[0.5, 1.5, 2.3, 2.85, 3.3, 4.0, 5.2, 7.0])
