# B0（開場影片提案 B）：新郎推開休息室的門走出來 → 左轉 90° → 往畫面右邊走，接 B1→B2 的第 0 秒。新娘在新郎後面、遠側。
# 走位版（2026-10-12，使用者同意素材未齊先做走位）：新娘用替身（灰色膠囊，身高＝新郎 × 0.95，身體端給數字再換），
# 門、牆用灰色方塊；不做手指接觸、兩人接觸、穿模檢查、近照確認頁、定案。
# 動作（使用者 2026-10-12 選「先用現有的拼」：本機沒有開門、邊走邊轉的 Mixamo）：
#   male_start_walk（起步）→ male_standard_walk（走出門）→ turn_left_90（原地左轉，用加法段只取腳步與轉向）→ male_standard_walk（往右走）
#   推門：右手用手臂 IK 貼在門板上、跟著門轉開（門往外推、人靠近門用手帶身體推：Animation Mentor 開門教學）
# 座標：和 B1→B2 同一套。B0 結尾（新郎走路）＝B1→B2 第 0 秒：骨盆 (0, 0)、往 +X 走、走路相位接得上（同一支走路、同一格）。
# 鏡頭在 −Y 那一側（看 +Y），+X＝畫面右邊。門在後牆（y＝DOOR_Y），往 −Y（朝鏡頭）推開，鉸鏈在 −X 那一側（門扇擺到左邊，不擋往右走的路）。
# 用法（MCP）：
#   # BODY=groom
#   import sys; sys.path.insert(0, r"D:/SideProject/wedding-invitation/.claude/skills/zepeto-animation-generation-workflow/scripts")
#   import zanim as Z; Z.use_shot("opening-proposal-b", "b0"); import b0_shot as S; print(S.run())
import math, os, json
import bpy
from mathutils import Vector, Quaternion, Matrix
import zanim as Z
import zanim_fix as F
import zanim_blocking as BK
STATE = Z.STATE; L = Z.L; mr = Z.mr
HERE = os.path.dirname(os.path.abspath(__file__))
SCENE, PREFIX = "ANIM_B0", "ZA_"
FPS = 30
HANDLES = 1.0                    # film.json handles_s：頭尾各多做 1 秒
P = dict(a1=58, walk_out=0.9, face_fix=-1.0, X=9, stop_a=30, stop_b=66, settle=0.3, start_a=10, venue=(-0.654, 0.0),   # 第 3 輪：從 Stop Walking 第 stop_a 格附近接上、播到停穩、停穩後與轉完各停 settle 秒、起步從靜止那格開始             # 起步用到第幾格附近、走出門走幾圈、往右走的方向修正（度）、漸變格數
         door_w=0.75, door_h=1.75,          # 門照 ZEPETO 比例（角色 1.48 m；真實 2.1 m 的門會顯得太大）
         door_open_deg=85.0, door_t=(0.25, 1.0),
         bride_scale=1.0, bride_back=0.45, bride_lag=0.25, bride_behind_x=0.4)   # 替身身高倍率（2026-10-12 導演端：新娘先和新郎同身形）、在新郎後方（遠側）幾 m、晚幾秒、往左落後幾 m（側面鏡頭看，完全並排會被新郎擋住）


def setup():
    r = Z.setup(body="groom", scene=SCENE, prefix=PREFIX)
    STATE["out_dir"] = Z.use_shot("opening-proposal-b", "b0")[1]
    Z.load_clips(("male_start_walk", "turn_left_90", "male_standard_walk", "male_stop_walk"))
    return r


