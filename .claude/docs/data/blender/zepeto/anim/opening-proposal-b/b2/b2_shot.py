# B2（開場影片提案 B）：經過甜點餐檯，新郎停下、偷拿一塊小蛋糕塞進嘴裡，被走在前面的新娘回頭抓手腕拉走。接 B1→B2 結尾，捲進 B3。
# 走位版（2026-10-12）：新娘用替身（灰色膠囊＋朝向標記，身高＝新郎 × 0.95），餐檯、蛋糕用方塊；
# 不做手指捏蛋糕、嘴、手腕接觸、穿模檢查、近照確認頁、定案。
# 動作（本機沒有拿東西、吃、被拉的 Mixamo，照 B0 使用者的選擇「先用現有的拼」）：
#   male_standard_walk（接 B1→B2）→ male_stop_walk（停下）→ turn_left_90（轉向餐檯，只取前段約 60°）→ look_around（左右張望）
#   → turn_right_90（被拉回頭，只取中段）→ male_start_walk（被拉著起步）→ male_standard_walk
#   拿蛋糕、塞進嘴、右手被拉：手臂 IK 疊在上面（走位版只表達時間點與方向）
# 座標：和 B0、B1→B2 同一套（同一段連續場景）。開頭＝B1→B2 最後一格（骨盆、面向、走路相位）。
import math, os, json
import bpy, bmesh
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
import zanim_fix as F
STATE = Z.STATE; L = Z.L; mr = Z.mr
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE, PREFIX = "ANIM_B2", "ZA_"
FPS = 30
HANDLES = 1.0
CAKE_SCENE = (4.35, 0.34, 0.62)      # 場景 scene_venue_corridor 前面托盤上的小蛋糕 I_ZP_mini_cake.009（場景座標）
B12_END = r"D:/render-work/zepeto-anim/opening-proposal-b/b1_b2/end_state.json"    # B1→B2 最後一格（骨盆、面向、走路相位）
P = dict(X=9, walk_s=-0.25, stop_b=66, turn_b=32, look=(20, 74), back=(20, 50), start_a=10,   # 2026-10-12 第 4 輪（以動作流暢為主）：停下播到停穩（第 66 格）、起步從靜止開始（第 10 格）、張望用安靜的 20～74 格
         settle=0.4, after_eat=0.7, reach_delay=0.5, go_len=2.6,      # walk_s −0.25：停下提早開始，停穩的位置才在小蛋糕前； 停穩後停幾秒才轉向餐檯、吃完停幾秒才被拉、張望開始後幾秒才伸手
        
         table_back=0.55, table_len=2.4, table_h=0.50, table_d=0.5,
         bride_scale=1.0, bride_ahead=1.1, face_sw=0.0, face_w=-3.0,
         pull_ahead=0.75)   # 拉手腕時新娘在新郎前幾 m：禮服裙擺半徑 0.32 m，0.55 m 時新郎跨步會踩進裙子（2026-10-12 量到 −75 mm）   # face_*：起步、走路的方向修正（度），試過讓結尾走路和 +X 差 0.8°   # 替身身高倍率（2026-10-12 導演端：新娘先和新郎同身形）、新娘走在新郎前面幾 m


def setup():
    r = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b2")[1]
    Z.load_clips(("male_standard_walk", "male_stop_walk", "turn_left_90", "turn_right_90", "look_around", "male_start_walk"))
    return r


def _yaw_of(fw):
    """面向向量 → 擺放用的角度（0＝朝 −Y、90＝朝 +X）"""
    return math.degrees(math.atan2(fw.x, -fw.y))


