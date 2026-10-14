# B5（開場影片提案 B）：拍照背板前自拍。接 B4 走到背板前停下（1.2）→ 一起轉身面向鏡頭（新娘往前一步換到新郎靠鏡頭那一側、
# 站在新郎左邊＝畫面右邊）→ 新郎右手舉手機自拍、頭靠頭、新娘比 YA，3.0 秒按快門 → 3.4 秒手機放下、轉回往右起步（接 B6 的門框遮擋）。
# 走位版（2026-10-12，第 1 輪規則起做）：場景用素材庫真的走廊＋攝影區＋門廳（場景座標）；新娘＝膠囊替身＋裙擺；手機用素材庫 phone_zp。
# 不做頭靠頭、比 YA、手扶背、手搭手肘、拇指按快門、檢查、確認頁、定案。
# 動作（本機沒有自拍的 Mixamo，先用現有的拼）：
#   male_standard_walk（接 B4 的相位）→ male_stop_walk → turn_right_90（加法，轉 90° 面向鏡頭）→ texting_standing（站著拿手機）
#   → turn_left_90 前段（加法）→ male_start_walk（鎖住往 +X）→ male_standard_walk；舉手機＝右手臂 IK 到斜前上方
# 座標：場景座標（角色走 y＝0 往 +X、鏡頭 y＝-3、牆 y＝0.75）。拍照背板中心 x 10.2；門框中心 (12.51, -1.5)，左門柱 x 11.5 在結尾掃過鏡頭。
import math, os, json
import bpy
from mathutils import Vector
import zanim as Z
import zanim_fix as F
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
SCENE, PREFIX = "ANIM_B5", "ZA_"
FPS = 30
HANDLES = 1.0
B4_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b4/end_state.json"
CLIPS = ("male_standard_walk", "male_stop_walk", "turn_right_90", "texting_standing", "turn_left_90", "male_start_walk")
P = dict(X=9, walk_s=0.05, stop_b=66, turn=(22, 46), idle_a=10, tl=(3, 45), idle_n=108, settle=0.3, go_len=2.6,   # 第 2 輪（以動作流暢為主）：停下播到停穩、轉回用整段 Turn Left 90、起步從靜止開始；idle_n＝拿手機那段幾格（停下那段 ≥ 4 秒）   # turn_right_90 的轉身在第 24～44 格（前面是原地站）；turn_left_90 第 3～24 格轉約 55°，其餘交給起步
         start_a=10, face_sw=-3.0, face_w=-3.0,
         stop_at=1.2, go_at=3.4,                         # 第 1 輪用的分鏡秒數（第 2 輪起不用：秒數跟著動作走）
         pair_gap=0.6, side_back=0.45, side_behind=0.4, swap_s=1.0, swap_arc=0.22,   # 0.35 會擦進背板（新娘從新郎背後繞，背板正面 y 0.06）   # 新娘：走路在遠側；停下換到新郎左邊（+X）並排、從後面繞
         phone_d=0.3, shutter_d=1.8, out_d=0.6,         # 站著開始後幾秒舉手機、舉起後幾秒按快門、按完幾秒放下
         push=0.10, chest_dz=0.15)                                      # 1.2～3.4 跟拍停住、慢慢推近約 10%


def setup():
    r = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b5")[1]
    Z.load_clips(CLIPS)
    return r


def _props():
    return BK.props_api()


