# B0 正式版（2026-10-13 導演端「動畫開工：B0」：趁 B1→B2 等使用者看，先做 B0）。
# 走位版 v4（b0_shot.py）→ 正式版的差別：
#   1. 兩副真身體同場（zanim_cast：新郎 v8＋米色三件式、新娘 v3；禮服定案後填 OUTFIT_B 重跑穿模）。
#   2. 出門後的轉身：v4 是「停下 → 原地左轉 → 從靜止起步」，正式版改成邊走邊左轉（walk_turn_left_90），
#      站在門內等推門改用 standing_idle（導演端指定）。Mixamo 的 Walking Turn 90 Left 套上來骨盆只轉 36°、路線幾乎直的
#      → zanim_fix.amp_turn 把轉向放大到 90°（腳步不變、路線跟著彎）。
#   3. 結尾接 B1→B2 正式版鏡內第 0 格（b1_b2/start_state_formal.json）：新郎骨盆 (1.207, 0.098)、面向 +X、走路相位第 0 格；
#      新娘在新郎左後方、走路（放慢 0.854）相位第 30 格。整條從結尾往回擺；門的位置固定（venue_offset.json），推門的手用 IK 補差距。
# 用法（MCP）：
#   # BODY=groom,bride
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b0"); import b0_formal as B0F; print(B0F.run())
import bpy, os, sys, math, json, time
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
import zanim_fix as F
import zanim_cast as C
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE, PREFIX = "B0_FORMAL", "ZA_"
FPS = 30
HANDLES = 1.0
START = r"D:/render-work/zepeto-anim/opening-proposal-b/b1_b2/start_state_formal.json"
G_CLIPS = ("standing_idle", "male_start_walk", "walk_turn_left_90", "male_standard_walk")
B_CLIPS = ("standing_idle", "female_start_walk", "walk_turn_left_90", "female_walk")
DOOR_W, DOOR_H = 0.75, 1.75
DOOR_Y = 1.52            # 2026-10-13 場景端：走廊牆連同門退到 y 1.52（原本 0.75；讓出新娘走線）。門軸在左 x −1.029，門片往鏡頭這邊開
P = dict(X=9, si_a=0, sw_at=0.7, start_a=10, sw_exit=range(24, 78, 2), m=(0, 1), turn_deg=90.0, kk=range(0, 4), speed=(0.9, 0.94, 0.97, 1.0, 1.03, 1.06, 1.1),
         door_open_deg=100.0, door_t=(0.4, 1.0), push_release=(0.48, 0.7), hand_along=0.614, hand_back=0.05, hips_back=0.38,
         push_side="L", handle=(0.614, 0.11, 0.80))
# 2026-10-13 使用者第 4 輪：開門的手沒碰到門把 → 握住門把再推。門把在門片離門軸 0.614 m、高 0.80 m、門片房間那面再往外 0.11 m（素材 lounge_door 量的）；
#   新郎面向鏡頭站在門內時門把在他左手邊 → push_side＝L（左手握）；hand_along 照門把位置；
#   門開到 7° 時肩膀到門把就 0.51 m（手長 0.45）→ 握住、推一把，0.48 秒放手，門自己盪開到 100°（push_release）
# sw_at：鏡內第幾秒開始起步（Start Walking 第 start_a 格是靜止的，真的跨出第一步再晚約 0.5 秒）；sw_exit：起步那支播到第幾格接轉身（搜尋）；
# kk：轉完後整圈多走幾圈（搜尋）；speed：最後那段走路的快慢（搜尋，讓起點落在門後）；door_t：門開的鏡內秒（分鏡：0.4 秒推、1.0 秒全開）


def setup():
    m = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b0")[1]
    Z.load_clips(G_CLIPS)
    vo = json.load(open(BK.VENUE_OFFSET))
    STATE["door_c"] = Vector((vo["dx"], vo["dy"] + DOOR_Y, 0.0))        # 休息室門中心（動畫座標）
    STATE["hinge_x"] = STATE["door_c"].x - DOOR_W / 2; STATE["door_y"] = STATE["door_c"].y
    return m


def _yaw(tgt, R):
    v = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0))
    return math.degrees(math.atan2(v.x, -v.y))


