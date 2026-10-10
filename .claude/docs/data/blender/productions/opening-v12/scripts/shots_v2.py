# 情境版（preview-v2，2026-10-06）：② 玩具槌敲頭、⑦ 圓桌餵食與紅酒乾杯、⑤ 路人甲擋鏡頭。
# 依據：規劃表 wedding-becarefulinfo-show-plan-2.md 的 V12-02／V12-05／V12-07，＋使用者這次的決定（② 兩人站近 0.65 m、⑦ 落地長桌巾、
#   角色大小、⑦ 鏡頭全程固定）。動作用動作庫第 6、7 節的工廠（actions-catalog.md），前後兩個工廠給同一組參數，接續處淡入 0.3～0.4 秒。
# 幕代號 v2_02／v2_07／v2_05（和第一版 02／05／07 並存，不互相覆蓋）。時間一律是「這一幕開始後的秒數」，和影格率無關：
#   預覽版 RATE=24 RES=1280,720；正式版照 run_prod 預設（30fps、1920×1080）重渲即可。
import bpy, math, random, os, json
from mathutils import Vector, Matrix, Quaternion

B = globals()                     # 新娘（主命名空間）
GR = G                            # 新郎
PASSERBY_PROJ = os.path.join(os.path.dirname(PROJ), "passerby")
V2S = {}                          # 各幕 setup 的結果（第一次用到時算一次）


def v2_coll():
    root = bpy.data.collections.get("Set_Garden")
    return coll_new("Set_V2", root)


def v2_parts(on):
    """V2_* 子集合：只開 on 裡的"""
    root = bpy.data.collections.get("Set_V2")
    if not root:
        return
    for ch in root.children:
        ch.hide_render = ch.name not in on; ch.hide_viewport = ch.name not in on


class Actor2(Actor):
    """Actor 的版本：每一段自己的淡入秒數 segs＝[(起, 訖, spec, 淡入秒), …]；
    另外把舊動作的 palms 改成 palmsw（scene_lib.pose_frame_at 會把 palms 的目標再乘一次站位旋轉，站位 rz≠0 時掌心會偏；
    palms 本來就是骨架空間的方向，所以改走 palmsw＝不轉換，結果和站在原點的 pose_frame 相同）"""

    def __init__(self, ns, segs, place, mod=None):
        Actor.__init__(self, ns, [s[:3] for s in segs], place, mod)
        self.segs4 = segs; self._wfn = None

    def _at(self, t):
        i = 0
        for i, sg in enumerate(self.segs4):
            if t < sg[1]:
                break
        t0, t1, spec, bl = self.segs4[i][:4]
        self._wfn = self.segs4[i][4] if len(self.segs4[i]) > 4 else None       # 第 5 欄：每根骨頭自己的淡入進度
        P = act_pose(self.ns, spec, max(0.0, t - t0))
        if i > 0 and bl > 0 and t - t0 < bl:
            p0, p1, pspec = self.segs4[i - 1][:3]
            return act_pose(self.ns, pspec, t - p0), P, (t - t0) / bl if self._wfn else ease((t - t0) / bl)
        return P, None, 1.0

    @staticmethod
    def _fix(P):
        if P is not None and P.get("palms"):
            P = dict(P); P["palmsw"] = list(P.get("palmsw", [])) + list(P.pop("palms"))
        return P

    def pose(self, t):
        PA, PB, w = self._at(t)
        if self.mod:
            PA = self.mod(t, dict(PA))
            PB = self.mod(t, dict(PB)) if PB is not None else None
        PA, PB = self._fix(PA), self._fix(PB)
        pl = tuple(self.place(t))
        pa = (0.0, 0.0, 0.0) if PA.get("abs") else pl
        ns = self.ns
        if PB is None:
            ns["pose_frame_at"](ns["ARM"], PA, *pa)
        else:
            pb = (0.0, 0.0, 0.0) if PB.get("abs") else pl
            if self._wfn:
                pose_blend_w(ns, PA, PB, w, pa, pb, self._wfn)
            else:
                ns["pose_blend_at"](ns["ARM"], PA, PB, w, *pa, place_b=pb)


def arms_drop_first(name, w):
    """換動作淡入時各骨頭的進度：上臂先放下、前臂和手晚一點才伸直（全部同一個進度時，從「手在頭上」淡到「手在身側」
    前臂會先打直、上臂還舉著，中途手會甩到頭頂上方）"""
    if name.endswith(("UpperArm", "Shoulder")):
        return ease(min(1.0, w / 0.6))
    if name.endswith(("LowerArm", "Hand")) or "Thumb" in name or "Index" in name or "Middle" in name or "Ring" in name or "Little" in name:
        return ease(max(0.0, (w - 0.3) / 0.7))
    return ease(w)


def pose_blend_w(ns, PA, PB, w, pa, pb, wfn):
    """scene_lib.pose_blend_at 的「每根骨頭自己的進度」版：wfn(骨頭名, w) → 這根骨頭的內插比例"""
    arm = ns["ARM"]
    snap = []
    for P, pl in ((PA, pa), (PB, pb)):
        ns["pose_frame_at"](arm, P, *pl); bpy.context.view_layer.update()
        snap.append(({b.name: b.rotation_quaternion.copy() for b in arm.pose.bones}, arm.location.copy(), arm.rotation_euler.z))
    (qa, la, za), (qb, lb, zb) = snap
    for b in arm.pose.bones:
        b.rotation_quaternion = qa[b.name].slerp(qb[b.name], wfn(b.name, w))
    we = ease(w)
    arm.location = la.lerp(lb, we); arm.rotation_euler.z = za + (zb - za) * we
    fa, fb = PA.get("face", {}), PB.get("face", {})
    ns["set_face"]({k: fa.get(k, 0.0) * (1 - we) + fb.get(k, 0.0) * we for k in set(fa) | set(fb)})


def once(fn, dur, t_off=0.0, hold_end=True):
    """單次動作的工廠 fn（t∈[0,1) 對 fn.dur 秒）→ 時間軸 spec（tl＝這段開始後的秒數）；t_off＝從動作的第幾秒開始"""
    return lambda tl: fn(max(0.0, min(0.9999, (tl + t_off) / dur)))


def fast(ns, key, dur):
    """既有循環動作播一次、壓到 dur 秒（例：bow 3 秒 → 快速版 1.4 秒）"""
    f = ns["ACT"][key][1]
    return lambda tl: f(max(0.0, min(0.9999, tl / dur)))


def release_arms(ns, F, dur=0.30, bulge=(0.0, -0.16, 0.0)):
    """單次動作 F 的結尾（例：bonked 結尾左手在頭頂、右手在胸前）→ 站好、雙手垂下：手腕在空間裡內插、中段往身體前方繞（bulge，新娘尺寸 × 體型），
    手是從胸前放下來（骨頭四元數直接淡入的話，手會先往外上方甩）。之後接 bow 之類的動作再淡入"""
    arm = ns["ARM"]; k = ns["BODY_S"]
    S0 = F.state(F.dur)

    def fn(tl):
        w = ease(min(1.0, tl / dur))
        b = ns["_mixd"](S0["body"], {}, w)
        P = ns["_body"](ns["arms_down"]({}), b)
        r0 = Vector(S0["root"]); r1 = Vector((0.0, 0.0, -ns["SOFT_KNEE"] * k))
        for sd in ("L", "R"):
            st = ns["_mix_arm"](S0["arms"][sd], ns["_rest_state"](arm, P, sd), w, Vector(bulge) * k, arm=arm, P=P, side=sd)
            ns["_arm_set"](arm, P, sd, *st)
        f0 = S0["face"]; f1 = {"Fcl_ALL_Fun": 0.5}
        face = {n: f0.get(n, 0.0) * (1 - w) + f1.get(n, 0.0) * w for n in set(f0) | set(f1)}
        hl, hr = S0["hands"]
        return dict(P, hands=(("cup", "relax", round(w, 2)) if hl != "relax" else "relax", ("cup", "relax", round(w, 2)) if hr != "relax" else "relax"),
                    root=tuple(r0.lerp(r1, w)), face=face, feet=ns["PLANT"])
    return fn


def walk_from(W, t_start):
    """walk_fwd 從 t_start 秒開始走（之前停在出發的站姿）"""
    return lambda tl: dict(W(min(1.0, max(0.0, (tl - t_start) / W.dur))), abs=True)


def world_of_rest(ns, bone):
    """骨頭的「rest 骨架空間 → 世界」變換（先擺好姿勢）"""
    A = ns["ARM"]; pb = A.pose.bones[bone]
    return A.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted()


def palm_world(ns, side):
    A = ns["ARM"]; k = ns["BODY_S"]
    bpy.context.view_layer.update()
    pb = A.pose.bones[f"J_Bip_{side}_Hand"]
    return A.matrix_world @ pb.matrix @ ns["_palm_pt"](A, side, k)


def m_lerp(Ma, Mb, w):
    """兩個剛體矩陣內插（位置線性、旋轉 slerp）"""
    if w <= 0:
        return Ma.copy()
    if w >= 1:
        return Mb.copy()
    qa, qb = Ma.to_quaternion(), Mb.to_quaternion()
    if qa.dot(qb) < 0:
        qb.negate()
    M = qa.slerp(qb, w).to_matrix().to_4x4(); M.translation = Ma.translation.lerp(Mb.translation, w)
    return M


# ══════════ ② 0:07–0:16（9 秒）兩人從柱子後走到拱門下 → 偷牽手 → 抽槌、跳起來從斜上方敲頭（小星星）→ 快速鞠躬 ══════════
# 2026-10-07 第二版（主控端定的時間軸，② 加長成 9 秒）：動作庫新做 mallet_draw（抽槌上肩 0.7 秒）→ mallet_jump_bonk（2.25 秒，1.00 秒在空中敲中），
#   walk_fwd 改自然、held_prop('mallet') 改成 hammer 握法（第一版自己加的「繞槌柄轉一個角度」拿掉）。
# 站位：使用者指定兩人站近到約 0.65 m（手停在她手前 16.7 cm 也接受）。走道沿用第一版：樹籬牆後（從拱門看是在拱門下）。
#   左右相距 0.58 m；新郎站在新娘前面 0.28 m（並排時蓬裙下擺會穿過新郎的腿：實測 0.62 m 並排穿插 5,000 對三角形）。
# 鞠躬時槌扛在右肩（使用者同意；夾腋下的換手路徑會穿過兩人中間或掃過她的臉）。
V2_02 = dict(gy=0.80, by=1.08, gx=-0.27, bx=0.31, cam=(0.0, -5.95, 0.95), aim=(0.0, 0.96, 1.13), lens=58.0, jump=0.15, land_yaw=-25.0,
             hit_push=0.016)
T02 = dict(walk=(0.8, 4.0), walk_end=3.95, turn=(3.95, 4.40), sneak=(4.0, 6.0), bonk=(6.0, 7.3), g_release=(7.3, 7.45), g_bow=(7.45, 1.4),
           b_reach=(4.0, 4.3), draw=(4.3, 5.0), jump=(5.0, 7.25), b_bow=(7.25, 1.4), b_turn=(7.25, 7.65), hit=6.0, stars=(6.0, 7.3))
REACH_MODE = str(globals().get("REACH_MODE", "bulge"))       # "bulge"：骨頭角度淡入＋中段往外推；"path"：手腕沿路徑內插（較快、會甩）
REACH_BULGE = {"R": (-0.10, 0.0, 0.03), "L": (0.05, 0.0, 0.0)}    # 新娘伸手到背後握槌的過渡：手腕中段往外繞多少（新娘座標、× 體型；右手往 -X＝她的右邊）
MALLET_FACE_OFF = -0.02         # 槌頭 24 cm（使用者指定）比動作庫假設的 20 cm 長：槌頭往後挪 2 cm，敲擊面仍在槌頭中心前 10 cm（動作庫算的位置）


def postured(ns, spec):
    """男性站姿骨盆修正（動作庫 posture()：VRoid rest 骨盆前傾 13.5°，往後轉 11°、腰椎回補）套到 actions.py 的動作或情境自己寫的站姿上；
    動作庫已經套在 walk_fwd、sneak_hand、bonked，bow、release_arms 沒有，淡入時骨盆會轉回前傾（2026-10-08 使用者：新郎骨盆前傾很醜）。女性不變"""
    return lambda tl: ns["posture"](dict(spec(tl)))


def to_world_abs(F, me, t_start=0.0):
    """（t_start＝這段開始後再晚幾秒才開始；時間軸給的 tl 已經是「這段開始後的秒數」，通常給 0）站在 me 的單次動作（回傳角色座標的 root／rz、腿是 FK、沒有 feet／ik）→ abs 的時間軸 spec（root／rz 換成世界座標）。
    讓前後兩段可以用不同站位淡入淡出（例：跳完落地的位置接鞠躬）"""
    M = place_matrix(*me)

    def fn(tl):
        P = dict(F(max(0.0, min(0.9999, (tl - t_start) / F.dur))))
        P["root"] = tuple(M @ Vector(P.get("root", (0, 0, 0)))); P["rz"] = me[2] + P.get("rz", 0.0); P["abs"] = True
        return P
    return fn


def lift_arm(F, side, lift_fn):
    """站姿單次動作（mallet_draw／mallet_jump_bonk 這類：state() 給 P、root、rz、feet、arms）的某一隻手，手腕與手肘方向點一起平移 lift_fn(秒)
    （骨架空間的向量），其他照動作庫。腿照 _stand_legs、手臂照 _arm_set（和動作庫的 fn 相同）"""
    def fn(t):
        s = t * F.dur; st_ = F.state(s)
        P = dict(st_["P"]); B["_stand_legs"](ARM, P, st_["root"], st_["rz"], st_["feet"])
        for sd in ("L", "R"):
            W, pl, R = st_["arms"][sd]
            if sd == side:
                d = lift_fn(s)
                W, pl = Vector(W) + d, Vector(pl) + d
            B["_arm_set"](ARM, P, sd, W, pl, R)
        return dict(P, hands=st_["hands"], root=st_["root"], rz=st_["rz"], ground=False, face=st_["face"])
    fn.dur = F.dur; fn.state = F.state
    return fn


def bow_carry(F_end_state, dur=1.4):
    """新娘快速鞠躬（女性版：雙手交疊在小腹）但右手繼續把槌扛在右肩：右手換成 F_end_state（mallet_jump_bonk 結尾）的扛肩姿勢，
    跟著胸口（UpperChest）一起前彎（右手的 IK、掌心從鞠躬裡拿掉，改寫 FK）"""
    P_end = dict(F_end_state["P"]); st_c = F_end_state["arms"]["R"]
    Mc0 = B["_fkc"](ARM, P_end, "UpperChest")
    BOWF = fast(B, "bow", dur)

    def fn(tl):
        P = dict(BOWF(tl))
        P["ik"] = [it for it in P.get("ik", []) if it[0] != "R"]
        P["palms"] = [it for it in P.get("palms", []) if it[0] != "R"]
        D = B["_fkc"](ARM, P, "UpperChest") @ Mc0.inverted()
        B["_arm_set"](ARM, P, "R", D @ Vector(st_c[0]), D @ Vector(st_c[1]), D.to_3x3() @ Matrix(st_c[2]))
        P["hands"] = (P.get("hands", ("relax", "relax"))[0], "hammer")
        return P
    return fn


MOCAP_WALK = dict(bvh="35_01", frames=(60, 324))
# 2026-10-09 使用者裁決 (b)：35_01 本身沒有停步（整段等速，CMU 35 號的 walk 段都一樣），停步改接 CMU 16 號第 33 段「slow walk, stop」
# （放慢、併腳停下）。接法：兩段各自套 mocap_action（不鎖腳），在兩段「同一隻腳剛踩下去」的支撐期裡對齊這隻腳的腳踝、交叉淡入 blend 秒，
# 接好的整段再一起鎖腳、貼地、男性骨盆修正（和單段完全同一套 _fix_feet）。真人動作的時間不拉長不壓縮。
# frames：BVH 格號（第 1 格是 T 姿）；第 217 格起兩腳併好不動，取到 236 格（多 0.16 秒站穩）。WALK_STOP=0 退回上一版（只有 35_01）
MOCAP_STOP = dict(bvh="16_33", frames=(2, 236), side="L", blend=0.20, lead=4, straight_from=0.75, straight_reach=0.9997)


def _posture_R(ns, heading):
    """男性骨盆修正（posture_fix）寫進每格的世界旋轉：骨盆往後轉、腰以上回補；腿交給鎖腳 IK 重新對腳。女性回傳 None"""
    pt, pe = ns["posture_fix"]()
    if not (pt or pe):
        return None
    ax = Quaternion(Vector((0, 0, 1)), math.radians(heading)) @ Vector((1, 0, 0))
    qh = Quaternion(ax, math.radians(-pt)); qs = Quaternion(ax, math.radians(pe))

    def f(R_fk):
        out = []
        for R in R_fk:
            R = dict(R); R["Hips"] = qh @ R["Hips"]
            for kk in list(R):
                if kk != "Hips" and "Leg" not in kk and "Foot" not in kk and "ToeBase" not in kk:
                    R[kk] = qs @ R[kk]
            out.append(R)
        return out
    return f


def _runs(flags):
    out = []; i = 0; n = len(flags)
    while i < n:
        if flags[i]:
            j = i
            while j + 1 < n and flags[j + 1]:
                j += 1
            out.append((i, j)); i = j + 1
        else:
            i += 1
    return out


