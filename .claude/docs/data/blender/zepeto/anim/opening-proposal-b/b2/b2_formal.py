# B2 正式版（2026-10-13 導演端：等場景重排的空檔先做能做的）。經過甜點餐檯，新郎偷拿一塊小蛋糕塞進嘴裡，被走在前面的新娘回頭抓手腕拉走。
# 和走位版（b2_shot.py）的差別：
#   1. 開頭接 B1→B2 正式版最後一格（b1_b2/end_state_formal.json：新郎 (4.18, 0.07)、新娘 (3.98, 0.69)，兩人都在走路）；
#      走廊不再加 y 平移（B1→B2 已拉直，走線 y≈0.1，和 B0 一致）。
#   2. 新娘是真的身體（zanim_cast，v3）。B1→B2 結尾她在新郎左後方 → 新郎減速時她繼續走，自然超到前面（劇本：新娘一開始已走在前面）。
#   3. 餐檯靠牆（前緣 y≈1.05，2026-10-13 和導演端約定）：新郎減速時順勢往餐檯斜過去（停下那段的方向轉 approach 度），
#      停穩在 y≈0.5 → 左轉面向餐檯 → Picking Up 彎腰伸手拿（原地，往前約 0.55 m）。
#   4. 節奏照「以動作流暢為主」：停下播到停穩＋settle、拿完停一下才被拉、起步從靜止那格。
# 2026-10-13 場景端新座標：走廊牆退到 y 1.52；小蛋糕 (4.96, 1.15)、底部 z 0.616（托盤前排正中間）。
# 還沒做：手指捏蛋糕（碰到就停）、嘴嚼；新娘抓手腕的接觸（IK）。
# 用法（MCP）：
#   # BODY=groom,bride
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b2"); import b2_formal as B2F; print(B2F.run())
import bpy, os, sys, math, json, time
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
import zanim_fix as F
import zanim_cast as C
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE, PREFIX = "B2_FORMAL", "ZA_"
FPS = 30
HANDLES = 1.0
B12_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b1_b2/end_state_formal.json"
G_CLIPS = ("male_standard_walk", "male_stop_walk", "turn_left_90", "picking_up", "turn_right_90", "male_start_walk", "standing_idle")
P = dict(X=9, walk_s=0.0, stop_b=66, settle=0.3, wait=0.6, sneak_face=178.0, sneak_end=60, sneak_stop=45, tl=(0, 25), pick=(20, 75), after=1.25, pick_t=(0.75, 1.15, 1.75, 2.1), tr=(25, 45), start_a=10, go_len=2.6, go_face=(0.0, 0.0),
         fc=-10.0, piv1_s=1.2, piv2_s=0.9, pivot_lift=0.035, pu_hold=0.15, eat=(0.35, 0.3, 0.4), chew_s=0.5, held=1.35, drop=0.5)
# walk_s：鏡內第幾秒開始減速（0＝一開始就減速，導演端選的那版）；wait：停穩後等幾秒（新娘從他和餐檯之間超過去）；
# sneak_*：轉向餐檯走兩小步（Start Walking 播到第 sneak_end 格附近、接 Stop Walking 第 sneak_stop 格附近，面向 sneak_face 度）。
#   2026-10-13 試過：減速時就往餐檯斜 → 新郎擋到新娘的路；只在停下後半段轉彎 → 幾乎不移動、還是搆不到靠牆的餐檯；
# tl：Turn Left 90 取的格子（面向餐檯，約轉 60°；結尾多播 9 格給下一段漸變）；pick：Picking Up 取的格子（彎腰伸手拿起、捧到胸前）；
# 2026-10-13 導演端第 5 輪：拿起蛋糕後轉身面向鏡頭再吃、被拉走後蛋糕掉地上 →
#   fc：吃蛋糕時面向（0＝正對鏡頭，負＝往畫面左偏）；piv1_s／piv2_s：轉向鏡頭（往左轉約 170°）、被抓包轉向新娘（往左轉約 100°）幾秒（F.pivot_turn 跨步轉身）；
#   pu_hold：拿起後停幾秒才轉；eat：(轉完幾秒送到嘴, 咬住停幾秒, 放回胸前幾秒)；chew_s：放回胸前後嚼幾秒才被抓包轉身；
#   held：轉向新娘、被抓住手腕後幾秒起步；drop：起步後幾秒蛋糕從左手掉到地上
# after：拿完停幾秒才被拉（第 5 輪起不用）（停穩到起步要 ≥ 4 秒，字卡才看得完）；tr：Turn Right 90 取的格子（被拉回頭）；go_len：起步後幾秒結束（回到正常走路速度）


def setup():
    m = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b2")[1]
    Z.load_clips(G_CLIPS)
    return m


def _yaw(tgt, R):
    v = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0))
    return math.degrees(math.atan2(v.x, -v.y))


