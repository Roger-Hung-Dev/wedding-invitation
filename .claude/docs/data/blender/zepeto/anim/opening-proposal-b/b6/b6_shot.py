# B6（開場影片提案 B）：宴會廳大門前。門框從鏡頭前掃過換景 → 兩人並肩走到大門正前方停下（1.2）→ 一起向左轉 90° 背對鏡頭面向大門
# （新娘往前一步換到和新郎並排、在新郎左邊）→ 深呼吸 → 2.6 秒新郎左手牽新娘右手 → 2.9 秒大門自己打開 → 鏡頭繞到兩人正背後、往門裡推。
# 走位版（2026-10-12，第 1 輪規則起做）：場景用素材庫真的門廳＋攝影區（場景座標）；新娘＝膠囊替身＋裙擺；門片用場景裡可轉的那組。
# 不做深呼吸、牽手接觸（只把手帶到）、抬頭、閃白（剪接做）、檢查、確認頁、定案。
# 動作（本機沒有深呼吸、牽手的 Mixamo，先用現有的拼）：
#   male_standard_walk（接 B5 的相位）→ male_stop_walk → turn_left_90 前段（加法）→ look_around（站著，鎖住面向大門）；牽手＝左手臂 IK
# 座標：場景座標（角色走 y＝0 往 +X、鏡頭 y＝-3、門廳後牆 y＝0.75）。大門中心 x 13.1（門洞 1.7×2.2 m）；
# 前景門框中心 (12.51, -1.5) 不動，只在停下拉遠時框住兩人；換景改用另擺的柱子（第 2 輪 (c)）。B5→B6 在柱子後面切，不用接 B5 的位置。
import math, os, json
import bpy
from mathutils import Vector
import zanim as Z
import zanim_fix as F
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
SCENE, PREFIX = "ANIM_B6", "ZA_"
FPS = 30
HANDLES = 1.0
B5_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b5/end_state.json"
CLIPS = ("male_standard_walk", "male_stop_walk", "turn_left_90", "look_around")
DOOR_X, WALL_Y = 13.1, 0.75
P = dict(X=9, walk_s=0.5, stop_b=66, tl=(3, 45), idle=(20, 74), idle_hold=4.0, settle=0.3, idle2=(20, 74),   # 第 3 輪（以動作流暢為主）：停下播到停穩、整段左轉、站著重播一次安靜段再停住   # look_around 第 74 格後整個人會轉身張望（chk1：4.0 秒轉回來面對鏡頭）→ 只取安靜段、之後停住
           # turn_left_90 第 3～24 格轉約 55°，其餘由站著那段鎖住面向補完
         stop_at=1.2, pair_gap=0.7,   # stop_at：第 1、2 輪的分鏡秒數（第 3 輪起不用）   # 0.6 m 時裙擺碰到新郎的腿（2.77 秒 -4.5 cm）
         side_back=0.45, side_behind=0.4, swap_s=1.0,
         hold_d=1.2, door_d=0.6, door_s=1.2, orbit_d=0.5, orbit_s=1.0, push_s=0.8, tail=0.4,   # 面向大門後幾秒牽手（中間深呼吸）、牽手後幾秒開門、開門要幾秒、開門後幾秒鏡頭開始繞、繞幾秒、推幾秒、推完留幾秒
         far_dist=4.5, far_aim_z=1.05, pull_s=1.2,       # 停下後拉遠到 4.5 m（大門整扇入鏡），看向高度抬到 1.05 m
         orbit=(2.9, 3.6), back_dist=3.0, back_z=1.0, back_aim_z=1.0,   # 繞到正背後（胸口高）
         push=(3.6, 4.0), push_dist=1.5, push_z=1.15,
         pillar_d=0.9, pillar_hw=0.33, pillar_exit=0.9)   # 推進到背後 1.5 m、肩高；換景柱子（第 2 輪 (c)）：中心離鏡頭 0.9 m、半寬（素材 pillar 底座 0.66 m）、0.9 秒出畫（出畫後藏起來）


def setup():
    r = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b6")[1]
    Z.load_clips(CLIPS)
    return r