def build():
    """接段 → 擺放（結尾對齊 B1→B2 第 0 秒）→ 每格姿勢（含頭尾多做）→ 貼地、鎖腳 → 推門的手 → 門、替身、鏡頭的時間線"""
    tgt = STATE["tgt"]
    SW, TL, W, ST = (L._CL[n] for n in ("male_start_walk", "turn_left_90", "male_standard_walk", "male_stop_walk"))
    wn = W["n"] - 1; X = P["X"]
    # 2026-10-12 第 3 輪（以動作流暢為主）：走出門 → 減速停穩（Stop Walking 後段）→ 停一下 → 原地左轉 → 從靜止起步 → 走路。
    # 舊版是邊走邊疊原地轉身：0.4 秒內從 0.5 m/s 急停、轉完立刻全速
    a, b, _d = F.match_phase(tgt, SW, range(P["a1"] - 8, P["a1"] + 1), ST, range(P["stop_a"] - 8, P["stop_a"] + 8))
    a2, b2, _d2 = F.match_phase(tgt, SW, range(SW["n"] - 20, SW["n"] - 1), W, range(0, wn))
    segs = [mr.Seg(SW, 0, a + X, name="起步（Start Walking）"),
            mr.Seg(ST, b, P["stop_b"], hold=P["settle"], name="走出門、減速停下（Stop Walking 後段）"),
            mr.Seg(TL, add=True, hold=P["settle"], name="左轉 90°（Turn Left 90，只取腳步與轉向）"),
            mr.Seg(SW, P["start_a"], a2 + X, face=90.0 + P["face_fix"], name="起步往右（Start Walking）"),
            mr.Seg(W, b2, wn, loops=4, name="往右走（Walking）")]
    seq = mr.Sequence(tgt, segs, blend=X / 30)
    seq.place(0.0, (0.0, 0.0), 0.0)                       # 先擺：開頭面向 −Y（朝鏡頭）
    t_end = seq.T[4][0] + X / 30 + ((wn - b2) % wn) / 30  # 往右走那一段到走路第 0 格（相位和 B1→B2 第 0 秒一樣）
    shift = -Vector((*seq.at(t_end)[1][:2], 0.0))         # 整條平移：t_end 的骨盆到 (0, 0)
    dur = t_end                                           # 鏡內秒數（B0 正片）
    n = int(round((dur + 2 * HANDLES) * FPS)) + 1
    poses = []
    for i in range(n):
        t = i / FPS - HANDLES                             # 鏡內秒數（−1 ～ dur＋1）
        R, h, _y = seq.at(min(max(t, 0.0), seq.dur))      # 開頭多做的 1 秒：停在第一格（手已搭在門上）
        if t > seq.dur:
            R, h, _y = seq.at(seq.dur)
        poses.append((dict(R), h + shift))
    pts = L.sole_points(STATE["arm"])
    poses, off = F.ground(tgt, poses, pts)
    poses, _li = F.foot_lock(tgt, poses, pts, v_on=0.3, ramp=9)
    STATE.update(poses=poses, seq=seq, segs=[(round(seq.T[i][0], 2), round(s.dur, 2), s.name) for i, s in enumerate(segs)])
    # 門：手搭的位置＝第一格右手掌心正前方；門線在掌心前 1 cm
    Hd = tgt.fk(*poses[0]); c = Hd["J_Bip_R_Hand"]
    STATE["door_y"] = c.y - 0.05
    STATE["hinge_x"] = c.x - 0.5                           # 手搭在離鉸鏈 50 cm 的地方（門寬 75 cm）
    STATE["hand_h"] = c.z
    # 第 3 輪：走廊固定在 B2、B3 調好的位置（VENUE），整段平移讓門中心對上。
    # 結尾不再是 (0, 0)：B1→B2 重做時從 end_xy 接（少走那一段）
    vx, vy = P["venue"]
    d = Vector((vx - (STATE["hinge_x"] + P["door_w"] / 2), vy - (STATE["door_y"] - 0.75), 0.0))
    poses[:] = [(R, h + d) for R, h in poses]
    STATE["hinge_x"] += d.x; STATE["door_y"] += d.y
    STATE["end_xy"] = (round(d.x, 3), round(d.y, 3))
    _push(poses)
    STATE["dur"] = dur
    STATE["walk_y"] = STATE["end_xy"][1]
    return dict(dur_s=round(dur, 2), frames=n, cut=(a, b), ground_mm=(round(1000 * min(off), 1), round(1000 * max(off), 1)),
                door_y=round(STATE["door_y"], 2), walk_line_from_door=round(STATE["door_y"] - STATE["end_xy"][1], 2), end_xy=STATE["end_xy"],
                segs=STATE["segs"])


def door_angle(t):
    a0, a1 = P["door_t"]
    s = min(1.0, max(0.0, (t - a0) / (a1 - a0))); s = s * s * (3 - 2 * s)
    return math.radians(P["door_open_deg"]) * s