def plan_groom():
    tgt = STATE["tgt"]; X = P["X"]; end = json.load(open(B12_END))["groom"]
    W, ST, TL, PU, TR, SW, _ID = (L._CL[n] for n in G_CLIPS)
    wn = W["n"] - 1
    a0 = int(round(end["walk_phase"] - HANDLES * FPS)) % wn          # B1→B2 最後一格的相位往前推 1 秒（頭多做的）
    a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
    a4, b4, _ = F.match_phase(tgt, SW, range(SW["n"] - 30, SW["n"] - 9), W, range(0, wn))
    want = int(round((HANDLES + P["walk_s"]) * FPS))
    L1 = want + ((a1 + X - (a0 + want)) % wn)
    W1 = mr.splice_clip(W, [(a0 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * (L1 // wn + 2))
    W2 = mr.splice_clip(W, [(b4 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * 4)
    # 走兩小步到餐檯前：Start Walking 從靜止那格起播到 sneak_end 附近，接 Stop Walking 後段（配對腿的姿勢）
    a5, b5, _ = F.match_phase(tgt, SW, range(P["sneak_end"] - 3, P["sneak_end"] + 4), ST, range(P["sneak_stop"] - 6, P["sneak_stop"] + 7))
    STATE["walk_cut"] = dict(a0=a0, a1=a1, b1=b1, a4=a4, b4=b4, L1=L1, a5=a5, b5=b5)
    segs = [mr.Seg(W1, 0, L1, name="接 B1→B2 的走路（Walking）"),
            mr.Seg(ST, b1, P["stop_b"], hold=P["wait"], name="減速停穩，等新娘先走過去（Stop Walking）"),
            mr.Seg(SW, P["start_a"], a5 + X, face=P["sneak_face"], name="轉向餐檯、偷偷走兩小步（Start Walking 前段）"),
            mr.Seg(ST, b5, P["stop_b"], hold=P["settle"], name="在餐檯前停住（Stop Walking 後段）"),
            mr.Seg(PU, P["pick"][0], P["pick"][1], hold=P["pu_hold"], name="彎腰伸手拿蛋糕、捧到胸前（Picking Up）"),
            _idle(P["piv1_s"] + sum(P["eat"]) + P["chew_s"], P["fc"], "轉身面向鏡頭（往左跨步轉）、咬一口蛋糕、嚼（Standing Idle＋左手 IK）"),
            _idle(P["piv2_s"] + P["held"], 90.0, "被抓包：轉向新娘（往左跨步轉）、被抓住手腕（Standing Idle）"),
            mr.Seg(SW, P["start_a"], a4 + X, face=90.0 + P["go_face"][0], name="被拉著起步（Start Walking，從靜止那格）"),
            mr.Seg(W2, 0, int(3.5 * FPS), face=90.0 + P["go_face"][1], name="走路（Walking）")]
    return segs


def _idle(sec, face, name):
    ID = L._CL["standing_idle"]; nf = int(round(sec * FPS)) + P["X"]; b = min(ID["n"] - 1, nf)
    return mr.Seg(ID, 0, b, hold=max(0.0, (nf - b) / FPS), face=face, name=name)


def _pivots(tgt, poses, T):
    """兩次跨步轉身（同 B3）：拿完 → 面向鏡頭（往左轉）、嚼完 → 面向新娘（往左轉）"""
    n1 = int(round(P["piv1_s"] * FPS)); n2 = int(round(P["piv2_s"] * FPS))
    i1 = int(round(T[5][0] * FPS)) - 2; i2 = int(round(T[6][0] * FPS)) - 2
    poses = F.pivot_turn(tgt, poses, i1, i1 + n1, first="L", lift=P["pivot_lift"], sign=1)
    poses = F.pivot_turn(tgt, poses, i2, i2 + n2, first="L", lift=P["pivot_lift"], sign=1)
    return poses, (i1, i1 + n1, i2, i2 + n2)


def build_groom():
    tgt = STATE["tgt"]; end = json.load(open(B12_END))["groom"]
    segs = plan_groom()
    seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS)
    # 第 HANDLES 秒（＝B1→B2 最後一格）骨盆位置、面向要對上。停下那段有 face（往餐檯斜），place 的時間要在它之前 → 擺在第 0 格、反覆修正
    want = Vector((end["hips"][0], end["hips"][1])); xy = Vector((want.x - 0.7, want.y)); yaw = end["yaw"]
    for _ in range(5):
        seq.place(0.0, tuple(xy), yaw)
        R, h, _y = seq.at(HANDLES)
        yaw += end["yaw"] - _yaw(tgt, R); xy += want - h.xy
    seq.place(0.0, tuple(xy), yaw)
    T = seq.T
    t_go = T[7][0]; dur = t_go + P["go_len"] - HANDLES
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    poses = [(dict(R), h.copy()) for R, h in (seq.at(min(i / FPS, seq.dur))[:2] for i in range(n))]
    pts = L.sole_points(STATE["arm"])
    poses, off = F.ground(tgt, poses, pts)
    B0 = _b0()
    poses, piv = _pivots(tgt, poses, T)                   # 鎖腳前後各做一次（鎖腳會釘住要抬的腳）
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9, z_on=0.015, gap_max=25)
    # 2026-10-13：偷偷走兩小步那段滑 9.5 mm。分段放寬門檻再鎖（B0 的 lock_win）在窗口交界會跳 7 cm（停著的段落接不回原片）
    #   → 整段：踩地時腳掌朝向固定＋抵銷貼地點的位移（B0 的 _pin_foot_turn、zero_slide），沒有交界
    poses = B0._pin_foot_turn(tgt, poses, pts)
    poses = B0.zero_slide(tgt, poses, pts, 0, len(poses) - 1)
    poses, piv = _pivots(tgt, poses, T)
    poses = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in poses]
    tt = dict(table=T[3][0], pick=T[4][0], p1=(piv[0] / FPS, piv[1] / FPS), p2=(piv[2] / FPS, piv[3] / FPS), go=t_go)
    STATE["T_pick"] = (T[4][0], T[5][0])
    poses = _cake_arms(tgt, poses, tt)
    i0 = int(round(T[1][0] * FPS))
    still = next(i for i in range(i0, n - 3) if (poses[i + 3][1] - poses[i][1]).length * 10 < 0.08)
    marks = dict(stop=T[1][0] - HANDLES, still=still / FPS - HANDLES, sneak=T[2][0] - HANDLES, at_table=T[3][0] - HANDLES,
                 pick=T[4][0] - HANDLES, face_cam=tt["p1"][0] - HANDLES, back=tt["p2"][0] - HANDLES, caught=tt["p2"][1] - HANDLES, go=t_go - HANDLES, end=dur)
    STATE.update(poses=poses, seq=seq, dur=dur, marks=marks, segs=[(round(T[k][0], 2), round(s.dur, 2), s.name) for k, s in enumerate(segs)])
    STATE["stats"] = Z.stats()
    hs = poses[still][1]
    return dict(dur=round(dur, 2), marks={k: round(v, 2) for k, v in marks.items()}, still_xy=(round(hs.x, 2), round(hs.y, 2)),
                still_yaw=round(_yaw(tgt, poses[still][0]), 1), stats=STATE["stats"]["summary"],
                segs=[(round(t - HANDLES, 2), d, nm) for t, d, nm in STATE["segs"]])


CAKE = Vector((4.96, 1.15, 0.616))                # 場景端 2026-10-13：新郎拿的那塊（底部中心）
CAKE_SCALE = 1.6                                   # 2026-10-13 導演端：5 cm 的小蛋糕落地後在全景只有幾個像素 → 新郎拿的那塊放大 1.6 倍（原點在底部中心，放大後底部不動）
CAKE_H = 0.045 * CAKE_SCALE                        # 小蛋糕高度（抓的位置在中間）
ARM_R = ("J_Bip_R_UpperArm", "J_Bip_R_LowerArm", "J_Bip_R_Hand")


def _w(t, a, b, c, d):
    if t <= a or t >= d:
        return 0.0
    x = (t - a) / (b - a) if t < b else ((d - t) / (d - c) if t > c else 1.0)
    return x * x * (3 - 2 * x)


def mouth_pt(tgt, R, Hd):
    """蛋糕中心碰到嘴唇的位置：頭骨往臉的前方 MOUTH[0] m、往上 MOUTH[1] m。
    2026-10-13 量：jawOpen 會動的頂點中心在頭骨正前方、高度差 1 mm，最前緣 0.143 m；臉在嘴的高度最前 0.144～0.155 m
    （走位版的 0.12 m、往上 0.05 m 在臉裡面 → 手陷進頭 2.5 cm）"""
    fw = _head_fw(tgt, R)
    return Hd["J_Bip_C_Head"] + fw * MOUTH[0] + Vector((0, 0, MOUTH[1]))


MOUTH = (0.168 + 0.015, -0.005)                   # 蛋糕放大後半徑多 1.5 cm：中心再往前，蛋糕邊才剛好碰到嘴唇


def _head_fw(tgt, R):
    fw = (R["J_Bip_C_Head"] @ tgt.rest_q["J_Bip_C_Head"].inverted()) @ Vector((0, -1, 0)); fw.z = 0
    return fw.normalized()


def pinch_pt(tgt, R, h, side="L"):
    """捏的點：拇指、食指、中指指尖的中點"""
    Hd = tgt.fk(R, h)
    return sum((tgt.tail(R, Hd, f"J_Bip_{side}_{f}3") for f in ("Thumb", "Index", "Middle")), Vector()) / 3


def hold_pt(tgt, R, Hd):
    """拿著蛋糕在胸前的位置：嘴前再往前 HOLD[0] m、往下 HOLD[1] m、往左手那側 HOLD[2] m"""
    fw = _head_fw(tgt, R); lf = Vector((-fw.y, fw.x, 0))           # 面向逆時針 90° ＝ 左邊
    return mouth_pt(tgt, R, Hd) + fw * HOLD[0] + Vector((0, 0, -HOLD[1])) + lf * HOLD[2]


HOLD = (0.08, 0.26, 0.06)


def cake_goal(tgt, R, Hd, t, ct):
    """t 秒（含 HANDLES）左手捏的點：餐檯上 → 胸前 → 嘴前（咬一口）→ 胸前（嚼、被抓包、被拉走）。回傳 (點, 手腕朝向內插 k)"""
    grab = CAKE + Vector((0, 0, CAKE_H / 2))
    hp = hold_pt(tgt, R, Hd); mp = mouth_pt(tgt, R, Hd)
    if t < ct["lift"]:
        return grab, 0.0
    k = _sm(t, ct["lift"], ct["lift"] + 0.6)
    if t < ct["lift"] + 0.6:
        return grab.lerp(hp, k), k
    if t < ct["to_mouth"]:
        return hp, 1.0
    if t < ct["mouth"]:
        return hp.lerp(mp, _sm(t, ct["to_mouth"], ct["mouth"])), 1.0
    if t < ct["bite_end"]:
        return mp, 1.0
    return mp.lerp(hp, _sm(t, ct["bite_end"], ct["back_hold"])), 1.0


def _cake_arms(tgt, poses, tt):
    """tt（格子秒數）：table 走到餐檯前、pick 開始彎腰拿、p1 轉向鏡頭 (起, 迄)、p2 轉向新娘 (起, 迄)、go 起步。
    左手：IK 到小蛋糕（拿起）→ 胸前 → 轉向鏡頭後送到嘴前咬一口 → 放回胸前拿著（嚼、被抓包、被拉走）→ 起步後 drop 秒鬆手（蛋糕掉地上）回原片；
    右手：停在走到餐檯前那一格的手臂（自然垂下），被抓手腕時交給 pull_arms"""
    pk = P["pick_t"]; t_pick = tt["pick"]
    e = P["eat"]
    ct = dict(reach=t_pick + pk[0], lift=t_pick + pk[1])
    ct["to_mouth"] = tt["p1"][1] + 0.05; ct["mouth"] = tt["p1"][1] + e[0]; ct["bite_end"] = ct["mouth"] + e[1]
    ct["back_hold"] = ct["bite_end"] + e[2]; ct["drop"] = tt["go"] + P["drop"]
    t_grab = tt["p2"][1]
    iref = int(round(tt["table"] * FPS)) + 6; Rref = poses[iref][0]
    out = []
    for i, (R, h) in enumerate(poses):
        t = i / FPS
        wr = _w(t, t_pick - 0.2, t_pick + 0.2, t_grab - 0.4, t_grab + 0.1)
        if wr > 0:
            R = dict(R)
            for b in ARM_R:
                R[b] = R[b].slerp(Rref[b], wr)
        wl = _w(t, ct["reach"] - 0.45, ct["reach"], ct["drop"], ct["drop"] + 0.45)
        if wl > 0:
            Hd = tgt.fk(R, h)
            goal, k = cake_goal(tgt, R, Hd, t, ct)
            # 手腕：在餐檯上掌心朝下捏（蛋糕上方 3.5 cm）→ 拿起後在蛋糕前方 6.5 cm、低 1.5 cm（指尖朝嘴）
            wrist = goal + Vector((0, 0, 0.035)).lerp(_head_fw(tgt, R) * 0.065 + Vector((0, 0, -0.015)), k)
            w0 = Hd["J_Bip_L_Hand"]
            g = wl if t < ct["drop"] else 1.0 - _sm(t, ct["drop"], ct["drop"] + 0.12)     # 鬆手：手指先打開
            R0 = mr.gesture(tgt, R, "L", "hold", g)
            for _ in range(3):                             # 2026-10-13 近照：只對手腕，捏的點（指尖）差 8～10 cm → 照指尖再修手腕
                R = mr.arm_ik(tgt, R0, h, "L", w0.lerp(wrist, wl), Vector((0.5, 0, -1)))
                pp = pinch_pt(tgt, R, h)
                wrist = wrist + (goal - pp)
        out.append((R, h))
    STATE["cake_t"] = {k: v - HANDLES for k, v in ct.items()}
    return out


def heading(key=None, step=15):
    st = C.actor(key) if key else STATE
    tgt = st["tgt"]
    return [(round(i / FPS - HANDLES, 2), round(_yaw(tgt, R), 1), round(h.x, 2), round(h.y, 2)) for i, (R, h) in enumerate(st["poses"]) if i % step == 0]


def cleanup():
    return Z.cleanup(SCENE)


# ════════ 新娘（zanim_cast：v3 身體） ════════
# 劇本（b2.md）：新娘走在前面，發現新郎沒跟上 → 停下、回頭瞪 → 伸右手抓新郎右手腕 → 轉回前方拖著他往右走。
# 2026-10-13 做法：不往回走（她停的位置就在新郎拿蛋糕處右邊 PB["gap"] m）。兩次轉身都臉朝鏡頭：
#   回頭＝Turn 180 Left 鏡射成往右轉（經過面向鏡頭），轉回來＝Turn 180 Left 原樣（也經過面向鏡頭）；
#   等他拿蛋糕那段用 Angry Gesture 當身體＋IK 插腰（同 B1→B2）。
B_CLIPS = ("female_walk", "female_stop_walk", "turn_180_left", "angry_gesture", "female_start_walk")
PB = dict(gap=0.55, side=-0.55, react=0.25, reach=0.45, grab_dt=0.6, turn2=-0.05, lead=0.25, seam=1, ag_ramp=0.35, stop_bend=-65.0, sw_k=True,
          lock=dict(v_on=0.3, ramp=9, z_on=0.015, gap_max=25), win_v=2.0, win_z=0.03, bend=12.0,
          skirt=dict(margin=0.015, elbow_k=2.0, max_deg=40), approach=(18, 24), ap_lead=0.15, go_face=(0.0, 0.0), g_pre=0.3)
PB.update(grab_dt=0.25, turn2=0.6, ag_max=40)       # ag_max：Angry Gesture 最多播到第幾格、之後停住（第 5 輪等比較久，播到後段她會轉頭看畫面右邊、背對新郎）                  # 2026-10-13 第 5 輪：grab_dt 改成新郎轉向她轉完後幾秒抓到；turn2 改成抓到後幾秒她轉回前方
# 2026-10-13 穿禮服（裙擺半徑 0.335）：停在新郎右前方 0.35～0.45 m 會整段撞到他 → stop_bend −65、side −0.55（多走一圈、停在他右前方約 1.1 m、偏鏡頭側），
#   回頭插腰瞪他之後插著腰「往回走兩小步」（分鏡原本就這樣寫；approach＝起步、停下兩支的剪接格，走約 0.54 m）再抓手腕；
#   grab_dt 0.15 → 0.6、新郎 after 0.8 → 1.25、react 0.35 → 0.25：多出走兩步的時間（新郎多嚼一下才被拉走）；
#   g_pre：抓到前幾秒新郎手腕就開始被帶向接觸點；
#   ap_lead：走完那一格比開始伸手晚幾秒（邊停邊伸手）；go_face：(起步, 走路) 面向偏幾度（負＝斜向鏡頭側，拉著走時離他的腳遠一點）
# stop_bend：停下那段往右（鏡頭側）偏幾度（2026-10-13：不偏的話她停在新郎拿蛋糕處右邊 0.40 m，禮服裙擺會碰到）；
# gap：她停穩時骨盆離新郎拿蛋糕那格的骨盆幾 m（往 +X；禮服裙擺半徑 0.32＋新郎腳 0.12 → ≥ 0.44）；side：再往 y 偏幾 m；
# react：她停穩後幾秒回頭；reach：抓手腕前幾秒開始伸手；grab_dt：新郎蛋糕送到嘴後幾秒抓到；
# turn2：新郎被拉回頭（back）前後幾秒她開始轉回前方；lead：比新郎早幾秒起步（她在前面拉）；bend：伸手時上身往前彎幾度


def _fm():
    p = os.path.abspath(os.path.join(HERE, "..", "b1_b2"))
    if p not in sys.path:
        sys.path.insert(0, p)
    import b1b2_formal as FM
    return FM


def _b0():
    p = os.path.abspath(os.path.join(HERE, "..", "b0"))
    if p not in sys.path:
        sys.path.insert(0, p)
    import b0_formal as B0
    return B0


def add_bride():
    m = C.add_actor("bride", "bride")
    with C.as_actor("bride"):
        Z.load_clips(B_CLIPS)
    return m


def _bride_segs(L1x):
    """L1x：走路多走幾格（調停下的位置）。回傳 segs、時間節點（鏡內秒）"""
    FM = _fm(); X = P["X"]; mk = STATE["marks"]; ct = STATE["cake_t"]; end = json.load(open(B12_END))["bride"]
    with C.as_actor("bride"):
        tgt = STATE["tgt"]
        W, ST, TT, AG, SW = (L._CL[n] for n in B_CLIPS)
        W = FM._retime(W, end["walk_k"]); wn = W["n"] - 1
        if PB["sw_k"]:                                     # 起步也放慢（女生起步比新郎快：不放慢的話拉著走時越拉越遠，手搆不到）
            SW = FM._retime(SW, end["walk_k"] if PB["sw_k"] is True else PB["sw_k"])
        TR = dict(mr.mirror_clip(TT, tgt), name="turn_180_right")
        a0 = int(round(end["walk_phase"] - HANDLES * FPS)) % wn
        a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 12))
        a4, b4, _ = F.match_phase(tgt, SW, range(SW["n"] - 25, SW["n"] - 6), W, range(0, wn))
        if PB["stop_bend"]:                                # 停下時順勢往鏡頭側偏（走路一圈 0.95 m，停的位置只能整圈挑 → 拉開和新郎的距離靠這個）
            ST = F.bend(ST, PB["stop_bend"], b1, b1 + 20)
        L1 = L1x + ((a1 + X - (a0 + L1x)) % wn)
        sx = PB["seam"] / FPS; cyc = wn / FPS
        W1 = mr.splice_clip(W, [(a0 / FPS, cyc)] + [(0, cyc, sx)] * (L1 // wn + 2))
        W2 = mr.splice_clip(W, [(b4 / FPS, cyc)] + [(0, cyc, sx)] * 4)
        st_i = FM._still(ST, b1 + 10)
        t_still = (L1 - X + (st_i - b1)) / FPS - HANDLES
        t_turn1 = t_still + PB["react"]
        t_grab = mk["caught"] + PB["grab_dt"]              # 第 5 輪：新郎轉向她（被抓包）轉完就抓
        t_turn2 = t_grab + PB["turn2"]
        t_go = mk["go"] - PB["lead"]
        t_ag = t_turn1 + (TT["n"] - 1 - X) / FPS
        ap = PB["approach"]
        if ap:                                             # 往回走兩小步（分鏡）：Female Start Walking 3→a 接 Female Stop Walking b→結尾，約 0.54 m
            SWa, STa = L._CL["female_start_walk"], L._CL["female_stop_walk"]
            d_ap = ((ap[0] - 3) + (STa["n"] - 1 - ap[1])) / FPS
            t_ap = t_grab - PB["reach"] + PB["ap_lead"] - d_ap
            ag_b = min(AG["n"] - 1, max(X + 1, int(round((t_ap - t_ag) * FPS)) + X))
        else:
            ag_b = min(AG["n"] - 1, int(round((t_turn2 - t_ag) * FPS)) + X)
        segs = [mr.Seg(W1, 0, L1, name="新娘走路（Female Walk）"),
                mr.Seg(ST, b1, ST["n"] - 1, name="停下（Female Stop Walking）"),
                mr.Seg(TR, 0, TR["n"] - 1, at=t_turn1 + HANDLES, name="回頭（Turn 180 Left 鏡射成右轉，經過面向鏡頭）"),
                mr.Seg(AG, 0, min(ag_b, PB["ag_max"]), hold=max(0, ag_b - PB["ag_max"]) / FPS, name="插腰瞪他（Angry Gesture 當身體）")]
        if ap:
            segs += [mr.Seg(SWa, 3, ap[0] + X, at=t_ap + HANDLES, name="插著腰往回走兩小步（Female Start Walking）"),
                     mr.Seg(STa, ap[1], STa["n"] - 1, name="停在他面前、伸手抓手腕（Female Stop Walking）")]
        segs += [mr.Seg(TT, 0, TT["n"] - 1, at=t_turn2 + HANDLES, name="抓著手腕轉回前方（Turn 180 Left）"),
                mr.Seg(SW, 3, a4 + X, face=90.0 + PB["go_face"][0], at=t_go + HANDLES, name="拉著他起步（Female Start Walking）"),
                mr.Seg(W2, 0, int(3.0 * FPS), face=90.0 + PB["go_face"][1], name="走路（Female Walk）")]
        tm = dict(still=t_still, turn1=t_turn1, ag=t_ag, reach=t_grab - PB["reach"], grab=t_grab, turn2=t_turn2, go=t_go, b4=b4, wn=wn)
        if ap:
            tm["approach"] = t_ap
        return segs, tm


def build_bride():
    """擺放：第 HANDLES 秒（＝B1→B2 最後一格）骨盆、面向對上 end_state；走路長度挑「停穩位置最接近 新郎拿蛋糕骨盆＋(gap, side)」"""
    FM = _fm(); end = json.load(open(B12_END))["bride"]; n = len(STATE["poses"])
    gi = int(round((STATE["marks"]["pick"] + HANDLES) * FPS)); gp = STATE["poses"][gi][1]
    goal = Vector((gp.x + PB["gap"], gp.y + PB["side"]))
    want = Vector(end["hips"][:2])

    def make(L1x):
        segs, tm = _bride_segs(L1x)
        with C.as_actor("bride"):
            tgt = STATE["tgt"]; xy = Vector((want.x - 0.6, want.y)); yaw = end["yaw"]
            for _ in range(5):
                seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS); seq.place(0.0, tuple(xy), yaw)
                R, h, _y = seq.at(HANDLES)
                yaw += end["yaw"] - _yaw(tgt, R); xy += want - h.xy
            seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS); seq.place(0.0, tuple(xy), yaw)
            hs = seq.at(tm["still"] + HANDLES)[1]
        return segs, tm, seq, hs

    best = None
    for L1x in range(30, 130, 2):
        segs, tm, seq, hs = make(L1x)
        if tm["turn1"] > STATE["marks"]["pick"] - 0.2:
            break
        e = (hs.xy - goal).length
        if best is None or e < best[0]:
            best = (e, L1x)
    segs, tm, seq, hs = make(best[1])
    with C.as_actor("bride"):
        tgt = STATE["tgt"]
        poses = [seq.at(min(i / FPS, seq.start + seq.dur))[:2] for i in range(n)]
        pts = L.sole_points(STATE["arm"])
        poses, off = F.ground(tgt, poses, pts)
        # 同 B0 新娘（b0_formal.build_bride）：先壓掉兩腳同時離地 → 全段鎖腳 → 轉身、起步那幾格放寬門檻再鎖＋腳掌朝向固定＋抵銷貼地點位移
        # 2026-10-13 試過：轉身那幾格放寬門檻（v 2.0、z 0.03）→ 兩腳離地 35 mm；分段再鎖 → 交界跳 14 cm。
        #   → 整段照一般門檻鎖，再整段固定踩地的腳掌朝向＋抵銷貼地點位移（B0 的 _pin_foot_turn、zero_slide）：最多 0.5 mm
        B0 = _b0(); hop = None
        poses, _li = F.foot_lock(tgt, poses, pts, **PB["lock"])
        poses = B0._pin_foot_turn(tgt, poses, pts)
        poses = B0.zero_slide(tgt, poses, pts, 0, n - 1)
        poses, tm_head = F.level_head(tgt, poses)         # 2026-10-13 導演端（使用者）：新娘走路頭往斜上方看 → 仰角超過 5° 壓回來
        poses = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in poses]
        if OUTFIT_B:                                      # 禮服：手垂下會沒入裙子 → 手臂往外擺、手肘微彎（插腰、抓手腕那幾段之後由 IK 蓋掉）
            poses, Z.STATE["skirt_arms_deg"] = F.skirt_arms(tgt, poses, **PB["skirt"])
        tm["ag_end"] = tm["reach"]; tm["head_up_max"] = tm_head
        STATE.update(poses=poses, seq=seq, b_tm=tm, segs=[(round(seq.T[i][0], 2), round(sg.dur, 2), sg.name) for i, sg in enumerate(segs)])
    return dict(L1x=best[1], err=round(best[0], 3), still_xy=(round(hs.x, 2), round(hs.y, 2)), goal=(round(goal.x, 2), round(goal.y, 2)),
                tm={k: round(v, 2) for k, v in tm.items()}, hop_mm=hop, segs=[(round(t - HANDLES, 2), d, nm) for t, d, nm in C.actor("bride")["segs"]])