def _seq():
    tgt = STATE["tgt"]; end = BK.load_end(B5_END)
    W, ST, TL, LA = (L._CL[n] for n in CLIPS)
    wn = W["n"] - 1; X = P["X"]
    a0 = int(round(end["phase_frame"] - HANDLES * 30)) % wn
    t1 = (wn - a0) / 30.0; need = HANDLES + P["walk_s"] - (t1 - X / 30)
    _a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
    segs = [mr.Seg(W, a0, wn, name="接 B5 的走路"),
            mr.Seg(W, 0, wn, loops=max(0.05, need * 30 / wn), name="走到大門前"),
            mr.Seg(ST, b1, P["stop_b"], hold=P["settle"], name="停下（Stop Walking 前段）"),
            mr.Seg(TL, *P["tl"], add=True, name="向左轉面對大門（Turn Left 90 前段）"),
            mr.Seg(LA, *P["idle"], face=180.0, name="站著望向大門（Standing Idle，鎖住面向大門）"),
            mr.Seg(LA, *P["idle2"], hold=P["idle_hold"], face=180.0, name="站著（再播一次安靜段）")]
    seq = mr.Sequence(tgt, segs, blend=X / 30)
    seq.place(HANDLES, (0.0, 0.0), 90.0)
    idx = {sg.name: k for k, sg in enumerate(segs)}
    return seq, segs, (lambda nm: seq.T[idx[nm]][0] - HANDLES)