def mocap_walk_stop(ns, heading, fps=120.0):
    """35_01（走路）＋16_33（放慢、併腳停下）接成一段（見 MOCAP_STOP 說明）。回傳和 mocap_action 一樣的 fn(t)（fn.dur、fn.pos、fn.join…）"""
    lib = os.path.join(LIB, "mocap")
    FA = ns["mocap_action"](os.path.join(lib, MOCAP_WALK["bvh"] + ".bvh"), frames=MOCAP_WALK["frames"], heading=heading, origin=(0.0, 0.0),
                            foot_fix=False, fix_arm_offset=False)
    FB = ns["mocap_action"](os.path.join(lib, MOCAP_STOP["bvh"] + ".bvh"), frames=MOCAP_STOP["frames"], heading=heading, origin=(0.0, 0.0),
                            foot_fix=False, fix_arm_offset=False)
    rig = FA.rig; NA, NB = len(FA.R_fk), len(FB.R_fk)
    K = int(round(MOCAP_STOP["blend"] * fps)); sd = MOCAP_STOP["side"]; lead = MOCAP_STOP["lead"]
    # 接點：16_33 第一次「這隻腳」踩下（還在走、開始放慢）↔ 35_01 最後一次完整的同一隻腳支撐期；兩邊都從踩下後 lead 格開始淡入
    rb = [r for r in FB.contact_src[sd] if r[0] > 3 and r[1] - r[0] >= K + lead + 2][0]
    ra = [r for r in FA.contact_src[sd] if r[0] > 3 and r[0] + lead + K <= NA - 1][-1]      # 35_01 用到最後一次踩下（走路整段保留）
    jA, jB = ra[0] + lead, rb[0] + lead
    HA = rig.fk(FA.R_fk[jA], FA.roots[jA]); HB = rig.fk(FB.R_fk[jB], FB.roots[jB])
    off = HA[f"{sd}_Foot"] - HB[f"{sd}_Foot"]; off.z = 0.0          # 支撐腳的腳踝對齊（水平）
    R_c, r_c = list(FA.R_fk[:jA]), list(FA.roots[:jA])
    slerp = ns["_slerp"]
    for i in range(K + 1):
        u = i / K; w = u * u * (3 - 2 * u)
        Ra, Rb = FA.R_fk[jA + i], FB.R_fk[jB + i]
        R_c.append({k: slerp(Ra[k], Rb[k], w) for k in rig.keys}); r_c.append(FA.roots[jA + i].lerp(FB.roots[jB + i] + off, w))
    R_c += FB.R_fk[jB + K + 1:]; r_c += [r + off for r in FB.roots[jB + K + 1:]]
    N = len(R_c); cut = jA + K // 2
    contact = {}
    for s in "LR":
        fa = [any(a <= i <= b for a, b in FA.contact_src[s]) for i in range(NA)]
        fb = [any(a <= i <= b for a, b in FB.contact_src[s]) for i in range(NB)]
        contact[s] = _runs([fa[i] if i < cut else fb[i - jA + jB] for i in range(N)])
    pf = _posture_R(ns, heading)
    if pf:
        R_c = pf(R_c)
    sole = {"L": [], "R": []}
    for b, co in ns["sole_points"](ns["ARM"]):
        s = "L" if "_L_" in b else "R"
        key = next((k for k in rig.keys if ns["bn"](k) == b), None)
        if key:
            sole[s].append((key, co))

    def sole_pts(R, Hd, s, o=Vector()):
        return [(Matrix.Translation(Hd[key] + o) @ R[key].to_matrix().to_4x4()) @ co for key, co in sole[s]]
    R_out, roots, contacts, extra = ns["_fix_feet"](rig, R_c, r_c, sole, sole_pts, contact, 0.995, fps)
    # 膝蓋打直（2026-10-09 使用者裁決，必要修正）：CMU 資料站著時膝蓋就彎約 30°，看起來像微蹲。只在停步的最後一兩步與站定
    # （片段結束前 straight_from 秒起）把骨盆漸進抬高到腿伸到 straight_reach（≈ 膝彎 3°），腳踝目標不變，所以腳仍鎖在原地、貼地；
    # 用同一套 _fix_feet 重算一次（只差骨盆高度與可伸直的上限），前面走路照第一次的結果，接點前後 0.1 秒淡入
    st_from = MOCAP_STOP.get("straight_from")
    if st_from and int(globals().get("KNEE_STRAIGHT", 1)):
        i0 = max(1, N - 1 - int(round(st_from * fps)))
        last = max(contacts[s][-1][0] for s in "LR")
        i1 = max(i0 + 1, last)
        Rch = MOCAP_STOP["straight_reach"]
        # 站定那格兩腳一前一後、髖到腳踝的距離不同：只抬高的話先打直的那條腿會被「構不到就下沉」拉回，另一條還彎著。
        # 改成找骨盆最小的移動量 D（上下＋前後左右），讓兩條腿同時伸到 Rch（交替投影，幾十次就收斂）
        Hn = rig.fk(R_out[-1], roots[-1]); D = Vector((0.0, 0.0, 0.0)); LEG = {}
        for s in "LR":
            L1 = (rig.rest_h[f"{s}_LowerLeg"] - rig.rest_h[f"{s}_UpperLeg"]).length; L2 = (rig.rest_h[f"{s}_Foot"] - rig.rest_h[f"{s}_LowerLeg"]).length
            LEG[s] = (Hn[f"{s}_UpperLeg"], Hn[f"{s}_Foot"], (L1 + L2) * Rch)
        for _ in range(2000):                     # 兩條腿的修正量同時取平均（逐條輪流投影會停在最後投影的那條腿上，另一條差一點）
            c = Vector((0.0, 0.0, 0.0))
            for s in "LR":
                h, a_, Rm = LEG[s]; v = (h + D) - a_
                c += v.normalized() * (Rm - v.length)
            D = D + c * 0.5
            if c.length < 1e-7:
                break
        need = D.z
        # 每格：骨盆照 smoothstep 移 D×w，腿重新解兩骨 IK 對到「原本那格的腳踝位置」（膝蓋彎的方向照原本），腳掌、腳趾的世界旋轉不動
        # → 腳底位置與角度和打直前完全相同（不會滑、不會陷），只有骨盆和大腿小腿變
        qb = ns["_qbetween"]
        # 每格可以抬多少：單腳支撐（另一腳在空中）時支撐腿本來就快伸直，再抬會構不到、腳被拉離地面。
        # 所以每格的進度取 min(smoothstep, 兩條腿都還構得到的上限)，再平滑一次（仍不超過上限）
        LL = {s: ((rig.rest_h[f"{s}_LowerLeg"] - rig.rest_h[f"{s}_UpperLeg"]).length + (rig.rest_h[f"{s}_Foot"] - rig.rest_h[f"{s}_LowerLeg"]).length) * Rch
              for s in "LR"}
        lam = [0.0] * N; cap = [1.0] * N
        for i in range(i0, N):
            u = max(0.0, min(1.0, (i - i0) / (i1 - i0))); w = u * u * (3 - 2 * u)
            Hd1 = rig.fk(R_out[i], roots[i]); lo, hi = 0.0, 1.0
            for s in "LR":
                h, a_ = Hd1[f"{s}_UpperLeg"], Hd1[f"{s}_Foot"]
                if (h - a_).length >= LL[s]:
                    hi = 0.0; break
                if (h + D - a_).length > LL[s]:            # 二分法找這條腿構得到的最大比例
                    l0, l1 = 0.0, 1.0
                    for _ in range(30):
                        m = 0.5 * (l0 + l1)
                        if (h + D * m - a_).length > LL[s]:
                            l1 = m
                        else:
                            l0 = m
                    hi = min(hi, l0)
            cap[i] = hi; lam[i] = min(w, hi)
        sm = ns["_gauss"](lam, 0.04 * fps)
        lam = [min(sm[i], cap[i]) if i >= i0 else 0.0 for i in range(N)]
        sm = ns["_gauss"](lam, 0.02 * fps)
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
        extra["knee_straight"] = dict(from_frame=i0, full_frame=i1, raise_mm=round(need * 1000, 1), shift_mm=[round(x * 1000, 1) for x in D])
    # 手骨的擷取雜訊：16_33 接近停下時右手骨在 120 fps 的一格裡突然轉 33°（之後停在新的角度；手指、手腕是 CMU 最不準的地方，真人手腕不會 8 ms 轉 33°）。
    # 只修這種單格跳動（120 fps 一格 > 8°，正常擺手每格 1～3°）：把那一下的轉動攤到前後 0.15 秒（smoothstep），其他格不動
    fixed = {}; Wn = int(round(0.15 * fps))
    for key in ("L_Hand", "R_Hand"):
        for i in range(1, N):
            dq = R_out[i][key] @ R_out[i - 1][key].inverted()
            a = math.degrees(dq.angle); a = min(a, 360 - a)
            if a <= 8.0 or a > 60.0:          # 新娘的手被提裙 IK 蓋掉，那邊的資料不管
                continue
            fixed.setdefault(key, []).append((i, round(a, 1)))
            for j in range(max(0, i - Wn), min(N, i + Wn)):
                u = (j - (i - Wn) + 0.5) / (2 * Wn); w = u * u * (3 - 2 * u)
                part = Quaternion().slerp(dq, w) if j < i else Quaternion().slerp(dq.inverted(), 1 - w)
                R_out[j] = dict(R_out[j]); R_out[j][key] = part @ R_out[j][key]
    extra["hand_despike"] = fixed
    dur = (N - 1) / fps
    face_base = {"Fcl_ALL_Fun": 0.45}

    def fn(t):
        x = max(0.0, min(1.0, t)) * (N - 1); i = min(int(x), N - 2); f = x - i
        R = {k: slerp(R_out[i][k], R_out[i + 1][k], f) for k in rig.keys}
        root = roots[i].lerp(roots[i + 1], f)
        P = rig.to_dict(R)
        blink = 1.0 if abs(t - 0.62) < 0.012 else 0.0
        return dict(P, hands=("walk_relax", "walk_relax"), root=(root.x, root.y, root.z), rz=0.0, ground=False,
                    face=dict(face_base, Fcl_EYE_Close=blink))
    fn.dur = dur; fn.rig = rig; fn.R = R_out; fn.roots = roots; fn.contacts = contacts; fn.info = extra
    fn.pos = lambda t: tuple(roots[int(round(max(0, min(1, t)) * (N - 1)))].xy + rig.rest_h["Hips"].xy)
    fn.join = dict(a_frame=MOCAP_WALK["frames"][0] + jA, b_frame=MOCAP_STOP["frames"][0] + jB, blend_frames=K,
                   t_join=round(jA / fps, 3), a_dur=round((NA - 1) / fps, 3), b_tail=round((NB - 1 - jB) / fps, 3))
    # 最後一次著地的開始（兩腳都踩著、不再動的第一格）：之後才接站姿
    last = max(contacts[s][-1][0] for s in "LR") if all(contacts[s] for s in "LR") else N - 1
    fn.settle = round(last / fps, 3)
    return fn


def mocap_walk(ns, heading, stop, skirt=False):
    """純真人走路（見 v2_02_setup 說明）：mocap_retarget.mocap_action 直接套，男性骨盆修正照 export_web_preview.make_mocap 的做法
    （在鎖腳之前把骨盆往後轉、腰以上回補，寫進世界旋轉，腿由鎖腳 IK 重新對腳）。整段平移到「最後一格骨盆＝stop」。
    skirt＝新娘：手臂換成 walk_fwd 提裙的做法（垂手往外 3°、雙手 IK 捏在臀部高度的裙面上、跟著 Hips），下半身與軀幹照真人。
    回傳 fn（同 mocap_action）＋ fn.spec(t_end)：時間軸 spec，t_end 秒時走完最後一格（之前停在第一格，人在樹籬牆後看不到）"""
    if "mocap_action" not in ns:
        ns["use"]("mocap_retarget")
    path = os.path.join(LIB, "mocap", MOCAP_WALK["bvh"] + ".bvh")
    pt, pe = ns["posture_fix"]()
    if int(globals().get("WALK_STOP", 1)):
        F = mocap_walk_stop(ns, heading)
    else:
        orig = ns["_fix_feet"]; pf = _posture_R(ns, heading)

        def fix_feet_with_posture(rig, R_fk, roots, *rest, **kw):
            return orig(rig, pf(R_fk) if pf else R_fk, roots, *rest, **kw)
        ns["_fix_feet"] = fix_feet_with_posture
        try:
            F = ns["mocap_action"](path, frames=MOCAP_WALK["frames"], heading=heading, origin=(0.0, 0.0), foot_fix=True, fix_arm_offset=False)
        finally:
            ns["_fix_feet"] = orig
        F.join = None; F.settle = F.dur
    end = Vector(F.pos(1.0)); off = Vector((stop[0], stop[1])) - end
    k = ns["BODY_S"]

    def pose(u):
        P = dict(F(u))
        r = P["root"]; P["root"] = (r[0] + off.x, r[1] + off.y, r[2])
        if skirt:
            ns["arms_down"](P, l_out=3, r_out=3); P["L_Hand"] = []; P["R_Hand"] = []
            P["ik"] = [(sd, ns["_V"](k, sg * 0.245, -0.060, 0.905), ns["_V"](k, sg * 0.50, 0.25, 1.00), None, "Hips")
                       for sd, sg in (("L", 1), ("R", -1))]
            P["hands"] = ("pinch", "pinch")
        P["abs"] = True
        return P

    def spec(t_end):
        t0 = t_end - F.dur
        return lambda tl: pose(max(0.0, min(1.0, (tl - t0) / F.dur)))
    F.spec = spec; F.pose_at = pose; F.offset = off
    print("MOCAP_WALK", ns["WHO"], "dur", round(F.dur, 3), "dist", round((Vector(F.pos(1.0)) - Vector(F.pos(0.0))).length, 3),
          "start", [round(v, 3) for v in (Vector(F.pos(0.0)) + off)], "end", [round(v, 3) for v in (end + off)], "posture", (pt, pe), "join", F.join, "settle", F.settle,
          "info", getattr(F, "info", None), flush=True)
    return F


def v2_02_setup():
    if V2S.get("02"):
        return V2S["02"]
    if V2_02_DANCE:
        return v2_02_setup_dance()
    c = V2_02; t = T02
    # 2026-10-08 使用者規定「先套成熟的骨骼動作再調整」：走路改用純真人動作捕捉（CMU 35_01 第 60～324 格，2.2 秒約 2.94 m），
    # 只做扭轉對齊、腳底鎖地、男性骨盆修正；不再用 walk_fwd（為了塞進 3.2 秒、1.5 m、4 步疊了很多加工）。
    # 情境配合動作的節奏：兩人從更遠處（樹籬牆後）出發，走完整段、3.95 秒剛好停在原本的停點（再接原本的轉身與後面的時間軸）
    gx, gy, bx, by = c["gx"], c["gy"], c["bx"], c["by"]
    g_me, b_me = (gx, gy, 0.0), (bx, by, 0.0)
    if globals().get("WALK_STYLE") == "walk_fwd":                # 對照用（改前）：上一版的 walk_fwd（V12 參數）
        WG = GR["walk_fwd"](dist=1.5, steps=4, dur=3.2, dirx=1, start=0.15, end=0.25, origin=(gx - 1.5, gy))
        WB = B["walk_fwd"](dist=1.2, steps=4, dur=3.2, dirx=-1, start=0.15, end=0.25, arms="skirt", origin=(bx + 1.2, by))
        for W_ in (WG, WB):
            W_.spec = (lambda W2: (lambda t_end: walk_from(W2, t["walk"][0])))(W_)
    else:
        WG = mocap_walk(GR, 90.0, (gx, gy), skirt=False)
        WB = mocap_walk(B, -90.0, (bx, by), skirt=True)
    # 新娘右手（站好、垂手）的掌心：偷牽手的目標
    pose_frame_at(ARM, ACT["idle"][1](0.0), *b_me)
    hand_b = palm_world(B, "R")
    kw = dict(target=tuple(hand_b), me=g_me, gap=0.12, look=34.0, hand="L")
    SN = GR["sneak_hand"](dur=1.3, **kw)
    BK = GR["bonked"](sneak_dur=1.3, dur=1.3, **kw)
    # 新郎頭的中心（偷牽手結尾那一格；跳起來敲的目標）：頭骨 rest 位置往上 10.5 cm、往後 1.5 cm（和動作庫 V12_HEADC_G 同定義）
    GR["pose_frame_at"](GR["ARM"], SN(0.9999), *g_me); bpy.context.view_layer.update()
    kg = GR["BODY_S"]; hc = GR["ARM"].data.bones["J_Bip_C_Head"].head_local + Vector((0.0, 0.015 * kg, 0.105 * kg))
    head_c = world_of_rest(GR, "J_Bip_C_Head") @ hc
    DR = B["mallet_draw"](dur=0.7, hand="R")
    JB = B["mallet_jump_bonk"](head_c=tuple(head_c), me=b_me, jump=c["jump"], t_hit=1.0, land_yaw=c["land_yaw"], dur=2.25, hand="R")
    # 動作庫把他的頭當成半徑 10.5 cm×體型的球；新郎那一側的頭髮表面實際比球低一點（v2_check 量到敲中那格槌面離頭髮 13.8 mm）：
    # 頭的中心沿敲擊方向往裡挪 hit_push，槌面剛好碰到頭髮（再壓進約 2 mm，敲中時槌頭壓扁）
    dw = Vector(JB.hit_dir); dw = Vector((dw.x, dw.y, dw.z)).normalized()
    head_c = head_c + dw * c["hit_push"]
    JB = B["mallet_jump_bonk"](head_c=tuple(head_c), me=b_me, jump=c["jump"], t_hit=1.0, land_yaw=c["land_yaw"], dur=2.25, hand="R")
    hit_w = B["_to_world"](JB.hit_point, b_me); head_w = B["_to_world"](JB.hit_head, b_me)
    # 敲完回彈、扛回肩上那段（動作的 1.05～1.75 秒）拳頭會從她自己頭頂上方經過、槌柄切進頭髮：右手腕往上 6 cm、往外 3 cm 繞過去
    JBL = lift_arm(JB, "R", lambda s_: Vector((-0.03, 0.0, 0.06)) * B["BODY_S"] * bump(s_, 1.05, 1.22, 1.45, 1.75))
    # 跳完落地的位置（世界）→ 鞠躬的站位；鞠躬淡入時轉回面向鏡頭
    S_end = JB.state(JB.dur)
    end_root = place_matrix(*b_me) @ Vector(S_end["root"]); end_rz = b_me[2] + S_end["rz"]
    print("V2_02_SETUP groom", [round(v, 3) for v in g_me], "bride", [round(v, 3) for v in b_me], "sneak gap", round(SN.gap, 3),
          "head_c", [round(v, 3) for v in head_c], "hit", [round(v, 3) for v in hit_w], "mallet head", [round(v, 3) for v in head_w],
          "choice", JB.hit_choice, "land", [round(end_root.x, 3), round(end_root.y, 3), round(end_rz, 1)], flush=True)

    NT = int(globals().get("NO_TURN", 0))          # 檢查用：不轉身（量「轉身」本身造成多少滑腳）

    def place_g(tt):
        return (gx, gy, 90.0 if NT else turn(tt, t["turn"][0], t["turn"][1], 90.0, 0.0))

    def place_b(tt):
        if tt < t["jump"][1]:
            return (bx, by, -90.0 if NT else turn(tt, t["turn"][0], t["turn"][1], -90.0, 0.0))
        return (end_root.x, end_root.y, turn(tt, t["b_turn"][0], t["b_turn"][1], end_rz, 0.0))

    # 新娘：走完（雙手提裙）→ 右手伸到背後握槌（mallet_draw 第 0 格）、左手放下的過渡（2026-10-09）：
    # 原本直接淡入骨頭角度，右手從裙面直線切到背後、前臂穿進身體側面 14.7 mm。改成手腕從走完那格的位置沿路徑內插、中段往外繞（REACH_BULGE）
    P_end = dict(WB.spec(t["walk_end"])(t["walk_end"]))
    pose_frame_at(ARM, P_end, 0.0, 0.0, 0.0); bpy.context.view_layer.update()
    arm_end = {}
    Mw = ARM.matrix_world.copy()
    for sd in "LR":
        pbs = {n: ARM.pose.bones[f"J_Bip_{sd}_{n}"] for n in ("UpperArm", "LowerArm", "Hand")}
        S_ = Mw @ pbs["UpperArm"].head; E_ = Mw @ pbs["LowerArm"].head; W_ = Mw @ pbs["Hand"].head
        dr = (W_ - S_).normalized(); pp = (E_ - S_) - dr * (E_ - S_).dot(dr)
        arm_end[sd] = (W_, S_ + dr * 0.15 + pp.normalized() * 0.4, Mw.to_3x3() @ pbs["Hand"].matrix.to_3x3())
    rb0, rb1 = t["b_reach"]

    def reach_spec(tl):
        w = ease(min(1.0, tl / (rb1 - rb0)))
        st_ = DR.state(0.0)
        P = dict(st_["P"]); B["_stand_legs"](ARM, P, st_["root"], st_["rz"], st_["feet"])
        pl = place_b(rb0 + tl)
        Ma = Matrix.Translation(place_matrix(*pl) @ Vector(st_["root"])) @ Matrix.Rotation(math.radians(pl[2] + st_["rz"]), 4, "Z")
        Mi = Ma.inverted(); M3 = Mi.to_3x3()
        if REACH_MODE == "bulge":                 # 舊的骨頭角度淡入（Actor2 照常），只把目標手腕／手肘中段往外推 REACH_BULGE（淡入的進度和這裡同一條曲線）
            h = 4.0 * w * (1.0 - w)
            for sd in "LR":
                W1, p1, R1 = st_["arms"][sd]; dv = Vector(REACH_BULGE[sd]) * B["BODY_S"] * h
                B["_arm_set"](ARM, P, sd, Vector(W1) + dv, Vector(p1) + dv * 1.5, R1)
            return dict(P, hands=st_["hands"], root=st_["root"], rz=st_["rz"], ground=False, face=st_["face"])
        for sd in "LR":
            W0, p0, R0 = arm_end[sd]
            cur = B["_mix_arm"]((Mi @ W0, Mi @ p0, M3 @ R0), st_["arms"][sd], w, Vector(REACH_BULGE[sd]) * B["BODY_S"], arm=ARM, P=P, side=sd,
                                elbow=str(globals().get("REACH_ELBOW", "dir")))          # 手肘位置在肩膀周圍的球面上內插（"bend" 在這段會一格翻面：提裙和背後兩端的彎向幾乎相反）
            B["_arm_set"](ARM, P, sd, *cur)
        return dict(P, hands=st_["hands"], root=st_["root"], rz=st_["rz"], ground=False, face=st_["face"])

    def arms_own(name, w):                 # 這段淡入時手臂整段照 reach_spec（它的路徑本身就從走完那格的手出發），身體其他骨頭照常淡入
        if any(k in name for k in ("_Shoulder", "UpperArm", "LowerArm")) or name.endswith("_Hand"):     # 手指照常淡入（提裙捏 → 握拳）
            return 1.0
        return ease(w)

    def glance(tt, P):                     # 新娘站好後瞄一眼新郎伸過來的手（頭往右轉、低一點），抽槌時淡掉
        if t["b_reach"][0] <= tt < t["draw"][1] and "Head" in P and not P.get("abs"):
            w = seg01(tt, 4.0, 4.3) * (1 - seg01(tt, 4.45, 4.85))
            P["Head"] = list(P.get("Head", [])) + [("Z", -22.0 * w), ("X", 9.0 * w)]
        return P

    AG = Actor2(GR, [(0.0, t["walk"][1], WG.spec(t["walk_end"]), 0.0),
                     (t["sneak"][0], t["sneak"][1], once(SN, SN.dur), 0.35),            # 4.0～5.3 偷牽手，停在結尾姿勢等到 6.0
                     (t["bonk"][0], t["bonk"][1], once(BK, BK.dur), 0.0),               # 6.0 被敲
                     (t["g_release"][0], t["g_bow"][0], postured(GR, release_arms(GR, BK, 0.30)), 0.0),   # 7.3～7.6 手從頭上、胸前放下來
                     (t["g_bow"][0], 10.0, postured(GR, fast(GR, "bow", t["g_bow"][1])), 0.25)], place_g)
    AB = Actor2(B, [(0.0, t["walk"][1], WB.spec(t["walk_end"]), 0.0),
                    (t["b_reach"][0], t["b_reach"][1], reach_spec if int(globals().get("REACH_PATH", 1)) else (lambda F: (lambda tl: F(0.0)))(DR), 0.30) + ((arms_own,) if REACH_MODE == "path" else ()),   # 手伸到背後握住槌（mallet_draw 第 0 格）
                    (t["draw"][0], t["draw"][1], once(DR, DR.dur), 0.0),
                    (t["jump"][0], t["jump"][1], to_world_abs(JBL, b_me, 0.0), 0.0),
                    (t["b_bow"][0], 10.0, bow_carry(S_end, t["b_bow"][1]), 0.40)], place_b, mod=glance)
    V2S["02"] = dict(reach_spec=reach_spec, arm_end=arm_end, place_b=place_b, WG=WG, WB=WB, SN=SN, BK=BK, DR=DR, JB=JB, g_me=g_me, b_me=b_me, head_c=head_c, hit_w=hit_w, AG=AG, AB=AB)
    SHOTS["v2_02"]["actors"] = [AG, AB]
    return V2S["02"]