def _sm(t, a, b):
    x = 0.0 if t <= a else (1.0 if t >= b else (t - a) / (b - a))
    return x * x * (3 - 2 * x)


BS = "L"                                           # 2026-10-13 使用者：新娘用左手拉（她在前、新郎在她左後方；原本右手要橫過身體）


def pull_arms(rb=0.465, rg=0.47, wrap=0.025, smooth=3, turn_s=1.1, r_min=0.32):
    """抓手腕、拉著走（互動接觸：新娘左手（BS）握新郎右手腕，拉的方向朝 +X）。
    接觸點 C（新郎右手腕）：先照新郎原本的手腕；她的肩膀搆不到（> rb）就把 C 沿著連線往她那邊拉（新郎手臂被提起來、拉直）；
    兩人離太遠、新郎也搆不到（> rg）時 C 往新郎那邊退（記錄脫開的距離）。前後 smooth 格平均，免得一格一格抖。
    新娘：t_reach 起左手漸漸伸向 C，t_grab 握住（手腕 IK 到 C 往她肩膀退 wrap、手指 grip）；新郎：t_grab 起右手腕跟著 C"""
    from zanim_hand import hand_quat, put_hand_pole
    tm = STATE["b_tm"]; gst = STATE; bst = C.actor("bride")
    tg, tb = gst["tgt"], bst["tgt"]; n = len(gst["poses"])
    i_reach = int(round((tm["reach"] + HANDLES) * FPS)); i_grab = int(round((tm["grab"] + HANDLES) * FPS))
    raw = []; info = dict(gap_max_mm=0.0, lift_max_mm=0.0)
    for i in range(n):
        if i < i_reach:
            raw.append(None); continue
        Rg, hg = gst["poses"][i]; Rb, hb = bst["poses"][i]
        Hg = tg.fk(Rg, hg); Hb = tb.fk(Rb, hb)
        Wg = Hg["J_Bip_R_Hand"]; Sb = Hb[f"J_Bip_{BS}_UpperArm"]; Sg = Hg["J_Bip_R_UpperArm"]
        c = Wg.copy()
        if (Sb - c).length > rb:
            c = Sb + (c - Sb).normalized() * rb
            info["lift_max_mm"] = max(info["lift_max_mm"], round(1000 * (c - Wg).length, 1))
        if (c - Sg).length > rg:
            c2 = Sg + (c - Sg).normalized() * rg
            info["gap_max_mm"] = max(info["gap_max_mm"], round(1000 * (c2 - c).length, 1)); c = c2
        raw.append(c)
    # 她轉回前方那 turn_s 秒：右肩整個繞半圈，照「搆得到」算的點會甩 30 cm → 從抓到那一點平順移到轉完時的拉手位置
    i_t2 = int(round((tm["turn2"] + HANDLES) * FPS)); i_t2e = min(n - 1, i_t2 + int(turn_s * FPS))
    # 2026-10-13 近照：直線內插的話手腕從新郎胸前穿過 → 繞著他的骨盆（極座標內插角度與半徑，半徑至少 r_min）
    c_a = raw[i_t2]; c_b = raw[i_t2e]
    for i in range(i_t2, i_t2e + 1):
        k = (i - i_t2) / max(1, i_t2e - i_t2); k = k * k * (3 - 2 * k)
        hg = gst["poses"][i][1]
        va = (c_a - hg).xy; vb = (c_b - hg).xy
        aa = math.atan2(va.y, va.x); ab = math.atan2(vb.y, vb.x); da = (ab - aa + math.pi) % (2 * math.pi) - math.pi
        ang = aa + da * k; rad = max(r_min, va.length + (vb.length - va.length) * k)
        z = c_a.z + (c_b.z - c_a.z) * k + 0.05 * math.sin(math.pi * k)
        raw[i] = Vector((hg.x + rad * math.cos(ang), hg.y + rad * math.sin(ang), z))
    Cs = []
    for i in range(n):
        if raw[i] is None:
            Cs.append(None); continue
        w = [raw[j] for j in range(max(i_reach, i - smooth), min(n, i + smooth + 1))]
        Cs.append(sum(w, Vector()) / len(w))
    STATE["pull_C"] = Cs
    gout, bout = [], []
    for i in range(n):
        Rg, hg = gst["poses"][i]; Rb, hb = bst["poses"][i]
        if Cs[i] is None:
            gout.append((Rg, hg)); bout.append((Rb, hb)); continue
        t = i / FPS - HANDLES; c = Cs[i]
        wg = _sm(t, tm["grab"] - PB["g_pre"], tm["grab"] + 0.02)     # 2026-10-13 穿禮服站得遠：他的手腕在她伸手時一起被帶過去（原本抓到後 0.12 秒內跳 27 cm）
        if wg > 0:
            Hg = tg.fk(Rg, hg)
            Rg = mr.arm_ik(tg, Rg, hg, "R", Hg["J_Bip_R_Hand"].lerp(c, wg), Vector((0, 0, -1)) + (Hg["J_Bip_R_UpperArm"] - Hg["J_Bip_C_Hips"]).normalized() * 0.3)
        wb = _sm(t, tm["reach"], tm["grab"] - 0.1)
        if wb > 0:
            # 手：指向沿著「肩膀→手腕」、掌心朝下蓋在新郎手腕上（手掌中心在手腕上方 wrap），四指 grip 繞過去
            Hb = tb.fk(Rb, hb); Sb = Hb[f"J_Bip_{BS}_UpperArm"]
            d = (c - Sb); d.z = min(d.z, 0.0); d.normalize()
            palm = Vector((0, 0, -1)) - d * d.z; palm.normalize()
            q = hand_quat(tb, BS, d, palm)
            plen = 0.6 * (tb.rest_h[f"J_Bip_{BS}_Middle1"] - tb.rest_h[f"J_Bip_{BS}_Hand"]).length
            M = Matrix.Translation(c - d * plen - palm * wrap) @ q.to_matrix().to_4x4()
            Rb = put_hand_pole(tb, Rb, hb, BS, M, wb, ((Sb - Hb["J_Bip_C_Hips"]).normalized() * 0.5 + Vector((0, 0, -1))).normalized(), 0.6)
            Rb = mr.gesture(tb, Rb, BS, "grip", wb)
        gout.append((Rg, hg)); bout.append((Rb, hb))
    gst["poses"] = gout; bst["poses"] = bout
    # 接觸檢查：新娘手掌中心（手腕往中指根 60%）到新郎手腕的距離
    d = []
    for i in range(i_grab, n):
        Hb = tb.fk(*bst["poses"][i]); Hg = tg.fk(*gst["poses"][i])
        pc = Hb[f"J_Bip_{BS}_Hand"].lerp(Hb[f"J_Bip_{BS}_Middle1"], 0.6)
        d.append(round(1000 * ((pc - Hg["J_Bip_R_Hand"]).length - wrap), 1))      # 手掌中心離新郎手腕表面（扣掉 wrap）
    info["palm_to_wrist_mm"] = (min(d), max(d))
    return info