def _segs_groom(a_sw, kk, sp, m=0):
    """起步（Start Walking 從靜止播到 a_sw 附近）→ 走出門（Walking，m 圈＋湊到轉身的相位；門退到 y 1.52 後起步那支不夠長）
    → 邊走邊左轉 90°（放大過的 Walking Turn）→ 往右走（最後一段快慢 sp，第 Lw 格＝B1→B2 第 0 格）"""
    tgt = STATE["tgt"]; X = P["X"]
    SI, SW, WT, W = (L._CL[n] for n in G_CLIPS)
    wn = W["n"] - 1
    if "WT90" not in STATE:
        STATE["WT90"], STATE["amp_g"] = F.amp_turn(tgt, WT, P["turn_deg"])
    WT9 = STATE["WT90"]
    mt = STATE.setdefault("_mt", {})
    if a_sw not in mt:
        mt[a_sw] = F.match_phase(tgt, SW, range(a_sw - 2, a_sw + 3), W, range(0, wn))
    a1, b1, _ = mt[a_sw]
    if "_mwt" not in STATE:
        STATE["_mwt"] = F.match_phase(tgt, W, range(0, wn), WT9, range(0, 8))
    a3, b3, _ = STATE["_mwt"]
    if "_mw" not in STATE:
        STATE["_mw"] = F.match_phase(tgt, WT9, range(WT9["n"] - 14, WT9["n"] - X), W, range(0, wn))
        a2_, _b, _d = STATE["_mw"]
        # 只用到第 b3～a2 格（前後各有漸變）：這幾格裡實際轉的角度要剛好 90°，不然走出門的方向會斜（試過斜 30°、擦到門框）
        for _ in range(3):
            got = _yaw(tgt, WT9["R"][a2_]) - _yaw(tgt, WT9["R"][b3])
            STATE["WT90"], STATE["amp_g"] = F.amp_turn(tgt, WT, STATE.get("_amp_total", P["turn_deg"]) * P["turn_deg"] / got)
            STATE["_amp_total"] = STATE.get("_amp_total", P["turn_deg"]) * P["turn_deg"] / got
            WT9 = STATE["WT90"]
        STATE["_mw"] = F.match_phase(tgt, WT9, range(WT9["n"] - 14, WT9["n"] - X), W, range(0, wn))
    WT9 = STATE["WT90"]
    a2, b2, _ = STATE["_mw"]
    Lo = ((a3 + X - b1) % wn) + m * wn                    # 走出門：從相位 b1 走到相位 a3＋X（接轉身）
    Wo = mr.splice_clip(W, [(b1 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * (m + 2))
    if abs(sp - 1) > 1e-6:                                 # 走出門那段也照同一個快慢（補起點的距離；只差幾 %，看不出來）
        Wo = F.retime(Wo, sp); Lo = int(round(Lo / sp))
    Wk = F.retime(W, sp) if abs(sp - 1) > 1e-6 else W
    wk = Wk["n"] - 1
    b2k = int(round(b2 / sp))
    Lw = ((wk - b2k) % wk) + kk * wk                       # 從相位 b2 走到相位 0（B1→B2 第 0 格的相位）
    W2 = mr.splice_clip(Wk, [(b2k / FPS, wk / FPS)] + [(0, wk / FPS, 1 / FPS)] * (kk + 3))
    segs = [mr.Seg(SI, P["si_a"], P["si_a"] + 170, name="門內站著、手搭在門上（Standing Idle）"),
            mr.Seg(SW, P["start_a"], a1 + X, at=P["sw_at"] + HANDLES, name="推開門、起步（Start Walking）"),
            mr.Seg(Wo, 0, max(X + 1, Lo), name="走出門（Walking）"),
            mr.Seg(WT9, b3, a2 + X, name="邊走邊左轉 90°（Walking Turn 90 Left，轉向放大到 90°）"),
            mr.Seg(W2, 0, Lw + 45, name="往右走（Walking；第 Lw 格＝B1→B2 第 0 格，之後是尾巴多做的）")]
    return segs, dict(a_sw=a1, b_walk_out=b1, out_frames=Lo, b_turn=b3, a_turn=a2, b_walk=b2, kk=kk, speed=sp, walk_frames=Lw, m=m)


def _hand_target():
    """推門的手（右手腕）在第 0 格要在的位置：離門軸 hand_along m、門板後面 hand_back m"""
    return Vector((STATE["hinge_x"] + P["hand_along"], STATE["door_y"] + P["hand_back"]))


def solve_groom():
    """從結尾往回擺：結尾那格（最後一段走完）骨盆＝B1→B2 第 0 格、面向 +X。
    搜尋起步播到第幾格、轉完多走幾圈、最後走路快慢 → 第 0 格右手腕最接近門上的推點"""
    tgt = STATE["tgt"]; st = json.load(open(START))["groom"]
    end_xy = tuple(st["hips"][:2]); end_yaw = st["yaw"]
    want = _hand_target(); best = None; t0 = time.time()
    for a_sw in P["sw_exit"]:
      for m in P["m"]:
        for kk in P["kk"]:
            for sp in P["speed"]:
                segs, info = _segs_groom(a_sw, kk, sp, m)
                seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS)
                te = seq.T[4][0] + info["walk_frames"] / FPS
                seq.place(te, end_xy, end_yaw)
                seq.place(te, end_xy, 2 * end_yaw - _yaw(tgt, seq.at(te)[0]))      # 骨盆面向（含走路左右擺）對上 B1→B2 第 0 格
                R, h, _y = seq.at(HANDLES)
                hand = tgt.fk(R, h)[f"J_Bip_{P['push_side']}_Hand"]   # 站著時手垂在身側：x 當推點，y 不準（推的時候手往前伸）
                along = hand.x - STATE["hinge_x"]               # 推點離門軸幾 m：門寬 0.75，0.3～0.6 都推得動 → 不硬要 hand_along
                err = (abs(h.y - (STATE["door_y"] + P["hips_back"])) + max(0.0, abs(along - P["hand_along"]) - 0.15) + 0.5 * abs(sp - 1.0)
                       + max(0.0, abs(h.x - STATE["door_c"].x) - 0.12) + 0.3 * abs(_yaw(tgt, R)) / 90)   # 起點在門中間附近、正對鏡頭（直直走出門，不擦門框）
                # 骨盆在門板後 hips_back m（手往前伸剛好搭到門）；最後走路快慢差越少越好（接 B1→B2 的走路是原速）
                if best is None or err < best[0]:
                    best = (err, a_sw, kk, sp, tuple(round(x, 3) for x in h.xy), round(te - HANDLES, 2), m)
    STATE["g_best"] = best
    return dict(err_m=round(best[0], 3), a_sw=best[1], kk=best[2], speed=best[3], m=best[6], hips0=best[4], hips_want_y=round(STATE["door_y"] + P["hips_back"], 3), dur=best[5], sec=round(time.time() - t0, 1))


def build_groom():
    """照 solve_groom 的解接段、擺放 → 每格姿勢（頭多做的 1 秒站著不動）→ 貼地、鎖腳 → 推門的手"""
    import b0_shot as B
    tgt = STATE["tgt"]; st = json.load(open(START))["groom"]
    _e, a_sw, kk, sp, hand, _d, m = STATE["g_best"]
    segs, info = _segs_groom(a_sw, kk, sp, m)
    seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS)
    te = seq.T[4][0] + info["walk_frames"] / FPS          # 這一格＝B1→B2 正式版鏡內第 0 格
    seq.place(te, tuple(st["hips"][:2]), st["yaw"]); seq.place(te, tuple(st["hips"][:2]), 2 * st["yaw"] - _yaw(tgt, seq.at(te)[0]))
    dur = te - HANDLES
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    poses = [seq.at(i / FPS)[:2] for i in range(n)]       # 開頭多做的 1 秒：Standing Idle 本來就是站著（手搭門上）
    poses = [(dict(R), h.copy()) for R, h in poses]
    pts = L.sole_points(STATE["arm"])
    poses, off = F.ground(tgt, poses, pts)
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9, z_on=0.015, gap_max=25)
    poses = lock_win(tgt, poses, pts, [(seq.T[3][0] - 0.15, seq.T[4][0] + 0.25)])     # 放大轉向那段：踩地的腳會跟著轉 → 放寬門檻再鎖一次
    poses = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in poses]
    # 門：推點＝第 0 格右手腕的位置（離門軸 along、高度 hand_h）
    Hd = tgt.fk(*poses[int(HANDLES * FPS)])
    STATE["hand_h"] = Hd["J_Bip_R_Hand"].z
    B.P.update(door_open_deg=P["door_open_deg"], door_t=P["door_t"])
    B.STATE = STATE
    STATE.update(poses=poses, seq=seq, dur=dur, segs=[(round(seq.T[k][0], 2), round(s.dur, 2), s.name) for k, s in enumerate(segs)])
    _push(poses, Hd[f"J_Bip_{P['push_side']}_Hand"].x - STATE["hinge_x"])
    STATE["stats"] = Z.stats()
    marks = dict(sw=P["sw_at"], out=seq.T[2][0] - HANDLES, turn=seq.T[3][0] - HANDLES, walk=seq.T[4][0] - HANDLES, end=dur)
    STATE["marks"] = marks
    return dict(dur=round(dur, 2), frames=n, info=info, marks={k: round(v, 2) for k, v in marks.items()},
                segs=[(round(t - HANDLES, 2), d, nm) for t, d, nm in STATE["segs"]], stats=STATE["stats"]["summary"],
                ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)))


