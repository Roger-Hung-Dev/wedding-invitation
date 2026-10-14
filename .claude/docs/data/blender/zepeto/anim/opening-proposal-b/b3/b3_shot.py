# B3（開場影片提案 B）：走廊的代客泊車立牌前。新娘拉著新郎手腕走進來停下 → 新郎掏車鑰匙晃（要去開車）→ 新娘一把抓走、
# 搖手指（喝酒不開車）→ 兩人起步往右走；結尾柱子從鏡頭前掃過，柱子遮住的那幾格兩人從一前一後換成並肩（接 B4）。
# 走位版（2026-10-12）：新娘＝膠囊替身（和新郎同高）；車鑰匙用方塊；立牌、柱子、牆用素材庫真的走廊場景（2026-10-12 v2 起）。不做手指、接觸、檢查、確認頁、定案。
# 動作（本機沒有掏東西、失望、搖手指的 Mixamo，先用現有的拼）：
#   male_standard_walk（接 B2）→ male_stop_walk（停下）→ look_around（站著）→ male_start_walk → male_standard_walk
#   掏鑰匙、舉到胸口、被抓走後手垂下：右手臂 IK
# 座標：和 B0～B2 同一套（同一段連續場景 ①）。開頭＝B2 最後一格。
import math, os, json
import bpy
from mathutils import Vector
import zanim as Z
import zanim_fix as F
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
SCENE, PREFIX = "ANIM_B3", "ZA_"
FPS = 30
HANDLES = 1.0
B2_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b2/end_state.json"
P = dict(X=9, walk_s=-0.5, stop_b=66, idle=(20, 74), start_a=10,   # 2026-10-12 第 3 輪（以動作流暢為主）：停下播到停穩、起步從靜止開始
         settle=0.4, idle_hold=0.7, go_len=2.6, idle2=(20, 74),             # 停穩後停幾秒、站著那段最後停住幾秒（搖手指的時間）、起步後幾秒切到 B4（走回正常速度）
         key_up=0.5, grab=1.5, drop=1.8,                    # 站著開始後幾秒：掏鑰匙、被抓走、手垂下
         face_sw=0.0, face_w=-3.0,
         bride_ahead=0.75, side_back=0.45, side_behind=0.4,                # 拉著走：新娘在前 0.75 m（裙擺半徑 0.32 m，0.55 m 會被新郎跨步踩到）；並肩（B4）：遠側 0.45 m、往左落後 0.4 m
         pillar_t=3.1, pillar_d=1.3, pillar_hw=0.33)   # pillar_d：換景柱子中心離鏡頭（m）、pillar_hw：柱子半寬（素材 pillar 底座 0.66 m）； 柱子擋住新郎的時間：v2 起由場景柱子的位置算（_pillar_cross），算不到才用這個；換鏡的接點藏在柱子後面


def setup():
    r = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b3")[1]
    Z.load_clips(("male_standard_walk", "male_stop_walk", "look_around", "male_start_walk"))
    return r


