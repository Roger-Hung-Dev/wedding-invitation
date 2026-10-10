# 花園幕：②（後段）③ ⑤ ⑦ ⑧（中段）。時間一律是「這一幕開始後的秒數」（照規劃表的時間碼）。
# 每幕的 frame(t, props, cast, cam) 擺好第 t 秒：道具、角色、鏡頭（render_cast 會分開呼叫，物理子步驟只擺角色和道具）。
# 第二階段（2026-10-06）：接上動作庫的新動作 walk_fwd、pull_walk、toast、taste（工廠函式，參數照 V12 實測通過的值）。
#   walk_fwd／pull_walk 自帶世界站位（origin、dirx），時間軸用 walk_seg() 包起來；走完接 idle／bow 用 Actor 的 place(t)。
import bpy, math, random
from mathutils import Vector, Matrix

B = globals()                     # 新娘的命名空間（主）
GR = G                            # 新郎的命名空間
_built = {"garden": False}


def need_garden():
    if not _built["garden"]:
        build_garden(); _built["garden"] = True
    garden_world()


def cast_pose(actors, t):
    for a in actors:
        a.pose(t)


def turn(t, a, b, r0, r1):
    return r0 + (r1 - r0) * seg01(t, a, b)


# ══════════ ② 0:07–0:15（8 秒）後段：花園拱門，兩人從樹籬牆後走到拱門下 → 鞠躬／屈膝禮 ══════════
WALK_Y = 1.05                     # 樹籬牆後的走道（蓬裙半徑 0.5，離牆背面 0.47 要留空）
G02_END, B02_END = -0.42, 0.42
W02_G = GR["walk_fwd"](dist=1.5, steps=4, dur=3.2, dirx=1, start=0.15, end=0.25, origin=(G02_END - 1.5, WALK_Y))
W02_B = B["walk_fwd"](dist=1.2, steps=4, dur=3.2, dirx=-1, start=0.15, end=0.25, arms="skirt", origin=(B02_END + 1.2, WALK_Y))
T02_TURN = (4.0, 4.5)             # 走完原地轉向鏡頭（沒有轉身動作，腳掌原地轉）


def s02_place(W, sgn):
    def place(t):
        if t < 2.0:
            x, y = W.pos(0.0)
            return (x, y, 90 * sgn)
        x, y = W.pos(1.0)
        return (x, y, turn(t, T02_TURN[0], T02_TURN[1], 90 * sgn, 8 * sgn))
    return place


S02_G = Actor(GR, [(0, 0.8, "idle"), (0.8, 4.0, walk_seg(W02_G)), (4.0, 4.55, "idle"), (4.55, 7.55, "bow"), (7.55, 9.0, "idle")],
              s02_place(W02_G, 1), blend=0.3)
S02_B = Actor(B, [(0, 0.8, "idle"), (0.8, 4.0, walk_seg(W02_B)), (4.0, 4.55, "idle"), (4.55, 7.55, "curtsy"), (7.55, 9.0, "idle")],
              s02_place(W02_B, -1), blend=0.3)


def s02_petals(i, rnd):
    if i >= 90:
        return None
    t0 = rnd.uniform(0.3, 8.5)
    u = rnd.uniform(0.05, 0.7)
    p = arc_pt(u, ARCH_Y + rnd.uniform(-0.2, 0.2))
    return (t0, p, (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.4, -0.1), 0.0))


def s02_frame(t, props=True, cast=True, cam=True):
    if props:
        garden_parts(()); petals_update(t, s02_petals)
    if cast:
        cast_pose([S02_G, S02_B], t)
    if cam:
        u = seg01(t, 0.5, 1.6)                          # 接「掉進畫裡」：前 1 秒還在往前推一點
        look(lerpv((0, -6.4, 1.05), (0, -5.4, 0.95), u), (0, 0.8, 1.22), 36)


SHOTS["02"] = dict(set="Set_Garden", cast=True, t0=0.5, dur=8.3, tail=0.0, build=need_garden, frame=s02_frame,
                   actors=[S02_G, S02_B], qa_skip=[T02_TURN], stills=[1.2, 2.4, 3.6, 6.0])


