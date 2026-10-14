# ⑤ 路人甲闖進合照（9 秒）。2026-10-10 Mixamo 版第 1 關（骨骼）。
# 站位、鏡頭照現行 v2_05（shots_v2.py 的 V2_05、shots_garden.py 的 G05／B05／OC）：
#   新郎 (−0.42, 0.30)、新娘 (0.40, 0.30)，面向前景老相機 OC (−2.05, −2.35)（face_to：新郎 −31.6°、新娘 −42.8°）；
#   路人甲從畫面右緣外和畫面平行地走進來，停在 (−0.50, −2.66)、面向新人 170°，舉手機拍照 → 尷尬鞠躬 → 摸頭 → 轉身往右走出去。
#   鏡頭 (−0.10, −6.00, 2.00) 看 (−1.00, 0.30, 1.20)、45 mm（0.4～2.4 秒拉焦：老相機 → 新人）。
# Mixamo 的節奏比舊版程式動作慢，路人甲整段提早約 1.5 秒出場（劇情順序不變）；動作本身不改。
import math
from mathutils import Quaternion

OC = (-2.05, -2.35)
G05, B05 = (-0.42, 0.30), (0.40, 0.30)
P_STOP, P_FACE = (-0.50, -2.66), 170.0


def face_to(p, q):
    return math.degrees(math.atan2(q[0] - p[0], -(q[1] - p[1])))


# ════════ 第 2 關「正式版骨骼」的微調（FINAL=1 才套；2026-10-10）════════
FINAL = OPT.get("FINAL") == "1"
OC_LENS = (-2.05, -2.35, 1.31)         # 前景老相機鏡頭（新人一開始看的地方）
FPS_ = 30


def win(t, a, b, c, d):
    """權重：a 之前 0、a→b 漸入、b～c 為 1、c→d 漸出（smoothstep）"""
    def sm(x):
        x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
    if t <= a or t >= d:
        return 0.0
    if t < b:
        return sm((t - a) / max(1e-6, b - a))
    if t <= c:
        return 1.0
    return 1.0 - sm((t - c) / max(1e-6, d - c))


