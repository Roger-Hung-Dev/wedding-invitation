# B1→B2 正式版（2026-10-13 導演端：整支片加速，先做能做的，禮服一到就穿上）。
# 和定案第 4 版（b1b2_shot.run_r3，只有新郎、11.2 秒）的差別：
#   1. 開頭接 B0 結尾：骨盆 (1.207, 0.098)、面向 +X、走路相位第 0 格；頭尾各多做 1 秒（film.json handles_s）。
#   2. 路線拉直：第 4 版走完往鏡頭偏 13°（結尾面向 (0.974, −0.227)）→ 起步、走路兩段用 face 鎖住 +X。
#   3. 節奏照「以動作流暢為主」（checklist 24）：停下播到停穩（Stop Walking 第 66 格）＋停 settle 秒才拿手機；
#      按完靜音停 after 秒才起步；起步從靜止那格（第 10 格）開始、走 go_len 秒回到正常速度才結束。
#   4. 新娘是真的身體（zanim_cast，v3），不是膠囊：同行在遠側 → 一起停 → 手機一響轉向新郎、雙手插腰瞪他 → 按掉後轉回來、一起走。
#   手機的握法、拇指按開關、「啵」全部沿用第 4 版（final.json），時間跟著拿手機那段平移。
# 用法（MCP）：
#   # BODY=groom,bride
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b1_b2"); import b1b2_formal as FM; print(FM.run_groom())
import bpy, os, sys, math, json, time
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
import zanim_fix as F
import zanim_cast as C
STATE = Z.STATE; L = Z.L; mr = Z.mr
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE, PREFIX = "B12_FORMAL", "B12_"          # 前綴沿用 B12_：第 4 版的手機、星星程式認 B12_studio 這些名字
FPS = 30
HANDLES = 1.0
B0_END = (1.207, 0.098)                       # B0 走位版第 3 輪的結尾（骨盆），面向 +X、走路相位第 0 格
FINAL4 = os.path.join(HERE, "final.json")
OUT_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b1_b2/end_state_formal.json"
G_CLIPS = ("male_standard_walk", "male_stop_walk", "texting_standing", "male_start_walk")
P = dict(X=9, walk_s=1.0, stop_b=66, settle=0.4, after=0.6, start_a=10, go_len=2.6, face=90.0)
# walk_s：鏡內第幾秒開始「停下」（停下段約 1.2 秒才停穩）；settle：停穩後停幾秒才拿手機；after：按完靜音後停幾秒才起步


def setup():
    m = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b1_b2")[1]
    import b1b2_shot as S
    Z.POSE_HOOKS.append(S._phone_hook)
    Z.CAM_HOOKS.append(S._stars_face)
    Z.load_clips(G_CLIPS)
    return m


def _old_text():
    """第 4 版拿手機那段：Texting 用的格子範圍、那段在第 4 版的開始秒數（按開關 6.2 秒就是相對它算）"""
    import b1b2_shot as S
    tgt = STATE["tgt"]; base = S.matched_plan()
    seq = mr.Sequence(tgt, base["segs"], blend=base["blend"]); seq.place(0.0, (0, 0), 90.0)
    tx = base["segs"][2]
    return dict(a=tx.a, b=tx.b, t0=seq.T[2][0], match=STATE["match"])


def plan_groom():
    tgt = STATE["tgt"]; X = P["X"]
    W, ST, TX, SW = (L._CL[n] for n in G_CLIPS)
    wn = W["n"] - 1
    old = _old_text(); STATE["old_text"] = old
    a0 = int(round(-HANDLES * FPS)) % wn                 # B0 結尾＝走路第 0 格；往前多走 1 秒
    a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
    a4, b4, _ = F.match_phase(tgt, SW, range(SW["n"] - 30, SW["n"] - 9), W, range(0, wn))
    # 走路要從相位 a0 起、在相位 a1＋X 結束（漸變起點兩邊正好是配對的那一對格子）：
    # 用 splice_clip 把循環「轉」成從 a0 起的一支（Seg 的 loops 只能整圈從 a 播到 b，從半圈起播 loops 會把半圈當一圈）
    want = int(round((HANDLES + P["walk_s"]) * FPS))
    L1 = want + ((a1 + X - (a0 + want)) % wn)
    cyc = wn / FPS; k = L1 // wn + 2
    W1 = mr.splice_clip(W, [(a0 / FPS, cyc)] + [(0, cyc, 1 / FPS)] * k)
    W2 = mr.splice_clip(W, [(b4 / FPS, cyc)] + [(0, cyc, 1 / FPS)] * 4)
    STATE["walk_cut"] = dict(a0=a0, a1=a1, b1=b1, a4=a4, b4=b4, walk_frames=L1)
    segs = [mr.Seg(W1, 0, L1, name="接 B0 的走路（Walking）"),
            mr.Seg(ST, b1, P["stop_b"], hold=P["settle"], name="放慢停下（Stop Walking，播到停穩）"),
            mr.Seg(TX, old["a"], old["b"], hold=P["after"], name="拿手機、按靜音（Texting While Standing）"),
            mr.Seg(SW, P["start_a"], a4 + X, face=P["face"], name="起步（Start Walking，從靜止那格）"),
            mr.Seg(W2, 0, int(3.5 * FPS), face=P["face"], name="走路（Walking）")]
    return segs