def v2_02_build():
    need_garden()
    c = v2_coll()
    if V2_02_DANCE:                      # 跳舞版不用槌和星星（物件不建；若 .blend 裡已有，frame 會藏起來）
        v2_02_setup(); return
    if "V2_Mallet" not in bpy.data.objects:
        build_mallet(coll_new("V2_MalletSet", c))
        bpy.data.objects["V2_MalletHeadMesh"].location = (0.0, MALLET_FACE_OFF, 0.0)
    if "V2_Star0" not in bpy.data.objects:
        build_stars(coll_new("V2_StarSet", c))
    v2_02_setup()


def v2_02_mallet(t):
    # 4.36 秒前不顯示：mallet_draw 開頭槌頭會從她左肩後露出一點（動作庫已知限制），4.36 之後槌在她身體後面、接著從右側出來
    if t < float(globals().get("MALLET_FROM", T02["draw"][0] + 0.06)):
        mallet_set(Matrix.Identity(4), show=False); return
    bpy.context.view_layer.update()
    h = T02["hit"]
    M = B["held_prop"]("mallet", "R")
    # 敲完回彈、扛回肩上那段（6.05～6.7）槌柄會從她頭頂的頭髮上方切過去（實測穿進頭髮、碰到臉）：槌在拳頭裡往離開她頭的方向斜一點（最多 22°）
    w = bump(t, h + 0.05, h + 0.17, h + 0.45, h + 0.70)
    if w > 0:
        hc = world_of_rest(B, "J_Bip_C_Head") @ (ARM.data.bones["J_Bip_C_Head"].head_local + Vector((0, 0, 0.09 * B["BODY_S"])))
        g = M.translation; z = M.col[2].to_3d().normalized(); v = (hc - g)
        ax = z.cross(v)
        if ax.length > 1e-6:
            R = Matrix.Rotation(-math.radians(22.0) * w, 4, ax.normalized())
            M = Matrix.Translation(g) @ R @ Matrix.Translation(-g) @ M
    mallet_set(M, bump(t, h - 0.03, h + 0.01, h + 0.05, h + 0.16))


def v2_02_stars(t):
    """敲中時從新郎頭頂冒出 4 顆小星星（暖黃×2、乾燥玫瑰×2），在頭頂上方繞一圈後縮小消失（T02 的 stars 時段）"""
    a, b_ = T02["stars"]
    kg = GR["BODY_S"]; hc = GR["ARM"].data.bones["J_Bip_C_Head"].head_local + Vector((0.0, 0.015 * kg, 0.105 * kg))
    bpy.context.view_layer.update()
    ctr = world_of_rest(GR, "J_Bip_C_Head") @ (hc + Vector((0.0, 0.0, 0.16 * kg)))       # 頭髮頂上方約 6 cm（抱頭的手在下面）
    stars_update(t, a, b_, ctr, sc.camera.matrix_world.translation if sc.camera else Vector((0, -6, 1)))


def v2_02_frame(t, props=True, cast=True, cam=True):
    S = v2_02_setup()
    if V2_02_DANCE:
        return v2_02_frame_dance(t, props, cast, cam)
    if props:
        garden_parts(()); v2_parts(("V2_MalletSet", "V2_StarSet")); petals_update(t, s02_petals)
    if cast:
        # 鞠躬時裙擺物理收斂：前彎時裙擺彈簧會讓裙子往後擺到 16°，前擺掀起、看得到腿和鞋（第一版實測）。跳起來、落地那段照原本的物理
        sk = B.get("skirt")
        if sk is not None:
            u = seg01(t, 7.0, 7.3)
            sk.lean_gain = 3.0 - 2.3 * u; sk.max = math.radians(16.0 - 11.0 * u)
        S["AG"].pose(t); S["AB"].pose(t)
    if props:
        v2_02_mallet(t); v2_02_stars(t)
    if cam:
        c = V2_02
        u = seg01(t, 0.0, 1.2)                               # 接「掉進畫裡」：開頭 1.2 秒輕輕推近 3%，之後固定
        sh = math.exp(-((t - T02["hit"]) / 0.12) ** 2) if t >= T02["hit"] else 0.0       # 敲中時輕震
        jit = Vector((0.006 * math.sin(97 * t), 0.0, 0.005 * math.sin(131 * t + 1.0))) * sh
        look(Vector(c["cam"]), Vector(c["aim"]) + jit, c["lens"] * (0.97 + 0.03 * u))


# ══════════ ② 跳舞版（2026-10-10 第 5 輪使用者回饋：拿掉敲槌，兩人一起跳同一段歡樂的舞；轉身改用真人轉身）══════════
# 全部用真人動作捕捉（CMU），只做必要修正（扭轉對齊、腳底鎖地、男性骨盆修正、新娘手臂避開蓬裙）：
#   0.78～3.95 走路＋停步（沿用 mocap_walk_stop：35_01＋16_33；停點左右拉開，見 D02）
#   → 轉身：新郎 69_18（turn in place，順時針）、新娘 69_16（逆時針），各取一段約 75～80° 的原地轉身（腳先踩、骨盆肩頭跟著轉）
#   → 跳舞：兩人同一段 93_03「charleston_01」（CMU 93 號照 60 fps 播：93_07 走路步頻在 60 fps 才是 1.85 步/秒），同一時間開始＝舞步同步
#   → 快速鞠躬（動作庫 bow，新郎套 posture）
# 每段各自套 mocap_action（腳底鎖地在它自己的座標裡做），再整段繞 Z 轉、平移接到上一段結尾（轉身的開頭朝向＝走完的朝向，
# 跳舞的平均朝向＝轉身結尾的朝向；腳的中點對齊），接點用 Actor2 淡入。V2_02_DANCE=0 退回敲槌版。
V2_02_DANCE = int(globals().get("V2_02_DANCE", 1))
D02 = dict(gx=-0.45, gy=0.80, bx=0.50, by=1.08,                      # 停點：兩人左右相距 0.95 m（敲槌版 0.58 m；跳舞時蓬裙半徑 0.6～0.73 m）
           turn_g=("69_18", (135, 290), 120.0), turn_b=("69_16", (2, 150), 120.0),
           dance=("93_03", (53, 221), 60.0),                        # 93_03 第 0.85～3.65 秒（60 fps）：從站姿起跳、到兩腳都踩地的那一拍
           t_turn=3.80, xf=0.25, bl_walk=0.30, joy_in=0.3,
           bow=dict(g=32.0, b=26.0, down=0.40, hold=0.30),           # 收尾鞠躬：腳照跳舞最後一格不動，只彎上身（度、秒）
           arm_margin=0.05, leg_margin=0.07, stance_v_turn=0.15, bow_reach=0.995)
# 新娘蓬裙半徑（站姿量的，v2_02_skirt_probe.py；每 0.1 m 高度取 8 個方向的最大值）：(離地高, 半徑)，骨盆高 0.905 時
SKIRT_R = [(0.0, 0.73), (0.1, 0.72), (0.2, 0.63), (0.3, 0.57), (0.4, 0.56), (0.5, 0.54), (0.6, 0.50), (0.7, 0.43), (0.8, 0.37),
           (0.9, 0.28), (1.0, 0.15), (1.08, 0.0)]
# 同一份量測、8 個方向取最小值（腿往外踢時用：正前方最窄）
SKIRT_RMIN = [(0.0, 0.57), (0.1, 0.60), (0.2, 0.58), (0.3, 0.51), (0.4, 0.48), (0.5, 0.44), (0.6, 0.41), (0.7, 0.37), (0.8, 0.32),
              (0.9, 0.25), (1.0, 0.11), (1.08, 0.0)]


def skirt_r(z, tab=None):
    tab = tab or SKIRT_R
    if z <= tab[0][0]:
        return tab[0][1]
    for (z0, r0), (z1, r1) in zip(tab, tab[1:]):
        if z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 0.0


def _facing(rig, R):
    l = (R["Hips"] @ rig.rest_q["Hips"].inverted()) @ Vector((1, 0, 0))
    return math.degrees(math.atan2(l.y, l.x))          # rz：左手方向的角度（rest＝0，面向 −Y）


def _feet_mid(rig, R, root):
    H = rig.fk(R, root); m = (H["L_Foot"] + H["R_Foot"]) * 0.5; m.z = 0.0
    return m


def mocap_seg(ns, bvh, frames, src_fps, stance_v=0.5):
    """單段真人動作（原地）：mocap_action(heading=None) ＋ 鎖腳前套男性骨盆修正（每格照骨盆自己的左右軸）"""
    if "mocap_action" not in ns:
        ns["use"]("mocap_retarget")
    pt, pe = ns["posture_fix"]()
    orig = ns["_fix_feet"]

    def fix_with(rig, R_fk, roots, *a, **kw):
        if pt or pe:
            new = []
            for R in R_fk:
                ax = (R["Hips"] @ rig.rest_q["Hips"].inverted()) @ Vector((1, 0, 0)); ax.z = 0.0; ax.normalize()
                qh = Quaternion(ax, math.radians(-pt)); qs = Quaternion(ax, math.radians(pe))
                R = dict(R); R["Hips"] = qh @ R["Hips"]
                for kk in list(R):
                    if kk != "Hips" and "Leg" not in kk and "Foot" not in kk and "ToeBase" not in kk:
                        R[kk] = qs @ R[kk]
                new.append(R)
            R_fk = new
        return orig(rig, R_fk, roots, *a, **kw)
    ns["_fix_feet"] = fix_with
    try:
        F = ns["mocap_action"](os.path.join(LIB, "mocap", bvh + ".bvh"), frames=frames, heading=None, origin=(0.0, 0.0), src_fps=src_fps,
                               foot_fix=True, fix_arm_offset=False, stance_v=stance_v)
    finally:
        ns["_fix_feet"] = orig
    F.src_fps = src_fps
    return F


def seg_place(F, rz_add, T):
    """整段繞 Z 轉 rz_add 度（繞原點）再平移 T（世界）：骨頭世界旋轉、骨盆位置一起換"""
    rig = F.rig; q = Quaternion(Vector((0, 0, 1)), math.radians(rz_add)); hr = rig.rest_h["Hips"]
    F.R[:] = [{k: q @ R[k] for k in R} for R in F.R]
    F.roots[:] = [(q @ (r + hr)) + T - hr for r in F.roots]


def arm_clear(F, ns, margin):
    """新娘：手臂（前臂中段、手腕、手掌、指尖）進到蓬裙裡時，整條手臂繞胸口前方軸往外張（最小角度、時間上平滑）。真人資料的擺手節奏不變"""
    rig = F.rig; rq, rh = rig.rest_q, rig.rest_h
    N = len(F.R); ang = {"L": [0.0] * N, "R": [0.0] * N}

    def pts(R, H, sd):
        h = H[f"{sd}_Hand"]; e = H[f"{sd}_LowerArm"]
        mv = (R[f"{sd}_Hand"] @ rq[f"{sd}_Hand"].inverted()) @ (rh[f"{sd}_Middle1"] - rh[f"{sd}_Hand"])
        return [(e + h) * 0.5, h, h + mv * 0.6, h + mv * 1.9]

    def worst(R, H, sd, q, piv, hip, dz):
        w = 9.0
        for p in pts(R, H, sd):
            p = piv + q @ (p - piv); r = math.hypot(p.x - hip.x, p.y - hip.y)
            w = min(w, r - (skirt_r(p.z - dz) + margin))
        return w
    for i in range(N):
        R = F.R[i]; H = rig.fk(R, F.roots[i]); hip = H["Hips"]; dz = hip.z - 0.905
        fwd = (R["UpperChest"] @ rq["UpperChest"].inverted()) @ Vector((0, -1, 0))
        for sd, sg in (("L", 1), ("R", -1)):
            piv = H[f"{sd}_UpperArm"]
            for a in range(0, 82, 2):
                q = Quaternion(fwd, math.radians(sg * a))
                if worst(R, H, sd, q, piv, hip, dz) >= 0.0:
                    break
            ang[sd][i] = float(a)
    w = max(1, int(0.08 * F.src_fps))
    for sd in "LR":
        a = ns["_smooth_max"](ang[sd], w); a = ns["_gauss"](a, 0.03 * F.src_fps)
        ang[sd] = [max(x, y) for x, y in zip(a, ang[sd])]
        ang[sd] = ns["_gauss"](ang[sd], 0.02 * F.src_fps)
    for i in range(N):
        R = dict(F.R[i]); H = rig.fk(R, F.roots[i])
        fwd = (R["UpperChest"] @ rq["UpperChest"].inverted()) @ Vector((0, -1, 0))
        for sd, sg in (("L", 1), ("R", -1)):
            if ang[sd][i] > 1e-3:
                q = Quaternion(fwd, math.radians(sg * ang[sd][i]))
                for b in ("UpperArm", "LowerArm", "Hand"):
                    R[f"{sd}_{b}"] = q @ R[f"{sd}_{b}"]
        F.R[i] = R
    F.arm_out = {sd: (round(max(ang[sd]), 1), round(sum(ang[sd]) / N, 1)) for sd in "LR"}


def seg_spec(F, t_start, face_fn=None, hands=("relax", "relax")):
    """時間軸 spec（abs）：t_start 秒開始播，之前停在第一格、之後停在最後一格"""
    rig = F.rig; N = len(F.R); slerp = B["_slerp"]

    def fn(tl):
        t = tl - t_start if t_start is not None else tl
        x = max(0.0, min(1.0, t / F.dur)) * (N - 1); i = min(int(x), N - 2); f = x - i
        R = {k: slerp(F.R[i][k], F.R[i + 1][k], f) for k in rig.keys}
        r = F.roots[i].lerp(F.roots[i + 1], f)
        P = rig.to_dict(R)
        return dict(P, hands=hands, root=(r.x, r.y, r.z), rz=0.0, ground=False, abs=True, face=face_fn(t) if face_fn else {"Fcl_ALL_Fun": 0.45})
    return fn


def v2_02_setup_dance_r0():
    """第 5 輪第一版（各段分開、Actor2 淡入；接點滑腳 69 mm、腳陷地 5.7 cm）——留作對照，已不用"""
    c = D02; info = {}
    WG = mocap_walk(GR, 90.0, (c["gx"], c["gy"]), skirt=False)
    WB = mocap_walk(B, -90.0, (c["bx"], c["by"]), skirt=True)
    t_walk_end = T02["walk_end"]
    out = {}
    for who, ns, W, tk in (("groom", GR, WG, "turn_g"), ("bride", B, WB, "turn_b")):
        rig = W.rig
        R_end = W.R[-1]; r_end = W.roots[-1] + Vector((W.offset.x, W.offset.y, 0.0))
        yaw_end = _facing(rig, R_end); mid_end = _feet_mid(rig, R_end, r_end)
        TF = mocap_seg(ns, *c[tk])
        seg_place(TF, yaw_end - _facing(TF.rig, TF.R[0]), Vector())
        seg_place(TF, 0.0, mid_end - _feet_mid(TF.rig, TF.R[0], TF.roots[0]))
        yaw_t = _facing(TF.rig, TF.R[-1]); mid_t = _feet_mid(TF.rig, TF.R[-1], TF.roots[-1])
        DF = mocap_seg(ns, *c["dance"])
        mean = math.degrees(math.atan2(sum(math.sin(math.radians(_facing(DF.rig, R))) for R in DF.R),
                                       sum(math.cos(math.radians(_facing(DF.rig, R))) for R in DF.R)))
        seg_place(DF, yaw_t - mean, Vector())
        seg_place(DF, 0.0, mid_t - _feet_mid(DF.rig, DF.R[0], DF.roots[0]))
        if who == "bride":
            arm_clear(TF, ns, c["arm_margin"]); arm_clear(DF, ns, c["arm_margin"])
        yaw_d = _facing(DF.rig, DF.R[-1]); mid_d = _feet_mid(DF.rig, DF.R[-1], DF.roots[-1])
        out[who] = dict(W=W, TF=TF, DF=DF, end=(mid_d.x, mid_d.y, yaw_d))
        info[who] = dict(walk_end_yaw=round(yaw_end, 1), turn_dur=round(TF.dur, 3), turn_yaw=round(yaw_t - yaw_end, 1), dance_dur=round(DF.dur, 3),
                         dance_end=[round(mid_d.x, 3), round(mid_d.y, 3), round(yaw_d, 1)], turn_info=TF.info.get("contacts"),
                         arm_out=getattr(TF, "arm_out", None), arm_out_dance=getattr(DF, "arm_out", None))
    t_turn, t_dance = c["t_turn"], c["t_dance"]
    t_bow = t_dance + max(out["groom"]["DF"].dur, out["bride"]["DF"].dur) - 0.15
    bow_dur = 9.0 - t_bow

    def face_fn(t0):
        def f(tl):
            return {"Fcl_ALL_Fun": 0.45}
        return f
    actors = {}
    for who, ns in (("groom", GR), ("bride", B)):
        o = out[who]
        bow = fast(ns, "bow", bow_dur)
        if who == "groom":
            bow = postured(GR, bow)
        endp = o["end"]
        segs = [(0.0, t_turn, o["W"].spec(t_walk_end), 0.0),
                (t_turn, t_dance, seg_spec(o["TF"], 0.0, hands=("walk_relax", "walk_relax")), c["bl_turn"]),
                (t_dance, t_bow, seg_spec(o["DF"], 0.0, hands=("relax", "relax")), c["bl_dance"]),
                (t_bow, 10.0, bow, c["bl_bow"])]
        actors[who] = Actor2(ns, segs, (lambda e: (lambda tt: e))(endp))
    info["timeline"] = dict(turn=t_turn, dance=t_dance, bow=round(t_bow, 3), bow_dur=round(bow_dur, 3))
    print("V2_02_DANCE_SETUP", json.dumps(info, ensure_ascii=False), flush=True)
    V2S["02"] = dict(dance=True, AG=actors["groom"], AB=actors["bride"], out=out, info=info, t_bow=t_bow, WG=WG, WB=WB)
    SHOTS["v2_02"]["actors"] = [actors["groom"], actors["bride"]]
    return V2S["02"]


class _Seq:
    """接好的真人動作序列（120 fps）：rig、R（每格骨頭世界旋轉）、roots、dur、src_fps"""
    def __init__(self, rig, R, roots, fps=120.0):
        self.rig = rig; self.R = R; self.roots = roots; self.src_fps = fps; self.dur = (len(R) - 1) / fps


def resample(F, fps=120.0):
    """mocap_action 的結果（src_fps）→ fps 的格（骨頭 slerp、骨盆線性內插）"""
    N = len(F.R); n = int(round(F.dur * fps)) + 1; slerp = B["_slerp"]; R, ro = [], []
    for j in range(n):
        x = min(N - 1.0, j / fps * F.src_fps); i = min(int(x), N - 2); f = x - i
        R.append({k: slerp(F.R[i][k], F.R[i + 1][k], f) for k in F.rig.keys}); ro.append(F.roots[i].lerp(F.roots[i + 1], f))
    return R, ro


def _children(rig):
    ch = {k: [] for k in rig.keys}
    for k in rig.keys:
        if rig.parent[k]:
            ch[rig.parent[k]].append(k)

    def sub(k):
        out = [k]
        for c_ in ch[k]:
            out += sub(c_)
        return out
    return sub