FACE_CHEW = dict(jawOpen=1.0, cheekPuff=0.0)


def chew_w(t):
    """新郎嘴：送到嘴前張開（0.25 秒），塞進去那格起邊嚼（每秒約 2.2 下）、臉頰鼓起"""
    ct = STATE["cake_t"]; m = ct["mouth"]
    if t < m - 0.3:
        return 0.0, 0.0
    if t < m:
        return 0.55 * _sm(t, m - 0.3, m - 0.05), 0.0
    k = _sm(t, m, m + 0.15)
    jaw = 0.55 * (1 - k) + k * 0.18 * (1 - math.cos(2 * math.pi * 2.2 * (t - m)))
    return jaw, 0.6 * _sm(t, m, m + 0.25)


def bride_glare_w(t):
    tm = STATE["b_tm"]; a = tm["turn1"] + 0.3; b = tm["go"] + 0.6
    return _sm(t, a, a + 0.25) * (1 - _sm(t, b, b + 0.4))


def _face_hook(i):
    FM = _fm(); t = i / FPS - HANDLES
    hd = L.head_mesh(C.actor("bride")["arm"]); w = bride_glare_w(t)
    for k, v in FM.FACE_GLARE.items():
        kb = hd.data.shape_keys.key_blocks.get(k)
        if kb is not None:
            kb.value = v * w
    hg = L.head_mesh(STATE["arm"]); jaw, puff = chew_w(t)
    for k, v in (("jawOpen", jaw), ("cheekPuff", puff)):
        kb = hg.data.shape_keys.key_blocks.get(k)
        if kb is not None:
            kb.value = v