def build_groom():
    """新郎：接段 → 擺放（第 HANDLES 秒＝B0 結尾）→ 底（低頭調淺、貼地、起步不下沉，同第 4 版）→ STATE["P0"]、t_text、t_start"""
    import b1b2_r2 as R2, zanim_blocking as BK
    tgt = STATE["tgt"]; fin = json.load(open(FINAL4, encoding="utf8"))
    segs = plan_groom()
    seq, STATE["straight"] = straighten(segs)
    T = seq.T
    t_text = (T[2][0], T[2][0] + segs[2].dur); t_go = T[3][0]; t_start = (t_go, t_go + segs[3].dur)
    dur = t_go + P["go_len"] - HANDLES
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    raw = [seq.at(min(i / FPS, seq.dur))[:2] for i in range(n)]
    info = {}; P0 = []
    keep = fin["base_r3"]["keep"]
    for R, h in raw:
        P0.append((R2.lift_head(tgt, R, keep=keep), h))
    P0, off = F.ground(tgt, P0, L.sole_points(STATE["arm"]))
    info["ground_offset_mm"] = (round(1000 * min(off), 1), round(1000 * max(off), 1))
    a = int((t_start[0] - 0.1) * FPS); b = min(n - 1, int((t_start[0] + 1.75) * FPS))
    z0 = [P0[i][1].z for i in range(a, b + 1)]
    P0, dz = R2.straighten_stance(tgt, P0, L.sole_points(STATE["arm"]), a, b, kmax=fin["base_r3"]["kmax"], zcap=P0[a][1].z + 0.002)
    info["start_hip_drop_before_mm"] = round(1000 * (P0[a][1].z - min(z0)), 1)
    info["start_hip_drop_after_mm"] = round(1000 * (P0[a][1].z - min(P0[i][1].z for i in range(a, b + 1))), 1)
    i0 = int(round(T[1][0] * FPS))                       # 停穩＝停下段開始後、骨盆速度第一次低於 0.08 m/s（checklist 24）
    still = next(i for i in range(i0, n - 3) if (P0[i + 3][1] - P0[i][1]).length * 10 < 0.08)
    marks = dict(stop=T[1][0] - HANDLES, still=still / FPS - HANDLES, text=t_text[0] - HANDLES, go=t_go - HANDLES)
    STATE.update(P0=P0, raw=raw, seq=seq, t_text=t_text, t_start=t_start, info0=info, dur=dur, marks=marks,
                 segs=[(round(T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])    # zanim.stats 用格子秒數（含頭多做的 1 秒）
    shot = [(round(t - HANDLES, 2), d, nm) for t, d, nm in STATE["segs"]]
    return dict(dur=round(dur, 2), frames=n, marks={k: round(v, 2) for k, v in marks.items()}, segs=shot, info=info, straight=STATE["straight"])


def _dir(seq, ta, tb):
    """seq 第 ta～tb 秒骨盆的水平位移方向（度，0＝正 +X；正值＝往 +Y、離鏡頭）"""
    a = seq.at(ta)[1]; b = seq.at(tb)[1]
    return math.degrees(math.atan2(b.y - a.y, b.x - a.x)), (b - a).length


def straighten(segs, iters=4):
    """拉直（第 4 版往鏡頭偏 13°；這次量到走路、停下兩段本身也會往 +Y 斜）：
    每一段有位移的（開頭走路＋走路、停下、起步、最後走路）各自轉到「實際位移方向＝+X」：
    開頭兩段用擺放的角度、其餘用 Seg.face（段開頭的面向）修正；拿手機那段原地站，不動。回傳 (seq, 各段修正前後的偏角)"""
    tgt = STATE["tgt"]; X = P["X"] / FPS
    for k in (1, 3, 4):
        segs[k].face = P["face"]
    yaw = 90.0; log = {}
    for it in range(iters):
        seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS)
        seq.place(HANDLES, B0_END, yaw)
        T = [t for t, _r, _o in seq.T] + [seq.start + seq.dur]
        rng = {"walk": (seq.start, T[1] + X), 1: (T[1] + X, T[2]), 3: (T[3] + X, T[4]), 4: (T[4] + X, T[5])}
        cur = {k: _dir(seq, *v) for k, v in rng.items()}
        if it == 0:
            log["before"] = {str(k): round(a, 1) for k, (a, _l) in cur.items()}
        yaw -= cur["walk"][0]
        for k in (1, 3, 4):
            segs[k].face -= cur[k][0]
    seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS); seq.place(HANDLES, B0_END, yaw)
    T = [t for t, _r, _o in seq.T] + [seq.start + seq.dur]
    rng = {"walk": (seq.start, T[1] + X), 1: (T[1] + X, T[2]), 3: (T[3] + X, T[4]), 4: (T[4] + X, T[5])}
    log["after"] = {str(k): round(_dir(seq, *v)[0], 1) for k, v in rng.items()}
    log["faces"] = {str(k): round(segs[k].face, 1) for k in (1, 3, 4)}; log["place_yaw"] = round(yaw, 1)
    return seq, log


