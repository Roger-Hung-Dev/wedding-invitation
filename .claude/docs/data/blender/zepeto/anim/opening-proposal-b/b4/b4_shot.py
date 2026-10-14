# B4（開場影片提案 B）：攝影區。柱子擦過換景 → 兩人並肩走來、停下 → 轉身約 45° 面向蹲著拍照的攝影師（新娘往前一步換到新郎靠鏡頭那一側並排、手輕搭新郎手肘內側）→
# 新郎整理領結、抬下巴；攝影師 3.8 秒按快門、4.0 秒放下相機比讚 → 兩人挽著手起步往右（接 B5）。
# 走位版（2026-10-12）：場景用素材庫真的走廊＋攝影區（v2 起照場景座標；B3→B4 在柱子後面切，不受走廊改距離影響）；
# 新娘、攝影師用膠囊替身（攝影師蹲著＝矮膠囊），相機用素材庫 dslr；不做挽手、捏領結、相機握法、檢查、確認頁、定案。
# 動作（本機沒有蹲拍、挽手、整理領結的 Mixamo，先用現有的拼）：
#   male_standard_walk（接 B3 的相位）→ male_stop_walk → turn_right_90 前段（轉約 45° 面向攝影師）→ look_around（站著）
#   → male_start_walk（鎖住往 +X）→ male_standard_walk；整理領結＝右手臂 IK 到領口
# 座標：場景座標（角色走 y＝0 往 +X、鏡頭 y＝-3、牆 y＝0.75）。兩人停在 x≈7.4（場景端建議），攝影師在前方偏右。
import math, os, json
import bpy
from mathutils import Vector
import zanim as Z
import zanim_fix as F
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
SCENE, PREFIX = "ANIM_B4", "ZA_"
FPS = 30
HANDLES = 1.0
B3_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b3/end_state.json"
PROPS_PY = r"D:/SideProject/wedding-invitation/.claude/docs/data/blender/library/props-zepeto/use_props.py"
P = dict(X=9, walk_s=1.4,   # v2：1.0 → 1.4，鏡頭要多走 0.4 m 才能把換景柱子帶出畫面
         stop_b=66, turn=(0, 40), idle=(20, 74), start_a=10, face_sw=-7.0, face_w=-3.0,   # 第 2 輪（以動作流暢為主）：停下播到停穩、起步從靜止開始
         settle=0.3, idle2=(20, 60), idle_hold=0.4, go_len=2.6,   # 停穩後停幾秒才轉向、站著再播一次安靜段（look_around 74 格後會轉身）、最後停住幾秒、起步後幾秒切到 B5
         tie=(0.3, 1.5), shutter_d=2.0, down_d=0.4,             # 站著開始後幾秒整理領結、幾秒按快門；按完幾秒放下相機比讚
         stop_x=8.0, line_y=-0.6,   # line_y：攝影區兩人走的線（2026-10-12：y 0 時新娘在遠側會穿進拍照背板（正面 y 0.06）→ 往鏡頭移 0.6 m；B5 接著走）
         side_back=0.45, side_behind=0.4,     # 2026-10-12 v2：場景端建議 7.4，但新娘（新郎左後方 0.4 m）會埋進走廊盡頭的裝飾柱 (6.9, 0.45) → 8.0
         ph_frac=0.95, ph_y=-1.2, ph_h=0.95, mid_hold=0.60, pan_s=0.8,   # 攝影師：畫面 95% 露半身（93% 時新郎的手碰到攝影師邊緣）（第 1 輪 (b)：停下這段兩人中點改放 60%，右邊留給攝影師；pan_s＝60%↔70% 平移秒數）；放 (0.3, -0.75)、(0.25, -1.0) 都會擋住新郎；場景端建議 (8.2, -0.8) 在新郎放畫面 70% 時會出畫（右緣約 x 8.3）
         pillar_d=1.3,
         pair_gap=0.75, swap_s=1.0, swap_arc=0.1)   # swap_arc 0.2 → 0.1：線移到 y -0.6 後，往左繞 0.2 m 裙擺會擦到走廊盡頭的裝飾柱   # 第 1 輪：停下時新娘換到靠鏡頭側並排（骨盆間距 0.75 m：0.6 m 在畫面上裙擺會蓋到新郎的腿）、換邊 0.7 秒、往左繞 0.2 m   # 換景柱子中心離鏡頭 1.3 m（場景原位 0.8 m 太近：寬 0.66 m 的柱子會把整個畫面白掉將近 1 秒）


