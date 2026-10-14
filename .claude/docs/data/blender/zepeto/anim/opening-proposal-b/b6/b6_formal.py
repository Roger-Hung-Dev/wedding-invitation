# B6 正式版（2026-10-13 導演端：B4～B6 正式版一開始就穿禮服做；新娘看前方）。宴會廳大門前（門廳），全片最後一鏡：
# 換景柱子擦過（B5→B6 在柱子後面切，不必接 B5 的位置；走路相位、誰在哪一側照 B5 結尾）→ 兩人並肩走到大門正前方停下
# → 一起往左跨一步轉身面向大門（背對鏡頭；新郎在右、新娘在左）→ 深呼吸（肩膀抬起、胸口鼓起再放下，新娘晚 0.1 秒）
# → 新郎左手牽新娘右手 → 大門往內打開、門後的光 → 新郎微微抬頭；鏡頭停下後拉遠到 4.5 m（大門整扇入鏡）→ 繞到兩人正背後 → 往門裡推（閃白由剪接做）。
# 動作（Mixamo 原樣）：新郎 Walking → Stop Walking → Standing Idle（跨步轉身用 F.pivot_turn）；
#   新娘 Female Walk → Female Stop Walking → Female Idle（走路放慢 0.854，和新郎並排）。深呼吸、牽手、抬頭是在原片上疊的小幅度轉動與手臂 IK。
# 站位（場景端 venue_foyer.py，場景座標 → 動畫座標 x −0.654）：大門中心 x 15.746（門洞 1.7×2.2 m）、後牆 y 0.75；
#   新郎停在 (16.096, 0)、新娘 (15.396, 0)（間距 0.7 m：0.6 m 時裙擺碰到新郎的腿）；走路時新娘在遠側 0.52 m（同 B2、B4）、停下時往裡收（深度方向）。
#   換景柱子：開頭在鏡頭前 0.9 m 擋住兩人中點，0～0.9 秒往左滑出畫、之後藏起來（停下後鏡頭拉遠，不藏會再入鏡；走位版做法）。
# 姿勢參考：
#   深呼吸：吸氣時胸口鼓起、肩膀上抬約 1～2 cm，吐氣時慢慢放下，一次約 3～4 秒（放鬆呼吸）——這裡縮成 1.6 秒、幅度放大才看得出背影；
#   牽手：掌心相對、手指扣住對方手背，手臂自然垂在兩人中間。
# 用法（MCP）：
#   # BODY=groom,bride
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b6"); import b6_formal as B6F; print(B6F.run())
import bpy, os, sys, math, json, time
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
import zanim_fix as F
import zanim_cast as C
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE, PREFIX = "B6_FORMAL", "ZA_"
FPS = 30
HANDLES = 1.0
B5_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b5/end_state_formal.json"
G_CLIPS = ("male_standard_walk", "male_stop_walk", "standing_idle")
B_CLIPS = ("female_walk", "female_stop_walk", "female_idle")
DOOR_X, WALL_Y = 15.746, 0.75
STOP_G = Vector((16.096, 0.0, 0.0)); STOP_B = Vector((15.396, 0.0, 0.0))
P = dict(X=9, walk_s=1.0, stop_b=66, settle=0.3, pivot_s=0.9, pivot_lift=0.035,
         breathe_d=0.2, breathe_s=1.6, b_breathe_lag=0.1, hold_d=0.1, reach_s=0.5, door_d=0.6, door_s=1.2,
         orbit_d=0.5, orbit_s=1.0, push_s=0.8, tail=0.4, chin=6.0, hand_dz=0.30)
