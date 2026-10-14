# B4 正式版（2026-10-13 導演端：B4～B6 正式版一開始就穿禮服做）。攝影區：
# 柱子擦過換景 → 兩人並肩走來（新郎靠鏡頭、新娘遠側）→ 新郎停下、轉向蹲著拍照的攝影師；新娘繞到新郎靠鏡頭那一側停下（第 1 輪回饋：換邊並排）
# → 新娘手輕搭新郎手肘內側、新郎整理領結抬下巴 → 攝影師按快門、放下相機比讚 → 兩人轉回前方起步（接 B5）。
# 座標（動畫座標＝場景座標＋venue_offset (−0.654, 0)）：新郎停點 (10.646, −0.6)、攝影師 (10.886, −1.8)、換景柱子 (8.906, −1.60)（場景端 2026-10-13）。
# B3→B4 在換景柱子後面切：開頭不必和 B3 結尾同位置（兩人在柱子後面從一前一後換成並肩）。
# 姿勢參考：
#   攝影師單膝跪拍：一膝跪地、手肘撐在立起的那隻膝蓋上，身體當三腳架（photographytalk.com/photography-articles/7285-6-poses-you-can-use-to-avoid-camera-shake）；
#   相機貼臉、手肘收緊、左手托鏡頭、右手握機身按快門（digitalcameraworld.com/uk/tutorials/cheat-sheet-how-to-hold-your-camera-properly）。
#   Mixamo Kneeling Idle 正好是右膝跪地、左腳踩地（分鏡要的）。
# 用法（MCP）：
#   # BODY=groom,bride,photographer
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b4"); import b4_formal as B4F; print(B4F.run())
import bpy, os, sys, math, json, time
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
import zanim_fix as F
import zanim_cast as C
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE, PREFIX = "B4_FORMAL", "ZA_"
FPS = 30
HANDLES = 1.0
OUT_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b4/end_state_formal.json"
G_CLIPS = ("male_standard_walk", "male_stop_walk", "turn_right_90", "standing_idle", "turn_left_90", "male_start_walk")
B_CLIPS = ("female_walk", "female_stop_walk", "female_idle", "turn_left_90", "female_start_walk")
PH_CLIPS = ("kneeling_idle",)
STOP = Vector((10.646, -0.6, 0.0))                 # 新郎停穩的骨盆
PH_XY = Vector((10.886, -1.8, 0.0))                # 攝影師（骨盆）
P = dict(X=9, walk_s=1.4, stop_b=66, settle=0.3, g_turn=-79.0, tr=(0, 45), idle_a=0, hold=3.0, start_a=10, go_len=0.9,
         tie=(0.6, 1.8), shutter=2.2, ph_down=0.25, pivot_s=1.0, pivot_lift=0.035, ph_frac=0.93, ph_y=-1.8)
# walk_s：鏡內走幾秒才開始停下（換景柱子要先被跟拍的鏡頭帶出畫面）；g_turn：新郎停穩後轉向攝影師幾度（負＝右轉）；
# hold：新郎轉完到開始轉回前方的秒數（字卡至少 4 秒）；tie：轉完後幾秒開始／結束整理領結；shutter：轉完後幾秒按快門；ph_down：快門後幾秒放下相機比讚
PB = dict(walk_k=0.854, side=0.6, lag=0.35, bend=-40.0, bend_n=25, bend_w=0.0, bend_wn=30, target=(-0.65, -0.5), L1x=0, g_shift=0.15, lead=0.1, b_turn=100.0,
          skirt=dict(margin=0.015, elbow_k=2.0, max_deg=40))
# side：走路時在新郎遠側幾 m；lag：比新郎晚幾秒停穩；bend_w＋bend：走路最後 bend_wn 格＋停下那段往右彎幾度（合起來約 100°：半徑約 0.9 m 的弧，
#   從新郎背後繞到他靠鏡頭那一側、順便面向攝影師）；
# target：停穩時相對新郎停點的位置；b_turn：起步前轉回 +X 幾度
# 2026-10-13 第 1 版自我檢驗沒過：新娘從新郎背後繞（target (−0.65, −0.5)）要落後 1.5 m 走，跟拍時新郎被切出畫面 →
#   第 2 試：從新郎前面繞到他右前方（target (0.74, −0.3)）→ 和畫面右緣的攝影師疊在一起、遠側走時裙子擦到轉角裝飾柱和背板；
#   定案：新娘走在新郎後面約 1～1.3 m、偏鏡頭側 0.2～0.3 m（裙子離遠側擺設遠），新郎停下後她往前走上來停在他左前方（分鏡：往前一步換到靠鏡頭那側），
#   自然面向攝影師（bend −40）；
#   g_shift：新郎轉身那一步順便往她那邊跨幾 m（搭手肘搆得到；骨盆隔約 0.65 m）


def setup():
    m = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b4")[1]
    Z.load_clips(G_CLIPS)
    C.add_actor("bride", "bride")
    with C.as_actor("bride"):
        Z.load_clips(B_CLIPS)
    C.add_actor("photographer", "photographer")
    with C.as_actor("photographer"):
        Z.load_clips(PH_CLIPS)
    return m


def _yaw(tgt, R):
    v = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0))
    return math.degrees(math.atan2(v.x, -v.y))