def build():
    tgt = STATE["tgt"]; end = json.load(open(B12_END))
    W, ST, TL, TR, LA, SW = (L._CL[n] for n in ("male_standard_walk", "male_stop_walk", "turn_left_90", "turn_right_90", "look_around", "male_start_walk"))
    wn = W["n"] - 1; X = P["X"]
    ph = end["phase_frame"]; a0 = int(round(ph - HANDLES * 30)) % wn     # 往前多走 1 秒（頭多做的部分）
    a1, b1, _ = F.match_phase(tgt, W, range(0, wn), ST, range(0, 16))
    # 走路：先播到這一圈結尾（a0～wn），再整圈循環，讓「停下」在鏡內 walk_s 秒開始；接停下用 match_phase 找的格子（a1）
    t1 = (wn - a0) / 30.0
    need = HANDLES + P["walk_s"] - (t1 - X / 30)          # 第二段要播幾秒（扣掉漸變重疊）
    # 第二段：從走路循環的第 0 格播 need 秒（可以不是整圈），結尾漸變進「停下」的 b1 格（走位版接受漸變；腳由鎖腳收）
    segs = [mr.Seg(W, a0, wn, name="接 B1→B2 的走路"),
            mr.Seg(W, 0, wn, loops=max(0.05, need * 30 / wn), name="走路（到餐檯前）"),
            mr.Seg(ST, b1, P["stop_b"], hold=P["settle"], name="停下（Stop Walking 前段）"),
            mr.Seg(TL, 0, P["turn_b"], add=True, name="轉向餐檯（Turn Left 90 前段）"),
            mr.Seg(LA, *P["look"], hold=P["after_eat"], name="左右張望（Standing Idle Looking Around）"),
            mr.Seg(TR, *P["back"], add=True, name="被拉回頭（Turn Right 90 中段）"),
            mr.Seg(SW, P["start_a"], SW["n"] - 1, face=STATE.get("walk_face", 90.0) + P["face_sw"], name="被拉著起步（Start Walking 後段）"),
            mr.Seg(W, 0, wn, loops=3, face=STATE.get("walk_face", 90.0) + P["face_w"], name="走路")]
    # 2026-10-12：只取一部分的左轉、右轉合起來不會剛好轉回來 → 起步、走路兩段用 face 鎖住方向（往右＝+X，和牆平行）
    segs = [x for x in segs if x is not None]
    seq = mr.Sequence(tgt, segs, blend=X / 30)
    fw = Vector(end["fw"]); hx, hy = end["hips"][0], end["hips"][1]
    yaw = _yaw_of(fw)
    for _ in range(2):                                    # 擺放：第 HANDLES 秒＝B1→B2 最後一格（位置、面向）
        seq.place(HANDLES, (hx, hy), yaw)
        R, h, _y = seq.at(HANDLES)
        f2 = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0)); f2.z = 0; f2.normalize()
        yaw += _yaw_of(fw) - _yaw_of(f2)
    seq.place(HANDLES, (hx, hy), yaw)
    idx = {sg.name: k for k, sg in enumerate(segs)}
    T = lambda nm: seq.T[idx[nm]][0]
    t_go = T("被拉著起步（Start Walking 後段）")                # 起步那一段開始（seq 時間）
    dur = t_go + P["go_len"] - HANDLES                    # 鏡內長度：起步後走回正常速度才切到 B3（第 4 輪：起步從靜止開始，要 2.6 秒）
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    poses = [seq.at(min(i / FPS, seq.dur))[:2] for i in range(n)]
    poses = [(dict(R), h.copy()) for R, h in poses]
    pts = L.sole_points(STATE["arm"])
    poses, off = F.ground(tgt, poses, pts)
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9)
    STATE.update(poses=poses, seq=seq, dur=dur, segs=[(round(seq.T[i][0] - HANDLES, 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    # 餐檯：停下的位置後方（遠離鏡頭、+Y 那側）
    t_stop = T("轉向餐檯（Turn Left 90 前段）")
    hs = poses[int(round(t_stop * FPS))][1]
    STATE["stop_xy"] = Vector((hs.x, hs.y, 0))
    STATE["t_marks"] = dict(stop=round(t_stop - HANDLES, 2), look=round(T("左右張望（Standing Idle Looking Around）") - HANDLES, 2),
                            back=round(T("被拉回頭（Turn Right 90 中段）") - HANDLES, 2), go=round(t_go - HANDLES, 2))
    # 小蛋糕的位置要在算手臂之前知道：場景座標 (4.35, 0.34, 0.62)＋和 standins() 一樣的平移
    import zanim_blocking as BK
    vo = json.load(open(BK.VENUE_OFFSET)); s0 = STATE["stop_xy"]
    STATE["cake_home"] = Vector((CAKE_SCENE[0] + vo["dx"], CAKE_SCENE[1] + vo["dy"] + s0.y, CAKE_SCENE[2]))
    _arms(poses)
    return dict(dur_s=round(dur, 2), frames=n, marks=STATE["t_marks"], ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)),
                stop_xy=tuple(round(x, 2) for x in hs[:2]), segs=STATE["segs"])


def cake_xy():
    """新郎要拿的小蛋糕（場景托盤上那塊）；還沒擺場景時先用停下位置前方估"""
    if "cake_home" in STATE:
        return STATE["cake_home"].copy()
    s = STATE["stop_xy"]
    return Vector((s.x + 0.1, s.y + P["table_back"] - 0.08, P["table_h"] + 0.03))


def _w(t, a, b, c, d):
    """梯形權重：a→b 漸入、c→d 漸出"""
    if t <= a or t >= d:
        return 0.0
    if t < b:
        x = (t - a) / (b - a)
    elif t > c:
        x = (d - t) / (d - c)
    else:
        return 1.0
    return x * x * (3 - 2 * x)


def _arms(poses):
    """左手：伸向蛋糕 → 拿起送到嘴前 → 放下；右手：被新娘往前（+X）拉直。時間照 t_marks"""
    tgt = STATE["tgt"]; m = STATE["t_marks"]
    t_reach = m["look"] + P["reach_delay"]; t_mouth = t_reach + P["pull_ahead"]; t_drop = t_mouth + 0.35
    STATE["t_marks"].update(reach=round(t_reach, 2), mouth=round(t_mouth, 2))
    for i, (R, h) in enumerate(poses):
        t = i / FPS - HANDLES
        Hd = tgt.fk(R, h)
        # 左手
        w = _w(t, t_reach - 0.4, t_reach, t_mouth + 0.15, t_drop + 0.3)
        if w > 0:
            head = Hd["J_Bip_C_Head"]
            fwd = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0)); fwd.z = 0; fwd.normalize()
            mouth = head + fwd * 0.12 + Vector((0, 0, 0.05))
            k = min(1.0, max(0.0, (t - t_reach) / (t_mouth - t_reach))); k = k * k * (3 - 2 * k)
            goal = cake_xy().lerp(mouth, k)
            cur = Hd["J_Bip_L_Hand"]
            R = mr.arm_ik(tgt, R, h, "L", cur.lerp(goal, w), Vector((0, 0, -1)))
        # 右手被拉
        w2 = _w(t, m["back"] + 0.2, m["back"] + 0.5, m["go"] + 1.2, m["go"] + 1.6)
        if w2 > 0:
            sh = Hd["J_Bip_R_UpperArm"]
            goal = sh + Vector((0.42, -0.05, -0.18))
            cur = Hd["J_Bip_R_Hand"]
            R = mr.arm_ik(tgt, R, h, "R", cur.lerp(goal, w2), Vector((0, 0, -1)))
        poses[i] = (R, h)