def heading(step=15):
    """每 step 格的骨盆面向（度，90＝+X）與骨盆 y：看路線直不直"""
    import zanim_blocking as BK
    P_ = STATE.get("poses") or STATE["P0"]
    return [(round(i / FPS - HANDLES, 2), round(BK.yaw_of(BK.hips_fw(R)), 1), round(h.y, 3)) for i, (R, h) in enumerate(P_) if i % step == 0]


def hands_groom():
    """手機、握法、按開關、「啵」：沿用第 4 版 final.json，時間跟著拿手機那段平移"""
    import b1b2_shot as S, b1b2_r3 as R3
    fin = json.load(open(FINAL4, encoding="utf8")); old = STATE["old_text"]
    arm = STATE["arm"]; body = L.body_mesh(arm)
    STATE["rad"] = {s: R3.finger_radius(arm, body, s) for s in "LR"}
    g = {"__file__": r"D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/props-zepeto/use_props.py"}
    exec(open(g["__file__"], encoding="utf8").read(), g)
    for key, name in ((fin["phone"]["before"], "B12_Phone"), (fin["phone"]["after"], "B12_PhoneMute")):
        if name not in bpy.data.objects:
            g["place_prop"](key, name=name, parent=bpy.data.collections[PREFIX + "studio"])
    STATE["GL"] = {k: (tuple(v) if isinstance(v, list) else v) for k, v in fin["grip"]["L"].items()}
    STATE["GR"] = {k: (tuple(v) if isinstance(v, list) else v) for k, v in fin["grip"]["R"].items()}
    br = dict(fin["build_r3"]); shift = STATE["t_text"][0] - old["t0"]       # 第 4 版的秒數（從第 0 格算）→ 這一版的格子秒數
    br["t_press"] = br["t_press"] + shift; br["ref_t"] = br["ref_t"] + shift
    r = S.build_r3(**br)
    pp = fin["pop"]
    S.POP_SCALE = tuple(pp["phone_scale"]); S.STAR_SCALE = tuple(pp["star_scale"]); S.STAR_ALPHA = tuple(pp["star_alpha"])
    S.STARS = [(s_["name"], s_["shape"], s_["radius_m"], s_["color"], tuple(s_["dir_m"])) for s_ in pp["stars"]]
    pop = S.pop_setup()
    on = [i for i, m in enumerate(STATE["phone"]) if m is not None]; STATE["phone_c_last"] = STATE["phone"][on[0]].translation.copy()
    STATE["marks"].update(pop=on[0] / FPS - HANDLES, phone_off=on[-1] / FPS - HANDLES, press=br["t_press"] - HANDLES)
    return dict(stats=r["stats"], r3=r["r3"], pop=pop, marks={k: round(v, 2) for k, v in STATE["marks"].items()})


def run_groom():
    t0 = time.time(); m = setup(); r = build_groom(); r["hands"] = hands_groom(); r["sec"] = round(time.time() - t0, 1)
    return r


def cleanup():
    return Z.cleanup(SCENE)


# ════════ 新娘（zanim_cast：v3 身體，2026-10-13 起不是膠囊） ════════
B_CLIPS = ("female_walk", "female_stop_walk", "turn_right_90", "angry_gesture", "turn_left_90", "female_start_walk")
PB = dict(back=0.58, behind=0.52, lag=0.25, react=0.35, tr=(20, 42), tl=(0, 26), start_a=3, lead=0.0, add=False, aim=False, walk_k=None, seam=1,
          akimbo_ramp=0.35, waist_up=0.21, waist_x=0.175, waist_back=0.01,
          skirt=dict(margin=0.015, elbow_k=2.0, max_deg=40), go_turn=(-10.0, 0.0),
          lock=dict(v_on=0.3, ramp=9, z_on=0.015, gap_max=25), win_v=2.0, win_z=0.03, tr_hold=0.0,
          lock_win=[(("t_turn", -0.2), ("t_turn", 0.9)), (("t_go", -0.3), ("t_go", 0.35))])   # 放寬鎖腳的時段：(節點, 秒偏移)
# 2026-10-13 穿上禮服（裙擺半徑 0.335 m）：back 0.45 → 0.58（新郎走路擺手會掃進裙子 8 cm）、behind 0.4 → 0.52（B0 出門才對準門中心）；插腰的手移到裙子上方的腰
#   （waist_up 0.14 → 0.21、waist_x 0.13 → 0.175：原本的位置在裙子腰帶裡面）；skirt：F.skirt_arms 的參數（手臂往外擺離開裙子）
# go_turn：(起步, 走路) 兩段的走向各偏幾度（負＝往新郎那側）（轉身＋插腰＋轉回來會讓她往餐檯那側偏 12 cm，穿禮服時裙擺會碰到餐檯 → 起步後慢慢修回來）
# back／behind：停下時在新郎遠側（+Y）幾 m、往 −X 落後幾 m（和 B0 走位版一樣，側面鏡頭看才不會整個被新郎擋住）；
# lag：比新郎晚幾秒停穩；react：手機「啵」之後幾秒轉頭瞪他；
# tr／tl：Turn Right／Left 90 只取的格子：下一段的漸變從這段結尾前 9 格開始、方向照那一格接 → 結尾多播 9 格（第 33 格約轉 48°＝面向新郎）；
# add：轉身要不要用加法（2026-10-13 試過：加法的轉向不會帶進下一段，插腰時還是面向前方 → 不用）；
# start_a：起步從第幾格（靜止）；lead：比新郎早幾秒起步（負＝晚）