# walk_s：鏡內走幾秒才開始停下；breathe_d／breathe_s：兩人都轉好後幾秒開始深呼吸、一次幾秒；hold_d：吐完氣後幾秒伸手、reach_s 秒牽到；
# door_d：牽到後幾秒開門、door_s 開門幾秒；orbit_d：開門後幾秒鏡頭開始繞、orbit_s 繞幾秒、push_s 推幾秒、tail 推完留幾秒；chin：開門後新郎抬頭幾度
PB = dict(walk_k=0.854, lane_y=(-0.72, -0.22), lag=0.0, ahead=0.6, breathe=(5.0, 4.0), shoulder=(7.0, 6.0), skirt=dict(margin=0.015, elbow_k=2.0, max_deg=40))
# lane_y：(新郎, 新娘) 走路時骨盆的 y（2026-10-13 第 2 版禮服實量：新郎原片走線偏到 y 0.29、新娘再外側 0.52 → 裙子擦進門廳牆 10 cm、碰到門片 3 cm；
#   牆在 y 0.75、裙擺半徑 0.335 → 新娘 ≤ 0.39，新郎再往鏡頭側 0.48；第 3 版 0.33 時裙子還擦到門廳牆邊的花台 10 cm、攝影區燈架腳 4 cm；0.16 時還擦到門左邊花柱（台座在 x 14.30、y 0.40、半徑 0.2）→ 新娘 −0.22、新郎 −0.72，停下前 1.2 秒斜走到門正前方）；lag：新娘比新郎晚幾秒停穩（2026-10-13 第 1 版 0.35：她要多走、開頭落後 1.3 m，跟拍一次只拍到一個人；
#   走路長度只能整圈調；−0.7 時她先停在左邊、新郎接著走過去會穿過她 → 0）；
# ahead：新娘走路那段往前補幾 m（開頭補滿、停穩時 0；lag 0 時她開頭落後 1.3 m → 約 0.7 m，同 B5 的漸進平移）；breathe：(新郎, 新娘) 吸氣時上身往後仰幾度（胸口鼓起）；shoulder：肩膀抬幾度
CAM = dict(dist=3.6, far_dist=4.5, far_aim_z=1.05, pull_s=1.2, back_dist=3.0, back_z=1.0, back_aim_z=1.0, push_dist=1.5, push_z=1.15)
PILLAR = dict(d=0.9, hw=0.33, exit=0.9)


def setup():
    m = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b6")[1]
    Z.load_clips(G_CLIPS)
    C.add_actor("bride", "bride")
    with C.as_actor("bride"):
        Z.load_clips(B_CLIPS)
    return m


class _nullctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ctx(key):
    return C.as_actor("bride") if key == "bride" else _nullctx()


def _yaw(tgt, R):
    v = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0))
    return math.degrees(math.atan2(v.x, -v.y))


def _sm(t, a, b):
    x = 0.0 if t <= a else (1.0 if t >= b else (t - a) / (b - a))
    return x * x * (3 - 2 * x)


def _still(poses, i0, thr=0.08):
    return next((i for i in range(i0, len(poses) - 3) if (poses[i + 3][1] - poses[i][1]).length * 10 < thr), i0)


def _b0():
    p = os.path.abspath(os.path.join(HERE, "..", "b0"))
    if p not in sys.path:
        sys.path.insert(0, p)
    import b0_formal as B0
    return B0


