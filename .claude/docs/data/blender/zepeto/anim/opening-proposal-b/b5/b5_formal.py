# B5 正式版（2026-10-13 導演端：B4～B6 正式版一開始就穿禮服做；新娘看前方）。攝影區最後一站：拍照背板前自拍。
# 接 B4 正式版最後一格（b4/end_state_formal.json：新郎 (10.88, −0.58)、新娘在他靠鏡頭那側後面 0.66 m），側面捲動不切：
#   新郎走到背板前停下 → 跨一步右轉面向鏡頭、拿出手機（「啵」：縮放彈出）；
#   新娘從他靠鏡頭那側超過去、停在他左邊（畫面右邊）並排 → 跨一步右轉面向鏡頭；
#   新郎右手把手機舉到斜前上方（螢幕朝兩人的臉）、左手輕扶新娘背後；兩人身體、頭互相靠過去（頭靠頭）、笑；新娘外側的左手比 YA；
#   新郎拇指點一下螢幕（快門）→ 放下手機（收掉）、兩人跨一步左轉回前方起步，往大門走（接 B6 的門框遮擋）。
# 動作（Mixamo 原樣）：新郎 Walking → Stop Walking → Standing Idle（跨步轉身用 F.pivot_turn）→ Start Walking → Walking；
#   新娘 Female Walk → Female Stop Walking → Female Idle → Female Start Walking → Female Walk（走路、起步放慢 0.854，和新郎並排）。
# 站位（場景端 venue_photo_zone.py，場景座標 → 動畫座標 x −0.654）：背板中心 x 12.146、正面 y 0.16；兩人走 y −0.58（新郎）。
#   新娘裙擺半徑 0.335 → 並排時骨盆隔 PB["gap"]；她超過新郎時在他靠鏡頭那側 0.52 m（同 B4），超過以後才往裡收（深度方向，側面鏡頭幾乎看不出）。
# 姿勢參考：
#   情侶自拍：手機舉在斜前上方、手臂伸直，鏡頭略高於眼睛（俯拍顯瘦）；兩人頭靠頭、身體往對方傾（tips.photography／couple selfie poses）；
#   比 YA：手掌朝鏡頭（手機）、食指中指張開成 V、在臉旁邊（smartphone selfie peace sign）；
#   手扶背：掌心貼在對方腰背、手指朝她外側（side hug）。
# 用法（MCP）：
#   # BODY=groom,bride
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b5"); import b5_formal as B5F; print(B5F.run())
import bpy, os, sys, math, json, time
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
import zanim_fix as F
import zanim_cast as C
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE, PREFIX = "B5_FORMAL", "ZA_"
FPS = 30
HANDLES = 1.0
B4_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b4/end_state_formal.json"
OUT_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b5/end_state_formal.json"
G_CLIPS = ("male_standard_walk", "male_stop_walk", "standing_idle", "male_start_walk")
B_CLIPS = ("female_walk", "female_stop_walk", "female_idle", "female_start_walk")
STOP = Vector((11.88, -0.58, 0.0))                # 新郎停穩的骨盆（目標；實際照走路整圈挑最接近的，差多少用漸進平移補）
P = dict(X=9, stop_b=66, settle=0.3, b_settle=0.6, start_a=10, go_len=1.2, pivot_s=0.9, pivot_lift=0.035, x_tol=0.25,
         g_lag=0.4, g_go_face=(-20.0, -8.0), phone=0.2, raise_s=0.6, lean_d=0.3, lean_s=0.5, shutter=2.0, hold_after=0.7, down_s=0.5, go_d=0.25)
# g_lag：新郎比新娘晚幾秒起步、g_go_face：(起步, 走路) 新郎面向往鏡頭側偏幾度
#   （2026-10-13 第 1 試：兩人同時起步、同一條線 → 新郎走在禮服後面，裙子重疊 27 cm；改成新娘先走、新郎往鏡頭側斜出去，走路時照舊新郎靠鏡頭）
# b_settle：新娘停穩後幾秒才轉身（0.3 時 Female Stop Walking 最後一步還在落地、轉身就開始 → 右腳每格滑 2 cm）
# x_tol：停點 x 可以離 STOP 多遠不補（背板寬，站偏一點沒關係）；
# 以 t_pair（兩人都轉好面向鏡頭）為準：phone：新郎轉好後幾秒手機彈出；raise_s：舉起幾秒；lean_d／lean_s：t_pair 後幾秒開始靠、靠幾秒；
# shutter：t_pair 後幾秒按快門；hold_after：按完再停幾秒；down_s：放下幾秒；go_d：放下後幾秒跨步轉回前方
PB = dict(walk_k=0.854, gap=0.6, lag=0.9, lean=(9.0, 8.0), tilt=(17.0, 16.0), back_off=0.17, back_dz=0.08, arc_r=0.42,
          skirt=dict(margin=0.015, elbow_k=2.0, max_deg=40))