def _contacts(rig, R, roots, sole_pts, fps, v_max=0.20, z_max=0.012):
    """接好的序列重新判斷著地（各段已經各自鎖過腳、貼過地）：鞋底最低三點離地 < z_max 而且水平速度 < v_max"""
    N = len(R); low = {"L": [], "R": []}
    for i in range(N):
        H = rig.fk(R[i], roots[i])
        for sd in "LR":
            p = sorted(sole_pts(R[i], H, sd), key=lambda v: v.z)[:3]
            low[sd].append(sum(p, Vector()) / len(p))
    out = {}
    for sd in "LR":
        c_ = []
        for i in range(N):
            j, k = max(0, i - 1), min(N - 1, i + 1)
            v = (low[sd][k] - low[sd][j]).xy.length * fps / max(1, k - j)
            c_.append(low[sd][i].z < z_max and v < v_max)
        runs = [r for r in _runs(c_) if r[1] - r[0] + 1 >= int(0.06 * fps) or r[0] == 0 or r[1] == N - 1]
        merged = []
        for r in runs:
            if merged and r[0] - merged[-1][1] <= int(0.08 * fps):
                merged[-1] = (merged[-1][0], r[1])
            else:
                merged.append(r)
        out[sd] = merged
    return out


def leg_clear(Q, margin, contact):
    """新娘：踢腿時膝蓋、小腿、腳從蓬裙穿出去 → 整條腿繞髖關節往骨盆中心收（最小角度、時間上平滑；著地的格不動）"""
    rig = Q.rig; N = len(Q.R); fps = Q.src_fps
    ang = {"L": [0.0] * N, "R": [0.0] * N}; axs = {"L": [None] * N, "R": [None] * N}

    def on(sd, i):
        return any(a <= i <= b for a, b in contact[sd])
    for i in range(N):
        H = rig.fk(Q.R[i], Q.roots[i]); hip = H["Hips"]; dz = hip.z - 0.905
        for sd in "LR":
            if on(sd, i):
                continue
            k_, a_, t_ = H[f"{sd}_LowerLeg"], H[f"{sd}_Foot"], H[f"{sd}_ToeBase"]
            P = [k_, (k_ + a_) * 0.5, a_, t_ + (t_ - a_) * 0.8]; piv = H[f"{sd}_UpperLeg"]

            def worst(q):
                w = 9.0
                for p in P:
                    p = piv + q @ (p - piv)
                    if p.z - dz < 0.12:
                        continue
                    w = min(w, (skirt_r(p.z - dz, SKIRT_RMIN) - margin) - math.hypot(p.x - hip.x, p.y - hip.y))
                return w
            if worst(Quaternion()) >= 0.0:
                continue
            fp = max(P, key=lambda p: math.hypot(p.x - hip.x, p.y - hip.y)); d = Vector((fp.x - hip.x, fp.y - hip.y, 0.0)).normalized()
            ax = Vector((0, 0, 1)).cross(d)
            best = None
            for a in range(2, 62, 2):
                for sg in (1, -1):
                    if worst(Quaternion(ax, math.radians(sg * a))) >= 0.0:
                        best = sg * a; break
                if best is not None:
                    break
            ang[sd][i] = best if best is not None else 60.0; axs[sd][i] = ax
    w = max(1, int(0.06 * fps)); Q.leg_in = {}
    for sd in "LR":
        mag = B["_smooth_max"]([abs(x) for x in ang[sd]], w); mag = B["_gauss"](mag, 0.03 * fps)
        idx = [j for j in range(N) if axs[sd][j] is not None]
        for i in range(N):
            if mag[i] < 0.05 or not idx or on(sd, i):
                continue
            near = min(idx, key=lambda j: abs(j - i))
            Hh = rig.fk(Q.R[i], Q.roots[i]); az = Hh[f"{sd}_Foot"].z
            wz = max(0.0, min(1.0, (az - 0.15) / 0.10))         # 腳快踩地時不收（收了腳會陷地、滑）
            if wz <= 0.0:
                continue
            q = Quaternion(axs[sd][near], math.radians(math.copysign(mag[i] * wz, ang[sd][near])))
            R = dict(Q.R[i])
            for b in ("UpperLeg", "LowerLeg", "Foot", "ToeBase"):
                R[f"{sd}_{b}"] = q @ R[f"{sd}_{b}"]
            Q.R[i] = R
        Q.leg_in[sd] = round(max(mag), 1)


def bow_overlay(rig, R0, root0, amp, n, fps, down, hold):
    """收尾鞠躬：下半身停在 R0（跳舞最後一格），脊椎往前彎（腰 45%、胸 30%、上胸 15%、頸頭 10%），手跟著胸口"""
    sub = _children(rig); out_R, out_r = [], []
    parts = (("Spine", 0.45), ("Chest", 0.30), ("UpperChest", 0.15), ("Neck", 0.05), ("Head", 0.05))
    l = (R0["Hips"] @ rig.rest_q["Hips"].inverted()) @ Vector((1, 0, 0)); l.z = 0.0; l.normalize()
    up = max(1e-3, (n - 1) / fps - down - hold)
    for j in range(n):
        t = j / fps
        a = amp * (ease(t / down) if t < down else (1.0 if t < down + hold else 1.0 - ease((t - down - hold) / up)))
        R = dict(R0)
        for b, f in parts:
            q = Quaternion(l, math.radians(a * f))
            for k in sub(b):
                R[k] = q @ R[k]
        out_R.append(R); out_r.append(root0.copy())
    return out_R, out_r


def straighten(rig, BR, Br, reach, n_in):
    """鞠躬時站直：跳舞最後一拍膝蓋彎 55～70°（查爾斯頓的蹲低），鞠躬的前 n_in 格骨盆漸進抬高／移到兩腳中間，讓兩腿伸到 reach；
    腳踝位置、腳掌角度不動（腿兩骨 IK 重新對腳，膝蓋彎的方向照原本）"""
    qb = B["_qbetween"]; H0 = rig.fk(BR[0], Br[0]); D = Vector(); LEG = {}
    for sd in "LR":
        L1 = (rig.rest_h[f"{sd}_LowerLeg"] - rig.rest_h[f"{sd}_UpperLeg"]).length; L2 = (rig.rest_h[f"{sd}_Foot"] - rig.rest_h[f"{sd}_LowerLeg"]).length
        LEG[sd] = (H0[f"{sd}_UpperLeg"], H0[f"{sd}_Foot"], (L1 + L2) * reach, L1, L2)
    for _ in range(2000):
        cc = Vector()
        for sd in "LR":
            h, a_, Rm = LEG[sd][:3]; v = (h + D) - a_; cc += v.normalized() * (Rm - v.length)
        D = D + cc * 0.5
        if cc.length < 1e-7:
            break
    for j in range(len(BR)):
        w = ease(j / max(1, n_in))
        if w <= 0:
            continue
        R = dict(BR[j]); Hd1 = rig.fk(R, Br[j]); r_new = Br[j] + D * w; Hn2 = rig.fk(R, r_new)
        for sd in "LR":
            ul, ll, ft = f"{sd}_UpperLeg", f"{sd}_LowerLeg", f"{sd}_Foot"; L1, L2 = LEG[sd][3], LEG[sd][4]
            S_ = Hn2[ul]; W_ = Hd1[ft]; v = W_ - S_; d = max(1e-4, min(v.length, (L1 + L2) * 0.9999)); dr = v.normalized()
            ca = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
            pp = Hd1[ll] - S_; pp = pp - dr * pp.dot(dr); pp = pp.normalized() if pp.length > 1e-6 else Vector((0, -1, 0))
            E = S_ + dr * math.cos(ca) * L1 + pp * math.sin(ca) * L1
            cur_t = (R[ul] @ rig.rest_q[ul].inverted()) @ (rig.rest_h[ll] - rig.rest_h[ul]); R[ul] = qb(cur_t, E - S_) @ R[ul]
            cur_s = (R[ll] @ rig.rest_q[ll].inverted()) @ (rig.rest_h[ft] - rig.rest_h[ll]); R[ll] = qb(cur_s, (S_ + dr * d) - E) @ R[ll]
        BR[j] = R; Br[j] = r_new


def v2_02_setup_dance():
    """第 5 輪第二版：走完 → 轉身 → 跳舞接成同一條 120 fps 的序列（接點交叉淡入 xf 秒），整條重新判斷著地、鎖腳、貼地；
    最後接只彎上身的鞠躬（腳不動）。新娘再做腿、手臂避開蓬裙"""
    c = D02; info = {}; fps = 120.0
    WG = mocap_walk(GR, 90.0, (c["gx"], c["gy"]), skirt=False)
    WB = mocap_walk(B, -90.0, (c["bx"], c["by"]), skirt=True)
    t_walk_end = T02["walk_end"]
    seg = {}
    for who, ns, W, tk in (("groom", GR, WG, "turn_g"), ("bride", B, WB, "turn_b")):
        rig = W.rig
        R_end = W.R[-1]; r_end = W.roots[-1] + Vector((W.offset.x, W.offset.y, 0.0))
        yaw_end = _facing(rig, R_end); mid_end = _feet_mid(rig, R_end, r_end)
        TF = mocap_seg(ns, *c[tk], stance_v=c["stance_v_turn"])
        seg_place(TF, yaw_end - _facing(TF.rig, TF.R[0]), Vector())
        seg_place(TF, 0.0, mid_end - _feet_mid(TF.rig, TF.R[0], TF.roots[0]))
        yaw_t = _facing(TF.rig, TF.R[-1]); mid_t = _feet_mid(TF.rig, TF.R[-1], TF.roots[-1])
        DF = mocap_seg(ns, *c["dance"])
        mean = math.degrees(math.atan2(sum(math.sin(math.radians(_facing(DF.rig, R))) for R in DF.R),
                                       sum(math.cos(math.radians(_facing(DF.rig, R))) for R in DF.R)))
        seg_place(DF, yaw_t - mean, Vector())
        seg_place(DF, 0.0, mid_t - _feet_mid(DF.rig, DF.R[0], DF.roots[0]))
        seg[who] = (ns, W, R_end, r_end, TF, DF, yaw_end, yaw_t)
    td = max(seg[w][4].dur for w in seg)                  # 兩人的跳舞同一格開始（轉身比較快的人最後停一下）
    t_dance = c["t_turn"] + td
    out = {}
    for who, (ns, W, R_end, r_end, TF, DF, yaw_end, yaw_t) in seg.items():
        rig = TF.rig; slerp = B["_slerp"]; K = int(round(c["xf"] * fps))
        TR, Tr = resample(TF, fps); DR, Dr = resample(DF, fps)
        while len(TR) < int(round(td * fps)) + 1:
            TR.append(TR[-1]); Tr.append(Tr[-1].copy())
        R, ro = [], []
        for i in range(len(TR)):                            # 走完的站姿 → 轉身（交叉淡入 xf 秒）
            w = ease(i / K) if i < K else 1.0
            R.append({k: slerp(R_end[k], TR[i][k], w) for k in rig.keys}); ro.append(r_end.lerp(Tr[i], w))
        RT, rT = R[-1], ro[-1]
        for i in range(1, len(DR)):                         # 轉身結尾 → 跳舞
            w = ease(i / K) if i < K else 1.0
            R.append({k: slerp(RT[k], DR[i][k], w) for k in rig.keys}); ro.append(rT.lerp(Dr[i], w))
        sole = {"L": [], "R": []}
        for b_, co in ns["sole_points"](ns["ARM"]):
            sd = "L" if "_L_" in b_ else "R"
            key = next((k for k in rig.keys if ns["bn"](k) == b_), None)
            if key:
                sole[sd].append((key, co))

        def sole_pts(Rr, Hd, sd, o=Vector(), sole=sole):
            return [(Matrix.Translation(Hd[key] + o) @ Rr[key].to_matrix().to_4x4()) @ co for key, co in sole[sd]]
        con = _contacts(rig, R, ro, sole_pts, fps)
        j0 = len(TR) - 1                                    # 交叉淡入的那幾格兩腳都當著地（鎖在原地，差的位置到下一次抬腳再接回去）
        for sd in "LR":
            rr = sorted(con[sd] + [(0, K), (j0, j0 + K)]); m = []
            for r in rr:
                if m and r[0] <= m[-1][1] + int(0.15 * fps):     # 淡入結束後很快又踩地：併成同一次著地（中間不接回，免得 3 格裡滑十幾公分）
                    m[-1] = (m[-1][0], max(m[-1][1], r[1]))
                else:
                    m.append(r)
            con[sd] = m
        R, ro, contacts, extra = ns["_fix_feet"](rig, R, ro, sole, sole_pts, con, 0.995, fps)
        bw_ = c["bow"]; nb = int(round((9.0 - t_dance - DF.dur) * fps)) + 1
        BR, Br = bow_overlay(rig, R[-1], ro[-1], bw_["g" if who == "groom" else "b"], nb, fps, bw_["down"], bw_["hold"])
        straighten(rig, BR, Br, c["bow_reach"], int(round(c["bow"]["down"] * fps)))
        R += BR[1:]; ro += Br[1:]
        Q = _Seq(rig, R, ro, fps)
        if who == "bride":
            leg_clear(Q, c["leg_margin"], contacts); arm_clear(Q, ns, c["arm_margin"])
        out[who] = Q
        info[who] = dict(walk_end_yaw=round(yaw_end, 1), turn_dur=round(TF.dur, 3), turn_yaw=round(yaw_t - yaw_end, 1), dance_dur=round(DF.dur, 3),
                         contacts={sd: [(round(a / fps + c["t_turn"], 2), round(b / fps + c["t_turn"], 2)) for a, b in contacts[sd]] for sd in "LR"},
                         pelvis_drop_mm=extra.get("pelvis_drop_max_mm"), arm_out=getattr(Q, "arm_out", None), leg_in=getattr(Q, "leg_in", None))
    t_bow = t_dance + seg["groom"][5].dur
    actors = {}
    for who, ns in (("groom", GR), ("bride", B)):
        segs = [(0.0, c["t_turn"], seg[who][1].spec(t_walk_end), 0.0),
                (c["t_turn"], 10.0, seg_spec(out[who], c["t_turn"] - c["t_turn"], hands=("relax", "relax")), c["bl_walk"])]
        actors[who] = Actor2(ns, segs, lambda tt: (0.0, 0.0, 0.0))
    info["timeline"] = dict(turn=c["t_turn"], dance=round(t_dance, 3), bow=round(t_bow, 3))
    print("V2_02_DANCE_SETUP", json.dumps(info, ensure_ascii=False), flush=True)
    V2S["02"] = dict(dance=True, AG=actors["groom"], AB=actors["bride"], out=out, info=info, t_bow=t_bow, t_dance=t_dance, WG=WG, WB=WB)
    SHOTS["v2_02"]["actors"] = [actors["groom"], actors["bride"]]
    return V2S["02"]


def joy_w(t):
    a = V2S["02"]["t_dance"] - 0.1; b = a + D02["joy_in"]
    return 0.0 if t <= a else (1.0 if t >= b else ease((t - a) / (b - a)))


def v2_02_frame_dance(t, props=True, cast=True, cam=True):
    S = V2S["02"]
    if props:
        garden_parts(()); v2_parts(()); petals_update(t, s02_petals)
    if cast:
        sk = B.get("skirt")
        if sk is not None:                       # 鞠躬時裙擺物理收斂（同敲槌版）
            u = seg01(t, S["t_bow"], S["t_bow"] + 0.3)
            sk.lean_gain = 3.0 - 2.3 * u; sk.max = math.radians(16.0 - 11.0 * u)
        S["AG"].pose(t); S["AB"].pose(t)
        w = joy_w(t)                             # 跳舞起張嘴笑（眼睛不瞇，同 ⑧ 的 MTH_Joy＋BRW_Joy）
        for ns in (GR, B):
            kb = bpy.data.objects[ns["WHO"] + "_Face"].data.shape_keys.key_blocks
            for k in ("Fcl_MTH_Joy", "Fcl_BRW_Joy"):
                if k in kb:
                    kb[k].value = w
    if cam:
        c = V2_02
        u = seg01(t, 0.0, 1.2)
        look(Vector(c["cam"]), Vector(c["aim"]), c["lens"] * (0.97 + 0.03 * u))


SHOTS["v2_02"] = dict(set="Set_Garden", cast=True, t0=0.0, dur=9.0, tail=0.0, build=v2_02_build, frame=v2_02_frame,
                      actors=[], qa_skip=([] if V2_02_DANCE else [(3.9, 4.5), (7.25, 7.7)]),
                      stills=[1.0, 2.6, 4.0, 4.3, 4.65, 5.0, 5.4, 5.8, 6.0, 6.3, 6.8, 7.25, 7.8, 8.4, 8.95])


# ══════════ ⑦ 0:52–1:04（12 秒）花園一角的圓桌：餵食 → 相視一笑拿酒杯 → 坐姿乾杯 → 喝一口 ══════════
# 圓桌（桌面 0.73 m、半徑 0.40，落地長桌巾）在拱門右側的草地上；兩張椅子在桌子後方，兩人約 90°、各自 3/4 對鏡頭（動作庫 V12_SEAT 的相對位置）。
# 鏡頭在桌前略高、全程固定；黑板在桌子右側的畫架上（空白，粉筆字之後 2D 疊）。
# 新娘坐著穿蓬裙，裙子壓不扁 → skirt_mode："hide"＝藏起下半截裙子（坐下後都在桌巾裡面）、"shrink"＝裙擺骨頭整個縮小
V2_07 = dict(tc=(1.85, -1.25), cam=(1.98, -3.95, 1.36), aim=(1.99, -1.05, 0.97), lens=38.0,
             plate=(0.03, -0.38), fork_at=(0.17, -0.30), glass_at=(0.0, -0.24), clink=(0.0, 0.31, 0.89),
             easel=(0.82, -0.02), skirt_mode="hide")
T07 = dict(feed=(0.0, 4.5), pick=(4.5, 6.3), toast=(6.3, 8.5), sip=(8.5, 12.0), clink=7.2, fork_pick=0.05)
SKIRT_LOW = ("bride_Cos_Tulle1", "bride_Cos_Tulle2", "bride_Cos_Frill1", "bride_Cos_Frill2", "bride_Cos_Lining", "bride_Cos_Cascade",
             "bride_Cos_Petal", "bride_Cos_Ruffle")
# 桌上的東西（桌心座標）：主餐大盤在兩人中間（他叉的那一口在盤子上）、點心小盤×3、水果盤（左前）、紅酒瓶（左前）、餐巾。
# 兩人沒事做的那隻手平放在桌上的位置（動作庫 _table_hand）要空出來：新郎右手約 (−0.27, 0.09)、新娘左手約 (0.29, 0.13)、新娘右手約 (0.13, 0.29)
# （2026-10-07 新版 fed 右手整段放在桌上；主餐盤從 (−0.02, 0.10) 挪到 (−0.04, 0.09)：新娘右手移去拿杯子時會擦到盤緣）
DIN_LAYOUT = dict(main=(-0.04, 0.09), desserts=[(0.15, -0.07), (0.02, -0.20), (0.22, -0.22)], fruit=(-0.17, -0.12),
                  bottle=(-0.29, -0.22), napkins=[((-0.06, -0.33), 90.0)])


# ── ⑦ 表情覆寫（2026-10-09 第 2 輪回饋；動作庫 actions_custom.py 不動，用 Actor2 的 mod 在情境裡蓋掉 face）──
#   新娘：2.64 秒咬下後張眼、小幅咀嚼 4 下（2.78～4.18，嘴巴一開一合 0.35 秒一下），之後閉嘴微笑；
#   新郎：2.6 秒餵完後張眼、閉嘴微笑；兩人舉杯（6.3～8.5）、喝酒（8.5～）都張眼閉嘴微笑，不大笑不露牙，只留眨眼；
#   喝酒時嘴型沿用動作庫的 Fcl_MTH_U（唇碰杯緣）。V2_07_FACE_LEGACY=1 → 不覆寫（改前對照）
F07 = dict(smile=0.5, brow=0.2, chew=(2.78, 4.18, 4), chew_amp=0.16, chew_smile=0.2, eye_open=0.25,
           blink=dict(bride=(4.45, 6.05, 8.05, 10.6), groom=(3.9, 5.7, 7.85, 10.9)),
           start=dict(bride=(2.64, 2.78), groom=(2.6, 2.85)))


