# B1→B2「經過」（開場影片提案 B，手機 → 餐檯）：新郎走路 → 放慢停下 → 雙手拿手機、右手拇指 6.2 秒點靜音開關 → 起步走掉，11.2 秒；
# 手機 4.9 秒「啵」一下冒出來。使用者 2026-10-12 定案第 4 版（還沒穿衣服）。
# 2026-10-12 搬進動畫工作流：共通的部分改用 zanim（場景、讀 Mixamo、擺姿勢、拍照、清場景），這裡只留這一鏡專用的
# （接段計畫、低頭、手機與握法、拇指點開關、「啵」）。動作內容和搬家前完全一樣（搬家後重建比對過每一格）。
# 用法（MCP）：
#   # BODY=groom
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b1_b2"); import b1b2_shot as S; print(S.run_r3())
import bpy, os, sys, math, json, time
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
from zanim import STATE, L, mr, _ctx, _aim, bone_world, in_scene, _head_bvh, _inside, stats, pose_at

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = "B12_WORK"
PREFIX = "B12_"                      # 攝影棚物件沿用搬家前的名字（B12_studio、B12_Cam…），這一鏡的程式都認這些名字


def setup(res=(640, 640)):
    r = Z.setup(body="groom", scene=SCENE, prefix=PREFIX, res=res)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b1_b2")[1]
    Z.POSE_HOOKS.append(_phone_hook)
    Z.CAM_HOOKS.append(_stars_face)
    return r


def load_clips(names=("male_standard_walk", "male_stop_walk", "texting_standing", "male_start_walk")):
    return Z.load_clips(names)


def _phone_hook(i):
    """pose_at 的 hook：這一格顯示哪支手機（phone_zp → 點到開關那一格起換 phone_mute_zp）、位置、「啵」"""
    if "phone" not in STATE:
        return
    import b1b2_r3
    Mp = STATE["phone"][i]; wh = STATE.get("phone_which", [None] * len(STATE["phone"]))[i]
    for nm in ("B12_Phone", "B12_PhoneMute"):
        ph = bpy.data.objects.get(nm)
        if ph is None:
            continue
        ph.hide_render = Mp is None or nm != wh
        if Mp is not None:
            ph.matrix_world = STATE["arm"].matrix_world @ Mp @ b1b2_r3.PROP_FROM_PHONE
    _pop_apply(i)


def phone_focus(dz=0.0):
    """shots() 的 focus：對準手機（這一格沒有手機就對最後一次手機的位置）"""
    def f(i):
        Mp = STATE.get("phone", [None] * (i + 1))[i]
        return STATE["arm"].matrix_world @ (Mp.translation if Mp is not None else STATE["phone_c_last"])
    return f


def shots(times, focus="J_Bip_C_Hips", dist=1.6, out=None, views=None, dz=0.0, lens=50):
    """同 zanim.shots；focus="phone" 對準手機"""
    return Z.shots(times, focus=phone_focus() if focus == "phone" else focus, dist=dist, out=out, views=views, dz=dz, lens=lens, up=0.12)


def cleanup():
    return Z.cleanup(SCENE)


# ════════ 接段計畫 ════════

def default_plan():
    """B1→B2：走路 → 放慢停下 → 低頭按手機 → 起步 → 走路。側面跟拍：角色往 +X 走（面向 yaw 90°）"""
    tgt = STATE["tgt"]; C = lambda n: L.clip(tgt, n)
    return dict(
        segs=[mr.Seg(C("male_standard_walk"), loops=2, name="走路（Walking）"),
              mr.Seg(C("male_stop_walk"), name="放慢停下（Stop Walking）"),
              mr.Seg(C("texting_standing"), 0, int(4.4 * 30), name="按手機（Texting While Standing 0～4.4 秒）"),
              mr.Seg(C("male_start_walk"), name="起步（Start Walking）"),
              mr.Seg(C("male_standard_walk"), loops=1, name="走路（Walking）")],
        blend=0.3, anchor=(0.0, (0.0, 0.0), 90.0))