# gap：並排時兩人骨盆隔幾 m（裙擺半徑 0.335＋新郎腳）；lag：新娘比新郎晚幾秒停穩；lean：(新郎, 新娘) 上身往對方傾幾度；tilt：頭再往對方歪幾度；
# back_off：新郎左手貼在新娘腰背、離她脊椎幾 m；back_dz：再往上幾 m（腰以下裙子往外撐）；arc_r：手繞過去時離她中心至少幾 m（從裙子上方繞）
# 2026-10-13 第 1 版禮服實量（網格）：gap 0.52 時新郎垂下的左手離她中心 0.30 m、在裙子裡（3.7 秒 2.9 cm）；
#   手直線伸到她背後會穿過裙子（5.3 秒 5.8 cm）；扶的位置在裙腰、陷進 1.3 cm → gap 0.6（傾、歪多一點維持頭靠頭）、手先往外往上繞、扶高一點


def setup():
    m = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b5")[1]
    Z.load_clips(G_CLIPS)
    C.add_actor("bride", "bride")
    with C.as_actor("bride"):
        Z.load_clips(B_CLIPS)
    return m


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


def _place(tgt, segs, end):
    """第 HANDLES 秒（＝B4 最後一格）骨盆、面向對上 end"""
    want = Vector(end["hips"][:2]); xy = Vector((want.x - 0.7, want.y)); yaw = end["yaw"]
    for _ in range(5):
        seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS); seq.place(0.0, tuple(xy), yaw)
        R, h, _y = seq.at(HANDLES)
        yaw += end["yaw"] - _yaw(tgt, R); xy += want - h.xy
    seq = mr.Sequence(tgt, segs, blend=P["X"] / FPS); seq.place(0.0, tuple(xy), yaw)
    return seq


def _drift(poses, i_a, i_b, d):
    """第 i_a～i_b 格之間把骨盆（整個人）漸進平移 d（smoothstep），之後維持；i_a 以前不動（接 B4）"""
    out = []
    for i, (R, h) in enumerate(poses):
        k = 0.0 if i <= i_a else (1.0 if i >= i_b else (i - i_a) / (i_b - i_a)); k = k * k * (3 - 2 * k)
        out.append((R, h + d * k))
    return out