def face07(who, t, f0):
    if globals().get("V2_07_FACE_LEGACY"):
        return f0
    a, b = F07["start"][who]
    if t < a:
        return f0
    blink = max([0.0] + [max(0.0, 1.0 - abs(t - tb) / 0.07) for tb in F07["blink"][who]])
    sm = F07["smile"]
    f = {"Fcl_MTH_Fun": sm, "Fcl_BRW_Fun": F07["brow"], "Fcl_EYE_Close": blink}
    if who == "bride":                                              # 新娘側臉時眼睛看起來像閉著：眼睛開大一點（新郎的專案底已有 0.4）
        f["Fcl_EYE_Surprised"] = F07["eye_open"] * (1 - blink)
    if who == "bride":
        c0, c1, n = F07["chew"]
        if t < c1 + 0.3:
            ph = max(0.0, min(1.0, (t - c0) / (c1 - c0)))
            env = 1.0 if t < c1 else 0.0
            f["Fcl_MTH_A"] = F07["chew_amp"] * 0.5 * (1 - math.cos(2 * math.pi * n * ph)) * env
            w = seg(t, c1, c1 + 0.3)                               # 嚼完 0.3 秒內嘴角揚到微笑
            f["Fcl_MTH_Fun"] = F07["chew_smile"] + (sm - F07["chew_smile"]) * w
    if t >= T07["sip"][0]:
        f["Fcl_MTH_U"] = f0.get("Fcl_MTH_U", 0.0)                   # 唇碰杯緣
        f["Fcl_MTH_Fun"] = sm * (1 - min(1.0, 3.0 * f["Fcl_MTH_U"]))
    if t < b:                                                       # 從動作庫的臉淡過來
        w = ease((t - a) / (b - a))
        f = {k: f0.get(k, 0.0) * (1 - w) + f.get(k, 0.0) * w for k in set(f0) | set(f)}
    return f


def face07_mod(who):
    def mod(t, P):
        P["face"] = face07(who, t, P.get("face") or {})
        return P
    return mod


def v2_07_setup_r2():
    """第 2 版（2026-10-09）：Actor2＋動作庫 feed／fed → glass_pick → toast_sit → sip（V2_07_R2=1 時用，改前對照）"""
    if V2S.get("07"):
        return V2S["07"]
    c = V2_07; TC = Vector((c["tc"][0], c["tc"][1], 0.0)); TB, SE = DIN["top"], DIN["seat"]
    g_me = (TC.x - 0.40, TC.y + 0.40, 45.0); b_me = (TC.x + 0.40, TC.y + 0.40, -45.0)
    camxy = (c["cam"][0], c["cam"][1])
    g_head = (g_me[0], g_me[1], 1.13); b_head = (b_me[0], b_me[1], 1.05)
    FD = B["fed"](partner=g_head, me=b_me, table=TB, seat=SE, dur=4.5, hand="R")
    mouth = tuple(FD.mouth_world(2.6 / 4.5))
    fkw = dict(target=mouth, plate=c["plate"], fork_at=c["fork_at"])
    FE = GR["feed"](me=g_me, table=TB, seat=SE, dur=4.5, hand="L", **fkw)
    GPg = GR["glass_pick"](role="groom", me=g_me, partner=b_head, glass_at=c["glass_at"], table=TB, seat=SE, dur=1.8, feed_kw=fkw)
    GPb = B["glass_pick"](role="bride", me=b_me, partner=g_head, glass_at=c["glass_at"], table=TB, seat=SE, dur=1.8, fed_kw=dict(partner=g_head))
    CL = (TC.x + c["clink"][0], TC.y + c["clink"][1], c["clink"][2])
    TSg = GR["toast_sit"](role="groom", me=g_me, partner=b_head, clink=CL, cam=camxy, table=TB, seat=SE, dur=2.2)
    TSb = B["toast_sit"](role="bride", me=b_me, partner=g_head, clink=CL, cam=camxy, table=TB, seat=SE, dur=2.2)
    SPg = GR["sip"](role="groom", me=g_me, cam=camxy, table=TB, seat=SE, dur=3.5)
    SPb = B["sip"](role="bride", me=b_me, cam=camxy, table=TB, seat=SE, dur=3.5)
    t = T07
    AG = Actor2(GR, [(0.0, t["feed"][1], once(FE, FE.dur), 0.0), (t["pick"][0], t["pick"][1], once(GPg, GPg.dur), 0.30),
                     (t["toast"][0], t["toast"][1], once(TSg, TSg.dur), 0.30), (t["sip"][0], 13.0, once(SPg, SPg.dur), 0.30)],
                (lambda p_: lambda tt: p_)(g_me), face07_mod("groom"))
    AB = Actor2(B, [(0.0, t["feed"][1], once(FD, FD.dur), 0.0), (t["pick"][0], t["pick"][1], once(GPb, GPb.dur), 0.30),
                    (t["toast"][0], t["toast"][1], once(TSb, TSb.dur), 0.30), (t["sip"][0], 13.0, once(SPb, SPb.dur), 0.30)],
                (lambda p_: lambda tt: p_)(b_me), face07_mod("bride"))
    S = dict(TC=TC, g_me=g_me, b_me=b_me, FE=FE, FD=FD, GPg=GPg, GPb=GPb, TSg=TSg, TSb=TSb, SPg=SPg, SPb=SPb, AG=AG, AB=AB, CL=CL, mouth=mouth)
    # 道具在桌上的世界座標（動作庫給的是角色座標）
    S["bite_at"] = B["_to_world"](FE.plate, g_me)
    S["glass_g"] = B["_to_world"](GPg.glass_at, g_me); S["glass_b"] = B["_to_world"](GPb.glass_at, b_me)
    # 叉子：拿起（0.05 秒開始抬）之前平放在桌上＝第 0.05 秒時手上叉子的位置；繞叉子軸固定轉一個角度，讓那一格叉子平躺（叉齒朝上）
    AG.pose(T07["fork_pick"]); bpy.context.view_layer.update()
    Mf = GR["held_prop"]("fork", "L"); zf = Mf.col[2].to_3d().normalized(); yf = Mf.col[1].to_3d().normalized()
    up = Vector((0, 0, 1)) - zf * zf.z; up.normalize()
    S["fork_roll"] = Matrix.Rotation(math.atan2(zf.dot(yf.cross(up)), yf.dot(up)), 4, "Z")
    S["fork_lie"] = Mf @ S["fork_roll"]
    # 那一口牛排：叉起（1.0 秒，叉尖在盤子上那一點）之後跟著叉子
    AG.pose(1.02); bpy.context.view_layer.update()
    Mf = GR["held_prop"]("fork", "L") @ S["fork_roll"]
    S["bite_rel"] = Mf.inverted() @ Matrix.Translation(S["bite_at"])
    # 叉子放回盤緣（glass_pick 第 0.45 秒放手）之後固定
    AG.pose(t["pick"][0] + 0.46); bpy.context.view_layer.update()
    S["fork_put"] = GR["held_prop"]("fork", "L") @ S["fork_roll"]
    print("V2_07_SETUP groom", [round(v, 3) for v in g_me], "bride", [round(v, 3) for v in b_me], "mouth", [round(v, 3) for v in mouth],
          "bite", [round(v, 3) for v in S["bite_at"]], flush=True)
    V2S["07"] = S
    SHOTS["v2_07"]["actors"] = [AG, AB]
    return S


# ══════════ ⑦ 第 5 輪（2026-10-10 使用者回饋；情境覆寫，動作庫 actions.py／actions_custom.py 不動）══════════
#  1. 新娘咬下（2.64）後直接收嘴，0.3 秒內轉成閉嘴微笑（拿掉咀嚼）；張眼、眨眼、新郎表情照第 2 版。
#  2. 新郎握叉：叉柄在手上的位置往手腕挪 12 mm、往小指那側挪 16 mm（v2_07_grip_search 量的：拇指、食指、中指到叉柄 ≤ 2 mm，
#     無名指、小指收在掌心），手指 fork7＝動作庫 fork 往 fist 內插 0.7、拇指多彎 10°；叉子的世界軌跡（叉尖到嘴、到盤子）照動作庫，
#     手照新握點重解（_hold）。拿起：0～0.15 秒手落到叉子上 → 0.08～0.40 握緊 → 0.40 才拿起（feed 的時間重新對應，2.55 秒起和動作庫同步，
#     咬下 2.6 不變）；放回：叉子 5.0 秒放好 → 5.0～5.2 手指鬆開（手不動）→ 5.2 起才去拿杯子（glass_pick 的後段加快，6.3 秒舉到胸前不變）。
#  3. 舉杯敬酒：toast_sit＋sip 換成情境自寫的 toast2（6.3～12.0）：7.0 碰杯 → 7.08～7.65 杯子舉到胸口～下巴、往鏡頭伸出 →
#     停 1 秒多（7.65～8.8，杯子不動，只有呼吸）→ 直接拿到嘴邊喝（8.8～10.2）→ 放下（10.15～10.85）→ 對鏡頭笑到結尾。不再先放回桌上。
#  4. 新娘喝完放下杯子（10.15）起：Fcl_MTH_Joy 1＋Fcl_BRW_Joy 1（張嘴笑、露一點上排牙），眼睛全開不加笑眼鍵（同 ⑧ 的 b08_face_keys）。
#  5. 動作連貫（覆寫層 Layer07，加在動作庫算出的狀態上）：上半身照「脊椎 → 胸（2 格）→ 肩（2 格）→ 頸（3 格）→ 頭（4 格）」先後跟上；
#     伸手時拿東西那隻手的前伸／抬高帶動肩、胸、脊椎（各晚 1～3 格、最多 3～5°）；整段加呼吸與重心微動；
#     手舉到定點（拿杯舉到胸前、舉杯停留、放下杯子、叉子收回）有一點過衝再回來；各段之間 0.3 秒在「動作狀態」層內插（不是整個姿勢 slerp）。
#     新娘咬下那段（2.05～2.95）不加延遲與呼吸（嘴的位置要對準叉尖）；喝酒時杯緣跟著延遲後的嘴走。
V2_07_R2 = int(globals().get("V2_07_R2", 0))
R5 = dict(grip_d=(0.0, -0.012, -0.016), grip_c=0.7, grip_th=10.0,
          fe_t0=0.40, fe_t1=2.55, land=0.15, land_off=(0.0, 0.015, 0.025), close=(0.08, 0.40),
          pk_put=0.5, pk_open=(0.5, 0.7), pk_end=1.8,
          hold_reach=0.36, hold_below_chin=0.035,
          lag=dict(spine=0.0, chest=2, shoulder=2, neck=3, head=4), lag_fps=30.0,
          drive=dict(sx=3.0, sz=3.0, sh=5.0), breath=(3.6, 0.6, 0.8, 0.5), sway=(6.3, 0.5, 0.4),
          os_gain=0.7, os_win=0.20,
          os_t=dict(groom=[(2.95, 3.75), (5.55, 6.45), (7.35, 8.15), (10.35, 11.3)], bride=[(5.55, 6.45), (7.35, 8.15), (10.35, 11.3)]),
          joy=(10.15, 10.45))
T07R5 = dict(feed=(0.0, 4.5), pick=(4.5, 6.3), toast=(6.3, 12.0), clink=7.0, hold=(7.65, 8.8), sip=(8.8, 10.2), lower=(10.15, 10.85))
_LAGK = dict(spine=("sx", "sy", "sz"), chest=("cx", "cy", "cz"), shoulder=("shl", "shr"), neck=("nx", "ny", "nz"), head=("hx", "hy", "hz"))


def herm_remap(t, t0, t1, s0, s1):
    """t0 以前停在 s0（速度 0）、t1 以後 s＝t－t1＋s1（速度 1）：中間三次 Hermite（速度連續）"""
    if t <= t0:
        return s0
    if t >= t1:
        return s1 + (t - t1)
    h = t1 - t0; x = (t - t0) / h
    return s0 + (s1 - s0) * (3 * x * x - 2 * x ** 3) + h * (x ** 3 - x * x)


def inv_remap(fn, s, lo, hi):
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if fn(m) < s:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def fe_s(t):
    """新郎 feed 的時間對應：0～0.40 停在 0.05（手落到叉子上、握緊）→ 2.55 起和動作庫同步"""
    return herm_remap(t, R5["fe_t0"], R5["fe_t1"], 0.05, R5["fe_t1"])


def gp_s(tl):
    """新郎 glass_pick 的時間對應：0～0.5 放叉子（同動作庫）→ 0.5～0.7 手不動、手指鬆開 → 0.7～1.8 走完動作庫的 0.5～1.8"""
    a, b = R5["pk_open"]
    if tl <= a:
        return tl
    if tl <= b:
        return a
    h = R5["pk_end"] - b; x = min(1.0, (tl - b) / h)
    return a + (R5["pk_end"] - a) * (3 * x * x - 2 * x ** 3) + h * (x ** 3 - x * x)


def fork7_register():
    H = GR["HANDS"]
    if "fork7" not in H:
        f, z = H["fork"], H["fist"]; c = R5["grip_c"]
        g = {k: tuple(a + (b - a) * c for a, b in zip(f[k], z[k])) for k in ("Index", "Middle", "Ring", "Little")}
        g["Thumb"] = tuple(a + R5["grip_th"] for a in f["Thumb"]); g["spread"] = f.get("spread", 0)
        H["fork7"] = g


def fork_off2():
    A = GR["ARM"]; k = GR["_kof"](A)
    return GR["_offk"](GR["OFF_FORK"], "L", k) + Vector(R5["grip_d"]), GR["_mir"](GR["AX_FORK"], "L").normalized()


def held_fork2():
    """held_prop('fork','L') 的新握點版（叉子原點＝握點、Z＝往叉尖）"""
    A = GR["ARM"]; bpy.context.view_layer.update()
    off, dl = fork_off2()
    M = A.matrix_world @ A.pose.bones["J_Bip_L_Hand"].matrix
    p = M @ off; R3 = M.to_3x3().normalized()
    z, y, x = GR["_frame"](R3 @ dl, R3.col[1])
    return Matrix.Translation(p) @ Matrix((y.cross(z), y, z)).transposed().to_4x4()


def make_toast2(ns, role, me, partner, clink, cam, table, seat, dur=5.7):
    """情境自寫的「碰杯 → 舉杯往鏡頭停 1 秒 → 直接喝 → 放下 → 笑」（局部秒數 s，0＝6.3 秒；胸前拿杯開始＝glass_pick 的結尾）。
    碰杯同 toast_sit（兩人同一個碰杯點、杯身各差 6 mm、碰一下）；喝酒同 sip（杯緣碰下唇、傾 34→46°）；用動作庫的 _glass／_table_hand／_seat_P"""
    A = ns["ARM"]; k = ns["_kof"](A); hand = ns["_NEAR"][role]; sg = 1 if hand == "L" else -1; o = ns["_alt"](hand)
    la = ns["_aim_deg"](me, partner); tsg = 1 if la > 0 else -1
    lc = ns["_aim_deg"](me, (cam[0], cam[1], 1.0)); csg = 1 if lc > 0 else -1
    Cl = ns["_to_local"](clink, me); pl = ns["_to_local"](partner, me); nd = Vector((pl.x, pl.y, 0.0)).normalized()
    GL = ns["GLASS"]
    G_c = Cl - nd * (GL["rim_r"] + 0.006) - Vector((0, 0, GL["bowl"]))
    H = ns["_glass_hold_G"](k, hand, table)
    HB = dict(ns["_HOLD_BODY"])
    Pr, rt = ns["_seat_P"](A, HB, seat)
    lips = ns["lips_rest"](A)
    chin = (ns["_fkc"](A, Pr, "Head") @ lips).z + rt[2] - 0.03 * k
    Sh = ns["_shoulder"](A, Pr, hand) + Vector(rt)
    cd = Vector((math.sin(math.radians(lc)), -math.cos(math.radians(lc)), 0.0))
    U = Vector((Sh.x, Sh.y, 0.0)) + cd * R5["hold_reach"] * k
    U.z = chin - GL["bowl"] - R5["hold_below_chin"] * k
    up = Vector((0, 0, 1))

    def state(s):
        s = max(0.0, min(dur, s))
        a = seg(s, 0.05, 0.62); tap = bump(s, 0.60, 0.69, 0.71, 0.79); c = seg(s, 0.78, 1.35)
        r = seg(s, 2.50, 3.25); sp = seg(s, 3.25, 3.70) * (1 - seg(s, 3.70, 3.90)); lo = seg(s, 3.85, 4.55)
        cw = a * (1 - c); hv = c * (1 - r)
        lk = la + (lc - la) * seg(s, 0.72, 1.30)
        cam_w = max(0.0, min(1.0, 1 - seg(s, 2.5, 3.0) + seg(s, 4.2, 4.9)))
        b = dict(HB)
        b["sx"] = HB.get("sx", 0.0) + 2.0 * cw + 3.0 * hv
        b["sz"] = tsg * 5.0 * cw + csg * 4.0 * hv; b["cz"] = tsg * 3.0 * cw + csg * 3.0 * hv
        b.update(ns["_look"]((lk - tsg * 8.0 * cw) * cam_w))
        nod = bump(s, 1.25, 1.40, 1.48, 1.68)
        b["hx"] = 6.0 * nod + 3.0 * r * (1 - lo) - 6.0 * sp
        b["nx"] = -2.0 * sp
        b["hy"] = 3.0 * seg(s, 4.8, 5.4) * csg
        P, root = ns["_seat_P"](A, b, seat)
        Lp = ns["_fkc"](A, P, "Head") @ lips + Vector(root)
        q = Vector((Lp.x - U.x, Lp.y - U.y, 0.0)).normalized()
        th = math.radians(34.0 + 12.0 * sp)
        dv = up * math.cos(th) + q * math.sin(th); m = q * math.cos(th) - up * math.sin(th)
        G_l = Lp + Vector((0, 0, -0.008 * k)) - q * 0.002 - dv * GL["rim"] - m * GL["rim_r"]
        G = (H.lerp(G_c, a) + nd * 0.006 * tap).lerp(U, c).lerp(G_l, r).lerp(H, lo)
        wl = r * (1 - lo)
        dd = ns["_slerp_dir"](up, dv, wl)
        po = Vector((sg * 0.32, 0.05, -0.32)).lerp(Vector((sg * 0.38, -0.02, -0.30)), c * (1 - lo)).lerp(Vector((sg * 0.45, -0.12, -0.22)), wl)
        arms = {hand: ns["_glass"](A, P, hand, root, k, G, dd, po), o: ns["_table_hand"](A, P, o, root, table, k)}
        face = {"Fcl_ALL_Fun": 0.3, "Fcl_EYE_Close": 0.55 * sp, "Fcl_MTH_U": 0.25 * wl}
        return dict(P=P, root=root, arms=arms, hands=ns["_hands"](hand, "stem"), face=face, body=b, lipw=wl)
    state.U = U; state.hand = hand
    return state