def build():
    tgt = STATE["tgt"]; end = BK.load_end(B2_END)
    W, ST, LA, SW = (L._CL[n] for n in ("male_standard_walk", "male_stop_walk", "look_around", "male_start_walk"))
    wn = W["n"] - 1; X = P["X"]
    a0 = int(round(end["phase_frame"] - HANDLES * 30)) % wn
    t1 = (wn - a0) / 30.0; need = HANDLES + P["walk_s"] - (t1 - X / 30)
    _a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
    segs = [mr.Seg(W, a0, wn, name="接 B2 的走路"),
            mr.Seg(W, 0, wn, loops=max(0.05, need * 30 / wn), name="被拉著走"),
            mr.Seg(ST, b1, P["stop_b"], hold=P["settle"], name="停下（Stop Walking 前段）"),
            mr.Seg(LA, *P["idle"], name="站著（Standing Idle）"),
            mr.Seg(LA, *P["idle2"], hold=P["idle_hold"], name="站著（再播一次安靜段）"),   # 第 3 輪：look_around 74 格後會轉身，只能重播安靜段拉長
            mr.Seg(SW, P["start_a"], SW["n"] - 1, face=90.0 + P["face_sw"], name="起步（Start Walking 後段）"),
            mr.Seg(W, 0, wn, loops=3, face=90.0 + P["face_w"], name="走路")]
    seq = mr.Sequence(tgt, segs, blend=X / 30)
    fw = Vector(end["fw"]); hx, hy = end["hips"][0], end["hips"][1]; yaw = BK.yaw_of(fw)
    for _ in range(2):
        seq.place(HANDLES, (hx, hy), yaw)
        yaw += BK.yaw_of(fw) - BK.yaw_of(BK.hips_fw(seq.at(HANDLES)[0]))
    seq.place(HANDLES, (hx, hy), yaw)
    idx = {sg.name: k for k, sg in enumerate(segs)}
    T = lambda nm: seq.T[idx[nm]][0] - HANDLES
    go = T("起步（Start Walking 後段）"); dur = go + P["go_len"]
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    poses = [(dict(R), h.copy()) for R, h, _y in (seq.at(min(i / FPS, seq.dur)) for i in range(n))]
    pts = L.sole_points(STATE["arm"])
    poses, off = F.ground(tgt, poses, pts)
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9)
    STATE.update(poses=poses, seq=seq, dur=dur, segs=[(round(seq.T[i][0] - HANDLES, 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    stop = T("站著（Standing Idle）")
    hs = poses[int(round((stop + HANDLES) * FPS))][1]
    STATE["stop_xy"] = Vector((hs.x, hs.y, 0)); STATE["line_y"] = hy
    m = dict(stop=round(stop, 2), go=round(go, 2))
    m.update(key_up=round(stop + P["key_up"], 2), grab=round(stop + P["grab"], 2), drop=round(stop + P["drop"], 2))
    m["swap"] = P["pillar_t"] if P["pillar_t"] < dur + HANDLES else dur
    STATE["t_marks"] = m
    _arms(poses)
    return dict(dur_s=round(dur, 2), frames=n, marks=m, ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)), segs=STATE["segs"])


def _w(t, a, b, c, d):
    if t <= a or t >= d:
        return 0.0
    x = (t - a) / (b - a) if t < b else ((d - t) / (d - c) if t > c else 1.0)
    return x * x * (3 - 2 * x)


def key_hold_pt(R, h):
    """新郎舉鑰匙的位置：胸口前 25 cm、略往右"""
    tgt = STATE["tgt"]; Hd = tgt.fk(R, h); fw = BK.hips_fw(R)
    return Hd["J_Bip_C_UpperChest"] + fw * 0.25 + Vector((0, 0, 0.02))


def _arms(poses):
    """右手：被拉直（0～停下）→ 掏鑰匙舉到胸前（key_up～grab）→ 被抓走後愣住、手垂下（drop 之後放開回原片）"""
    tgt = STATE["tgt"]; m = STATE["t_marks"]
    for i, (R, h) in enumerate(poses):
        t = i / FPS - HANDLES
        Hd = tgt.fk(R, h)
        w_pull = _w(t, -HANDLES - 1, -HANDLES, m["stop"] - 0.3, m["stop"] + 0.1)
        w_key = _w(t, m["key_up"] - 0.1, m["key_up"] + 0.4, m["drop"], m["drop"] + 0.6)
        goal = None
        if w_pull > 0:
            goal, w = Hd["J_Bip_R_UpperArm"] + Vector((0.42, -0.05, -0.18)), w_pull
        if w_key > 0:
            goal, w = key_hold_pt(R, h), w_key
        if goal is not None:
            R = mr.arm_ik(tgt, R, h, "R", Hd["J_Bip_R_Hand"].lerp(goal, w), Vector((0, 0, -1)))
        poses[i] = (R, h)


def bride_state(t):
    """拉著走（前 0.55 m）→ 停下、轉身面向新郎 → 抓鑰匙往前 10 cm → 搖手指（鼻子左右擺）→ 轉回 +X 跟著起步 → 柱子遮住時換到並肩（遠側）"""
    m = STATE["t_marks"]; poses = STATE["poses"]
    gi = lambda tt: poses[max(0, min(len(poses) - 1, int(round((tt + HANDLES) * FPS))))][1]
    g = gi(t); ly = STATE["line_y"] + 0.05
    if t >= m["swap"]:                                    # 柱子後面：並肩（B4 開頭）
        return Vector((g.x - P["side_behind"], g.y + P["side_back"], 0)), 90.0
    if t < m["stop"]:
        return Vector((g.x + P["bride_ahead"], ly, 0)), 90.0
    s = STATE["stop_xy"]; x0 = s.x + P["bride_ahead"]
    if t < m["go"]:
        x = x0 - (0.1 * _w(t, m["grab"] - 0.15, m["grab"], m["drop"] + 0.1, m["drop"] + 0.3))
        yaw = 90.0 + 180.0 * min(1.0, (t - m["stop"]) / 0.6)                         # 轉身面向新郎（270）
        if m["drop"] < t < m["drop"] + 1.0:
            yaw += 18.0 * math.sin((t - m["drop"]) * 2 * math.pi * 2.0)               # 搖手指「不行」（第 3 輪：搖 1 秒、2 下，搖完停一下再轉身）
        if t > m["go"] - 0.6:
            yaw = 270.0 - 180.0 * min(1.0, (t - (m["go"] - 0.6)) / 0.6)              # 轉回往右
        return Vector((x, ly, 0)), yaw
    return Vector((max(x0, g.x + P["bride_ahead"]), ly, 0)), 90.0


def standins():
    """2026-10-12 換成素材庫真的走廊場景（立牌、換景柱子都是場景裡的）；車鑰匙還是方塊"""
    off = json.load(open(BK.VENUE_OFFSET))
    objs = BK.venue("Scene_VenueCorridor", (off["dx"], off["dy"] + STATE["line_y"], 0))   # B2 起新郎走的線往鏡頭偏了（B1→B2 重做時拉直），場景跟著平移
    sign = next(o for n, o in objs.items() if n.startswith("I_ZP_valet_sign"))
    pil = min((o for n, o in objs.items() if n.startswith("I_ZP_pillar")), key=lambda o: o.location.y)   # 靠鏡頭那根＝換景柱子
    BK.box("ZA_Key", (0.03, 0.01, 0.06), (0, 0, 0), (0.95, 0.8, 0.3, 1), origin="center")
    BK.skirt(BK.capsule("ZA_Bride"))
    # 場景的柱子離鏡頭太近（正面 0.47 m、寬 0.66 m → 整個畫面白掉將近 1 秒，演戲時還擋住新娘與立牌）：
    # 這一鏡改放鏡頭前 pillar_d m、停下演戲時柱子左緣剛好在畫面外（已回報場景端）
    m = STATE["t_marks"]; l, a = side_cam()(int(round((m["stop"] + HANDLES) * FPS)))
    fwd = a - l; fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0)); hw = P["pillar_hw"]
    c = l + fwd * P["pillar_d"] + right * (BK.frame_w(P["pillar_d"] - hw) / 2 + hw + 0.05)
    pil.location = (c.x, c.y, 0)
    STATE["t_marks"]["swap"] = 99.0                     # 算交會時新娘還在前面（換位前）
    sw = _pillar_cross(pil.location); STATE["t_marks"]["swap"] = sw
    # 第 3 輪：鏡內結尾＝柱子蓋住兩人中點那一格（起步後多走的那段會讓結尾超過柱子，換景露出來）
    if sw < STATE["dur"]:
        STATE["dur"] = sw
        del STATE["poses"][int(round((sw + 2 * HANDLES) * FPS)) + 1:]
    Z.POSE_HOOKS.append(_hook)
    s = STATE["stop_xy"]
    return dict(pillar_xy=(round(pil.location.x, 2), round(pil.location.y, 2)), swap=STATE["t_marks"]["swap"], dur_s=round(STATE["dur"], 2),
                sign_from_stop=(round(sign.location.x - s.x, 2), round(sign.location.y - s.y, 2)))