def lock_win(tgt, poses, pts, wins, v_on=2.0, z_on=0.03, ramp=3, step_h=0.012):
    """只在 wins（格子秒數 (起, 迄)）裡放寬門檻再鎖一次腳（B1→B2 新娘轉身用過同一招；全段放寬會把走路弄壞）"""
    for a_, b_ in wins:
        a = max(0, int(round(a_ * FPS))); b = min(len(poses) - 1, int(round(b_ * FPS)))
        sub, _ = F.foot_lock(tgt, poses[a:b + 1], pts, v_on=v_on, ramp=ramp, z_on=z_on, step_h=step_h)
        poses[a:b + 1] = _pin_foot_turn(tgt, sub, pts)
        poses = zero_slide(tgt, poses, pts, a, b)
    return poses


def no_hop(tgt, poses, pts, keep=0.002, thr=0.006, smooth=3):
    """兩腳同時離地（鞋底最低點 > thr）的格子整個人往下壓，讓低的那隻腳貼地；壓的量前後 smooth 格取最大再平均，
    但每格不超過那格低的那隻腳離地的高度（不陷地）。B0 新娘起步、轉身前後懸空 10～13 mm"""
    low = []
    for R, h in poses:
        so = L.soles(tgt, R, h, pts)
        low.append(min(min(p.z for p in so["L"]), min(p.z for p in so["R"])))
    n = len(poses); d = [max(0.0, z - keep) if z > thr else 0.0 for z in low]
    dd = [max(d[max(0, i - smooth):min(n, i + smooth + 1)]) for i in range(n)]
    dd = [sum(dd[max(0, i - smooth):min(n, i + smooth + 1)]) / (min(n, i + smooth + 1) - max(0, i - smooth)) for i in range(n)]
    out = [(R, h - Vector((0, 0, min(dd[i], max(0.0, low[i] - keep))))) for i, (R, h) in enumerate(poses)]
    return out, round(1000 * max(dd), 1)