def build():
    tgt = STATE["tgt"]
    seq, segs, T = _seq()                                 # 第 3 輪：不再把停下塞進分鏡的 1.2 秒，秒數跟著動作走
    stop = T("向左轉面對大門（Turn Left 90 前段）"); look = T("站著望向大門（Standing Idle，鎖住面向大門）")
    P["hold_at"] = round(look + P["hold_d"], 2); P["door_at"] = round(P["hold_at"] + P["door_d"], 2)
    o0 = round(P["door_at"] + P["orbit_d"], 2); P["orbit"] = (o0, round(o0 + P["orbit_s"], 2))
    P["push"] = (P["orbit"][1], round(P["orbit"][1] + P["push_s"], 2))
    dur = P["push"][1] + P["tail"]
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    poses = [(dict(R), h.copy()) for R, h, _y in (seq.at(min(i / FPS, seq.dur)) for i in range(n))]
    hs = poses[int(round((stop + HANDLES) * FPS))][1]
    gx = DOOR_X + P["pair_gap"] / 2                       # 兩人中點對準大門中線：新郎在右（+X）
    sh = Vector((gx - hs.x, -hs.y, 0))
    poses = [(R, h + sh) for R, h in poses]
    pts = L.sole_points(STATE["arm"])
    poses, off = F.ground(tgt, poses, pts)
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9)
    m = dict(stop=round(stop, 2), look=round(look, 2), hold=P["hold_at"], door=P["door_at"])
    STATE.update(poses=poses, seq=seq, dur=dur, t_marks=m,
                 segs=[(round(seq.T[i][0] - HANDLES, 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    STATE["face_deg"] = 180.0
    STATE["stop_g"] = poses[int(round((stop + HANDLES) * FPS))][1].copy()
    _hold_hand(poses)
    fd = BK.yaw_of(BK.hips_fw(poses[int(round((look + 0.5 + HANDLES) * FPS))][0]))
    h0 = poses[int(HANDLES * FPS)][1]
    return dict(dur_s=round(dur, 2), frames=n, orbit=P["orbit"], push=P["push"], marks=m, walk_s=round(P["walk_s"], 2), face_deg=round(fd, 1),
                start_xy=(round(h0.x, 2), round(h0.y, 2)), stop_xy=(round(STATE["stop_g"].x, 2), round(STATE["stop_g"].y, 2)),
                ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)), segs=STATE["segs"])


def _w(t, a, b, c, d):
    if t <= a or t >= d:
        return 0.0
    x = (t - a) / (b - a) if t < b else ((d - t) / (d - c) if t > c else 1.0)
    return x * x * (3 - 2 * x)


def _hold_hand(poses):
    """2.6 秒起左手往左邊伸，帶到兩人中間（新娘右手的位置）；走位版只把手帶到，不做相握"""
    tgt = STATE["tgt"]; a = P["hold_at"]
    for i, (R, h) in enumerate(poses):
        t = i / FPS - HANDLES
        w = _w(t, a, a + 0.4, 99, 100)
        if w <= 0:
            continue
        Hd = tgt.fk(R, h); fw = BK.hips_fw(R)
        left = Vector((-fw.y, fw.x, 0))
        goal = Vector((h.x, h.y, 0)) + left * (P["pair_gap"] / 2) + fw * 0.05 + Vector((0, 0, 0.42))
        R = mr.arm_ik(tgt, R, h, "L", Hd["J_Bip_L_Hand"].lerp(goal, w), -left * 0.6 + Vector((0, 0, -1)))
        poses[i] = (R, h)


def bride_state(t):
    """走路：新郎左後方（遠側 0.45 m、往左落後 0.4 m）→ 停下：往前一步到新郎左邊並排（和新郎同一條線，第 1 輪回饋）、
    和新郎同一拍向左轉面向大門（背對鏡頭）"""
    m = STATE["t_marks"]; poses = STATE["poses"]
    g = poses[max(0, min(len(poses) - 1, int(round((t + HANDLES) * FPS))))][1]
    far = Vector((g.x - P["side_behind"], g.y + P["side_back"], 0))
    s0, s1 = m["stop"], m["stop"] + P["swap_s"]
    if t <= s0:
        return far, 90.0
    gs = STATE["stop_g"]; near = Vector((gs.x - P["pair_gap"], gs.y, 0))
    k = min(1.0, (t - s0) / (s1 - s0)); k = k * k * (3 - 2 * k)
    return far.lerp(near, k), 90.0 + 90.0 * k


def standins():
    col = Z.studio_col()
    BK.venue("Scene_VenuePhotoZone"); c = BK.venue("Scene_VenueFoyer")
    leaves = {}
    for n, o in c.items():
        if n.startswith("I_ZP_ballroom_doors"):           # 關著的整組大門（實例，不能轉）藏起來
            o.hide_render = o.hide_viewport = True
        elif n.startswith("ZP_ballroom_door_L_posed"):
            leaves["L"] = o
        elif n.startswith("ZP_ballroom_door_R_posed"):
            leaves["R"] = o
        elif n.startswith("ZP_ballroom_doors_") and n.split(".")[0].endswith("_posed"):
            o.hide_render = o.hide_viewport = False       # 門框、門後的光
    for k, o in leaves.items():
        o.name = "ZA_Door" + k; o.hide_render = o.hide_viewport = False
    door = next((o for n, o in c.items() if n.startswith("I_ZP_door_frame")), None)
    BK.skirt(BK.capsule("ZA_Bride"))
    # 換景柱子（第 2 輪 (c)）：開頭（鏡內 0 秒）在鏡頭前 pillar_d m、正好擋住兩人中點，鏡頭往右跟拍時從畫面左邊出去；
    # 出畫那一格起藏起來（停下後鏡頭往後拉遠，柱子在鏡頭和兩人之間，不藏會再入鏡）。前景門框不動，只當拉遠時的框
    cf = camera_fn(); i0 = int(HANDLES * FPS); l, a_ = cf(i0)
    fwd = (a_ - l); fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
    dg = _mid(i0) - Vector((l.x, l.y, 0)); k = dg.dot(right) / dg.dot(fwd)
    px = l + fwd * P["pillar_d"] + right * (k * P["pillar_d"])
    BK.props_api()["place_prop"]("pillar", loc=(px.x, px.y, 0), parent=col, name="ZA_Pillar")
    STATE["pillar_xy"] = Vector((px.x, px.y, 0))
    # 停下前鏡頭只往右移約 0.6 m，柱子出不了畫，拉遠時又會入鏡（chk3）→ 0～pillar_exit 秒柱子再往左滑 slide m，剛好在那一格出畫、之後藏起來
    STATE["pillar_slide"] = _slide_needed(cf, P["pillar_exit"]); STATE["pillar_off"] = P["pillar_exit"]
    Z.POSE_HOOKS.append(_hook)
    r = dict(doors=sorted(leaves), door_frame=tuple(round(v, 2) for v in door.location) if door else None,
             pillar=(round(px.x, 2), round(px.y, 2)), pillar_slide_m=STATE["pillar_slide"], pillar_off_s=STATE["pillar_off"])
    if door is not None:
        r["frame_cover"] = _cover(Vector((door.location.x - 1.01, door.location.y, 0)))
    return r


def _pillar_at(t):
    sl = STATE.get("pillar_slide", 0.0); k = min(1.0, max(0.0, t / P["pillar_exit"]))
    return STATE["pillar_xy"] + Vector((-sl * k, 0, 0))


def _slide_needed(cf, te):
    """te 秒時柱子右緣要剛好在畫面左緣外：算出這時還差多少（m）"""
    i = int(round((te + HANDLES) * FPS)); l, a = cf(i); fwd = a - l; fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
    q = STATE["pillar_xy"] - Vector((l.x, l.y, 0)); d = q.dot(fwd)
    edge = 0.5 + (q.dot(right) + P["pillar_hw"]) / BK.frame_w(d)
    return round(max(0.0, edge * BK.frame_w(d) + 0.02), 3)


def _pillar_exit(cf):
    """柱子右緣離開畫面左緣的時間（鏡內秒）；從這一格起藏起來"""
    p = STATE["pillar_xy"]; hw = P["pillar_hw"]
    for i in range(int(HANDLES * FPS), len(STATE["poses"])):
        l, a = cf(i); fwd = a - l; fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
        d = (p - Vector((l.x, l.y, 0))).dot(fwd)
        edge = 0.5 + ((p - Vector((l.x, l.y, 0))).dot(right) + hw) / BK.frame_w(max(d, 0.05))
        if edge < 0:
            return round(i / FPS - HANDLES, 2)
    return None


def _cover(p):
    """門框左柱在畫面上的位置（0＝左緣、1＝右緣）與兩人中點的位置，看開頭有沒有擋住兩人"""
    cam = camera_fn(); out = []
    for t in (0.0, 0.2, 0.4, 0.6, 0.8):
        i = int(round((t + HANDLES) * FPS)); l, a = cam(i)
        fwd = a - l; fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
        g = STATE["poses"][i][1]; b, _ = bride_state(t); mid = (Vector((g.x, g.y, 0)) + b) / 2
        fr = lambda q: 0.5 + (q - l).dot(right) / BK.frame_w((q - l).dot(fwd))
        out.append((t, round(fr(Vector((p.x, p.y, 0))), 2), round(fr(mid), 2)))
    return out


def _hook(i):
    t = i / FPS - HANDLES
    pil = bpy.data.objects.get("ZA_Pillar")
    if pil is not None:
        off = STATE.get("pillar_off")
        pil.hide_render = off is not None and t >= off
        pil.location = _pillar_at(t)
    b = bpy.data.objects.get("ZA_Bride")
    if b is not None:
        p, yaw = bride_state(t); BK.place_capsule(b, p, yaw)
    k = _w(t, P["door_at"], P["door_at"] + P["door_s"], 99, 100)   # 2.9 秒起門往內開（L 0 → +90°、R 0 → −90°）
    for s, sign in (("L", 1), ("R", -1)):
        d = bpy.data.objects.get("ZA_Door" + s)
        if d is not None:
            d.rotation_euler = (0, 0, sign * math.radians(90) * k)


def _mid(i):
    t = i / FPS - HANDLES; g = STATE["poses"][i][1]; b, _ = bride_state(t)
    return Vector(((g.x + b.x) / 2, (g.y + b.y) / 2, 0))


def camera_fn():
    """0～停下：側面跟拍（對準兩人中點、畫面 70%）→ 停下後 pull_s 秒拉遠到 4.5 m、看向抬高（大門整扇入鏡）並停住
    → 2.9～3.6 繞到兩人正背後、對準大門中線（胸口高）→ 3.6～4.0 往門裡推到背後 1.5 m（肩高）"""
    m = STATE["t_marks"]
    base = BK.side_follow(holds=[(m["stop"] + P["swap_s"], 99)], handles=HANDLES,
                          partner=lambda i: bride_state(i / FPS - HANDLES)[0])
    i_s = int(round((m["stop"] + P["swap_s"] + HANDLES) * FPS))
    ms = _mid(i_s)
    dx = -BK.frame_w(P["far_dist"]) * BK.CAP_SHIFT
    far_l = Vector((ms.x + dx, ms.y - P["far_dist"], 0.6 + 0.25)); far_a = Vector((ms.x + dx, ms.y, P["far_aim_z"]))
    back_l = Vector((DOOR_X, ms.y - P["back_dist"], P["back_z"])); back_a = Vector((DOOR_X, WALL_Y, P["back_aim_z"]))
    push_l = Vector((DOOR_X, ms.y - P["push_dist"], P["push_z"])); push_a = Vector((DOOR_X, WALL_Y, P["push_z"]))
    s = lambda x: x * x * (3 - 2 * x)

    def f(i):
        t = i / FPS - HANDLES
        l, a = base(i)
        k = s(min(1.0, max(0.0, (t - m["stop"]) / P["pull_s"])))
        l, a = l.lerp(far_l, k), a.lerp(far_a, k)
        o0, o1 = P["orbit"]
        if t > o0:                                        # 繞：位置沿弧線（水平先偏外再收回中線），看向點移到大門中線
            k = s(min(1.0, (t - o0) / (o1 - o0)))
            arc = Vector((0, -0.6 * math.sin(math.pi * k), 0))
            l, a = far_l.lerp(back_l, k) + arc, far_a.lerp(back_a, k)
        p0, p1 = P["push"]
        if t > p0:
            k = s(min(1.0, (t - p0) / (p1 - p0)))
            l, a = back_l.lerp(push_l, k), back_a.lerp(push_a, k)
        return l, a
    return f


def run():
    import time
    t0 = time.time(); setup(); r = build(); r.update(standins()); r["sec"] = round(time.time() - t0, 1)
    return r


def blocking_clip(v=1):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", BK.LENS)
    out = SP.bake(objects=[bpy.data.objects[n] for n in ("ZA_Bride", "ZA_DoorL", "ZA_DoorR", "ZA_Pillar")], camera_fn=camera_fn())
    path = SP.save("b6_blocking")
    cmd = SP.render_clip("b6_blocking", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + f"/blocking_v{v}.mp4")
    return dict(out, path=path, cmd=cmd)


def cleanup():
    return Z.cleanup(SCENE)