CAKE_OBJ = "I_ZP_mini_cake.011"


def _hand_M(tgt, R, h, side="L"):
    Hd = tgt.fk(R, h); b = f"J_Bip_{side}_Hand"
    return Matrix.Translation(Hd[b]) @ R[b].to_matrix().to_4x4()


CAKE_BITE = 0.8                                    # 咬一口：蛋糕縮成 0.8 倍（看得出少了一塊）
FLOOR_Z = 0.02                                     # 走廊地毯（ZP_venue_corridor_runner）表面高 2 cm（設 0 時蛋糕落地一半埋進地毯）


def cake_track():
    """小蛋糕：拿起那格起跟著左手捏的點（指尖中點、保持直立），咬一口那格縮成 CAKE_BITE 倍；
    起步後 drop 秒鬆手 → 照鬆手那格手的速度拋出、重力落下、邊掉邊往前翻，落地後側躺在地上不動"""
    ob = bpy.data.objects.get(CAKE_OBJ); ct = STATE["cake_t"]
    if ob is None:
        return None
    M0 = STATE.get("cake_M0") or (ob.matrix_world.copy() @ Matrix.Scale(CAKE_SCALE, 4)); STATE["cake_M0"] = M0
    ix = lambda t: int(round((t + HANDLES) * FPS))
    il, im, idr = ix(ct["lift"]), ix(ct["mouth"]) + 2, ix(ct["drop"])
    off = Vector((0, 0, CAKE_H / 2)); out = []; R0 = M0.to_3x3()
    pos = []
    for i, (R, h) in enumerate(STATE["poses"]):
        if i < il:
            out.append(M0); pos.append(M0.translation.copy()); continue
        sc = CAKE_BITE if i >= im else 1.0
        if i <= idr:
            p = pinch_pt(STATE["tgt"], R, h) - off * sc
            k = min(1.0, (i - il) / 4.0)
            p = M0.translation.lerp(p, k); pos.append(p)
            out.append(Matrix.Translation(p) @ (R0 @ Matrix.Diagonal((sc, sc, sc))).to_4x4()); continue
        out.append(None)
    # 掉落：鬆手那格的速度、重力；繞水平軸（垂直於水平速度）翻轉，落地（最低點碰地）就停
    p0 = pos[idr]; v0 = (pos[idr] - pos[idr - 1]) * FPS
    vh = Vector((v0.x, v0.y, 0)); vh = vh if vh.length > 1e-3 else Vector((1, 0, 0))
    ax = Vector((0, 0, 1)).cross(vh).normalized()       # 往前翻
    ob_bb = [Vector(c) for c in ob.bound_box]
    land = None
    for i in range(idr + 1, len(out)):
        t = (i - idr) / FPS
        if land is None:
            ang = min(math.radians(100), math.radians(330) * t)
            Rm = Quaternion(ax, ang).to_matrix() @ R0 @ Matrix.Diagonal((CAKE_BITE,) * 3)
            c = p0 + vh * t * 0.6 + Vector((0, 0, v0.z * t - 4.9 * t * t))
            zmin = min((Rm @ v).z for v in ob_bb) + c.z
            if zmin <= FLOOR_Z:
                c.z += FLOOR_Z - zmin; land = Matrix.Translation(c) @ Rm.to_4x4(); out[i] = land
                STATE["cake_land"] = dict(i=i, t=round(i / FPS - HANDLES, 2), xy=(round(c.x, 2), round(c.y, 2)))
                continue
            out[i] = Matrix.Translation(c) @ Rm.to_4x4()
        else:
            out[i] = land
    STATE["cake_M"] = out
    return dict(lift_i=il, bite_i=im, drop_i=idr, land=STATE.get("cake_land"))


