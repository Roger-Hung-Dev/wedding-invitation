# 第 3 關第 3 輪（2026-10-11）回饋「⑦ 拆成兩幕」的第二幕 ⑦b 喝酒不開車：晚上的餐廳門口＋卡通計程車＋新郎醉紅的臉頰。
#   mx_preview 的 SID=07b 才載入（use("set_v3_street")）；登記成 SHOTS["v3_07b"]（集合 Set_Street，花園景整個關掉）。
# 世界座標：人行道面 z 0（y 0～3.2），馬路 z −0.12（y < 0），路緣在 y 0；餐廳門面在 y 3.2（正面朝 −y），門在 x −0.35～0.55。
# 計程車停在路邊、車頭朝 −X（台灣靠右行駛，右側貼著路緣）：車身右側 y −0.02、左側 −1.87；車頭 x −2.25、車尾 2.05；車頂 1.60。
#   尺寸照新郎（mx_scene_07b）實際的動作量：右後門轉軸 x 0.18、門寬 0.88（門把在 x 0.70、高 0.94＝他 4.0～4.2 秒摸到的地方）；
#   門的開口上緣 1.48（鑽進去時頭頂最高 1.38＋頭髮）；車內地板 0.24、後座座墊 0.72（坐好時骨盆 0.84）、靠背前緣 x 0.72。
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

TAXI = dict(front=-2.25, rear=2.05, right=-0.02, left=-1.87, road=-0.12, belt=0.95, roof=1.60, wheel_r=0.30,
            hinge=(0.18, -0.02), door_w=0.88, door_z=(0.28, 1.48), handle=(0.52, 0.94), axle=(-1.45, 1.45))
ST = {}


def _m(name, hexc, **kw):
    return pmat(name, srgb(hexc), **kw)


def _night_world():
    w = bpy.context.scene.world
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (*srgb("#1B2A4A"), 1.0); bg.inputs[1].default_value = 0.55


def _light(c, name, kind, loc, energy, color, size=0.1, rot=None, spot=None):
    ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, kind)
    ld.energy = energy; ld.color = color
    try:
        ld.shadow_soft_size = size
    except Exception:
        pass
    if kind == "AREA":
        ld.size = size
    if spot and kind == "SPOT":
        ld.spot_size = math.radians(spot); ld.spot_blend = 0.6
    o = bpy.data.objects.get(name) or bpy.data.objects.new(name, ld)
    if o.name not in c.objects:
        c.objects.link(o)
    o.location = loc
    if rot:
        o.rotation_euler = rot
    return o