def add_bride():
    m = C.add_actor("bride", "bride")
    with C.as_actor("bride"):
        Z.load_clips(B_CLIPS)
    return m


def _still(c, a, thr=0.08):
    """clip 從第 a 格起、骨盆速度第一次低於 thr m/s 的格子"""
    H = c["hips"]
    for i in range(a, c["n"] - 3):
        if (H[i + 3] - H[i]).length * 10 < thr:
            return i
    return c["n"] - 1


def _retime(c, k):
    """動畫放慢／加快：k＜1 變慢（格數變多）。每格照原片內插（骨頭 slerp、骨盆 lerp）"""
    n0 = c["n"]; n = int(round((n0 - 1) / k)) + 1
    R, H, Y = [], [], []
    for j in range(n):
        x = min(j * k, n0 - 1); i = min(int(x), n0 - 2); f = x - i
        R.append({b: c["R"][i][b].slerp(c["R"][i + 1][b], f) for b in c["R"][i]})
        H.append(c["hips"][i].lerp(c["hips"][i + 1], f)); Y.append(c["yaw"][i] + (c["yaw"][i + 1] - c["yaw"][i]) * f)
    return dict(c, n=n, R=R, hips=H, yaw=Y)


def _no_hop(tgt, poses, pts, keep=0.0015, smooth=4):
    """兩腳同時離地的格子（Mixamo 快轉身會小跳一下：最高 25 mm、約 0.3 秒）整個人往下壓，讓低的那隻腳貼地；前後 smooth 格平滑"""
    low = []
    for R, h in poses:
        so = L.soles(tgt, R, h, pts)
        low.append(min(min(p.z for p in so["L"]), min(p.z for p in so["R"])))
    d = [max(0.0, z - keep) if z > 0.008 else 0.0 for z in low]
    n = len(d); dd = [max(d[max(0, i - smooth):min(n, i + smooth + 1)]) for i in range(n)]
    dd = [sum(dd[max(0, i - smooth):min(n, i + smooth + 1)]) / (min(n, i + smooth + 1) - max(0, i - smooth)) for i in range(n)]
    out = [(R, h - Vector((0, 0, min(dd[i], max(0.0, low[i] - keep))))) for i, (R, h) in enumerate(poses)]   # 壓下去不超過低的那隻腳離地的高度（不陷地）
    return out, round(1000 * max(dd), 1)


def _akimbo(tgt, poses, t0, t1):
    """插腰（2026-10-13 近照：Angry Gesture 的手在骨盆兩側同高，ZEPETO 手臂長 → 套上去手臂打直、像垂手）。
    參考：arms akimbo＝手放腰上、手肘往外彎（phrases.org.uk／literarydevices.net），常帶不服、挑釁的意思。
    t0～t1（鏡內秒）：手腕放到腰側（骨盆上 waist_up、離中線 waist_x、往後 waist_back），四指朝前下、掌心貼腰，手肘往外後方；
    前後 PB["akimbo_ramp"] 秒漸入漸出"""
    from zanim_hand import hand_quat, put_hand_pole
    rp = PB["akimbo_ramp"]; out = []
    for i, (R, h) in enumerate(poses):
        t = i / FPS - HANDLES
        if t <= t0 or t >= t1:
            out.append((R, h)); continue
        w = min(1.0, (t - t0) / rp, (t1 - t) / rp); w = w * w * (3 - 2 * w)
        Rh = R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()
        Hd = tgt.fk(R, h); c = Hd["J_Bip_C_Hips"]
        up = Vector((0, 0, 1)); fw = Rh @ Vector((0, -1, 0)); fw.z = 0; fw.normalize()
        for s_, sg in (("L", 1), ("R", -1)):
            side = Rh @ Vector((sg, 0, 0)); side.z = 0; side.normalize()
            wrist = c + up * PB["waist_up"] + side * PB["waist_x"] - fw * PB["waist_back"]
            q = hand_quat(tgt, s_, fw * 0.75 - up * 0.65, -side)
            M = Matrix.Translation(wrist) @ q.to_matrix().to_4x4()
            R = put_hand_pole(tgt, R, h, s_, M, w, (side - fw * 0.5).normalized(), 1.0)
        out.append((R, h))
    return out


FACE_GLARE = dict(browDownLeft=1.0, browDownRight=1.0, eyeSquintLeft=0.7, eyeSquintRight=0.7, mouthFrownLeft=1.0, mouthFrownRight=1.0,
                  mouthPressLeft=0.5, mouthPressRight=0.5, noseSneerLeft=0.4, noseSneerRight=0.4, cheekSquintLeft=0.3, cheekSquintRight=0.3)
# 瞪人：眉壓低、瞇眼、嘴角往下、抿嘴（ARKit 52 的名稱）。2026-10-13 近照比較：眉 0.8／嘴角 0.55 那組看起來只像嘟嘴，這組才像在瞪


def face_w(t):
    """瞪人表情的權重：轉頭那一刻起 0.2 秒變臉、轉回來後 0.4 秒消掉"""
    bp = STATE["b_plan"]; a = bp["t_turn"]; b = bp["glare"][1] + 0.2
    if t <= a or t >= b + 0.4:
        return 0.0
    w = min(1.0, (t - a) / 0.2, (b + 0.4 - t) / 0.4)
    return w * w * (3 - 2 * w)