def setup():
    r = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b4")[1]
    Z.load_clips(("male_standard_walk", "male_stop_walk", "turn_right_90", "look_around", "male_start_walk"))
    return r


def _props():
    g = {"__file__": PROPS_PY}
    exec(open(PROPS_PY, encoding="utf8").read(), g)
    return g


def build():
    tgt = STATE["tgt"]; end = BK.load_end(B3_END)
    W, ST, TR, LA, SW = (L._CL[n] for n in ("male_standard_walk", "male_stop_walk", "turn_right_90", "look_around", "male_start_walk"))
    wn = W["n"] - 1; X = P["X"]
    a0 = int(round(end["phase_frame"] - HANDLES * 30)) % wn
    t1 = (wn - a0) / 30.0; need = HANDLES + P["walk_s"] - (t1 - X / 30)
    _a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
    segs = [mr.Seg(W, a0, wn, name="接 B3 的走路"),
            mr.Seg(W, 0, wn, loops=max(0.05, need * 30 / wn), name="並肩走來"),
            mr.Seg(ST, b1, P["stop_b"], hold=P["settle"], name="停下（Stop Walking 前段）"),
            mr.Seg(TR, *P["turn"], add=True, name="轉向攝影師（Turn Right 90 前段，約 45°）"),
            mr.Seg(LA, *P["idle"], name="站著擺姿勢（Standing Idle）"),
            mr.Seg(LA, *P["idle2"], hold=P["idle_hold"], name="站著（再播一次安靜段）"),
            mr.Seg(SW, P["start_a"], SW["n"] - 1, face=90.0 + P["face_sw"], name="起步（Start Walking 後段）"),
            mr.Seg(W, 0, wn, loops=3, face=90.0 + P["face_w"], name="走路")]
    seq = mr.Sequence(tgt, segs, blend=X / 30)
    seq.place(HANDLES, (0.0, 0.0), 90.0)                  # 先擺：開頭往 +X 走
    idx = {sg.name: k for k, sg in enumerate(segs)}
    T = lambda nm: seq.T[idx[nm]][0] - HANDLES
    stop = T("轉向攝影師（Turn Right 90 前段，約 45°）"); go = T("起步（Start Walking 後段）"); dur = go + P["go_len"]
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    poses = [(dict(R), h.copy()) for R, h, _y in (seq.at(min(i / FPS, seq.dur)) for i in range(n))]
    hs = poses[int(round((stop + HANDLES) * FPS))][1]
    sh = Vector((P["stop_x"] - hs.x, P["line_y"] - hs.y, 0))   # 整條平移：停下的位置＝(stop_x, line_y)
    poses = [(R, h + sh) for R, h in poses]
    pts = L.sole_points(STATE["arm"])
    poses, off = F.ground(tgt, poses, pts)
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9)
    STATE.update(poses=poses, seq=seq, dur=dur, segs=[(round(seq.T[i][0] - HANDLES, 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    look = T("站著擺姿勢（Standing Idle）")
    m = dict(stop=round(stop, 2), look=round(look, 2), go=round(go, 2), tie=(round(look + P["tie"][0], 2), round(look + P["tie"][1], 2)),
             shutter=round(look + P["shutter_d"], 2), ph_down=round(look + P["shutter_d"] + P["down_d"], 2))
    STATE["t_marks"] = m
    _tie(poses)
    # 新郎停下後面向攝影師的角度（量出來，給替身照抄）
    STATE["face_deg"] = BK.yaw_of(BK.hips_fw(poses[int(round((look + 0.3 + HANDLES) * FPS))][0]))
    return dict(dur_s=round(dur, 2), frames=n, marks=m, face_deg=round(STATE["face_deg"], 1),
                ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)), segs=STATE["segs"])


def _w(t, a, b, c, d):
    if t <= a or t >= d:
        return 0.0
    x = (t - a) / (b - a) if t < b else ((d - t) / (d - c) if t > c else 1.0)
    return x * x * (3 - 2 * x)


def _tie(poses):
    """整理領結：右手到領口前（走位版只表達時間與方向）"""
    tgt = STATE["tgt"]; a, b = STATE["t_marks"]["tie"]
    for i, (R, h) in enumerate(poses):
        t = i / FPS - HANDLES
        w = _w(t, a - 0.2, a + 0.2, b - 0.2, b + 0.2)
        if w <= 0:
            continue
        Hd = tgt.fk(R, h); fw = BK.hips_fw(R)
        goal = Hd["J_Bip_C_Neck"] + fw * 0.09 + Vector((0, 0, -0.03))
        R = mr.arm_ik(tgt, R, h, "R", Hd["J_Bip_R_Hand"].lerp(goal, w), Vector((0.3, 0, -1)))
        poses[i] = (R, h)


def _near_side(g):
    """停下面對攝影師時新娘的位置：新郎靠鏡頭那一側、和新郎並排（垂直於面向）、隔 pair_gap m"""
    a = math.radians(STATE["face_deg"]); f = Vector((math.sin(a), -math.cos(a), 0))
    side = Vector((f.y, -f.x, 0))
    if side.y > 0:
        side = -side                                      # 取靠鏡頭（−Y）那一側
    return Vector((g.x, g.y, 0)) + side * P["pair_gap"]


def bride_state(t):
    """走路：遠側（0.45 m、往左落後 0.4 m）→ 停下：往前一步換到新郎靠鏡頭那一側、並排面向攝影師（第 1 輪回饋）
    → 起步：換回遠側一起走。換邊時往左繞（不穿過新郎）。手輕搭新郎手肘內側＝走位版不做"""
    m = STATE["t_marks"]; poses = STATE["poses"]
    g = poses[max(0, min(len(poses) - 1, int(round((t + HANDLES) * FPS))))][1]
    far = Vector((g.x - P["side_behind"], g.y + P["side_back"], 0))
    s0, s1 = m["stop"], m["stop"] + P["swap_s"]           # 換到靠鏡頭側
    b0, b1 = m["go"] - 0.1, m["go"] - 0.1 + P["swap_s"]   # 換回遠側
    if t <= s0 or t >= b1:
        return far, 90.0
    gs = poses[int(round((s0 + HANDLES) * FPS))][1]; near = _near_side(gs)
    if s1 <= t <= b0:
        return near, STATE["face_deg"]
    k = (t - s0) / (s1 - s0) if t < s1 else 1 - (t - b0) / (b1 - b0)
    k = k * k * (3 - 2 * k)
    p = far.lerp(near, k) + Vector((-P["swap_arc"] * math.sin(math.pi * k), 0, 0))
    return p, 90.0 + (STATE["face_deg"] - 90.0) * k


def standins():
    """2026-10-12 v2：走廊＋攝影區都用素材庫真的場景、照場景座標放（B3→B4 在柱子後面切，不用接 B3 的平移）"""
    col = Z.studio_col()
    a = BK.venue("Scene_VenueCorridor"); BK.venue("Scene_VenuePhotoZone")
    for n, o in a.items():                                # 走廊自己的遮擋柱子（離鏡頭太近）不用；換景柱子由這一鏡自己擺
        if n.startswith("I_ZP_pillar") and o.location.y < -1.0:
            o.hide_render = o.hide_viewport = True
    ph = BK.capsule("ZA_Photographer", height=P["ph_h"], radius=0.18, color=(0.35, 0.35, 0.4, 1))
    # 攝影師：停下演戲時在畫面右緣 ph_frac（前景、切掉一部分）；y 固定 ph_y。第 1 輪起鏡頭對準兩人中點，位置跟著鏡頭算
    l, a_ = side_cam()(int(round((STATE["t_marks"]["look"] + HANDLES) * FPS)))
    phy = P["line_y"] + P["ph_y"]; dep = phy - l.y      # ph_y 是相對兩人走的線
    ph_xy = (round(l.x + (P["ph_frac"] - 0.5) * BK.frame_w(dep), 3), round(phy, 3)); STATE["ph_xy"] = ph_xy
    gx = Vector((P["stop_x"], P["line_y"], 0)) - Vector((*ph_xy, 0))
    BK.place_capsule(ph, ph_xy, BK.yaw_of(gx.normalized()))
    STATE["ph_yaw"] = BK.yaw_of(gx.normalized())
    _props()["place_prop"]("dslr", parent=col, name="ZA_DSLR")
    BK.skirt(BK.capsule("ZA_Bride"))
    # 換景柱子：開頭（鏡內 0 秒）在鏡頭前 pillar_d m、正好擋住兩人；鏡頭往右跟拍時從畫面左邊出去
    cf = side_cam(); i0 = int(HANDLES * FPS); l, a_ = cf(i0); h = STATE["poses"][i0][1]
    fwd = (a_ - l); fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
    bp, _ = bride_state(0.0)                              # 對準兩人中間（新娘在新郎左後方）：兩個人都要擋住
    mid = (Vector((h.x, h.y, 0)) + Vector((bp.x, bp.y, 0))) / 2
    dg = mid - l; k = dg.dot(right) / dg.dot(fwd)
    px = l + fwd * P["pillar_d"] + right * (k * P["pillar_d"])
    _props()["place_prop"]("pillar", loc=(px.x, px.y, 0), parent=col, name="ZA_Pillar")
    Z.POSE_HOOKS.append(_hook)
    return dict(pillar=(round(px.x, 2), round(px.y, 2)), ph_xy=ph_xy, ph_yaw=round(STATE["ph_yaw"], 1))


def _hook(i):
    t = i / FPS - HANDLES; m = STATE["t_marks"]
    b = bpy.data.objects.get("ZA_Bride")
    if b is not None:
        p, yaw = bride_state(t); BK.place_capsule(b, p, yaw)
    c = bpy.data.objects.get("ZA_DSLR")
    if c is not None:                                     # 相機舉到攝影師臉前（觀景窗貼眼）→ 4.0 秒放到胸前；鏡頭朝兩人
        x, y = STATE["ph_xy"]; yaw = math.radians(STATE["ph_yaw"])
        fw = Vector((math.sin(yaw), -math.cos(yaw), 0))
        k = min(1.0, max(0.0, (t - m["ph_down"]) / 0.4))
        z = P["ph_h"] - 0.15 - 0.25 * k
        c.location = Vector((x, y, z)) + fw * (0.2 + 0.05 * k)
        c.rotation_euler = (0, 0, yaw)                     # dslr 鏡頭朝 −Y＝面向角度 0；轉到攝影師的面向


def side_cam():
    m = STATE.get("t_marks", {})
    holds = [(m["stop"] + 0.2, m["go"])] if m else []
    base = BK.side_follow(holds=holds, handles=HANDLES,
                          partner=lambda i: bride_state(i / FPS - HANDLES)[0])   # 第 1 輪：對準兩人中點
    if not m:
        return base
    # 第 1 輪 (b)：停下面對攝影師這段構圖破例，兩人中點放畫面 mid_hold（60%），右邊留給攝影師露半身；
    # 停下時平移過去、起步後平移回全片規則 70%（不硬切）
    dx = BK.frame_w(3.0) * (0.70 - P["mid_hold"])
    a0, a1 = m["stop"], m["stop"] + P["pan_s"]; b0, b1 = m["go"], m["go"] + P["pan_s"]

    def f(i):
        l, a = base(i); t = i / FPS - HANDLES
        k = 0.0 if t <= a0 or t >= b1 else (1.0 if a1 <= t <= b0 else ((t - a0) / (a1 - a0) if t < a1 else 1 - (t - b0) / (b1 - b0)))
        k = k * k * (3 - 2 * k); d = Vector((dx * k, 0, 0))
        return l + d, a + d
    return f


def run():
    import time
    t0 = time.time(); setup(); r = build(); r.update(standins()); r["sec"] = round(time.time() - t0, 1)
    return r


def blocking_clip(v=1):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", BK.LENS)
    out = SP.bake(objects=[bpy.data.objects[n] for n in ("ZA_Bride", "ZA_DSLR")], camera_fn=side_cam())
    path = SP.save("b4_blocking")
    cmd = SP.render_clip("b4_blocking", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + f"/blocking_v{v}.mp4")
    return dict(out, path=path, cmd=cmd)


def end_state():
    W = L._CL["male_standard_walk"]; wn = W["n"] - 1; seq = STATE["seq"]
    ph = ((STATE["dur"] + HANDLES - seq.T[-1][0]) * 30) % wn
    bp, byaw = bride_state(STATE["dur"])
    return BK.end_state(r"D:/render-work/zepeto-anim/opening-proposal-b/b4/end_state.json", STATE["dur"],
                        dict(phase_frame=round(ph, 1), wn=wn, bride=list(bp), bride_yaw=byaw, arrangement="並肩挽手：新娘在遠側 0.45 m、往左落後 0.4 m"))


def cleanup():
    return Z.cleanup(SCENE)