def _seq(idle_n):
    tgt = STATE["tgt"]; end = BK.load_end(B4_END)
    W, ST, TR, TX, TL, SW = (L._CL[n] for n in CLIPS)
    wn = W["n"] - 1; X = P["X"]
    a0 = int(round(end["phase_frame"] - HANDLES * 30)) % wn
    t1 = (wn - a0) / 30.0; need = HANDLES + P["walk_s"] - (t1 - X / 30)
    _a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
    i1 = min(TX["n"] - 1, P["idle_a"] + idle_n)
    segs = [mr.Seg(W, a0, wn, name="接 B4 的走路"),
            mr.Seg(W, 0, wn, loops=max(0.05, need * 30 / wn), name="走到背板前"),
            mr.Seg(ST, b1, P["stop_b"], hold=P["settle"], name="停下（Stop Walking 前段）"),
            mr.Seg(TR, *P["turn"], add=True, name="轉身面向鏡頭（Turn Right 90）"),
            mr.Seg(TX, P["idle_a"], i1, face=0.0, name="站著拿手機（Texting Standing）"),   # 這支動作身體本來就斜 25°：鎖住面向鏡頭
            mr.Seg(TL, *P["tl"], add=True, name="轉回（Turn Left 90）"),
            mr.Seg(SW, P["start_a"], SW["n"] - 1, face=90.0 + P["face_sw"], name="起步（Start Walking 後段）"),
            mr.Seg(W, 0, wn, loops=3, face=90.0 + P["face_w"], name="走路")]
    seq = mr.Sequence(tgt, segs, blend=X / 30)
    seq.place(HANDLES, (0.0, 0.0), 90.0)
    idx = {sg.name: k for k, sg in enumerate(segs)}
    T = lambda nm: seq.T[idx[nm]][0] - HANDLES
    return seq, segs, T