def door_point(t, along=0.5, z=None):
    """門板上離鉸鏈 along m 的點（世界座標）；門往 −Y 推開（鉸鏈在 −X 那一側、逆時針看是往 −Y 轉）"""
    th = door_angle(t)
    hx, dy = STATE["hinge_x"], STATE["door_y"]
    return Vector((hx + along * math.cos(th), dy - along * math.sin(th), STATE["hand_h"] if z is None else z))


def _push(poses):
    """右手貼在門板上跟著門轉開：0～1.0 秒全重，1.0～1.3 秒放開回原片手臂"""
    tgt = STATE["tgt"]
    for i, (R, h) in enumerate(poses):
        t = i / FPS - HANDLES
        w = 1.0 if t <= 1.0 else max(0.0, 1.0 - (t - 1.0) / 0.3)
        if w <= 0:
            continue
        Hd = tgt.fk(R, h)
        goal = door_point(t) + Vector((0, 0.02, 0))        # 手腕在門板後面一點點（掌心貼門）
        cur = Hd["J_Bip_R_Hand"]
        pole = Vector((-0.3, 0.3, -1.0))                    # 手肘往下、往外
        R2 = mr.arm_ik(tgt, R, h, "R", cur.lerp(goal, w), pole)
        # 掌心朝門板（往 −Y 推）、手指朝上
        q = Quaternion((0, 0, 1), -door_angle(t))          # 門往 −Y 推開＝從上面看順時針轉
        R2 = mr.aim_hand(tgt, R2, h, "R", (q @ Vector((0, 0, 1))), palm=q @ Vector((0, -1, 0)), palm_w=w, max_bend=None)
        poses[i] = (R2, h)