def zero_slide(tgt, poses, pts, a, b, z_on=0.005):
    """逐格把「上一格和這一格都貼地的鞋底點」的平均水平位移抵銷（腿 IK 把腳踝往回移）：
    蹬地時腳跟抬起、只剩腳尖貼地，鎖腳踝會讓腳尖往前掃（B0 放大轉向那段一格 15 mm）→ 改成鎖真的貼地的點"""
    for s_ in "LR":
        sp = [(bn, c) for bn, c in pts if f"_{s_}_" in bn]
        prev = None
        for i in range(a, b + 1):
            R, h = poses[i]
            cur = L.soles(tgt, R, h, sp)[s_]
            if prev is not None:
                idx = [k for k, (p0, p1) in enumerate(zip(prev, cur)) if p0.z <= z_on and p1.z <= z_on]
                if len(idx) >= 3:
                    d = sum((cur[k] - prev[k] for k in idx), Vector()) / len(idx); d.z = 0
                    if d.length > 0.0005:
                        Hd = tgt.fk(R, h)
                        an = Hd[f"J_Bip_{s_}_Foot"]
                        pole = Hd[f"J_Bip_{s_}_LowerLeg"] - (Hd[f"J_Bip_{s_}_UpperLeg"] + an) / 2
                        R = F.leg_ik(tgt, R, h, s_, an - d, pole)
                        poses[i] = (R, h); cur = L.soles(tgt, R, h, sp)[s_]
            prev = cur
    return poses


def _foot_yaw(tgt, R, k):
    v = (R[k] @ tgt.rest_q[k].inverted()) @ Vector((0, -1, 0))
    return math.atan2(v.x, -v.y)


def _pin_foot_turn(tgt, poses, pts, z_on=0.006, ramp=3):
    """踩地期間腳掌方向固定（腳踝 XY 已由 foot_lock 釘住，但放大轉向時腳掌跟著身體轉 → 腳尖在地上掃，一格 15 mm）：
    每段著地（鞋底最低點 ≤ z_on 連續 3 格以上）腳骨、腳趾骨的水平朝向停在這段第一格，頭尾 ramp 格漸入漸出。
    第一版整個旋轉都固定：蹬地時腳跟抬不起來、整隻腳離地 22～52 mm → 只固定朝向"""
    n = len(poses)
    for s_ in "LR":
        low = [min(p.z for p in L.soles(tgt, R, h, [(b, c) for b, c in pts if f"_{s_}_" in b])[s_]) for R, h in poses]
        on = [z <= z_on for z in low]; i = 0
        while i < n:
            if not on[i]:
                i += 1; continue
            j = i
            while j + 1 < n and on[j + 1]:
                j += 1
            if j - i >= 2:
                fk = f"J_Bip_{s_}_Foot"
                y0 = _foot_yaw(tgt, poses[i][0], fk)
                for q in range(i, min(n, j + ramp + 1)):
                    w = 1.0 if q <= j else 1.0 - (q - j) / (ramp + 1)
                    d = (y0 - _foot_yaw(tgt, poses[q][0], fk) + math.pi) % (2 * math.pi) - math.pi
                    rq = Quaternion((0, 0, 1), d * mr._smooth(w))        # 只轉回水平朝向；腳跟抬起、腳尖貼地（蹬地）照原片
                    R = dict(poses[q][0])
                    for k in (fk, f"J_Bip_{s_}_ToeBase"):
                        if k in R:
                            R[k] = rq @ R[k]
                    poses[q] = (R, poses[q][1])
            i = j + 1
    return poses