def _cake_hook(i):
    ob = bpy.data.objects.get(CAKE_OBJ); Ms = STATE.get("cake_M")
    if ob is None or not Ms:
        return
    M = Ms[min(i, len(Ms) - 1)]
    ob.matrix_world = M if M is not None else STATE["cake_M0"]


def akimbo_bride():
    FM = _fm(); tm = STATE["b_tm"]
    with C.as_actor("bride"):
        STATE["poses"] = FM._akimbo(STATE["tgt"], STATE["poses"], tm["ag"] - 0.25, tm["reach"] + 0.1)
    return True



# ════════ 衣服、場景、鏡頭、短片 ════════
OUTFIT_G = "groom-beige-3piece"
OUTFIT_B = "bride-blush-ballgown"                   # 2026-10-13 服裝端定案（outfit/bride_blush_ballgown@bride v1，裙寬 0.32 m）
HIDE_B3 = ()                                       # 第 3 版藏過 B3 的牌子、柱子（舊位置擋路）；2026-10-13 場景端已搬到 x 7.9、9.5，走廊延長 → 不用藏


def dress():
    import zanim_dress as D
    out = {"groom": D.dress(OUTFIT_G)}
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
    """走廊（venue_offset.json 固定平移，同 B0、B1→B2）；換景柱子（y＜−1）、還沒搬的 B3 道具藏起來；小蛋糕跟手"""
    vo = json.load(open(BK.VENUE_OFFSET)); off = (vo["dx"], vo["dy"], 0.0)
    old = bpy.data.collections.get("ZP_Scene_VenueCorridor")
    if old is not None and old.name in Z.studio_col().children:      # 已經載過（重跑）就沿用
        objs = {o.name: o for o in old.all_objects}
    else:
        objs = BK.venue("Scene_VenueCorridor", off)
    hid = []
    STATE["sc"].view_layers[0].update()
    for n_, o in objs.items():
        if (n_.startswith("I_ZP_pillar") and o.matrix_world.translation.y < -1.0) or n_ in HIDE_B3:
            o.hide_render = o.hide_viewport = True; hid.append(n_)
    STATE["sc"].view_layers[0].update()
    ck = cake_track()
    for hk in (_cake_hook, _face_hook):
        if hk not in Z.POSE_HOOKS:
            Z.POSE_HOOKS.append(hk)
    return dict(offset=off, hidden=hid, cake=ck)