TALK = dict(a=0.35, b=0.25, hz=(4.2, 2.7), jaw=0.5)
# 2026-10-13 使用者（B1→B2 第 1 輪）：6.2 秒新娘要動嘴巴跟新郎講話＝插腰瞪他時開口唸他。
#   瞪人開始 a 秒後到結束前 b 秒：下巴一開一合（兩個頻率疊起來，不像機器節拍），講話時嘴角的抿嘴（mouthPress）放掉、偶爾嘟嘴


def talk_vals(t):
    """唸他的嘴型（加在瞪人表情上）"""
    bp = STATE["b_plan"]; a = bp["glare"][0] + TALK["a"]; b = bp["glare"][1] - TALK["b"]
    if t <= a or t >= b:
        return {}
    env = min(1.0, (t - a) / 0.15, (b - t) / 0.15)
    s1 = abs(math.sin(2 * math.pi * TALK["hz"][0] * (t - a))); s2 = 0.5 + 0.5 * math.sin(2 * math.pi * TALK["hz"][1] * (t - a) + 1.0)
    jaw = TALK["jaw"] * env * (0.35 + 0.65 * s1) * (0.6 + 0.4 * s2)
    return dict(jawOpen=jaw, mouthPressLeft=-0.5 * env, mouthPressRight=-0.5 * env, mouthFunnel=0.25 * env * (1 - s1) * s2, mouthLowerDownLeft=0.3 * jaw, mouthLowerDownRight=0.3 * jaw)


def face_vals(t):
    w = face_w(t); out = {k: v * w for k, v in FACE_GLARE.items()}
    for k, v in talk_vals(t).items():
        out[k] = max(0.0, out.get(k, 0.0) + v)
    return out


FACE_KEYS = tuple(dict.fromkeys(list(FACE_GLARE) + ["jawOpen", "mouthFunnel", "mouthLowerDownLeft", "mouthLowerDownRight"]))


def _face_hook(i):
    hd = L.head_mesh(C.actor("bride")["arm"]); v = face_vals(i / FPS - HANDLES)
    for k in FACE_KEYS:
        kb = hd.data.shape_keys.key_blocks.get(k)
        if kb is not None:
            kb.value = v.get(k, 0.0)


def bake_face():
    """表情烤成形態鍵的關鍵影格（樣張用；SP.bake 只烤骨頭和物件）"""
    hd = L.head_mesh(C.actor("bride")["arm"]); key = hd.data.shape_keys; n = len(STATE["poses"])
    ad = key.animation_data_create(); act = bpy.data.actions.get("SAMPLE_BrideFace") or bpy.data.actions.new("SAMPLE_BrideFace"); ad.action = act
    import zanim_sample as SP
    V = [face_vals(i / FPS - HANDLES) for i in range(n)]
    for k in FACE_KEYS:
        if k in key.key_blocks:
            SP._put(act, key, f'key_blocks["{k}"].value', 0, [V[i].get(k, 0.0) for i in range(n)])
    return len(FACE_KEYS)