# ════════ 代替品 ════════
def _box(name, size, loc, col, color):
    me = bpy.data.meshes.new(name); sx, sy, sz = size
    v = [(x * sx / 2, y * sy / 2, z * sz) for x in (-1, 1) for y in (-1, 1) for z in (0, 1)]
    me.from_pydata(v, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = loc
    m = bpy.data.materials.new(name + "_mat"); b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = color; me.materials.append(m)
    return o


def standins():
    """2026-10-12：用真的 scene_venue_corridor（和 B0 同一個平移 venue_offset.json；y 再加上這一鏡新郎走路線的偏移，
    因為 B1→B2 定案版走路往鏡頭偏了約 13°，重做時會拉直）。新郎拿的是場景前面托盤上的那塊小蛋糕（I_ZP_mini_cake.009）"""
    import zanim_blocking as BK
    vo = json.load(open(BK.VENUE_OFFSET))
    s = STATE["stop_xy"]
    off = (vo["dx"], vo["dy"] + s.y, 0.0)
    objs = BK.venue("Scene_VenueCorridor", off)
    for n, o in objs.items():                             # 走廊的換景柱子是 B3 結尾用的（場景端 2026-10-12 移到 (6.16, -1.68)）：B2 結尾會蓋掉畫面 → 藏起來
        if n.startswith("I_ZP_pillar") and o.location.y < -1.0:
            o.hide_render = o.hide_viewport = True
    want = Vector((CAKE_SCENE[0] + off[0], CAKE_SCENE[1] + off[1], CAKE_SCENE[2]))      # 用位置找（再次載入時物件名的編號會變）
    cake = min((o for n, o in objs.items() if n.startswith("I_ZP_mini_cake")), key=lambda o: (o.location - want).length)
    cake.name = "ZA_Cake"; STATE["cake_home"] = cake.location.copy()
    H = STATE["measure"]["head_top"] * P["bride_scale"]
    b = BK.capsule("ZA_Bride", height=H); BK.skirt(b)
    Z.POSE_HOOKS.append(_standin_hook)
    return dict(bride_h=round(H, 3), venue_offset=tuple(round(x, 3) for x in off), cake=tuple(round(x, 2) for x in cake.location))


def bride_state(t):
    """替身：在新郎前面（+X）bride_ahead m 走 → 1.4 秒停下 → 回頭（面向 −X）走回一兩步伸手 → 2.4～抓住手腕往前拉（面向 +X）。
    時間跟著新郎的實際節點（停下、被拉回頭、起步）走，回傳 (位置, 面向角度：0＝朝 −Y)"""
    m = STATE["t_marks"]; tgt = STATE["tgt"]; poses = STATE["poses"]
    def gh(tt):
        i = max(0, min(len(poses) - 1, int(round((tt + HANDLES) * FPS))))
        return poses[i][1]
    base_y = STATE["stop_xy"].y + 0.05
    stop_x = STATE["stop_xy"].x + P["bride_ahead"] + 0.25
    if t < m["stop"]:                                     # 和新郎同速往右走，停在新郎前面
        g = gh(t); return Vector((g.x + P["bride_ahead"] + 0.25 * min(1.0, (t + 1) / (m["stop"] + 1)), base_y, 0)), 90.0
    if t < m["back"]:                                     # 停下、轉身回頭（面向 −X）、往回走到新郎前 0.55 m
        k = (t - m["stop"]) / max(0.01, m["back"] - m["stop"]); k = k * k * (3 - 2 * k)
        x = stop_x + (STATE["stop_xy"].x + P["pull_ahead"] - stop_x) * k
        return Vector((x, base_y, 0)), 90.0 + 180.0 * min(1.0, k * 2)
    g = gh(t)                                             # 拉著新郎往右走：在新郎前 0.55 m
    k = min(1.0, (t - m["back"]) / 0.4)
    return Vector((g.x + P["pull_ahead"], base_y, 0)), 270.0 - 180.0 * k


def _standin_hook(i):
    t = i / FPS - HANDLES
    b = bpy.data.objects.get("ZA_Bride")
    if b is not None:
        p, yaw = bride_state(t)
        b.location = p; b.rotation_euler = (0, 0, math.radians(yaw))
    c = bpy.data.objects.get("ZA_Cake")
    if c is not None:
        m = STATE["t_marks"]
        if t < m["reach"]:
            c.location = cake_xy(); c.hide_render = False
        elif t < m["mouth"]:                              # 在左手上
            arm = STATE["arm"]; c.location = arm.matrix_world @ arm.pose.bones["J_Bip_L_Hand"].head + Vector((0, 0, 0.02)); c.hide_render = False
        else:
            c.hide_render = True                           # 塞進嘴就消失


# ════════ 鏡頭（側面跟拍；0.8～2.6 固定；兩人中點放畫面 70%） ════════
CAP_SHIFT = 0.2


def camera_fn():
    import zanim_sample as SP
    m = STATE["t_marks"]
    follow = SP.follow_camera(offset=(0.0, -3.0, 0.25), aim_z=0.70,
                              partner=lambda i: bride_state(i / FPS - HANDLES)[0])   # 第 1 輪：對準兩人中點
    half3 = 3.0 * math.tan(math.radians(54.43 / 2)); dx3 = -2 * half3 * CAP_SHIFT
    i_hold0 = int(round((m["stop"] + HANDLES) * FPS)); i_hold1 = int(round((m["go"] + HANDLES) * FPS))
    l0, a0 = follow(i_hold0)

    def f(i):
        l, a = follow(i)
        if i_hold0 <= i <= i_hold1:                       # 停下到起步之間鏡頭固定
            l, a = l0, a0
        elif i > i_hold1:                                 # 起步後從固定位置慢慢追上
            k = min(1.0, (i - i_hold1) / 30.0); k = k * k * (3 - 2 * k)
            l = l0.lerp(l, k); a = a0.lerp(a, k)
        return l + Vector((dx3, 0, 0)), a + Vector((dx3, 0, 0))
    return f


def run():
    import time
    t0 = time.time(); setup(); r = build(); r.update(standins()); r["sec"] = round(time.time() - t0, 1)
    return r


def blocking_clip(v=1):
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", 35.0)
    objs = [bpy.data.objects[n] for n in ("ZA_Bride", "ZA_Cake")]
    out = SP.bake(objects=objs, camera_fn=camera_fn())
    path = SP.save("b2_blocking")
    cmd = SP.render_clip("b2_blocking", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + f"/blocking_v{v}.mp4")
    return dict(out, path=path, cmd=cmd)


def cleanup():
    return Z.cleanup(SCENE)


def end_state(path=r"D:/render-work/zepeto-anim/opening-proposal-b/b2/end_state.json"):
    """鏡內最後一格（t＝dur）的骨盆、面向、走路相位：下一鏡（B3）的開頭照這個接"""
    tgt = STATE["tgt"]; seq = STATE["seq"]; W = L._CL["male_standard_walk"]; wn = W["n"] - 1
    i = int(round((STATE["dur"] + HANDLES) * FPS)); R, h = STATE["poses"][i]
    fw = (R["J_Bip_C_Hips"] @ tgt.rest_q["J_Bip_C_Hips"].inverted()) @ Vector((0, -1, 0)); fw.z = 0; fw.normalize()
    t_last = seq.T[-1][0]                                 # 最後一段（走路，從第 0 格）開始的 seq 時間
    ph = ((STATE["dur"] + HANDLES - t_last) * 30) % wn
    m = STATE["t_marks"]; bp, byaw = bride_state(STATE["dur"])
    d = dict(hips=list(h), fw=list(fw), phase_frame=round(ph, 1), wn=wn, bride=list(bp), bride_yaw=byaw)
    json.dump(d, open(path, "w")); return d