# ════════ 代替品：牆、門、新娘替身 ════════
def _box(name, size, loc, col, color=(0.6, 0.6, 0.6, 1)):
    me = bpy.data.meshes.new(name)
    sx, sy, sz = size
    v = [(x * sx / 2, y * sy / 2, z * sz) for x in (-1, 1) for y in (-1, 1) for z in (0, 1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(v, [], f)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = loc
    m = bpy.data.materials.get(name + "_mat") or bpy.data.materials.new(name + "_mat")
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); b.inputs["Base Color"].default_value = color
    me.materials.append(m)
    return o


def standins():
    """2026-10-12 場景端照走位改好走廊（牆 y＝0.75、門 0.75×1.75、門軸在左）：用真的 scene_venue_corridor。
    場景座標的休息室門中心在 x＝0 → 整組平移到動畫座標的門中心（記進 venue_offset.json，B2、B3 照同一個平移）。
    場景裡關著的門（實例）藏起來，另外複製一扇 lounge_door、門片 ZP_lounge_door_leaf 跟著推門轉開"""
    import zanim_blocking as BK
    dc = STATE["hinge_x"] + P["door_w"] / 2
    off = (P["venue"][0], P["venue"][1], 0.0)             # 第 3 輪起固定（build 已把新郎平移到門前）
    json.dump(dict(dx=off[0], dy=off[1], note="場景座標＋(dx, dy)＝動畫座標（休息室門中心；走廊同一段場景 B0～B3 共用；2026-10-12 第 3 輪起固定，B0 結尾改在 end_xy）"), open(BK.VENUE_OFFSET, "w"))
    objs = BK.venue("Scene_VenueCorridor", off)
    for n, o in objs.items():
        if n.startswith("I_ZP_lounge_door"):
            o.hide_render = True; o.hide_viewport = True
    g = BK.props_api(); dcol = g["append_prop"]("lounge_door", parent=Z.studio_col())
    leaf = None
    for o in dcol.all_objects:
        if o.parent is None:
            o.location = o.location + Vector((dc, STATE["door_y"], 0))
        if o.name.startswith("ZP_lounge_door_leaf"):
            leaf = o
    leaf.name = "ZA_DoorLeaf"
    b = BK.capsule("ZA_Bride", height=STATE["measure"]["head_top"] * P["bride_scale"])
    BK.skirt(b)
    Z.POSE_HOOKS.append(_standin_hook)
    return dict(venue_offset=tuple(round(x, 3) for x in off), bride_h=round(STATE["measure"]["head_top"] * P["bride_scale"], 3))


def bride_xy(t):
    """替身路線：門內等 → 跟著走出門 → 左轉 → 在新郎左手邊（遠側、後方 bride_back m）往右走；時間比新郎晚 bride_lag 秒"""
    tgt = STATE["tgt"]; poses = STATE["poses"]
    i = max(0, min(len(poses) - 1, int(round((t - P["bride_lag"] + HANDLES) * FPS))))
    gh = poses[i][1]
    t0 = 0.0
    # 新郎的路線往後（+Y）平移 bride_back、往 −X 退半步：遠側並肩
    p = Vector((gh.x - P["bride_behind_x"], gh.y + P["bride_back"], 0))
    # 新郎還在門裡（出門前）時，替身在他正後方
    if gh.y > STATE["door_y"] - 0.2:
        p = Vector((gh.x, gh.y + 0.5, 0))
    return p


def _standin_hook(i):
    t = i / FPS - HANDLES
    d = bpy.data.objects.get("ZA_DoorLeaf")
    if d is not None:
        d.rotation_euler = (0, 0, -door_angle(t))               # 門片原點在門軸；0 → −85° 往鏡頭這側開
    b = bpy.data.objects.get("ZA_Bride")
    if b is not None:
        b.location = bride_xy(t)


# ════════ 鏡頭 ════════
CAP_SHIFT = 0.2        # 字卡留白左邊 40% → 主體（第 1 輪起＝兩人中點）放在畫面 70% 處：鏡頭往左偏「畫面寬 × 0.2」


def camera_fn():
    """0～1.6 秒固定（門在畫面右側 60% 的中間）；1.6～3.0 秒轉成側面跟拍（新郎右手側 3 m、比骨盆高 0.25 m），
    跟拍規則和 B1→B2 共用：鏡頭在骨盆 −Y 3 m、看向骨盆高度 0.70 m、主體（第 1 輪起＝兩人中點）放在畫面 70%（35 mm：3 m 處畫面寬 3.08 m）"""
    import zanim_sample as SP
    arm = STATE["arm"]; n = len(STATE["poses"])
    follow = SP.follow_camera(offset=(0.0, -3.0, 0.25), aim_z=0.70,
                              partner=lambda i: bride_xy(i / FPS - HANDLES))   # 第 1 輪：對準兩人中點
    half3 = 3.0 * math.tan(math.radians(54.43 / 2))
    dx3 = -2 * half3 * CAP_SHIFT
    dyd = STATE["door_y"]; hx = STATE["hinge_x"]
    door_c = Vector((hx + P["door_w"] / 2, dyd, 0.70))
    half35 = 3.5 * math.tan(math.radians(54.43 / 2))
    fixed_aim = door_c + Vector((-2 * half35 * CAP_SHIFT, 0, 0))
    fixed_loc = fixed_aim + Vector((0, -3.5, 0.25))

    def f(i):
        t = i / FPS - HANDLES
        l, a = follow(i)
        l = l + Vector((dx3, 0, 0)); a = a + Vector((dx3, 0, 0))
        s = min(1.0, max(0.0, (t - 1.6) / 1.4)); s = s * s * (3 - 2 * s)
        return fixed_loc.lerp(l, s), fixed_aim.lerp(a, s)
    return f


def run():
    import time
    t0 = time.time()
    setup(); r = build(); r.update(standins()); r["sec"] = round(time.time() - t0, 1)
    return r


def blocking_clip(v=1):
    """走位版：存樣張（不登記總表：還沒定案）→ 回傳背景渲短片的指令"""
    import zanim_sample as SP
    SP.new_camera("SAMPLE_Cam", 35.0)
    out = SP.bake(objects=[bpy.data.objects["ZA_DoorLeaf"], bpy.data.objects["ZA_Bride"]], camera_fn=camera_fn())
    path = SP.save("b0_blocking")
    cmd = SP.render_clip("b0_blocking", 0.0, len(STATE["poses"]) / FPS - 0.04, STATE["out_dir"] + f"/blocking_v{v}.mp4")
    return dict(out, path=path, cmd=cmd)


def cleanup():
    return Z.cleanup(SCENE)