class Layer07:
    """⑦ 第 5 輪的角色演出：segs＝[(起, 訖, state(局部秒)→動作庫狀態 dict, 淡入秒)]。
    每格：① 時間軸在「狀態」層內插（身體角度、手臂 (W, pole, R)、表情）；② 覆寫層（上身先後跟上的延遲、伸手帶動肩胸脊椎、呼吸重心、手的過衝）；
    ③ _seat_P＋_arm_set 組出姿勢 → pose_frame_at。手臂目標 W 在骨架空間，身體怎麼改手都會到同一點（接觸點不變）"""

    def __init__(self, ns, who, segs, place, face_mod, alpha=None):
        self.ns, self.who, self.segs, self.place, self.face_mod = ns, who, segs, place, face_mod
        self.alpha = alpha or (lambda t: 1.0)
        self.A = ns["ARM"]; self.k = ns["_kof"](self.A); self.cache = {}
        self.hand = ns["_NEAR"][who]; self.lips = ns["lips_rest"](self.A)
        self.ph = 0.0 if who == "groom" else 1.7

    def seg_state(self, i, t):
        t0, t1, fn, bl = self.segs[i]
        S = dict(fn(max(0.0, t - t0)))
        S.setdefault("lipw", 0.0)
        return S

    def base(self, t):
        key = round(t, 5)
        if key in self.cache:
            return self.cache[key]
        if len(self.cache) > 4000:
            self.cache.clear()
        t = max(0.0, t)
        i = 0
        for i, sg_ in enumerate(self.segs):
            if t < sg_[1]:
                break
        S = self.seg_state(i, t)
        t0, bl = self.segs[i][0], self.segs[i][3]
        if i > 0 and bl > 0 and t - t0 < bl:
            Sp = self.seg_state(i - 1, t)
            w = ease((t - t0) / bl); ns = self.ns
            b = ns["_mixd"](Sp["body"], S["body"], w)
            P, root = ns["_seat_P"](self.A, b, DIN["seat"])
            arms = {sd: ns["_mix_arm"](Sp["arms"][sd], S["arms"][sd], w, arm=self.A, P=P, side=sd) for sd in "LR"}
            S = dict(S, body=b, P=P, root=root, arms=arms, face=ns["_mixf"](Sp["face"], S["face"], w),
                     lipw=Sp["lipw"] * (1 - w) + S["lipw"] * w)
        self.cache[key] = S
        return S

    def pose_dict(self, t):
        ns, A = self.ns, self.A
        S = self.base(t)
        b0 = S["body"]; b = dict(b0)
        al = self.alpha(t)
        fps = R5["lag_fps"]; sdA = self.hand; sgA = 1 if sdA == "L" else -1
        # ① 上身先後跟上（延遲）
        for grp, lag in R5["lag"].items():
            if lag and al > 0:
                bl_ = self.base(t - lag / fps)["body"]
                for kk in _LAGK[grp]:
                    if kk in b0 or kk in bl_:
                        b[kk] = b0.get(kk, 0.0) + al * (bl_.get(kk, 0.0) - b0.get(kk, 0.0))

        # ② 伸手帶動：拿東西那隻手往前伸、往上舉 → 肩（晚 1 格）、胸（2 格）、脊椎（3 格）
        def drive(tt):
            Sx = self.base(tt)
            W = Vector(Sx["arms"][sdA][0]); Sh_ = ns["_shoulder"](A, Sx["P"], sdA); v = W - Sh_
            reach = max(-0.3, min(1.0, (-v.y - 0.22) / 0.20)); upv = max(0.0, min(1.0, (v.z + 0.10) / 0.25))
            return reach, upv
        dr = R5["drive"]
        if al > 0:
            r1, u1 = drive(t - 1 / fps); r2, _ = drive(t - 2 / fps); r3, _ = drive(t - 3 / fps)
            shk = "shl" if sdA == "L" else "shr"
            b[shk] = b.get(shk, 0.0) + al * dr["sh"] * u1
            b["cx"] = b.get("cx", 0.0) + al * 0.4 * dr["sx"] * r2; b["cz"] = b.get("cz", 0.0) + al * 0.4 * sgA * dr["sz"] * r2
            b["sx"] = b.get("sx", 0.0) + al * 0.6 * dr["sx"] * r3; b["sz"] = b.get("sz", 0.0) + al * 0.6 * sgA * dr["sz"] * r3
        # ③ 呼吸、重心微動（動作段之間也不會完全靜止）
        per, a_s, a_c, a_sh = R5["breath"]; ph = 2 * math.pi * (t / per) + self.ph
        sw_per, sw_y, sw_z = R5["sway"]; ps = 2 * math.pi * (t / sw_per) + 2.3 * self.ph
        b["sx"] = b.get("sx", 0.0) + al * a_s * math.sin(ph)
        b["cx"] = b.get("cx", 0.0) + al * a_c * math.sin(ph - 0.5)
        b["shl"] = b.get("shl", 0.0) + al * a_sh * (0.5 + 0.5 * math.sin(ph - 0.3))
        b["shr"] = b.get("shr", 0.0) + al * a_sh * (0.5 + 0.5 * math.sin(ph - 0.3))
        b["sy"] = b.get("sy", 0.0) + al * sw_y * math.sin(ps)
        b["sz"] = b.get("sz", 0.0) + al * sw_z * math.sin(ps + 0.9)
        P, root = ns["_seat_P"](A, b, DIN["seat"])
        P0 = S["P"]
        arms = {}
        for sd in "LR":
            W, pole, R = S["arms"][sd]; W = Vector(W)
            pole = Vector(pole) + (ns["_shoulder"](A, P, sd) - ns["_shoulder"](A, P0, sd))
            if sd == sdA:
                # ④ 手的過衝：W 減掉過去 0.2 秒的平均（移動中略超前、停下後一點點超過再回來），只在指定的時段
                e = 0.0
                for a_, b_ in R5["os_t"][self.who]:
                    e = max(e, bump(t, a_, a_ + 0.15, b_ - 0.15, b_))
                if e > 0:
                    n = 6; Wm = Vector((0, 0, 0))
                    for j in range(n):
                        Wm += Vector(self.base(t - R5["os_win"] * j / (n - 1))["arms"][sd][0])
                    W = W + (W - Wm / n) * R5["os_gain"] * e
                # ⑤ 喝酒時杯緣跟著延遲後的嘴走
                if S["lipw"] > 0:
                    Hd0 = ns["_fkc"](A, P0, "Head") @ self.lips; Hd1 = ns["_fkc"](A, P, "Head") @ self.lips
                    W = W + (Hd1 - Hd0) * S["lipw"]
            arms[sd] = (W, pole, R)
        for sd in "LR":
            ns["_arm_set"](A, P, sd, *arms[sd])
        out = dict(P, hands=S["hands"], root=root, face=dict(S["face"]), ground=False)
        if self.face_mod:
            out = self.face_mod(t, out)
        return out

    def pose(self, t):
        P = self.pose_dict(t)
        self.ns["pose_frame_at"](self.ns["ARM"], P, *self.place(t))


def face07_r5(who, t, f0):
    """第 5 輪表情：同第 2 版（face07），但新娘咬下後不咀嚼（2.64～2.94 從動作庫的臉淡到閉嘴微笑）、喝酒唇碰杯的時段照 toast2；
    新娘 10.15 秒起的 MTH_Joy／BRW_Joy 由 b07_joy_keys 直接寫形狀鍵（這裡把 MTH_Fun／BRW_Fun 淡掉）"""
    a, b = (2.64, 2.94) if who == "bride" else F07["start"][who]
    if t < a:
        return f0
    blink = max([0.0] + [max(0.0, 1.0 - abs(t - tb) / 0.07) for tb in F07["blink"][who]])
    sm = F07["smile"]
    f = {"Fcl_MTH_Fun": sm, "Fcl_BRW_Fun": F07["brow"], "Fcl_EYE_Close": blink}
    if who == "bride":
        f["Fcl_EYE_Surprised"] = F07["eye_open"] * (1 - blink)
    u = f0.get("Fcl_MTH_U", 0.0)
    if u > 0:
        f["Fcl_MTH_U"] = u
        f["Fcl_MTH_Fun"] = sm * (1 - min(1.0, 3.0 * u))
    if who == "bride":
        wj = b07_joy_w(t)
        if wj > 0:
            f["Fcl_MTH_Fun"] = f["Fcl_MTH_Fun"] * (1 - wj); f["Fcl_BRW_Fun"] = f["Fcl_BRW_Fun"] * (1 - wj)
    if t < b:
        w = ease((t - a) / (b - a))
        f = {k: f0.get(k, 0.0) * (1 - w) + f.get(k, 0.0) * w for k in set(f0) | set(f)}
    return f


def b07_joy_w(t):
    a, b = R5["joy"]
    return 0.0 if t <= a else (1.0 if t >= b else ease((t - a) / (b - a)))


def b07_joy_keys(t):
    kb = bpy.data.objects[B["WHO"] + "_Face"].data.shape_keys.key_blocks
    w = 0.0 if V2_07_R2 else b07_joy_w(t)
    for n in ("Fcl_MTH_Joy", "Fcl_BRW_Joy"):
        if n in kb:
            kb[n].value = w


def v2_07_setup():
    return v2_07_setup_r2() if V2_07_R2 else v2_07_setup_r5()


def v2_07_setup_r5():
    if V2S.get("07"):
        return V2S["07"]
    c = V2_07; TC = Vector((c["tc"][0], c["tc"][1], 0.0)); TB, SE = DIN["top"], DIN["seat"]
    g_me = (TC.x - 0.40, TC.y + 0.40, 45.0); b_me = (TC.x + 0.40, TC.y + 0.40, -45.0)
    camxy = (c["cam"][0], c["cam"][1])
    g_head = (g_me[0], g_me[1], 1.13); b_head = (b_me[0], b_me[1], 1.05)
    FD = B["fed"](partner=g_head, me=b_me, table=TB, seat=SE, dur=4.5, hand="R")
    mouth = tuple(FD.mouth_world(2.6 / 4.5))
    fkw = dict(target=mouth, plate=c["plate"], fork_at=c["fork_at"])
    FE = GR["feed"](me=g_me, table=TB, seat=SE, dur=4.5, hand="L", **fkw)
    GPg = GR["glass_pick"](role="groom", me=g_me, partner=b_head, glass_at=c["glass_at"], table=TB, seat=SE, dur=1.8, feed_kw=fkw)
    GPb = B["glass_pick"](role="bride", me=b_me, partner=g_head, glass_at=c["glass_at"], table=TB, seat=SE, dur=1.8, fed_kw=dict(partner=g_head))
    CL = (TC.x + c["clink"][0], TC.y + c["clink"][1], c["clink"][2])
    TWg = make_toast2(GR, "groom", g_me, b_head, CL, camxy, TB, SE)
    TWb = make_toast2(B, "bride", b_me, g_head, CL, camxy, TB, SE)
    fork7_register()
    AG_ = GR["ARM"]; off2, dl2 = fork_off2()
    lo_, hi_ = R5["land"], R5["close"]
    Gf, df = FE.state(FE.dur)["G"], FE.state(FE.dur)["d"]
    G_put, d_put = GPg.fork_put
    put_cache = {}

    def resolve(P, root, G, d, pole):
        return GR["_hold"](AG_, P, "L", Vector(G) - Vector(root), d, dl2, off2, pole)[0]

    def g_feed(tl):
        s = fe_s(tl); S = dict(FE.state(s)); arms = dict(S["arms"])
        W, pole, R = resolve(S["P"], S["root"], S["G"], S["d"], arms["L"][1])
        if tl < lo_:
            W = W + Vector(R5["land_off"]) * (1 - seg(tl, 0.0, lo_))
        arms["L"] = (W, pole, R)
        g = seg(tl, *hi_)
        S["arms"] = arms; S["hands"] = (("relax", "fork7", round(g, 2)) if g < 1 else "fork7", "relax")
        return S

    def g_pick(tl):
        s = gp_s(tl); S = dict(GPg.state(s)); arms = dict(S["arms"])
        a_, b_ = R5["pk_open"]
        if s <= R5["pk_put"] + 1e-9:
            x1 = seg(s, 0.0, 0.5)
            arms["L"] = resolve(S["P"], S["root"], Gf.lerp(G_put, x1), GR["_slerp_dir"](df, d_put, x1), arms["L"][1])
        else:
            if "b" not in put_cache:
                Sb = GPg.state(R5["pk_put"]); Wb, pb_, Rb = Sb["arms"]["L"]
                Wn, _, Rn = resolve(Sb["P"], Sb["root"], G_put, d_put, pb_)
                dq_ = (Matrix(Rn) @ Matrix(Rb).transposed()).to_quaternion()
                if dq_.w < 0:
                    dq_.negate()
                put_cache["b"] = (Vector(Wn) - Vector(Wb), dq_)
            dW, dq = put_cache["b"]
            gr = seg(s, 0.5, 1.0)
            W, pole, R = arms["L"]
            qd = Quaternion().slerp(dq, 1 - gr)
            arms["L"] = (Vector(W) + dW * (1 - gr), pole, qd.to_matrix() @ Matrix(R))
        if tl < a_:
            hs = "fork7"
        elif tl < b_:
            hs = ("fork7", "relax", round(seg(tl, a_, b_), 2))
        elif s < 1.0:
            hs = "relax"
        else:
            hs = S["hands"][0]
        S["arms"] = arms; S["hands"] = (hs, S["hands"][1])
        return S

    t = T07R5
    AG = Layer07(GR, "groom", [(0.0, t["feed"][1], g_feed, 0.0), (t["pick"][0], t["pick"][1], g_pick, 0.30),
                               (t["toast"][0], 13.0, TWg, 0.30)],
                 (lambda p_: lambda tt: p_)(g_me), lambda tt, P: dict(P, face=face07_r5("groom", tt, P.get("face") or {})))
    AB = Layer07(B, "bride", [(0.0, t["feed"][1], FD.state, 0.0), (t["pick"][0], t["pick"][1], GPb.state, 0.30),
                              (t["toast"][0], 13.0, TWb, 0.30)],
                 (lambda p_: lambda tt: p_)(b_me), lambda tt, P: dict(P, face=face07_r5("bride", tt, P.get("face") or {})),
                 alpha=lambda tt: 1.0 - bump(tt, 2.05, 2.30, 2.75, 2.95))
    S = dict(TC=TC, g_me=g_me, b_me=b_me, FE=FE, FD=FD, GPg=GPg, GPb=GPb, TWg=TWg, TWb=TWb, AG=AG, AB=AB, CL=CL, mouth=mouth)
    S["bite_at"] = B["_to_world"](FE.plate, g_me)
    S["glass_g"] = B["_to_world"](GPg.glass_at, g_me); S["glass_b"] = B["_to_world"](GPb.glass_at, b_me)
    t_fork = R5["fe_t0"]                                         # 0.40 秒才拿起：之前叉子平放在桌上（＝那一格手上叉子的位置、轉到叉齒朝上）
    AG.pose(t_fork); bpy.context.view_layer.update()
    Mf = held_fork2(); zf = Mf.col[2].to_3d().normalized(); yf = Mf.col[1].to_3d().normalized()
    upv = Vector((0, 0, 1)) - zf * zf.z; upv.normalize()
    S["fork_roll"] = Matrix.Rotation(math.atan2(zf.dot(yf.cross(upv)), yf.dot(upv)), 4, "Z")
    S["fork_lie"] = Mf @ S["fork_roll"]
    S["t_fork"] = t_fork
    S["t_spear"] = inv_remap(fe_s, 1.02, 0.0, 2.55)             # 叉子在盤上叉起那一口（動作庫 1.02 秒）
    AG.pose(S["t_spear"]); bpy.context.view_layer.update()
    S["bite_rel"] = (held_fork2() @ S["fork_roll"]).inverted() @ Matrix.Translation(S["bite_at"])
    S["t_put"] = t["pick"][0] + R5["pk_put"]                     # 5.0 秒叉子放好、之後固定
    AG.pose(S["t_put"]); bpy.context.view_layer.update()
    S["fork_put"] = held_fork2() @ S["fork_roll"]
    S["fork_held"] = (t_fork, S["t_put"])
    S["t_glass_g"] = t["pick"][0] + inv_remap(gp_s, 1.15, R5["pk_open"][1], R5["pk_end"])
    S["t_glass_b"] = t["pick"][0] + 1.15
    print("V2_07_SETUP_R5 t_spear", round(S["t_spear"], 3), "t_glass_g", round(S["t_glass_g"], 3), "holdU g", [round(v, 3) for v in TWg.U],
          "b", [round(v, 3) for v in TWb.U], flush=True)
    V2S["07"] = S
    SHOTS["v2_07"]["actors"] = [AG, AB]
    return S


def v2_07_props(t):
    if V2_07_R2:
        return v2_07_props_r2(t)
    S = V2S["07"]
    bpy.context.view_layer.update()
    if t < S["t_fork"]:
        Mf = S["fork_lie"]
    elif t < S["t_put"]:
        Mf = held_fork2() @ S["fork_roll"]
    else:
        Mf = S["fork_put"]
    bpy.data.objects["V2_Fork"].matrix_world = Mf
    bite = bpy.data.objects["V2_ForkBite"]
    if t < S["t_spear"]:
        bite.matrix_world = Matrix.Translation(S["bite_at"]); bite.hide_render = False
    elif t < 2.62:
        bite.matrix_world = Mf @ S["bite_rel"]; bite.hide_render = False
    else:
        bite.hide_render = True
    for who_, ns, hand, key, tg in (("groom", GR, "L", "glass_g", S["t_glass_g"]), ("bride", B, "R", "glass_b", S["t_glass_b"])):
        Mg = Matrix.Translation(S[key]) if t < tg else ns["held_prop"]("glass", hand)
        bpy.data.objects[f"V2_Wine_{who_}"].matrix_world = Mg
        wine_level(f"V2_Wine_{who_}", Mg)



def v2_07_build():
    need_garden()
    c = v2_coll()
    if "V2_Table" not in bpy.data.objects:
        dc = coll_new("V2_DinnerSet", c)
        tc = V2_07["tc"]
        build_dinner(dc, tc)
        build_dinner_items(dc, dict(DIN_LAYOUT))
        for who_ in ("groom", "bride"):
            build_glass(dc, f"V2_Wine_{who_}")
        build_fork(dc, "V2_Fork")
        TC = Vector((tc[0], tc[1], 0.0))
        build_chair(dc, "V2_ChairG", (TC.x - 0.40, TC.y + 0.40, 45.0))
        build_chair(dc, "V2_ChairB", (TC.x + 0.40, TC.y + 0.40, -45.0))
        ex, ey = TC.x + V2_07["easel"][0], TC.y + V2_07["easel"][1]
        build_easel(dc, (ex, ey), face_to((ex, ey), V2_07["cam"]))
    v2_07_setup()
    if V2_07["skirt_mode"] == "hide":
        for n in SKIRT_LOW:
            o = bpy.data.objects.get(n)
            if o:
                o.hide_render = True; o.hide_viewport = True


def v2_07_skirt():
    if V2_07["skirt_mode"] == "shrink" and "Skirt_Sway" in ARM.pose.bones:
        ARM.pose.bones["Skirt_Sway"].scale = (0.55, 0.55, 0.55)


def v2_07_props_r2(t):
    S = V2S["07"]; t_pick = T07["pick"][0]
    bpy.context.view_layer.update()
    if t < T07["fork_pick"]:                                      # 叉子
        Mf = S["fork_lie"]
    elif t < t_pick + 0.45:
        Mf = GR["held_prop"]("fork", "L") @ S["fork_roll"]
    else:
        Mf = S["fork_put"]
    bpy.data.objects["V2_Fork"].matrix_world = Mf
    bite = bpy.data.objects["V2_ForkBite"]
    if t < 1.02:
        bite.matrix_world = Matrix.Translation(S["bite_at"]); bite.hide_render = False
    elif t < 2.62:
        bite.matrix_world = Mf @ S["bite_rel"]; bite.hide_render = False
    else:
        bite.hide_render = True                                    # 2.62 秒咬下（吃掉）
    # 酒杯：glass_pick 第 1.15 秒前在桌上，之後在手上；液面每格切成水平
    for who_, ns, hand, key in (("groom", GR, "L", "glass_g"), ("bride", B, "R", "glass_b")):
        Mg = Matrix.Translation(S[key]) if t < t_pick + 1.15 else ns["held_prop"]("glass", hand)
        bpy.data.objects[f"V2_Wine_{who_}"].matrix_world = Mg
        wine_level(f"V2_Wine_{who_}", Mg)


def v2_07_petals(i, rnd):
    TC = V2S["07"]["TC"]
    if i < 70:                                                    # 7.2 秒碰杯：花瓣從上方（拱門那側）飄下來
        return (T07["clink"] - 0.1 + rnd.uniform(0, 0.8), TC + Vector((rnd.uniform(-1.1, 1.3), rnd.uniform(-0.6, 0.7), rnd.uniform(1.9, 2.5))),
                (rnd.uniform(-0.25, 0.25), rnd.uniform(-0.3, 0.0), 0.0))
    if i < 95:                                                    # 整段零星飄落
        return (rnd.uniform(-2.0, 11.0), TC + Vector((rnd.uniform(-1.3, 1.5), rnd.uniform(-0.4, 1.0), rnd.uniform(2.0, 2.6))), (0, -0.1, 0))
    return None


def v2_07_frame(t, props=True, cast=True, cam=True):
    S = v2_07_setup()
    if props:
        garden_parts(()); v2_parts(("V2_DinnerSet",)); petals_update(t, v2_07_petals)
    if cast:
        S["AG"].pose(t); S["AB"].pose(t); v2_07_skirt(); b07_joy_keys(t)
    if props:
        v2_07_props(t)
    if cam:
        c = V2_07
        if globals().get("TOPDOWN"):                              # 檢查用：桌子正上方往下看（看桌上東西有沒有重疊、手的位置）
            look(S["TC"] + Vector((0.0, -0.01, 2.6)), S["TC"] + Vector((0, 0, 0.73)), 50.0)
        else:
            look(Vector(c["cam"]), Vector(c["aim"]), c["lens"])


SHOTS["v2_07"] = dict(set="Set_Garden", cast=True, t0=0.0, dur=12.0, tail=0.0, build=v2_07_build, frame=v2_07_frame,
                      actors=[], skirt=False, stills=[0.5, 1.8, 2.6, 4.0, 5.4, 6.3, 7.2, 8.0, 9.6, 11.5])