def build_street():
    """晚上的街景：人行道＋路緣、馬路（車道線）、餐廳門面（暖光的玻璃門、兩扇窗、遮雨棚、招牌、盆栽）、路燈、對面的房子剪影"""
    c = coll_new("Set_Street"); coll_clear("Set_Street")
    random.seed(5)
    M = dict(walk=_m("V3_Sidewalk", "#B8B0A6", rough=0.85, noise=0.25), curb=_m("V3_Curb", "#D2CCC4", rough=0.8, noise=0.15),
             road=_m("V3_Asphalt", "#3A3D44", rough=0.9, noise=0.3), line=_m("V3_RoadLine", "#E8E4D8", rough=0.7),
             wall=_m("V3_Wall", "#C9A88A", rough=0.85, noise=0.2), trim=_m("V3_WoodTrim", "#5A3B2A", rough=0.6),
             glow=_m("V3_WindowGlow", "#FFD9A0", rough=0.3, emit=2.2), awn=_m("V3_Awning", "#8E2A36", rough=0.7, sheen=0.4),
             awn2=_m("V3_Awning2", "#F3E6CF", rough=0.7), sign=_m("V3_Sign", "#F6EFE6", rough=0.6, emit=0.6),
             gold=_m("V3_SignGold", "#C9A45C", rough=0.35, metal=0.6), pot=_m("V3_Pot", "#7A5A48", rough=0.7),
             leaf=_m("V3_PotLeaf", "#4F7A45", rough=0.8, noise=0.2), pole=_m("V3_LampPole", "#2E3138", rough=0.4, metal=0.6),
             bulb=_m("V3_LampBulb", "#FFE2B0", rough=0.3, emit=6.0), far=_m("V3_FarHouse", "#2A3550", rough=0.9),
             farwin=_m("V3_FarWin", "#F5C77A", rough=0.4, emit=1.4), hedge=_m("V3_StreetHedge", "#3E5A3A", rough=0.9, noise=0.3),
             rose=_m("V3_SignRose", "#D9777F", rough=0.6, emit=0.3))
    bm = MB()
    box(bm, Vector((0, 1.6 + 0.075, -0.06)), (16.0, 3.2 - 0.15, 0.12), mi=0)             # 人行道（面 z 0）
    box(bm, Vector((0, 0.075, -0.06)), (16.0, 0.15, 0.12), mi=1)                         # 路緣石
    box(bm, Vector((0, -6.0, -0.13)), (16.0, 12.0, 0.02), mi=2)                          # 馬路（面 z −0.12）
    for k in range(-8, 9):                                                               # 車道虛線
        box(bm, Vector((k * 1.0, -3.9, -0.118)), (0.55, 0.12, 0.004), mi=3)
    for k in range(-15, 16):                                                             # 人行道磚縫
        box(bm, Vector((k * 0.5, 1.68, 0.0005)), (0.01, 3.0, 0.001), mi=1)
    mesh_obj("V3_Ground", bm, [M["walk"], M["curb"], M["road"], M["line"]], c)
    bm = MB()                                                                            # 餐廳門面
    for x0, x1 in ((-8.0, -0.35), (0.55, 8.0)):
        box(bm, Vector(((x0 + x1) / 2, 3.35, 1.75)), (x1 - x0, 0.3, 3.5), mi=0)
    box(bm, Vector((0.1, 3.35, 2.85)), (0.9, 0.3, 1.3), mi=0)                            # 門上方的牆
    for x in (-0.35, 0.55):
        box(bm, Vector((x, 3.19, 1.1)), (0.08, 0.06, 2.2), mi=1)                         # 門框
    box(bm, Vector((0.1, 3.19, 2.22)), (0.98, 0.06, 0.08), mi=1)
    box(bm, Vector((0.1, 3.3, 1.1)), (0.82, 0.04, 2.16), mi=2)                           # 玻璃門（裡面亮著暖光）
    box(bm, Vector((0.1, 3.27, 1.1)), (0.03, 0.03, 2.16), mi=1)                          # 雙開門中縫
    for wx in (-2.1, 2.3):                                                               # 兩扇大窗
        box(bm, Vector((wx, 3.3, 1.4)), (2.0, 0.04, 1.5), mi=2)
        for dx in (-1.0, 0.0, 1.0):
            box(bm, Vector((wx + dx, 3.19, 1.4)), (0.06, 0.06, 1.56), mi=1)
        for z in (0.65, 2.15):
            box(bm, Vector((wx, 3.19, z)), (2.06, 0.07, 0.07), mi=1)
    mesh_obj("V3_Facade", bm, [M["wall"], M["trim"], M["glow"]], c)
    bm = MB()                                                                            # 遮雨棚（紅白條紋，往外斜）
    for k in range(8):
        x = -0.55 + 0.165 * k + 0.0825
        box(bm, Vector((x, 2.95, 2.42)), (0.165, 0.62, 0.025), rot=Matrix.Rotation(math.radians(-18), 4, "X"), mi=k % 2)
    mesh_obj("V3_Awning", bm, [M["awn"], M["awn2"]], c)
    bm = MB(); box(bm, Vector((0.1, 3.17, 2.95)), (1.6, 0.05, 0.42), mi=0)               # 招牌（米白發光底、金框、一排小花，不寫字）
    for z in (2.75, 3.15):
        box(bm, Vector((0.1, 3.14, z)), (1.64, 0.03, 0.03), mi=1)
    for x in (-0.71, 0.91):
        box(bm, Vector((x, 3.14, 2.95)), (0.03, 0.03, 0.43), mi=1)
    for k in range(5):
        ball(bm, Vector((-0.4 + 0.25 * k, 3.13, 2.95)), 0.05, mi=2, seg=12)
    mesh_obj("V3_Sign", bm, [M["sign"], M["gold"], M["rose"]], c, smooth=True)
    bm = MB()                                                                            # 門口兩盆植物
    for x in (-0.75, 0.95):
        cyl(bm, Vector((x, 2.95, 0.22)), 0.2, 0.44, seg=20, r2=0.24, mi=0)
        for k in range(9):
            a = 2 * math.pi * k / 9
            ball(bm, Vector((x + 0.14 * math.cos(a), 2.95 + 0.14 * math.sin(a), 0.6 + random.uniform(0, 0.25))), 0.15, mi=1, seg=10)
        ball(bm, Vector((x, 2.95, 0.9)), 0.17, mi=1, seg=10)
    mesh_obj("V3_Pots", bm, [M["pot"], M["leaf"]], c, smooth=True)
    bm = MB()                                                                            # 路燈（兩盞）
    for lx in (-1.7, -6.8):
        cyl(bm, Vector((lx, 0.35, 1.65)), 0.05, 3.3, seg=12, mi=0)
        cyl(bm, Vector((lx, 0.35, 0.08)), 0.11, 0.16, seg=12, mi=0)
        cyl(bm, Vector((lx, 0.1, 3.3)), 0.025, 0.55, axis="Y", seg=8, mi=0)
        cyl(bm, Vector((lx, -0.18, 3.22)), 0.16, 0.12, seg=16, r2=0.06, mi=0)
        ball(bm, Vector((lx, -0.18, 3.13)), (0.12, 0.12, 0.05), mi=1, seg=12)
    mesh_obj("V3_StreetLamps", bm, [M["pole"], M["bulb"]], c, smooth=True)
    bm = MB()                                                                            # 對面的房子剪影＋亮著的窗、路邊矮樹叢
    for k in range(7):
        x = -8 + 2.6 * k + random.uniform(-0.2, 0.2); w_ = random.uniform(2.0, 2.4); h = random.uniform(3.5, 6.0)
        box(bm, Vector((x, -10.5, h / 2 - 0.12)), (w_, 2.0, h), mi=0)
        for j in range(int(h // 1.3)):
            for i in range(2):
                if random.random() < 0.7:
                    box(bm, Vector((x - 0.45 + 0.9 * i, -9.48, 0.9 + 1.25 * j)), (0.55, 0.04, 0.7), mi=1)
    for k in range(30):
        ball(bm, Vector((-8 + 0.55 * k, -8.6, 0.25)), (0.4, 0.35, 0.45), mi=2, seg=10)
    mesh_obj("V3_FarStreet", bm, [M["far"], M["farwin"], M["hedge"]], c, smooth=True)
    # 燈光：月光（冷）、路燈（暖）、餐廳門窗透出來的暖光、鏡頭側的補光
    _light(c, "V3_Moon", "SUN", (0, 0, 10), 0.35, (0.62, 0.72, 1.0), rot=(math.radians(55), 0, math.radians(-30)))
    for i, lx in enumerate((-1.7, -6.8)):
        _light(c, f"V3_LampL{i}", "POINT", (lx, -0.18, 3.0), 260.0, (1.0, 0.80, 0.55), size=0.15)
    _light(c, "V3_DoorGlow", "AREA", (0.1, 3.05, 2.1), 90.0, (1.0, 0.78, 0.52), size=1.0, rot=(math.radians(70), 0, 0))
    _light(c, "V3_WinGlowL", "AREA", (-2.1, 3.05, 1.5), 70.0, (1.0, 0.78, 0.52), size=1.6, rot=(math.radians(75), 0, 0))
    _light(c, "V3_WinGlowR", "AREA", (2.3, 3.05, 1.5), 70.0, (1.0, 0.78, 0.52), size=1.6, rot=(math.radians(75), 0, 0))
    _light(c, "V3_Fill", "AREA", (4.0, 0.5, 2.6), 60.0, (0.85, 0.88, 1.0), size=2.0, rot=(math.radians(55), 0, math.radians(70)))
    _night_world()
    return c


def build_taxi(c):
    """卡通黃色計程車（車頭朝 −X）。全部掛在 V3_Taxi（開走時整台平移），右後門掛在轉軸 V3_TaxiHinge（繞 Z 開門），輪子各自轉"""
    T = TAXI
    M = dict(body=_m("V3_TaxiYellow", "#F4C430", rough=0.25, spec=0.6, coat=0.5), dark=_m("V3_TaxiTrim", "#26282E", rough=0.5),
             glass=_m("V3_TaxiGlass", "#1C2430", rough=0.08, spec=0.9, coat=0.4), inner=_m("V3_TaxiInner", "#2A2724", rough=0.85),
             seat=_m("V3_TaxiSeat", "#4A4038", rough=0.8, noise=0.15), tire=_m("V3_Tire", "#1A1A1C", rough=0.9),
             hub=_m("V3_Hub", "#C8CBD0", rough=0.25, metal=0.8), head=_m("V3_HeadLight", "#FFF4D6", rough=0.2, emit=4.0),
             tail=_m("V3_TailLight", "#E0303A", rough=0.3, emit=1.4), sign=_m("V3_TaxiSign", "#FFF6D8", rough=0.4, emit=2.5),
             chrome=_m("V3_Chrome", "#D8D8DC", rough=0.15, metal=1.0), signtxt=_m("V3_TaxiSignText", "#1E1E22", rough=0.5))
    root = empty("V3_Taxi", c, (0, 0, 0))
    fr, re, R, L, rd, belt, roof = T["front"], T["rear"], T["right"], T["left"], T["road"], T["belt"], T["roof"]
    hx, hy = T["hinge"]; dw = T["door_w"]; dz0, dz1 = T["door_z"]
    W = R - L
    cy = (R + L) / 2
    bot = rd + 0.27                                                                    # 車身底（輪子露出下半）
    bm = MB()
    # 下半車身：左側整片、右側在後門開口前後兩段＋門檻、車頭（引擎蓋）、車尾（後車廂）、車底、車內地板
    box(bm, Vector(((fr + re) / 2, L + 0.05, (bot + belt) / 2)), (re - fr, 0.10, belt - bot), mi=0)
    box(bm, Vector(((fr + hx) / 2, R - 0.05, (bot + belt) / 2)), (hx - fr, 0.10, belt - bot), mi=0)
    box(bm, Vector(((hx + dw + re) / 2, R - 0.05, (bot + belt) / 2)), (re - hx - dw, 0.10, belt - bot), mi=0)
    box(bm, Vector((hx + dw / 2, R - 0.05, (bot + dz0) / 2)), (dw, 0.10, dz0 - bot), mi=0)
    box(bm, Vector(((fr + (-1.0)) / 2, cy, (bot + belt + 0.02) / 2)), (-1.0 - fr, W - 0.2, belt + 0.02 - bot), mi=0)
    box(bm, Vector(((1.25 + re) / 2, cy, (bot + belt + 0.04) / 2)), (re - 1.25, W - 0.2, belt + 0.04 - bot), mi=0)
    box(bm, Vector(((fr + re) / 2, cy, bot + 0.02)), (re - fr - 0.1, W - 0.1, 0.04), mi=2)
    box(bm, Vector(((-1.0 + 1.25) / 2, cy, 0.22)), (2.25, W - 0.2, 0.04), mi=2)
    # 上半：車頂、A／B／C 柱、前擋、後擋（暗色玻璃）、左側車窗、右前車窗
    box(bm, Vector(((-1.05 + 1.35) / 2, cy, roof - 0.04)), (2.4, W - 0.06, 0.08), mi=0)
    for px, pw in ((-1.05, 0.10), (hx - 0.04, 0.08), (hx + dw + 0.07, 0.14), (1.32, 0.10)):
        for yy in (R - 0.04, L + 0.04):
            box(bm, Vector((px, yy, (belt + roof) / 2)), (pw, 0.06, roof - belt), mi=0)
    rot_ws = Matrix.Rotation(math.radians(-30), 4, "Y")
    box(bm, Vector((-1.22, cy, (belt + roof) / 2)), (0.03, W - 0.14, (roof - belt) / math.cos(math.radians(30))), rot=rot_ws, mi=1)
    rot_rw = Matrix.Rotation(math.radians(25), 4, "Y")
    box(bm, Vector((1.47, cy, (belt + roof) / 2)), (0.03, W - 0.14, (roof - belt) / math.cos(math.radians(25))), rot=rot_rw, mi=1)
    box(bm, Vector((0.15, L + 0.03, (belt + roof) / 2)), (2.4, 0.02, roof - belt - 0.04), mi=1)
    box(bm, Vector(((-1.0 + hx - 0.08) / 2, R - 0.03, (belt + roof) / 2)), (hx - 0.08 + 1.0, 0.02, roof - belt - 0.04), mi=1)
    box(bm, Vector((1.20, R - 0.03, (belt + roof) / 2)), (0.16, 0.02, roof - belt - 0.04), mi=1)
    # 車內：後座（座墊面 0.72、靠背）、前座椅背、儀表板、司機剪影（從暗色車窗看得出有人在開）
    box(bm, Vector((0.49, cy, 0.48)), (0.47, W - 0.24, 0.48), mi=3)
    box(bm, Vector((0.80, cy, 1.03)), (0.16, W - 0.24, 0.62), rot=Matrix.Rotation(math.radians(-8), 4, "Y"), mi=3)
    for yy in (cy + 0.42, cy - 0.42):
        box(bm, Vector((-0.20, yy, 0.80)), (0.12, 0.62, 0.95), mi=3)
    box(bm, Vector((-0.95, cy, 0.95)), (0.30, W - 0.2, 0.18), mi=2)
    ball(bm, Vector((-0.45, cy - 0.42, 1.28)), (0.11, 0.10, 0.12), mi=2, seg=12)
    box(bm, Vector((-0.45, cy - 0.42, 1.0)), (0.22, 0.40, 0.42), mi=2)
    # 保險桿、車頭燈、尾燈、後照鏡
    box(bm, Vector((fr - 0.04, cy, bot + 0.12)), (0.10, W + 0.02, 0.16), mi=4)
    box(bm, Vector((re + 0.04, cy, bot + 0.12)), (0.10, W + 0.02, 0.16), mi=4)
    for yy in (R - 0.28, L + 0.28):
        box(bm, Vector((fr - 0.01, yy, belt - 0.16)), (0.03, 0.32, 0.12), mi=5)
        box(bm, Vector((re + 0.01, yy, belt - 0.12)), (0.03, 0.30, 0.16), mi=6)
        box(bm, Vector((-1.0, (R + 0.08) if yy > cy else (L - 0.08), belt + 0.08)), (0.10, 0.14, 0.09), mi=0)
    mesh_obj("V3_TaxiBody", bm, [M["body"], M["glass"], M["inner"], M["seat"], M["dark"], M["head"], M["tail"]], c, parent=root)
    bm = MB()                                                                            # 車頂 TAXI 燈
    box(bm, Vector((0.15, cy, roof + 0.09)), (0.55, 0.30, 0.18), mi=0)
    box(bm, Vector((0.15, cy, roof + 0.005)), (0.60, 0.34, 0.01), mi=1)
    mesh_obj("V3_TaxiSign", bm, [M["sign"], M["dark"]], c, parent=root)
    fnt = None
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try:
            fnt = bpy.data.fonts.load(p, check_existing=True); break
        except Exception:
            pass
    # 字體物件繞 X 轉 90° 後字面朝 −y：右側（+y 面）要再轉 180°，左側不用（第 4 輪檢查：右側原本是反的「IXAT」）
    for nm, loc, rz in (("V3_TaxiTxtR", (0.15, cy + 0.151, roof + 0.09), 180.0), ("V3_TaxiTxtL", (0.15, cy - 0.151, roof + 0.09), 0.0),
                        ("V3_TaxiTxtB", (0.426, cy, roof + 0.09), 90.0)):
        cu = bpy.data.curves.get(nm) or bpy.data.curves.new(nm, "FONT")
        cu.body = "TAXI"; cu.size = 0.11; cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = 0.002
        if fnt:
            cu.font = fnt
        if nm in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
        o = bpy.data.objects.new(nm, cu); c.objects.link(o); o.parent = root
        cu.materials.clear(); cu.materials.append(M["signtxt"])
        o.location = loc; o.rotation_euler = (math.radians(90), 0, math.radians(rz))
    # 右後門（轉軸在門的前緣；局部 x＝沿門往車尾，關著時門外側在 y −0.02）
    hinge = empty("V3_TaxiHinge", c, (hx, hy, 0.0), parent=root)
    bm = MB()
    box(bm, Vector((dw / 2, -0.04, (dz0 + belt) / 2)), (dw, 0.08, belt - dz0), mi=0)
    for xx in (0.03, dw - 0.03):
        box(bm, Vector((xx, -0.03, (belt + dz1) / 2)), (0.06, 0.04, dz1 - belt), mi=0)
    box(bm, Vector((dw / 2, -0.03, dz1 - 0.02)), (dw, 0.04, 0.04), mi=0)
    box(bm, Vector((dw / 2, -0.03, (belt + dz1) / 2)), (dw - 0.10, 0.02, dz1 - belt - 0.04), mi=1)
    box(bm, Vector((T["handle"][0], 0.012, T["handle"][1])), (0.14, 0.025, 0.035), mi=2)                            # 門把
    box(bm, Vector((dw / 2, -0.085, 0.78)), (dw - 0.1, 0.01, 0.30), mi=3)                                          # 門內飾板
    mesh_obj("V3_TaxiDoor", bm, [M["body"], M["glass"], M["chrome"], M["inner"]], c, parent=hinge)
    wheels = []
    for i, ax in enumerate(T["axle"]):
        for j, yy in enumerate((R - 0.17, L + 0.17)):
            e = empty(f"V3_Wheel{i}{j}", c, (ax, yy, rd + T["wheel_r"]), parent=root)
            bm = MB()
            cyl(bm, Vector((0, 0, 0)), T["wheel_r"], 0.22, axis="Y", seg=28, mi=0)
            sy = 0.11 if j == 0 else -0.11
            cyl(bm, Vector((0, sy, 0)), 0.17, 0.02, axis="Y", seg=20, mi=1)
            for k in range(5):                                                         # 輪框的輻條（看得出輪子在轉）
                a = 2 * math.pi * k / 5
                box(bm, Vector((0.09 * math.cos(a), sy * 1.11, 0.09 * math.sin(a))), (0.035, 0.01, 0.13),
                    rot=Matrix.Rotation(-a + math.pi / 2, 4, "Y"), mi=0)
            mesh_obj(f"V3_WheelMesh{i}{j}", bm, [M["tire"], M["hub"]], c, smooth=True, parent=e)
            wheels.append(e)
    _light(c, "V3_TaxiHead", "SPOT", (fr - 0.05, cy, belt - 0.15), 120.0, (1.0, 0.93, 0.78), size=0.05,
           rot=(math.radians(90), 0, math.radians(90)), spot=55).parent = root
    _light(c, "V3_TaxiTail", "POINT", (re + 0.35, cy, belt - 0.1), 1.2, (1.0, 0.2, 0.2), size=0.05).parent = root   # 第一版 8 W 把車尾照成一團橘光
    ST.update(root=root, hinge=hinge, wheels=wheels)
    return root


def taxi_set(door_deg, drive_x):
    """右後門開幾度（往人行道那側開，正值）、整台往 −X 開了多遠（drive_x ≤ 0）；輪子照距離轉"""
    ST["hinge"].rotation_euler = (0, 0, math.radians(door_deg))
    ST["root"].location = (drive_x, 0, 0)
    for e in ST["wheels"]:
        e.rotation_euler = (0, drive_x / TAXI["wheel_r"], 0)


def make_blush(arm, face_name, strength=0.85):
    """醉紅的臉頰：兩片柔邊的紅色貼片（中心不透明 → 邊緣透明），貼在臉頰表面、掛在頭骨上跟著頭動。
    位置：眼珠骨頭往下 3 cm、往外 1.5 cm，從臉前往後打一道光線找臉的表面"""
    m = bpy.data.materials.get("V3_Blush") or bpy.data.materials.new("V3_Blush")
    m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord"); gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.75; cr.color_ramp.elements[1].color = (strength, strength, strength, 1)
    nt.links.new(tc.outputs["Object"], gr.inputs["Vector"]); nt.links.new(gr.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], bs.inputs["Alpha"]); nt.links.new(bs.outputs[0], out.inputs["Surface"])
    bs.inputs["Base Color"].default_value = (*srgb("#E8505E"), 1)
    bs.inputs["Roughness"].default_value = 0.6
    if "Emission Color" in bs.inputs:
        bs.inputs["Emission Color"].default_value = (*srgb("#E8505E"), 1); bs.inputs["Emission Strength"].default_value = 0.25
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    # 臉頰位置在臉部網格的原始姿勢（骨架 rest 空間）裡找：預覽為了加速關掉網格修改器，場景裡的臉停在原點，光線打不到
    #   （第一版用 scene.ray_cast，打到後面的牆）。rest 空間：面向 −Y、上 +Z、左手邊 +X
    bpy.context.view_layer.update()
    face = bpy.data.objects[face_name]; Ai = arm.matrix_world.inverted()
    Fm = Ai @ face.matrix_world
    V = [(Fm @ v.co, (Fm.to_3x3() @ v.normal).normalized()) for v in face.data.vertices]
    pb = arm.pose.bones; bH = arm.data.bones["J_Bip_C_Head"]
    P = arm.matrix_world @ pb["J_Bip_C_Head"].matrix @ bH.matrix_local.inverted()      # rest 空間 → 現在姿勢的世界座標
    made = []
    for side, sg in (("L", 1.0), ("R", -1.0)):
        eye = arm.data.bones[f"J_Adj_{side}_FaceEye"].head_local
        gx, gz = eye.x + sg * 0.015, eye.z - 0.030
        near = [(co, n) for co, n in V if abs(co.x - gx) < 0.006 and abs(co.z - gz) < 0.006 and n.y < -0.3]
        if near:
            co, n = min(near, key=lambda cn: cn[0].y)                                   # 最前面（−Y）的那一點＝臉頰表面
        else:
            co, n = Vector((gx, eye.y - 0.02, gz)), Vector((0, -1, 0))
        loc = P @ co; nrm = (P.to_3x3() @ n).normalized()
        lft = (P.to_3x3() @ Vector((1, 0, 0))).normalized()
        print("BLUSH", side, len(near), [round(x, 3) for x in co], flush=True)
        me = bpy.data.meshes.new(f"V3_Blush{side}")
        bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=1.0); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.get(f"V3_Blush{side}")
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
        o = bpy.data.objects.new(f"V3_Blush{side}", me); bpy.context.scene.collection.objects.link(o)
        me.materials.append(m)
        z = Vector(nrm).normalized(); x = (lft - z * lft.dot(z)).normalized(); y = z.cross(x)
        Mw = Matrix.Translation(loc + z * 0.0015) @ Matrix((x, y, z)).transposed().to_4x4() @ Matrix.Diagonal((0.026, 0.019, 1.0, 1.0))
        o.parent = arm; o.parent_type = "BONE"; o.parent_bone = "J_Bip_C_Head"
        bpy.context.view_layer.update()
        o.matrix_world = Mw
        made.append(o)
    return made