def build():
    tgt = STATE["tgt"]; end = BK.load_end(B4_END)
    TX = L._CL["texting_standing"]
    idle_n = P["idle_n"]                                  # 第 2 輪：不再把停下、起步塞進分鏡的 1.2／3.4 秒，秒數跟著動作走
    seq, segs, T = _seq(idle_n)
    stop = T("轉身面向鏡頭（Turn Right 90）"); go = T("轉回（Turn Left 90）")
    dur = T("起步（Start Walking 後段）") + P["go_len"]
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    poses = [(dict(R), h.copy()) for R, h, _y in (seq.at(min(i / FPS, seq.dur)) for i in range(n))]
    h0 = poses[int(round(HANDLES * FPS))][1]
    sh = Vector((end["hips"][0] - h0.x, end["hips"][1] - h0.y, 0))   # 整條平移：開頭骨盆＝B4 最後一格
    poses = [(R, h + sh) for R, h in poses]
    pts = L.sole_points(STATE["arm"])
    poses, off = F.ground(tgt, poses, pts)
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9)
    look = T("站著拿手機（Texting Standing）")
    P["phone_in"] = round(look + P["phone_d"], 2); P["shutter"] = round(P["phone_in"] + P["shutter_d"], 2)
    P["phone_out"] = round(P["shutter"] + P["out_d"], 2)
    m = dict(stop=round(stop, 2), look=round(look, 2), go=round(go, 2), start=round(T("起步（Start Walking 後段）"), 2),
             phone=(P["phone_in"], P["phone_out"]), shutter=P["shutter"])
    STATE.update(poses=poses, seq=seq, dur=dur, t_marks=m,
                 segs=[(round(seq.T[i][0] - HANDLES, 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    _selfie(poses)
    STATE["face_deg"] = BK.yaw_of(BK.hips_fw(poses[int(round((look + 0.3 + HANDLES) * FPS))][0]))
    hs = poses[int(round((stop + HANDLES) * FPS))][1]
    return dict(dur_s=round(dur, 2), frames=n, marks=m, idle_frames=idle_n, walk_s=round(P["walk_s"], 2), face_deg=round(STATE["face_deg"], 1),
                stop_xy=(round(hs.x, 2), round(hs.y, 2)), ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)), segs=STATE["segs"])


def _w(t, a, b, c, d):
    if t <= a or t >= d:
        return 0.0
    x = (t - a) / (b - a) if t < b else ((d - t) / (d - c) if t > c else 1.0)
    return x * x * (3 - 2 * x)


def _selfie_goal(Hd, fw):
    """自拍時右手（手機）的位置：右肩往前 0.32 m、往上 0.30 m、往外（新郎右邊、遠離新娘）0.15 m。
    正面鏡頭拍自拍：手機放臉前面會擋住臉（chk2）→ 舉到新郎右上方；往上 0.42 m 手機會出畫（chk3）"""
    right = Vector((fw.y, -fw.x, 0))
    return Hd["J_Bip_R_UpperArm"] + fw * 0.32 + Vector((0, 0, 0.30)) + right * 0.15


def _selfie(poses):
    """舉手機：右手臂 IK 到斜前上方（走位版只表達時間與方向）"""
    tgt = STATE["tgt"]; a, b = P["phone_in"], P["phone_out"]
    for i, (R, h) in enumerate(poses):
        t = i / FPS - HANDLES
        w = _w(t, a, a + 0.6, b - 0.3, b)
        if w <= 0:
            continue
        Hd = tgt.fk(R, h); fw = BK.hips_fw(R)
        right = Vector((fw.y, -fw.x, 0))
        R = mr.arm_ik(tgt, R, h, "R", Hd["J_Bip_R_Hand"].lerp(_selfie_goal(Hd, fw), w), right * 0.6 + Vector((0, 0, -1)))
        poses[i] = (R, h)


def _beside(g):
    """停下面向鏡頭時新娘的位置：新郎左手側（面向 −Y 時＝+X、畫面右邊）並排、隔 pair_gap m"""
    a = math.radians(STATE["face_deg"]); f = Vector((math.sin(a), -math.cos(a), 0))
    left = Vector((-f.y, f.x, 0))
    return Vector((g.x, g.y, 0)) + left * P["pair_gap"]


def bride_state(t):
    """走路：遠側（0.45 m、往左落後 0.4 m）→ 停下轉身：往前一步換到新郎左邊並排面向鏡頭（第 1 輪回饋）
    → 起步：換回遠側。換邊時從新郎後面繞（不穿過新郎）。手搭手肘、頭靠頭、比 YA＝走位版不做"""
    m = STATE["t_marks"]; poses = STATE["poses"]
    g = poses[max(0, min(len(poses) - 1, int(round((t + HANDLES) * FPS))))][1]
    far = Vector((g.x - P["side_behind"], g.y + P["side_back"], 0))
    s0, s1 = m["stop"], m["stop"] + P["swap_s"]
    b0, b1 = m["go"], m["go"] + P["swap_s"]
    if t <= s0 or t >= b1:
        return far, 90.0
    gs = poses[int(round((s0 + HANDLES) * FPS))][1]; near = _beside(gs)
    if s1 <= t <= b0:
        return near, STATE["face_deg"]
    k = (t - s0) / (s1 - s0) if t < s1 else 1 - (t - b0) / (b1 - b0)
    k = k * k * (3 - 2 * k)
    p = far.lerp(near, k) + Vector((0, P["swap_arc"] * math.sin(math.pi * k), 0))
    return p, 90.0 + (STATE["face_deg"] - 90.0) * k


def standins():
    col = Z.studio_col()
    a = BK.venue("Scene_VenueCorridor"); BK.venue("Scene_VenuePhotoZone"); c = BK.venue("Scene_VenueFoyer")
    for n, o in a.items():                                # 走廊的近景遮擋柱子這一鏡用不到
        if n.startswith("I_ZP_pillar") and o.location.y < -1.0:
            o.hide_render = o.hide_viewport = True
    door = next((o for n, o in c.items() if n.startswith("I_ZP_door_frame")), None)
    _props()["place_prop"]("phone_zp", parent=col, name="ZA_Phone")
    BK.skirt(BK.capsule("ZA_Bride"))
    Z.POSE_HOOKS.append(_hook)
    r = dict(door_frame=tuple(round(v, 2) for v in door.location) if door else None)
    if door is not None:
        r["door_cross_s"] = _cross(Vector((door.location.x - 1.0, door.location.y, 0)))
    return r


def _cross(p):
    """遮擋物（門框左柱）在畫面上蓋過兩人中點的時間（鏡內秒）；在這一鏡之後就回傳 None"""
    cam = side_cam(); go = STATE["t_marks"]["go"]
    for i in range(len(STATE["poses"])):
        t = i / FPS - HANDLES
        if t < go:
            continue
        l, a = cam(i); fwd = a - l; fwd.z = 0; fwd.normalize(); right = Vector((fwd.y, -fwd.x, 0))
        g = STATE["poses"][i][1]; b, _ = bride_state(t)
        mid = (Vector((g.x, g.y, 0)) + b) / 2
        dp, dg = Vector((p.x, p.y, 0)) - l, mid - l
        if dp.dot(right) / dp.dot(fwd) <= dg.dot(right) / dg.dot(fwd):
            return round(t, 2)
    return None


def _hook(i):
    t = i / FPS - HANDLES
    b = bpy.data.objects.get("ZA_Bride")
    if b is not None:
        p, yaw = bride_state(t); BK.place_capsule(b, p, yaw)
    ph = bpy.data.objects.get("ZA_Phone")
    if ph is not None:
        if P["phone_in"] <= t < P["phone_out"]:           # 在右手；螢幕朝兩人的臉（面向角度＝新郎面向＋180°）
            arm = STATE["arm"]; STATE["sc"].view_layers[0].update()   # 骨架要先依這一格更新，不然讀到上一個姿勢的手
            ph.location = arm.matrix_world @ arm.pose.bones["J_Bip_R_Hand"].head + Vector((0, 0, 0.03))
            ph.rotation_euler = (math.radians(75), 0, math.radians(STATE["face_deg"] + 180.0))
            ph.hide_render = False
        else:
            ph.hide_render = True


def side_cam():
    """側面跟拍（對準兩人中點、放畫面 70%）；停下到起步之間停住、慢慢推近 push（10%）"""
    m = STATE["t_marks"]
    base = BK.side_follow(holds=[(m["stop"] + P["swap_s"], m["go"])],   # 等新娘換好位置才停住（停在換位前會把新娘切出畫面）
                           handles=HANDLES, partner=lambda i: bride_state(i / FPS - HANDLES)[0])
    i0, i1 = int(round((m["stop"] + HANDLES) * FPS)), int(round((m["go"] + HANDLES) * FPS))

    def f(i):
        l, a = base(i)
        if i0 < i:
            k = min(1.0, (i - i0) / (i1 - i0)) if i <= i1 else max(0.0, 1 - (i - i1) / 18)   # 起步後 0.6 秒拉回
            k = k * k * (3 - 2 * k)
            up = Vector((0, 0, P["chest_dz"] * k))         # 中景、胸口高：推近時一起抬高，頭頂才不會被切
            l = l.lerp(a, P["push"] * k) + up; a = a + up
        return l, a
    return f


def run():
    import time
    t0 = time.time(); setup(); r = build(); r.update(standins()); r["sec"] = round(time.time() - t0, 1)
    return r


def blocking_clip(v=1):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", BK.LENS)
    out = SP.bake(objects=[bpy.data.objects[n] for n in ("ZA_Bride", "ZA_Phone")], camera_fn=side_cam())
    path = SP.save("b5_blocking")
    cmd = SP.render_clip("b5_blocking", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + f"/blocking_v{v}.mp4")
    return dict(out, path=path, cmd=cmd)


def end_state():
    W = L._CL["male_standard_walk"]; wn = W["n"] - 1; seq = STATE["seq"]
    ph = ((STATE["dur"] + HANDLES - seq.T[-1][0]) * 30) % wn
    bp, byaw = bride_state(STATE["dur"])
    return BK.end_state(r"D:/render-work/zepeto-anim/opening-proposal-b/b5/end_state.json", STATE["dur"],
                        dict(phase_frame=round(ph, 1), wn=wn, bride=list(bp), bride_yaw=byaw, arrangement="並肩：新娘在遠側 0.45 m、往左落後 0.4 m"))


def cleanup():
    return Z.cleanup(SCENE)