# ══════════ ③ 0:15–0:23（8 秒）新郎拖著押花進度條走向新娘 ══════════
# pull_walk(dist1=2.0, steps1=5, walk1=2.0, stuck=0.8, steps2=2, walk2=0.8, start=0.2, end=0.4)：
#   0.2～2.2 走 2.0 m（把手 0→99%）、2.2～3.0 卡住（2.6 扯到底 → 100%）、3.0～3.8 再走約 0.58 m 到新娘身邊。
# 進度條長度照實測距離算（0→99% 的距離＝新郎 0～2.2 秒走的距離）；新郎與把手之間的緞帶水平長度 TOW。
G03_Y, B03 = -1.08, (-0.30, -0.98)
TOW = 0.55
SHOULDER03 = "L"                  # 緞帶扛左肩：新郎面向 +X，左肩在進度條那一側，緞帶往後拖不會穿過身體
_PW_ARGS = dict(dist1=2.0, steps1=5, walk1=2.0, stuck=0.8, steps2=2, walk2=0.8, start=0.2, end=0.4, dirx=1, shoulder=SHOULDER03)
_pw0 = GR["pull_walk"](origin=(0.0, G03_Y), **_PW_ARGS)
D03_TOTAL = _pw0.pos(1.0)[0] - _pw0.pos(0.0)[0]
T99 = _pw0.times["walk1"][1]                                # 2.2：走到 99%
T_YANK = _pw0.times["yank"]                                 # 2.6：扯到底
T100 = T_YANK + 0.04
D03_99 = _pw0.pos(T99 / _pw0.dur)[0] - _pw0.pos(0.0)[0]
G03_END = B03[0] - 0.80                                     # 新郎停在新娘左邊（蓬裙半徑 0.5＋新郎半身寬＋跨步時前腳的餘裕）
G03_X0 = G03_END - D03_TOTAL
PW03 = GR["pull_walk"](origin=(G03_X0, G03_Y), **_PW_ARGS)
HEAD0 = G03_X0 - TOW                                        # 把手起點（0%）
LFILL = D03_99 / 0.99
BAR_X0, BAR_X1 = HEAD0 - 0.05, HEAD0 + LFILL + 0.05         # 覆寫 set_garden 的進度條範圍（build_bar 在 build_garden 時才讀）
T03_REL = PW03.dur - 0.3                                    # 3.9：放下緞帶、轉向鏡頭
T03_TURN = (T03_REL, T03_REL + 0.5)
print("S03_GEOM total", round(D03_TOTAL, 3), "to99", round(D03_99, 3), "bar", round(BAR_X0, 3), round(BAR_X1, 3), "groom x0", round(G03_X0, 3), flush=True)


def s03_progress(t):
    if t < T99:
        d = PW03.pos(max(0.0, t) / PW03.dur)[0] - G03_X0
        return 0.99 * max(0.0, min(1.0, d / D03_99))
    return 0.99 + 0.01 * seg01(t, T_YANK - 0.05, T100)


def s03_place_g(t):
    x, y = PW03.pos(1.0)
    return (x, y, turn(t, T03_TURN[0], T03_TURN[1], 90, 35))


def s03_place_b(t):
    return (B03[0], B03[1], turn(t, 4.6, 5.0, -58, -15))      # 拍手時面向新郎，4.6 起轉向鏡頭並肩歡呼


S03_G = Actor(GR, [(0, T03_REL, walk_seg(PW03)), (T03_REL, T03_REL + 0.5, "idle"), (T03_REL + 0.5, 9.0, "wave2")], s03_place_g, blend=0.3)
# 分鏡（plan-2 V12-03 改寫版）：新娘 0～2.8 歡呼加油、2.8～4.8 拍手（新郎走到身邊、最後一朵盛開）、4.8～8.0 和新郎並肩歡呼
S03_B = Actor(B, [(0, 2.8, "cheer"), (2.8, 4.8, "clap"), (4.8, 9.0, "cheer")], s03_place_b, blend=0.3)


def s03_petals(i, rnd):
    if i < 70:                                            # 最後一朵花迸出的花瓣
        c = Vector((bud_x(N_BUDS - 1), BAR_Y - 0.05, BAR_Z))
        a = rnd.uniform(0, 2 * math.pi); s_ = rnd.uniform(0.6, 1.6)
        return (T100 + rnd.uniform(0, 0.12), c, (math.cos(a) * s_ * 0.8, -abs(math.sin(a)) * 0.6 - 0.2, rnd.uniform(0.6, 2.0)))
    t0 = T100 + rnd.uniform(0.05, 1.6)                   # 整個畫面的花瓣雨
    return (t0, (rnd.uniform(-4.6, 0.4), rnd.uniform(-1.6, 0.2), rnd.uniform(2.6, 3.4)), (0, 0, 0))


