# B3 正式版（2026-10-13 導演端：場景搬好就照 B2 結尾直接開工）。走廊的代客泊車立牌前：
# 新娘拉著新郎手腕走進來停下 → 放開 → 新郎從褲袋掏車鑰匙、舉到胸前晃（要去開車）→ 新娘轉身一把抓走鑰匙、收在胸前、
# 右手食指在臉旁左右搖（喝酒不開車）→ 新郎手停在半空、垂下 → 新娘轉回前方、兩人起步。
# 開頭接 B2 正式版最後一格（b2/end_state_formal.json：位置、面向、走路相位、新娘左手（BS）握新郎右手腕）。
# 2026-10-13 場景端新座標：走廊 x 5.746 以後牆退到 y 1.9（泊車凹處）；立牌 (7.946, 1.62)；裝飾柱 (9.546, 0.45) 在走線上 → 新娘骨盆最遠 x≈8.55。
# 姿勢參考：搖手指＝食指伸直朝上、其餘握起，左右擺，意思是警告、不贊成、堅定的「不」（talks.co/p/hand-gesture-meanings）；
#   晃鑰匙：分鏡寫「拇指與食指捏住鑰匙圈，鑰匙垂在手下方」（網路上查不到專門描述，照分鏡）。
# 用法（MCP）：
#   # BODY=groom,bride
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b3"); import b3_formal as B3F; print(B3F.run())
import bpy, os, sys, math, json, time
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
import zanim_fix as F
import zanim_cast as C
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE, PREFIX = "B3_FORMAL", "ZA_"
FPS = 30
HANDLES = 1.0
B2_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b2/end_state_formal.json"
OUT_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b3/end_state_formal.json"
G_CLIPS = ("male_standard_walk", "male_stop_walk", "standing_idle", "male_start_walk", "turn_right_90", "turn_left_90")
B_CLIPS = ("female_walk", "female_stop_walk", "turn_180_left", "female_idle", "female_start_walk", "shaking_head_no_dismissive")
# 2026-10-13 第 1 版：Shaking Head No 整個人往前彎 90°（原片是彎腰對矮的人搖手）→ 改 Female Idle＋Shaking Head No（Dismissive，只搖頭、手不動），手用 IK
P = dict(X=9, g_half=True, face_off=15.0, stop_b=66, start_a=10, g_lag=0.0, go_lag=0.25, go_len=0.9,
         release=0.15, rel_s=0.45, rel_lift=0.15, pocket=(0.35, 0.75), key_up=(0.9, 1.4), grab=3.0, freeze=0.35, drop=0.6,
         turn1=0.35, wag=(3.3, 4.6), turn2=4.7, go=5.4, g_tr=(20, 56), g_tl=(0, 40), g_face=1.0, g_extra=-25.0, b_stop_bend=25.0, b_go_face=(-20.0, -10.0), g_go_face=(10.0, 5.0), b_turn_inplace=True, b_turn_left=True, b_pivot=True, b_pivot_s=1.2, pivot_s=0.9, pivot_lift=0.035,
         jig_hz=2.5, jig_amp=(0.035, 0.025), key_swing=32.0, show=(0.33, 0.06, 0.12), g_back=0.06)
# 2026-10-13 使用者第 4 次：① 新郎再往右轉、看得到半張臉（g_extra）；② 鑰匙不明顯、甩太短 → grab 2.3 → 3.0（甩約 1.6 秒，之後的時間一起往後 0.7 秒）、
#   手甩的幅度 jig_amp（左右 m、上下 m）、鑰匙擺動 key_swing 度、每秒 jig_hz 下、鑰匙放大 KEY_SCALE；
#   show：舉鑰匙的位置（上胸往前 m、往右 m、往上 m；舉到肩膀高、襯在淺色牆前，胸前時深色鑰匙疊在西裝上看不出來）；
#   g_back：轉身那一步順便往後退幾 m（多轉 25° 後鞋子碰進裙擺 1.8 cm）
# 2026-10-13 使用者第 2 次：看不出面對面（新娘比新郎靠鏡頭 0.5 m，兩人連線斜向鏡頭）→ b_stop_bend：新娘停下時往牆那側彎幾度、
#   face_off 40 → 15（她多朝鏡頭的角度）、g_face 0.85 → 1.0（新郎正對她）；兩人同深度後一起往前走左右只隔 0.23 m →
#   b_go_face／g_go_face：起步、走路兩段的走向偏幾度（新娘斜向鏡頭、新郎斜向牆，拉開距離；B4 在柱子後面重新站位）
# g_tr：Turn Right 90 取的格子（轉身在 24～44 格；後面要多播 9 格以上，否則下一段照「漸變開始那格」的面向接，等於轉回去——2026-10-13 使用者：新郎短暫轉身又回復原本方向）
SKIRT = dict(margin=0.015, elbow_k=2.0, max_deg=40)   # F.skirt_arms（同 B1→B2）
# 時間（鏡內秒，相對新娘停穩 t_bs）：release 放開手腕（rel_s 秒內鬆開）；pocket 新郎右手伸進褲袋（到、拿出）；key_up 舉到胸前（起、到）；
# grab 新娘左手抓走；freeze 新郎手停在半空幾秒、drop 幾秒內垂下；turn1 新娘轉身面向新郎；wag 搖手指（起、迄）；turn2 轉回前方；go 新娘起步
# g_lag：新郎比新娘晚幾秒開始停下；go_lag：新郎比新娘晚幾秒起步；go_len：新娘起步後幾秒結束（骨盆不能過 x 8.55）


def _b2():
    p = os.path.abspath(os.path.join(HERE, "..", "b2"))
    if p not in sys.path:
        sys.path.insert(0, p)
    import b2_formal as B2F
    return B2F


def _fm():
    return _b2()._fm()


def _b0():
    return _b2()._b0()


def setup():
    m = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b3")[1]
    Z.load_clips(G_CLIPS)
    C.add_actor("bride", "bride")
    with C.as_actor("bride"):
        Z.load_clips(B_CLIPS)
    return m