CAM = dict(ease=1.0, bias=0.8, hold_bias=0.5, dist=3.9)
# 2026-10-13 導演端（rough_v12 第 24 秒）：新郎轉身面向鏡頭吃蛋糕時貼在剪接 col 版面露出區（原片 x 40～100%）最左緣、左肩被切
#   → 停住那段（字卡期間）鏡頭拉遠到 dist m、跟拍點 hold_bias（0.5＝兩人中點；量過 3.9 m＋0.5：新郎最左 46.6%、新娘最右 94.8%；3.6 m 只剩 45.1%／97.0%）；起步後 ease 秒回到 3 m（B3 開頭照 3 m 接）
# 2026-10-13 穿禮服：新娘停在新郎右前方約 1 m（不撞裙子）→ 原本「新郎停穩那格」的構圖會把她切出畫面右邊。
#   改成：新郎停穩後 ease 秒內移到「新娘停穩那格」的構圖再固定（字卡期間不動）；跟拍點不是正中點，偏向新娘 bias（0.5＝中點；越大新娘越靠近畫面 70% 處、新郎往左。0.8：新郎約 44%、新娘約 76%）


def camera_fn():
    """側面跟拍（兩人之間偏新娘 bias、畫面 70%）；新郎停穩 → ease 秒內移到新娘停穩時的構圖 → 固定到被拉著起步（字卡）→ ease 秒追上"""
    mk = STATE["marks"]; tm = STATE["b_tm"]; arm = STATE["arm"]

    def partner(k_):
        def p(i):                                        # follow_camera 剛 pose_at(i)：用擺出來的世界座標（原始資料的 hips 座標不同）
            g = arm.matrix_world @ arm.pose.bones["J_Bip_C_Hips"].head; b = Vector(tuple(C.hips_world("bride")))
            return (g.x + (b.x - g.x) * k_, g.y + (b.y - g.y) * k_)
        return p
    mid = BK.side_follow(holds=[], handles=HANDLES, partner=partner(1.0))          # 開頭照兩人中點（接 B1→B2 的構圖）
    base = BK.side_follow(holds=[], handles=HANDLES, partner=partner(CAM["bias"] / 0.5))
    far = BK.side_follow(holds=[], handles=HANDLES, partner=partner(CAM["hold_bias"] / 0.5), offset=(0.0, -CAM["dist"], 0.25))
    ix = lambda t: int(round((t + HANDLES) * FPS))
    i0, i1, i2 = ix(mk["still"]), ix(max(tm["still"], mk["still"])), ix(mk["go"]); ne = int(CAM["ease"] * FPS)
    hold = far(i1)

    def ease(a, b, k):
        k = max(0.0, min(1.0, k)); k = k * k * (3 - 2 * k)
        return a[0].lerp(b[0], k), a[1].lerp(b[1], k)

    def f(i):
        if i < i0:
            return mid(i)
        if i < i0 + ne:
            return ease(mid(i0), hold, (i - i0) / ne)
        if i <= i2:
            return hold
        return ease(hold, base(i), (i - i2) / ne)
    return f