def s03_frame(t, props=True, cast=True, cam=True):
    if props:
        garden_parts(("G_Bar",))
        p = s03_progress(t)
        hold = None; shake = 0.0
        if T99 - 0.25 <= t < T100:                       # 第 10 朵：半開、顫動
            hold = 0.5 * seg01(t, T99 - 0.25, T99); shake = 7 * math.sin(2 * math.pi * 9 * t) * seg01(t, T99, T99 + 0.1)
        elif t >= T100:
            hold = 0.5 + 0.5 * seg01(t, T100, T100 + 0.22)
        head = bar_update(p, t, last_hold=hold, shake=shake)
        petals_update(t, s03_petals)
    if cast:
        cast_pose([S03_G, S03_B], t)
    if props:
        # 緞帶：把手 → 垂下 → 肩上 → 肩前的拳頭 → 前面的拳頭（動作庫 ribbon_points）；
        # 100% 時緞帶尾端從把手脫開、拖在新郎身後的草地上；3.9 秒放手，整條落到草地
        bpy.context.view_layer.update()
        far_fist, near_fist, sh = GR["ribbon_points"](SHOULDER03, GR["ARM"])
        gx = GR["ARM"].location.x
        loose = seg01(t, T100, T100 + 0.45)
        tail = head.lerp(Vector((gx - 0.75, G03_Y + 0.28, 0.012)), loose)
        drop = seg01(t, T03_REL, T03_REL + 0.45)
        if drop > 0:
            def gnd(v, dx):
                return v.lerp(Vector((v.x + dx, v.y + 0.12, 0.012)), drop)
            sh, near_fist, far_fist = gnd(sh, -0.25), gnd(near_fist, -0.1), gnd(far_fist, 0.0)
        mid = tail.lerp(sh, 0.45); mid.z = max(0.012, min(tail.z, sh.z) - 0.10 * (1 - drop))
        tow_update([tail, mid, sh, near_fist, far_fist])
    if cam:
        cx = (BAR_X0 + B03[0] + 0.5) / 2
        look((cx, -7.0, 1.2), (cx, -0.6, 1.05), 38)


SHOTS["03"] = dict(set="Set_Garden", cast=True, t0=0.0, dur=8.0, tail=0.8, build=need_garden, frame=s03_frame,
                   actors=[S03_G, S03_B], qa_skip=[T03_TURN], stills=[1.0, 2.0, 2.6, 3.4, 5.0])


# ══════════ ⑤ 0:32–0:41（9 秒）前景老相機、新人在拱門下擺姿勢；拉焦 ══════════
OC = Vector((-2.05, -2.35, 0.0))
G05, B05 = (-0.42, ARCH_Y), (0.40, ARCH_Y)


def face_to(p, q):
    d = Vector(tuple(q)[:2]) - Vector(tuple(p)[:2])
    return math.degrees(math.atan2(d.x, -d.y))


def s05_place_g(t):
    base = face_to(G05, OC)
    return (G05[0], G05[1], base + 45 * bump(t, 3.6, 4.0, 6.3, 6.7))      # lookout 時轉向左後方


def s05_place_b(t):
    return (B05[0], B05[1], face_to(B05, OC))


S05_G = Actor(GR, [(0, 3.6, "peace"), (3.6, 6.6, "lookout"), (6.6, 9.5, "nod")], s05_place_g)
def _bq_head(head_key, t_start):
    """整段捧著花（bouquet 的手、腳），頭和脖子換成 head_key（tilt 歪頭／shake 搖頭）的動作：
    tilt 原本雙手背在身後，捧花會跟著跑到腰後穿進裙子，所以只借它的頭部"""
    def fn(tl):
        P = dict(act_pose(B, "bouquet", t_start + tl))
        if head_key:
            H = act_pose(B, head_key, tl)
            P["Head"] = H.get("Head", []); P["Neck"] = H.get("Neck", [])
            P["face"] = H.get("face", P.get("face", {}))
        return P
    return fn