def matched_plan():
    """第 2 版：每個接縫找腿部姿勢最像的那一格剪接（b12_fix.match_phase）"""
    import zanim_fix as F
    tgt = STATE["tgt"]; C = lambda n: L.clip(tgt, n)
    W, ST, TX, SW = C("male_standard_walk"), C("male_stop_walk"), C("texting_standing"), C("male_start_walk")
    wn = W["n"] - 1                                                  # 走路一圈的格數（第 0 格＝第 wn 格）
    a1, b1, d1 = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))              # 走路 → 停下
    a2, b2, d2 = F.match_phase(tgt, ST, range(ST["n"] - 20, ST["n"] - 9), TX, range(0, 31))   # 停下 → 按手機
    a3, b3, d3 = F.match_phase(tgt, TX, range(int(3.6 * 30), int(4.6 * 30)), SW, range(0, 12))  # 按手機 → 起步
    a4, b4, d4 = F.match_phase(tgt, SW, range(SW["n"] - 30, SW["n"] - 9), W, range(0, wn))  # 起步 → 走路
    # 起步之後的走路從第 b4 格開始：把走路循環「轉」成從 b4 起（剪接成新的一支）
    cyc = wn / 30.0
    W2 = mr.splice_clip(W, [(b4 / 30, cyc), (0, cyc, 1 / 30), (0, cyc, 1 / 30)])
    STATE["match"] = dict(walk_to_stop=(a1, b1, d1), stop_to_text=(a2, b2, d2), text_to_start=(a3, b3, d3), start_to_walk=(a4, b4, d4))
    # Sequence 的漸變從「前一段結束前 blend 秒」開始、而且下一段的位置和面向是對齊在漸變的起點：
    # 所以前一段要多播 X 格（剛好一個漸變長度），下一段從配對格 b 開始 → 漸變起點兩邊正好是配對的那一對格子，之後兩邊同步往前
    X = 9
    return dict(
        segs=[mr.Seg(W, 0, wn, loops=1 + (a1 + X) / wn, name="走路（Walking）"),
              mr.Seg(ST, b1, a2 + X, name="放慢停下（Stop Walking）"),
              mr.Seg(TX, b2, a3 + X, name="按手機（Texting While Standing）"),
              mr.Seg(SW, b3, a4 + X, name="起步（Start Walking）"),
              mr.Seg(W2, 0, int(1.2 * 30), name="走路（Walking）")],
        blend=X / 30, anchor=(0.0, (0.0, 0.0), 90.0))


def snap(R, h, Mp, out, tag, which="B12_Phone", views=(("face", None), ("front", 90), ("main", 0)), dist=0.45, lens=50):
    """單一姿勢的近照（第 3 輪試握法用）：face＝從臉的位置看手機（螢幕那一面）"""
    import b1b2_r3 as R3
    sc = STATE["sc"]; cam = sc.camera; arm = STATE["arm"]
    mr.apply_pose(arm, STATE["tgt"], R, h)
    for nm in ("B12_Phone", "B12_PhoneMute"):
        o = bpy.data.objects.get(nm)
        if o is not None:
            o.hide_render = (nm != which) or Mp is None
            if Mp is not None:
                o.matrix_world = arm.matrix_world @ Mp @ R3.PROP_FROM_PHONE
    sc.view_layers[0].update()
    os.makedirs(out, exist_ok=True); sc.render.image_settings.file_format = "JPEG"
    c = arm.matrix_world @ Mp.translation if Mp is not None else bone_world("J_Bip_C_Chest")
    files = []
    for name, az in views:
        if az is None:                                   # 從頭的右後上方往下看螢幕（肩後視角；臉的位置被頭擋住）
            loc = c + Vector((0.02, -0.20, 0.36)) * (dist / 0.45)
        elif isinstance(az, tuple):                     # 直接給偏移（m，角色往 +X 走）
            loc = c + Vector(az)
        else:
            r = math.radians(az); loc = c + Vector((math.sin(r) * dist, -math.cos(r) * dist, 0.25 * dist))
        _aim(cam, loc, c, lens)
        sc.render.filepath = os.path.join(out, f"{tag}_{name}.jpg")
        with bpy.context.temp_override(**_ctx(sc)):
            bpy.ops.render.render(write_still=True, scene=sc.name)
        files.append(sc.render.filepath)
    return files