def _push(poses, along):
    """握住門把（門片房間那面，離門軸 handle[0] m、高 handle[2] m）跟著門轉開；push_release 秒內放開回原片手臂。
    手：四指從上面包住門把（掌心朝下、手指朝門軸方向），用 grip 手勢"""
    import b0_shot as B
    tgt = STATE["tgt"]; r0, r1 = P["push_release"]; s_ = P["push_side"]; ha, hb, hz = P["handle"]
    plen = 0.6 * (tgt.rest_h[f"J_Bip_{s_}_Middle1"] - tgt.rest_h[f"J_Bip_{s_}_Hand"]).length
    from zanim_hand import hand_quat, put_hand_pole
    for i, (R, h) in enumerate(poses):
        t = i / FPS - HANDLES
        w = 1.0 if t <= r0 else max(0.0, 1.0 - (t - r0) / (r1 - r0))
        if w <= 0:
            continue
        th = B.door_angle(max(t, 0.0)); u = Vector((math.cos(th), -math.sin(th), 0)); nrm = Vector((math.sin(th), math.cos(th), 0))
        grip = B.door_point(max(t, 0.0), along=ha, z=hz) + nrm * hb                      # 門把（房間那一側）
        d = (-u + Vector((0, 0, -0.35))).normalized(); palm = Vector((0, 0, -1))
        q = hand_quat(tgt, s_, d, palm)
        M = Matrix.Translation(grip - d * plen + Vector((0, 0, 0.025))) @ q.to_matrix().to_4x4()
        R2 = put_hand_pole(tgt, R, h, s_, M, w, Vector((0.3 if s_ == "L" else -0.3, 0.3, -1.0)).normalized(), 0.6)
        R2 = mr.gesture(tgt, R2, s_, "grip", w)
        poses[i] = (R2, h)
    STATE["push_along"] = along


def heading(key=None, step=15):
    st = C.actor(key) if key else STATE
    tgt = st["tgt"]
    return [(round(i / FPS - HANDLES, 2), round(_yaw(tgt, R), 1), round(h.x, 2), round(h.y, 2)) for i, (R, h) in enumerate(st["poses"]) if i % step == 0]


# ════════ 新娘（zanim_cast，v3） ════════
PB = dict(start_a=3, sw_exit=range(16, 54, 2), kk=range(0, 3), behind_y=0.50, lag_min=0.0, walk_k=None, step_h=0.004, zero_walk=True, win_pre=0.35,
          skirt=dict(margin=0.015, elbow_k=2.0, max_deg=40), speed=(1.0, 1.1, 1.2, 1.3, 1.4), min_d=0.6, door_w=2.0, bend=(0.0,))
# 2026-10-13 穿禮服：speed＝最後那段走路的快慢（搜尋）；min_d：兩人骨盆至少隔幾 m（裙擺半徑 0.335）；
#   bend：走出門那段轉彎幾度（搜尋；試過 ±12°，門口那點幾乎不動 → 改在 B1→B2 讓新娘多落後 12 cm，整條路線左移對準門中心）；
#   門開到 100°（原 80°：新娘經過時裙子擦進門片 2.5 cm）；door_w：經過門口時離門中心的距離也算進誤差（門寬 0.75、裙寬 0.67，偏 4 cm 就擦到門框）
# behind_y：門內等的時候在新郎後面幾 m；lag_min：至少比新郎晚幾秒起步。2026-10-13 門退到 1.52 後：晚 0.35 秒起步的話
#   追不上結尾的站位（解出來她只在新郎後面 9 cm）→ 0（實際晚 0.13 秒；她在後面 0.5 m，一路至少隔 0.48 m）


def add_bride():
    m = C.add_actor("bride", "bride")
    with C.as_actor("bride"):
        Z.load_clips(B_CLIPS)
    return m