def _walk_segs(tgt, clips, end, L1x, k=None):
    """走路（接 B4 相位）→ 停下 → 站著（face 0＝面向鏡頭）→ 起步（at 之後補）→ 走路"""
    X = P["X"]
    W, ST, ID, SW = clips
    if k:
        W = F.retime(W, k); SW = F.retime(SW, k)
    wn = W["n"] - 1
    a0 = int(round(end["walk_phase"] - HANDLES * FPS)) % wn
    a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
    a4, b4, _ = F.match_phase(tgt, SW, range(SW["n"] - 30, SW["n"] - 6), W, range(0, wn))
    L1 = L1x + ((a1 + X - (a0 + L1x)) % wn)
    W1 = mr.splice_clip(W, [(a0 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * (L1 // wn + 2))
    W2 = mr.splice_clip(W, [(b4 / FPS, wn / FPS)] + [(0, wn / FPS, 1 / FPS)] * 4)
    return W1, W2, ST, ID, SW, dict(a0=a0, a1=a1, b1=b1, a4=a4, b4=b4, wn=wn, L1=L1)


def plan(key, L1x, t_go=None, t_hold=None):
    """key：groom／bride。t_go：起步（鏡內秒，None＝先排個大概）"""
    end = json.load(open(B4_END))[key]
    names = G_CLIPS if key == "groom" else B_CLIPS
    with (C.as_actor("bride") if key == "bride" else _nullctx()):
        tgt = STATE["tgt"]; X = P["X"]
        W1, W2, ST, ID, SW, cut = _walk_segs(tgt, [L._CL[n] for n in names], end, L1x, PB["walk_k"] if key == "bride" else None)
        stop_b = P["stop_b"] if key == "groom" else ST["n"] - 1
        hold = t_hold if t_hold is not None else 4.0
        segs = [mr.Seg(W1, 0, cut["L1"], name="走到背板前（%s）" % ("Walking" if key == "groom" else "Female Walk")),
                mr.Seg(ST, cut["b1"], stop_b, hold=P["settle"] if key == "groom" else P["b_settle"], name="停下（%s Stop Walking，播到停穩）" % ("" if key == "groom" else "Female")),
                mr.Seg(ID, 0, min(ID["n"] - 1, int((hold + 1.0) * FPS)), hold=max(0.0, hold + 1.0 - (ID["n"] - 1) / FPS), face=0.0,
                       name="跨一步右轉面向鏡頭 → 站著自拍（%s Idle）" % ("Standing" if key == "groom" else "Female"))]
        kw = dict(at=t_go + HANDLES) if t_go is not None else {}
        gf = P["g_go_face"] if key == "groom" else (0.0, 0.0)
        segs += [mr.Seg(SW, P["start_a"] if key == "groom" else 3, cut["a4"] + X, face=90.0 + gf[0], name="跨一步左轉回前方 → 起步（Start Walking）", **kw),
                 mr.Seg(W2, 0, int(2.5 * FPS), face=90.0 + gf[1], name="走向大門（Walking）")]
        seq = _place(tgt, segs, end)
    return segs, seq, cut


def _pose_list(key, seq, n):
    with (C.as_actor("bride") if key == "bride" else _nullctx()):
        return [(dict(R), h.copy()) for R, h, _y in (seq.at(min(i / FPS, seq.start + seq.dur)) for i in range(n))]


def build():
    """兩人排段 → 停點（整圈挑最接近、差的漸進平移）→ 兩次跨步轉身 → 貼地鎖腳 → 新娘頭看前方、手臂避開裙子"""
    i0 = int(HANDLES * FPS)
    # 新郎：停點 x 最接近 STOP 的走路長度
    best = None
    for L1x in range(0, 37 * 4, 37):                    # 走路長度只能整圈（相位要配停下那支）→ 一圈一圈試
        segs, seq, cut = plan("groom", L1x)
        si = _still([seq.at(i / FPS)[:2] for i in range(i0, i0 + 150)], 0) + i0
        hx = seq.at(si / FPS)[1].x
        if hx > STOP.x + 0.6:
            break
        if best is None or abs(hx - STOP.x) < best[0]:
            best = (abs(hx - STOP.x), L1x)
    g_L1x = best[1]
    segs, seq, cut = plan("groom", g_L1x)
    n_tmp = int(12 * FPS)
    pg = _pose_list("groom", seq, n_tmp); gi = _still(pg, int(round(seq.T[1][0] * FPS)))
    g_still = gi / FPS - HANDLES; g_turn_end = g_still + P["pivot_s"]
    # 新娘：停點＝新郎停點往 +X gap（面向鏡頭時她在他左邊＝畫面右邊），比他晚 lag 秒左右停穩
    gs = pg[gi][1]; goal_b = Vector((gs.x + PB["gap"], STOP.y, 0))
    bbest = None
    for L1x in range(0, 41 * 5, 41):
        _s, bseq, _c = plan("bride", L1x)
        with C.as_actor("bride"):
            bp = [bseq.at(i / FPS)[:2] for i in range(i0, i0 + 240)]
        bi = _still(bp, int(round(bseq.T[1][0] * FPS)) - i0) + i0
        e = abs(bseq.at(bi / FPS)[1].x - goal_b.x) + 0.5 * abs(bi / FPS - HANDLES - (g_still + PB["lag"]))
        if bbest is None or e < bbest[0]:
            bbest = (e, L1x)
    b_L1x = bbest[1]
    _s, bseq, bcut = plan("bride", b_L1x)
    pb = _pose_list("bride", bseq, n_tmp); bi = _still(pb, int(round(bseq.T[1][0] * FPS)))
    b_still = bi / FPS - HANDLES; b_turn_end = b_still + P["pivot_s"]
    t_pair = max(g_turn_end, b_turn_end)
    t_phone = g_turn_end + P["phone"]
    t_shut = t_pair + P["shutter"]; t_down = t_shut + P["hold_after"]; t_go = t_down + P["down_s"] + P["go_d"]
    tm = dict(g_still=g_still, g_turn_end=g_turn_end, b_still=b_still, b_turn_end=b_turn_end, pair=t_pair, phone=t_phone,
              raise_end=max(t_pair, t_phone + P["raise_s"]), lean=t_pair + P["lean_d"], shutter=t_shut, down=t_down, phone_off=t_down + P["down_s"],
              go=t_go, g_go=t_go + P["g_lag"], end=t_go + P["g_lag"] + P["pivot_s"] + P["go_len"])
    dur = tm["end"]; n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    out = {}
    for key, L1x, still, t_end in (("groom", g_L1x, g_still, g_turn_end), ("bride", b_L1x, b_still, b_turn_end)):
        tg_ = t_go + (P["g_lag"] if key == "groom" else 0.0)
        segs, seq, cut = plan(key, L1x, t_go=tg_, t_hold=tg_ - still)
        poses = _pose_list(key, seq, n)
        si = int(round((still + HANDLES) * FPS))
        want = STOP if key == "groom" else Vector((STOP.x + PB["gap"], STOP.y, 0))
        if key == "groom":
            dx = poses[si][1].x - STOP.x; want = Vector((STOP.x + max(-P["x_tol"], min(P["x_tol"], dx)), STOP.y, 0))
        else:
            gx = STATE["poses"][int(round((tm["g_still"] + HANDLES) * FPS))][1].x
            want = Vector((gx + PB["gap"], STOP.y, 0))
        d = want - poses[si][1]; d.z = 0
        # 平移：x 整段走路漸進補；新娘的 y（往裡收）等她超過新郎以後才收（最後 0.9 秒）
        if key == "groom":
            poses = _drift(poses, i0, si, d)
        else:
            poses = _drift(poses, i0, si, Vector((d.x, 0, 0)))
            poses = _drift(poses, si - int(0.9 * FPS), si, Vector((0, d.y, 0)))
        with (C.as_actor("bride") if key == "bride" else _nullctx()):
            tgt = STATE["tgt"]; X = P["X"]; nt = int(round(P["pivot_s"] * FPS))
            i1 = int(round(seq.T[2][0] * FPS)) - 2; i2 = int(round(seq.T[3][0] * FPS)) + X
            piv = lambda q: F.pivot_turn(tgt, F.pivot_turn(tgt, q, i1, i1 + nt, first="R", lift=P["pivot_lift"], sign=-1),
                                         i2 - nt, i2, first="L", lift=P["pivot_lift"], sign=1)
            poses = piv(poses)
            pts = L.sole_points(STATE["arm"])
            poses, _off = F.ground(tgt, poses, pts)
            poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9, z_on=0.015, gap_max=25)
            B0 = _b0()
            poses = B0._pin_foot_turn(tgt, poses, pts)
            poses = B0.zero_slide(tgt, poses, pts, 0, n - 1)
            poses = piv(poses)                             # 鎖腳後再做一次（鎖腳會釘住要抬起的腳）
            poses = [(mr.gesture(tgt, mr.gesture(tgt, R, "L", "relaxed"), "R", "relaxed"), h) for R, h in poses]
            info = dict(L1x=L1x, still=round(still, 2), still_xy=(round(poses[si][1].x, 3), round(poses[si][1].y, 3)), drift=(round(d.x, 3), round(d.y, 3)),
                        pivots=((round(i1 / FPS - HANDLES, 2), round((i1 + nt) / FPS - HANDLES, 2)), (round((i2 - nt) / FPS - HANDLES, 2), round(i2 / FPS - HANDLES, 2))))
            if key == "bride":
                poses, info["head_up_max"] = F.level_head(tgt, poses)   # 全片通用：新娘頭看前方
                poses, info["skirt_arms"] = F.skirt_arms(tgt, poses, **PB["skirt"])
            STATE.update(poses=poses, seq=seq, segs=[(round(seq.T[k][0], 2), round(s.dur, 2), s.name) for k, s in enumerate(segs)])
            if key == "groom":
                STATE.update(dur=dur, b5_tm=tm, marks=dict(still=g_still, go=t_go, end=dur), walk_cut=cut)
            else:
                STATE["b_cut"] = cut
        out[key] = info
    out["tm"] = {k: round(v, 2) for k, v in tm.items()}
    return out


class _nullctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# ════════ 自拍：靠過去、頭靠頭、舉手機、扶背、比 YA、按快門 ════════
def _frame(tgt, R):
    q = R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()
    fw = q @ Vector((0, -1, 0)); fw.z = 0; fw.normalize()
    return fw, Vector((fw.y, -fw.x, 0))                  # 前方、右手方向


def _lean(tgt, R, h, toward, deg_body, deg_head, w):
    """上身（脊椎以上全部）往 toward 傾 deg_body，脖子＋頭再歪 deg_head（骨頭存的是世界旋轉：子骨頭要一起轉才不會脫節）"""
    if w <= 0:
        return R
    p = Vector((toward.x, toward.y, 0)).normalized(); ax = Vector((0, 0, 1)).cross(p).normalized()
    R = dict(R)
    qb = Quaternion(ax, math.radians(deg_body) * w)
    for b in ["J_Bip_C_Spine"] + F._chain(tgt, "J_Bip_C_Spine"):
        R[b] = qb @ R[b]
    qh = Quaternion(ax, math.radians(deg_head) * w)
    for b in ["J_Bip_C_Neck"] + F._chain(tgt, "J_Bip_C_Neck"):
        R[b] = qh @ R[b]
    return R


PHONE_W, PHONE_H = 0.078 * 0.125 / 0.155, 0.125      # phone_zp：寬、高（原點在底部中心、螢幕朝 −Y、長邊沿 +Z）
SEL = dict(fw=0.36, up=0.24, out=0.22, tilt=20.0)     # 手機中心：右肩往前 fw、往上 up、往外 out（b5_shot 量過：放臉前會擋臉、再高會出畫）


def selfie():
    from zanim_hand import hand_quat, put_hand_pole
    tm = STATE["b5_tm"]; gst = STATE; bst = C.actor("bride"); tg, tb = gst["tgt"], bst["tgt"]; n = len(gst["poses"])
    plen_g = 0.6 * (tg.rest_h["J_Bip_R_Middle1"] - tg.rest_h["J_Bip_R_Hand"]).length
    gout, bout, phone = [], [], []
    for i in range(n):
        t = i / FPS - HANDLES
        Rg, hg = gst["poses"][i]; Rb, hb = bst["poses"][i]
        wl = _sm(t, tm["lean"], tm["lean"] + P["lean_s"]) * (1 - _sm(t, tm["down"], tm["down"] + P["down_s"]))
        # 1) 靠過去（先傾，手臂 IK 用傾過後的肩膀）
        to_b = hb - hg; to_g = hg - hb
        Rg = _lean(tg, Rg, hg, to_b, PB["lean"][0], PB["tilt"][0], wl)
        Rb = _lean(tb, Rb, hb, to_g, PB["lean"][1], PB["tilt"][1], wl)
        Hg = tg.fk(Rg, hg); Hb = tb.fk(Rb, hb)
        fw, rt = _frame(tg, Rg); fwb, rtb = _frame(tb, Rb)
        # 2) 新郎右手舉手機：彈出（phone）→ 舉起（raise_end）→ 按快門 → 放下（down～phone_off）
        wh = _sm(t, tm["phone"] - 0.3, tm["phone"]) * (1 - _sm(t, tm["phone_off"], tm["phone_off"] + 0.3))   # 右手離開原片的權重
        k_up = _sm(t, tm["phone"] + 0.15, tm["raise_end"]) * (1 - _sm(t, tm["down"], tm["phone_off"]))       # 胸前 → 舉高 → 放回胸前
        M_ph = None
        if wh > 0:
            heads = (Hg["J_Bip_C_Head"] + Hb["J_Bip_C_Head"]) / 2 + Vector((0, 0, 0.08))
            hold = Hg["J_Bip_R_UpperArm"] + fw * 0.30 - Vector((0, 0, 0.25)) + rt * 0.05     # 剛拿出來：胸前偏右、低
            up_ = Hg["J_Bip_R_UpperArm"] + fw * SEL["fw"] + Vector((0, 0, SEL["up"])) + rt * SEL["out"]
            c = hold.lerp(up_, k_up)
            nrm = (heads - c).normalized()                  # 螢幕法線朝兩人的臉
            u = Vector((0, 0, 1)) - nrm * nrm.z; u.normalize()
            wdt = u.cross(nrm).normalized()
            d = (u * math.cos(math.radians(SEL["tilt"])) + rt * math.sin(math.radians(SEL["tilt"]))).normalized()   # 手指沿手機長邊、往外斜一點
            q = hand_quat(tg, "R", d, nrm)                  # 掌心貼手機背面、朝兩人
            M = Matrix.Translation(c - nrm * 0.022 - d * plen_g) @ q.to_matrix().to_4x4()
            Rg = put_hand_pole(tg, Rg, hg, "R", M, wh, (rt + Vector((0, 0, -1))).normalized(), 0.6)
            tap = _sm(t, tm["shutter"] - 0.08, tm["shutter"]) * (1 - _sm(t, tm["shutter"] + 0.05, tm["shutter"] + 0.15))
            Rg = mr.gesture(tg, Rg, "R", "hold", wh)
            if tap > 0:                                     # 拇指點一下螢幕
                for f_ in ("J_Bip_R_Thumb2", "J_Bip_R_Thumb3"):
                    ax_ = (Rg[f_] @ tg.rest_q[f_].inverted()) @ Vector((0, 0, 1))
                    Rg[f_] = Quaternion(ax_, math.radians(25) * tap) @ Rg[f_]
            # 手機黏在手上：照實際手的位置，用設計時的相對關係擺
            Hg2 = tg.fk(Rg, hg); Mh = Matrix.Translation(Hg2["J_Bip_R_Hand"]) @ (Rg["J_Bip_R_Hand"] @ tg.rest_q["J_Bip_R_Hand"].inverted()).to_matrix().to_4x4()
            Mdes = Matrix.Translation(c - nrm * 0.022 - d * plen_g) @ q.to_matrix().to_4x4()
            Pm = Matrix((wdt, -nrm, u)).transposed().to_4x4(); Pm.translation = c - u * (PHONE_H / 2)
            M_ph = Mh @ (Matrix(Mdes).inverted() @ Pm)
            pop = _sm(t, tm["phone"], tm["phone"] + 0.1) * (1.0 + 0.15 * (1 - _sm(t, tm["phone"] + 0.1, tm["phone"] + 0.22)))
            pop *= 1 - _sm(t, tm["phone_off"] - 0.12, tm["phone_off"])
            M_ph = M_ph @ Matrix.Scale(max(1e-4, pop), 4) if tm["phone"] <= t <= tm["phone_off"] else None
        phone.append(M_ph)
        # 3) 新郎左手扶新娘腰背
        wbk = wl
        if wbk > 0:
            back = Hb["J_Bip_C_Spine"] - fwb * PB["back_off"] + Vector((0, 0, PB["back_dz"]))
            side_g = (hg - hb); side_g.z = 0; side_g.normalize()
            touch = back + side_g * 0.06
            d = (-side_g); palm = fwb                        # 手指朝她外側、掌心貼她背
            q = hand_quat(tg, "L", d, palm)
            plen = 0.6 * (tg.rest_h["J_Bip_L_Middle1"] - tg.rest_h["J_Bip_L_Hand"]).length
            # 路線：垂下的手 → 往外往上（離她中心至少 arc_r、高到扶的高度）→ 繞到背後貼上（從裙子上方繞，不直線穿過裙子）
            p0 = tg.fk(Rg, hg)["J_Bip_L_Middle1"]; c0 = Vector((hb.x, hb.y, 0))
            def outward(p, r):
                v = Vector((p.x, p.y, 0)) - c0
                return p if v.length >= r else Vector((c0.x, c0.y, p.z)) + v.normalized() * r
            p_mid = outward(Vector((p0.x, p0.y, touch.z + 0.03)), PB["arc_r"])
            if wbk < 0.5:
                pt = outward(p0.lerp(p_mid, wbk / 0.5), PB["arc_r"])
            else:
                k2 = (wbk - 0.5) / 0.5; pt = p_mid.lerp(touch, k2)
                pt = outward(pt, PB["arc_r"] * (1 - k2) + 0.0 * k2)
            M = Matrix.Translation(pt - d * plen - palm * 0.02 * min(1.0, wbk * 2)) @ q.to_matrix().to_4x4()
            Rg = put_hand_pole(tg, Rg, hg, "L", M, min(1.0, wbk * 3), (-fw + Vector((0, 0, -1))).normalized(), 0.6)
            Rg = mr.gesture(tg, Rg, "L", "relaxed", wbk)
        # 4) 新娘外側的左手比 YA（掌心朝手機、在臉旁邊）
        wy = _sm(t, tm["lean"] + 0.2, tm["lean"] + 0.6) * (1 - _sm(t, tm["down"], tm["down"] + 0.4))
        if wy > 0:
            lf = -rtb
            goal = Hb["J_Bip_C_Head"] + lf * 0.17 + fwb * 0.07 + Vector((0, 0, 0.0))
            d = (Vector((0, 0, 1)) + lf * 0.25).normalized(); palm = fwb
            q = hand_quat(tb, "L", d, palm)
            M = Matrix.Translation(goal - d * 0.05) @ q.to_matrix().to_4x4()
            Rb = put_hand_pole(tb, Rb, hb, "L", M, wy, (lf + Vector((0, 0, -1))).normalized(), 0.6)
            Rb = mr.gesture(tb, Rb, "L", "peace", wy)
        gout.append((Rg, hg)); bout.append((Rb, hb))
    gst["poses"] = gout; bst["poses"] = bout; STATE["phone_M"] = phone
    # 量：兩人頭的距離（頭骨）、新郎左手掌心離新娘脊椎
    i_m = int(round(((tm["lean"] + P["lean_s"] + tm["shutter"]) / 2 + HANDLES) * FPS))
    Hg = tg.fk(*gout[i_m]); Hb = tb.fk(*bout[i_m])
    return dict(head_d=round((Hg["J_Bip_C_Head"] - Hb["J_Bip_C_Head"]).length, 3), at=round(i_m / FPS - HANDLES, 2))


# ════════ 表情 ════════
FACE_SMILE = dict(mouthSmileLeft=0.8, mouthSmileRight=0.8, cheekSquintLeft=0.35, cheekSquintRight=0.35, eyeSquintLeft=0.25, eyeSquintRight=0.25)


def face_vals(t):
    tm = STATE["b5_tm"]
    w = _sm(t, tm["pair"], tm["pair"] + 0.5) * (1 - _sm(t, tm["down"] + 0.2, tm["go"] + 0.3))
    return ({k: v * w for k, v in FACE_SMILE.items()}, {k: v * w for k, v in FACE_SMILE.items()})


def _faces():
    return [STATE["arm"], C.actor("bride")["arm"]]


def _face_hook(i):
    for arm, v in zip(_faces(), face_vals(i / FPS - HANDLES)):
        hm = L.head_mesh(arm); kb = hm.data.shape_keys if hm else None
        if kb is None:
            continue
        for k, x in v.items():
            if k in kb.key_blocks:
                kb.key_blocks[k].value = x


def bake_face():
    import zanim_sample as SP
    n = len(STATE["poses"]); V = [face_vals(i / FPS - HANDLES) for i in range(n)]
    for j, (who, arm) in enumerate(zip(("groom", "bride"), _faces())):
        hm = L.head_mesh(arm); key = hm.data.shape_keys if hm else None
        if key is None:
            continue
        ad = key.animation_data_create(); act = bpy.data.actions.get("SAMPLE_B5Face_" + who) or bpy.data.actions.new("SAMPLE_B5Face_" + who); ad.action = act
        for k in V[0][j].keys():
            if k in key.key_blocks:
                SP._put(act, key, 'key_blocks["%s"].value' % k, 0, [V[i][j][k] for i in range(n)])
    return True


# ════════ 衣服、場景、手機、鏡頭、短片 ════════
OUTFIT_G = "groom-beige-3piece"
OUTFIT_B = "bride-blush-ballgown"
PHONE_OBJ = "ZA_Phone"
CAM = dict(dist=3.6, push=0.10, chest_dz=0.15, hold_d=0.2)   # 停下自拍：鏡頭固定、慢慢推近 push、抬高 chest_dz（中景、胸口高）；dist 同 B3、B4


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


def _phone_hook(i):
    ob = bpy.data.objects.get(PHONE_OBJ); Ms = STATE.get("phone_M")
    if ob is None or not Ms:
        return
    M = Ms[min(i, len(Ms) - 1)]
    if M is None:
        ob.matrix_world = Matrix.Translation(Vector((0, 0, -5))) @ Matrix.Scale(1e-4, 4)
    else:
        ob.matrix_world = M


def scene_set():
    vo = json.load(open(BK.VENUE_OFFSET)); off = (vo["dx"], vo["dy"], 0.0)
    objs = {}
    for key in ("Scene_VenueCorridor", "Scene_VenuePhotoZone", "Scene_VenueFoyer"):
        old = bpy.data.collections.get("ZP_" + key)
        if old is not None and old.name in Z.studio_col().children:
            objs.update({o.name: o for o in old.all_objects})
        else:
            objs.update(BK.venue(key, off))
    STATE["sc"].view_layers[0].update()
    hid = []
    for n_, o in objs.items():                            # 走廊的近景換景柱子（y＜−1）這一鏡用不到
        if n_.startswith("I_ZP_pillar") and o.matrix_world.translation.y < -1.0:
            o.hide_render = o.hide_viewport = True; hid.append(n_)
    if bpy.data.objects.get(PHONE_OBJ) is None:
        BK.props_api()["place_prop"]("phone_zp", name=PHONE_OBJ, parent=Z.studio_col())
    for hk in (_phone_hook, _face_hook):
        if hk not in Z.POSE_HOOKS:
            Z.POSE_HOOKS.append(hk)
    door = next((o for n_, o in objs.items() if n_.startswith("I_ZP_door_frame")), None)
    bd = next((o for n_, o in objs.items() if "backdrop" in n_), None)
    return dict(offset=off, hidden=hid, n=len(objs), door=tuple(round(v, 2) for v in door.matrix_world.translation) if door else None,
                backdrop=tuple(round(v, 2) for v in bd.matrix_world.translation) if bd else None)


def camera_fn():
    """側面跟拍（兩人中點、畫面 70%、離 dist m）；兩人都轉好前 hold_d 秒起固定、慢慢推近 push＋抬高（中景、胸口高）；起步後 0.6 秒拉回、追上"""
    tm = STATE["b5_tm"]; arm = STATE["arm"]

    def partner(i):
        g = arm.matrix_world @ arm.pose.bones["J_Bip_C_Hips"].head; b = Vector(tuple(C.hips_world("bride")))
        return (b.x, b.y)                                 # side_follow 自己取兩人中點
    a0 = tm["b_still"] - CAM["hold_d"]
    base = BK.side_follow(holds=[(a0, tm["go"])], handles=HANDLES, partner=partner, offset=(0.0, -CAM["dist"], 0.25))
    i0, i1 = int(round((a0 + HANDLES) * FPS)), int(round((tm["go"] + HANDLES) * FPS))

    def f(i):
        l, a = base(i)
        if i0 < i:
            k = min(1.0, (i - i0) / max(1, i1 - i0)) if i <= i1 else max(0.0, 1 - (i - i1) / 18)
            k = k * k * (3 - 2 * k)
            up = Vector((0, 0, CAM["chest_dz"] * k))
            l = l.lerp(a, CAM["push"] * k) + up; a = a + up
        return l, a
    return f


def clip(v=1, size=(960, 540)):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", 35.0)
    for a in _faces():
        a.animation_data_clear()
        hm = L.head_mesh(a); hk = hm.data.shape_keys if hm else None
        if hk is not None:
            hk.animation_data_clear()
    objs = [o for o in (bpy.data.objects.get(PHONE_OBJ),) if o]
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
    path = SP.save("b5_formal")
    cmd = SP.render_clip("b5_formal", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + "/formal_v%d.mp4" % v, size=size)
    return dict(out, path=path, cmd=cmd)


def run():
    t0 = time.time(); r = {}
    if "bride" not in C.cast():
        setup()
    r.update(build()); r["selfie"] = selfie()
    STATE["stats"] = Z.stats(); r["groom_stats"] = STATE["stats"]["summary"]
    with C.as_actor("bride"):
        STATE["stats"] = Z.stats(); r["bride_stats"] = STATE["stats"]["summary"]
    if not STATE.get("outfit_objs"):
        r["dress"] = dress()
    r["scene"] = scene_set(); r["sec"] = round(time.time() - t0, 1)
    return r


def end_state(path=OUT_END):
    """鏡內最後一格兩人的骨盆、面向、走路相位（B6 開頭照這個接）"""
    i = int(round((STATE["dur"] + HANDLES) * FPS)); out = {}
    for key, st, cut, clip_ in (("groom", STATE, STATE["walk_cut"], "male_standard_walk"), ("bride", C.actor("bride"), STATE["b_cut"], "female_walk")):
        R, h = st["poses"][i]; t_w = st["seq"].T[-1][0]
        with (C.as_actor("bride") if key == "bride" else _nullctx()):
            yaw = _yaw(STATE["tgt"], R)
        out[key] = dict(hips=[round(x, 3) for x in h], yaw=round(yaw, 2), walk_phase=round((cut["b4"] + (i / FPS - t_w) * FPS) % cut["wn"], 1), wn=cut["wn"], clip=clip_)
    out["bride"]["walk_k"] = PB["walk_k"]
    d = dict(what="B5 正式版鏡內最後一格（B6 開頭照這個接）", t_end=round(STATE["dur"], 3), **out,
             holding="無；新娘在新郎%s（y 差 %.2f m）" % ("靠鏡頭那側" if out["bride"]["hips"][1] < out["groom"]["hips"][1] else "遠側", out["bride"]["hips"][1] - out["groom"]["hips"][1]))
    json.dump(d, open(path, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return d


def cleanup():
    return Z.cleanup(SCENE)