def _pillar_cross(p):
    """柱子在畫面上擋住新郎的時間（鏡內秒）：起步後柱子的畫面位置追上新郎的那一格；換位藏在這一格"""
    cam = side_cam(); go = STATE["t_marks"]["go"]
    for i, (_R, h) in enumerate(STATE["poses"]):
        t = i / FPS - HANDLES
        if t < go:
            continue
        l, a = cam(i); fwd = a - l; fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
        b, _ = bride_state(t); mid = (Vector((h.x, h.y, 0)) + b) / 2   # 第 3 輪：對兩人中點（只對新郎時柱子蓋住的那格新娘還露在外面）
        dp, dg = Vector((p.x, p.y, 0)) - l, mid - l
        if dp.dot(right) / dp.dot(fwd) <= dg.dot(right) / dg.dot(fwd):
            return round(t, 2)
    return P["pillar_t"]


def _hook(i):
    t = i / FPS - HANDLES; m = STATE["t_marks"]
    b = bpy.data.objects.get("ZA_Bride")
    if b is not None:
        p, yaw = bride_state(t); BK.place_capsule(b, p, yaw)
    k = bpy.data.objects.get("ZA_Key")
    if k is not None:
        arm = STATE["arm"]; STATE["sc"].view_layers[0].update()   # 骨架要先依這一格更新，不然讀到上一個姿勢的手
        if m["key_up"] < t < m["grab"]:                   # 在新郎右手
            k.location = arm.matrix_world @ arm.pose.bones["J_Bip_R_Hand"].head + Vector((0, 0, -0.04)); k.hide_render = False
        elif t >= m["grab"] and t < m["swap"]:            # 在新娘手上（胸前）
            p, _ = bride_state(t); k.location = (p.x - 0.12, p.y - 0.1, STATE["measure"]["head_top"] * 0.62); k.hide_render = False
        else:
            k.hide_render = True                          # 還在口袋裡／柱子後換景就不出現（B4 新娘雙手空著）