S05_B = Actor(B, [(0, 3.6, _bq_head(None, 0.0)), (3.6, 6.3, _bq_head("tilt", 3.6)), (6.3, 9.5, _bq_head("shake", 6.3))], s05_place_b)


def s05_frame(t, props=True, cast=True, cam=True):
    if props:
        garden_parts(("G_Cam",)); oldcam_aim((0, ARCH_Y, 1.15)); oldcam_lamp(t)
        petals_update(t, lambda i, rnd: None if i >= 40 else (rnd.uniform(0, 9), arc_pt(rnd.uniform(0.05, 0.6), ARCH_Y), (0, -0.2, 0)))
    if cast:
        cast_pose([S05_G, S05_B], t)
    if props:
        bq = bpy.data.objects["G_Bouquet"]
        bpy.context.view_layer.update()
        wl, wr = hand_frame(B, "L")[0], hand_frame(B, "R")[0]
        c = (wl + wr) / 2
        fwd = place_matrix(*s05_place_b(t)).to_3x3() @ Vector((0, -1, 0))
        Mb = (fwd * 0.5 + Vector((0, 0, 1))).to_track_quat("Z", "Y").to_matrix().to_4x4()
        Mb.translation = c + fwd * 0.03 + Vector((0, 0, 0.02))
        bq.matrix_world = Mb
    if cam:
        u = seg01(t, 0.4, 2.4)                           # 拉焦：前景老相機 → 拱門下的新人
        c = look((-1.78, -3.48, 1.35), (-1.03, 0.45, 1.07), 24)       # 老相機在左 1/3（看得到右側面＋遮光布）、新人在右後方
        d_near = (Vector((-2.05, -2.35, 1.31)) - c.location).length
        d_far = (Vector((0.0, ARCH_Y, 1.2)) - c.location).length
        c.data.dof.use_dof = True; c.data.dof.aperture_fstop = 1.2
        c.data.dof.focus_distance = d_near + (d_far - d_near) * u


SHOTS["05"] = dict(set="Set_Garden", cast=True, t0=0.0, dur=9.0, tail=0.8, build=need_garden, frame=s05_frame,
                   actors=[S05_G, S05_B], qa_skip=[(3.6, 4.0), (6.3, 6.7)], stills=[0.3, 2.8, 5.0])


# ══════════ ⑦ 0:52–1:02（10 秒）下午茶桌：乾杯 → 放下杯子、品嚐 → 鏡頭推近小黑板 ══════════
# 內側的手（新郎左手、新娘右手）拿香檳杯：toast 0～2.5 → 把杯子放到桌上 2.5～2.85 → 同一隻手 taste 捏起點心 2.85～4.9。
# 站位、碰杯方向（aim）與高度在 build 時解：兩人碰杯那一格（0.9 秒）杯身中心相距 6.5 cm、同高。
GLASS_GRIP_Z = 0.105              # 香檳杯網格：手握的位置（杯身下段）離杯底的高度
CLINK_Z = 1.30
S07 = {}