def plan(key, walk_s, hold):
    """走路（接 B5 結尾的相位）→ 停下 → 站著（face 180＝面向大門）。回傳 seq"""
    end = json.load(open(B5_END))[key]; X = P["X"]
    with _ctx(key):
        tgt = STATE["tgt"]
        W, ST, ID = (L._CL[n] for n in (G_CLIPS if key == "groom" else B_CLIPS))
        if key == "bride":
            W = F.retime(W, PB["walk_k"])
        wn = W["n"] - 1
        a0 = int(round(end["walk_phase"] - HANDLES * FPS)) % wn
        a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
        want = int(round((HANDLES + walk_s) * FPS))
        L1 = want + ((a1 + X - (a0 + want)) % wn)
        W1 = mr.splice_clip(W, [(a0 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * (L1 // wn + 2))
        stop_b = P["stop_b"] if key == "groom" else ST["n"] - 1
        nf = int((hold + 1.0) * FPS); b = min(ID["n"] - 1, nf)
        segs = [mr.Seg(W1, 0, L1, name="走到大門前（Walking）"),
                mr.Seg(ST, b1, stop_b, hold=P["settle"], name="停下（Stop Walking，播到停穩）"),
                mr.Seg(ID, 0, b, hold=max(0.0, (nf - b) / FPS), face=180.0, name="跨一步左轉面向大門 → 深呼吸、牽手、看大門打開（Idle）")]
        seq = mr.Sequence(tgt, segs, blend=X / FPS); seq.place(0.0, (0.0, 0.0), 90.0)
    return segs, seq


def build():
    """兩人排段 → 整條平移到停點（新娘走路時在遠側 side m、停下前收回）→ 跨步轉身 → 貼地鎖腳 → 新娘頭看前方、手臂避開裙子"""
    out = {}; n_tmp = int(10 * FPS)
    segs, seq = plan("groom", P["walk_s"], 8.0)
    pg = [seq.at(i / FPS)[:2] for i in range(n_tmp)]
    g_still = _still(pg, int(round(seq.T[1][0] * FPS))) / FPS - HANDLES
    # 新娘：停穩比新郎晚 lag 秒左右（走路長度只能整圈，挑最接近的）
    best = None
    for ws in [x / 10 for x in range(0, 30)]:
        _s, bs = plan("bride", ws, 8.0)
        with _ctx("bride"):
            bp = [bs.at(i / FPS)[:2] for i in range(n_tmp)]
        bst = _still(bp, int(round(bs.T[1][0] * FPS))) / FPS - HANDLES
        e = abs(bst - (g_still + PB["lag"]))
        if best is None or e < best[0]:
            best = (e, ws, bst)
    b_ws, b_still = best[1], best[2]
    g_turn = g_still + P["pivot_s"]; b_turn = b_still + P["pivot_s"]; pair = max(g_turn, b_turn)
    br = pair + P["breathe_d"]; hold = br + P["breathe_s"] + P["b_breathe_lag"] + P["hold_d"]
    held = hold + P["reach_s"]; door = held + P["door_d"]; orbit = door + P["orbit_d"]; push = orbit + P["orbit_s"]
    dur = push + P["push_s"] + P["tail"]
    tm = dict(g_still=g_still, b_still=b_still, g_turn=g_turn, b_turn=b_turn, pair=pair, breathe=br, hold=hold, held=held, door=door,
              orbit=orbit, push=push, end=dur)
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    for key, ws, still, goal in (("groom", P["walk_s"], g_still, STOP_G), ("bride", b_ws, b_still, STOP_B)):
        segs, seq = plan(key, ws, dur - still + 1.0)
        with _ctx(key):
            tgt = STATE["tgt"]
            poses = [(dict(R), h.copy()) for R, h, _y in (seq.at(min(i / FPS, seq.start + seq.dur)) for i in range(n))]
            si = int(round((still + HANDLES) * FPS))
            sh = goal - poses[si][1]; sh.z = 0
            poses = [(R, h + sh) for R, h in poses]
            # 走線：走路時骨盆（1 秒平均，保留左右晃）在 lane_y，停下前 1.2 秒內收到門正前方（深度方向，側面鏡頭幾乎看不出）
            a = si - int(1.2 * FPS); i0 = int(HANDLES * FPS); ys = [h.y for R, h in poses]; m = 15
            ysm = [sum(ys[max(0, j - m):j + m + 1]) / len(ys[max(0, j - m):j + m + 1]) for j in range(len(ys))]
            Y = PB["lane_y"][0 if key == "groom" else 1]
            poses = [(R, h + Vector((PB["ahead"] * (1 - _sm(i, i0, si)) if key == "bride" else 0.0,
                                     (Y - ysm[i]) * (1 - _sm(i, a, si)), 0))) for i, (R, h) in enumerate(poses)]
            nt = int(round(P["pivot_s"] * FPS)); i1 = int(round(seq.T[2][0] * FPS)) - 2
            piv = lambda q: F.pivot_turn(tgt, q, i1, i1 + nt, first="L", lift=P["pivot_lift"], sign=1)
            poses = piv(poses)
            pts = L.sole_points(STATE["arm"])
            poses, _off = F.ground(tgt, poses, pts)
            poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9, z_on=0.015, gap_max=25)
            B0 = _b0()
            poses = B0._pin_foot_turn(tgt, poses, pts)
            poses = B0.zero_slide(tgt, poses, pts, 0, n - 1)
            poses = piv(poses)
            poses = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in poses]
            info = dict(walk_s=ws, still=round(still, 2), still_xy=(round(poses[si][1].x, 3), round(poses[si][1].y, 3)),
                        start_xy=(round(poses[int(HANDLES * FPS)][1].x, 2), round(poses[int(HANDLES * FPS)][1].y, 2)),
                        pivot=(round(i1 / FPS - HANDLES, 2), round((i1 + nt) / FPS - HANDLES, 2)))
            if key == "bride":
                poses, info["head_up_max"] = F.level_head(tgt, poses)
                poses, info["skirt_arms"] = F.skirt_arms(tgt, poses, **PB["skirt"])
            STATE.update(poses=poses, seq=seq, segs=[(round(seq.T[k][0], 2), round(s.dur, 2), s.name) for k, s in enumerate(segs)])
            if key == "groom":
                STATE.update(dur=dur, b6_tm=tm, marks=dict(still=g_still, end=dur))
        out[key] = info
    out["tm"] = {k: round(v, 2) for k, v in tm.items()}
    return out


# ════════ 深呼吸、牽手、抬頭 ════════
def _frame(tgt, R):
    q = R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()
    fw = q @ Vector((0, -1, 0)); fw.z = 0; fw.normalize()
    return fw, Vector((fw.y, -fw.x, 0))


def _breathe(tgt, R, w, back_deg, sh_deg):
    """吸氣 w（0～1）：胸口以上往後仰 back_deg（胸口鼓起）、兩邊肩膀往上抬 sh_deg（子骨頭一起轉）"""
    if w <= 0:
        return R
    fw, rt = _frame(tgt, R)
    R = dict(R)
    q = Quaternion(rt, math.radians(back_deg) * w)        # 繞右手方向轉正角＝往後仰
    for b in ["J_Bip_C_Chest"] + F._chain(tgt, "J_Bip_C_Chest"):
        R[b] = q @ R[b]
    for s, sg in (("L", 1), ("R", -1)):
        sb = f"J_Bip_{s}_Shoulder"
        if sb not in R:
            continue
        qs = Quaternion(fw, sg * math.radians(sh_deg) * w)  # 左肩繞前方轉正角＝往上抬（右肩反向）
        for b in [sb] + F._chain(tgt, sb):
            R[b] = qs @ R[b]
    return R


def breathe_hold():
    from zanim_hand import hand_quat, put_hand_pole
    tm = STATE["b6_tm"]; gst = STATE; bst = C.actor("bride"); tg, tb = gst["tgt"], bst["tgt"]; n = len(gst["poses"])
    bw = lambda t, lag: math.sin(math.pi * min(1.0, max(0.0, (t - tm["breathe"] - lag) / P["breathe_s"]))) ** 2
    gout, bout = [], []
    info = dict(palm_gap_mm=[])
    for i in range(n):
        t = i / FPS - HANDLES
        Rg, hg = gst["poses"][i]; Rb, hb = bst["poses"][i]
        Rg = _breathe(tg, Rg, bw(t, 0.0), PB["breathe"][0], PB["shoulder"][0])
        Rb = _breathe(tb, Rb, bw(t, P["b_breathe_lag"]), PB["breathe"][1], PB["shoulder"][1])
        wh = _sm(t, tm["hold"], tm["held"])
        if wh > 0:
            Hg = tg.fk(Rg, hg); Hb = tb.fk(Rb, hb)
            fw, rt = _frame(tg, Rg)                       # 面向大門（+Y）：新郎右手方向＝+X、新娘在 −X
            mid = (Hg["J_Bip_L_UpperArm"] + Hb["J_Bip_R_UpperArm"]) / 2
            c = Vector((mid.x, mid.y, mid.z - P["hand_dz"])) + fw * 0.08   # 兩人中間、稍微往前、肩膀往下 hand_dz（ZEPETO 手臂短：用骨盆高度算會搆不到，掌心差 13 cm）
            down = (fw * 0.35 + Vector((0, 0, -1))).normalized()
            for who, tgt, R, h, side, pal in (("g", tg, Rg, hg, "L", -rt), ("b", tb, Rb, hb, "R", rt)):
                q = hand_quat(tgt, side, down, pal)            # 手指往下、掌心朝對方
                plen = 0.6 * (tgt.rest_h[f"J_Bip_{side}_Middle1"] - tgt.rest_h[f"J_Bip_{side}_Hand"]).length
                Hc = c - pal * 0.018                           # 兩隻手掌各退 1.8 cm（掌心相貼）
                M = Matrix.Translation(Hc - down * plen) @ q.to_matrix().to_4x4()
                R = put_hand_pole(tgt, R, h, side, M, wh, (Vector((0, 0, -1)) - fw * 0.5).normalized(), 0.6)
                R = mr.gesture(tgt, R, side, "grip", 0.55 * wh)
                if who == "g":
                    Rg = R
                else:
                    Rb = R
        wc = _sm(t, tm["door"] + 0.2, tm["door"] + 0.9)    # 門開後新郎微微抬頭
        if wc > 0:
            fw, rt = _frame(tg, Rg); Rg = dict(Rg)
            for b in ["J_Bip_C_Head"] + F._chain(tg, "J_Bip_C_Head"):
                Rg[b] = Quaternion(rt, math.radians(P["chin"]) * wc) @ Rg[b]
        gout.append((Rg, hg)); bout.append((Rb, hb))
    gst["poses"] = gout; bst["poses"] = bout
    i_m = int(round((tm["held"] + 0.3 + HANDLES) * FPS))
    Hg = tg.fk(*gout[i_m]); Hb = tb.fk(*bout[i_m])
    pc = lambda H, s: H[f"J_Bip_{s}_Hand"].lerp(H[f"J_Bip_{s}_Middle1"], 0.6)
    return dict(palm_d_mm=round(1000 * (pc(Hg, "L") - pc(Hb, "R")).length, 1), at=round(i_m / FPS - HANDLES, 2))


# ════════ 衣服、場景、大門、換景柱子、鏡頭、短片 ════════
OUTFIT_G = "groom-beige-3piece"
OUTFIT_B = "bride-blush-ballgown"


def dress():
    import zanim_dress as D
    out = {"groom": D.dress(OUTFIT_G)}
    with C.as_actor("bride"):
        out["bride"] = D.dress(OUTFIT_B, body="bride")
    names = set(STATE.get("outfit_objs") or []) | set(C.actor("bride").get("outfit_objs") or [])
    for o in bpy.data.objects:
        if o.name in names:
            for m in o.modifiers:
                if m.type == "SOLIDIFY" or "FixFolds" in m.name:
                    m.show_viewport = False
    return {k: (list(v[0])[:3], v[1]) for k, v in out.items()}


def _hook(i):
    t = i / FPS - HANDLES; tm = STATE["b6_tm"]
    pil = bpy.data.objects.get("ZA_Pillar")
    if pil is not None:
        pil.hide_render = pil.hide_viewport = t >= PILLAR["exit"]
        k = min(1.0, max(0.0, t / PILLAR["exit"]))
        pil.location = STATE["pillar_xy"] + Vector((-STATE.get("pillar_slide", 0.0) * k, 0, 0))
    k = _sm(t, tm["door"], tm["door"] + P["door_s"])     # 大門往內開（L 0 → +90°、R 0 → −90°）
    for s, sign in (("L", 1), ("R", -1)):
        d = bpy.data.objects.get("ZA_Door" + s)
        if d is not None:
            d.rotation_mode = "XYZ"                        # 烤樣張會把它改成四元數（之後設 rotation_euler 沒作用 → 第 2 版大門沒打開）
            d.rotation_euler = (0, 0, sign * math.radians(90) * k)


def scene_set():
    vo = json.load(open(BK.VENUE_OFFSET)); off = (vo["dx"], vo["dy"], 0.0)
    objs = {}
    for key in ("Scene_VenuePhotoZone", "Scene_VenueFoyer"):
        old = bpy.data.collections.get("ZP_" + key)
        if old is not None and old.name in Z.studio_col().children:
            objs.update({o.name: o for o in old.all_objects})
        else:
            objs.update(BK.venue(key, off))
    leaves = {}
    for n_, o in objs.items():
        if n_.startswith("I_ZP_ballroom_doors"):          # 關著的整組大門（實例，不能轉）藏起來，用可轉的門片
            o.hide_render = o.hide_viewport = True
        elif n_.startswith("ZP_ballroom_door_L_posed"):
            leaves["L"] = o
        elif n_.startswith("ZP_ballroom_door_R_posed"):
            leaves["R"] = o
        elif n_.startswith("ZP_ballroom_doors_") and n_.split(".")[0].endswith("_posed"):
            o.hide_render = o.hide_viewport = False
    for k, o in leaves.items():
        o.name = "ZA_Door" + k; o.hide_render = o.hide_viewport = False
    STATE["sc"].view_layers[0].update()
    if bpy.data.objects.get("ZA_Pillar") is None:
        BK.props_api()["place_prop"]("pillar", loc=(0, 0, 0), parent=Z.studio_col(), name="ZA_Pillar")
    r = pillar_place()
    if _hook not in Z.POSE_HOOKS:
        Z.POSE_HOOKS.append(_hook)
    door = next((o for n_, o in objs.items() if n_.startswith("I_ZP_door_frame")), None)
    return dict(offset=off, doors=sorted(leaves), door_frame=tuple(round(v, 2) for v in door.matrix_world.translation) if door else None, pillar=r)


def _mid(i):
    g = STATE["poses"][i][1]; b = C.actor("bride")["poses"][i][1]
    return Vector(((g.x + b.x) / 2, (g.y + b.y) / 2, 0))


def camera_fn():
    """0～停下：側面跟拍（兩人中點、畫面 70%、dist m）→ 新娘停穩後 pull_s 秒拉遠到 far_dist、看向抬高（大門整扇入鏡）並停住
    → orbit～push 繞到兩人正背後、對準大門中線（胸口高）→ push～ 往門裡推到背後 push_dist（肩高）"""
    tm = STATE["b6_tm"]
    t_st = max(tm["g_still"], tm["b_still"])            # 兩人都停穩才固定、拉遠
    base = BK.side_follow(holds=[(t_st, 99)], handles=HANDLES, partner=lambda i: tuple(C.hips_world("bride"))[:2],   # follow_camera 剛 pose_at(i)：用擺出來的世界座標
                          offset=(0.0, -CAM["dist"], 0.25))
    ms = _mid(int(round((t_st + HANDLES) * FPS)))
    dx = -BK.frame_w(CAM["far_dist"]) * BK.CAP_SHIFT
    far_l = Vector((ms.x + dx, ms.y - CAM["far_dist"], 0.85)); far_a = Vector((ms.x + dx, ms.y, CAM["far_aim_z"]))
    # 2026-10-13 導演端（rough_v16 第 66 秒）：繞到背後對準大門中線時，剪接 col 版面（原片 x 40～100%）裡新娘被切掉左半、右半被前景門框佔掉
    #   → 背後機位也照「兩人中點放畫面 70%」往左平移（同側面跟拍）：兩人落在 45～95%，門框兩根柱子都在畫面外
    bx = ms.x - BK.frame_w(CAM["back_dist"]) * BK.CAP_SHIFT
    back_l = Vector((bx, ms.y - CAM["back_dist"], CAM["back_z"])); back_a = Vector((bx, WALL_Y, CAM["back_aim_z"]))
    push_l = Vector((bx, ms.y - CAM["push_dist"], CAM["push_z"])); push_a = Vector((bx, WALL_Y, CAM["push_z"]))
    s = lambda x: x * x * (3 - 2 * x)

    def f(i):
        t = i / FPS - HANDLES
        l, a = base(i)
        k = s(min(1.0, max(0.0, (t - t_st) / CAM["pull_s"])))
        l, a = l.lerp(far_l, k), a.lerp(far_a, k)
        if t > tm["orbit"]:
            k = s(min(1.0, (t - tm["orbit"]) / P["orbit_s"]))
            arc = Vector((0, -0.6 * math.sin(math.pi * k), 0))
            l, a = far_l.lerp(back_l, k) + arc, far_a.lerp(back_a, k)
        if t > tm["push"]:
            k = s(min(1.0, (t - tm["push"]) / P["push_s"]))
            l, a = back_l.lerp(push_l, k), back_a.lerp(push_a, k)
        return l, a
    return f


def _cam_noface(fn, keep=()):
    """算鏡頭／烤樣張要逐格擺姿勢：網格先關掉顯示（穿衣服的人一格要好幾秒）。
    keep：要記錄位置的物件不能關（2026-10-13 第 1 版：大門、柱子也被關掉 → Blender 不更新它們的矩陣，記下來的一直是第一格：大門從頭開到尾）"""
    keep = {o.name for o in keep}
    meshes = [o for o in STATE["sc"].objects if o.type == "MESH" and not o.hide_viewport and o.name not in keep]
    for o in meshes:
        o.hide_viewport = True
    try:
        return fn()
    finally:
        for o in meshes:
            o.hide_viewport = False


def pillar_place():
    """換景柱子：鏡內第 0 格在鏡頭前 d m、擋住兩人中點；0～exit 秒往左滑到剛好出畫（之後藏起來）"""
    def calc():
        cf = camera_fn(); i0 = int(HANDLES * FPS); l, a = cf(i0)
        fwd = a - l; fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
        dg = _mid(i0) - Vector((l.x, l.y, 0)); k = dg.dot(right) / dg.dot(fwd)
        p = l + fwd * PILLAR["d"] + right * (k * PILLAR["d"]); p.z = 0
        ie = int(round((PILLAR["exit"] + HANDLES) * FPS)); l2, a2 = cf(ie); f2 = a2 - l2; f2.z = 0; f2.normalize(); r2 = Vector((f2.y, -f2.x, 0))
        q = Vector((p.x, p.y, 0)) - Vector((l2.x, l2.y, 0)); d = q.dot(f2)
        edge = 0.5 + (q.dot(r2) + PILLAR["hw"]) / BK.frame_w(d)
        return p, max(0.0, edge * BK.frame_w(d) + 0.02)
    p, slide = _cam_noface(calc)
    STATE["pillar_xy"] = Vector((p.x, p.y, 0)); STATE["pillar_slide"] = slide
    return dict(xy=(round(p.x, 2), round(p.y, 2)), slide=round(slide, 3))


def clip(v=1, size=(960, 540)):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", 35.0)
    for a in (STATE["arm"], C.actor("bride")["arm"]):
        a.animation_data_clear()
    objs = [o for o in (bpy.data.objects.get(n) for n in ("ZA_Pillar", "ZA_DoorL", "ZA_DoorR")) if o]
    for o in objs:
        o.animation_data_clear()
    out = _cam_noface(lambda: SP.bake(objects=objs, camera_fn=camera_fn()), keep=objs)
    path = SP.save("b6_formal")
    cmd = SP.render_clip("b6_formal", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + "/formal_v%d.mp4" % v, size=size)
    return dict(out, path=path, cmd=cmd)


def run():
    t0 = time.time(); r = {}
    if "bride" not in C.cast():
        setup()
    r.update(build()); r["hold"] = breathe_hold()
    STATE["stats"] = Z.stats(); r["groom_stats"] = STATE["stats"]["summary"]
    with C.as_actor("bride"):
        STATE["stats"] = Z.stats(); r["bride_stats"] = STATE["stats"]["summary"]
    if not STATE.get("outfit_objs"):
        r["dress"] = dress()
    r["scene"] = scene_set(); r["sec"] = round(time.time() - t0, 1)
    return r


def cleanup():
    return Z.cleanup(SCENE)