def bake_face():
    """兩人的表情（新娘瞪、新郎張嘴嚼）烤成形態鍵關鍵影格"""
    import zanim_sample as SP
    FM = _fm(); n = len(STATE["poses"]); out = {}
    for who, arm, keys in (("bride", C.actor("bride")["arm"], {k: (lambda t, v=v: v * bride_glare_w(t)) for k, v in FM.FACE_GLARE.items()}),
                           ("groom", STATE["arm"], {"jawOpen": lambda t: chew_w(t)[0], "cheekPuff": lambda t: chew_w(t)[1]})):
        key = L.head_mesh(arm).data.shape_keys
        ad = key.animation_data_create(); act = bpy.data.actions.get(f"SAMPLE_Face_{who}") or bpy.data.actions.new(f"SAMPLE_Face_{who}"); ad.action = act
        for k, fn in keys.items():
            if k in key.key_blocks:
                SP._put(act, key, f'key_blocks["{k}"].value', 0, [fn(i / FPS - HANDLES) for i in range(n)])
        out[who] = len(keys)
    return out


def clip(v=1, size=(960, 540)):
    """存工作用樣張 → 回傳背景渲短片的指令（BODY 自動點名兩副身體）"""
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", 35.0)
    for a in (STATE["arm"], C.actor("bride")["arm"]):
        a.animation_data_clear()
        hk = L.head_mesh(a).data.shape_keys
        if hk is not None:
            hk.animation_data_clear()
    cake = bpy.data.objects.get(CAKE_OBJ)
    if cake is not None:
        cake.animation_data_clear()
    meshes = [o for o in STATE["sc"].objects if o.type == "MESH" and not o.hide_viewport]
    for o in meshes:
        o.hide_viewport = True
    try:
        cf = camera_fn()
        out = SP.bake(objects=[cake] if cake else [], camera_fn=cf)
    finally:
        for o in meshes:
            o.hide_viewport = False
    out["face_keys"] = bake_face()
    path = SP.save("b2_formal")
    cmd = SP.render_clip("b2_formal", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + f"/formal_v{v}.mp4", size=size)
    return dict(out, path=path, cmd=cmd)


def close(t, views, out=None, res=480, lens=50, hide=None):
    return _fm().close(t, views, out=out or STATE["out_dir"] + "/formal_close", res=res, lens=lens, hide=hide)


def run():
    t0 = time.time(); r = {}
    if "bride" not in C.cast():
        setup(); add_bride()
    r["groom"] = build_groom(); r["bride"] = build_bride(); akimbo_bride(); r["pull"] = pull_arms()
    STATE["stats"] = Z.stats(); r["groom_stats"] = STATE["stats"]["summary"]
    with C.as_actor("bride"):
        STATE["stats"] = Z.stats(); r["bride_stats"] = STATE["stats"]["summary"]
    r["dress"] = dress(); r["scene"] = scene_set(); r["sec"] = round(time.time() - t0, 1)
    return r


def end_state(path=r"D:/render-work/zepeto-anim/opening-proposal-b/b2/end_state_formal.json"):
    """鏡內最後一格兩人的骨盆、面向（B3 開頭照這個接；場景端照這個搬 B3 道具）"""
    i = int(round((STATE["dur"] + HANDLES) * FPS))
    R, h = STATE["poses"][i]; bR, bh = C.actor("bride")["poses"][i]
    with C.as_actor("bride"):
        byaw = _yaw(STATE["tgt"], bR)
    # 走路相位（B3 從這一格的步伐接）：最後一段走路從 b4 那格起播
    wn = L._CL["male_standard_walk"]["n"] - 1; tg = STATE["seq"].T[-1][0]
    gph = (STATE["walk_cut"]["b4"] + (i / FPS - tg) * FPS) % wn
    tm = STATE["b_tm"]; tb = C.actor("bride")["seq"].T[-1][0]                 # 最後一段（走路）
    bph = (tm["b4"] + (i / FPS - tb) * FPS) % tm["wn"]
    end_b = json.load(open(B12_END))["bride"]
    d = dict(what="B2 正式版鏡內最後一格（B3 開頭照這個接）", t_end=round(STATE["dur"], 3),
             groom=dict(hips=[round(x, 3) for x in h], yaw=round(_yaw(STATE["tgt"], R), 2), walk_phase=round(gph, 1), wn=wn, clip="male_standard_walk"),
             bride=dict(hips=[round(x, 3) for x in bh], yaw=round(byaw, 2), walk_phase=round(bph, 1), wn_retimed=tm["wn"], walk_k=end_b["walk_k"], clip="female_walk"),
             holding="新娘左手（BS）握新郎右手腕（新娘在前）；接觸點每格在 STATE['pull_C']")
    json.dump(d, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return d