def _segs_bride(a_sw, kk, m=0, sp=1.0, bend=0.0):
    """同新郎：起步 → 走出門（m 圈＋湊相位）→ 邊走邊左轉（實際用到的格子轉滿 90°）→ 往右走（放慢 walk_k，第 Lw 格＝B1→B2 第 0 格）"""
    st = json.load(open(START))["bride"]; X = P["X"]
    tgt = STATE["tgt"]
    SI, SW, WT, W = (L._CL[n] for n in B_CLIPS)
    if "b_Wk" not in STATE:                               # 新娘自己的一份（Mixamo 重定向跟身體比例有關，不能用新郎的）
        STATE["b_Wk"] = F.retime(W, st["walk_k"])
        STATE["b_WT90"], _g = F.amp_turn(tgt, WT, P["turn_deg"]); STATE["_b_amp"] = P["turn_deg"]
    Wk = STATE["b_Wk"]; wk = Wk["n"] - 1
    mt = STATE.setdefault("_bmt", {})
    if a_sw not in mt:
        mt[a_sw] = F.match_phase(tgt, SW, range(a_sw - 2, a_sw + 3), Wk, range(0, wk))
    a1, b1, _ = mt[a_sw]
    if "_bmw" not in STATE:
        WT9 = STATE["b_WT90"]
        b3 = F.match_phase(tgt, Wk, range(0, wk), WT9, range(0, 8))[1]
        for _ in range(3):                                # 用到的格子裡轉滿 90°（同新郎）
            a2_ = F.match_phase(tgt, WT9, range(WT9["n"] - 14, WT9["n"] - X), Wk, range(0, wk))[0]
            got = _yaw(tgt, WT9["R"][a2_]) - _yaw(tgt, WT9["R"][b3])
            STATE["_b_amp"] *= P["turn_deg"] / got
            STATE["b_WT90"], _g = F.amp_turn(tgt, WT, STATE["_b_amp"]); WT9 = STATE["b_WT90"]
        STATE["_bmwt"] = F.match_phase(tgt, Wk, range(0, wk), WT9, range(0, 8))
        STATE["_bmw"] = F.match_phase(tgt, WT9, range(WT9["n"] - 14, WT9["n"] - X), Wk, range(0, wk))
    WT9 = STATE["b_WT90"]
    a3, b3, _ = STATE["_bmwt"]; a2, b2, _ = STATE["_bmw"]
    Lo = ((a3 + X - b1) % wk) + m * wk
    Wo = mr.splice_clip(Wk, [(b1 / FPS, wk / FPS)] + [(0, wk / FPS, 1 / FPS)] * (m + 2))
    if bend:                                              # 走出門那段微微轉彎（正＝左轉）：讓她從門中心出來（禮服裙寬 0.67、門寬 0.75）
        Wo = F.bend(Wo, bend, 0, max(X + 1, Lo))
    Lw = ((st["walk_phase"] - b2) % wk) + kk * wk           # 從相位 b2 走到 B1→B2 第 0 格的相位
    if sp != 1.0:                                         # 最後那段走路的快慢（同新郎的 speed）：結尾固定，走快一點起點就更往門裡面
        key = ("b_Wk2", round(sp, 3))
        if key not in STATE:
            STATE[key] = F.retime(L._CL[B_CLIPS[3]], st["walk_k"] * sp)
        Wk2 = STATE[key]
    else:
        Wk2 = Wk
    wk2 = Wk2["n"] - 1; f2 = wk2 / wk                     # 快慢不同的那支一圈格數不同：相位、格數照比例換
    W2 = mr.splice_clip(Wk2, [(b2 * f2 / FPS, wk2 / FPS)] + [(0, wk2 / FPS, 1 / FPS)] * (kk + 3))
    Lw = int(round(Lw * f2))
    segs = [mr.Seg(SI, 0, 170, name="新娘在門內等（Standing Idle）"),
            mr.Seg(SW, PB["start_a"], a1 + X, name="跟著起步（Female Start Walking）"),
            mr.Seg(Wo, 0, max(X + 1, Lo), name="走出門（Female Walk，放慢）"),
            mr.Seg(WT9, b3, a2 + X, name="邊走邊左轉 90°（Walking Turn 90 Left，轉向放大）"),
            mr.Seg(W2, 0, Lw + 45, name="在新郎左後方往右走（Female Walk，放慢到新郎的速度）")]
    return segs, dict(a_sw=a1, b_walk_out=b1, out_frames=Lo, b_turn=b3, a_turn=a2, b_walk=b2, kk=kk, m=m, walk_frames=Lw)


def _place_bride(segs, info, te):
    """結尾（te，格子秒數）對上 B1→B2 第 0 格的新娘；起步時間＝結尾往回推（Seg.at）"""
    tgt = STATE["tgt"]; st = json.load(open(START))["bride"]
    X = P["X"] / FPS
    t_walk = te - info["walk_frames"] / FPS
    t_turn = t_walk - (segs[3].dur - X)
    t_out = t_turn - (segs[2].dur - X)
    t_sw = t_out - (segs[1].dur - X)
    segs[1].at = t_sw; segs[2].at = t_out; segs[3].at = t_turn; segs[4].at = t_walk
    seq = mr.Sequence(tgt, segs, blend=X)
    seq.place(te, tuple(st["hips"][:2]), st["yaw"]); seq.place(te, tuple(st["hips"][:2]), 2 * st["yaw"] - _yaw(tgt, seq.at(te)[0]))
    return seq, t_sw


def solve_bride():
    """搜尋起步播到第幾格、轉完多走幾圈 → 門內等的位置最接近（門中心 x、新郎後方 behind_y），而且比新郎晚 lag_min 秒以上起步"""
    te = STATE["dur"] + HANDLES; gx, gy = STATE["poses"][0][1].x, STATE["poses"][0][1].y
    want = Vector((STATE["door_c"].x, gy + PB["behind_y"]))
    best = None
    with C.as_actor("bride"):
        tgt = STATE["tgt"]
        GP = C.cast()["_main"]["state"]["poses"]                 # 新郎（as_actor 期間 STATE 是新娘的）
        for a_sw in PB["sw_exit"]:
          for m in (0, 1, 2):
            for kk in PB["kk"]:
              for sp in PB["speed"]:
               for bd in PB["bend"]:
                segs, info = _segs_bride(a_sw, kk, m, sp, bd)
                seq, t_sw = _place_bride(segs, info, te)
                if t_sw - HANDLES < P["sw_at"] + PB["lag_min"]:
                    continue
                try:
                    dmin = min((seq.at(i / FPS)[1].xy - GP[i][1].xy).length for i in range(0, len(GP), 3))
                except IndexError:                        # 片子不夠長（這組湊不出來）
                    continue
                if dmin < PB["min_d"]:                    # 禮服：骨盆至少隔 min_d（裙擺半徑 0.335＋新郎半身＋擺手）
                    continue
                R, h, _y = seq.at(HANDLES)
                d_door = abs(seq_x_at(seq, STATE["door_y"], len(GP)) - STATE["door_c"].x)
                err = (h.xy - want).length + 0.3 * abs(_yaw(tgt, R)) / 90 + PB["door_w"] * d_door
                if best is None or err < best[0]:
                    best = (err, a_sw, kk, tuple(round(x, 3) for x in h.xy), round(t_sw - HANDLES, 2), m, sp, bd, round(dmin, 3), round(d_door, 3))
    STATE["b_best"] = best
    return dict(err_m=round(best[0], 3), a_sw=best[1], kk=best[2], m=best[5], sp=best[6], bend=best[7], hips0=best[3], want=tuple(round(x, 3) for x in want), t_sw=best[4],
                min_d=best[8], off_door_center=best[9])