def plan_bride(extra=0):
    """新娘的時間全部跟著新郎的節點（停穩、啵、起步）"""
    X = P["X"]; mk = STATE["marks"]; g_still = mk["still"]
    with C.as_actor("bride"):
        tgt = STATE["tgt"]
        W, ST, TR, AG, TL, SW = (L._CL[n] for n in B_CLIPS)
        gW = C.cast()["_main"]["clips"]["male_standard_walk"]
        sp = lambda c: (c["hips"][-1] - c["hips"][0]).length / ((c["n"] - 1) / FPS)
        STATE["b_plan_speed"] = k = PB["walk_k"] or sp(gW) / sp(W)    # 新娘走路照新郎的速度（女生走路每秒 0.815 m、新郎 0.70 m：不放慢的話前段落後 1.4 m、起步後追上去和新郎重疊）
        W = _retime(W, k)
        wn = W["n"] - 1
        a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 12))
        a4, b4, _ = F.match_phase(tgt, SW, range(SW["n"] - 25, SW["n"] - 6), W, range(0, wn))
        st_i = _still(ST, b1 + 10)                        # 停下那支第幾格停穩
        t_still = g_still + PB["lag"]                     # 新娘停穩（鏡內秒）
        t_stop = t_still - (st_i - b1) / FPS              # 停下那段開始
        L1 = int(round((t_stop + HANDLES + X / FPS) * FPS))
        L1 = L1 + ((a1 + X - L1) % wn) + extra * wn       # 走路從第 0 格起、在 a1＋X 結束（相位對得上）；extra：多走／少走幾圈
        t_stop = L1 / FPS - X / FPS - HANDLES
        sx = PB["seam"] / FPS                             # 女生走路頭尾不是完全接得起來：接縫漸變 seam 格（1 格時每圈滑 9.5 mm）
        W1 = mr.splice_clip(W, [(0, wn / FPS)] + [(0, wn / FPS, sx)] * (L1 // wn + 2))
        W2 = mr.splice_clip(W, [(b4 / FPS, wn / FPS)] + [(0, wn / FPS, sx)] * 4)
        t_turn = mk["pop"] + PB["react"]
        t_go = mk["go"] - PB["lead"]
        tl_d = (PB["tl"][1] - PB["tl"][0]) / FPS
        segs = [mr.Seg(W1, 0, L1, name="新娘走路（Female Walk）"),
                mr.Seg(ST, b1, ST["n"] - 1, name="新娘停下（Female Stop Walking）"),
                mr.Seg(TR, *PB["tr"], hold=PB["tr_hold"], add=PB["add"], at=t_turn + HANDLES, name="手機一響轉頭瞪他（Turn Right 90 中段，約 48°）"),
                mr.Seg(AG, 0, AG["n"] - 1, name="插腰生氣（Angry Gesture）"),
                mr.Seg(TL, *PB["tl"], add=PB["add"], at=t_go - tl_d - 0.2 + HANDLES, name="轉回來（Turn Left 90 前段，約 48°）"),
                mr.Seg(SW, PB["start_a"], a4 + X, face=P["face"], at=t_go + HANDLES, name="新娘起步（Female Start Walking）"),
                mr.Seg(W2, 0, int(3.0 * FPS), face=P["face"], name="新娘走路（Female Walk）")]
        STATE["b_plan_b4"] = b4
        STATE["b_plan"] = dict(walk_k=round(k, 3), t_stop=round(t_stop, 2), t_still=round(t_stop + (st_i - b1) / FPS, 2), t_turn=round(t_turn, 2), t_go=round(t_go, 2), st_i=st_i, b1=b1, a1=a1)
        return segs


def build_bride():
    """擺放：停穩那一格骨盆在新郎停穩位置＋(−behind, +back)；走路方向拉直（同新郎）"""
    import zanim_blocking as BK
    n = len(STATE["poses"])                               # 和新郎一樣多格
    gi = int(round((STATE["marks"]["still"] + HANDLES) * FPS)); gh = STATE["P0"][gi][1]
    g0 = STATE["P0"][0][1]
    # 2026-10-13：開頭就在新郎左後方（behind、back），再挑停下的時機（走路多走／少走整圈）讓停穩時離新郎最接近 behind。
    # 舊做法（停穩的位置往回推）：新郎停下那段比她多走約 1 m → 前段落後 1.4 m
    best = None
    for extra in (-1, 0, 1, 2):
        segs = plan_bride(extra)
        if STATE["b_plan"]["t_still"] > STATE["marks"]["pop"] + PB["react"] - 0.3 or STATE["b_plan"]["t_stop"] < -0.5:
            continue
        with C.as_actor("bride"):
            seq = mr.Sequence(STATE["tgt"], segs, blend=P["X"] / FPS); seq.place(0.0, (g0.x - PB["behind"], g0.y + PB["back"]), 90.0)
            hb = seq.at(STATE["b_plan"]["t_still"] + HANDLES)[1]
        gap = gh.x - hb.x
        if best is None or abs(gap - PB["behind"]) < abs(best[1] - PB["behind"]):
            best = (extra, gap)
    segs = plan_bride(best[0]); STATE["b_plan"]["gap_at_still"] = round(best[1], 2)
    with C.as_actor("bride"):
        tgt = STATE["tgt"]
        ta = 0.0
        xy = (g0.x - PB["behind"], g0.y + PB["back"])
        X = P["X"] / FPS; yaw = 90.0
        bx = Vector((gh.x - best[1], gh.y + PB["back"], 0)); gx = Vector((gh.x, gh.y, 0))          # 停穩時兩人的位置
        STATE["b_plan"]["to_groom"] = round(math.degrees(math.atan2((gx - bx).x, -(gx - bx).y)), 1)
        if PB["aim"]:                                     # 插腰那段直接指定面向新郎（加法轉身的轉向不會帶進下一段；但硬轉會讓腳在漸變那 0.3 秒滑 11 mm）
            segs[3].face = STATE["b_plan"]["to_groom"]
        for k in (5, 6):
            segs[k].face = P["face"]
        for it in range(4):
            seq = mr.Sequence(tgt, segs, blend=X); seq.place(ta, xy, yaw)
            T = [t for t, _r, _o in seq.T] + [seq.start + seq.dur]
            yaw -= _dir(seq, seq.start, T[1] + X)[0]
            for k in (5, 6):
                segs[k].face -= _dir(seq, T[k] + X, T[k + 1])[0] - PB["go_turn"][k - 5]
        seq = mr.Sequence(tgt, segs, blend=X); seq.place(ta, xy, yaw)
        poses = [seq.at(min(i / FPS, seq.start + seq.dur))[:2] for i in range(n)]
        pts = L.sole_points(STATE["arm"])
        poses, off = F.ground(tgt, poses, pts)
        a = int(round((STATE["b_plan"]["t_turn"] - 0.2 + HANDLES) * FPS)); b = int(round((STATE["b_plan"]["t_turn"] + 0.9 + HANDLES) * FPS))
        sub, hop = _no_hop(tgt, poses[a:b + 1], pts)      # 只處理轉身那段（女生走路本來就有兩腳都離地的格子，不能動）
        poses[a:b + 1] = sub
        STATE["b_plan"]["hop_removed_mm"] = hop
        poses, _li = F.foot_lock(tgt, poses, pts, **PB["lock"])
        mk = STATE["b_plan"]
        for a_, b_ in PB["lock_win"]:                    # 轉身、起步第一步：腳踝快過 0.3 m/s 不算著地 → 只在這幾格放寬門檻再鎖一次（全段放寬會把走路弄壞）。
            a = int(round((mk[a_[0]] + a_[1] + HANDLES) * FPS)); b = int(round((mk[b_[0]] + b_[1] + HANDLES) * FPS))
            sub, _ = F.foot_lock(tgt, poses[a:b + 1], pts, v_on=PB["win_v"], ramp=3, z_on=PB["win_z"])   # 試過一次鎖完（v_on 給每格不同值）：ramp 只能全段一樣，轉身那幾格反而滑 6 mm
            poses[a:b + 1] = sub
        poses = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in poses]   # Mixamo 原片手指套到這副身體會像在比手勢（同新郎第 4 版）
        T_ = seq.T
        STATE["b_plan"].update(glare=(round(T_[3][0] - HANDLES, 2), round(T_[4][0] - HANDLES, 2)))
        if OUTFIT_B:                                      # 禮服：手垂下會沒入裙子 → 手臂往外擺（插腰那段之後由 IK 蓋掉）
            poses, STATE["b_plan"]["skirt_arms_deg"] = F.skirt_arms(tgt, poses, **PB["skirt"])
        poses, STATE["b_plan"]["head_up_max"] = F.level_head(tgt, poses)   # 2026-10-13 使用者：新娘走路頭往斜上方看 → 仰角超過 5° 壓回來
        poses = _akimbo(tgt, poses, *STATE["b_plan"]["glare"])
        STATE.update(poses=poses, seq=seq, segs=[(round(seq.T[i][0], 2), round(sg.dur, 2), sg.name) for i, sg in enumerate(segs)])
        STATE["stats"] = Z.stats()
        st = STATE["stats"]["summary"]
        yaws = [(round(i / FPS - HANDLES, 2), round(BK.yaw_of(BK.hips_fw(R)), 1), round(h.x, 2), round(h.y, 2)) for i, (R, h) in enumerate(poses) if i % 15 == 0]
    return dict(plan=STATE["b_plan"], segs=[(round(t - HANDLES, 2), d, nm) for t, d, nm in C.actor("bride")["segs"]], stats=st, track=yaws)


# ════════ 衣服、場景、鏡頭、短片 ════════
OUTFIT_G = "groom-beige-3piece"
OUTFIT_B = "bride-blush-ballgown"                   # 2026-10-13 服裝端定案（outfit/bride_blush_ballgown@bride v1，裙寬 0.32 m）


def dress():
    """衣服一開始就穿（新郎西裝）；新娘禮服還沒定案就先不穿。衣服的 Solidify／FixFolds 在視窗關掉（擺姿勢快）"""
    import zanim_dress as D
    out = {}
    out["groom"] = D.dress(OUTFIT_G)
    if OUTFIT_B:
        with C.as_actor("bride"):
            out["bride"] = D.dress(OUTFIT_B, body="bride")
    for o in bpy.data.objects:
        if o.name in (STATE.get("outfit_objs") or []) + (C.actor("bride").get("outfit_objs") or []):
            for m in o.modifiers:
                if m.type in ("SOLIDIFY",) or "FixFolds" in m.name:
                    m.show_viewport = False
    return out


def scene_set():
    """走廊（和 B0 同一個平移 venue_offset.json：拉直後走線在 y≈0.1，和 B0 一致，不再加 B2 走位版用的 stop_y）"""
    import zanim_blocking as BK
    vo = json.load(open(BK.VENUE_OFFSET)); off = (vo["dx"], vo["dy"], 0.0)
    objs = BK.venue("Scene_VenueCorridor", off)
    hid = []
    for n, o in objs.items():                             # 換景柱子是 B3 結尾用的，這一鏡藏起來（同 B2）
        if n.startswith("I_ZP_pillar") and o.location.y < -1.0:
            o.hide_render = o.hide_viewport = True; hid.append(n)
    return dict(offset=off, hidden=hid, n=len(objs))


def camera_fn():
    """側面跟拍（全片規則：兩人中點放畫面 70%）；新郎停穩到起步之間鏡頭固定"""
    import zanim_blocking as BK
    mk = STATE["marks"]
    return BK.side_follow(holds=[(mk["still"], mk["go"])], handles=HANDLES,
                          partner=lambda i: tuple(C.hips_world("bride"))[:2])


def clip(v=1, size=(960, 540)):
    """存工作用樣張（不登記總表）→ 回傳背景渲短片的指令（BODY 自動點名兩副身體）"""
    import zanim_sample as SP, b1b2_shot as S
    SP.new_camera("SAMPLE_Cam", 35.0)
    for a in (STATE["arm"], C.actor("bride")["arm"]):     # 上一次烤的關鍵影格會蓋掉 pose_at 擺的姿勢 → 先清掉
        a.animation_data_clear()
    hk = L.head_mesh(C.actor("bride")["arm"]).data.shape_keys
    if hk is not None:
        hk.animation_data_clear()
    objs = [o for o in (bpy.data.objects.get("B12_Phone"), bpy.data.objects.get("B12_PhoneMute")) if o]
    stars = [bpy.data.objects[s_[0]] for s_ in S.STARS if s_[0] in bpy.data.objects]
    alpha = [(o, next(nd for nd in o.active_material.node_tree.nodes if nd.type == "BSDF_PRINCIPLED"), "Alpha") for o in stars]
    # 烤關鍵影格只需要骨頭：網格（身體、衣服、場景）先關掉視窗顯示，每格不用重算變形（穿衣服的兩個人一格要好幾秒，會超過 MCP 120 秒）
    meshes = [o for o in STATE["sc"].objects if o.type == "MESH" and not o.hide_viewport and o not in objs + stars]
    for o in meshes:
        o.hide_viewport = True
    try:
        cf = camera_fn()                                  # 建鏡頭路線也要逐格擺姿勢：一樣在關掉網格時做
        out = SP.bake(objects=objs + stars, alpha=alpha, camera_fn=cf)
    finally:
        for o in meshes:
            o.hide_viewport = False
    out["face_keys"] = bake_face()
    path = SP.save("b1_b2_formal")
    cmd = SP.render_clip("b1_b2_formal", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + f"/formal_v{v}.mp4", size=size)
    return dict(out, path=path, cmd=cmd)


def run(load_bride=True):
    t0 = time.time(); r = run_groom()
    if load_bride:
        add_bride()
    r["bride"] = build_bride(); r["dress"] = dress()
    if _face_hook not in Z.POSE_HOOKS:
        Z.POSE_HOOKS.append(_face_hook); r["scene"] = scene_set(); r["sec"] = round(time.time() - t0, 1)
    return r


def close(t, views, out=None, res=480, lens=50, hide=None):
    """近照：烤好的樣張用 frame_set 擺姿勢（鏡頭 SAMPLE_Cam 有關鍵影格，另開 CLOSE_Cam）。
    views：[(名稱, 角色 "groom"|"bride", 骨頭, (dx, dy, dz) 鏡頭相對骨頭的位置, 看向點再往上幾 m)]"""
    sc = STATE["sc"]; out = out or STATE["out_dir"] + "/formal_close"; os.makedirs(out, exist_ok=True)
    cam = bpy.data.objects.get("CLOSE_Cam")
    if cam is None:
        cam = bpy.data.objects.new("CLOSE_Cam", bpy.data.cameras.new("CLOSE_Cam")); sc.collection.objects.link(cam)
    prev = sc.camera; sc.camera = cam
    rx, ry = sc.render.resolution_x, sc.render.resolution_y; sc.render.resolution_x = sc.render.resolution_y = res
    files = []
    hid = []
    if hide:                                              # 擋到鏡頭的人先藏（例：新娘面向新郎時，正面近照被新郎擋住）
        arm = STATE["arm"] if hide == "groom" else C.actor("bride")["arm"]
        hid = [o for o in sc.objects if o.type == "MESH" and not o.hide_render and (o.parent == arm or any(m.type == "ARMATURE" and m.object == arm for m in o.modifiers))]
        hid += [o for o in arm.children_recursive if o.type == "MESH" and not o.hide_render and o not in hid]
        for o in hid:
            o.hide_render = True
    try:
        sc.frame_set(1 + int(round((t + HANDLES) * FPS)))
        for name, who, bone, off, up in views:
            arm = STATE["arm"] if who == "groom" else C.actor("bride")["arm"]
            c = arm.matrix_world @ arm.pose.bones[bone].head + Vector((0, 0, up))
            Z._aim(cam, c + Vector(off), c, lens)
            files.append(Z.render_still(f"{out}/{t:05.2f}_{name}.jpg"))
    finally:
        sc.camera = prev; sc.render.resolution_x, sc.render.resolution_y = rx, ry
        for o in hid:
            o.hide_render = False
    return files


def end_state(path=OUT_END):
    """鏡內最後一格（t＝dur）兩人的骨盆、面向、走路相位：B2 正式版的開頭照這個接（2026-10-13）"""
    import zanim_blocking as BK
    i = int(round((STATE["dur"] + HANDLES) * FPS))
    R, h = STATE["poses"][i]; tgt = STATE["tgt"]
    W = L._CL["male_standard_walk"]; wn = W["n"] - 1
    tg = STATE["seq"].T[4][0]
    gph = (STATE["walk_cut"]["b4"] + (i / FPS - tg) * FPS) % wn
    bst = C.actor("bride"); bR, bh = bst["poses"][i]; bseq = bst["seq"]
    with C.as_actor("bride"):
        byaw = BK.yaw_of(BK.hips_fw(bR))
        bwn = int(round((L._CL["female_walk"]["n"] - 1) / STATE["b_plan"]["walk_k"]))
    bph = (STATE["b_plan_b4"] + (i / FPS - bseq.T[6][0]) * FPS) % bwn
    d = dict(what="B1→B2 正式版鏡內最後一格（B2 開頭照這個接）", t_end=round(STATE["dur"], 3),
             groom=dict(hips=list(h), yaw=round(BK.yaw_of(BK.hips_fw(R)), 2), walk_phase=round(gph, 1), wn=wn, clip="male_standard_walk"),
             bride=dict(hips=list(bh), yaw=round(byaw, 2), walk_phase=round(bph, 1), wn_retimed=bwn, walk_k=STATE["b_plan"]["walk_k"], clip="female_walk"))
    json.dump(d, open(path, "w"), ensure_ascii=False, indent=1)
    return d