def sm_(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def spline(t, P):
    """[(秒, 點)…] 平順曲線（Catmull-Rom 切線＋Hermite）：經過每個點、中間不停；頭尾和「相鄰兩點一樣」（停住）切線為 0"""
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
            return p0 * (2 * u ** 3 - 3 * u ** 2 + 1) + tan(i) * ((u ** 3 - 2 * u ** 2 + u) * dt) + p1 * (-2 * u ** 3 + 3 * u ** 2) + tan(i + 1) * ((u ** 3 - u ** 2) * dt)
    return P[-1][1].copy()


def frame_of(t):
    return max(0, int(round(t * FPS_)))


def passerby_head(t):
    P = BUILT["passerby"]; f = min(len(P) - 1, frame_of(t))
    return P[f]["J_Bip_C_Head"] + Vector((0, 0, 0.06))


def look_target(t, t_turn):
    """一開始看老相機，t_turn 起 0.7 秒轉去看路人甲（他走進畫面後）"""
    u = win(t, t_turn, t_turn + 0.7, 99, 100)
    return Vector(OC_LENS).lerp(passerby_head(t), u)


CROWN_UP, CROWN_BACK = 0.209, 0.012       # 路人甲頭髮最高點相對頭骨（passerby_costume.blend 量的，2026-10-11）
T_SEE_G = 2.4          # 路人甲約 2.0 秒走進畫面右緣，新郎 2.4 秒才轉頭（舊版：走進畫面後才轉）
T_SEE_B = T_SEE_G + 0.15


def groom_mod():
    G = tgt("groom")

    def mod(t, R, h):
        R = breathe(G, R, h, t)                                              # 呼吸：擺拍、等點頭那兩段原片全身不動 1.5 秒，像定格（第 3 關自我審查）
        R = gesture(G, R, "R", "peace", w=win(t, -1, 0, 3.3, 3.7))          # 0～3.4 秒右手比 YA，手放下時收掉
        # 2026-10-11 第 3 關回饋「新郎的手變異常」（7.0 秒）：近照看出兩件事——
        #   原片手指套到 VRoid 上變成食指往前伸、拇指翹開 → 手放下後兩手都換成自然下垂的手指（relaxed）；
        #   手臂垂得太貼身，手腕插進外套下襬（外套網格出現破裂紋）→ 手放下後兩隻上臂各往外張 8°
        down = win(t, 3.5, 3.9, 99, 100)
        R = gesture(G, R, "L", "relaxed", w=1.0)
        R = gesture(G, R, "R", "relaxed", w=down)
        if down > 0:
            Hd = G.fk(R, h)
            lft = Hd["J_Bip_L_UpperLeg"] - Hd["J_Bip_R_UpperLeg"]; lft.z = 0; lft.normalize()
            fwd = Vector((lft.y, -lft.x, 0))
            for s_, sg in (("L", 1.0), ("R", -1.0)):
                R = rotate_subtree(G, R, f"J_Bip_{s_}_UpperArm", Quaternion(fwd, math.radians(8.0 * sg * down)))
        # 2026-10-11 第 3 關第 2 輪回饋「新郎到手放下的時候，他的左手手掌方向不正確，是往外凹」：原片手腕往手背折、掌心朝外 →
        #   垂下的手手腕打直（手掌順著前臂、微微往前 8°）、掌心朝大腿（身體內側）。左手整段、右手放下後
        Hd = G.fk(R, h)
        lft = Hd["J_Bip_L_UpperLeg"] - Hd["J_Bip_R_UpperLeg"]; lft.z = 0; lft.normalize()
        fwd = Vector((lft.y, -lft.x, 0))
        for s_, sg, wp in (("L", 1.0, 1.0), ("R", -1.0, down)):
            if wp <= 0:
                continue
            H2 = G.fk(R, h)
            fa = (H2[f"J_Bip_{s_}_Hand"] - H2[f"J_Bip_{s_}_LowerArm"]).normalized()
            cur = (H2[f"J_Bip_{s_}_Middle1"] - H2[f"J_Bip_{s_}_Hand"]).normalized()
            want = (fa + fwd * 0.14).normalized()
            R = aim_hand(G, R, h, s_, cur.lerp(want, wp), palm=(-lft * sg), palm_w=wp)
        R = look_at(G, R, h, look_target(t, T_SEE_G), split=(0.15, 0.25, 0.60))
        return R
    return mod


def bride_mod():
    B = tgt("bride"); up = Vector((0, 0, 1))

    def mod(t, R, h):
        Hd = B.fk(R, h)
        left = Hd["J_Bip_L_UpperLeg"] - Hd["J_Bip_R_UpperLeg"]; left.z = 0; left.normalize()
        fwd = Vector((left.y, -left.x, 0))
        hip = Hd["J_Bip_C_Hips"]
        center = Vector((hip.x, hip.y, hip.z)) + fwd * 0.24 + up * 0.10           # 捧花：雙手在腰前、肚臍高度
        for s_, sg in (("L", 1.0), ("R", -1.0)):
            wrist = center + left * (sg * 0.05) + up * (0.02 * sg)               # 兩手一上一下握花莖
            R = arm_ik(B, R, h, s_, wrist, left * sg + up * (-0.4))
            R = aim_hand(B, R, h, s_, (fwd * 0.5 - left * sg).normalized(), palm=(-left * sg + up * 0.3).normalized())
            R = gesture(B, R, s_, "grip")
        R = look_at(B, R, h, look_target(t, T_SEE_B), split=(0.15, 0.25, 0.60))    # 抬頭（原片低頭看手機）、跟著看路人甲
        return R
    return mod


def passerby_mod():
    P = tgt("passerby"); up = Vector((0, 0, 1))

    def chest_hold(Hd, R, sg):
        """兩手拿著手機在胸前（跟著上胸骨頭走，鞠躬時手跟著身體一起彎）：上胸往前 22 cm、往下 14 cm、兩手各往外 5 cm"""
        q = R["J_Bip_C_UpperChest"] @ P.rest_q["J_Bip_C_UpperChest"].inverted()
        f2 = q @ Vector((0, -1, 0)); u2 = q @ Vector((0, 0, 1)); l2 = q @ Vector((1, 0, 0))
        return Hd["J_Bip_C_UpperChest"] + f2 * 0.22 - u2 * 0.14 + l2 * (sg * 0.05), f2, u2, l2

    def hold_hand(R, h, s_, sg, goal, f2, u2, l2, w):
        """手（掌心中點）到 goal：手指往前、往中間，掌心朝上偏內（托著手機）"""
        H = P.fk(R, h); start = H[f"J_Bip_{s_}_Hand"]; pm = (start + H[f"J_Bip_{s_}_Middle1"]) * 0.5
        want = pm.lerp(goal, w); target = start + (want - pm); R0 = R
        for _ in range(3):
            R = arm_ik(P, R0, h, s_, target, l2 * sg - u2 * 0.6 - f2 * 0.2)
            H2 = P.fk(R, h)
            cur = (H2[f"J_Bip_{s_}_Middle1"] - H2[f"J_Bip_{s_}_Hand"]).normalized()
            R = aim_hand(P, R, h, s_, cur.lerp((f2 * 0.8 - l2 * sg * 0.45).normalized(), w), palm=(u2 * 0.7 - l2 * sg * 0.5).normalized(), palm_w=w)
            H3 = P.fk(R, h); p3 = (H3[f"J_Bip_{s_}_Hand"] + H3[f"J_Bip_{s_}_Middle1"]) * 0.5
            target = target + (want - p3)
        return R

    def mod(t, R, h):
        Hd = P.fk(R, h)
        left = Hd["J_Bip_L_UpperLeg"] - Hd["J_Bip_R_UpperLeg"]; left.z = 0; left.normalize()
        fwd = Vector((left.y, -left.x, 0))
        # 0) 2026-10-11 第 3 關第 2 輪回饋「尷尬鞠躬的時候肩膀會突然塌下來」：以前拍完照（5.25～5.6 秒）手一下子放回原片垂下，剛好接鞠躬，
        #    看起來像肩膀塌掉 → 拍完照兩手拿著手機收到胸前、鞠躬時手跟著身體一起彎；右手 6.2 秒去摸頭，左手拿著手機到轉身前
        for s_, sg, wh in (("R", -1.0, win(t, 4.6, 5.0, 6.2, 6.35)), ("L", 1.0, win(t, 4.6, 5.0, 7.5, 7.85))):
            if wh > 0:
                Hd = P.fk(R, h)
                g_, f2, u2, l2 = chest_hold(Hd, R, sg)
                R = hold_hand(R, h, s_, sg, g_, f2, u2, l2, wh)
        Hd = P.fk(R, h)
        head = Hd["J_Bip_C_Head"]
        w = win(t, 4.45, 4.85, 5.25, 5.6)                                        # 舉手機到眼前拍照（4.85～5.25）
        if w > 0:
            for s_, sg in (("L", 1.0), ("R", -1.0)):
                start = Hd[f"J_Bip_{s_}_Hand"]
                goal = head + fwd * 0.30 + left * (sg * 0.07) + up * (-0.02)
                R = arm_ik(P, R, h, s_, start.lerp(goal, w), left * sg + up * (-0.5))
                # 2026-10-11 第 3 關自我審查：手掌方向以前一開始就 100% 朝上（手臂才剛要舉），手腕往後折 133°、手跳一下 → 跟著 w 漸進
                H2 = P.fk(R, h)
                cur = (H2[f"J_Bip_{s_}_Middle1"] - H2[f"J_Bip_{s_}_Hand"]).normalized()
                R = aim_hand(P, R, h, s_, cur.lerp((up * 0.7 - left * sg * 0.3).normalized(), w), palm=(fwd * -1.0), palm_w=w)
        # 右手摸後腦（尷尬抓頭）——第 3 關回饋「舉手的手勢不正確」「手跑到頭的裡面」、第 2 輪「摸頭的手居然還會比 1，應該是手掌摸頭」
        #   「轉身的時候手都變形」改：從胸前拿手機的位置 → 臉前 → 耳邊 → 後腦勺（頭髮最高點往後 7 cm），掌心貼頭髮、四指併攏微彎（不再伸出食指），
        #   前後搓兩三下 → 7.3 秒離開頭、7.65 秒放到身側；7.5 秒才開始轉身（轉身前手已經放下，不會邊轉邊拉手）
        w = win(t, 6.15, 6.3, 7.68, 7.92)
        if w > 0:
            Hd = P.fk(R, h)
            rgt = -left
            sh = Hd["J_Bip_R_UpperArm"]
            crown = head + up * CROWN_UP - fwd * CROWN_BACK
            back = crown - fwd * 0.07 - up * 0.035                              # 後腦勺上方（頭頂往後 7 cm、往下 3.5 cm）
            nrm = (back - (head + up * 0.10)).normalized()                       # 頭髮表面往外的方向（從頭的中心往外）
            rub = (fwd * 0.012) * math.sin(2 * math.pi * 3.0 * t)                # 前後搓兩三下
            ear = head + rgt * 0.15 + fwd * 0.05 + up * 0.08
            hold_r = chest_hold(Hd, R, -1.0)[0]
            pts = [(6.25, hold_r),                                               # 胸前拿手機的位置（接上一段）
                   (6.55, head + fwd * 0.17 - up * 0.24 + rgt * 0.05),           # 臉前下方（貼近身體，不往前伸）
                   (6.8, ear), (7.0, back + nrm * 0.01), (7.25, back + nrm * 0.01),
                   (7.47, ear - up * 0.08 + fwd * 0.02), (7.8, sh + fwd * 0.05 + rgt * 0.08 - up * 0.45)]   # 放下：經耳邊、放到身側
            raw_palm = (Hd["J_Bip_R_Hand"] + Hd["J_Bip_R_Middle1"]) * 0.5
            # 第 2 輪回饋「路人甲的動作可以再調整細緻？」：以前每兩點之間各自 smoothstep，手到每個點都停一下（一頓一頓、加速度 126 m/s²）
            #   → 平順曲線（經過每個點、中間不停；只有在後腦勺搓的那段停住）
            goal = spline(t, pts)
            if 7.0 <= t <= 7.25:
                goal = goal + rub * sm_(min(t - 7.0, 7.25 - t) / 0.06)
            t0_, t1_ = Hd["J_Bip_C_Hips"] + up * 0.05, Hd["J_Bip_C_UpperChest"] + up * 0.06   # 身體近似成膠囊：掌心至少離脊椎線 17 cm
            ax_ = (t1_ - t0_); L_ = ax_.length; ax_ = ax_ / max(1e-6, L_)
            k_ = (goal - t0_).dot(ax_); near = t0_ + ax_ * max(0.0, min(L_, k_))
            if (goal - near).length < 0.17:
                # 第 2 輪自我審查：以前一律只往側面推（拿掉沿脊椎的分量），手經過胸口頂端上方時高度被壓到胸口頂端、離開後又跳回去（6.67 秒一格跳 12 cm）
                #   → 膠囊兩端是圓頂：在兩端外面時從端點往外推（保留高度）
                dv = goal - near
                if 0.0 < k_ < L_:
                    dv = dv - ax_ * dv.dot(ax_)
                goal = near + (dv.normalized() if dv.length > 1e-6 else fwd) * 0.17
            hc = head + up * 0.10                                                # 頭（含頭髮）近似成球：中心頭骨上 10 cm、掌心至少離中心 13 cm
            if (goal - hc).length < 0.13:                                        # 兩個點之間直線會切過頭的側面 → 推到頭髮外面（變成繞著頭走的弧）
                goal = hc + (goal - hc).normalized() * 0.13
            want = raw_palm.lerp(goal, w)
            R = lift_shoulder(P, R, "R", 14.0 * win(t, 6.6, 6.9, 7.25, 7.55))
            R0 = R; target = Hd["J_Bip_R_Hand"] + (want - raw_palm)
            on_head = win(t, 6.8, 7.0, 7.25, 7.42)                               # 手掌在頭上時：掌心朝頭、手指往前上方
            rise = win(t, 6.25, 6.5, 6.65, 6.85) * (1 - on_head)                # 抬到臉前時：手指朝上、掌心朝自己（不好意思的手勢）
            for _ in range(3):
                # 手肘往外、往前（以前往外上方：上臂要外轉 140°，超過人的極限）
                R = arm_ik(P, R0, h, "R", target, rgt * 0.8 + fwd * 0.6 + up * 0.2)
                H2 = P.fk(R, h)
                cur = (H2["J_Bip_R_Middle1"] - H2["J_Bip_R_Hand"]).normalized()
                d_ = cur.lerp((up * 0.85 + fwd * 0.15).normalized(), rise).lerp((fwd * 0.6 + up * 0.3 + left * 0.4).normalized(), on_head)
                pv = left * rise + (-nrm) * on_head                                # 掌心：抬手時朝自己、在頭上時朝頭，平順轉過去
                R = aim_hand(P, R, h, "R", d_.normalized(), palm=pv.normalized() if pv.length > 1e-6 else None, palm_w=max(rise, on_head))
                H3 = P.fk(R, h)
                p3 = (H3["J_Bip_R_Hand"] + H3["J_Bip_R_Middle1"]) * 0.5
                target = target + (want - p3)
            R = gesture(P, R, "R", "relaxed", w=w)                              # 四指併攏自然微彎（原片拍背的手指套過來是食指伸直）
            R = gesture(P, R, "R", "cup", w=on_head)                            # 在頭上時再彎一點，貼著頭髮
        return R
    return mod


def scene():
    # 新郎：比 YA（Mixamo 沒有比 YA；用 Waving 手舉在臉旁那一格停住，第 2 關套 YA 手勢）→ 手放下（Patting 的收手段）→ 點頭
    groom = dict(segs=[
        S("groom", "waving_one_hand", 0.0, 0.1, hold=3.3, label="手舉在臉旁（Waving 第 0 格停住，第 2 關套比 YA 手勢）"),
        S("groom", "pat_back", 1.8, 3.3, at=3.4, label="手放下（Patting On The Back 的收手段 1.8～3.3 秒）"),
        S("groom", "nod_yes", 0.0, None, at=6.4, label="點頭（Nodding Head Yes）"),
    ], anchor=(0.0, G05, face_to(G05, OC)), mod=groom_mod() if FINAL else None)
    # 新娘：整段捧花（Mixamo 沒有捧花待機；用 Texting While Standing 雙手在胸前那段，第 2 關把頭抬起來、手放到捧花位置）
    bride = dict(segs=[
        S("bride", "texting_standing", 2.4, 11.4, label="雙手在胸前（Texting While Standing 2.4～11.4 秒，當捧花姿勢的底）"),
    ], anchor=(0.0, B05, face_to(B05, OC)), mod=bride_mod() if FINAL else None)
    # 路人甲：邊走邊看手機進來 → 右轉面向新人 → 舉手機 → 尷尬鞠躬 → 摸頭（Patting 代替）→ 右轉 → 走出去
    # 2026-10-10 第 2 輪回饋「右轉後沒有跑出去，走出去只有 0.1 秒」→ 下載 Running（使用者同意），右轉後跑出去；
    #   整段提早、各段只取動作最明顯的那幾秒（不加速），讓他 7.9 秒起跑、跑出畫面
    T_TURN = 3.3
    passerby = dict(segs=[
        S("passerby", "walk_texting", 0.0, None, loops=0.62, at=1.0, label="邊走邊看手機（Male Walking While Texting）"),
        S("passerby", "turn_right_90", 0.8, 2.0, at=T_TURN, add=True, label="右轉面向新人（Quick 90 Degree Right Turn，只取腳步和轉向）"),
        S("passerby", "texting_standing", 1.2, 2.4, at=4.3, label="舉起手機（Texting While Standing 1.2～2.4 秒）"),
        S("passerby", "bow_informal", 0.6, 1.8, at=5.3, label="尷尬鞠躬（Quick Informal Bow）"),
        S("passerby", "pat_back", 0.7, 2.2, at=6.3, label="摸頭（Patting On The Back 代替，手只到肩高）"),
        S("passerby", "turn_right_90", 0.8, 1.5, at=7.5, add=True, label="右轉（Quick 90 Degree Right Turn，只取腳步和轉向）"),
        S("passerby", "male_run", 0.0, None, loops=2.0, at=7.9, label="跑出去（Running Forward Quickly）"),
    ], anchor=("end:1", P_STOP, P_FACE), mod=passerby_mod() if FINAL else None)
    props = garden_props() + [
        dict(kind="box", name="前景老相機（三腳架）", min=[-2.25, -2.55, 0.0], max=[-1.85, -2.15, 1.45], color="#7A5236", opacity=0.6),
    ]
    cam = dict(pos=[-0.10, -6.00, 2.00], aim=[-1.00, 0.30, 1.20], lens=45.0, sensor=36.0, aspect=16 / 9)
    return dict(id="05", title="⑤ 路人甲闖進合照", dur=9.0, chars=dict(passerby=passerby, groom=groom, bride=bride),
                props=props, cam=cam, skirt=dict(who="bride", r_floor=0.70, r_waist=0.16, h_waist=0.98),
                note="橘色是路人甲。新人面向左前方的老相機（棕色方塊）。段與段之間 0.3 秒漸變，動作本身沒有改。",
                decide=DECIDE_FINAL if FINAL else ["路人甲跑出去（照你第 2 輪的回饋改）：下載了 Mixamo「Running」，7.5 秒右轉、7.9 秒起跑，約 8.4 秒跑出畫面右邊。"
                        "為了在 9 秒內跑完，整段再提早：約 2.0 秒走進畫面、4.3 秒舉手機、5.3 秒鞠躬、6.3 秒摸頭（各段只挑動作最明顯的那幾秒，沒有加速）。Mixamo 的跑步是全速循環，所以起跑沒有加速，一轉身就全速跑。",
                        "新郎比 YA：Mixamo 下載的動畫裡沒有。暫用「揮手」手舉在臉旁那一格停住（0～3.4 秒），第 2 關再套比 YA 的手勢。",
                        "新娘捧花：沒有捧花待機。暫用「站著滑手機」雙手在胸前那段當底；她的頭現在是低著的（原片在看手機），第 2 關要抬頭、跟著路人甲轉。",
                        "路人甲摸頭：用「拍背」代替，差很多——手只舉到肩膀高度（1.3 m，頭在 1.5 m），而且在身體右側（像拍旁邊的人的背），不是摸自己的頭。",
                        "路人甲舉手機拍照：用「站著滑手機」把手機拿起來那段，手機只到胸口，不像舉起來拍照。",
                        "要改善上面四項，建議我再去 Mixamo 找：站立待機、拍照、抓頭不好意思、捧花（或雙手在腰前）的待機。下載前會先問你。",
                        "新郎、新娘的頭跟著路人甲轉（第 3 輪你要的）是第 2 關才加的微調，骨骼這關還看不到。"])


DECIDE_FINAL = [
    "【第 2 關的微調，灰線是 Mixamo 原樣】新郎比 YA：0～3.4 秒右手食指、中指伸直張開約 18°，無名指、小指彎起來，拇指壓在上面（只改手指，手的位置照原片）；3.3～3.7 秒手放下時收掉。",
    "新郎的手（第 3 關回饋「新郎的手變異常」）：比完 YA（3.5～3.9 秒）之後，兩手手指換成自然下垂的微彎（原片套過來是食指往前伸、拇指翹開），兩隻上臂各往外張 8°，手腕不再插進外套下襬。",
    "新郎、新娘看人（第 3 關回饋後修正：之前上下方向算反，新郎抬頭、新娘低頭）：一開始看左前方老相機的鏡頭；路人甲約 2.0 秒走進畫面，新郎 2.4 秒起、新娘晚 0.15 秒，用 0.7 秒轉頭去看他，之後一直跟著他。轉角分給脖子 60%、上胸 25%、腰 15%（舊版的比例），最多轉 75°。",
    "新娘捧花：雙手移到腰前肚臍高度（骨盆往前 24 cm、往上 10 cm），兩手一上一下握著花莖、手指握起來；原片低頭看手機，現在抬頭跟著看。",
    "路人甲舉手機拍照：4.45～4.85 秒雙手把手機舉到眼前（頭前方 30 cm、低 2 cm），停到 5.25 秒，5.6 秒前放回原片的動作接鞠躬。",
    "路人甲摸頭（第 3 關回饋「舉手的手勢不正確」「手跑到頭的裡面」改）：原片「拍背」6.4 秒起手會往旁邊甩出去，改成 6.2 秒就接手——右手從垂在身側直接抬到胸前（手指朝上、掌心朝自己，6.62 秒）→ 6.85 秒到耳邊 → 7.05 秒到後腦勺（頭髮最高點往後 7 cm），掌心貼頭髮、手指微彎前後搓兩三下 → 7.45 秒放下，先到肩膀前下方、7.9 秒前接回原片；肩胛跟著抬 14°。",
]