def _sm(t, a, b):
    x = 0.0 if t <= a else (1.0 if t >= b else (t - a) / (b - a))
    return x * x * (3 - 2 * x)


def _still(poses, i0, thr=0.08):
    return next((i for i in range(i0, len(poses) - 3) if (poses[i + 3][1] - poses[i][1]).length * 10 < thr), i0)


def _turn_clip(tgt, name, a, b, total):
    c = L._CL[name]
    out, _ = F.amp_turn(tgt, c, total, a, b)
    return dict(out, name=name + "_amp")


# ════════ 新郎 ════════
def plan_groom():
    tgt = STATE["tgt"]; X = P["X"]
    W, ST, TR, ID, TL, SW = (L._CL[n] for n in G_CLIPS)
    wn = W["n"] - 1
    a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
    a4, b4, _ = F.match_phase(tgt, SW, range(SW["n"] - 30, SW["n"] - 9), W, range(0, wn))
    want = int(round((HANDLES + P["walk_s"]) * FPS))
    L1 = want + ((a1 + X - want) % wn)
    W1 = mr.splice_clip(W, [(0, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * (L1 // wn + 2))
    W2 = mr.splice_clip(W, [(b4 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * 3)
    # 2026-10-13（B3 的教訓）：轉身不用 Mixamo Turn 90（整段運動員預備站姿：微蹲、縮小轉角後變碎步）→ 站著那段直接用轉好的面向，
    #   轉身由 build_groom 的 F.pivot_turn 補（轉向那側的腳先跨、另一腳跟上）
    t_still = (L1 - X + (P["stop_b"] - b1)) / FPS - HANDLES + P["settle"]
    t_turn_end = t_still + P["pivot_s"]
    t_back = t_turn_end + P["hold"]
    t_go = t_back + P["pivot_s"]
    segs = [mr.Seg(W1, 0, L1, name="並肩走來（Walking）"),
            mr.Seg(ST, b1, P["stop_b"], hold=P["settle"], name="停下（Stop Walking，播到停穩）"),
            mr.Seg(ID, P["idle_a"], ID["n"] - 1, face=90.0 + P["g_turn"], name="跨一步轉向攝影師 → 站著擺姿勢（Standing Idle；整理領結用手 IK）"),
            mr.Seg(SW, P["start_a"], a4 + X, face=90.0, at=t_go + HANDLES, name="跨一步轉回前方 → 起步（Start Walking）"),
            mr.Seg(W2, 0, int(2.5 * FPS), face=90.0, name="走路（Walking）")]
    tm = dict(turn=t_still, turn_end=t_turn_end, back=t_back, go=t_go, b4=b4, wn=wn)
    return segs, tm


def build_groom():
    tgt = STATE["tgt"]; segs, tm = plan_groom()
    seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS); seq.place(0.0, (0.0, 0.0), 90.0)
    dur = tm["go"] + P["go_len"]; n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    poses = [(dict(R), h.copy()) for R, h, _y in (seq.at(min(i / FPS, seq.start + seq.dur)) for i in range(n))]
    i0 = int(round(seq.T[1][0] * FPS)); still = _still(poses, i0)
    sh = Vector((STOP.x - poses[still][1].x, STOP.y - poses[still][1].y, 0))
    poses = [(R, h + sh) for R, h in poses]
    T = seq.T; nt = int(round(P["pivot_s"] * FPS)); X = P["X"]
    i1 = int(round(T[2][0] * FPS)) - 2; i2 = int(round(T[3][0] * FPS)) + X
    poses = F.pivot_turn(tgt, poses, i1, i1 + nt, first="R", lift=P["pivot_lift"])        # 往右轉：右腳先跨
    poses = F.pivot_turn(tgt, poses, i2 - nt, i2, first="L", lift=P["pivot_lift"])        # 轉回來：左腳先跨
    tm["pivot"] = ((i1 / FPS - HANDLES, (i1 + nt) / FPS - HANDLES), ((i2 - nt) / FPS - HANDLES, i2 / FPS - HANDLES))
    pts = L.sole_points(STATE["arm"])
    poses, _off = F.ground(tgt, poses, pts)
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9, z_on=0.015, gap_max=25)
    B0 = _b0()
    poses = B0._pin_foot_turn(tgt, poses, pts)
    poses = B0.zero_slide(tgt, poses, pts, 0, n - 1)
    poses = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in poses]
    tm.update(still=still / FPS - HANDLES, end=dur)
    STATE.update(poses=poses, seq=seq, dur=dur, b4_tm=tm, marks=dict(still=tm["still"], go=tm["go"], end=dur),
                 segs=[(round(seq.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    return dict(dur=round(dur, 2), tm={k: (round(v, 2) if isinstance(v, float) else v) for k, v in tm.items()},
                face_deg=round(_yaw(tgt, poses[int(round((tm["turn_end"] + 0.5 + HANDLES) * FPS))][0]), 1))


def _b0():
    p = os.path.abspath(os.path.join(HERE, "..", "b0"))
    if p not in sys.path:
        sys.path.insert(0, p)
    import b0_formal as B0
    return B0


# ════════ 新娘 ════════
def plan_bride(L1x=0):
    X = P["X"]; tm = STATE["b4_tm"]
    with C.as_actor("bride"):
        tgt = STATE["tgt"]
        W, ST, ID, TL, SW = (L._CL[n] for n in B_CLIPS)
        W = F.retime(W, PB["walk_k"]); wn = W["n"] - 1
        SW = F.retime(SW, PB["walk_k"])
        a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 12))
        a4, b4, _ = F.match_phase(tgt, SW, range(SW["n"] - 25, SW["n"] - 6), W, range(0, wn))
        STb = F.bend(ST, PB["bend"], b1, b1 + PB["bend_n"])
        st_i = _fm()._still(ST, b1 + 10)
        t_still = tm["still"] + PB["lag"]
        L1 = int(round((t_still + HANDLES) * FPS)) - (st_i - b1) + X
        L1 = L1 + ((a1 + X - L1) % wn) + L1x * wn
        t_still = (L1 - X + (st_i - b1)) / FPS - HANDLES
        W1 = mr.splice_clip(W, [(0, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * (L1 // wn + 2))
        if PB["bend_w"]:                                  # 走路最後 bend_wn 格就開始往右彎（和停下那段接成一個大弧，繞過新郎背後）
            W1 = F.bend(W1, PB["bend_w"], L1 - PB["bend_wn"], L1)
        W2 = mr.splice_clip(W, [(b4 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * 3)
        t_back = tm["back"] - PB["lead"]; t_go = t_back + P["pivot_s"]
        segs = [mr.Seg(W1, 0, L1, name="在新郎遠側並肩走來（Female Walk）"),
                mr.Seg(STb, b1, ST["n"] - 1, name="停下時往右繞到新郎靠鏡頭那一側（Female Stop Walking，路線往右彎）"),
                mr.Seg(ID, 0, ID["n"] - 1, name="站在新郎身邊、手搭他手肘（Female Idle）"),
                mr.Seg(SW, 3, a4 + X, face=90.0, at=t_go + HANDLES, name="跨一步轉回前方 → 起步（Female Start Walking）"),
                mr.Seg(W2, 0, int(2.5 * FPS), face=90.0, name="走路（Female Walk）")]
        return segs, dict(still=t_still, back=t_back, go=t_go, L1=L1, b4=b4, wn=wn)


def _fm():
    p = os.path.abspath(os.path.join(HERE, "..", "b1_b2"))
    if p not in sys.path:
        sys.path.insert(0, p)
    import b1b2_formal as FM
    return FM


def build_bride(L1x=None, place_only=False):
    """擺放：停穩那格骨盆＝新郎停點＋target；回傳走路那段離新郎的側向距離、和裙子的最近距離（骨架估算）"""
    L1x = PB["L1x"] if L1x is None else L1x
    segs, btm = plan_bride(L1x)
    n = len(STATE["poses"]); gp = STATE["poses"]
    with C.as_actor("bride"):
        tgt = STATE["tgt"]
        seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS); seq.place(0.0, (0.0, 0.0), 90.0)
        poses = [(dict(R), h.copy()) for R, h, _y in (seq.at(min(i / FPS, seq.start + seq.dur)) for i in range(n))]
        si = int(round((btm["still"] + HANDLES) * FPS))
        goal = STOP + Vector((PB["target"][0], PB["target"][1], 0))
        sh = Vector((goal.x - poses[si][1].x, goal.y - poses[si][1].y, 0))
        poses = [(R, h + sh) for R, h in poses]
        side = [poses[i][1].y - gp[i][1].y for i in range(int(HANDLES * FPS), int(round((STATE["b4_tm"]["still"] - 0.5 + HANDLES) * FPS)))]
        lag = [gp[i][1].x - poses[i][1].x for i in range(int(HANDLES * FPS), int(round((STATE["b4_tm"]["still"] - 0.5 + HANDLES) * FPS)))]
        info = dict(L1x=L1x, still=round(btm["still"], 2), side=(round(min(side), 2), round(max(side), 2)), lag=(round(min(lag), 2), round(max(lag), 2)),
                    gap=F.skirt_gap(STATE["tgt"], gp, poses), yaw_still=round(_yaw(tgt, poses[si][0]), 1))
        if place_only:
            return info
        nt = int(round(P["pivot_s"] * FPS)); i2 = int(round(seq.T[3][0] * FPS)) + P["X"]
        poses = F.pivot_turn(tgt, poses, i2 - nt, i2, first="L", lift=P["pivot_lift"])       # 轉回前方（往左轉 100°）：左腳先跨
        pts = L.sole_points(STATE["arm"])
        poses, _off = F.ground(tgt, poses, pts)
        poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9, z_on=0.015, gap_max=25)
        B0 = _b0()
        poses = B0._pin_foot_turn(tgt, poses, pts)
        poses = B0.zero_slide(tgt, poses, pts, 0, n - 1)
        poses = F.pivot_turn(tgt, poses, i2 - nt, i2, first="L", lift=P["pivot_lift"])       # 鎖腳後再做一次：鎖腳會把要抬起的那隻腳釘住，抬起那格跳 1.2 cm
        poses, info["head_up_max"] = F.level_head(tgt, poses)   # 2026-10-13 導演端第 3 輪（全片通用）：新娘走路頭往斜上方看 → 仰角超過 5° 壓回來
        poses = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in poses]
        poses, info["skirt_arms"] = F.skirt_arms(tgt, poses, **PB["skirt"])
        STATE.update(poses=poses, seq=seq, b4b_tm=btm, segs=[(round(seq.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    return info


def groom_shift():
    """新郎轉向攝影師那一步順便往新娘那邊跨 g_shift m：兩次轉身之間整段平移（轉身的跨步內插過去，站著那段不滑）"""
    tm = STATE["b4_tm"]; (a1, b1), (a2, b2) = tm["pivot"]
    i1, i2 = int(round((b1 + HANDLES) * FPS)), int(round((a2 + HANDLES) * FPS))
    bi = int(round((STATE["b4b_tm"]["still"] + HANDLES) * FPS))
    d = C.actor("bride")["poses"][bi][1] - STATE["poses"][i1][1]; d.z = 0; d = d.normalized() * PB["g_shift"]
    gp = STATE["poses"]
    for i in range(i1, i2 + 1):
        gp[i] = (gp[i][0], gp[i][1] + d)
    tgt = STATE["tgt"]; ia, ib = int(round((a1 + HANDLES) * FPS)), i1
    STATE["poses"] = F.pivot_turn(tgt, gp, ia, ib, first="R", lift=P["pivot_lift"])
    STATE["poses"] = F.pivot_turn(tgt, STATE["poses"], i2, int(round((b2 + HANDLES) * FPS)), first="L", lift=P["pivot_lift"])
    return tuple(round(x, 3) for x in d)


def _b3():
    p = os.path.abspath(os.path.join(HERE, "..", "b3"))
    if p not in sys.path:
        sys.path.insert(0, p)
    import b3_formal as B3F
    return B3F


# ════════ 攝影師（Kneeling Idle：右膝跪地、左腳踩地）＋相機 ════════
DSLR_VF = Vector((0.0, 0.037, 0.072))             # 素材 dslr：原點在底部中心、鏡頭朝 −Y；觀景窗（機背上方）
DSLR_GRIP = Vector((-0.058, -0.005, 0.045))        # 握把（拿相機的人的右手邊＝−X）
DSLR_LENS = Vector((0.0, -0.075, 0.012))           # 鏡頭下緣（左手托的地方）
PH = dict(eye=(0.15, 0.06), vf_gap=0.012, chest=(0.26, -0.02), tilt=-55.0, down_s=0.45, thumb=(0.16, 0.27, 0.16))
# eye：眼睛在頭骨往臉前 m、往上 m；vf_gap：觀景窗離眼睛幾 m；chest：放下時相機在上胸往前 m、往上 m、機背往上翻 tilt 度（看螢幕）；
# thumb：比讚的手腕在上胸往前、往右、往上 m（2026-10-13 自我檢驗：(0.24, 0.13, 0.04) 和放在胸前的相機疊在一起、看不出比讚 → 移到右肩旁、舉高）


def build_ph():
    """攝影師：Kneeling Idle 循環，跪在 PH，面向兩人停下時的中點"""
    tm = STATE["b4_tm"]; n = len(STATE["poses"])
    gi = int(round((tm["turn_end"] + 1.0 + HANDLES) * FPS)); g = STATE["poses"][gi][1]; b = C.actor("bride")["poses"][gi][1]
    mid = (g + b) / 2
    global PH_XY                                          # 攝影師：停下這段的鏡頭裡，放在畫面右邊 ph_frac 處露半身（同走位版的算法），y 照場景端 −1.8
    cf = camera_fn(); l, a_ = cf(gi); fwd = a_ - l; fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
    D = (P["ph_y"] - l.y) / max(1e-3, fwd.y)
    PH_XY = l + fwd * D + right * ((P["ph_frac"] - 0.5) * BK.frame_w(D)); PH_XY.z = 0
    d = mid - PH_XY; d.z = 0
    yaw = math.degrees(math.atan2(d.x, -d.y))
    with C.as_actor("photographer"):
        tgt = STATE["tgt"]; KI = L._CL["kneeling_idle"]
        loops = (n / FPS) / ((KI["n"] - 1) / FPS) + 1
        seq = mr.Sequence(tgt, [mr.Seg(KI, 0, KI["n"] - 1, loops=loops, name="單膝跪著拍照（Kneeling Idle）")], blend=0.3)
        seq.place(0.0, (PH_XY.x, PH_XY.y), yaw)
        poses = [(dict(R), h.copy()) for R, h, _y in (seq.at(min(i / FPS, seq.start + seq.dur - 1e-3)) for i in range(n))]
        sh = Vector((PH_XY.x - poses[0][1].x, PH_XY.y - poses[0][1].y, 0)); poses = [(R, h + sh) for R, h in poses]
        pts = L.sole_points(STATE["arm"])
        poses, off = F.ground(tgt, poses, pts)
        STATE.update(poses=poses, seq=seq, segs=[(0.0, round(seq.dur, 2), "單膝跪著拍照（Kneeling Idle）")])
    STATE["ph_target"] = mid + Vector((0, 0, 0.95))
    return dict(xy=(round(PH_XY.x, 3), round(PH_XY.y, 3)), yaw=round(yaw, 1), ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)))


def ph_arms():
    """相機貼眼（右手握握把、左手托鏡頭，左手肘往下收向左膝）→ 快門（右手食指）→ 放下到胸前看螢幕（左手拿）＋右手比讚"""
    from zanim_hand import hand_quat, put_hand_pole
    tm = STATE["b4_tm"]; t_sh = tm["turn_end"] + P["shutter"]; t_dn = t_sh + P["ph_down"]
    st = C.actor("photographer"); tgt = st["tgt"]; n = len(st["poses"]); target = STATE["ph_target"]
    plen = lambda s: 0.6 * (tgt.rest_h[f"J_Bip_{s}_Middle1"] - tgt.rest_h[f"J_Bip_{s}_Hand"]).length
    out = []; Ms = []
    for i in range(n):
        t = i / FPS - HANDLES; R, h = st["poses"][i]; Hd = tgt.fk(R, h)
        qh = R["J_Bip_C_Head"] @ tgt.rest_q["J_Bip_C_Head"].inverted()
        hf = qh @ Vector((0, -1, 0)); hf.z = 0; hf.normalize()
        eye = Hd["J_Bip_C_Head"] + hf * PH["eye"][0] + Vector((0, 0, PH["eye"][1]))
        fwd = (target - eye).normalized()
        q_up = fwd.to_track_quat("-Y", "Z")                            # 相機鏡頭（−Y）對準兩人
        M_up = Matrix.Translation(eye + fwd * PH["vf_gap"] - q_up @ DSLR_VF) @ q_up.to_matrix().to_4x4()
        qb = R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()
        bf = qb @ Vector((0, -1, 0)); bf.z = 0; bf.normalize(); br = Vector((bf.y, -bf.x, 0))
        q_dn = bf.to_track_quat("-Y", "Z") @ Quaternion((1, 0, 0), math.radians(PH["tilt"]))
        c_dn = Hd["J_Bip_C_UpperChest"] + bf * PH["chest"][0] + Vector((0, 0, PH["chest"][1]))
        M_dn = Matrix.Translation(c_dn) @ q_dn.to_matrix().to_4x4()
        k = _sm(t, t_dn, t_dn + PH["down_s"])
        loc = M_up.translation.lerp(M_dn.translation, k); rot = M_up.to_quaternion().slerp(M_dn.to_quaternion(), k)
        M = Matrix.Translation(loc) @ rot.to_matrix().to_4x4(); Ms.append(M); Rc = rot
        # 左手托鏡頭下緣（掌心朝上、四指往相機右邊包），手肘往下收向左膝
        lens = M @ DSLR_LENS
        dL = (Rc @ Vector((-1, 0, 0.35))).normalized(); pL = Rc @ Vector((0, 0, 1))
        qL = hand_quat(tgt, "L", dL, pL)
        ML = Matrix.Translation(lens - dL * plen("L") - pL * 0.018) @ qL.to_matrix().to_4x4()
        R = put_hand_pole(tgt, R, h, "L", ML, 1.0, (Hd["J_Bip_L_LowerLeg"] - Hd["J_Bip_L_UpperArm"]).normalized(), 0.7)
        R = mr.gesture(tgt, R, "L", "cup", 1.0)
        # 右手：握握把（快門前）→ 放下後比讚
        grip = M @ DSLR_GRIP
        dR = (Rc @ Vector((0.15, -1.0, -0.25))).normalized(); pR = Rc @ Vector((1, 0, 0))
        qR = hand_quat(tgt, "R", dR, pR)
        MR = Matrix.Translation(grip - dR * plen("R") * 0.55 - pR * 0.022) @ qR.to_matrix().to_4x4()
        th = Hd["J_Bip_C_UpperChest"] + bf * PH["thumb"][0] + br * PH["thumb"][1] + Vector((0, 0, PH["thumb"][2]))
        qT = hand_quat(tgt, "R", (bf + Vector((0, 0, 0.2))).normalized(), -br)
        MT = Matrix.Translation(th) @ qT.to_matrix().to_4x4()
        kt = _sm(t, t_dn + 0.15, t_dn + 0.55)
        MRx = Matrix.Translation(MR.translation.lerp(MT.translation, kt)) @ MR.to_quaternion().slerp(MT.to_quaternion(), kt).to_matrix().to_4x4()
        R = put_hand_pole(tgt, R, h, "R", MRx, 1.0, Vector((0.0, 0.0, -1.0)) + br * 0.4, 0.6)
        if kt < 1.0:
            R = mr.gesture(tgt, R, "R", "grip", 1.0 - kt)
        if kt > 0:
            R = mr.gesture(tgt, R, "R", "thumbs_up", kt)
        out.append((R, h))
    st["poses"] = out; STATE["dslr_M"] = Ms
    return dict(shutter=round(t_sh, 2), down=round(t_dn, 2))


def _dslr_hook(i):
    ob = bpy.data.objects.get("ZA_DSLR"); Ms = STATE.get("dslr_M")
    if ob is not None and Ms:
        ob.matrix_world = Ms[min(i, len(Ms) - 1)]


# ════════ 新郎整理領結、新娘手搭新郎手肘（用哪隻手照站位決定） ════════
def tie_and_elbow():
    """新郎：轉好後拇指食指捏領結、左右整理兩下、抬下巴（頭往後仰 8°）→ 放下。
    新娘：停穩後輕搭新郎手肘外側偏前（掌心貼著、手指順著前臂），起步前放開。
    用哪隻手照站位自動決定：新娘在新郎哪一側，她就用靠他的那隻手搭他那一側的手肘；新郎用另一隻手整理領結（分鏡寫右手，新娘在他右邊時改左手）"""
    from zanim_hand import hand_quat, put_hand_pole
    B3 = _b3(); tm = STATE["b4_tm"]; bt = STATE["b4b_tm"]
    gst = STATE; bst = C.actor("bride"); tg, tb = gst["tgt"], bst["tgt"]; n = len(gst["poses"])
    a, b = tm["turn_end"] + P["tie"][0], tm["turn_end"] + P["tie"][1]
    im = int(round((bt["still"] + 0.5 + HANDLES) * FPS)); _fw, _rt = B3._frame(tg, *gst["poses"][im])
    on_right = (bst["poses"][im][1] - gst["poses"][im][1]).dot(_rt) > 0      # 新娘在新郎右手邊？
    GT = "L" if on_right else "R"; GE = "R" if on_right else "L"; BH = "L" if on_right else "R"   # 整理領結的手、被搭的手肘、新娘搭的手
    sg = 1.0 if GT == "R" else -1.0
    gout = []
    for i in range(n):
        t = i / FPS - HANDLES; R, h = gst["poses"][i]
        w = _sm(t, a - 0.3, a) * (1 - _sm(t, b, b + 0.35))
        if w > 0:
            Hd = tg.fk(R, h); fw, rt = B3._frame(tg, R, h)
            wig = math.sin(2 * math.pi * 1.6 * (t - a)) * _sm(t, a, a + 0.2) * (1 - _sm(t, b - 0.3, b))
            goal = Hd["J_Bip_C_Neck"] + fw * 0.085 + rt * 0.03 * sg + Vector((0, 0, -0.035)) + rt * 0.008 * wig
            R = B3._ik_pinch(tg, R, h, GT, goal, w, Vector((0, 0, -1)) + rt * 0.5 * sg)
            lift = math.radians(8) * w                                     # 抬下巴
            hq = R["J_Bip_C_Head"] @ tg.rest_q["J_Bip_C_Head"].inverted()
            R = dict(R); R["J_Bip_C_Head"] = Quaternion(hq @ Vector((1, 0, 0)), -lift) @ R["J_Bip_C_Head"]
        gout.append((R, h))
    gst["poses"] = gout
    ea, eb = bt["still"] + 0.3, bt["back"] - 0.1
    bout = []
    for i in range(n):
        t = i / FPS - HANDLES; R, h = bst["poses"][i]
        w = _sm(t, ea, ea + 0.5) * (1 - _sm(t, eb - 0.3, eb))
        if w > 0:
            Rg, hg = gst["poses"][i]; Hg = tg.fk(Rg, hg); Hb = tb.fk(R, h)
            elbow = Hg[f"J_Bip_{GE}_LowerArm"]; fore = (Hg[f"J_Bip_{GE}_Hand"] - elbow).normalized()
            fwg, rtg = B3._frame(tg, Rg, hg); out_ = rtg if GE == "R" else -rtg
            touch = elbow + out_ * 0.045 + fwg * 0.02                      # 被搭的手肘外側偏前（她那一側）
            d = (fore * 0.6 + (touch - Hb[f"J_Bip_{BH}_UpperArm"]).normalized() * 0.4).normalized()
            palm = -out_                                                   # 掌心朝他的手肘
            q = hand_quat(tb, BH, d, palm)
            plen = 0.6 * (tb.rest_h[f"J_Bip_{BH}_Middle1"] - tb.rest_h[f"J_Bip_{BH}_Hand"]).length
            M = Matrix.Translation(touch - d * plen - palm * 0.022) @ q.to_matrix().to_4x4()
            R = put_hand_pole(tb, R, h, BH, M, w, Vector((0, 0, -1)), 0.5)
            R = mr.gesture(tb, R, BH, "relaxed", w)
        bout.append((R, h))
    bst["poses"] = bout
    return dict(tie=(round(a, 2), round(b, 2)), elbow=(round(ea, 2), round(eb, 2)), tie_hand=GT, elbow_of=GE, bride_hand=BH)


FACE_SMILE = dict(mouthSmileLeft=0.75, mouthSmileRight=0.75, cheekSquintLeft=0.3, cheekSquintRight=0.3, eyeSquintLeft=0.2, eyeSquintRight=0.2)


def face_vals(t):
    tm = STATE["b4_tm"]; bt = STATE["b4b_tm"]; t_dn = tm["turn_end"] + P["shutter"] + P["ph_down"]
    wg = _sm(t, tm["turn_end"] - 0.3, tm["turn_end"] + 0.3) * (1 - _sm(t, tm["back"], tm["back"] + 0.5))
    wb = _sm(t, bt["still"] - 0.2, bt["still"] + 0.4) * (1 - _sm(t, bt["back"], bt["back"] + 0.5))
    wp = _sm(t, t_dn, t_dn + 0.4)
    return ({k: v * wg for k, v in FACE_SMILE.items()}, {k: v * wb for k, v in FACE_SMILE.items()}, {k: v * wp for k, v in FACE_SMILE.items()})


def _faces():
    return [STATE["arm"], C.actor("bride")["arm"], C.actor("photographer")["arm"]]


def _face_hook(i):
    vals = face_vals(i / FPS - HANDLES)
    for arm, v in zip(_faces(), vals):
        hm = L.head_mesh(arm); kb = hm.data.shape_keys if hm else None
        if kb is None:
            continue
        for k, x in v.items():
            if k in kb.key_blocks:
                kb.key_blocks[k].value = x


def bake_face():
    import zanim_sample as SP
    n = len(STATE["poses"]); V = [face_vals(i / FPS - HANDLES) for i in range(n)]
    for j, (who, arm) in enumerate(zip(("groom", "bride", "photographer"), _faces())):
        hm = L.head_mesh(arm); key = hm.data.shape_keys if hm else None
        if key is None:
            continue
        ad = key.animation_data_create(); act = bpy.data.actions.get("SAMPLE_B4Face_" + who) or bpy.data.actions.new("SAMPLE_B4Face_" + who); ad.action = act
        for k in V[0][j].keys():
            if k in key.key_blocks:
                SP._put(act, key, 'key_blocks["%s"].value' % k, 0, [V[i][j][k] for i in range(n)])
    return True


# ════════ 衣服、場景、換景柱子、鏡頭、短片 ════════
OUTFIT_G = "groom-beige-3piece"
OUTFIT_B = "bride-blush-ballgown"
OUTFIT_P = "photographer-black-casual"
PILLAR = dict(d=1.3)                                   # 換景柱子：鏡內第 0 格擋住兩人中點、離鏡頭 d m（同 B3）；之後不動，跟拍的鏡頭往右把它帶出畫面
CAM = dict(mid_hold=0.68, pan_s=0.8, dist=3.6)         # 停下面對攝影師這段：兩人中點放畫面 mid_hold（右邊留給攝影師露半身；分鏡第 1 輪 (b)）；dist：鏡頭離兩人幾 m
# 2026-10-13 導演端：剪接 col 版面只露原片 x 40～100%，0.60＋3 m 時新娘左半身出框 → 3.6 m（同 B3 結尾）＋0.68：新娘左緣約 51%、新郎右緣約 78%


def dress():
    import zanim_dress as D
    out = {"groom": D.dress(OUTFIT_G)}
    with C.as_actor("bride"):
        out["bride"] = D.dress(OUTFIT_B, body="bride")
    with C.as_actor("photographer"):
        out["photographer"] = D.dress(OUTFIT_P, body="photographer")
    names = set(STATE.get("outfit_objs") or [])
    for k in ("bride", "photographer"):
        names |= set(C.actor(k).get("outfit_objs") or [])
    for o in bpy.data.objects:
        if o.name in names:
            for m in o.modifiers:
                if m.type == "SOLIDIFY" or "FixFolds" in m.name:
                    m.show_viewport = False
    return {k: (list(v[0])[:3], v[1]) for k, v in out.items()}


def scene_set():
    vo = json.load(open(BK.VENUE_OFFSET)); off = (vo["dx"], vo["dy"], 0.0)
    objs = {}
    for key in ("Scene_VenueCorridor", "Scene_VenuePhotoZone"):
        old = bpy.data.collections.get("ZP_" + key)
        if old is not None and old.name in Z.studio_col().children:
            objs.update({o.name: o for o in old.all_objects})
        else:
            objs.update(BK.venue(key, off))
    STATE["sc"].view_layers[0].update()
    pil = [o for n_, o in objs.items() if n_.startswith("I_ZP_pillar") and o.matrix_world.translation.y < -1.0]
    STATE["pillar_obj"] = pil[0].name if pil else None
    if bpy.data.objects.get("ZA_DSLR") is None:
        BK.props_api()["place_prop"]("dslr", name="ZA_DSLR", parent=Z.studio_col())
    for hk in (_dslr_hook, _face_hook):
        if hk not in Z.POSE_HOOKS:
            Z.POSE_HOOKS.append(hk)
    return dict(offset=off, pillar=STATE["pillar_obj"], n=len(objs))


def camera_fn():
    """側面跟拍（兩人中點、畫面 70%）；停下面對攝影師這段中點平移到 60%（右邊留給攝影師）、鏡頭固定；起步後平移回 70%"""
    tm = STATE["b4_tm"]; arm = STATE["arm"]

    def partner(i):                                       # 走路時新娘落後約 1 m → 跟拍點偏向新郎（新娘權重 0.25），新郎停穩後 0.8 秒內回到中點（0.5）
        t = i / FPS - HANDLES; wb = 0.25 + 0.25 * _sm(t, tm["still"], tm["still"] + 0.8)
        g = arm.matrix_world @ arm.pose.bones["J_Bip_C_Hips"].head; b = Vector(tuple(C.hips_world("bride")))
        return (g.x + (b.x - g.x) * 2 * wb, g.y + (b.y - g.y) * 2 * wb)
    base = BK.side_follow(holds=[(tm["still"] + 0.2, tm["go"])], handles=HANDLES, partner=partner, offset=(0.0, -CAM["dist"], 0.25))
    dx = BK.frame_w(CAM["dist"]) * (0.70 - CAM["mid_hold"])
    a0, a1 = tm["still"], tm["still"] + CAM["pan_s"]; b0, b1 = tm["go"], tm["go"] + CAM["pan_s"]

    def f(i):
        l, a = base(i); t = i / FPS - HANDLES
        k = 0.0 if t <= a0 or t >= b1 else (1.0 if a1 <= t <= b0 else ((t - a0) / (a1 - a0) if t < a1 else 1 - (t - b0) / (b1 - b0)))
        k = k * k * (3 - 2 * k); d = Vector((dx * k, 0, 0))
        return l + d, a + d
    return f


def pillar_place():
    """換景柱子：鏡內第 0 格在鏡頭往前 d m 那條線上、正好擋住兩人中點（之後不動）"""
    meshes = [o for o in STATE["sc"].objects if o.type == "MESH" and not o.hide_viewport]   # 算鏡頭要逐格擺姿勢：網格先關掉（穿衣服的三個人一格要好幾秒）
    for o in meshes:
        o.hide_viewport = True
    try:
        cf = camera_fn(); i0 = int(HANDLES * FPS); l, a = cf(i0)
    finally:
        for o in meshes:
            o.hide_viewport = False
    fwd = a - l; fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
    mid = (STATE["poses"][i0][1] + C.actor("bride")["poses"][i0][1]) / 2; dm = mid - l; dm.z = 0
    p = l + fwd * PILLAR["d"] + right * (dm.dot(right) / max(1e-3, dm.dot(fwd)) * PILLAR["d"]); p.z = 0
    ob = bpy.data.objects.get(STATE.get("pillar_obj") or "")
    if ob is not None:
        ob.location.x += p.x - ob.matrix_world.translation.x; ob.location.y += p.y - ob.matrix_world.translation.y
    STATE["pillar_P"] = p
    return tuple(round(x, 3) for x in p)


def clip(v=1, size=(960, 540)):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", 35.0)
    for a in _faces():
        a.animation_data_clear()
        hm = L.head_mesh(a); hk = hm.data.shape_keys if hm else None
        if hk is not None:
            hk.animation_data_clear()
    objs = [o for o in (bpy.data.objects.get("ZA_DSLR"),) if o]
    for o in objs:
        o.animation_data_clear()
    meshes = [o for o in STATE["sc"].objects if o.type == "MESH" and not o.hide_viewport]
    for o in meshes:
        o.hide_viewport = True
    try:
        out = SP.bake(objects=objs, camera_fn=camera_fn())
    finally:
        for o in meshes:
            o.hide_viewport = False
    out["face"] = bake_face()
    path = SP.save("b4_formal")
    cmd = SP.render_clip("b4_formal", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + "/formal_v%d.mp4" % v, size=size)
    return dict(out, path=path, cmd=cmd)


def run():
    t0 = time.time(); r = {}
    if "bride" not in C.cast():
        setup()
    r["groom"] = build_groom(); r["bride"] = build_bride(); r["shift"] = groom_shift(); r["ph"] = build_ph()
    r["ph_arms"] = ph_arms(); r["tie"] = tie_and_elbow()
    n = len(STATE["poses"])
    for st in (STATE, C.actor("bride")):
        st["segs"] = [s for s in st["segs"] if s[0] * FPS < n - 2]
    STATE["stats"] = Z.stats(); r["groom_stats"] = STATE["stats"]["summary"]
    for k in ("bride", "photographer"):
        with C.as_actor(k):
            STATE["stats"] = Z.stats(); r[k + "_stats"] = STATE["stats"]["summary"]
    if not STATE.get("outfit_objs"):
        r["dress"] = dress()
    r["scene"] = scene_set(); r["pillar"] = pillar_place(); r["sec"] = round(time.time() - t0, 1)
    return r


def cleanup():
    return Z.cleanup(SCENE)


def end_state(path=OUT_END):
    """鏡內最後一格兩人的骨盆、面向、走路相位（B5 開頭照這個接）"""
    i = int(round((STATE["dur"] + HANDLES) * FPS)); out = {}
    for key, st, tm, clip in (("groom", STATE, STATE["b4_tm"], "male_standard_walk"), ("bride", C.actor("bride"), STATE["b4b_tm"], "female_walk")):
        R, h = st["poses"][i]; t_w = st["seq"].T[-1][0]
        with C.as_actor(key if key != "groom" else None) if key != "groom" else _nullctx():
            yaw = _yaw(STATE["tgt"], R)
        out[key] = dict(hips=[round(x, 3) for x in h], yaw=round(yaw, 2), walk_phase=round((tm["b4"] + (i / FPS - t_w) * FPS) % tm["wn"], 1), wn=tm["wn"], clip=clip)
    out["bride"]["walk_k"] = PB["walk_k"]
    d = dict(what="B4 正式版鏡內最後一格（B5 開頭照這個接）", t_end=round(STATE["dur"], 3), **out,
             holding="無；新娘在新郎%s（y 差 %.2f m）" % ("靠鏡頭那側" if out["bride"]["hips"][1] < out["groom"]["hips"][1] else "遠側", out["bride"]["hips"][1] - out["groom"]["hips"][1]))
    json.dump(d, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return d


class _nullctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