# ════════ 真實車款的計程車（2026-10-11 使用者選：3D Warehouse「TOYOTA camry xle V6 LINE TAXI」，台灣網友 Cheng Yen, TSAO 做的）════════
#   檔案 D:\render-work\assets\taxi_line_camry\line_taxi_camry.glb（3D Warehouse 一般模型授權：可用在自己的影片、不能再散布模型檔）。
#   原檔單位小了 3.92 倍、車頭朝 −Y → 放大、轉 −90°（車頭朝 −X、右側朝 +Y），模型座標（車心在原點、輪子底 z 0）再平移 CAR_SHIFT：
#   右後門的門把（模型 x 約 1.05）對到新郎 4.0～4.2 秒摸到的地方（場景 x 0.70），右側車身（模型 y 0.94）貼路緣（y −0.02），輪子貼馬路。
#   車門不是獨立零件 → 照右後門的範圍（模型 x 0.165～1.24、y > 0.70）把面切出來，掛在門的前緣（轉軸）。
#   商標：V12 規定不放官方商標 → 前門 LINE TAXI 標誌、後門車號、後擋風玻璃車號、車牌字都拿掉（車牌留白）；車身換成台灣小黃的黃色。
TAXI_GLB = r"D:\render-work\assets\taxi_line_camry\line_taxi_camry.glb"
TAXI_S = 3.92
CAR_SHIFT = Vector((-0.35, -0.96, -0.12))
DOOR_M = dict(x=(0.165, 1.24), z=(0.20, 1.36), y_out=0.70, y_in=0.70, win_x=1.0, arch=(1.33, 0.33, 0.43))   # 模型座標
WHEELS_M = [(-1.47, 0.33), (1.33, 0.33)]                                                                     # 前／後輪心（模型 x, z）
# 前門 LINE TAXI 標誌、後門車號是「印在車門外板貼圖上」（外板本身），不能藏 → 換成車身黃；後擋風玻璃的車號貼紙、車牌紅字藏起來；
#   車頂燈箱的貼圖是 TaxiGo 車隊商標 → 換成白色燈箱，前後各貼一個「TAXI」字
DECAL_MATS = ("前門版logo", "後門版-右-01", "後門版-左-01")
HIDE_MATS = ("車牌字", "[Color_A01]")
SIGN_MAT = "taxigo-w"
YELLOW = "#F7C600"