def side_cam():
    m = STATE["t_marks"]
    return BK.side_follow(holds=[(m["stop"], m["go"])], handles=HANDLES,
                          partner=lambda i: bride_state(i / FPS - HANDLES)[0])   # 第 1 輪：對準兩人中點


def run():
    import time
    t0 = time.time(); setup(); r = build(); r.update(standins()); r["sec"] = round(time.time() - t0, 1)
    return r


def blocking_clip(v=1):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", BK.LENS)
    out = SP.bake(objects=[bpy.data.objects[n] for n in ("ZA_Bride", "ZA_Key")], camera_fn=side_cam())
    path = SP.save("b3_blocking")
    cmd = SP.render_clip("b3_blocking", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + f"/blocking_v{v}.mp4")
    return dict(out, path=path, cmd=cmd)


def end_state():
    tgt = STATE["tgt"]; W = L._CL["male_standard_walk"]; wn = W["n"] - 1; seq = STATE["seq"]
    ph = ((STATE["dur"] + HANDLES - seq.T[-1][0]) * 30) % wn
    # B4 開頭已經是並肩（換位藏在柱子後面，接點在柱子遮住的時候）：新娘位置照並肩的規則算
    g = STATE["poses"][int(round((STATE["dur"] + HANDLES) * FPS))][1]
    bp, byaw = Vector((g.x - P["side_behind"], g.y + P["side_back"], 0)), 90.0
    return BK.end_state(r"D:/render-work/zepeto-anim/opening-proposal-b/b3/end_state.json", STATE["dur"],
                        dict(phase_frame=round(ph, 1), wn=wn, bride=list(bp), bride_yaw=byaw, arrangement="並肩：新娘在遠側 0.45 m、往左落後 0.4 m"))


def cleanup():
    return Z.cleanup(SCENE)