def seq_x_at(seq, y, n):
    """新娘骨盆經過 y（門口）那一刻的 x（找片內 n 格）"""
    prev = None
    for i in range(n):
        try:
            h = seq.at(i / FPS)[1]
        except IndexError:                                # 段落交界的浮點誤差偶爾超出片尾一格
            continue
        if prev is not None and (prev.y - y) * (h.y - y) <= 0:
            return h.x
        prev = h
    return 1e3


def build_bride():
    te = STATE["dur"] + HANDLES; n = len(STATE["poses"])
    _e, a_sw, kk, _h, _t, m, sp, bd = STATE["b_best"][:8]
    with C.as_actor("bride"):
        tgt = STATE["tgt"]
        segs, info = _segs_bride(a_sw, kk, m, sp, bd)
        seq, t_sw = _place_bride(segs, info, te)
        poses = [seq.at(i / FPS)[:2] for i in range(n)]
        poses = [(dict(R), h.copy()) for R, h in poses]
        pts = L.sole_points(STATE["arm"])
        poses, off = F.ground(tgt, poses, pts)
        poses, hop = no_hop(tgt, poses, pts)               # 先壓再鎖腳：壓下去後才貼地的腳要給鎖腳看到（反過來做，那隻腳會貼地拖 30 mm）
        poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9, z_on=0.015, gap_max=25)   # 抬腳 12 mm 照預設：改成 4 mm 起步第一步會貼地拖 30 mm（寧可 0.1 秒兩腳離地 1 cm）
        poses = lock_win(tgt, poses, pts, [(seq.T[3][0] - PB["win_pre"], seq.T[4][0] + 0.25)], step_h=PB["step_h"])   # 小碎步抬腳 12 mm 時新娘轉身兩腳同時離地 10～40 mm
        if PB["zero_walk"]:
            poses = zero_slide(tgt, poses, pts, int(round(seq.T[1][0] * FPS)), n - 1)   # 女生走路（放慢）每圈接縫滑 10 mm
        poses = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in poses]
        if OUTFIT_B:                                      # 禮服：手垂下會沒入裙子 → 手臂往外擺、手肘微彎（同 B1→B2）
            poses, STATE["skirt_arms_deg"] = F.skirt_arms(tgt, poses, **PB["skirt"])
        poses, STATE["head_up_max"] = F.level_head(tgt, poses)     # 2026-10-13 使用者第 4 輪：新娘走路頭往斜上方看 → 仰角超過 5° 的部分壓回來
        STATE.update(poses=poses, seq=seq, segs=[(round(seq.T[k][0], 2), round(s.dur, 2), s.name) for k, s in enumerate(segs)])
        STATE["stats"] = Z.stats()
        st = STATE["stats"]["summary"]
        segs_shot = [(round(t - HANDLES, 2), d, nm) for t, d, nm in STATE["segs"]]
    return dict(info=info, t_sw=round(t_sw - HANDLES, 2), segs=segs_shot, stats=st, ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)))


# ════════ 衣服、場景（走廊＋會開的門）、鏡頭、短片 ════════
OUTFIT_G = "groom-beige-3piece"
OUTFIT_B = "bride-blush-ballgown"                   # 2026-10-13 服裝端定案（outfit/bride_blush_ballgown@bride v1，裙寬 0.32 m）


def dress():
    import zanim_dress as D
    out = {"groom": D.dress(OUTFIT_G)}
    if OUTFIT_B:
        with C.as_actor("bride"):
            out["bride"] = D.dress(OUTFIT_B, body="bride")
    names = set(STATE.get("outfit_objs") or []) | set(C.actor("bride").get("outfit_objs") or [])
    for o in bpy.data.objects:
        if o.name in names:
            for m in o.modifiers:
                if m.type == "SOLIDIFY" or "FixFolds" in m.name:
                    m.show_viewport = False
    return out