# ══════════ ⑤ 0:32–0:41（9 秒）前景老相機、新人在拱門下擺姿勢 → 路人甲走進來拍照擋鏡頭 → 尷尬鞠躬 → 轉身走出去 ══════════
# 新人沿用第一版 ⑤ 的站位與動作（拱門下 (−0.42, 0.30)、(0.40, 0.30)，面向老相機；新娘整段捧花、只換頭部動作）。
# 路人甲（projects/passerby，海軍藍西裝外套）：第一次用到時 add_character 附加進來（Cast_passerby）。
#   2026-10-07 主控端決定（動作庫加了 steps／stop）：路人甲約 3.8 秒從畫面右緣外走進來，walk_in_photo 結束在 6.7（約 6.4 按快門）→
#   oops_bow 6.7～7.5 → turn_exit 7.5～9.0（out＝0.65 → 1.5 秒，往右一直走到這幕結束，隨轉場推出）。
#   三個動作同一組位置參數（KW：origin、stop、steps、face…）；回傳的 root／rz 已是世界座標（Actor2 用 abs=True、站位 (0, 0, 0)）。
#   開始時間＝6.7 − walk_in_photo 的長度（照步數算出來）。
# 鏡頭（2026-10-07 使用者決定往右繞、看得到老相機側面）：在新人右前方、高 2.0 m 往下看。老相機在畫面左緣、從側後方 66° 看
# （胡桃木機身、皮腔、黃銅鏡頭、紅燈朝向新人），新郎在 61%、新娘在 78%，新郎頭頂 31%、下巴 37%、腳 91%。
# 偏高是為了路人甲：他比新人近，鏡頭低時他的頭（和抓頭時舉起的手肘）會投影到新郎臉的高度；從 2.0 m 往下看，他的頭頂在 42%，
# 比新郎的肩膀還低，大腿以下出畫（1.8 m 時抓頭的手臂會擋到新郎的臉，實測 7.1～7.8 秒）。
# 路人甲停在 (−0.50, −2.66)（兩腳中點）：老相機前方約 0.6 m、鏡頭軸右側約 1.4 m（從這個角度看在老相機和新郎之間），畫面 53%，
# 擋住新郎左半邊、不擋臉；面向新人 rz 170°。出發點＝停點沿畫面右方向 walk_out m（畫面右緣外），和畫面平行地走進來。
# （第一版 preview-v2 的鏡頭在老相機正後方 35°，見 design.md §17）
V2_05 = dict(cam=(-0.10, -6.00, 2.00), aim=(-1.00, 0.30, 1.20), lens=45.0, fstop=1.4,
             p_stop=(-0.50, -2.66), face=170.0, steps=5, walk_out=1.95, walk_end=6.7)
T05 = dict(oops=(6.7, 7.5), exit=(7.5, 9.0))


def g05_mod(t, P):
    """2026-10-09 第 2 輪回饋（情境覆寫，動作庫不改）：新郎整段站直＋不瞇眼。
    peace 的 legs() 讓膝蓋隨節拍一彎一直（骨盆跟著上下 0～1.2 cm）→ 拿掉腿的彎曲，腿回 rest（打直）；
    ground（自動貼地）會把骨盆放回打直時的高度，stand_fix 照常套。表情：peace 有 Fcl_EYE_Close_R 1.0（右眼眨）→ 拿掉，眼睛照常睜開"""
    P = dict(P)
    for sd in "LR":
        for n in ("UpperLeg", "LowerLeg", "Foot"):
            P.pop(f"{sd}_{n}", None)
    if P.get("face"):
        P["face"] = {k: v for k, v in P["face"].items() if k not in ("Fcl_EYE_Close_R", "Fcl_EYE_Close_L")}
    return P


def scratch_fix(ns, P, st, hcen, phi, u):
    """路人甲抱頭的右手（2026-10-09 第 2 輪回饋：手掌和前臂垂直）：
    掌心貼頭的那一點 Cp、掌心朝向都不動，手掌繞掌心法線轉 phi 度，手肘改放到「手指方向的正後方」（前臂接著手掌、手腕不折），
    手肘的位置由 IK 算（肩膀到手腕的距離不變，所以只是手肘換一個方向）。u：套用比例（0＝原動作）"""
    if u <= 0:
        return st
    arm = ns["ARM"]; k = ns["_kof"](arm)
    W, pole, R = st; R = Matrix(R)
    pp = ns["_palm_pt"](arm, "R", k)
    Cp = Vector(W) + R @ pp
    pn = -Vector(R.col[0])
    R2 = Matrix.Rotation(math.radians(phi), 3, pn) @ R
    W2 = Cp - R2 @ pp
    L1, L2 = ns["_len_arm"](arm, "R")
    E_star = W2 - Vector(R2.col[1]) * L2
    S = ns["_shoulder"](arm, P, "R")
    # pole：從肩膀往理想手肘的方向（_elbow 只取偏離肩→腕線的方向）
    pole2 = E_star + (E_star - (S + W2) * 0.5)
    st2 = (W2, pole2, R2)
    if u >= 1:
        return st2
    return ns["_mix_arm"](st, st2, u, arm=arm, P=P, side="R")


def scratch_phi(ns, P, st, hcen):
    """選 phi：手腕彎最少、前臂不穿過頭、手肘不低於肩膀太多；同彎角時偏好轉得少的"""
    arm = ns["ARM"]; k = ns["_kof"](arm)
    S = ns["_shoulder"](arm, P, "R"); best = None
    for phi in range(-180, 180, 3):
        W2, pole2, R2 = scratch_fix(ns, P, st, hcen, phi, 1.0)
        E = ns["_elbow"](arm, "R", S, W2, pole2)[0]
        bend = math.degrees((W2 - E).angle(Vector(R2.col[1])))
        # 前臂線段離頭中心的最近距離
        d = W2 - E; tt = max(0.0, min(1.0, (hcen - E).dot(d) / d.length_squared)); dmin = (E + d * tt - hcen).length
        cost = bend + abs(phi) * 0.05 + (200.0 if dmin < 0.115 * k else 0.0) + max(0.0, (S.z - 0.05 * k) - E.z) * 300.0
        if best is None or cost < best[0]:
            best = (cost, phi, bend, dmin, E.z - S.z)
    return best


def rearm(ns, F, fix_r, hands_fn=None):
    """單次動作工廠 F（有 .state、.dur，oops_bow／turn_exit）的包裝：右手狀態先經過 fix_r(P, st, s) 再寫進 FK（其餘同原本的 fn）；
    hands_fn(s, hands)：換手勢（第 3 輪：抱頭的右手不用 cup，見 HEADPAT）"""
    arm = ns["ARM"]

    def fn(t):
        s = t * F.dur; st_ = F.state(s)
        P = dict(st_["P"])
        arms = dict(st_["arms"]); arms["R"] = fix_r(P, arms["R"], s)
        for sd in ("L", "R"):
            A_, pole, rel = st_["legs"][sd]
            ns["_leg_set"](arm, P, sd, A_, pole, rel)
            W, pl, R = arms[sd]
            ns["_arm_set"](arm, P, sd, W, pl, R)
        hs = st_["hands"] if hands_fn is None else hands_fn(s, st_["hands"])
        return dict(P, hands=hs, root=st_["root"], rz=st_["rz"], ground=False, face=st_["face"])
    for a in ("dur", "state", "photo", "look", "phone0", "scratch", "head_c", "times", "steps", "prev", "stop", "end_face"):
        if hasattr(F, a):
            setattr(fn, a, getattr(F, a))
    return fn


def oops_path_fix(ns, OB, hcen, phi):
    """oops_bow 右手「手機 → 後腦」那一段整條重算：路徑和動作庫同一套（_mix_arm 從 walk_in_photo 結尾的手臂出發、往右外側繞 AROUND、
    同樣的弧長重新參數化、太靠近頭就往外推），只是終點換成 scratch_fix 修正過的抱頭姿勢 —— 不是把兩條路徑的結果再內插（那樣 7.23 秒手肘轉 25°/格）"""
    arm = ns["ARM"]; k = ns["_kof"](arm)
    S0R = OB.photo.state(OB.photo.dur)["arms"]["R"]
    AROUND = Vector((-0.20, 0.0, 0.06)) * k
    seg_ = ns["seg"]

    def tgt(P, s):
        scr = 0.008 * k * math.sin(2 * math.pi * 3.0 * max(0.0, s - 0.66)) * seg_(s, 0.66, 0.70)
        return scratch_fix(ns, P, OB.scratch(P, scr), hcen(P), phi, 1.0)
    P3 = OB.state(0.3)["P"]; T3 = tgt(P3, 0.3)
    global OOPS_TR
    OOPS_TR = float(globals().get("SCRATCH_TR", OOPS_TR))
    arc = ns["_arc_table"](arm, P3, lambda w: {"R": ns["_mix_arm"](S0R, T3, w, AROUND, None, arm=arm, P=P3, side="R")})

    def fix(P, st, s):
        wr = arc(ns["_tr"](s, 0.0, 0.70, OOPS_TR))      # 動作庫是 0.25；路徑變長（手肘換方向）後最高速 16°/格，加速段縮短讓最高速降下來
        armR = ns["_mix_arm"](S0R, tgt(P, s), wr, AROUND, None, arm=arm, P=P, side="R")
        hc_ = hcen(P); dvec = Vector(armR[0]) - hc_; rmin = 0.15 * k
        if dvec.length < rmin:
            Wn = hc_ + dvec.normalized() * rmin; dW = Wn - Vector(armR[0])
            armR = (Wn, Vector(armR[1]) + dW, armR[2])
        return armR
    return fix


OOPS_TR = 0.15
SCRATCH_W = dict(oops=(0.30, 0.66), exit=(0.0, 0.55))     # 抱頭修正的套用比例：oops_bow 0.30～0.66 秒淡入（0.70 手到頭），turn_exit 0～0.55 秒淡出

# ── 2026-10-09 第 3 輪回饋（情境覆寫，動作庫不改）──
# 使用者：「路人甲的手沒有摸到頭的感覺，摸完頭準備放下來的時候手的角度很奇怪，是往右上方凹」。
# 量到（變形後的網格）：7.3～7.5 秒掌心離頭髮 30～38 mm；放下時 7.9 秒手腕 61°（turn_exit 前半段整隻手臂繞胸口轉 70°，
#   那時手還是動作庫原本「手腕折 85°」的抱頭姿勢，第 2 輪的修正在 0～0.55 秒淡掉，折角就回來了）。
# 改法：① 貼點改用頭髮網格：從後腦右上方往頭中心打射線找頭髮表面 c 與法線 n，掌心中心放在 c + n·gap，
#   掌心朝 −n、手指沿頭皮往頭頂（scratch_fix 選手腕最直的轉角、手肘放在手指正後方）；搓頭改沿頭皮切線上下，不往裡外；
#   ② 手到頭之後不再被「手腕離頭中心 < 15 cm 就往外推」推開（推開只在路上用，接近終點淡掉）；
#   ③ 放下：turn_exit 的右手整段換成「貼頭（第 ① 點）→ 動作庫走路時垂下的手」的關節角內插（_mix_arm_fk：上臂方向球面內插、
#   手肘彎角內插＋中段多彎 fold 度、手相對前臂內插——兩端手腕都是直的，中間也不會折），弧長重新參數化、梯形速度。
#   中段多彎讓手先沿頭側往下、到肩膀高度才把手肘伸直往身體放（不往外劃開）。
COLL3 = {}
SCR3_MID = dict(on=1, e=(0.30, 0.30, -0.90), f=(-0.10, 0.50, 0.86))    # 放手的過渡姿勢：上臂方向、前臂方向（胸口的 右／前／上）
# 抱頭的右手手勢：動作庫是 cup（拇指往掌心收 22～28°），掌心貼頭時拇指尖戳進頭髮 8～27 mm →
# 拇指伸直、在手掌平面內靠向食指（thumb_in），四指微彎順著頭形
HP_EXIT = tuple(float(x) for x in str(globals().get("HP_EXIT", "0.15,0.55")).strip("()[] ").split(","))     # 模組重載時 HP_EXIT 已是 tuple
HEADPAT = dict(Thumb=(0, 4, 4), Index=(10, 14, 10), Middle=(10, 14, 10), Ring=(12, 16, 10), Little=(14, 18, 12), spread=1, thumb_in=20)
SCR3 = dict(app=0.08, app_w=(0.70, 1.0), t_end=0.80, dv=(-0.75, 0.50, 0.42), gap=0.0, low=1.20, low_tr=0.30, fold=35.0, roll=None, push_end=0.85)


def scr3_contact(PB, OB):
    """rest 姿勢的頭髮網格（_surface，骨架空間）上的貼點：(c, n, R_sc)；方向和動作庫 oops_bow 一樣（後腦右上方），
    但用幾條射線的平均法線（頭髮表面一塊一塊的，單一面法線會歪）"""
    arm = PB["ARM"]; k = PB["_kof"](arm); hc = OB.head_c
    dv = Vector(globals().get("SCR3_DV") or SCR3["dv"]).normalized()
    parts = ("_Hair", "_HairBack")
    c, n = PB["_surface"](arm, parts, hc + dv * 0.4, -dv)
    t1 = dv.cross(Vector((0, 0, 1))).normalized(); t2 = dv.cross(t1).normalized(); ns_ = Vector()
    for a in range(8):
        o = (t1 * math.cos(a * math.pi / 4) + t2 * math.sin(a * math.pi / 4)) * 0.025 * k
        c2, n2 = PB["_surface"](arm, parts, hc + dv * 0.4 + o, -dv)
        if c2 is not None:
            ns_ += n2
    n = (ns_ + n).normalized()
    up = Vector((0, 0, 1)); fy = Vector((0.25, 0.15, 1.0)); fy = (fy - n * fy.dot(n)).normalized()
    R_sc = PB["_rot_map"](Vector((0, 1, 0)), PB["_PALM_LOC"]["R"], fy, -n)
    tup = (up - n * up.dot(n)).normalized()
    return c, n, R_sc, tup


def scr3_state(PB, c, n, R_sc, tup, gap):
    """貼頭的右手狀態（跟著頭）：scr＝沿頭皮切線上下搓幾公尺"""
    arm = PB["ARM"]; k = PB["_kof"](arm); pp = PB["_palm_pt"](arm, "R", k)

    def st(P, scr, lift=0.0):
        Mh = PB["_fkc"](arm, P, "Head"); Rh = Mh.to_3x3() @ R_sc
        W = PB["_place_hand"](Rh, pp, Mh @ (c + n * (gap * k + lift) + tup * scr))
        return (W, PB["_shoulder"](arm, P, "R") + Vector((-0.45, 0.05, 0.30)) * k, Rh)
    return st


def hand_collide(ns, OB, n_rest, margin=0.001):
    """右手對頭髮的碰撞（rest 頭髮網格，頭骨 rest 空間）：手部皮膚取樣點穿進頭髮多深，就把整隻手沿貼點法線往外推多少。
    取樣點＝手骨／手指權重 > 0.5 的皮膚頂點（每 6 個取 1 個），用手骨剛體搬（忽略手指彎曲，cup 會再往掌心收一點）"""
    arm = ns["ARM"]; who = ns["WHO"]; body = bpy.data.objects[who + "_Body"]
    bvh = ns["_surf_bvh"](arm, ("_Hair", "_HairBack")); hc = OB.head_c
    gi = {g.name: g.index for g in body.vertex_groups}
    want = {gi[n] for n in gi if n == "J_Bip_R_Hand" or n.startswith("J_Bip_R_") and any(f in n for f in ("Thumb", "Index", "Middle", "Ring", "Little"))}
    Bh = arm.data.bones["J_Bip_R_Hand"]; Bl = Bh.matrix_local.to_3x3(); h0 = Bh.head_local
    Ma = arm.matrix_world.inverted() @ body.matrix_world
    pts = []
    for v in body.data.vertices:
        if sum(g.weight for g in v.groups if g.group in want) > 0.5:
            pts.append(Bl.transposed() @ (Ma @ v.co - h0))
    pts = pts[::6]

    def depth(P, st):
        Mi = ns["_fkc"](arm, P, "Head").inverted(); W, R = Vector(st[0]), Matrix(st[2]); d = 0.0
        for q in pts:
            x = Mi @ (W + R @ q)
            loc, nrm, i, dist = bvh.find_nearest(x)
            if loc is None:
                continue
            out = (x - hc).length - (loc - hc).length
            d = max(d, margin - out if out < margin else 0.0)
        return d

    def push(P, st):
        nW = ns["_fkc"](arm, P, "Head").to_3x3() @ n_rest
        for _ in range(3):
            d = depth(P, st)
            if d <= 1e-4:
                break
            st = (Vector(st[0]) + nW * d, Vector(st[1]) + nW * d, st[2])
        return st
    return push


def oops3_fix(ns, OB, hcen, phi, scr_state):
    """oops_bow 右手「手機 → 後腦」：路徑同 oops_path_fix（動作庫同一套 _mix_arm＋AROUND＋弧長表），終點換成貼頭髮的 scr3；
    「離頭中心太近往外推」只在路上（wr < push_end）用、之後淡掉，手到頭時掌心真的貼著頭髮"""
    arm = ns["ARM"]; k = ns["_kof"](arm); seg_ = ns["seg"]
    S0R = OB.photo.state(OB.photo.dur)["arms"]["R"]
    AROUND = Vector((-0.20, 0.0, 0.06)) * k
    pe = SCR3["push_end"]

    app = float(globals().get("SCR3_APP", SCR3["app"])) * k           # 最後一段沿頭髮法線貼上去：前面掌心停在表面外 app
    APR = tuple(float(x) for x in str(globals().get("SCR3_APPR", "")).split(",")) if globals().get("SCR3_APPR") else SCR3["app_w"]
    TEND = float(globals().get("SCR3_TEND", SCR3["t_end"]))

    def tgt(P, s, wr=1.0):
        scr = 0.008 * k * math.sin(2 * math.pi * 3.0 * max(0.0, s - 0.66)) * seg_(s, 0.66, 0.70)
        return scratch_fix(ns, P, scr_state(P, scr, app * (1.0 - ease(seg_(wr, *APR)))), hcen(P), phi, 1.0)
    P3 = OB.state(0.3)["P"]; T3 = tgt(P3, 0.3)
    arc = ns["_arc_table"](arm, P3, lambda w: {"R": ns["_mix_arm"](S0R, tgt(P3, 0.3, w), w, AROUND, None, arm=arm, P=P3, side="R")})

    def fix(P, st, s):
        wr = arc(ns["_tr"](s, 0.0, TEND, OOPS_TR))
        armR = ns["_mix_arm"](S0R, tgt(P, s, wr), wr, AROUND, None, arm=arm, P=P, side="R")
        hc_ = hcen(P); dvec = Vector(armR[0]) - hc_; rmin = 0.15 * k
        f = 1.0 - seg_(wr, pe - 0.25, pe)
        if dvec.length < rmin and f > 0:
            Wn = hc_ + dvec.normalized() * (dvec.length + (rmin - dvec.length) * f); dW = Wn - Vector(armR[0])
            armR = (Wn, Vector(armR[1]) + dW, armR[2])
        if COLL3.get("fn") and wr > 0.3:
            armR = COLL3["fn"](P, armR)
        return armR
    return fix