def load_taxi_model(c):
    import os
    if not os.path.exists(TAXI_GLB):
        return None
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=TAXI_GLB)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for cc in list(o.users_collection):
            cc.objects.unlink(o)
        c.objects.link(o)
    root = empty("V3_Taxi", c, (0, 0, 0))
    model = empty("V3_TaxiModel", c, (0, 0, 0), parent=root)
    for o in new:
        if o.parent is None:
            o.parent = model
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(cr) for o in meshes for cr in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr = (lo + hi) / 2
    Mm = Matrix.Rotation(math.radians(-90), 4, "Z") @ Matrix.Diagonal((TAXI_S, TAXI_S, TAXI_S, 1)) @ Matrix.Translation(-Vector((ctr.x, ctr.y, lo.z)))
    model.matrix_world = Matrix.Translation(CAR_SHIFT) @ Mm
    bpy.context.view_layer.update()
    W = Matrix.Translation(-CAR_SHIFT)                                  # 世界 → 模型座標（還沒開走時）
    # 材質：車身黃、拿掉商標與車號、車燈發光
    for o in meshes:
        for i, m in enumerate(o.data.materials):
            if not m:
                continue
            if m.name in HIDE_MATS:
                o.hide_render = True; o.hide_viewport = True
    ymat = _m("V3_TaxiYellowCar", YELLOW, rough=0.22, spec=0.6, coat=0.6)
    signm = _m("V3_TaxiSignBox", "#FFF8E8", rough=0.4, emit=1.6)
    for o in meshes:
        for i, m in enumerate(o.data.materials):
            if m and m.name in ("yellow-02", "yellow-1") + DECAL_MATS:
                o.data.materials[i] = ymat
            elif m and m.name == SIGN_MAT:
                o.data.materials[i] = signm
            elif m and m.name in ("BrakeLights_Glass",):
                o.data.materials[i] = _m("V3_TaxiBrake", "#C8202C", rough=0.2, emit=1.2)
            elif m and m.name in ("HeadLights_Glass",):
                o.data.materials[i] = _m("V3_TaxiHeadGlass", "#FFF4D6", rough=0.1, emit=2.0)
    # 右後門：把門範圍裡的面從各物件切出來（原物件刪掉那些面、複製一份只留那些面），合成一個門物件掛在轉軸
    hinge_w = W.inverted() @ Vector((DOOR_M["x"][0], 0.93, 0.0))
    hinge = empty("V3_TaxiHinge", c, (hinge_w.x, hinge_w.y, 0.0), parent=root)
    skip_mats = ("Tyres", "[Color M03]", "[Color M01]", "UnderCarriage") + HIDE_MATS
    ax, az, ar = DOOR_M["arch"]

    def in_door(p, mn):
        if mn in skip_mats:
            return False
        if not (DOOR_M["x"][0] <= p.x <= DOOR_M["x"][1] and DOOR_M["z"][0] <= p.z <= DOOR_M["z"][1]):
            return False
        if math.hypot(p.x - ax, p.z - az) < ar:                         # 後輪拱
            return False
        if mn == "Windows":
            return p.y > 0.60 and p.x <= DOOR_M["win_x"]
        if mn == "Interior":
            return p.y > DOOR_M["y_in"]
        return p.y > DOOR_M["y_out"]
    parts = []
    for o in meshes:
        if o.hide_render:
            continue
        Mo = W @ o.matrix_world
        mats = [m.name if m else "-" for m in o.data.materials]
        sel = [f.index for f in o.data.polygons if in_door(Mo @ f.center, mats[f.material_index] if mats else "-")]
        if not sel:
            continue
        if o.data.users > 1:                                            # GLB 的共用網格（左右對稱的零件、四個輪子）：先變成獨立的再切，不然會改到另一個
            o.data = o.data.copy()
        cp = o.copy(); cp.data = o.data.copy(); c.objects.link(cp)
        for ob, keep_sel in ((o, False), (cp, True)):
            bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
            S_ = set(sel)
            kill = [f for f in bm.faces if (f.index in S_) != keep_sel]
            bmesh.ops.delete(bm, geom=kill, context="FACES")
            bm.to_mesh(ob.data); bm.free()
        parts.append(cp)
    if parts:
        bpy.context.view_layer.update()
        for p_ in parts:
            Mw = p_.matrix_world.copy(); p_.parent = hinge; p_.matrix_world = Mw
    print("TAXI_MODEL door parts", len(parts), "faces", sum(len(p_.data.polygons) for p_ in parts), flush=True)
    # 輪子：輪心附近的小零件（輪胎、輪框）各掛一個轉軸
    wheels = []
    for i, (wx, wz) in enumerate(WHEELS_M):
        for j, wy in enumerate((0.85, -0.85)):
            cw = W.inverted() @ Vector((wx, wy, wz))
            e = empty(f"V3_Wheel{i}{j}", c, tuple(cw), parent=root)
            bpy.context.view_layer.update()                                 # 先更新轉軸的世界座標再掛輪子（沒更新時輪子位置被多加一次，跑到兩倍遠）
            for o in meshes:
                if o.parent and o.parent.name.startswith("V3_TaxiHinge"):
                    continue
                bb = [W @ o.matrix_world @ Vector(cr) for cr in o.bound_box]
                b0 = Vector((min(p.x for p in bb), min(p.y for p in bb), min(p.z for p in bb))); b1 = Vector((max(p.x for p in bb), max(p.y for p in bb), max(p.z for p in bb)))
                bc = (b0 + b1) / 2
                if (b1 - b0).length < 1.05 and abs(bc.x - wx) < 0.2 and abs(bc.z - wz) < 0.2 and bc.y * wy > 0 and abs(abs(bc.y) - 0.85) < 0.25:
                    Mw = o.matrix_world.copy(); o.parent = e; o.matrix_world = Mw
            wheels.append(e)
    # 車頂燈箱的「TAXI」字（前後兩面；燈箱在模型 x 0.29、高 1.45～1.61、寬 0.33）
    fnt = None
    for fp in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try:
            fnt = bpy.data.fonts.load(fp, check_existing=True); break
        except Exception:
            pass
    tm = _m("V3_TaxiSignText", "#1E1E22", rough=0.5)
    for nm, dx, rz in (("V3_TaxiTxtF", -0.037, -90.0), ("V3_TaxiTxtB", 0.037, 90.0)):
        cu = bpy.data.curves.get(nm) or bpy.data.curves.new(nm, "FONT")
        cu.body = "TAXI"; cu.size = 0.085; cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.extrude = 0.001
        if fnt:
            cu.font = fnt
        if nm in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
        ob = bpy.data.objects.new(nm, cu); c.objects.link(ob); ob.parent = root
        cu.materials.clear(); cu.materials.append(tm)
        ob.location = tuple(W.inverted() @ Vector((0.29 + dx, -0.01, 1.53))); ob.rotation_euler = (math.radians(90), 0, math.radians(rz))
    # 司機的剪影（模型沒有人；從暗色車窗看得出有人在開，駕駛座在左前）
    bm = MB()
    dp = W.inverted() @ Vector((-0.30, -0.38, 0.0))
    ball(bm, Vector((dp.x, dp.y, 1.02)), (0.10, 0.09, 0.11), mi=0, seg=12)
    box(bm, Vector((dp.x, dp.y, 0.74)), (0.22, 0.38, 0.40), mi=0)
    mesh_obj("V3_TaxiDriver", bm, [_m("V3_DriverDark", "#2A2724", rough=0.85)], c, parent=root)
    fr = W.inverted() @ Vector((-2.45, 0.0, 0.62)); rr = W.inverted() @ Vector((2.45, 0.0, 0.70))
    _light(c, "V3_TaxiHead", "SPOT", tuple(fr), 120.0, (1.0, 0.93, 0.78), size=0.05, rot=(math.radians(90), 0, math.radians(90)), spot=55).parent = root
    _light(c, "V3_TaxiTail", "POINT", tuple(rr + Vector((0.2, 0, 0))), 1.2, (1.0, 0.2, 0.2), size=0.05).parent = root
    ST.update(root=root, hinge=hinge, wheels=wheels)
    # mx_preview 用的門軸／門把（世界座標）
    TAXI.update(hinge=(hinge_w.x, hinge_w.y), wheel_r=0.333, model=True)
    return root


def v3_07b_build():
    c = build_street()
    if load_taxi_model(c) is None:                                          # 沒有下載的模型時退回幾何做的卡通車
        build_taxi(c)


def v3_07b_frame(t, props=True, cast=True, cam=True):
    show("Set_Street", True)


SHOTS["v3_07b"] = dict(set="Set_Street", cast=True, t0=0.0, dur=9.0, tail=0.0, build=v3_07b_build, frame=v3_07b_frame,
                       actors=[], skirt=False, stills=[0.5, 2.6, 4.5, 5.5, 6.5, 7.6, 8.5])