def _aim_to(a, b):
    """站在 a=(x, y, rz) 的角色看 b 在哪個方向：toast 的 aim（度，正值＝角色左邊）"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    r = math.radians(a[2])
    lx = dx * math.cos(r) + dy * math.sin(r); ly = -dx * math.sin(r) + dy * math.cos(r)
    return max(-40.0, min(40.0, math.degrees(math.atan2(lx, -ly))))


def _setdown_spec(ns, hand, place, spot, dur=0.35):
    """把杯子從胸前（toast 結束的位置）放到桌上 spot（杯底的世界座標）：用動作庫的 _solve_hand 算手腕與前臂扭轉"""
    arm = ns["ARM"]; k = ns["BODY_S"]; sg = -1 if hand == "R" else 1
    Mi = place_matrix(*place).inverted()
    H = ns["_V"](k, sg * 0.150, -0.270, 1.050)
    D = Mi @ (Vector(spot) + Vector((0, 0, GLASS_GRIP_Z)))
    off = ns["_off"]("grip", hand, k); pole = ns["_V"](k, sg * 0.45, 0.10, 0.95); up = Vector((0, 0, 1))
    cache = {}

    def fn(tl):
        u = round(ease(min(1.0, tl / dur)), 3)
        if u not in cache:
            P = {}; ns["arms_down"](P, l_fwd=4, r_fwd=4); P[f"{hand}_Hand"] = []
            W, tw = ns["_solve_hand"](arm, P, hand, H.lerp(D, u), off, pole, up)
            P["Spine"] = [("X", 4.0 * u)]
            cache[u] = dict(P, hands=("grip", "relax") if hand == "L" else ("relax", "grip"),
                            ik=[(hand, W, pole, None, "Hips")], twist=[(hand, tw)], face={"Fcl_ALL_Joy": 0.5})
        return dict(cache[u])
    return fn


def _table_pt(place, r, side_off=0.0):
    """桌面上朝向角色那一側、離桌心 r 的點；side_off＝往桌子後方（+Y 那側）偏移"""
    d = Vector((place[0] - TEA_C.x, place[1] - TEA_C.y)).normalized()
    back = Vector((-d.y, d.x))
    if back.y < 0:
        back = -back
    p = Vector((TEA_C.x, TEA_C.y)) + d * r + back * side_off
    return Vector((p.x, p.y, TEA_TOP + 0.004))


def s07_setup():
    """解站位與碰杯，建兩個角色的時間軸（第一次用到時呼叫一次）"""
    if S07.get("done"):
        return
    kg, kb = GR["BODY_S"], B["BODY_S"]
    g = [TEA_C.x - 0.40, TEA_C.y - 0.16, 42.0]; b = [TEA_C.x + 0.72, TEA_C.y - 0.20, -42.0]
    hg, hb = CLINK_Z / kg, CLINK_Z / kb
    t_clink = 0.36
    for it in range(4):
        TG = GR["toast"](hand="L", aim=_aim_to(g, b), height=hg)
        TB = B["toast"](hand="R", aim=_aim_to(b, g), height=hb)
        GR["pose_frame_at"](GR["ARM"], TG(t_clink), *g); pg = GR["hand_point"]("grip", "L", GR["ARM"], True).to_translation()
        pose_frame_at(ARM, TB(t_clink), *b); pb = hand_point("grip", "R", ARM, True).to_translation()
        dv = Vector((pb.x - pg.x, pb.y - pg.y)); gap = dv.length; u = dv.normalized()
        corr = u * (gap - 0.065)                         # 兩人各往對方靠一半
        g[0] += corr.x * 0.5; g[1] += corr.y * 0.5; b[0] -= corr.x * 0.5; b[1] -= corr.y * 0.5
        hb += (pg.z - pb.z) / kb
        print("S07_SOLVE", it, "gap", round(gap, 3), "dz", round(pg.z - pb.z, 3), flush=True)
    dist_b = (Vector((b[0], b[1])) - Vector((TEA_C.x, TEA_C.y))).length
    dist_g = (Vector((g[0], g[1])) - Vector((TEA_C.x, TEA_C.y))).length
    print("S07_PLACE groom", [round(v, 3) for v in g], "bride", [round(v, 3) for v in b], "table dist", round(dist_g, 3), round(dist_b, 3), flush=True)
    S07.update(g=tuple(g), b=tuple(b), TG=TG, TB=TB)
    for who_, ns, hand, pl, T in (("groom", GR, "L", tuple(g), TG), ("bride", B, "R", tuple(b), TB)):
        k = ns["BODY_S"]
        snack = _table_pt(pl, 0.255) + Vector((0, 0, 0.016))           # 點心中心
        glass = _table_pt(pl, 0.245, side_off=0.10)                    # 杯子放的位置（點心後方 10 cm）
        loc = place_matrix(*pl).inverted() @ snack
        pick = ((loc.x if hand == "R" else -loc.x) / k, loc.y / k, loc.z / k)
        TS = ns["taste"](hand=hand, pick=pick)
        SD = _setdown_spec(ns, hand, pl, glass)
        segs = [(0, 2.5, (lambda T_: lambda tl: T_(min(0.999, tl / 2.5)))(T)),
                (2.5, 2.85, SD),
                (2.85, 4.9, (lambda T_: lambda tl: T_(min(0.999, (tl + 0.45) / 2.5)))(TS)),
                (4.9, 10.5, "idle")]
        S07[who_] = dict(place=pl, snack=snack, glass=glass, taste=TS)
        S07["actor_" + who_] = Actor(ns, segs, (lambda p_: lambda t: p_)(pl), blend=0.25)
    SHOTS["07"]["actors"] = [S07["actor_groom"], S07["actor_bride"]]
    S07["done"] = True


def s07_build():
    need_garden(); s07_setup()


def s07_frame(t, props=True, cast=True, cam=True):
    s07_setup()
    if props:
        garden_parts(("G_Tea",)); chalk_reveal(4.9, t, per=0.1)      # 4.3～4.85 新郎拿司康的手會經過黑板前，等手離開、鏡頭推到特寫才開始寫
        petals_update(t, lambda i, rnd: None if i >= 120 else (rnd.uniform(0.9, 2.4) if i < 80 else rnd.uniform(0, 9),
                                                                  arc_pt(rnd.uniform(0.0, 1.0), ARCH_Y) + Vector((0, -0.3, 0)),
                                                                  (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.6, -0.2), 0.0)))
    if cast:
        cast_pose([S07["actor_groom"], S07["actor_bride"]], t)
    if props:
        bpy.context.view_layer.update()
        for who_, ns, hand, snack_obj in (("groom", GR, "L", "G_HandScone"), ("bride", B, "R", "G_HandMacaron")):
            d = S07[who_]
            fl = bpy.data.objects[f"G_Flute_{who_}"]
            if t < 2.85:                                 # 杯子在手上（保持直立）→ 2.85 秒放到桌上
                fl.matrix_world = ns["hand_point"]("grip", hand, ns["ARM"], True) @ Matrix.Translation((0, 0, -GLASS_GRIP_Z))
            else:
                fl.matrix_world = Matrix.Translation(d["glass"])
            o = bpy.data.objects[snack_obj]; o.hide_render = False
            if t < 2.85 + (0.6 - 0.45):                  # taste 第 0.6 秒捏起點心之前，點心在桌上
                o.matrix_world = Matrix.Translation(d["snack"])
            else:
                o.matrix_world = Matrix.Translation(ns["hand_point"]("pinch", hand, ns["ARM"]).to_translation())
    if cam:
        u = seg01(t, 4.0, 5.0)
        bd = Vector((TEA_C.x + BOARD_LOC[0], TEA_C.y + BOARD_LOC[1] + 0.02, TEA_TOP + 0.13))
        look(lerpv((0.2, -4.7, 1.45), (bd.x + 0.05, bd.y - 0.46, bd.z + 0.05), u), lerpv((0.2, -0.6, 0.98), bd + Vector((0.02, 0, 0)), u), 35)


SHOTS["07"] = dict(set="Set_Garden", cast=True, t0=0.0, dur=10.0, tail=0.0, build=s07_build, frame=s07_frame,
                   actors=[], stills=[0.9, 1.6, 2.8, 3.6, 4.4, 6.0])


# ══════════ ⑧ 1:02–1:12（10 秒）中段 6.2～9.0：穿過拱門小畫進入花園，新人在拱門下 ══════════
S08_G = Actor(GR, [(5.5, 6.4, "idle"), (6.4, 10.4, "wave2")], lambda t: (-0.42, ARCH_Y, 8))
S08_B = Actor(B, [(5.5, 6.4, "idle"), (6.4, 10.4, "heart")], lambda t: (0.40, ARCH_Y, -8))


def s08_petals(i, rnd):
    t0 = rnd.uniform(5.8, 9.4)
    return (t0, (rnd.uniform(-1.2, 1.2), rnd.uniform(0.2, 0.8), rnd.uniform(1.0, 2.6)), (rnd.uniform(-0.4, 0.4), rnd.uniform(-3.0, -1.8), rnd.uniform(-0.2, 0.4)))


def s08_frame(t, props=True, cast=True, cam=True):
    if props:
        garden_parts(()); petals_update(t, s08_petals)
    if cast:
        cast_pose([S08_G, S08_B], t)
    if cam:
        u = seg01(t, 5.8, 9.4)
        look(lerpv((0, -8.5, 1.5), (0, -4.7, 1.22), 1 - (1 - u) ** 2), (0, ARCH_Y, 1.2), 35)


SHOTS["08"] = dict(set="Set_Garden", cast=True, t0=5.8, dur=3.6, tail=0.0, build=need_garden, frame=s08_frame,
                   actors=[S08_G, S08_B], stills=[6.6, 8.0])