# ════════ 第 2 輪：低頭調淺、手機、起步不下沉 ════════
def build_r2(keep=0.4, phone_on_z=0.78, kmax=10.0, uncurl=0.0, uncurl_l=0.0, up=0.0, fwd_d=0.0):
    import zanim_fix as F, b1b2_r2 as R2
    tgt = STATE["tgt"]
    base = matched_plan()
    seq = mr.Sequence(tgt, base["segs"], blend=base["blend"]); seq.place(0.0, (0, 0), 90.0)
    n = int(seq.dur * 30) + 1
    raw = [seq.at(i / 30)[:2] for i in range(n)]
    T = seq.T; segs = base["segs"]
    t_text = (T[2][0], T[2][0] + segs[2].dur); t_start = (T[3][0], T[3][0] + segs[3].dur)
    info = {}
    # 1. 低頭調淺
    P = []
    pmax0 = pmax1 = 0.0
    for R, h in raw:
        p0 = R2.head_pitch(tgt, R); R = R2.lift_head(tgt, R, keep=keep)
        pmax0 = max(pmax0, p0); pmax1 = max(pmax1, R2.head_pitch(tgt, R)); P.append((R, h))
    info["head_pitch_max_before"] = round(pmax0, 1); info["head_pitch_max_after"] = round(pmax1, 1)
    # 3. 起步不下沉：起步段開頭到第一步踩穩（起步段前 1.6 秒）
    a = int(t_start[0] * 30); b = int((t_start[0] + 1.6) * 30)
    a = int((t_start[0] - 0.1) * 30); b = int((t_start[0] + 1.75) * 30)
    z0 = [P[i][1].z for i in range(a, b + 1)]
    STATE["knee_before"] = knee_profile(P, a, b)
    P, dz = R2.straighten_stance(tgt, P, L.sole_points(STATE["arm"]), a, b, kmax=kmax, zcap=P[a][1].z + 0.002)
    STATE["knee_after"] = knee_profile(P, a, b)
    info["stance_knee_max_before"] = max(k for k, _ in STATE["knee_before"])
    info["stance_knee_max_after"] = max(k for k, _ in STATE["knee_after"])
    info["start_hip_drop_before_mm"] = round(1000 * (P[a][1].z - min(z0)), 1)
    info["start_hip_drop_after_mm"] = round(1000 * (P[a][1].z - min(P[i][1].z for i in range(a, b + 1))), 1)
    info["start_hip_raise_max_mm"] = round(1000 * dz, 1)
    # 2. 手機：左手拿、右手貼另一邊；只在按手機段、雙手舉起來（左手高於 phone_on_z）時出現
    ta, tb = t_text
    vis = [False] * n
    for i in range(int(ta * 30), min(n, int(tb * 30) + 1)):
        Hd = tgt.fk(*P[i]); vis[i] = Hd["J_Bip_L_Hand"].z > phone_on_z
    on = [i for i in range(n) if vis[i]]
    mid = (on[0] / 30 + 0.6, on[-1] / 30 - 0.3)
    off_L, off_R = R2.phone_rig(tgt, P, mid)
    w = [0.0] * n
    for i in on:
        w[i] = 1.0
    for i in range(n):                                   # 右手前後 6 格漸入漸出
        if not vis[i]:
            d = min([abs(i - j) for j in (on[0], on[-1])])
            if d <= 6:
                w[i] = mr._smooth(1 - d / 7)
    phone = [None] * n
    for i in range(n):
        R, h = P[i]; Hd = tgt.fk(R, h)
        Mp = R2.hand_frame(tgt, R, Hd, "L") @ off_L
        if w[i] > 0 and (up or fwd_d):
            R, Mp = R2.lift_left(tgt, R, h, off_L, up, fwd_d, w[i])
        if w[i] > 0:
            R = R2.place_right(tgt, R, h, Mp, off_R, w[i])
            R = R2.open_fingers(tgt, R, "R", uncurl * w[i])
            R = R2.open_fingers(tgt, R, "L", uncurl_l * w[i])
        P[i] = (R, h)
        phone[i] = Mp if vis[i] else None
    info["phone_visible_s"] = (round(on[0] / 30, 2), round(on[-1] / 30, 2))
    ok = [p for p in phone if p is not None]
    info["phone_center_z_m"] = (round(min(p.translation.z for p in ok), 3), round(max(p.translation.z for p in ok), 3))
    info["phone_tilt_deg"] = round(sum(math.degrees(math.acos(max(-1, min(1, p.col[2].to_3d().normalized().z)))) for p in ok) / len(ok), 1)   # 螢幕法線離垂直幾度（0＝平放朝上）
    # 鎖腳
    P, _li = F.foot_lock(tgt, P, L.sole_points(STATE["arm"]), v_on=0.3, ramp=9)
    STATE.update(poses=P, seq=seq, raw=raw, phone=phone, labels=[seq.which(i / 30) for i in range(n)],
                 segs=[(round(seq.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    STATE["stats"] = stats()
    info.update(phone_checks())
    STATE["r2"] = info
    return dict(dur=round(seq.dur, 2), segs=STATE["segs"], stats=STATE["stats"]["summary"], r2=info)


def base_r3(keep=0.4, kmax=10.0):
    """第 3 輪的底：Mixamo 原樣接好＋低頭調淺＋起步不下沉（同第 2 輪的參數）；手機和手另外做。→ STATE["P0"]"""
    import b1b2_r2 as R2
    tgt = STATE["tgt"]
    base = matched_plan()
    seq = mr.Sequence(tgt, base["segs"], blend=base["blend"]); seq.place(0.0, (0, 0), 90.0)
    n = int(seq.dur * 30) + 1
    raw = [seq.at(i / 30)[:2] for i in range(n)]
    T = seq.T; segs = base["segs"]
    t_text = (T[2][0], T[2][0] + segs[2].dur); t_start = (T[3][0], T[3][0] + segs[3].dur)
    info = {}; P = []; pmax0 = pmax1 = 0.0
    for R, h in raw:
        p0 = R2.head_pitch(tgt, R); R = R2.lift_head(tgt, R, keep=keep)
        pmax0 = max(pmax0, p0); pmax1 = max(pmax1, R2.head_pitch(tgt, R)); P.append((R, h))
    info["head_pitch_max_before"] = round(pmax0, 1); info["head_pitch_max_after"] = round(pmax1, 1)
    import zanim_fix as F
    P, off = F.ground(tgt, P, L.sole_points(STATE["arm"]))
    info["ground_offset_mm"] = (round(1000 * min(off), 1), round(1000 * max(off), 1))
    a = int((t_start[0] - 0.1) * 30); b = int((t_start[0] + 1.75) * 30)
    z0 = [P[i][1].z for i in range(a, b + 1)]
    P, dz = R2.straighten_stance(tgt, P, L.sole_points(STATE["arm"]), a, b, kmax=kmax, zcap=P[a][1].z + 0.002)
    info["start_hip_drop_before_mm"] = round(1000 * (P[a][1].z - min(z0)), 1)
    info["start_hip_drop_after_mm"] = round(1000 * (P[a][1].z - min(P[i][1].z for i in range(a, b + 1))), 1)
    info["start_hip_raise_max_mm"] = round(1000 * dz, 1)
    STATE.update(P0=P, raw=raw, seq=seq, t_text=t_text, t_start=t_start, info0=info,
                 segs=[(round(seq.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    return dict(dur=round(seq.dur, 2), t_text=[round(x, 2) for x in t_text], segs=STATE["segs"], info=info)


def build_r3(t_press=6.2, tilt=25.0, up=0.08, fwd_d=0.02, phone_on_z=0.80, hover=0.008, ref_t=6.2, smooth=4, lock=None):
    """第 3 輪：底（base_r3）→ 手機（兩手掌心中點往上抬、螢幕朝臉再仰 tilt 度）→ 兩手照握法（STATE["GL"]/["GR"]）放上去
    → 手指碰到就停（握法在參考格 ref_t 解一次，之後每格照用：手相對手機不動）→ 右手拇指點開關 → 鎖腳"""
    import zanim_fix as F, b1b2_r3 as R3
    tgt = STATE["tgt"]; P0 = STATE["P0"]; rad = STATE["rad"]; n = len(P0)
    GL, GR = STATE["GL"], STATE["GR"]
    ta, tb = STATE["t_text"]
    vis = [False] * n
    for i in range(int(ta * 30), min(n, int(tb * 30) + 1)):
        vis[i] = tgt.fk(*P0[i])["J_Bip_L_Hand"].z > phone_on_z
    on = [i for i in range(n) if vis[i]]
    w = [0.0] * n
    for i in range(n):
        if vis[i]:
            w[i] = 1.0
        else:
            d = min(abs(i - on[0]), abs(i - on[-1]))
            if d <= 6:
                w[i] = mr._smooth(1 - d / 7)
    # 手機理想位置（前後 smooth 格平均，去掉 Mixamo 手的小抖動）
    ideal = [None] * n
    for i in range(n):
        if w[i] > 0:
            ideal[i] = R3.tilt_up(R3.phone_pose(tgt, *P0[i], up=up, fwd_d=fwd_d), tilt)
    for i in range(n):
        if ideal[i] is not None:
            js = [j for j in range(i - smooth, i + smooth + 1) if 0 <= j < n and ideal[j] is not None]
            STATE.setdefault("_tmp", {})[i] = __import__("b1b2_r2")._avg_mat([ideal[j] for j in js])
    ideal = [STATE["_tmp"].get(i) for i in range(n)]; STATE.pop("_tmp")
    # 握法在參考格解一次
    i0 = int(ref_t * 30); R, h = P0[i0]
    RL, rL = R3.eval_grip(tgt, R, h, ideal[i0], rad["L"], "L", GL)
    RR_, rR = R3.eval_grip(tgt, RL, h, ideal[i0], rad["R"], "R", GR)
    curls = {"L": rL["curls"], "R": rR["curls"]}
    offL = R3.grip_local(tgt, "L", GL); offR = R3.grip_local(tgt, "R", GR)
    # 按開關：拇指兩個姿勢（相對手）在參考格解一次 → 下去 6 格、碰 3 格、上來 6 格，其他時候停在開關上方 hover
    touch, hov, prep = R3.thumb_press_poses(tgt, RR_, h, "R", ideal[i0], rad["R"], R3.SWITCH, hover)
    p0 = int(t_press * 30)
    def press_at(i):
        if p0 - 6 <= i < p0:
            return mr._smooth((i - (p0 - 6)) / 6)
        if p0 <= i < p0 + 3:
            return 1.0
        if p0 + 3 <= i < p0 + 9:
            return 1 - mr._smooth((i - (p0 + 3)) / 6)
        return 0.0
    P = list(P0); phone = [None] * n; which = [None] * n; press = {}
    for i in range(n):
        # 沒拿手機的格子手指一律用共用手勢 relaxed（Mixamo 原片的手指套到這副身體會食指、中指伸直像在比手勢）；
        # 拿手機時再從 relaxed 混到握法
        R, h = P0[i]
        for s in "LR":
            R = mr.gesture(tgt, R, s, "relaxed")
        if w[i] <= 0:
            P[i] = (R, h)
            continue
        Mp = ideal[i]
        R = R3.put_hand(tgt, R, h, "L", Mp @ offL, w[i])
        R = R3.put_hand(tgt, R, h, "R", Mp @ offR, w[i])
        Hd = tgt.fk(R, h)
        MpL = R3.hand_mat(tgt, R, Hd, "L") @ offL.inverted()       # 手機黏在左手（手伸不到時跟著手走）
        for s in "LR":
            R = mr.finger_pose(tgt, R, s, curls[s], None, w[i])
        k = press_at(i)
        loc = {t: hov[t].slerp(touch[t], k) for t in R3.THUMBS}
        R = R3.set_thumb(R, "R", loc, w[i])
        if abs(i - p0) <= 10 and vis[i]:
            g, qp = R3.thumb_pad(tgt, R, tgt.fk(R, h), "R", MpL.inverted(), rad["R"], True)
            gs = R3.sdf(qp, False) - rad["R"]["J_Bip_R_Thumb3"]
            press[i] = dict(k=round(k, 2), gap_switch_mm=round(1000 * g, 2), gap_screen_mm=round(1000 * gs, 2), pad_mm=tuple(round(1000 * x, 1) for x in qp))
        P[i] = (R, h)
        if vis[i]:
            phone[i] = MpL; which[i] = "B12_Phone" if i < p0 else "B12_PhoneMute"
    info = dict(STATE["info0"])
    info["phone_visible_s"] = (round(on[0] / 30, 2), round(on[-1] / 30, 2))
    info["press_s"] = round(p0 / 30, 2); info["press_ref"] = prep
    info["grip_ref"] = dict(L=rL["curls"], R=rR["curls"], why_L=rL["why"], why_R=rR["why"])
    P, _li = F.foot_lock(tgt, P, L.sole_points(STATE["arm"]), **(lock or dict(v_on=0.3, ramp=9)))
    STATE.update(poses=P, phone=phone, phone_which=which, press=press, vis=vis,
                 labels=[STATE["seq"].which(i / 30) for i in range(n)])
    STATE["stats"] = stats()
    STATE["r3"] = info
    return dict(stats=STATE["stats"]["summary"], r3=info)


def mesh_checks(step=3):
    """第 3 輪：用變形後的皮膚網格（不是骨頭近似）量手和手機。每 step 格一次（手機看得到的格子＋點開關那幾格）。
    每隻手：手指頂點最深陷進機身幾 mm（含螢幕面板、開關）、掌心頂點離機身最近幾 mm；右手拇指指腹離開關／螢幕"""
    import b1b2_r3 as R3
    arm = STATE["arm"]; body = L.body_mesh(arm); tgt = STATE["tgt"]
    if "hand_vids" not in STATE:
        gi = {g.index: g.name for g in body.vertex_groups}
        vids = {}
        for v in body.data.vertices:
            for g in v.groups:
                nm = gi.get(g.group, "")
                if g.weight > 0.3 and nm.startswith("J_Bip_") and ("Hand" in nm or any(f in nm for f in R3.FINGERS + ("Thumb",))):
                    side = nm.split("_")[2]; part = "palm" if nm.endswith("Hand") else ("thumb" if "Thumb" in nm else "finger")
                    vids.setdefault((side, part), set()).add(v.index)
        STATE["hand_vids"] = {k: sorted(s) for k, s in vids.items()}
    vids = STATE["hand_vids"]
    frames = [i for i, Mp in enumerate(STATE["phone"]) if Mp is not None and (i % step == 0 or i in STATE.get("press", {}))]
    vl = STATE["sc"].view_layers[0]; out = {}
    worst = {}; t0 = time.time()
    for i in frames:
        pose_at(i / 30); dg = vl.depsgraph; oe = body.evaluated_get(dg); me = oe.to_mesh()
        Mi = STATE["phone"][i].inverted() @ arm.matrix_world.inverted() @ body.matrix_world
        row = {}
        for (side, part), ids in vids.items():
            ds = [R3.sdf(Mi @ me.vertices[k].co, STATE["phone_which"][i] == "B12_PhoneMute") for k in ids]
            row[(side, part)] = min(ds)
        if i in STATE.get("press", {}):
            ids = vids[("R", "thumb")]
            row["thumb_switch"] = min(R3.sdf(Mi @ me.vertices[k].co, True) for k in ids)
            row["thumb_screen"] = min(R3.sdf(Mi @ me.vertices[k].co, False) for k in ids)
        oe.to_mesh_clear()
        out[i] = row
        for k, v in row.items():
            if k not in worst or v < worst[k][0]:
                worst[k] = (v, i)
    STATE["mesh_rows"] = out
    fmt = lambda k: k if isinstance(k, str) else f"{k[0]}_{k[1]}"
    return dict(frames=len(frames), sec=round(time.time() - t0, 1),
                min_mm={fmt(k): (round(1000 * v, 1), round(i / 30, 2)) for k, (v, i) in worst.items()})


def phone_checks():
    """手機和手：指尖、掌心離手機表面多遠（負＝穿進手機），左右掌心離手機邊的距離；手機離頭、離身體"""
    import b1b2_r2 as R2
    tgt = STATE["tgt"]; W, Hh, D = R2.PHONE
    pen = 0.0; pen_at = None; gapL = []; gapR = []; head_min = 9.9
    bvh = _head_bvh()
    for i, Mp in enumerate(STATE["phone"]):
        if Mp is None:
            continue
        R, h = STATE["poses"][i]; Hd = tgt.fk(R, h); Mi = Mp.inverted()
        for s in "LR":
            for b in ("Thumb2", "Thumb3", "Index2", "Index3", "Middle3", "Ring3", "Little3"):
                n = f"J_Bip_{s}_{b}"
                for p in (Hd[n], tgt.tail(R, Hd, n)):
                    q = Mi @ p
                    # 點在盒子裡多深（三軸都在裡面時，取離最近面的距離）
                    dx, dy, dz = W / 2 - abs(q.x), Hh / 2 - abs(q.y), D / 2 - abs(q.z)
                    if dx > 0 and dy > 0 and dz > 0:
                        dd = min(dx, dy, dz)
                        if dd > pen:
                            pen, pen_at = dd, (round(i / 30, 2), n)
            c, nrm, _d = R2.palm_info(tgt, R, Hd, s)
            q = Mi @ c
            (gapL if s == "L" else gapR).append(abs(q.x) - W / 2)
        Mh = (Matrix.Translation(Hd["J_Bip_C_Head"]) @ R["J_Bip_C_Head"].to_matrix().to_4x4()).inverted()
        for cx in (-1, 1):
            for cy in (-1, 1):
                p = Mp @ Vector((cx * W / 2, cy * Hh / 2, 0))
                loc, nrm, _i, d = bvh.find_nearest(Mh @ p)
                head_min = min(head_min, d)
    return dict(finger_in_phone_mm=round(pen * 1000, 1), finger_in_phone_at=pen_at,
                palmL_gap_mm=(round(min(gapL) * 1000, 1), round(max(gapL) * 1000, 1)),
                palmR_gap_mm=(round(min(gapR) * 1000, 1), round(max(gapR) * 1000, 1)),
                phone_head_min_mm=round(head_min * 1000, 1))


def phone_obj(key="phone_mute"):
    """素材庫的黏土風手機（集合實例，唯讀連結）；擺放時用 b12_r2.PROP_FROM_PHONE 從手機座標換到道具座標"""
    if "B12_Phone" in bpy.data.objects:
        return bpy.data.objects["B12_Phone"]
    g = {"__file__": r"D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/props-zepeto/use_props.py"}
    exec(open(r"D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/props-zepeto/use_props.py", encoding="utf8").read(), g)
    return g["place_prop"](key, name="B12_Phone", parent=bpy.data.collections["B12_studio"])


def knee_profile(P, a, b):
    """每格：踩地那隻腳（鞋底 ≤ 12 mm）膝蓋彎幾度（取大）、骨盆高度"""
    tgt = STATE["tgt"]; pts = L.sole_points(STATE["arm"]); out = []
    for i in range(a, b + 1):
        R, h = P[i]; Hd = tgt.fk(R, h); so = L.soles(tgt, R, h, pts); k = 0.0
        for s in "LR":
            if min(p.z for p in so[s]) <= 0.012:
                u = Hd[f"J_Bip_{s}_LowerLeg"] - Hd[f"J_Bip_{s}_UpperLeg"]; v = Hd[f"J_Bip_{s}_Foot"] - Hd[f"J_Bip_{s}_LowerLeg"]
                k = max(k, math.degrees(u.angle(v)))
        out.append((round(k, 1), round(h.z, 3)))
    return out


# ════════ 第 3 輪第 2 版：手機「啵」一下冒出來（使用者 2026-10-12 裁決） ════════
# 出現那 4 格手機從小放大到 1.15 再彈回 1，縮放中心在雙手握的位置（不是機身底部原點）；
# 旁邊 3 個小星星（2 個星形＋1 個圓點，素材庫 PAL 的 butter／ivory）放大後淡出，約 6 格。消失照舊
POP_SCALE = (0.30, 0.75, 1.15, 1.0)
STAR_SCALE = (0.5, 0.9, 1.1, 1.2, 1.2, 1.15)
STAR_ALPHA = (1.0, 1.0, 1.0, 0.7, 0.4, 0.15)
STARS = [  # (名稱, 形狀, 外半徑 m, 顏色, 手機座標裡的方向)
    ("B12_Star0", "star", 0.014, "#F6D77A", (-0.060, 0.055, 0.045)),     # 往螢幕前方（朝臉）45 mm，不被手擋住
    ("B12_Star1", "star", 0.011, "#F6D77A", (0.065, 0.040, 0.045)),
    ("B12_Star2", "dot", 0.006, "#FFFCF7", (0.005, 0.095, 0.040)),
]


def _hexc(h, a=1.0):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (a,)


def _star_mesh(name, shape, r):
    """星形＝五角星往前後鼓起的「枕頭星」（從側面看也有厚度）；圓點＝小球"""
    me = bpy.data.meshes.new(name)
    if shape == "dot":
        import bmesh
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r); bm.to_mesh(me); bm.free()
    else:
        V = []
        for k in range(10):
            a = math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
            V.append((rr * math.cos(a), rr * math.sin(a), 0.0))
        V += [(0, 0, r * 0.35), (0, 0, -r * 0.35)]
        F = [(k, (k + 1) % 10, 10) for k in range(10)] + [((k + 1) % 10, k, 11) for k in range(10)]
        me.from_pydata(V, [], F)
    for p in me.polygons:
        p.use_smooth = shape == "dot"
    return me


def pop_setup():
    """建星星物件、算縮放中心（雙手握的位置，手機座標）、記下每格的「啵」狀態 → STATE["pop"]"""
    import b1b2_r2 as R2
    tgt = STATE["tgt"]; col = bpy.data.collections["B12_studio"]
    for name, shape, r, hexv, _d in STARS:
        if name not in bpy.data.objects:
            m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Base Color"].default_value = _hexc(hexv)
            b.inputs["Emission Color"].default_value = _hexc(hexv); b.inputs["Emission Strength"].default_value = 0.6
            b.inputs["Roughness"].default_value = 0.6
            try:
                m.surface_render_method = "BLENDED"
            except Exception:
                m.blend_method = "BLEND"
            me = _star_mesh(name, shape, r); me.materials.append(m)
            o = bpy.data.objects.new(name, me); col.objects.link(o); o.hide_render = True
    on = [i for i, Mp in enumerate(STATE["phone"]) if Mp is not None]
    i0 = on[0]
    iref = i0 + len(POP_SCALE)                                # 手已經握穩的那一格
    R, h = STATE["poses"][iref]; Hd = tgt.fk(R, h); Mi = STATE["phone"][iref].inverted()
    c = (Mi @ R2.palm_info(tgt, R, Hd, "L")[0] + Mi @ R2.palm_info(tgt, R, Hd, "R")[0]) / 2
    c.z = 0.0                                                 # 機身厚度中線上
    pop = {}
    for k, s in enumerate(POP_SCALE):
        pop.setdefault(i0 + k, {})["scale"] = s
    for k, (s, a) in enumerate(zip(STAR_SCALE, STAR_ALPHA)):
        pop.setdefault(i0 + k, {})["star"] = (k, s, a)
    STATE["pop"] = pop; STATE["pop_c"] = c
    return dict(first=round(i0 / 30, 2), center_mm=tuple(round(1000 * x, 1) for x in c), frames=sorted(pop))


def _pop_apply(i):
    """pose_at 之後呼叫：這一格的手機縮放、星星位置／大小／透明度"""
    pop = STATE.get("pop", {}).get(i, {}); arm = STATE["arm"]
    Mp = STATE["phone"][i] if "phone" in STATE else None
    if Mp is not None and "scale" in pop:
        import b1b2_r3 as b12_r3
        c = STATE["pop_c"]; s = pop["scale"]
        S = Matrix.Translation(c) @ Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-c)
        for nm in ("B12_Phone", "B12_PhoneMute"):
            ph = bpy.data.objects.get(nm)
            if ph is not None and not ph.hide_render:
                ph.matrix_world = arm.matrix_world @ Mp @ S @ b12_r3.PROP_FROM_PHONE
    for j, (name, shape, r, hexv, d) in enumerate(STARS):
        o = bpy.data.objects.get(name)
        if o is None:
            continue
        if "star" not in pop or Mp is None:
            o.hide_render = True; continue
        k, s, a = pop["star"]
        p = STATE["pop_c"] + Vector(d) * (0.8 + 0.3 * k / 5)
        o.hide_render = False
        o.matrix_world = Matrix.Translation(arm.matrix_world @ (Mp @ p)) @ Matrix.Diagonal((s, s, s, 1.0))
        b = next(n for n in o.active_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Alpha"].default_value = a


def _stars_face(cam_loc):
    """星星轉向鏡頭（星形是平的，正面朝鏡頭才看得出形狀）"""
    for name, *_ in STARS:
        o = bpy.data.objects.get(name)
        if o is not None and not o.hide_render:
            loc = o.matrix_world.translation.copy(); sc = o.matrix_world.to_scale()
            q = (Vector(cam_loc) - loc).to_track_quat("Z", "Y")
            o.matrix_world = Matrix.LocRotScale(loc, q, sc)


FINAL = os.path.join(HERE, "final.json")          # 定案參數（狀態紀錄 anim/b1_b2 的 artifact）


def run_r3(load=True, final=FINAL):
    """第 3 輪定案版一次重建（B12_WORK 被清掉之後用）。定案參數全部讀 final.json（狀態紀錄 anim/b1_b2 的 artifact 就是這個檔）：
    場景＋角色＋攝影棚 → 讀 Mixamo → 底（低頭、貼地、起步不沉）→ 手指粗細、兩支手機道具 → 握法＋點開關＋鎖腳 → 「啵」。約 5～15 秒"""
    import b1b2_r3 as R3
    global POP_SCALE, STAR_SCALE, STAR_ALPHA, STARS
    fin = json.load(open(final, encoding="utf8"))
    t0 = time.time()
    setup()
    if load:
        load_clips()
    base_r3(**fin["base_r3"])
    arm = STATE["arm"]; body = L.body_mesh(arm)
    STATE["rad"] = {s: R3.finger_radius(arm, body, s) for s in "LR"}
    g = {"__file__": r"D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/props-zepeto/use_props.py"}
    exec(open(g["__file__"], encoding="utf8").read(), g)
    for key, name in ((fin["phone"]["before"], "B12_Phone"), (fin["phone"]["after"], "B12_PhoneMute")):
        if name not in bpy.data.objects:
            g["place_prop"](key, name=name, parent=bpy.data.collections["B12_studio"])
    STATE["GL"] = {k: (tuple(v) if isinstance(v, list) else v) for k, v in fin["grip"]["L"].items()}
    STATE["GR"] = {k: (tuple(v) if isinstance(v, list) else v) for k, v in fin["grip"]["R"].items()}
    r = build_r3(**fin["build_r3"])
    pp = fin["pop"]
    POP_SCALE = tuple(pp["phone_scale"]); STAR_SCALE = tuple(pp["star_scale"]); STAR_ALPHA = tuple(pp["star_alpha"])
    STARS = [(s_["name"], s_["shape"], s_["radius_m"], s_["color"], tuple(s_["dir_m"])) for s_ in pp["stars"]]
    pop = pop_setup()
    on = [i for i, m in enumerate(STATE["phone"]) if m is not None]; STATE["phone_c_last"] = STATE["phone"][on[0]].translation.copy()
    return dict(sec=round(time.time() - t0, 1), stats=r["stats"], r3=r["r3"], pop=pop)


# ════════ 樣張（定案交接時存；render-settings 面板的試渲、確認頁短片用） ════════
def sample():
    """側面跟拍（鏡頭跟著骨盆走），手機、星星（位置、顯示、透明度）一起烤成關鍵影格"""
    import zanim_sample as SP
    objs = [o for o in (bpy.data.objects.get("B12_Phone"), bpy.data.objects.get("B12_PhoneMute")) if o]
    stars = [bpy.data.objects[s[0]] for s in STARS if s[0] in bpy.data.objects]
    alpha = [(o, next(nd for nd in o.active_material.node_tree.nodes if nd.type == "BSDF_PRINCIPLED"), "Alpha") for o in stars]
    SP.new_camera("SAMPLE_Cam", 35.0)
    out = SP.bake(objects=objs + stars, alpha=alpha, camera_fn=SP.follow_camera(offset=(0.0, -3.0, 0.25), aim_z=0.70))
    path = SP.save("b1_b2")
    reg = SP.register("b1_b2", "B1→B2 手機 → 餐檯", "b1_b2", path,
                      [(2.0, "走路"), (4.97, "手機「啵」冒出來（星星）"), (6.2, "拇指按靜音"), (9.0, "起步走掉（動得快）")],
                      note="定案 v4；還沒穿西裝", kind="shot")
    return dict(out, path=path, reg=reg)