_yaw = lambda tgt, R: _b2()._yaw(tgt, R)
_sm = lambda t, a, b: _b2()._sm(t, a, b)


def _walk_in(tgt, W, ST, end, k=None, half=False):
    """接 B2 的走路：從 end 的相位起播，走 L1 格接停下（相位配對）。回傳 (W1, a1, b1, wn, a0)。
    half：改用另一隻腳接停下（配對點在最佳點的半圈外）→ 停點多走半步（停點只能整圈挑，半步才調得到兩人距離）"""
    FM = _fm()
    if k:
        W = FM._retime(W, k)
    wn = W["n"] - 1
    a0 = int(round(end["walk_phase"] - HANDLES * FPS)) % wn
    a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 12))
    if half:
        a1, b1, _ = F.match_phase(tgt, W, [(a1 + wn // 2 + d) % wn for d in range(-4, 5)], ST, range(0, 20))
    W1 = mr.splice_clip(W, [(a0 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * 4)
    return W, W1, a1, b1, wn, a0


def _place(tgt, segs, end):
    """第 HANDLES 秒骨盆、面向對上 B2 最後一格（反覆修正擺在第 0 格的位置）"""
    want = Vector(end["hips"][:2]); xy = Vector((want.x - 0.6, want.y)); yaw = end["yaw"]
    for _ in range(5):
        seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS); seq.place(0.0, tuple(xy), yaw)
        R, h, _y = seq.at(HANDLES)
        yaw += end["yaw"] - _yaw(tgt, R); xy += want - h.xy
    seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS); seq.place(0.0, tuple(xy), yaw)
    return seq


def plan_bride(L1x=0, base=None):
    """新娘：走路（接 B2）→ 停下 → 往右轉身（Turn 180 Left 鏡射，臉朝鏡頭）→ Shaking Head No（身體）→ Turn 180 Left 轉回前方 → 起步"""
    X = P["X"]; end = json.load(open(B2_END))["bride"]; FM = _fm()
    with C.as_actor("bride"):
        tgt = STATE["tgt"]
        W, ST, TT, SH, SW, SD = (L._CL[n] for n in B_CLIPS)
        W, W1, a1, b1, wn, a0 = _walk_in(tgt, W, ST, end, end["walk_k"])
        SW = FM._retime(SW, end["walk_k"])
        TR = dict(mr.mirror_clip(TT, tgt), name="turn_180_right")
        T1, T2 = (TT, TR) if P["b_turn_left"] else (TR, TT)   # 2026-10-13 使用者（導演第 4 輪）：新娘轉身改往左（新郎在她左後方，往左轉約 160° 就面向他；往右要轉 200°、圈太大），轉回前方往右
        if P["b_turn_inplace"]:                           # 原地轉身：轉 180° 的兩支原片會往前走約 0.3 m，穿禮服時會走到新郎身上（兩人只剩 0.4 m）
            T1, T2 = (dict(c, hips=[Vector((c["hips"][0].x, c["hips"][0].y, h.z)) for h in c["hips"]]) for c in (T1, T2))
        a4, b4, _ = F.match_phase(tgt, SW, range(SW["n"] - 25, SW["n"] - 6), W, range(0, wn))
        L1 = L1x + ((a1 + X - (a0 + L1x)) % wn)
        st_i = FM._still(ST, b1 + 10)
        if P["b_stop_bend"]:                              # 停下時往牆那側彎（正＝左轉）：和新郎站到差不多的深度，鏡頭才看得出兩人面對面
            ST = F.bend(ST, P["b_stop_bend"], b1, b1 + 20)
        t_bs = (L1 - X + (st_i - b1)) / FPS - HANDLES             # 新娘停穩（鏡內秒）
        t0 = t_bs if base is None else base                       # 動作的起算點：兩人都停穩那一刻（新郎比她晚停）
        tm = {k: (t0 + v if isinstance(v, float) else tuple(t0 + x for x in v)) for k, v in P.items()
              if k in ("release", "pocket", "key_up", "grab", "turn1", "wag", "turn2", "go")}
        tm["bs"] = t_bs; tm["base"] = t0
        W2 = mr.splice_clip(W, [(b4 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * 3)
        segs = [mr.Seg(W1, 0, L1, name="新娘拉著新郎走（Female Walk）"),
                mr.Seg(ST, b1, ST["n"] - 1, name="停在立牌旁（Female Stop Walking）")]
        if P["b_pivot"]:                                  # 2026-10-13：轉身改用 F.pivot_turn（build() 補）——Turn 180 往左套上去左腳滑 5 cm、兩腳同時離地 7 格
            segs += [mr.Seg(SH, 0, min(SH["n"] - 1, int(round((tm["wag"][0] - 0.3 - tm["turn1"]) * FPS)) + X), at=tm["turn1"] + HANDLES,
                            name="往左轉身面向新郎（跨步）→ 看他掏鑰匙、搶過來（Female Idle）"),
                     mr.Seg(SD, 0, SD["n"] - 1, at=tm["wag"][0] - 0.3 + HANDLES, name="搖頭搖手指（Shaking Head No Dismissive）")]
        else:
            segs += [mr.Seg(T1, 0, T1["n"] - 1, at=tm["turn1"] + HANDLES, name="轉身面向新郎（%s）" % ("Turn 180 Left，往左轉" if P["b_turn_left"] else "Turn 180 Left 鏡射成右轉")),
                     mr.Seg(SH, 0, min(SH["n"] - 1, int(round((tm["wag"][0] - 0.3 - tm["turn1"] - (TR["n"] - 1 - X) / FPS) * FPS)) + X),
                            name="看他掏鑰匙、搶過來（Female Idle）"),
                     mr.Seg(SD, 0, SD["n"] - 1, at=tm["wag"][0] - 0.3 + HANDLES, name="搖頭搖手指（Shaking Head No Dismissive）"),
                     mr.Seg(T2, 0, T2["n"] - 1, at=tm["turn2"] + HANDLES, name="轉回前方（%s）" % ("Turn 180 Left 鏡射成右轉" if P["b_turn_left"] else "Turn 180 Left"))]
        segs += [mr.Seg(SW, 3, a4 + X, face=90.0 + P["b_go_face"][0], at=tm["go"] + HANDLES, name="轉回前方（往右跨步）→ 起步（Female Start Walking）"),
                mr.Seg(W2, 0, int(2.5 * FPS), face=90.0 + P["b_go_face"][1], name="走路（Female Walk）")]
        return segs, tm


def plan_groom(tm, L1x=0, turn=0.0, yaw0=90.0):
    """新郎：走路（接 B2）→ 停下 → 轉向新娘（Turn Right 90，轉向調成 turn 度）→ Standing Idle（掏鑰匙、被搶、手垂下都是右手 IK）
    → 轉回前方（Turn Left 90）→ 起步 → 走路。2026-10-13 使用者：面對面時新郎沒有轉身面向她 → 加兩段轉身"""
    X = P["X"]; end = json.load(open(B2_END))["groom"]
    tgt = STATE["tgt"]
    W, ST, ID, SW, TR, TL = (L._CL[n] for n in G_CLIPS)
    W, W1, a1, b1, wn, a0 = _walk_in(tgt, W, ST, end, half=P["g_half"])
    a4, b4, _ = F.match_phase(tgt, SW, range(SW["n"] - 30, SW["n"] - 9), W, range(0, wn))
    L1 = L1x + ((a1 + X - (a0 + L1x)) % wn)
    t_go = tm["go"] + P["go_lag"]
    W2 = mr.splice_clip(W, [(b4 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * 3)
    segs = [mr.Seg(W1, 0, L1, name="被拉著走（Walking）"),
            mr.Seg(ST, b1, P["stop_b"], name="停下（Stop Walking）")]
    if abs(turn) > 1.0:
        # 2026-10-13 使用者：轉身前微蹲、轉身時雙腳小碎步 → 不用 Mixamo 的 Turn Right／Left 90（整段運動員預備站姿，
        #   縮成 30° 左右的小轉身會兩腳一起離地亂動）；站著那段直接用轉好的面向，轉身由 build() 的 F.pivot_turn 補（先跨一步、另一腳跟上）
        segs += [mr.Seg(ID, 0, ID["n"] - 1, face=yaw0 + turn, name="轉身面向新娘（跨一步轉 %.0f°）→ 站著掏鑰匙、晃、被搶走（Standing Idle＋右手 IK）" % -turn)]
    else:
        segs += [mr.Seg(ID, 0, ID["n"] - 1, name="站著掏鑰匙、晃、被搶走（Standing Idle＋右手 IK）")]
    segs += [mr.Seg(SW, P["start_a"], a4 + X, face=90.0 + P["g_go_face"][0], at=t_go + HANDLES, name="轉回前方（跨一步）→ 起步（Start Walking）"),
             mr.Seg(W2, 0, int(2.5 * FPS), face=90.0 + P["g_go_face"][1], name="走路（Walking）")]
    STATE["g_cut"] = dict(b4=b4, wn=wn, a1=a1, b1=b1)
    return segs


def _contact_lock(tgt, poses, n):
    FM = _fm(); B0 = _b0(); pts = L.sole_points(STATE["arm"])
    poses, off = F.ground(tgt, poses, pts)
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9, z_on=0.015, gap_max=25)
    poses = B0._pin_foot_turn(tgt, poses, pts)
    poses = B0.zero_slide(tgt, poses, pts, 0, n - 1)
    return poses


def build(L1x_b=41, L1x_g=72):
    """兩人：排段 → 擺放（接 B2）→ 貼地鎖腳（整段：foot_lock＋腳掌朝向固定＋抵銷貼地點位移，B2 的做法）"""
    end = json.load(open(B2_END))
    segs_b, tm = plan_bride(L1x_b)
    seq_g0 = _place(STATE["tgt"], plan_groom(tm, L1x_g), end["groom"])     # 先算新郎幾秒停穩 → 動作從兩人都停穩起算
    i0 = int(round(seq_g0.T[1][0] * FPS)); hs = [seq_g0.at(i / FPS)[1] for i in range(i0, i0 + 120)]
    g_st = (i0 + next((j for j in range(len(hs) - 3) if (hs[j + 3] - hs[j]).length * 10 < 0.08), 0)) / FPS - HANDLES
    segs_b, tm = plan_bride(L1x_b, base=max(tm["bs"], g_st))
    with C.as_actor("bride"):
        seq_b = _place(STATE["tgt"], segs_b, end["bride"])
    t_go_g = tm["go"] + P["go_lag"]
    dur = tm["go"] + P["go_len"]
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    segs_g = plan_groom(tm, L1x_g)
    seq_g = _place(STATE["tgt"], segs_g, end["groom"])
    # 新娘轉身面向新郎：搖手指那段的面向＝停穩時她看向新郎的方向
    hb = seq_b.at(tm["bs"] + HANDLES)[1]; hg = seq_g.at(tm["bs"] + HANDLES + 0.5)[1]
    to_g = math.degrees(math.atan2((hg - hb).x, -(hg - hb).y))
    # face_off：比正對新郎再往鏡頭轉幾度（2026-10-13：正對新郎是 −124°，轉回 +X 要轉 214°、Turn 180 Left 只轉 174° → 漂向新郎 15 cm、兩人只剩 0.37 m）
    for sg in segs_b:                                     # 面向新郎那兩段（看他掏鑰匙、搖頭）
        if sg.name.startswith(("看他", "往左轉身", "搖頭")):
            sg.face = to_g + P["face_off"]
    # 新郎轉身面向新娘：停穩時看向新娘的方向和他當下面向的差 × g_face（身體轉大部分，臉再靠 Standing Idle 自己的轉頭）
    yaw_g = _yaw(STATE["tgt"], seq_g.at(g_st + HANDLES)[0])
    to_b = math.degrees(math.atan2((hb - hg).x, -(hb - hg).y))
    g_turn = ((to_b - yaw_g + 180) % 360 - 180) * P["g_face"] + P["g_extra"]   # g_extra：再往鏡頭多轉（兩人一前一後，正對她時鏡頭只看到側臉）
    segs_g = plan_groom(tm, L1x_g, g_turn, yaw_g)
    seq_g = _place(STATE["tgt"], segs_g, end["groom"])
    tm["g_turn"] = g_turn
    with C.as_actor("bride"):
        seq_b = _place(STATE["tgt"], segs_b, end["bride"])
        tgt = STATE["tgt"]
        pb = [(dict(R), h.copy()) for R, h in (seq_b.at(min(i / FPS, seq_b.start + seq_b.dur))[:2] for i in range(n))]
        if P["b_pivot"]:                                  # 往左轉身面向新郎（左腳先跨）、起步前往右轉回前方（左腳先跨、右腳最後跨直接接起步）；鎖腳前後各做一次（鎖腳會釘住要抬的腳）
            nb = int(round(P["b_pivot_s"] * FPS)); j1 = int(round((tm["turn1"] + HANDLES) * FPS)); j2 = int(round((tm["go"] + HANDLES) * FPS)) + P["X"]
            piv = lambda q: F.pivot_turn(tgt, F.pivot_turn(tgt, q, j1, j1 + nb, first="L", lift=P["pivot_lift"], sign=1), j2 - nb, j2, first="L", lift=P["pivot_lift"], sign=-1)   # 起步那支一開始就抬右腳 → 右腳最後跨，直接接起步
            pb = piv(pb)
        pb = _contact_lock(tgt, pb, n)
        if P["b_pivot"]:
            pb = piv(pb)
        pb, Z.STATE["head_up_max"] = F.level_head(tgt, pb)   # 2026-10-13 導演端（全片通用）：新娘走路頭往斜上方看 → 仰角超過 5° 壓回來
        pb = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in pb]
        if OUTFIT_B:                                      # 禮服：手垂下會沒入裙子 → 手臂往外擺、手肘微彎（搶鑰匙、搖手指之後由 IK 蓋掉）
            pb, Z.STATE["skirt_arms_deg"] = F.skirt_arms(tgt, pb, **SKIRT)
        STATE.update(poses=pb, seq=seq_b, segs=[(round(seq_b.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(segs_b)])
    tgt = STATE["tgt"]
    pg = [(dict(R), h.copy()) for R, h in (seq_g.at(min(i / FPS, seq_g.dur))[:2] for i in range(n))]
    if abs(g_turn) > 1.0:                                 # 轉身：站穩那格 → 轉好站穩那格之間，先跨轉向那側的腳、另一腳跟上
        X = P["X"]; T = seq_g.T; nt = int(round(P["pivot_s"] * FPS))
        i1 = int(round(T[2][0] * FPS)) - 2; i2 = int(round(T[3][0] * FPS)) + X
        if P["g_back"]:                                   # 站著那段整段往後（離新娘）g_back m：兩次轉身的跨步順便退一步、再走回來
            gb = seq_g.at(tm["bs"] + HANDLES)[1] - seq_b.at(tm["bs"] + HANDLES)[1]; gb.z = 0; gb = gb.normalized() * P["g_back"]
            for i in range(i1 + nt, i2 - nt + 1):
                pg[i] = (pg[i][0], pg[i][1] + gb)
        pg = F.pivot_turn(tgt, pg, i1, i1 + nt, first="R" if g_turn < 0 else "L", lift=P["pivot_lift"])
        pg = F.pivot_turn(tgt, pg, i2 - nt, i2, first="L" if g_turn < 0 else "R", lift=P["pivot_lift"])
        tm["pivot"] = ((i1 / FPS - HANDLES, (i1 + nt) / FPS - HANDLES), ((i2 - nt) / FPS - HANDLES, i2 / FPS - HANDLES))
    pg = _contact_lock(tgt, pg, n)
    pg = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in pg]
    i0 = int(round(seq_g.T[1][0] * FPS))
    still = next((i for i in range(i0, n - 3) if (pg[i + 3][1] - pg[i][1]).length * 10 < 0.08), i0)
    tm.update(g_still=still / FPS - HANDLES, g_go=t_go_g, end=dur, to_groom=to_g)
    STATE.update(poses=pg, seq=seq_g, dur=dur, b3_tm=tm, marks=dict(still=tm["g_still"], go=t_go_g, end=dur),
                 segs=[(round(seq_g.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(segs_g)])
    i_bs = int(round((tm["bs"] + HANDLES) * FPS)); i_e = int(round((dur + HANDLES) * FPS))
    return dict(dur=round(dur, 2), tm={k: round(v, 2) if isinstance(v, float) else v for k, v in tm.items()},
                bride_still=tuple(round(x, 2) for x in C.actor("bride")["poses"][i_bs][1].xy),
                groom_still=tuple(round(x, 2) for x in pg[i_bs][1].xy),
                bride_end_x=round(C.actor("bride")["poses"][i_e][1].x, 2),
                gap_still=round((C.actor("bride")["poses"][i_bs][1].xy - pg[i_bs][1].xy).length, 2))


# ════════ 手：放開手腕、掏鑰匙、搶鑰匙、搖手指 ════════
POINT = dict(curl={"Index": (0, 4, 4), "Middle": (85, 100, 60), "Ring": (88, 100, 60), "Little": (90, 100, 60), "Thumb": (25, 35, 30)},
             spread={"Index": 0, "Middle": 0, "Ring": -2, "Little": -4}, thumb_to="Middle2")   # 食指伸直、其餘握起（搖手指）


def _frame(tgt, R, h):
    """骨盆朝向的前方、右方（水平）"""
    q = R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()
    fw = q @ Vector((0, -1, 0)); fw.z = 0; fw.normalize()
    rt = Vector((fw.y, -fw.x, 0))                        # 面向 fw 時的右手方向（fw 順時針轉 90°：面向 +X 時右手在 −Y）
    return fw, rt


def _pinch(tgt, R, h, side):
    Hd = tgt.fk(R, h)
    return sum((tgt.tail(R, Hd, f"J_Bip_{side}_{f}3") for f in ("Thumb", "Index", "Middle")), Vector()) / 3


def _ik_pinch(tgt, R, h, side, goal, w, pole, gesture="hold"):
    """手指捏的點（拇指、食指、中指指尖中點）對到 goal：先手腕 IK，再照指尖差修手腕（B2 捏蛋糕的做法）"""
    if w <= 0:
        return R
    R0 = mr.gesture(tgt, R, side, gesture, w)
    Hd = tgt.fk(R0, h); w0 = Hd[f"J_Bip_{side}_Hand"]; wrist = w0 + (goal - _pinch(tgt, R0, h, side))
    for _ in range(3):
        R = mr.arm_ik(tgt, R0, h, side, w0.lerp(wrist, w), pole)
        wrist = wrist + (goal - _pinch(tgt, R, h, side)) * w
    return R


BS = "L"                                           # 2026-10-13 使用者：新娘用左手拉（她在前、新郎在她左後方；原本右手要橫過身體）


def pull_release(rb=0.465, rg=0.47, wrap=0.025, smooth=3):
    """開頭：新娘左手（BS）握新郎右手腕（接 B2 的拉手，同 b2_formal.pull_arms 的接觸點算法），tm["release"] 起 rel_s 秒內放開回原片手臂"""
    from zanim_hand import hand_quat, put_hand_pole
    tm = STATE["b3_tm"]; gst = STATE; bst = C.actor("bride"); tg, tb = gst["tgt"], bst["tgt"]; n = len(gst["poses"])
    i_end = min(n, int(round((tm["release"] + P["rel_s"] + HANDLES) * FPS)) + 1)
    raw = []
    for i in range(i_end):
        Hg = tg.fk(*gst["poses"][i]); Hb = tb.fk(*bst["poses"][i])
        c = Hg["J_Bip_R_Hand"].copy(); Sb = Hb[f"J_Bip_{BS}_UpperArm"]; Sg = Hg["J_Bip_R_UpperArm"]
        if (Sb - c).length > rb:
            c = Sb + (c - Sb).normalized() * rb
        if (c - Sg).length > rg:
            c = Sg + (c - Sg).normalized() * rg
        raw.append(c)
    Cs = [sum(raw[max(0, i - smooth):i + smooth + 1], Vector()) / len(raw[max(0, i - smooth):i + smooth + 1]) for i in range(i_end)]
    for i in range(i_end):
        t = i / FPS - HANDLES; w = 1.0 - _sm(t, tm["release"], tm["release"] + P["rel_s"])
        if w <= 0:
            continue
        c = Cs[i]
        Rg, hg = gst["poses"][i]; Hg = tg.fk(Rg, hg)
        Rg = mr.arm_ik(tg, Rg, hg, "R", Hg["J_Bip_R_Hand"].lerp(c, w), Vector((0, 0, -1)) + (Hg["J_Bip_R_UpperArm"] - Hg["J_Bip_C_Hips"]).normalized() * 0.3)
        Rb, hb = bst["poses"][i]; Hb = tb.fk(Rb, hb); Sb = Hb[f"J_Bip_{BS}_UpperArm"]
        d = (c - Sb); d.z = min(d.z, 0.0); d.normalize()
        palm = Vector((0, 0, -1)) - d * d.z; palm.normalize()
        q = hand_quat(tb, BS, d, palm)
        plen = 0.6 * (tb.rest_h[f"J_Bip_{BS}_Middle1"] - tb.rest_h[f"J_Bip_{BS}_Hand"]).length
        lift = Vector((0, 0, P["rel_lift"] * math.sin(math.pi * (1 - w)) / max(w, 0.25)))   # 放手後手往上帶（禮服：直線回身側會穿過裙子背面）
        M = Matrix.Translation(c - d * plen - palm * wrap + lift) @ q.to_matrix().to_4x4()
        Rb = put_hand_pole(tb, Rb, hb, BS, M, w, ((Sb - Hb["J_Bip_C_Hips"]).normalized() * 0.5 + Vector((0, 0, -1))).normalized(), 0.6)
        Rb = mr.gesture(tb, Rb, BS, "grip", w)
        gst["poses"][i] = (Rg, hg); bst["poses"][i] = (Rb, hb)
    return dict(release=round(tm["release"], 2))


def key_arms():
    """新郎右手：伸進右前褲袋（pocket）→ 捏著鑰匙圈舉到胸前（key_up）、小幅晃 → 被搶（grab）後停在半空 freeze 秒 → drop 秒內垂下。
    新娘左手：grab 前 0.4 秒伸過去捏住鑰匙圈 → 0.4 秒內收到胸前、一直拿著（走路也拿著）。
    新娘右手：wag 期間食指朝上、在臉旁左右搖（每秒約 3 下、±3.5 cm）。
    回傳鑰匙每格的位置（捏的點）與在誰手上"""
    tm = STATE["b3_tm"]; gst = STATE; bst = C.actor("bride"); tg, tb = gst["tgt"], bst["tgt"]; n = len(gst["poses"])
    pk0, pk1 = tm["pocket"]; up0, up1 = tm["key_up"]; gr = tm["grab"]; fz = gr + P["freeze"]; dr = fz + P["drop"]
    ix = lambda t: int(round((t + HANDLES) * FPS))
    Rp, hp = gst["poses"][ix(pk1)]; fwp, rtp = _frame(tg, Rp, hp)                 # 口袋：伸進去那一刻的身體
    pocket = hp + rtp * 0.12 + fwp * 0.04 + Vector((0, 0, -0.06))
    ib = ix(up1 + 0.1); Rg0, hg0 = gst["poses"][ib]                                # 舉到胸前：轉完身那一刻的身體（2026-10-13 新郎多轉 25°）
    fw0, rt0 = _frame(tg, Rg0, hg0)
    Hg0 = tg.fk(Rg0, hg0)
    to_b = (bst["poses"][ib][1] - hg0); to_b.z = 0; to_b.normalize()
    show = Hg0["J_Bip_C_UpperChest"] + (fw0 * 0.6 + to_b * 0.4).normalized() * P["show"][0] + rt0 * P["show"][1] + Vector((0, 0, P["show"][2]))
    key = [None] * n; owner = [None] * n; g_hand = [None] * n; last = show
    for i in range(n):
        t = i / FPS - HANDLES
        Rg, hg = gst["poses"][i]
        # ── 新郎右手 ──
        if pk0 - 0.1 < t < dr:
            if t < pk1:
                goal = pocket; w = _sm(t, pk0 - 0.1, pk0 + 0.2)
            elif t < up1:
                k = _sm(t, up0 - 0.15, up1); goal = pocket.lerp(show, k) + Vector((0, 0, 0.04 * math.sin(math.pi * k))); w = 1.0
            elif t < gr:
                jig = math.sin(2 * math.pi * P["jig_hz"] * (t - up1)) * min(1.0, (t - up1) / 0.2)
                goal = show + rt0 * P["jig_amp"][0] * jig + Vector((0, 0, P["jig_amp"][1] * abs(jig))); w = 1.0
            else:
                goal = last; w = 1.0 - _sm(t, fz, dr)                       # 被搶走：手停在最後那一格的位置（愣住），再垂下
            Rg = _ik_pinch(tg, Rg, hg, "R", goal, w, Vector((0.3, 0, -1)) + rt0 * 0.6)
            g_hand[i] = goal
            if t < gr:
                last = goal
        gst["poses"][i] = (Rg, hg)
        if pk1 - 0.1 <= t < gr:
            key[i] = _pinch(tg, Rg, hg, "R"); owner[i] = "groom"
    # ── 新娘 ──
    ig = int(round((gr + HANDLES) * FPS)); kg = key[ig - 1]
    for i in range(n):
        t = i / FPS - HANDLES
        Rb, hb = bst["poses"][i]
        if t > gr - 0.45:
            Hb = tb.fk(Rb, hb); fwb, rtb = _frame(tb, Rb, hb)
            chest = Hb["J_Bip_C_UpperChest"] + fwb * 0.17 - rtb * 0.05 + Vector((0, 0, -0.05))
            if t < gr:
                goal = kg; w = _sm(t, gr - 0.45, gr - 0.05)
            else:
                goal = kg.lerp(chest, _sm(t, gr + 0.05, gr + 0.45)); w = 1.0
            Rb = _ik_pinch(tb, Rb, hb, "L", goal, w, Vector((-0.3, 0, -1)) - rtb * 0.6, gesture="grip")
            if t >= gr:
                key[i] = _pinch(tb, Rb, hb, "L"); owner[i] = "bride"
        w0, w1 = tm["wag"]
        ww = _sm(t, w0 - 0.35, w0) * (1 - _sm(t, w1, w1 + 0.35))
        if ww > 0:
            from zanim_hand import hand_quat, put_hand_pole
            Hb = tb.fk(Rb, hb); fwb, rtb = _frame(tb, Rb, hb)
            sway = math.sin(2 * math.pi * 3.0 * (t - w0)) * min(1.0, max(0.0, (t - w0 + 0.1) / 0.25))
            wrist = Hb["J_Bip_C_Head"] + fwb * 0.20 + rtb * (0.13 + 0.035 * sway) + Vector((0, 0, -0.16))
            up = (Vector((0, 0, 1)) + rtb * 0.25 * sway).normalized()
            q = hand_quat(tb, "R", up, fwb)                    # 食指朝上、掌心朝前（對著新郎）
            Rb = put_hand_pole(tb, Rb, hb, "R", Matrix.Translation(wrist) @ q.to_matrix().to_4x4(), ww, (rtb - Vector((0, 0, 1))).normalized(), 0.6)
            Rb = mr.finger_pose(tb, Rb, "R", POINT["curl"], POINT["spread"], ww, POINT["thumb_to"])
        bst["poses"][i] = (Rb, hb)
    STATE["key"] = key; STATE["key_owner"] = owner
    return dict(pocket=tuple(round(x, 2) for x in pocket), show=tuple(round(x, 2) for x in show), grab_pt=tuple(round(x, 2) for x in kg))


# ════════ 道具、表情、場景、鏡頭、短片 ════════
KEY_RING = 0.063                                   # car_key 原點在底部、鑰匙圈中心離原點 0.063 m（圈在上、鑰匙往下垂）
KEY_FOB = 0.045                                    # 新娘握的是遙控器那段（離原點 0.045 m）
KEY_SCALE = 1.8                                    # 2026-10-13 使用者：鑰匙不明顯 → 放大 1.6 倍（原本 9 cm 長在畫面上只有幾個像素）


def key_track():
    """每格鑰匙的矩陣：新郎捏鑰匙圈（圈在指尖、鑰匙往下垂，晃的時候前後擺）；新娘握遙控器；口袋裡那段縮成 0"""
    out = []; tm = STATE["b3_tm"]; up1 = tm["key_up"][1]
    for i, (p, who) in enumerate(zip(STATE["key"], STATE["key_owner"])):
        t = i / FPS - HANDLES
        if p is None:
            out.append(None); continue
        if who == "groom":
            sw = math.radians(P["key_swing"]) * math.sin(2 * math.pi * P["jig_hz"] * (t - up1) - 0.6) * (1.0 if t > up1 else 0.3)
            M = Matrix.Translation(p) @ Matrix.Rotation(sw, 4, "X") @ Matrix.Scale(KEY_SCALE, 4) @ Matrix.Translation((0, 0, -KEY_RING))
        else:
            M = Matrix.Translation(p + Vector((0, 0, -KEY_FOB * KEY_SCALE))) @ Matrix.Scale(KEY_SCALE, 4)
        out.append(M)
    STATE["key_M"] = out
    return sum(1 for m in out if m is not None)


def _key_hook(i):
    ob = bpy.data.objects.get("ZA_CarKey"); Ms = STATE.get("key_M")
    if ob is None or not Ms:
        return
    M = Ms[min(i, len(Ms) - 1)]
    ob.matrix_world = M if M is not None else Matrix.Translation((0, 0, -5)) @ Matrix.Scale(0.0001, 4)


FACE_G = {"smug": dict(mouthSmileLeft=0.7, mouthSmileRight=0.7, browOuterUpLeft=0.4, browOuterUpRight=0.4, eyeSquintLeft=0.2, eyeSquintRight=0.2),
          "sad": dict(browInnerUp=0.9, mouthFrownLeft=0.6, mouthFrownRight=0.6, mouthPucker=0.3, eyeLookDownLeft=0.3, eyeLookDownRight=0.3)}


def face_vals(t):
    """新郎：開頭還在嚼（接 B2，臉頰鼓起慢慢消）→ 掏鑰匙晃的時候得意 → 被搶走愣住、失望；新娘：搶的時候瞪、搖手指"""
    tm = STATE["b3_tm"]; g = {}; b = {}
    m = 1 - _sm(t, tm["pocket"][0] - 0.6, tm["pocket"][0])
    g["jawOpen"] = m * 0.18 * (1 - math.cos(2 * math.pi * 2.2 * (t + 3.85))); g["cheekPuff"] = 0.6 * m
    ws = _sm(t, tm["key_up"][0], tm["key_up"][1]) * (1 - _sm(t, tm["grab"], tm["grab"] + 0.25))
    wd = _sm(t, tm["grab"] + P["freeze"] * 0.5, tm["grab"] + P["freeze"] + 0.3) * (1 - _sm(t, tm["go"], tm["go"] + 0.6))
    for k, v in FACE_G["smug"].items():
        g[k] = g.get(k, 0) + v * ws
    for k, v in FACE_G["sad"].items():
        g[k] = g.get(k, 0) + v * wd
    wb = _sm(t, tm["grab"] - 0.4, tm["grab"] - 0.1) * (1 - _sm(t, tm["wag"][1], tm["wag"][1] + 0.4))
    for k, v in _fm().FACE_GLARE.items():
        b[k] = v * 0.85 * wb
    return g, b


def _face_hook(i):
    g, b = face_vals(i / FPS - HANDLES)
    for arm, vals in ((STATE["arm"], g), (C.actor("bride")["arm"], b)):
        kb = L.head_mesh(arm).data.shape_keys.key_blocks
        for k, v in vals.items():
            if k in kb:
                kb[k].value = v


def bake_face():
    import zanim_sample as SP
    n = len(STATE["poses"]); V = [face_vals(i / FPS - HANDLES) for i in range(n)]
    for who, arm, j in (("groom", STATE["arm"], 0), ("bride", C.actor("bride")["arm"], 1)):
        key = L.head_mesh(arm).data.shape_keys
        ad = key.animation_data_create(); act = bpy.data.actions.get("SAMPLE_B3Face_" + who) or bpy.data.actions.new("SAMPLE_B3Face_" + who); ad.action = act
        for k in V[0][j].keys():
            if k in key.key_blocks:
                SP._put(act, key, 'key_blocks["%s"].value' % k, 0, [V[i][j][k] for i in range(n)])
    return True


OUTFIT_G = "groom-beige-3piece"
OUTFIT_B = "bride-blush-ballgown"                   # 2026-10-13 服裝端定案（outfit/bride_blush_ballgown@bride v1，裙寬 0.32 m）
PILLAR = dict(d=1.3, hw=0.33, slide=0.7)          # 換景柱子：離鏡頭 d m、半寬 hw（素材 pillar 底座 0.66 m）、最後 slide 秒從畫面右外滑到蓋住兩人中點
# 2026-10-13：新娘骨盆最遠 x 8.55（走廊盡頭裝飾柱在走線上）→ 起步後只剩 0.9 秒，鏡頭跟拍移動太少、靜止的柱子掃不過畫面 →
#   改成柱子自己滑進來（同場景端 B5→B6 的換景柱子做法）


def dress():
    return _b2().dress()


def scene_set():
    """走廊（venue_offset.json；2026-10-13 場景端：x 5.746 以後退到 y 1.9 的泊車凹處、立牌 (7.946, 1.62)；2026-10-13 使用者：立牌被兩人擋住 → 場景端移到 (6.95, 1.62)）＋車鑰匙；
    換景柱子（y＜−1 那根）由 pillar_track 算位置"""
    vo = json.load(open(BK.VENUE_OFFSET)); off = (vo["dx"], vo["dy"], 0.0)
    old = bpy.data.collections.get("ZP_Scene_VenueCorridor")
    if old is not None and old.name in Z.studio_col().children:
        objs = {o.name: o for o in old.all_objects}
    else:
        objs = BK.venue("Scene_VenueCorridor", off)
    STATE["sc"].view_layers[0].update()
    pil = [o for n_, o in objs.items() if n_.startswith("I_ZP_pillar") and o.matrix_world.translation.y < -1.0]
    STATE["pillar_obj"] = pil[0].name if pil else None
    if bpy.data.objects.get("ZA_CarKey") is None:
        BK.props_api()["place_prop"]("car_key", name="ZA_CarKey", parent=Z.studio_col())
    key_track()
    for hk in (_key_hook, _face_hook, _pillar_hook):
        if hk not in Z.POSE_HOOKS:
            Z.POSE_HOOKS.append(hk)
    return dict(offset=off, pillar=STATE["pillar_obj"], n_objs=len(objs))


CAM = dict(dist=3.6, bias=0.65)
# 2026-10-13 穿禮服：新娘停在新郎靠鏡頭側前方 0.8 m，3 m 跟拍時裙擺被切在畫面右緣、下緣 → 新郎停穩前慢慢拉遠到 dist m（開頭仍 3 m 接 B2），
#   跟拍點偏向新娘 bias（0.5＝中點）


def camera_fn():
    mk = STATE["marks"]; arm = STATE["arm"]; k_ = CAM["bias"] / 0.5

    def partner(i):                                       # follow_camera 剛 pose_at(i)：用擺出來的世界座標
        g = arm.matrix_world @ arm.pose.bones["J_Bip_C_Hips"].head; b = Vector(tuple(C.hips_world("bride")))
        return (g.x + (b.x - g.x) * k_, g.y + (b.y - g.y) * k_)
    near = BK.side_follow(holds=[(mk["still"], mk["go"])], handles=HANDLES, partner=partner)       # 開頭照 B2 的 3 m（接得上）
    far = BK.side_follow(holds=[(mk["still"], mk["go"])], handles=HANDLES, offset=(0.0, -CAM["dist"], 0.25), partner=partner)
    a, b = HANDLES * FPS, (mk["still"] + HANDLES) * FPS            # 鏡內 0 秒 → 新郎停穩：慢慢拉遠

    def f(i):
        k = max(0.0, min(1.0, (i - a) / max(1.0, b - a))); k = k * k * (3 - 2 * k)
        (l0, a0), (l1, a1) = near(i), far(i)
        return l0.lerp(l1, k), a0.lerp(a1, k)
    return f


def pillar_track():
    """換景柱子每格的位置：鏡頭往前 d m 那條線上，dur−slide 秒時在畫面右外，dur 秒時蓋住兩人中點"""
    cf = camera_fn(); n = len(STATE["poses"]); dur = STATE["dur"]; out = []
    gb = C.actor("bride")["poses"]
    for i in range(n):
        t = i / FPS - HANDLES
        l, a = cf(i); fwd = a - l; fwd.z = 0; fwd.normalize()
        right = Vector((fwd.y, -fwd.x, 0))
        mid = (STATE["poses"][i][1] + gb[i][1]) / 2; dm = mid - l; dm.z = 0
        s_mid = dm.dot(right) / max(1e-3, dm.dot(fwd)) * PILLAR["d"]
        s_out = BK.frame_w(PILLAR["d"]) / 2 + PILLAR["hw"] + 0.05
        k = _sm(t, dur - PILLAR["slide"], dur)
        p = l + fwd * PILLAR["d"] + right * (s_out + (s_mid - s_out) * k); p.z = 0
        out.append(p)
    STATE["pillar_P"] = out
    return tuple(round(x, 3) for x in out[int(round((dur + HANDLES) * FPS))])


def _pillar_hook(i):
    nm = STATE.get("pillar_obj"); Ps = STATE.get("pillar_P")
    if not nm or not Ps:
        return
    ob = bpy.data.objects.get(nm)
    if ob is not None:
        ob.location = Ps[min(i, len(Ps) - 1)]


def clip(v=1, size=(960, 540)):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", 35.0)
    for a in (STATE["arm"], C.actor("bride")["arm"]):
        a.animation_data_clear()
        hk = L.head_mesh(a).data.shape_keys
        if hk is not None:
            hk.animation_data_clear()
    objs = [o for o in (bpy.data.objects.get("ZA_CarKey"), bpy.data.objects.get(STATE.get("pillar_obj") or "")) if o]
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
    path = SP.save("b3_formal")
    cmd = SP.render_clip("b3_formal", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + "/formal_v%d.mp4" % v, size=size)
    return dict(out, path=path, cmd=cmd)


def close(t, views, out=None, res=480, lens=50, hide=None):
    return _fm().close(t, views, out=out or STATE["out_dir"] + "/formal_close", res=res, lens=lens, hide=hide)


def run():
    t0 = time.time(); r = {}
    if "bride" not in C.cast():
        setup()
    r["build"] = build(); r["pull"] = pull_release(); r["key"] = key_arms()
    n = len(STATE["poses"])
    if OUTFIT_B:                                          # IK（放開手腕、伸手搶鑰匙）的路徑會穿回裙子 → 再避一次；握著手腕、拿著鑰匙那幾段不動
        tm = STATE["b3_tm"]; ix = lambda t: int(round((t + HANDLES) * FPS))
        with C.as_actor("bride"):
            STATE["poses"], r["skirt_arms_2"] = F.skirt_arms(STATE["tgt"], STATE["poses"], skip=[(0, ix(tm["release"])), (ix(tm["grab"]), n)], **dict(SKIRT, smooth=2))
    for st in (STATE, C.actor("bride")):
        st["segs"] = [s for s in st["segs"] if s[0] * FPS < n - 2]   # 起步後的走路段超出片尾，stats 不算
    STATE["stats"] = Z.stats(); r["groom_stats"] = STATE["stats"]["summary"]
    with C.as_actor("bride"):
        STATE["stats"] = Z.stats(); r["bride_stats"] = STATE["stats"]["summary"]
    if not STATE.get("outfit_objs"):
        r["dress"] = dress()
    r["scene"] = scene_set(); r["pillar_end"] = pillar_track(); r["sec"] = round(time.time() - t0, 1)
    return r


def end_state(path=OUT_END):
    i = int(round((STATE["dur"] + HANDLES) * FPS))
    R, h = STATE["poses"][i]; bR, bh = C.actor("bride")["poses"][i]
    with C.as_actor("bride"):
        byaw = _yaw(STATE["tgt"], bR)
    d = dict(what="B3 正式版鏡內最後一格（換景柱子正好蓋住兩人中點；B4 開頭換成並肩）", t_end=round(STATE["dur"], 3),
             groom=dict(hips=[round(x, 3) for x in h], yaw=round(_yaw(STATE["tgt"], R), 2)),
             bride=dict(hips=[round(x, 3) for x in bh], yaw=round(byaw, 2), holding="左手握車鑰匙在胸前"),
             pillar=[round(x, 3) for x in STATE["pillar_P"][i]], camera=[[round(x, 3) for x in v] for v in camera_fn()(i)])
    json.dump(d, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return d