def exit3_fix(ns, TE, hcen, phi, scr_state, scr_end):
    """turn_exit 右手整段：貼頭（開頭 0.15 秒把搓頭收掉）→ 動作庫走路時垂下的手（TE.state(s, arc_w=1) 的右手），
    _mix_arm_fk 關節角內插（fold＝中段手肘多彎幾度），弧長表重新參數化、梯形速度 low 秒"""
    arm = ns["ARM"]; k = ns["_kof"](arm); seg_ = ns["seg"]
    c = SCR3; dur = float(globals().get("SCR3_LOW", c["low"])); fold = float(globals().get("SCR3_FOLD", c["fold"]))
    roll = c["roll"]; REF = {}

    lift = float(globals().get("SCR3_LIFT", 0.05)) * k               # 離開時先沿頭髮法線抬離（w 0～0.35 抬 lift），再往身體放

    def ends(P, s, w=0.0):
        a = scratch_fix(ns, P, scr_state(P, scr_end * (1 - seg_(s, 0.0, 0.15)), lift * ease(seg_(w, 0.0, 0.35))), hcen(P), phi, 1.0)
        b = TE.state(s, arc_w=1.0)["arms"]["R"]
        return a, b

    L1, L2 = ns["_len_arm"](arm, "R")
    MID = dict(SCR3_MID)
    if globals().get("SCR3_MID_OUT"):
        MID["out"] = tuple(float(x) for x in str(globals()["SCR3_MID_OUT"]).split(","))
    for k_ in ("e", "f"):
        if globals().get("SCR3_MID_" + k_.upper()):
            MID[k_] = tuple(float(x) for x in str(globals()["SCR3_MID_" + k_.upper()]).split(","))

    def mid(P):
        """過渡姿勢（跟著胸口）：手肘往下收在身側偏外，前臂往上、手在耳朵旁（手腕直、掌心朝頭）"""
        Mc = ns["_fkc"](arm, P, "UpperChest").to_3x3()
        rt, fw, up = Mc @ Vector((-1, 0, 0)), Mc @ Vector((0, -1, 0)), Mc @ Vector((0, 0, 1))
        S = ns["_shoulder"](arm, P, "R")
        de = (rt * MID["e"][0] + fw * MID["e"][1] + up * MID["e"][2]).normalized(); E = S + de * L1
        df = (rt * MID["f"][0] + fw * MID["f"][1] + up * MID["f"][2]).normalized(); W = E + df * L2
        pin = -rt; pin = (pin - df * pin.dot(df)).normalized()
        R = ns["_rot_map"](Vector((0, 1, 0)), ns["_PALM_LOC"]["R"], df, pin)
        pole = E + (E - (S + W) * 0.5) * 2.0
        return (W, pole, R)
    REF2 = {}

    def mix(P, a, b, w):
        if not MID.get("on", 1):
            return ns["_mix_arm_fk"](a, b, w, arm, P, "R", ref=REF, fold=fold, roll=roll)
        m = mid(P); wm = float(MID.get("w", 0.45))
        # 兩段：貼頭 → 過渡（手肘收下來、手在耳朵旁）→ 垂手，各自關節角內插；弧長表讓接點速度連續。
        # 不用巢狀內插（de Casteljau）：兩段中間的上臂扭轉會差到接近 180°，外層取最短路徑在 7.65 秒換邊（一格 12°）、固定正負號則 8.33 秒前臂翻面（一格 42°）
        if w < wm:
            return ns["_mix_arm_fk"](a, m, w / wm, arm, P, "R", ref=REF)
        u = (w - wm) / (1.0 - wm)
        st2 = ns["_mix_arm_fk"](m, b, u, arm, P, "R", ref=REF2)
        # 第二段中途手腕往身體外側／前方繞一段弧（sin），不然 8.1 秒前臂擦進身體 15～20 mm
        out = MID.get("out", (0.0, 0.0))
        if out[0] or out[1]:
            Mc = ns["_fkc"](arm, P, "UpperChest").to_3x3()
            off = (Mc @ Vector((-1, 0, 0)) * out[0] + Mc @ Vector((0, -1, 0)) * out[1]) * k * math.sin(math.pi * u)
            st2 = (Vector(st2[0]) + off, Vector(st2[1]) + off, st2[2])
        return st2
    P3 = TE.state(0.25)["P"]; b3 = ends(P3, 0.25)[1]
    arc = ns["_arc_table"](arm, P3, lambda w: {"R": mix(P3, ends(P3, 0.25, w)[0], b3, w)})
    print("V2_05_EXIT3 dur", dur, "fold", fold, "total_deg", round(arc.total, 1), flush=True)

    def fix(P, st, s):
        w = arc(ns["_tr"](s, 0.0, dur, float(c["low_tr"])))
        a, b = ends(P, s, w)
        armR = mix(P, a, b, w)
        hc_ = hcen(P); dvec = Vector(armR[0]) - hc_; rmin = 0.15 * k
        f = seg_(w, 0.0, 0.25) if int(globals().get("SCR3_EXIT_PUSH", 0)) else 0.0   # 放手不推：抬離由 lift（沿頭髮法線 5 cm）負責，推的話 7.67 秒上臂一格 15°
        if dvec.length < rmin and f > 0:
            Wn = hc_ + dvec.normalized() * (dvec.length + (rmin - dvec.length) * f); dW = Wn - Vector(armR[0])
            armR = (Wn, Vector(armR[1]) + dW, armR[2])
        if COLL3.get("fn") and w < 0.85:
            armR = COLL3["fn"](P, armR)
        return armR
    return fix


# 新郎（第 3 輪回饋 1：「舉手看著路人甲，這裡手可以放下跟左手一樣，頭只要跟隨路人甲方向移動就好」）：
#   3.6 秒起 lookout（手遮眉＋整個人原地轉 45°）拿掉 → 雙手垂放（arms_down，和 peace 的左手同一個角度）＋呼吸，站位不轉（腳不滑）；
#   頭、脖子、一點點上身跟著路人甲轉（look-at：路人甲骨盆的水平位置，平滑過 0.5 秒；轉角 Head 60%、Neck 25%、Spine 15%），
#   4.0～4.7 秒轉過去、接 nod 時繼續看著他（nod 只加點頭，手不變）
G05L = dict(smooth=0.25, split=(0.60, 0.25, 0.15), clamp=75.0, arms_bl=0.6)


def g05_place3(t):
    return (G05[0], G05[1], face_to(G05, OC))


def g05_stand(tl):
    P = GR["arms_down"]({})
    GR["breathe"](P, (tl / 2.4) % 1.0)
    return dict(P, face={"Fcl_ALL_Joy": 0.6})


def look_table(AP, t_in, pos, rz_deg):
    """路人甲骨盆的水平位置 → 站在 pos、面向 rz_deg 的人頭要轉的角度（骨架空間 Z，正＝往角色左邊），每 1/60 秒一點、前後 smooth 秒平均；
    另外回傳路人甲在鏡頭水平視野內的時間（進畫面、出畫面，以他的身體中心算，鏡頭水平半視角＝atan(18/焦距)）"""
    rz = math.radians(rz_deg); g = Vector(pos[:2]); c = V2_05
    cam = Vector(c["cam"][:2]); fwd = (Vector(c["aim"][:2]) - cam).normalized(); half = math.degrees(math.atan(18.0 / c["lens"]))
    ts = [3.4 + i / 60.0 for i in range(int((9.6 - 3.4) * 60) + 1)]; raw = []; vis = []
    for t in ts:
        P = AP._at(max(t, t_in))[0]; r = P.get("root", (0, 0, 0))
        d = Vector((r[0], r[1])) - g
        dx = d.x * math.cos(-rz) - d.y * math.sin(-rz); dy = d.x * math.sin(-rz) + d.y * math.cos(-rz)
        raw.append(math.degrees(math.atan2(dx, -dy)))
        v = Vector((r[0], r[1])) - cam
        vis.append(t >= t_in and abs(math.degrees(fwd.angle_signed(v))) < half - 1.0)
    h = int(G05L["smooth"] * 60); sm = []
    for i in range(len(raw)):
        win = raw[max(0, i - h):i + h + 1]; sm.append(sum(win) / len(win))
    t_vis = next((t for t, v in zip(ts, vis) if v), t_in)
    t_out = next((t for t, v in zip(ts, vis) if t > t_vis + 0.5 and not v), 99.0)
    return ts, sm, t_vis, t_out


def g05_look_table(AP, t_in):
    return look_table(AP, t_in, G05, g05_place3(0)[2])


def look_yaw(tab, t, delay=0.0):
    """look-at 的轉角：路人甲進畫面（t_vis＋delay）起 0.7 秒轉過去、出畫面後 0.6 秒轉回正面"""
    ts, sm, t_vis, t_out = tab
    x = (min(max(t, ts[0]), ts[-1]) - ts[0]) * 60.0; i = min(int(x), len(sm) - 2); f = x - i
    y = sm[i] * (1 - f) + sm[i + 1] * f
    y = max(-G05L["clamp"], min(G05L["clamp"], y))
    a = t_vis + delay
    return y * ease(seg01(t, a, a + 0.7)) * (1.0 - ease(seg01(t, t_out + delay, t_out + delay + 0.6)))


def g05_yaw(t):
    S = V2S.get("05")
    if not S or "look" not in S:
        return 0.0
    return look_yaw(S["look"], t)


def b05_mod3(t, P):
    """新娘（第 3 輪補充回饋）：拿掉 tilt／shake，頭跟著路人甲轉（比新郎晚 0.15 秒），路人甲出畫面後回正面"""
    S = V2S.get("05")
    if not S or "look_b" not in S:
        return P
    y = look_yaw(S["look_b"], t, B05L["delay"])
    if abs(y) > 1e-4:
        P = dict(P); a, b, c = B05L["split"]
        for n, f in (("Head", a), ("Neck", b), ("Spine", c)):
            P[n] = list(P.get(n, [])) + [("Z", y * f)]
    return P


B05L = dict(delay=0.15, split=(0.60, 0.25, 0.15))


def g05_mod3(t, P):
    P = g05_mod(t, P)
    y = g05_yaw(t)
    if abs(y) > 1e-4:
        a, b, c = G05L["split"]
        for n, f in (("Head", a), ("Neck", b), ("Spine", c)):
            P[n] = list(P.get(n, [])) + [("Z", y * f)]
    return P


def v2_05_setup():
    if V2S.get("05"):
        return V2S["05"]
    c = V2_05
    PB = V2S.get("PB")
    if PB is None:
        PB = add_character(PASSERBY_PROJ); V2S["PB"] = PB
        PB["wear"]("costume"); PB["mesh_eval"](False, PB["ARM"].name)
    v = Vector((c["aim"][0] - c["cam"][0], c["aim"][1] - c["cam"][1])).normalized(); rgt = Vector((v.y, -v.x))      # 畫面右方向
    stop = Vector(c["p_stop"]); org = stop + rgt * c["walk_out"]
    KW = dict(origin=tuple(org), stop=tuple(stop), steps=c["steps"], face=c["face"], feet_turn=0.65, phone_dist=0.25)
    WI = PB["walk_in_photo"](dur=1.3, **KW)
    OB = PB["oops_bow"](photo_dur=1.3, cam=None, look=-100.0, bow=30.0, dur=0.8, **KW)
    TE = PB["turn_exit"](photo_dur=1.3, cam=None, look=-100.0, bow=30.0, bow_dur=0.8, exit_dirx=1, out=0.65, stride=0.24, settle=False, **KW)
    # 2026-10-09 第 2 輪：抱頭的右手掌貼頭、手腕順著前臂（情境覆寫 scratch_fix，動作庫不改）
    if not int(globals().get("SCRATCH_LEGACY", 0)):
        sg_ = PB["seg"]; A_ = PB["ARM"]
        hcen = lambda P: PB["_fkc"](A_, P, "Head") @ OB.head_c
        st_ref = OB.state(0.75)
        best = scratch_phi(PB, st_ref["P"], st_ref["arms"]["R"], hcen(st_ref["P"]))
        phi = float(globals().get("SCRATCH_PHI", best[1]))
        print("V2_05_SCRATCH phi", phi, "best", [round(x, 3) for x in best], flush=True)
        a, b_ = [float(x) for x in str(globals().get("SCRATCH_OOPS", "")).split(",")] if globals().get("SCRATCH_OOPS") else SCRATCH_W["oops"]
        a2, b2 = [float(x) for x in str(globals().get("SCRATCH_EXIT", "")).split(",")] if globals().get("SCRATCH_EXIT") else SCRATCH_W["exit"]
        if int(globals().get("SCRATCH_R2", 0)):         # 第 2 輪（改前對照）
            if globals().get("SCRATCH_OOPS"):           # 試驗用：原路徑和修正後的狀態直接內插
                OB = rearm(PB, OB, lambda P, st, s: scratch_fix(PB, P, st, hcen(P), phi, ease(sg_(s, a, b_))))
            else:
                OB = rearm(PB, OB, oops_path_fix(PB, OB, hcen, phi))
            TE = rearm(PB, TE, lambda P, st, s: scratch_fix(PB, P, st, hcen(P), phi, 1.0 - ease(sg_(s, a2, b2))))
        else:                                           # 第 3 輪：貼頭髮網格＋關節角放下
            k_ = PB["_kof"](A_)
            c3, n3, R3, tup3 = scr3_contact(PB, OB)
            sst = scr3_state(PB, c3, n3, R3, tup3, float(globals().get("SCR3_GAP", SCR3["gap"])))
            st_ref = OB.state(0.75); P_ref = st_ref["P"]
            best3 = scratch_phi(PB, P_ref, sst(P_ref, 0.0), hcen(P_ref))
            phi3 = float(globals().get("SCRATCH_PHI", best3[1]))
            print("V2_05_SCR3 phi", phi3, "best", [round(x, 3) for x in best3], "n", [round(x, 2) for x in n3], flush=True)
            scr_end = 0.008 * k_ * math.sin(2 * math.pi * 3.0 * max(0.0, 0.8 - 0.66)) * sg_(0.8, 0.66, 0.70)
            TE0 = TE
            COLL3["fn"] = None if int(globals().get("SCR3_NOCOLL", 0)) else hand_collide(PB, OB, n3, float(globals().get("SCR3_MARGIN", 0.002)))
            PB["HANDS"]["headpat"] = HEADPAT
            OB = rearm(PB, OB, oops3_fix(PB, OB, hcen, phi3, sst), lambda s, h: (h[0], ("pinch", "headpat", round(sg_(s, 0.05, 0.40), 2))))
            TE = rearm(PB, TE0, exit3_fix(PB, TE0, hcen, phi3, sst, scr_end), lambda s, h: (h[0], ("headpat", "relax", round(sg_(s, *HP_EXIT), 2))))
    t = T05; t_in = c["walk_end"] - WI.dur

    def ab(F, t0):
        return lambda tl: dict(F(max(0.0, min(0.9999, (tl - t0) / F.dur))), abs=True)
    AP = Actor2(PB, [(0.0, c["walk_end"], ab(WI, t_in), 0.0),
                     (t["oops"][0], t["oops"][1], ab(OB, 0.0), 0.0), (t["exit"][0], 10.0, ab(TE, 0.0), 0.0)], lambda tt: (0.0, 0.0, 0.0))
    if int(globals().get("LOOK_LEGACY", 0)) or int(globals().get("G05_LEGACY", 0)):     # 第 2 輪（lookout 手遮眉＋原地轉 45°）
        AG = Actor2(GR, [(0, 3.6, "peace", 0.3), (3.6, 6.6, "lookout", 0.3), (6.6, 9.5, "nod", 0.3)], s05_place_g,
                    None if int(globals().get("G05_LEGACY", 0)) else g05_mod)
    else:
        AG = Actor2(GR, [(0, 3.6, "peace", 0.3), (3.6, 6.6, g05_stand, G05L["arms_bl"]), (6.6, 9.5, "nod", 0.3)], g05_place3, g05_mod3)
    if int(globals().get("LOOK_LEGACY", 0)) or int(globals().get("G05_LEGACY", 0)):
        AB = Actor2(B, [(0, 3.6, _bq_head(None, 0.0), 0.3), (3.6, 6.3, _bq_head("tilt", 3.6), 0.3), (6.3, 9.5, _bq_head("shake", 6.3), 0.3)], s05_place_b)
    else:                                               # 第 3 輪補充：整段捧花，頭只跟著路人甲（tilt／shake 拿掉）
        AB = Actor2(B, [(0, 9.5, _bq_head(None, 0.0), 0.0)], s05_place_b, b05_mod3)
    A = PB["ARM"]

    def hand_m(side):
        bpy.context.view_layer.update()
        return A.matrix_world @ A.pose.bones[f"J_Bip_{side}_Hand"].matrix

    def phone_m(st):
        C, up, fwd = st["phone"]; M = A.matrix_world
        y = (M.to_3x3() @ Vector(up)).normalized(); z = M.to_3x3() @ Vector(fwd); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
        R = Matrix((x, y, z)).transposed().to_4x4(); R.translation = M @ Vector(C)
        return R
    # 手機：walk_in_photo 的 t_phone 秒（雙手拿好）前跟著右手、之後照動作庫給的位置；oops_bow、turn_exit 跟著左手（相對位置取 walk_in_photo 結尾那格）
    tp = WI.t_phone
    AP.pose(t_in + tp); relR = hand_m("R").inverted() @ phone_m(WI.state(tp))
    AP.pose(c["walk_end"] - 1e-3); relL = hand_m("L").inverted() @ phone_m(WI.state(WI.dur))
    S = dict(PB=PB, WI=WI, OB=OB, TE=TE, AP=AP, AG=AG, AB=AB, KW=KW, hand_m=hand_m, phone_m=phone_m, relR=relR, relL=relL, t_in=t_in)
    S["look"] = g05_look_table(AP, t_in)
    S["look_b"] = look_table(AP, t_in, B05, s05_place_b(0)[2])
    for nm in ("look", "look_b"):
        L_ = S[nm]
        print("V2_05_LOOK", nm, "in_frame", round(L_[2], 2), "out", round(L_[3], 2), "yaw", [(round(t_, 1), round(y_, 1)) for t_, y_ in zip(L_[0], L_[1])][::30], flush=True)
    sh = WI.times.get("shot") if isinstance(getattr(WI, "times", None), dict) else None
    print("V2_05_SETUP passerby origin", [round(v_, 3) for v_ in org], "stop", [round(v_, 3) for v_ in WI.stop], "walk_in", round(t_in, 2), "→",
          c["walk_end"], "dur", round(WI.dur, 2), "walk_end", round(t_in + WI.walk_end, 2), "phone", round(t_in + tp, 2),
          "shot", round(t_in + sh, 2) if sh is not None else None, "exit stop", [round(v_, 3) for v_ in TE.stop], "turn_exit dur", round(TE.dur, 2), flush=True)
    V2S["05"] = S
    SHOTS["v2_05"]["actors"] = [AG, AB, AP]
    return S


def v2_05_build():
    need_garden()
    c = v2_coll()
    if "V2_Phone" not in bpy.data.objects:
        build_phone(coll_new("V2_PhoneSet", c))
    v2_05_setup()


def v2_05_props(t):
    S = V2S["05"]; t0 = S["t_in"]
    bq = bpy.data.objects["G_Bouquet"]                              # 捧花（同第一版 ⑤：放在新娘兩手中間）
    bpy.context.view_layer.update()
    wl, wr = hand_frame(B, "L")[0], hand_frame(B, "R")[0]
    cc = (wl + wr) / 2
    fwd = place_matrix(*s05_place_b(t)).to_3x3() @ Vector((0, -1, 0))
    Mb = (fwd * 0.5 + Vector((0, 0, 1))).to_track_quat("Z", "Y").to_matrix().to_4x4(); Mb.translation = cc + fwd * 0.03 + Vector((0, 0, 0.02))
    bq.matrix_world = Mb
    if t < t0 - 0.05:                                              # 手機
        phone_set(Vector((0, 0, -50)), Vector((0, 0, 1)), Vector((0, 1, 0)), show=False); return
    s = t - t0
    if s < S["WI"].t_phone:
        M = S["hand_m"]("R") @ S["relR"]
    elif s < S["WI"].dur:
        M = S["phone_m"](S["WI"].state(s))
    else:
        M = S["hand_m"]("L") @ S["relL"]
    phone_set(M.translation, M.col[1].to_3d(), M.col[2].to_3d())


def v2_05_frame(t, props=True, cast=True, cam=True):
    S = v2_05_setup()
    if props:
        garden_parts(("G_Cam",)); v2_parts(("V2_PhoneSet",)); oldcam_aim((0, ARCH_Y, 1.15)); oldcam_lamp(t)
        petals_update(t, lambda i, rnd: None if i >= 40 else (rnd.uniform(0, 9), arc_pt(rnd.uniform(0.05, 0.6), ARCH_Y), (0, -0.2, 0)))
        cp = bpy.data.collections.get("Cast_passerby")
        if cp:
            on = t >= S["t_in"] - 0.05
            cp.hide_render = not on; cp.hide_viewport = not on
    if cast:
        S["AG"].pose(t); S["AB"].pose(t); S["AP"].pose(max(t, S["t_in"]))
    if props:
        v2_05_props(t)
    if cam:
        c = V2_05
        u = seg01(t, 0.4, 2.4)                           # 拉焦：前景老相機 → 拱門下的新人
        cm = look(Vector(c["cam"]), Vector(c["aim"]), c["lens"])
        d_near = (Vector((-2.05, -2.35, 1.31)) - cm.location).length
        d_far = (Vector((0.0, ARCH_Y, 1.2)) - cm.location).length
        cm.data.dof.use_dof = True; cm.data.dof.aperture_fstop = c["fstop"]
        cm.data.dof.focus_distance = d_near + (d_far - d_near) * u


SHOTS["v2_05"] = dict(set="Set_Garden", cast=True, t0=0.0, dur=9.0, tail=0.0, build=v2_05_build, frame=v2_05_frame,
                      actors=[], qa_skip=[(3.6, 4.0), (6.3, 6.7)] if (int(globals().get("LOOK_LEGACY", 0)) or int(globals().get("G05_LEGACY", 0))) else [], stills=[0.3, 2.8, 3.9, 4.4, 5.0, 5.6, 6.4, 6.9, 7.4, 7.8, 8.4, 8.9])