def scene_set():
    """走廊（venue_offset.json 固定平移）；場景裡關著的門藏起來，另放一扇 lounge_door、門片跟著推門轉開（同走位版）"""
    import b0_shot as B
    vo = json.load(open(BK.VENUE_OFFSET)); off = (vo["dx"], vo["dy"], 0.0)
    objs = BK.venue("Scene_VenueCorridor", off)
    for n, o in objs.items():
        if n.startswith("I_ZP_lounge_door"):
            o.hide_render = o.hide_viewport = True
        if n.startswith("I_ZP_pillar") and o.location.y < -1.0:      # B3 結尾用的換景柱子
            o.hide_render = o.hide_viewport = True
    g = BK.props_api(); dcol = g["append_prop"]("lounge_door", parent=Z.studio_col())
    leaf = None
    for o in dcol.all_objects:
        if o.parent is None:
            o.location = o.location + Vector((STATE["door_c"].x, STATE["door_y"], 0))
        if o.name.startswith("ZP_lounge_door_leaf"):
            leaf = o
        if o.name.startswith("ZP_lounge_door_frame") and o.parent is None:
            o.location.y -= 0.003                         # 2026-10-13 使用者第 4 輪「門框右邊白柱一直閃」：這扇門的門框有 1/3 的面和走廊牆上的門框完全重合（z-fighting）→ 往走廊挪 3 mm
    leaf.name = "ZA_DoorLeaf"
    if _door_hook not in Z.POSE_HOOKS:
        Z.POSE_HOOKS.append(_door_hook)
    return dict(offset=off, door_c=tuple(round(x, 3) for x in STATE["door_c"]), push_along=round(STATE["push_along"], 3))


def _door_hook(i):
    import b0_shot as B
    d = bpy.data.objects.get("ZA_DoorLeaf")
    if d is not None:
        d.rotation_euler = (0, 0, -B.door_angle(max(0.0, i / FPS - HANDLES)))


CAP_SHIFT = 0.2


def camera_fn(ease=1.8):
    """開頭固定（門在畫面右側 60% 的中間，離門 3.5 m）；新郎走出門起 ease 秒內轉成側面跟拍（兩人中點、畫面 70%），
    結尾＝B1→B2 第 0 格的跟拍（同 BK.side_follow：鏡頭在中點 −Y 3 m、比骨盆高 0.25、看向 0.70）"""
    import zanim_sample as SP
    follow = SP.follow_camera(offset=(0.0, -3.0, 0.25), aim_z=0.70, partner=lambda i: tuple(C.hips_world("bride"))[:2])
    dx3 = -BK.frame_w(3.0) * CAP_SHIFT
    door_c = Vector((STATE["door_c"].x, STATE["door_y"], 0.70))
    fixed_aim = door_c + Vector((-BK.frame_w(3.5) * CAP_SHIFT, 0, 0)); fixed_loc = fixed_aim + Vector((0, -3.5, 0.25))
    t0 = STATE["marks"]["out"]                            # 新郎一走出門就開始轉成跟拍（第 2 版等到轉身才跟，往鏡頭走那段被畫面右邊切掉）

    def f(i):
        t = i / FPS - HANDLES
        l, a = follow(i)
        l = l + Vector((dx3, 0, 0)); a = a + Vector((dx3, 0, 0))
        s = min(1.0, max(0.0, (t - t0) / ease)); s = s * s * (3 - 2 * s)
        return fixed_loc.lerp(l, s), fixed_aim.lerp(a, s)
    return f


def clip(v=1, size=(960, 540)):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", 35.0)
    for a in (STATE["arm"], C.actor("bride")["arm"]):
        a.animation_data_clear()
    leaf = bpy.data.objects["ZA_DoorLeaf"]
    leaf.animation_data_clear(); leaf.rotation_mode = "XYZ"   # 上一次烤完門片是四元數＋關鍵影格：_door_hook 設 rotation_euler 會沒作用（第 3 版門一開始就開著）
    meshes = [o for o in STATE["sc"].objects if o.type == "MESH" and not o.hide_viewport and o != leaf]
    for o in meshes:
        o.hide_viewport = True
    try:
        cf = camera_fn()
        out = SP.bake(objects=[leaf], camera_fn=cf)
    finally:
        for o in meshes:
            o.hide_viewport = False
    path = SP.save("b0_formal")
    cmd = SP.render_clip("b0_formal", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + f"/formal_v{v}.mp4", size=size)
    return dict(out, path=path, cmd=cmd)


def close(t, views, out=None, res=480, lens=50, hide=None):
    """近照（同 b1b2_formal.close）：烤好的樣張 frame_set，另開 CLOSE_Cam"""
    od = STATE["out_dir"]; Z.use_shot("opening-proposal-b", "b1_b2"); STATE["out_dir"] = od     # use_shot 只加 import 路徑
    import b1b2_formal as FM
    return FM.close(t, views, out=out or STATE["out_dir"] + "/formal_close", res=res, lens=lens, hide=hide)


def run():
    t0 = time.time(); m = setup(); r = dict(groom_solve=solve_groom()); r["groom"] = build_groom()
    add_bride(); r["bride_solve"] = solve_bride(); r["bride"] = build_bride()
    r["dress"] = dress(); r["scene"] = scene_set(); r["sec"] = round(time.time() - t0, 1)
    return r


def cleanup():
    return Z.cleanup(SCENE)
